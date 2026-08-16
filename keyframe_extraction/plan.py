from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .planning import (
    load_media_info,
    plan_video_shards,
    probe_video_files,
    write_shard_plan,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m keyframe_extraction.plan",
        description="Build duration-balanced extraction shard manifests.",
    )
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument(
        "--input",
        type=Path,
        help="directory containing source videos (searched recursively)",
    )
    sources.add_argument(
        "--media-info-dir",
        type=Path,
        help="directory of per-video JSON files with a numeric length field",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "manifests" / "generated",
        help="directory to write index.json and per-shard manifests",
    )
    parser.add_argument(
        "--target-hours",
        type=float,
        default=5.75,
        help="target source-video duration per shard (default: 5.75)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="planned seconds between keyframes (default: 2)",
    )
    parser.add_argument(
        "--probe-workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help="videos whose metadata is probed concurrently (default: up to 8)",
    )
    parser.add_argument(
        "--bytes-per-frame",
        type=float,
        help="optional measured average used to estimate each shard's output size",
    )
    parser.add_argument(
        "--mix-groups",
        action="store_true",
        help="allow a shard to contain different filename prefixes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the plan summary as JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.media_info_dir:
            videos = load_media_info(args.media_info_dir.expanduser())
        else:
            input_dir = args.input or DATA_DIR / "unzipped" / "video"
            videos = probe_video_files(input_dir.expanduser(), args.probe_workers)
        target_duration = args.target_hours * 3600
        shards = plan_video_shards(
            videos,
            target_duration_seconds=target_duration,
            keep_groups=not args.mix_groups,
        )
        index = write_shard_plan(
            shards,
            output_dir=args.output.expanduser(),
            interval_seconds=args.interval,
            target_duration_seconds=target_duration,
            bytes_per_frame=args.bytes_per_frame,
        )
    except ValueError as error:
        parser.error(str(error))

    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=2))
    else:
        for shard in index["shards"]:
            size = ""
            if "estimated_output_bytes" in shard:
                size = f", ~{shard['estimated_output_bytes'] / 1e9:.2f} GB"
            print(
                f"{shard['shard_id']}: {shard['video_count']} videos, "
                f"{shard['duration_seconds'] / 3600:.2f} h{size}"
            )
        print(
            f"Plan: {index['video_count']} videos -> {index['shard_count']} shards "
            f"in {args.output.expanduser().resolve()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
