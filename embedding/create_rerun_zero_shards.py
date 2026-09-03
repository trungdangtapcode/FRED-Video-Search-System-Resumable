"""Create sparse, full-row zero NPYs for shards explicitly marked RERUN."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = PROJECT_ROOT / "manifests" / "aic-2026"
OUTPUT_DIR = PROJECT_ROOT / "data" / "embedding" / "shards"


def main() -> None:
    embedding_manifest = json.loads(
        (MANIFEST_ROOT / "embedding-shards.json").read_text()
    )
    dimension = int(embedding_manifest["dimension"])
    rerun_ids = {
        item["shard_id"]
        for item in embedding_manifest["shards"]
        if item["status"] == "rerun_zero"
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for shard_id in sorted(rerun_ids):
        marker = json.loads(
            (
                PROJECT_ROOT
                / "data"
                / "keyframe_import_status"
                / f"{shard_id}.done.json"
            ).read_text()
        )
        shape = (int(marker["frame_count"]), dimension)
        path = OUTPUT_DIR / f"{shard_id}.npy"
        if path.exists():
            current = np.load(path, mmap_mode="r", allow_pickle=False)
            if current.shape[0] != 0:
                print(f"PRESERVE {path.name}: existing shape={current.shape}")
                continue
        array = np.lib.format.open_memmap(
            path, mode="w+", dtype=np.float32, shape=shape
        )
        del array
        print(f"ZERO     {path.name}: shape={shape}, dtype=float32")


if __name__ == "__main__":
    main()
