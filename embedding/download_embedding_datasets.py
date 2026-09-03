"""Download only NPY files from embedding datasets and validate before install."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = PROJECT_ROOT / "manifests" / "aic-2026"
OUTPUT_DIR = PROJECT_ROOT / "data" / "embedding" / "shards"
TEMP_ROOT = PROJECT_ROOT / "data" / "embedding" / "run_shards"


def validate(path: Path, rows: int, dimension: int) -> tuple[float, float]:
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    if array.shape != (rows, dimension):
        raise RuntimeError(f"expected {(rows, dimension)}, got {array.shape}")
    if not np.issubdtype(array.dtype, np.floating):
        raise RuntimeError(f"expected floating dtype, got {array.dtype}")
    min_norm = float("inf")
    max_norm = 0.0
    for start in range(0, rows, 2048):
        chunk = np.asarray(array[start : start + 2048], dtype=np.float32)
        if not np.isfinite(chunk).all():
            raise RuntimeError(f"non-finite value near row {start}")
        norms = np.linalg.norm(chunk, axis=1)
        if np.any(norms == 0):
            raise RuntimeError(f"zero vector near row {start}")
        min_norm = min(min_norm, float(norms.min()))
        max_norm = max(max_norm, float(norms.max()))
    return min_norm, max_norm


def main() -> None:
    manifest = json.loads((MANIFEST_ROOT / "embedding-shards.json").read_text())
    dimension = int(manifest["dimension"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for item in manifest["shards"]:
        if item["status"] != "done":
            continue
        shard_id = item["shard_id"]
        dataset = item["dataset"]
        filename = f"{shard_id}.npy"
        destination = OUTPUT_DIR / filename
        marker = json.loads(
            (
                PROJECT_ROOT
                / "data"
                / "keyframe_import_status"
                / f"{shard_id}.done.json"
            ).read_text()
        )
        rows = int(marker["frame_count"])
        try:
            if destination.exists():
                current = np.load(destination, mmap_mode="r", allow_pickle=False)
                if current.shape == (rows, dimension):
                    try:
                        norms = validate(destination, rows, dimension)
                    except RuntimeError as exc:
                        print(f"REPLACE  {shard_id}: local array is invalid ({exc})")
                    else:
                        print(f"SKIP     {shard_id}: already valid, norms={norms}")
                        continue
            with tempfile.TemporaryDirectory(prefix=f".{shard_id}-", dir=TEMP_ROOT) as tmp:
                command = [
                    shutil.which("kaggle") or "kaggle",
                    "datasets",
                    "download",
                    dataset,
                    "-f",
                    filename,
                    "-p",
                    tmp,
                    "--unzip",
                    "--quiet",
                ]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode:
                    message = (result.stderr or result.stdout).strip()
                    raise RuntimeError(message)
                downloaded = Path(tmp) / filename
                if not downloaded.is_file():
                    raise RuntimeError(f"download did not produce {filename}")
                norms = validate(downloaded, rows, dimension)
                os.replace(downloaded, destination)
                print(f"INSTALL  {shard_id}: shape=({rows}, {dimension}), norms={norms}")
        except Exception as exc:
            errors.append(f"{shard_id} ({dataset}): {exc}")
            print(f"ERROR    {errors[-1]}")

    if errors:
        raise SystemExit("Unavailable/invalid DONE datasets:\n- " + "\n- ".join(errors))


if __name__ == "__main__":
    main()
