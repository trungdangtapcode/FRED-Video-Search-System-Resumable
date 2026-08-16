from __future__ import annotations

import fcntl
import json
import math
import os
import shutil
import socket
import tempfile
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


MANIFEST_VERSION = 1
SUPPORTED_VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4", ".webm"}


@dataclass(frozen=True)
class ExtractionJob:
    video_path: str
    output_root: str
    metadata_dir: str
    status_dir: str
    interval: float = 2.0
    force: bool = False

    @property
    def video_id(self) -> str:
        return Path(self.video_path).stem

    @property
    def output_dir(self) -> Path:
        return Path(self.output_root) / self.video_id

    @property
    def metadata_path(self) -> Path:
        return Path(self.metadata_dir) / f"{self.video_id}.json"

    @property
    def status_path(self) -> Path:
        return Path(self.status_dir) / f"{self.video_id}.done.json"


@dataclass(frozen=True)
class ExtractionResult:
    video_id: str
    status: str
    frame_count: int = 0
    message: str = ""


def discover_videos(
    input_dir: Path,
    selected_videos: Sequence[str] | None = None,
    start: int = 0,
    limit: int | None = None,
) -> list[Path]:
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if start < 0:
        raise ValueError("start must be zero or greater")
    if limit is not None and limit < 1:
        raise ValueError("limit must be greater than zero")

    videos = sorted(
        (
            path.resolve()
            for path in input_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ),
        key=lambda path: path.name,
    )

    duplicate_ids = _duplicates(path.stem for path in videos)
    if duplicate_ids:
        names = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"Video filenames must have unique stems; duplicates: {names}")

    if selected_videos:
        requested = {Path(value).stem for value in selected_videos}
        available = {path.stem for path in videos}
        missing = requested - available
        if missing:
            raise ValueError(f"Videos not found: {', '.join(sorted(missing))}")
        videos = [path for path in videos if path.stem in requested]

    end = None if limit is None else start + limit
    return videos[start:end]


def load_video_manifest(path: Path) -> tuple[list[str], float | None]:
    """Load video IDs and the optional extraction interval from a shard manifest."""
    try:
        with path.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read manifest {path}: {error}") from error

    if not isinstance(manifest, dict):
        raise ValueError(f"Manifest must contain a JSON object: {path}")

    entries = manifest.get("videos")
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"Manifest must contain a non-empty 'videos' list: {path}")

    video_ids: list[str] = []
    for index, entry in enumerate(entries):
        if isinstance(entry, str):
            video_id = Path(entry).stem
        elif isinstance(entry, dict):
            value = entry.get("video_id") or entry.get("filename")
            if not isinstance(value, str):
                raise ValueError(
                    f"Manifest video entry {index} needs 'video_id' or 'filename'"
                )
            video_id = Path(value).stem
        else:
            raise ValueError(f"Manifest video entry {index} has an invalid type")

        if not video_id:
            raise ValueError(f"Manifest video entry {index} has an empty ID")
        video_ids.append(video_id)

    duplicates = _duplicates(video_ids)
    if duplicates:
        raise ValueError(
            "Manifest contains duplicate video IDs: " + ", ".join(sorted(duplicates))
        )

    interval = manifest.get("interval_seconds")
    if interval is None:
        return video_ids, None
    try:
        interval = float(interval)
    except (TypeError, ValueError) as error:
        raise ValueError("Manifest interval_seconds must be a number") from error
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("Manifest interval_seconds must be a positive number")
    return video_ids, interval


def build_jobs(
    videos: Iterable[Path],
    output_root: Path,
    metadata_dir: Path,
    status_dir: Path,
    interval: float,
    force: bool,
) -> list[ExtractionJob]:
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("interval must be a positive number")

    return [
        ExtractionJob(
            video_path=str(video.resolve()),
            output_root=str(output_root.resolve()),
            metadata_dir=str(metadata_dir.resolve()),
            status_dir=str(status_dir.resolve()),
            interval=interval,
            force=force,
        )
        for video in videos
    ]


