"""Validate aligned Qwen3-VL embeddings and build a cosine FAISS index."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import faiss
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIMENSION = 4096
DEFAULT_NPY = PROJECT_ROOT / "data" / "embedding" / "embeddings_qwen3_vl_8b.npy"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "npy",
        type=Path,
        nargs="?",
        default=DEFAULT_NPY,
        help="Combined NPY ordered by frame path",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=PROJECT_ROOT / "data" / "frames_metadata_v2.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "embeddings_qwen3_vl_8b.index",
    )
    parser.add_argument("--chunk-size", type=int, default=8192)
    parser.add_argument("--expected-dimension", type=int, default=EXPECTED_DIMENSION)
    parser.add_argument(
        "--allow-zero-vectors",
        action="store_true",
        help="Preserve intentional zero rows used for unavailable shards",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    npy_path = args.npy.resolve()
    metadata_path = args.metadata.resolve()
    output_path = args.output.resolve()

    with metadata_path.open() as handle:
        metadata = json.load(handle)
    paths = [item["frame_path"] for item in metadata]
    if len(paths) != len(set(paths)):
        raise RuntimeError("Metadata contains duplicate frame paths")
    if paths != sorted(paths):
        raise RuntimeError("Metadata frame paths are not globally lexicographic")

    vectors = np.load(npy_path, mmap_mode="r", allow_pickle=False)
    if vectors.ndim != 2:
        raise RuntimeError(f"Expected a 2-D NPY, got shape {vectors.shape}")
    if vectors.shape[0] != len(metadata):
        raise RuntimeError(
            f"Row mismatch: NPY has {vectors.shape[0]} rows; metadata has {len(metadata)}"
        )
    if vectors.shape[1] != args.expected_dimension:
        raise RuntimeError(
            f"Dimension mismatch: NPY has {vectors.shape[1]} columns; "
            f"Qwen3-VL-Embedding-8B produces {args.expected_dimension}"
        )
    if not np.issubdtype(vectors.dtype, np.number):
        raise RuntimeError(f"Expected numeric embeddings, got {vectors.dtype}")

    print(
        f"Validated shape/order contract: {vectors.shape[0]} rows, "
        f"dimension {vectors.shape[1]}, dtype {vectors.dtype}"
    )
    index = faiss.IndexFlatIP(vectors.shape[1])
    min_norm = float("inf")
    max_norm = 0.0
    zero_vectors = 0

    for start in range(0, vectors.shape[0], args.chunk_size):
        end = min(start + args.chunk_size, vectors.shape[0])
        # FAISS normalizes in place. Force a writable copy because mmap slices
        # can remain read-only even after ascontiguousarray when already float32.
        chunk = np.array(
            vectors[start:end], dtype=np.float32, order="C", copy=True
        )
        if not np.isfinite(chunk).all():
            bad = np.argwhere(~np.isfinite(chunk))[0]
            raise RuntimeError(
                f"Non-finite embedding value at row {start + int(bad[0])}, "
                f"column {int(bad[1])}"
            )
        norms = np.linalg.norm(chunk, axis=1)
        batch_zero_vectors = int(np.count_nonzero(norms == 0))
        zero_vectors += batch_zero_vectors
        if batch_zero_vectors and not args.allow_zero_vectors:
            row = start + int(np.flatnonzero(norms == 0)[0])
            raise RuntimeError(f"Zero-length embedding at row {row}")
        nonzero_norms = norms[norms != 0]
        if len(nonzero_norms):
            min_norm = min(min_norm, float(nonzero_norms.min()))
        max_norm = max(max_norm, float(norms.max()))

        # Unit vectors + inner product are exactly cosine similarity.
        faiss.normalize_L2(chunk)
        index.add(chunk)
        print(f"Indexed {end}/{vectors.shape[0]}", end="\r", flush=True)

    if index.ntotal != len(metadata):
        raise RuntimeError(
            f"Index count mismatch: {index.ntotal} vectors for {len(metadata)} rows"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    building_path = output_path.with_suffix(output_path.suffix + ".building")
    faiss.write_index(index, str(building_path))
    check = faiss.read_index(str(building_path))
    if check.ntotal != len(metadata) or check.d != vectors.shape[1]:
        raise RuntimeError("Written FAISS index failed read-back validation")
    os.replace(building_path, output_path)

    size_gib = output_path.stat().st_size / (1024**3)
    print()
    print(f"Input norm range before normalization: {min_norm:.6f}..{max_norm:.6f}")
    print(f"Intentional zero vectors preserved: {zero_vectors}")
    print(
        f"Wrote validated index: {output_path} "
        f"({check.ntotal} x {check.d}, {size_gib:.2f} GiB)"
    )


if __name__ == "__main__":
    main()
