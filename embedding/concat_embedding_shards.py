"""Validate and concatenate 28 lexicographically ordered embedding shards."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "embedding" / "shards"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "embedding" / "embeddings_qwen3_vl_8b.npy"
DEFAULT_DIMENSION = 4096


@dataclass(frozen=True)
class ShardSpec:
    shard_id: str
    rows: int
    video_ids: tuple[str, ...]
    allow_zero: bool = False


@dataclass(frozen=True)
class ShardArray:
    spec: ShardSpec
    path: Path
    dtype: np.dtype


def load_layout(project_root: Path = PROJECT_ROOT) -> list[ShardSpec]:
    manifests_root = project_root / "manifests" / "aic-2026"
    index = json.loads((manifests_root / "index.json").read_text())
    embedding_index = json.loads((manifests_root / "embedding-shards.json").read_text())
    embedding_status = {
        item["shard_id"]: item["status"] for item in embedding_index["shards"]
    }
    specs: list[ShardSpec] = []
    concatenated_video_ids: list[str] = []

    for shard in index["shards"]:
        shard_id = shard["shard_id"]
        manifest = json.loads((manifests_root / shard["manifest"]).read_text())
        marker = json.loads(
            (
                project_root
                / "data"
                / "keyframe_import_status"
                / f"{shard_id}.done.json"
            ).read_text()
        )
        video_ids = tuple(video["video_id"] for video in manifest["videos"])
        concatenated_video_ids.extend(video_ids)
        specs.append(
            ShardSpec(
                shard_id,
                int(marker["frame_count"]),
                video_ids,
                embedding_status.get(shard_id) == "rerun_zero",
            )
        )

    if len(specs) != 28:
        raise RuntimeError(f"Expected 28 shard specifications, found {len(specs)}")
    if len(concatenated_video_ids) != len(set(concatenated_video_ids)):
        raise RuntimeError("A video is assigned to more than one embedding shard")
    if concatenated_video_ids != sorted(concatenated_video_ids):
        raise RuntimeError("Manifest concat order is not global lexicographic video order")

    metadata = json.loads(
        (project_root / "data" / "frames_metadata_v2.json").read_text()
    )
    metadata_keys = [
        (Path(item["frame_path"]).parent.name, Path(item["frame_path"]).name)
        for item in metadata
    ]
    if metadata_keys != sorted(metadata_keys):
        raise RuntimeError("Global frame metadata is not lexicographically ordered")
    if sum(spec.rows for spec in specs) != len(metadata):
        raise RuntimeError(
            "Shard row total does not match data/frames_metadata_v2.json"
        )
    return specs


def validate_shards(
    specs: list[ShardSpec], input_dir: Path, dimension: int
) -> list[ShardArray]:
    arrays: list[ShardArray] = []
    incomplete: list[str] = []
    problems: list[str] = []

    for spec in specs:
        path = input_dir / f"{spec.shard_id}.npy"
        if not path.is_file():
            problems.append(f"{spec.shard_id}: missing {path}")
            continue
        try:
            array = np.load(path, mmap_mode="r", allow_pickle=False)
        except Exception as exc:
            problems.append(f"{spec.shard_id}: unreadable NPY ({exc})")
            continue
        if array.ndim != 2:
            problems.append(f"{spec.shard_id}: expected 2-D, got {array.shape}")
            continue
        if array.shape[0] == 0:
            incomplete.append(spec.shard_id)
            continue
        if array.shape != (spec.rows, dimension):
            problems.append(
                f"{spec.shard_id}: expected {(spec.rows, dimension)}, got {array.shape}"
            )
            continue
        if not np.issubdtype(array.dtype, np.floating):
            problems.append(f"{spec.shard_id}: expected floating dtype, got {array.dtype}")
            continue
        arrays.append(ShardArray(spec, path, array.dtype))

    if incomplete:
        problems.append(
            "placeholders not replaced: " + ", ".join(incomplete)
        )
    if problems:
        problems.insert(0, f"{len(arrays)}/{len(specs)} shard arrays ready")
        raise RuntimeError("Embedding shards are not ready:\n- " + "\n- ".join(problems))
    return arrays


def concatenate(
    arrays: list[ShardArray], output: Path, chunk_size: int, force: bool = False
) -> tuple[int, int, np.dtype]:
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists (use --force): {output}")
    total_rows = sum(item.spec.rows for item in arrays)
    dimension = np.load(arrays[0].path, mmap_mode="r", allow_pickle=False).shape[1]
    output_dtype = np.result_type(*(item.dtype for item in arrays))
    building = output.with_name(output.name + ".building")
    output.parent.mkdir(parents=True, exist_ok=True)
    if building.exists():
        building.unlink()

    destination = None
    try:
        destination = np.lib.format.open_memmap(
            building,
            mode="w+",
            dtype=output_dtype,
            shape=(total_rows, dimension),
        )
        offset = 0
        for item in arrays:
            source = np.load(item.path, mmap_mode="r", allow_pickle=False)
            if item.spec.allow_zero:
                for start in range(0, source.shape[0], chunk_size):
                    end = min(start + chunk_size, source.shape[0])
                    if np.any(source[start:end] != 0):
                        raise RuntimeError(
                            f"{item.spec.shard_id}: intentional zero shard contains nonzero data"
                        )
                # open_memmap created a sparse file; do not allocate its zero ranges.
                offset += source.shape[0]
                print(
                    f"{item.spec.shard_id}: {source.shape[0]} sparse zero rows; "
                    f"combined {offset}/{total_rows}"
                )
                continue
            for start in range(0, source.shape[0], chunk_size):
                end = min(start + chunk_size, source.shape[0])
                chunk = np.asarray(source[start:end])
                if not np.isfinite(chunk).all():
                    bad = np.argwhere(~np.isfinite(chunk))[0]
                    raise RuntimeError(
                        f"{item.spec.shard_id}: non-finite value at row "
                        f"{start + int(bad[0])}, column {int(bad[1])}"
                    )
                norms = np.linalg.norm(chunk.astype(np.float32, copy=False), axis=1)
                if np.any(norms == 0):
                    bad_row = start + int(np.flatnonzero(norms == 0)[0])
                    raise RuntimeError(
                        f"{item.spec.shard_id}: zero-length vector at row {bad_row}"
                    )
                destination[offset + start : offset + end] = chunk
            offset += source.shape[0]
            destination.flush()
            print(
                f"{item.spec.shard_id}: {source.shape[0]} rows; "
                f"combined {offset}/{total_rows}"
            )
        del destination
        destination = None

        check = np.load(building, mmap_mode="r", allow_pickle=False)
        if check.shape != (total_rows, dimension) or check.dtype != output_dtype:
            raise RuntimeError("Combined NPY failed read-back validation")
        del check
        os.replace(building, output)
    except Exception:
        if destination is not None:
            del destination
        building.unlink(missing_ok=True)
        raise
    return total_rows, dimension, output_dtype


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--chunk-size", type=int, default=8192)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = load_layout()
    try:
        arrays = validate_shards(specs, args.input_dir.resolve(), args.dimension)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Validated {len(arrays)} shards and {sum(x.spec.rows for x in arrays)} rows")
    if args.check_only:
        return
    rows, dimension, dtype = concatenate(
        arrays, args.output.resolve(), args.chunk_size, args.force
    )
    size_gib = args.output.resolve().stat().st_size / (1024**3)
    print(
        f"Wrote {args.output.resolve()}: shape=({rows}, {dimension}), "
        f"dtype={dtype}, size={size_gib:.2f} GiB"
    )


if __name__ == "__main__":
    main()
