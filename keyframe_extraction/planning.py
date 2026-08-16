from __future__ import annotations

import bisect
import json
import math
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .pipeline import discover_videos


PLAN_VERSION = 1


@dataclass(frozen=True)
class VideoInfo:
    video_id: str
    filename: str
    duration_seconds: float


@dataclass(frozen=True)
class VideoShard:
    shard_id: str
    group: str
    part: int
    part_count: int
    videos: tuple[VideoInfo, ...]

    @property
    def duration_seconds(self) -> float:
        return sum(video.duration_seconds for video in self.videos)


def probe_video_files(input_dir: Path, workers: int) -> list[VideoInfo]:
    if workers < 1:
        raise ValueError("probe workers must be greater than zero")

    videos = discover_videos(input_dir)
    worker_count = min(workers, len(videos), os.cpu_count() or 1)
    if worker_count < 2:
        return [_probe_video(path) for path in videos]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(_probe_video, videos))
    return sorted(results, key=lambda video: _natural_key(video.video_id))


def load_media_info(directory: Path) -> list[VideoInfo]:
    if not directory.is_dir():
        raise ValueError(f"Media-info directory does not exist: {directory}")

    videos: list[VideoInfo] = []
    for path in sorted(directory.rglob("*.json"), key=lambda item: _natural_key(item.name)):
        try:
            with path.open("r", encoding="utf-8") as file:
                value = json.load(file)
            duration = float(value["length"])
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid media-info file {path}: {error}") from error
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Invalid duration in media-info file {path}: {duration}")
        videos.append(VideoInfo(path.stem, f"{path.stem}.mp4", duration))

    if not videos:
        raise ValueError(f"No media-info JSON files found in: {directory}")
    _validate_unique_ids(videos)
    return videos


def plan_video_shards(
    videos: Sequence[VideoInfo],
    target_duration_seconds: float,
    keep_groups: bool = True,
) -> list[VideoShard]:
    if not videos:
        raise ValueError("At least one video is required to build a plan")
    if not math.isfinite(target_duration_seconds) or target_duration_seconds <= 0:
        raise ValueError("target duration must be a positive number")
    _validate_unique_ids(videos)

    grouped: dict[str, list[VideoInfo]] = {}
    for video in sorted(videos, key=lambda item: _natural_key(item.video_id)):
        group = _video_group(video.video_id) if keep_groups else "all"
        grouped.setdefault(group, []).append(video)

    shards: list[VideoShard] = []
    for group in sorted(grouped, key=_natural_key):
        group_videos = grouped[group]
        total_duration = sum(video.duration_seconds for video in group_videos)
        part_count = min(
            len(group_videos),
            max(1, math.ceil(total_duration / target_duration_seconds)),
        )
        parts = _balanced_contiguous_parts(group_videos, part_count)
        for part_number, part_videos in enumerate(parts, start=1):
            shards.append(
                VideoShard(
                    shard_id=f"{group}_p{part_number:02d}",
                    group=group,
                    part=part_number,
                    part_count=part_count,
                    videos=tuple(part_videos),
                )
            )
    return shards


