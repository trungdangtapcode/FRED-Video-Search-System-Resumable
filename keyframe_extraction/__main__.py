from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from .pipeline import (
    build_jobs,
    discover_videos,
    load_video_manifest,
    merge_completed_metadata,
    result_as_dict,
    run_jobs,
    write_success_marker,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m keyframe_extraction",
        description="Extract time-sampled keyframes with per-video resume support.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_DIR / "unzipped" / "video",
        help="directory containing source videos (searched recursively)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="shard manifest produced by python -m keyframe_extraction.plan",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="place every output for this shard below one directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "extracted_keyframes",
        help="directory for per-video frame folders",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=DATA_DIR / "frame_metadata",
        help="directory for per-video metadata JSON files",
    )
    parser.add_argument(
        "--status-dir",
        type=Path,
        default=DATA_DIR / "extraction_status",
        help="directory for completed-job manifests and locks",
    )
    parser.add_argument(
        "--merged-metadata",
        type=Path,
        default=DATA_DIR / "frames_metadata_v2.json",
        help="combined metadata JSON written after the run",
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="seconds between extracted frames (default: manifest value or 2)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(4, os.cpu_count() or 1),
        help="number of videos processed concurrently (default: up to 4)",
    )
    parser.add_argument(
        "--video",
        action="append",
        default=[],
        metavar="ID",
        help="only process this video ID or filename; repeat for multiple videos",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="zero-based offset in the sorted video list",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="maximum number of selected videos to process",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-extract videos even when their completed manifests are valid",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="do not rebuild the combined frame metadata file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the run summary as JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.manifest and (args.video or args.start != 0 or args.limit is not None):
        parser.error("--manifest cannot be combined with --video, --start, or --limit")

    selected_videos = args.video
    manifest_interval = None
    if args.manifest:
        try:
            selected_videos, manifest_interval = load_video_manifest(
                args.manifest.expanduser()
            )
        except ValueError as error:
            parser.error(str(error))

    interval = args.interval
    if interval is None:
        interval = manifest_interval if manifest_interval is not None else 2.0
    elif manifest_interval is not None and not math.isclose(
        interval, manifest_interval, rel_tol=0, abs_tol=1e-9
    ):
        parser.error(
            f"--interval {interval} does not match manifest interval "
            f"{manifest_interval}"
        )

    if args.run_dir:
        run_dir = args.run_dir.expanduser()
        output_root = run_dir / "keyframes"
        metadata_dir = run_dir / "frame_metadata"
        status_dir = run_dir / "extraction_status"
        merged_metadata = run_dir / "frames_metadata_v2.json"
        success_marker = run_dir / "_SUCCESS.json"
        success_marker.unlink(missing_ok=True)
    else:
        output_root = args.output.expanduser()
        metadata_dir = args.metadata_dir.expanduser()
        status_dir = args.status_dir.expanduser()
        merged_metadata = args.merged_metadata.expanduser()
        success_marker = None

    try:
        videos = discover_videos(
            args.input.expanduser(),
            selected_videos=selected_videos,
            start=args.start,
            limit=args.limit,
        )
        jobs = build_jobs(
            videos,
            output_root=output_root,
            metadata_dir=metadata_dir,
            status_dir=status_dir,
            interval=interval,
            force=args.force,
        )
        results = run_jobs(jobs, args.workers)
    except ValueError as error:
        parser.error(str(error))

    merge_summary = None
    if not args.no_merge:
        video_count, frame_count, intervals = merge_completed_metadata(
            metadata_dir.resolve(),
            status_dir.resolve(),
            merged_metadata.resolve(),
        )
        merge_summary = {
            "videos": video_count,
            "frames": frame_count,
            "intervals": intervals,
            "path": str(merged_metadata.resolve()),
        }

    counts = {
        status: sum(result.status == status for result in results)
        for status in ("completed", "skipped", "locked", "failed")
    }
    summary = {
        "selected": len(jobs),
        **counts,
        "results": [result_as_dict(result) for result in results],
        "merged_metadata": merge_summary,
    }
    if success_marker is not None and not counts["failed"] and not counts["locked"]:
        write_success_marker(success_marker, summary)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for result in results:
            detail = f" ({result.frame_count} frames)" if result.frame_count else ""
            message = f": {result.message}" if result.message else ""
            print(f"[{result.status.upper():9}] {result.video_id}{detail}{message}")
        print(
            "Summary: "
            + ", ".join([f"{key}={value}" for key, value in counts.items()])
        )
        if merge_summary is not None:
            print(
                f"Merged metadata: {merge_summary['frames']} frames from "
                f"{merge_summary['videos']} videos -> {merge_summary['path']}"
            )
            if len(merge_summary["intervals"]) > 1:
                print(
                    "Warning: completed videos use different extraction intervals: "
                    + ", ".join(map(str, merge_summary["intervals"]))
                )

    return 1 if counts["failed"] or counts["locked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
