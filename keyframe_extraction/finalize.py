from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .pipeline import (
    ExtractionJob,
    _atomic_write_json,
    discover_videos,
    merge_completed_metadata,
    validate_completed_job,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def _load_status(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            status = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read completion manifest {path}: {error}") from error
    if not isinstance(status, dict):
        raise ValueError(f"Completion manifest must be an object: {path}")
    return status


def finalize_artifacts(
    source_dir: Path,
    output_root: Path,
    metadata_dir: Path,
    status_dir: Path,
    merged_metadata: Path,
    fps_dict_path: Path,
) -> dict[str, int | str | list[float]]:
    source_dir = source_dir.resolve()
    output_root = output_root.resolve()
    metadata_dir = metadata_dir.resolve()
    status_dir = status_dir.resolve()
    videos = discover_videos(source_dir)

    fps_by_video: dict[str, float] = {}
    invalid: list[str] = []
    validated_frames = 0
    intervals: set[float] = set()
    for video in videos:
        video_id = video.stem
        status_path = status_dir / f"{video_id}.done.json"
        try:
            status = _load_status(status_path)
            interval = float(status["interval_seconds"])
            fps = float(status["fps"])
            if not math.isfinite(fps) or fps <= 0:
                raise ValueError(f"Invalid FPS for {video_id}: {fps}")
            job = ExtractionJob(
                video_path=str(video.resolve()),
                output_root=str(output_root),
                metadata_dir=str(metadata_dir),
                status_dir=str(status_dir),
                interval=interval,
            )
            valid, frame_count = validate_completed_job(job)
            if not valid:
                raise ValueError(f"Completion validation failed for {video_id}")
            fps_by_video[video_id] = fps
            validated_frames += frame_count
            intervals.add(interval)
        except (KeyError, TypeError, ValueError) as error:
            invalid.append(f"{video_id}: {error}")

    status_ids = {path.name.removesuffix(".done.json") for path in status_dir.glob("*.done.json")}
    source_ids = {video.stem for video in videos}
    extra_status = sorted(status_ids - source_ids)
    if invalid or extra_status:
        details = invalid[:10]
        if len(invalid) > 10:
            details.append(f"... and {len(invalid) - 10} more invalid videos")
        if extra_status:
            details.append("extra completion manifests: " + ", ".join(extra_status[:10]))
        raise ValueError("Cannot finalize incomplete dataset: " + "; ".join(details))

    merged_videos, merged_frames, merged_intervals = merge_completed_metadata(
        metadata_dir, status_dir, merged_metadata.resolve()
    )
    if merged_videos != len(videos) or merged_frames != validated_frames:
        raise ValueError(
            "Merged metadata count mismatch: "
            f"videos={merged_videos}/{len(videos)}, frames={merged_frames}/{validated_frames}"
        )
    if merged_intervals != sorted(intervals):
        raise ValueError(
            f"Merged interval mismatch: merged={merged_intervals}, validated={sorted(intervals)}"
        )

    _atomic_write_json(fps_dict_path.resolve(), fps_by_video)
    return {
        "video_count": len(videos),
        "frame_count": merged_frames,
        "intervals": merged_intervals,
        "merged_metadata": str(merged_metadata.resolve()),
        "fps_dict": str(fps_dict_path.resolve()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m keyframe_extraction.finalize",
        description="Validate every source video and build runtime keyframe metadata artifacts.",
    )
    parser.add_argument("--input", type=Path, default=DATA_DIR / "unzipped" / "video")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "extracted_keyframes")
    parser.add_argument("--metadata-dir", type=Path, default=DATA_DIR / "frame_metadata")
    parser.add_argument("--status-dir", type=Path, default=DATA_DIR / "extraction_status")
    parser.add_argument("--merged-metadata", type=Path, default=DATA_DIR / "frames_metadata_v2.json")
    parser.add_argument("--fps-dict", type=Path, default=DATA_DIR / "fps_dict_v2.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = finalize_artifacts(
            source_dir=args.input,
            output_root=args.output,
            metadata_dir=args.metadata_dir,
            status_dir=args.status_dir,
            merged_metadata=args.merged_metadata,
            fps_dict_path=args.fps_dict,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