def write_shard_plan(
    shards: Sequence[VideoShard],
    output_dir: Path,
    interval_seconds: float,
    target_duration_seconds: float,
    bytes_per_frame: float | None = None,
) -> dict[str, object]:
    if not shards:
        raise ValueError("At least one shard is required")
    if not math.isfinite(interval_seconds) or interval_seconds <= 0:
        raise ValueError("interval must be a positive number")
    if bytes_per_frame is not None and (
        not math.isfinite(bytes_per_frame) or bytes_per_frame <= 0
    ):
        raise ValueError("bytes per frame must be a positive number")

    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_manifest in output_dir.glob("*/part-*.json"):
        stale_manifest.unlink()
    index_entries: list[dict[str, object]] = []
    total_videos = 0
    total_duration = 0.0
    total_frames = 0

    for shard in shards:
        group_dir = output_dir / shard.group
        manifest_path = group_dir / f"part-{shard.part:03d}.json"
        estimated_frames = sum(
            math.ceil(video.duration_seconds / interval_seconds)
            for video in shard.videos
        )
        manifest: dict[str, object] = {
            "version": PLAN_VERSION,
            "shard_id": shard.shard_id,
            "group": shard.group,
            "part": shard.part,
            "part_count": shard.part_count,
            "interval_seconds": interval_seconds,
            "target_duration_seconds": target_duration_seconds,
            "duration_seconds": shard.duration_seconds,
            "estimated_frames": estimated_frames,
            "videos": [
                {
                    "video_id": video.video_id,
                    "filename": video.filename,
                    "duration_seconds": video.duration_seconds,
                }
                for video in shard.videos
            ],
        }
        if bytes_per_frame is not None:
            manifest["estimated_output_bytes"] = round(
                estimated_frames * bytes_per_frame
            )
        _atomic_write_json(manifest_path, manifest)

        relative_path = manifest_path.relative_to(output_dir)
        entry = {
            "shard_id": shard.shard_id,
            "manifest": relative_path.as_posix(),
            "group": shard.group,
            "video_count": len(shard.videos),
            "duration_seconds": shard.duration_seconds,
            "estimated_frames": estimated_frames,
        }
        if bytes_per_frame is not None:
            entry["estimated_output_bytes"] = round(estimated_frames * bytes_per_frame)
        index_entries.append(entry)
        total_videos += len(shard.videos)
        total_duration += shard.duration_seconds
        total_frames += estimated_frames

    index: dict[str, object] = {
        "version": PLAN_VERSION,
        "interval_seconds": interval_seconds,
        "target_duration_seconds": target_duration_seconds,
        "video_count": total_videos,
        "shard_count": len(shards),
        "duration_seconds": total_duration,
        "estimated_frames": total_frames,
        "shards": index_entries,
    }
    if bytes_per_frame is not None:
        index["bytes_per_frame"] = bytes_per_frame
        index["estimated_output_bytes"] = round(total_frames * bytes_per_frame)
    _atomic_write_json(output_dir / "index.json", index)
    return index


def _probe_video(path: Path) -> VideoInfo:
    import cv2

    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError(f"Cannot open video while planning: {path}")
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    finally:
        capture.release()

    if not math.isfinite(fps) or fps <= 0 or frame_count <= 0:
        raise ValueError(
            f"Cannot determine duration for {path.name}: fps={fps}, frames={frame_count}"
        )
    return VideoInfo(path.stem, path.name, frame_count / fps)


def _balanced_contiguous_parts(
    videos: Sequence[VideoInfo], part_count: int
) -> list[list[VideoInfo]]:
    if part_count == 1:
        return [list(videos)]

    prefix = [0.0]
    for video in videos:
        prefix.append(prefix[-1] + video.duration_seconds)

    boundaries = [0]
    for part_number in range(1, part_count):
        minimum = boundaries[-1] + 1
        maximum = len(videos) - (part_count - part_number)
        target = prefix[-1] * part_number / part_count
        position = bisect.bisect_left(prefix, target, minimum, maximum + 1)
        position = min(maximum, max(minimum, position))
        candidates = [position]
        if position - 1 >= minimum:
            candidates.append(position - 1)
        boundary = min(candidates, key=lambda index: (abs(prefix[index] - target), index))
        boundaries.append(boundary)
    boundaries.append(len(videos))

    return [
        list(videos[start:end])
        for start, end in zip(boundaries, boundaries[1:])
    ]


def _video_group(video_id: str) -> str:
    match = re.match(r"^([^_]+)_", video_id)
    return match.group(1) if match else "videos"


def _validate_unique_ids(videos: Sequence[VideoInfo]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for video in videos:
        if video.video_id in seen:
            duplicates.add(video.video_id)
        seen.add(video.video_id)
    if duplicates:
        raise ValueError("Duplicate video IDs: " + ", ".join(sorted(duplicates)))


def _natural_key(value: str) -> list[tuple[int, object]]:
    return [
        (0, int(part)) if part.isdigit() else (1, part.lower())
        for part in re.split(r"(\d+)", value)
    ]


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
