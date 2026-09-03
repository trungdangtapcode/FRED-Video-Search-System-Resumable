from __future__ import annotations

import argparse
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class DatasetFile:
    name: str
    size: int


_worker = threading.local()
_worker_contexts: list[object] = []
_worker_contexts_lock = threading.Lock()
_request_slot_lock = threading.Lock()
_next_request_at = 0.0


def _safe_target(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"Unsafe dataset file path: {name!r}")
    target = root.joinpath(*relative.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Dataset file escapes output directory: {name!r}")
    return target


def list_dataset_files(dataset: str) -> list[DatasetFile]:
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as error:
        raise RuntimeError("Install the official Kaggle CLI package first: pip install kaggle") from error

    api = KaggleApi()
    files: list[DatasetFile] = []
    page_token: str | None = None
    while True:
        response = api.dataset_list_files(dataset, page_token=page_token, page_size=200)
        for item in response.files or []:
            name = str(item.name)
            size = int(item.total_bytes)
            if size < 0:
                raise ValueError(f"Invalid size for {name!r}: {size}")
            files.append(DatasetFile(name=name, size=size))
        page_token = response.next_page_token or None
        if page_token is None:
            break

    names = [item.name for item in files]
    if not files or len(names) != len(set(names)):
        raise ValueError("Dataset file listing is empty or contains duplicate paths")
    return files


def _initialize_worker() -> None:
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    context = api.build_kaggle_client()
    client = context.__enter__()
    _worker.api = api
    _worker.client = client
    with _worker_contexts_lock:
        _worker_contexts.append(context)


def _wait_for_request_slot(interval: float) -> None:
    global _next_request_at
    if interval <= 0:
        return
    with _request_slot_lock:
        now = time.monotonic()
        delay = max(0.0, _next_request_at - now)
        _next_request_at = max(now, _next_request_at) + interval
    if delay:
        time.sleep(delay)


def _download_one(
    owner: str,
    slug: str,
    version: str | None,
    item: DatasetFile,
    output_dir: Path,
    retries: int,
    request_interval: float,
) -> tuple[str, int, bool]:
    from kaggle.api.kaggle_api_extended import ApiDownloadDatasetRequest

    target = _safe_target(output_dir, item.name)
    if target.is_file() and target.stat().st_size == item.size:
        return item.name, item.size, False

    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries + 1):
        try:
            request = ApiDownloadDatasetRequest()
            request.owner_slug = owner
            request.dataset_slug = slug
            request.dataset_version_number = int(version) if version else None
            request.file_name = item.name
            _wait_for_request_slot(request_interval)
            response = _worker.client.datasets.dataset_api_client.download_dataset(request)
            _worker.api.download_file(
                response,
                str(target),
                _worker.client.http_client(),
                quiet=True,
                resume=True,
            )
            actual_size = target.stat().st_size
            if actual_size != item.size:
                raise ValueError(
                    f"Size mismatch for {item.name}: expected {item.size}, got {actual_size}"
                )
            return item.name, item.size, True
        except Exception:
            if attempt == retries:
                raise
            time.sleep(min(30, 2**attempt))

    raise AssertionError("unreachable")


def download_dataset_files(
    dataset: str,
    output_dir: Path,
    workers: int = 24,
    retries: int = 6,
    progress_every: int = 100,
    request_interval: float = 0.0,
) -> dict[str, int | str]:
    parts = dataset.split("/")
    if len(parts) not in (2, 3) or not parts[0] or not parts[1]:
        raise ValueError("Dataset must be OWNER/SLUG or OWNER/SLUG/VERSION")
    owner, slug = parts[:2]
    version = parts[2] if len(parts) == 3 else None
    if workers < 1 or retries < 0 or progress_every < 1 or request_interval < 0:
        raise ValueError(
            "workers/progress-every must be positive; retries/request-interval cannot be negative"
        )

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = list_dataset_files(dataset)
    for item in files:
        _safe_target(output_dir, item.name)

    total_bytes = sum(item.size for item in files)
    print(f"FILES count={len(files)} bytes={total_bytes}", flush=True)
    completed = downloaded = completed_bytes = 0
    executor = ThreadPoolExecutor(max_workers=workers, initializer=_initialize_worker)
    try:
        futures = {
            executor.submit(
                _download_one,
                owner,
                slug,
                version,
                item,
                output_dir,
                retries,
                request_interval,
            ): item
            for item in files
        }
        for future in as_completed(futures):
            _, size, was_downloaded = future.result()
            completed += 1
            completed_bytes += size
            downloaded += int(was_downloaded)
            if completed % progress_every == 0 or completed == len(files):
                print(
                    f"PROGRESS files={completed}/{len(files)} bytes={completed_bytes}/{total_bytes}",
                    flush=True,
                )
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
        with _worker_contexts_lock:
            contexts = list(_worker_contexts)
            _worker_contexts.clear()
        for context in contexts:
            context.__exit__(None, None, None)

    return {
        "dataset": dataset,
        "file_count": len(files),
        "downloaded_file_count": downloaded,
        "total_bytes": total_bytes,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m keyframe_extraction.download_kaggle_files",
        description="Resumably download a Kaggle dataset file-by-file when its bundle is unavailable.",
    )
    parser.add_argument("dataset")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument(
        "--request-interval",
        type=float,
        default=0.0,
        help="minimum seconds between dataset signing requests across all workers",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = download_dataset_files(
            dataset=args.dataset,
            output_dir=args.output,
            workers=args.workers,
            retries=args.retries,
            progress_every=args.progress_every,
            request_interval=args.request_interval,
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
