"""Create tiny, non-destructive placeholders for the 28 embedding shards."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "manifests" / "aic-2026" / "index.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "embedding" / "shards"
DIMENSION = 4096


def main() -> None:
    index = json.loads(INDEX_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    preserved = 0
    for shard in index["shards"]:
        path = OUTPUT_DIR / f"{shard['shard_id']}.npy"
        if path.exists():
            # Never overwrite a downloaded or partially downloaded shard.
            array = np.load(path, mmap_mode="r", allow_pickle=False)
            if array.shape[0] == 0 and array.shape != (0, DIMENSION):
                np.save(path, np.empty((0, DIMENSION), dtype=np.float32))
                print(f"UPDATE   {path.name}: shape=(0, {DIMENSION}), dtype=float32")
                created += 1
                continue
            print(f"PRESERVE {path.name}: shape={array.shape}, dtype={array.dtype}")
            preserved += 1
            continue
        np.save(path, np.empty((0, DIMENSION), dtype=np.float32))
        print(f"CREATE   {path.name}: shape=(0, {DIMENSION}), dtype=float32")
        created += 1

    print(f"Ready: {created} created, {preserved} preserved, {len(index['shards'])} total")


if __name__ == "__main__":
    main()
