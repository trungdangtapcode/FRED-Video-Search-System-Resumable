from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .pipeline import ExtractionJob, _atomic_write_json, validate_completed_job


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class PreparedVideo:
    video_id: str
    source_frames: Path
    destination_frames: Path
    metadata: list[dict]
    status: dict


def _load_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read JSON {path}: {error}") from error


def _source_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _frame_signature(directory: Path) -> list[tuple[str, int]]:
    return [(path.name, path.stat().st_size) for path in sorted(directory.glob("*.png"))]


def _find_payload(staging_dir: Path) -> tuple[Path, Path]:
    payloads = sorted(staging_dir.glob("*/data"))
    if len(payloads) != 1:
        raise ValueError(
            f"Expected exactly one <shard>/data payload in {staging_dir}, "
            f"found {len(payloads)}"
        )
    payload = payloads[0]
    return payload.parent, payload


def _manifest_videos(manifest_path: Path) -> tuple[str, float, list[dict]]:
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError(f"Manifest must be a JSON object: {manifest_path}")
    shard_id = manifest.get("shard_id")
    videos = manifest.get("videos")
    interval = manifest.get("interval_seconds")
    if not isinstance(shard_id, str) or not shard_id:
        raise ValueError(f"Manifest has no shard_id: {manifest_path}")
    if not isinstance(videos, list) or not videos:
        raise ValueError(f"Manifest has no videos: {manifest_path}")
    try:
        interval = float(interval)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Manifest has invalid interval_seconds: {manifest_path}") from error
    return shard_id, interval, videos


def _prepare_video(
    entry: dict,
    interval: float,
    payload: Path,
    project_root: Path,
) -> PreparedVideo:
    video_id = entry.get("video_id")
    filename = entry.get("filename")
    if not isinstance(video_id, str) or not isinstance(filename, str):
        raise ValueError(f"Invalid video entry: {entry!r}")

    source_video = project_root / "data" / "unzipped" / "video" / filename
    source_frames = payload / "extracted_keyframes" / video_id
    source_metadata = payload / "frame_metadata" / f"{video_id}.json"
    source_status = payload / "extraction_status" / f"{video_id}.done.json"
    if not source_video.is_file():
        raise ValueError(f"Source video is missing: {source_video}")
    if not source_frames.is_dir():
        raise ValueError(f"Frame directory is missing: {source_frames}")

    metadata = _load_json(source_metadata)
    status = _load_json(source_status)
    if not isinstance(metadata, list):
        raise ValueError(f"Metadata must be a list: {source_metadata}")
    if not isinstance(status, dict):
        raise ValueError(f"Status must be an object: {source_status}")
    if status.get("video_id") != video_id:
        raise ValueError(f"Status video_id mismatch: {source_status}")
    if float(status.get("interval_seconds", 0)) != interval:
        raise ValueError(f"Status interval mismatch: {source_status}")

    frames = sorted(source_frames.glob("*.png"))
    frame_count = int(status.get("frame_count", -1))
    if frame_count < 1 or len(metadata) != frame_count or len(frames) != frame_count:
        raise ValueError(
            f"Frame invariant failed for {video_id}: status={frame_count}, "
            f"metadata={len(metadata)}, files={len(frames)}"
        )

    destination_frames = project_root / "data" / "extracted_keyframes" / video_id
    destination_video = source_video.resolve()
    destination_frames_resolved = destination_frames.resolve()
    rewritten_metadata: list[dict] = []
    for index, (frame, item) in enumerate(zip(frames, metadata)):
        expected_name = f"{index:05d}.png"
        if frame.name != expected_name or frame.stat().st_size == 0:
            raise ValueError(f"Invalid frame sequence for {video_id}: {frame.name}")
        if not isinstance(item, dict) or Path(str(item.get("frame_path", ""))).name != expected_name:
            raise ValueError(f"Metadata/frame mismatch for {video_id}: {expected_name}")
        rewritten_metadata.append(
            {
                **item,
                "video_path": str(destination_video),
                "frame_path": str(destination_frames_resolved / expected_name),
            }
        )

    rewritten_status = {**status, "source": _source_signature(source_video)}
    return PreparedVideo(
        video_id=video_id,
        source_frames=source_frames,
        destination_frames=destination_frames,
        metadata=rewritten_metadata,
        status=rewritten_status,
    )


def import_shard(
    staging_dir: Path,
    manifest_path: Path,
    project_root: Path = PROJECT_ROOT,
    dataset: str | None = None,
    cleanup: bool = False,
) -> dict:
    staging_dir = staging_dir.resolve()
    project_root = project_root.resolve()
    shard_root, payload = _find_payload(staging_dir)
    shard_id, interval, entries = _manifest_videos(manifest_path.resolve())

    prepared = [
        _prepare_video(entry, interval, payload, project_root) for entry in entries
    ]
    payload_ids = {path.name for path in (payload / "extracted_keyframes").iterdir() if path.is_dir()}
    expected_ids = {video.video_id for video in prepared}
    if payload_ids != expected_ids:
        missing = sorted(expected_ids - payload_ids)
        extra = sorted(payload_ids - expected_ids)
        raise ValueError(f"Shard video mismatch: missing={missing}, extra={extra}")

    metadata_dir = project_root / "data" / "frame_metadata"
    status_dir = project_root / "data" / "extraction_status"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    status_dir.mkdir(parents=True, exist_ok=True)

    frame_count = 0
    for video in prepared:
        video.destination_frames.parent.mkdir(parents=True, exist_ok=True)
        if video.destination_frames.exists():
            if _frame_signature(video.destination_frames) != _frame_signature(video.source_frames):
                raise ValueError(f"Existing frames differ for {video.video_id}")
            shutil.rmtree(video.source_frames)
        else:
            os.replace(video.source_frames, video.destination_frames)

        metadata_path = metadata_dir / f"{video.video_id}.json"
        status_path = status_dir / f"{video.video_id}.done.json"
        _atomic_write_json(metadata_path, video.metadata)
        _atomic_write_json(status_path, video.status)
        job = ExtractionJob(
            video_path=video.metadata[0]["video_path"],
            output_root=str((project_root / "data" / "extracted_keyframes").resolve()),
            metadata_dir=str(metadata_dir.resolve()),
            status_dir=str(status_dir.resolve()),
            interval=interval,
        )
        valid, count = validate_completed_job(job)
        if not valid:
            raise ValueError(f"Imported video did not validate: {video.video_id}")
        frame_count += count

    summary = {
        "version": 1,
        "shard_id": shard_id,
        "dataset": dataset,
        "video_count": len(prepared),
        "frame_count": frame_count,
        "interval_seconds": interval,
    }
    marker_dir = project_root / "data" / "keyframe_import_status"
    marker_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(marker_dir / f"{shard_id}.done.json", summary)

    if cleanup:
        shutil.rmtree(shard_root)
        for path in staging_dir.glob("*.sha256"):
            path.unlink()
        for path in staging_dir.glob("*.kaggle-partial"):
            path.unlink()

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m keyframe_extraction.import_shard",
        description="Validate and install one extracted-keyframe Kaggle shard.",
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset")
    parser.add_argument("--cleanup", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = import_shard(
            staging_dir=args.input,
            manifest_path=args.manifest,
            dataset=args.dataset,
            cleanup=args.cleanup,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