def run_jobs(jobs: Sequence[ExtractionJob], workers: int) -> list[ExtractionResult]:
    if workers < 1:
        raise ValueError("workers must be greater than zero")
    if not jobs:
        return []
    if workers == 1:
        return [extract_video_job(job) for job in jobs]

    results: list[ExtractionResult] = []
    worker_count = min(workers, len(jobs), os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(extract_video_job, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                results.append(future.result())
            except Exception as error:
                results.append(
                    ExtractionResult(job.video_id, "failed", message=str(error))
                )
    return sorted(results, key=lambda result: result.video_id)


def extract_video_job(job: ExtractionJob) -> ExtractionResult:
    video_path = Path(job.video_path)
    if not video_path.is_file():
        return ExtractionResult(job.video_id, "failed", message="source video missing")

    for directory in (
        Path(job.output_root),
        Path(job.metadata_dir),
        Path(job.status_dir),
    ):
        directory.mkdir(parents=True, exist_ok=True)

    lock_dir = Path(job.status_dir) / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{job.video_id}.lock"

    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return ExtractionResult(
                job.video_id,
                "locked",
                message="another process is extracting this video",
            )

        lock_file.seek(0)
        lock_file.truncate()
        json.dump(
            {"pid": os.getpid(), "host": socket.gethostname()},
            lock_file,
        )
        lock_file.flush()

        if not job.force:
            completed, frame_count = validate_completed_job(job)
            if completed:
                return ExtractionResult(job.video_id, "skipped", frame_count)

        try:
            frame_count = _extract_and_commit(job)
            return ExtractionResult(job.video_id, "completed", frame_count)
        except Exception as error:
            return ExtractionResult(job.video_id, "failed", message=str(error))


def validate_completed_job(job: ExtractionJob) -> tuple[bool, int]:
    try:
        with job.status_path.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
        if manifest.get("version") != MANIFEST_VERSION:
            return False, 0
        if manifest.get("video_id") != job.video_id:
            return False, 0
        if not math.isclose(
            float(manifest.get("interval_seconds")), job.interval, rel_tol=0, abs_tol=1e-9
        ):
            return False, 0
        if manifest.get("source") != _source_signature(Path(job.video_path)):
            return False, 0

        frame_count = int(manifest.get("frame_count", -1))
        if frame_count < 1 or not job.output_dir.is_dir():
            return False, 0

        frames = sorted(job.output_dir.glob("*.png"))
        if len(frames) != frame_count:
            return False, 0
        if any(path.stat().st_size == 0 for path in frames):
            return False, 0
        if any(path.name != f"{index:05d}.png" for index, path in enumerate(frames)):
            return False, 0

        with job.metadata_path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)
        if not isinstance(metadata, list) or len(metadata) != frame_count:
            return False, 0
        return True, frame_count
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False, 0


def merge_completed_metadata(
    metadata_dir: Path,
    status_dir: Path,
    output_path: Path,
) -> tuple[int, int, list[float]]:
    merged: list[dict] = []
    video_count = 0
    intervals: set[float] = set()

    for status_path in sorted(status_dir.glob("*.done.json")):
        try:
            with status_path.open("r", encoding="utf-8") as file:
                manifest = json.load(file)
            if manifest.get("version") != MANIFEST_VERSION:
                continue
            metadata_path = metadata_dir / f"{manifest['video_id']}.json"
            with metadata_path.open("r", encoding="utf-8") as file:
                video_metadata = json.load(file)
            if not isinstance(video_metadata, list):
                continue
            if len(video_metadata) != int(manifest["frame_count"]):
                continue
            merged.extend(video_metadata)
            video_count += 1
            intervals.add(float(manifest["interval_seconds"]))
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            continue

    _atomic_write_json(output_path, merged)
    return video_count, len(merged), sorted(intervals)


def write_success_marker(path: Path, summary: dict[str, object]) -> None:
    marker = {
        "version": MANIFEST_VERSION,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **summary,
    }
    _atomic_write_json(path, marker)


def _extract_and_commit(job: ExtractionJob) -> int:
    import cv2

    cv2.setNumThreads(1)
    video_path = Path(job.video_path)
    source_signature = _source_signature(video_path)
    output_root = Path(job.output_root)
    partial_root = output_root / ".partial"
    backup_root = output_root / ".backup"
    partial_root.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=True)

    _remove_matching_directories(partial_root, f"{job.video_id}.*")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{job.video_id}.", dir=partial_root))
    final_dir = job.output_dir
    backup_dir: Path | None = None
    installed_output = False

    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise RuntimeError(f"cannot open video: {video_path}")

        fps = float(capture.get(cv2.CAP_PROP_FPS))
        reported_total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not math.isfinite(fps) or fps <= 0:
            raise RuntimeError(f"invalid FPS reported for {video_path.name}: {fps}")

        frame_interval = max(1, int(round(fps * job.interval)))
        frame_index = 0
        saved_count = 0
        metadata: list[dict] = []
        final_dir_absolute = final_dir.resolve()
        video_path_absolute = video_path.resolve()

        while True:
            success, frame = capture.read()
            if not success:
                break
            if frame_index % frame_interval == 0:
                filename = f"{saved_count:05d}.png"
                temp_path = temp_dir / filename
                if not cv2.imwrite(str(temp_path), frame):
                    raise RuntimeError(f"failed to write frame: {temp_path}")
                metadata.append(
                    {
                        "video_path": str(video_path_absolute),
                        "fps": fps,
                        "timestamp": frame_index / fps,
                        "frame_idx": frame_index,
                        "frame_path": str(final_dir_absolute / filename),
                    }
                )
                saved_count += 1
            frame_index += 1
    finally:
        capture.release()

    if saved_count == 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"no frames decoded from {video_path.name}")

    tolerance = max(frame_interval, int(round(fps * 5)))
    if reported_total_frames > 0 and frame_index + tolerance < reported_total_frames:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(
            f"decoder stopped early at frame {frame_index}/{reported_total_frames}"
        )
    if _source_signature(video_path) != source_signature:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"source video changed during extraction: {video_path.name}")

    manifest = {
        "version": MANIFEST_VERSION,
        "video_id": job.video_id,
        "source": source_signature,
        "interval_seconds": job.interval,
        "fps": fps,
        "frame_interval": frame_interval,
        "decoded_frames": frame_index,
        "reported_total_frames": reported_total_frames,
        "frame_count": saved_count,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        job.status_path.unlink(missing_ok=True)
        if final_dir.exists():
            backup_dir = backup_root / f"{job.video_id}.{uuid.uuid4().hex}"
            os.replace(final_dir, backup_dir)
        os.replace(temp_dir, final_dir)
        installed_output = True
        _atomic_write_json(job.metadata_path, metadata)
        _atomic_write_json(job.status_path, manifest)
    except BaseException:
        if installed_output and final_dir.exists():
            shutil.rmtree(final_dir, ignore_errors=True)
        if backup_dir is not None and backup_dir.exists():
            os.replace(backup_dir, final_dir)
        raise

    if backup_dir is not None:
        shutil.rmtree(backup_dir, ignore_errors=True)
    return saved_count


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _source_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _remove_matching_directories(parent: Path, pattern: str) -> None:
    for path in parent.glob(pattern):
        if path.is_dir():
            shutil.rmtree(path)


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def result_as_dict(result: ExtractionResult) -> dict[str, object]:
    return asdict(result)
