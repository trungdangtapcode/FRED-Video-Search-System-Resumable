#!/usr/bin/env python3
"""Upload the AIC videos and extracted keyframes to R2 with bounded disk use.

The uploader deliberately keeps only one source ZIP on disk at a time.  Files
inside that ZIP are read directly and uploaded as individual repository-layout
objects.  A completed object is skipped when its R2 ContentLength matches the
source, so restarting the command is safe even without ListBucket permission.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import functools
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_ROOT = PROJECT_ROOT / "manifests" / "aic-2026"
DEFAULT_SOURCE_MANIFEST = MANIFEST_ROOT / "media-sources.json"
DEFAULT_STAGE_DIR = DATA_DIR / "r2_upload_stage"
DEFAULT_STATE_DIR = PROJECT_ROOT / ".runtime" / "r2_media_upload"
DEFAULT_MAX_TEMP_BYTES = 30_000_000_000
DEFAULT_PART_BYTES = 32 * 1024 * 1024

SHARD_RE = re.compile(r"^(L\d+)_p(\d+)$", re.IGNORECASE)
VIDEO_RE = re.compile(r"^(L\d+_V\d+)\.mp4$", re.IGNORECASE)
FRAME_RE = re.compile(r"^(L\d+_V\d+)/(\d{5})\.png$", re.IGNORECASE)

LOG = logging.getLogger("r2-media-upload")


def _load_botocore() -> tuple[object, type[Exception]]:
    """Use botocore from boto3 or the already-installed AWS CLI."""
    try:
        from botocore.config import Config  # type: ignore
        from botocore.exceptions import ClientError  # type: ignore
        from botocore.session import get_session  # type: ignore

        return (Config, ClientError, get_session)
    except ModuleNotFoundError:
        aws = shutil.which("aws")
        if not aws:
            raise RuntimeError("botocore is unavailable and aws is not installed")
        aws_root = Path(aws).resolve().parent.parent
        candidate = aws_root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if not candidate.is_dir():
            raise RuntimeError(f"cannot find AWS CLI botocore at {candidate}")
        sys.path.append(str(candidate))
        from botocore.config import Config  # type: ignore
        from botocore.exceptions import ClientError  # type: ignore
        from botocore.session import get_session  # type: ignore

        return (Config, ClientError, get_session)


Config, ClientError, get_session = _load_botocore()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def normalized_prefix(value: str) -> str:
    value = value.strip().strip("/")
    if not value or value in {".", ".."} or "//" in value:
        raise ValueError(f"invalid R2 prefix: {value!r}")
    return value


def read_nonblank_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]


@functools.lru_cache(maxsize=4)
def load_source_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text())
    if payload.get("version") != 1:
        raise RuntimeError(f"unsupported media source manifest version in {path}")
    if len(payload.get("video_archives", [])) != 14:
        raise RuntimeError(f"media source manifest must contain 14 video archives: {path}")
    if len(payload.get("media_info_archives", [])) != 1:
        raise RuntimeError(f"media source manifest must contain one media-info archive: {path}")
    if len(payload.get("keyframe_shards", [])) != 28:
        raise RuntimeError(f"media source manifest must contain 28 keyframe shards: {path}")
    return payload


def configured_video_urls(args: argparse.Namespace) -> list[str]:
    if args.video_urls:
        return read_nonblank_lines(Path(args.video_urls))
    payload = load_source_manifest(Path(args.source_manifest).resolve())
    return [entry["url"] for entry in payload["video_archives"] + payload["media_info_archives"]]


def configured_keyframe_datasets(args: argparse.Namespace) -> list[str]:
    if args.keyframe_urls:
        urls = read_nonblank_lines(Path(args.keyframe_urls))
        return [url.split("/datasets/", 1)[1].strip("/") for url in urls]
    payload = load_source_manifest(Path(args.source_manifest).resolve())
    return [entry["dataset"] for entry in payload["keyframe_shards"]]


def keyframe_source_entry(args: argparse.Namespace, shard_id: str) -> dict:
    payload = load_source_manifest(Path(args.source_manifest).resolve())
    matches = [entry for entry in payload["keyframe_shards"] if entry["shard_id"] == shard_id]
    if len(matches) != 1:
        raise RuntimeError(f"missing or duplicate source entry for {shard_id}")
    return matches[0]


def directory_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def ensure_stage_limit(stage_dir: Path, limit: int) -> None:
    used = directory_bytes(stage_dir)
    if used > limit:
        raise RuntimeError(f"temporary stage uses {used:,} bytes, above the {limit:,}-byte limit")


@dataclass(frozen=True)
class R2Settings:
    endpoint: str
    bucket: str
    access_key: str
    secret_key: str
    prefix: str
    workers: int

    @classmethod
    def from_env(cls, prefix: str, workers: int) -> "R2Settings":
        return cls(
            endpoint=require_env("R2_S3_CLIENT_URL"),
            bucket=require_env("R2_BUCKET"),
            access_key=require_env("R2_ACCESS_KEY_ID"),
            secret_key=require_env("R2_SECRET_ACCESS_KEY"),
            prefix=normalized_prefix(prefix),
            workers=workers,
        )

    def key(self, relative: str) -> str:
        relative = relative.lstrip("/")
        return f"{self.prefix}/{relative}"


class R2ClientPool:
    def __init__(self, settings: R2Settings):
        self.settings = settings
        self.local = threading.local()

    def get(self):
        client = getattr(self.local, "client", None)
        if client is None:
            session = get_session()
            client = session.create_client(
                "s3",
                endpoint_url=self.settings.endpoint,
                region_name="auto",
                aws_access_key_id=self.settings.access_key,
                aws_secret_access_key=self.settings.secret_key,
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 10, "mode": "standard"},
                    connect_timeout=30,
                    read_timeout=300,
                    max_pool_connections=max(16, self.settings.workers * 2),
                    s3={"addressing_style": "path"},
                ),
            )
            self.local.client = client
        return client

    def head(self, key: str) -> dict | None:
        try:
            return self.get().head_object(Bucket=self.settings.bucket, Key=key)
        except ClientError as exc:  # type: ignore[misc]
            response = getattr(exc, "response", {})
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = str(response.get("Error", {}).get("Code", ""))
            if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

    def matches(self, key: str, size: int) -> bool:
        head = self.head(key)
        return head is not None and int(head.get("ContentLength", -1)) == size

    def put_bytes(
        self,
        key: str,
        payload: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
        skip_matching: bool = True,
    ) -> str:
        size = len(payload)
        if skip_matching and self.matches(key, size):
            return "skipped"
        response = self.get().put_object(
            Bucket=self.settings.bucket,
            Key=key,
            Body=payload,
            ContentLength=size,
            ContentType=content_type,
            Metadata=metadata or {},
        )
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status not in {200, 201}:
            raise RuntimeError(f"R2 PUT returned HTTP {status} for {key}")
        if not self.matches(key, size):
            raise RuntimeError(f"R2 size verification failed for {key}")
        return "uploaded"

    def get_bytes(self, key: str) -> bytes:
        response = self.get().get_object(Bucket=self.settings.bucket, Key=key)
        expected = int(response.get("ContentLength", -1))
        body = response["Body"]
        try:
            payload = body.read()
        finally:
            body.close()
        if expected >= 0 and len(payload) != expected:
            raise RuntimeError(
                f"R2 read size mismatch for {key}: expected {expected:,}, got {len(payload):,}"
            )
        return payload

    def put_stream_multipart(
        self,
        key: str,
        stream: BinaryIO,
        expected_size: int,
        content_type: str,
        metadata: dict[str, str],
        part_bytes: int,
    ) -> str:
        if self.matches(key, expected_size):
            return "skipped"

        client = self.get()
        created = client.create_multipart_upload(
            Bucket=self.settings.bucket,
            Key=key,
            ContentType=content_type,
            Metadata=metadata,
        )
        upload_id = created["UploadId"]
        parts: list[dict[str, object]] = []
        total = 0
        part_number = 1
        try:
            while True:
                block = stream.read(part_bytes)
                if not block:
                    break
                total += len(block)
                uploaded = client.upload_part(
                    Bucket=self.settings.bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=block,
                    ContentLength=len(block),
                )
                parts.append({"ETag": uploaded["ETag"], "PartNumber": part_number})
                part_number += 1
            if total != expected_size:
                raise RuntimeError(f"source size mismatch for {key}: expected {expected_size:,}, read {total:,}")
            if not parts:
                client.abort_multipart_upload(
                    Bucket=self.settings.bucket, Key=key, UploadId=upload_id
                )
                return self.put_bytes(key, b"", content_type, metadata, skip_matching=False)
            response = client.complete_multipart_upload(
                Bucket=self.settings.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status not in {200, 201}:
                raise RuntimeError(f"R2 multipart completion returned HTTP {status} for {key}")
        except BaseException:
            with contextlib.suppress(Exception):
                client.abort_multipart_upload(
                    Bucket=self.settings.bucket, Key=key, UploadId=upload_id
                )
            raise
        if not self.matches(key, expected_size):
            raise RuntimeError(f"R2 size verification failed for {key}")
        return "uploaded"


def download_http_file(url: str, destination: Path, max_temp_bytes: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    head = requests.head(url, allow_redirects=True, timeout=60)
    head.raise_for_status()
    expected = int(head.headers.get("Content-Length", "0"))
    if not expected:
        raise RuntimeError(f"source did not provide Content-Length: {url}")
    other_usage = directory_bytes(destination.parent) - (destination.stat().st_size if destination.exists() else 0)
    if other_usage + expected > max_temp_bytes:
        raise RuntimeError(
            f"downloading {destination.name} would exceed the temporary limit: "
            f"{other_usage + expected:,} > {max_temp_bytes:,} bytes"
        )
    if destination.exists() and destination.stat().st_size == expected:
        LOG.info("source archive already complete: %s (%s bytes)", destination.name, f"{expected:,}")
        return
    if destination.exists() and destination.stat().st_size > expected:
        destination.unlink()
    LOG.info("downloading %s (%s bytes)", destination.name, f"{expected:,}")
    subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--retry",
            "8",
            "--retry-delay",
            "5",
            "--retry-all-errors",
            "--silent",
            "--show-error",
            "--continue-at",
            "-",
            "--output",
            str(destination),
            url,
        ],
        check=True,
    )
    actual = destination.stat().st_size
    if actual != expected:
        raise RuntimeError(f"downloaded size mismatch for {destination}: expected {expected:,}, got {actual:,}")


def download_kaggle_dataset(dataset: str, stage_dir: Path, max_temp_bytes: int) -> Path:
    slug = dataset.split("/", 1)[1]
    destination = stage_dir / f"{slug}.zip"
    LOG.info("downloading Kaggle dataset %s", dataset)
    subprocess.run(
        ["kaggle", "datasets", "download", dataset, "--path", str(stage_dir), "--quiet"],
        check=True,
    )
    if not destination.is_file():
        candidates = sorted(stage_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
        if len(candidates) != 1:
            raise RuntimeError(f"cannot identify Kaggle ZIP for {dataset} in {stage_dir}")
        destination = candidates[0]
    ensure_stage_limit(stage_dir, max_temp_bytes)
    LOG.info("Kaggle archive ready: %s (%s bytes)", destination.name, f"{destination.stat().st_size:,}")
    return destination


def manifest_bytes(records: Iterable[dict]) -> bytes:
    return b"".join(
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for record in records
    )


def write_local_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def upload_manifest(pool: R2ClientPool, key: str, records: list[dict]) -> None:
    pool.put_bytes(
        key,
        manifest_bytes(records),
        "application/x-ndjson",
        {"record-count": str(len(records))},
        skip_matching=False,
    )


def download_manifest(pool: R2ClientPool, key: str) -> list[dict]:
    payload = pool.get_bytes(key)
    records: list[dict] = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict) or not isinstance(record.get("key"), str):
            raise RuntimeError(f"invalid record {number} in R2 manifest {key}")
        if not isinstance(record.get("size"), int) or record["size"] < 0:
            raise RuntimeError(f"invalid size in record {number} of R2 manifest {key}")
        records.append(record)
    if not records:
        raise RuntimeError(f"R2 manifest is empty: {key}")
    return records


def recovered_video_summary(
    pool: R2ClientPool,
    manifest_key: str,
    archive_name: str,
    expected_videos: set[str],
) -> dict | None:
    if pool.head(manifest_key) is None:
        return None
    records = download_manifest(pool, manifest_key)
    video_ids: set[str] = set()
    is_video_archive = archive_name.startswith("Videos_")
    required_prefix = pool.settings.key(
        "data/unzipped/video/" if is_video_archive else "data/unzipped/media-info/"
    )
    for record in records:
        key = record["key"]
        if not key.startswith(required_prefix):
            raise RuntimeError(f"unexpected key in {manifest_key}: {key}")
        if is_video_archive:
            filename = PurePosixPath(key).name
            match = VIDEO_RE.fullmatch(filename)
            if not match:
                raise RuntimeError(f"invalid video key in {manifest_key}: {key}")
            video_id = match.group(1).upper()
            if video_id not in expected_videos or video_id in video_ids:
                raise RuntimeError(f"unexpected or duplicate video in {manifest_key}: {video_id}")
            video_ids.add(video_id)
    if not is_video_archive and len(records) != 873:
        raise RuntimeError(f"media-info manifest count mismatch: {len(records)} != 873")
    return {
        "archive": archive_name,
        "completed_at": utc_now(),
        "manifest_key": manifest_key,
        "object_count": len(records),
        "total_bytes": sum(record["size"] for record in records),
        "video_ids": sorted(video_ids),
        "recovered_from_r2": True,
    }


def recovered_keyframe_summary(
    args: argparse.Namespace,
    pool: R2ClientPool,
    manifest_key: str,
    dataset: str,
    shard_id: str,
) -> dict | None:
    if pool.head(manifest_key) is None:
        return None
    records = download_manifest(pool, manifest_key)
    source_entry = keyframe_source_entry(args, shard_id)
    expected_count = int(source_entry["frame_count"])
    if len(records) != expected_count:
        raise RuntimeError(
            f"R2 manifest count mismatch for {shard_id}: {len(records):,} != {expected_count:,}"
        )
    required_prefix = pool.settings.key("data/extracted_keyframes/")
    destinations: set[str] = set()
    for record in records:
        key = record["key"]
        if not key.startswith(required_prefix):
            raise RuntimeError(f"unexpected key in {manifest_key}: {key}")
        relative = key[len(required_prefix) :]
        if not FRAME_RE.fullmatch(relative) or key in destinations:
            raise RuntimeError(f"invalid or duplicate key in {manifest_key}: {key}")
        destinations.add(key)
    manifest = json.loads(shard_manifest_path(shard_id).read_text())
    return {
        "shard_id": shard_id,
        "dataset": dataset,
        "completed_at": utc_now(),
        "manifest_key": manifest_key,
        "object_count": len(records),
        "total_bytes": sum(record["size"] for record in records),
        "video_count": len(manifest["videos"]),
        "recovered_from_r2": True,
    }


def load_expected_videos() -> set[str]:
    expected: set[str] = set()
    for path in sorted(MANIFEST_ROOT.glob("L*/part-*.json")):
        payload = json.loads(path.read_text())
        for video in payload["videos"]:
            video_id = str(video["video_id"])
            if video_id in expected:
                raise RuntimeError(f"duplicate video in shard manifests: {video_id}")
            expected.add(video_id)
    if len(expected) != 873:
        raise RuntimeError(f"expected 873 unique videos, found {len(expected)}")
    return expected


def video_entries(archive: Path, expected_videos: set[str]) -> list[tuple[zipfile.ZipInfo, str, str]]:
    entries: list[tuple[zipfile.ZipInfo, str, str]] = []
    seen: set[str] = set()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            filename = PurePosixPath(info.filename).name
            match = VIDEO_RE.fullmatch(filename)
            if not match:
                continue
            video_id = match.group(1).upper()
            if video_id not in expected_videos:
                raise RuntimeError(f"unexpected video in {archive.name}: {info.filename}")
            if video_id in seen:
                raise RuntimeError(f"duplicate video in {archive.name}: {video_id}")
            seen.add(video_id)
            entries.append((info, video_id, filename))
    if not entries:
        raise RuntimeError(f"no MP4 files found in {archive}")
    return sorted(entries, key=lambda item: item[1])


def media_info_entries(archive: Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(archive) as zf:
        entries = [info for info in zf.infolist() if not info.is_dir() and info.filename.lower().endswith(".json")]
    if not entries:
        raise RuntimeError(f"no media-info JSON files found in {archive}")
    names = [PurePosixPath(info.filename).name for info in entries]
    if len(names) != len(set(names)):
        raise RuntimeError(f"duplicate media-info basenames in {archive}")
    return sorted(entries, key=lambda info: PurePosixPath(info.filename).name)


def upload_video_archive(
    archive: Path,
    source_url: str,
    pool: R2ClientPool,
    expected_videos: set[str],
    part_bytes: int,
) -> tuple[list[dict], set[str]]:
    entries = video_entries(archive, expected_videos)
    records: list[dict] = []
    found: set[str] = set()
    LOG.info("validated %s: %d video members", archive.name, len(entries))
    with zipfile.ZipFile(archive) as zf:
        for number, (info, video_id, filename) in enumerate(entries, 1):
            key = pool.settings.key(f"data/unzipped/video/{filename}")
            with zf.open(info, "r") as source:
                result = pool.put_stream_multipart(
                    key,
                    source,
                    info.file_size,
                    "video/mp4",
                    {
                        "source-archive": archive.name,
                        "source-crc32": f"{info.CRC:08x}",
                    },
                    part_bytes,
                )
            found.add(video_id)
            records.append(
                {
                    "key": key,
                    "size": info.file_size,
                    "source": source_url,
                    "source_member": info.filename,
                    "crc32": f"{info.CRC:08x}",
                }
            )
            LOG.info("video %d/%d %s %s (%s bytes)", number, len(entries), result, video_id, f"{info.file_size:,}")
    return records, found


def upload_media_info_archive(archive: Path, source_url: str, pool: R2ClientPool) -> list[dict]:
    entries = media_info_entries(archive)
    records: list[dict] = []
    LOG.info("validated %s: %d media-info members", archive.name, len(entries))
    with zipfile.ZipFile(archive) as zf:
        for number, info in enumerate(entries, 1):
            filename = PurePosixPath(info.filename).name
            key = pool.settings.key(f"data/unzipped/media-info/{filename}")
            payload = zf.read(info)
            result = pool.put_bytes(
                key,
                payload,
                "application/json",
                {"source-archive": archive.name, "source-crc32": f"{info.CRC:08x}"},
            )
            records.append(
                {
                    "key": key,
                    "size": info.file_size,
                    "source": source_url,
                    "source_member": info.filename,
                    "crc32": f"{info.CRC:08x}",
                }
            )
            if number % 100 == 0 or number == len(entries):
                LOG.info("media-info %d/%d last=%s %s", number, len(entries), filename, result)
    return records


def run_videos(
    args: argparse.Namespace,
    pool: R2ClientPool,
    stage_dir: Path,
    state_dir: Path,
) -> dict:
    urls = configured_video_urls(args)
    expected_videos = load_expected_videos()
    found_videos: set[str] = set()
    archive_summaries: list[dict] = []

    for url in urls:
        name = PurePosixPath(urllib.parse.urlparse(url).path).name
        if not (name.startswith("Videos_") or name.startswith("media-info")):
            raise RuntimeError(f"unexpected source archive name: {name}")
        if args.only_archive and name != args.only_archive:
            continue
        kind = "videos" if name.startswith("Videos_") else "media-info"
        state_path = state_dir / "videos" / f"{name}.done.json"
        manifest_key = pool.settings.key(f"manifests/{kind}/{name}.jsonl")
        if state_path.is_file():
            completed = json.loads(state_path.read_text())
            if str(completed["manifest_key"]) == manifest_key and pool.head(manifest_key) is not None:
                archive_summaries.append(completed)
                found_videos.update(completed.get("video_ids", []))
                LOG.info("completed checkpoint verified; skipping source archive %s", name)
                continue
            LOG.warning("local checkpoint exists but R2 manifest is absent; reprocessing %s", name)
        recovered = recovered_video_summary(pool, manifest_key, name, expected_videos)
        if recovered is not None:
            write_local_json(state_path, recovered)
            archive_summaries.append(recovered)
            found_videos.update(recovered["video_ids"])
            LOG.info("remote worker manifest verified; skipping source archive %s", name)
            continue
        archive = stage_dir / name
        download_http_file(url, archive, args.max_temp_bytes)
        if name.startswith("Videos_"):
            records, video_ids = upload_video_archive(
                archive, url, pool, expected_videos, args.video_part_bytes
            )
            found_videos.update(video_ids)
        else:
            records = upload_media_info_archive(archive, url, pool)
            video_ids = set()
        upload_manifest(pool, manifest_key, records)
        summary = {
            "archive": name,
            "completed_at": utc_now(),
            "manifest_key": manifest_key,
            "object_count": len(records),
            "total_bytes": sum(record["size"] for record in records),
            "video_ids": sorted(video_ids),
        }
        write_local_json(state_path, summary)
        archive_summaries.append(summary)
        archive.unlink()
        LOG.info("completed and removed temporary archive %s", name)
        ensure_stage_limit(stage_dir, args.max_temp_bytes)

    if not args.only_archive:
        if found_videos != expected_videos:
            missing = sorted(expected_videos - found_videos)
            extra = sorted(found_videos - expected_videos)
            raise RuntimeError(f"video coverage mismatch: missing={missing}, extra={extra}")
        LOG.info("video coverage verified: %d/%d", len(found_videos), len(expected_videos))
    return {
        "archive_count": len(archive_summaries),
        "video_count": len(found_videos),
        "archives": archive_summaries,
    }


def shard_from_dataset(dataset: str) -> str:
    slug = dataset.rstrip("/").split("/")[-1]
    match = re.search(r"aic-keyframes-(l\d+)-p(\d+)-output$", slug, re.IGNORECASE)
    if not match:
        raise RuntimeError(f"cannot derive shard ID from Kaggle dataset: {dataset}")
    return f"{match.group(1).upper()}_p{int(match.group(2)):02d}"


def shard_manifest_path(shard_id: str) -> Path:
    match = SHARD_RE.fullmatch(shard_id)
    if not match:
        raise ValueError(f"invalid shard ID: {shard_id}")
    return MANIFEST_ROOT / match.group(1).upper() / f"part-{int(match.group(2)):03d}.json"


def keyframe_entries(
    args: argparse.Namespace,
    archive: Path,
    shard_id: str,
) -> tuple[list[tuple[str, str, int, int]], int, set[str]]:
    manifest = json.loads(shard_manifest_path(shard_id).read_text())
    expected_videos = {str(video["video_id"]) for video in manifest["videos"]}
    source_entry = keyframe_source_entry(args, shard_id)
    expected_count = int(source_entry["frame_count"])
    entries: list[tuple[str, str, int, int]] = []
    destinations: set[str] = set()
    found_videos: set[str] = set()

    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".png"):
                continue
            parts = PurePosixPath(info.filename).parts
            try:
                marker = parts.index("extracted_keyframes")
            except ValueError:
                raise RuntimeError(f"PNG outside extracted_keyframes in {archive.name}: {info.filename}")
            relative = "/".join(parts[marker + 1 :])
            match = FRAME_RE.fullmatch(relative)
            if not match:
                raise RuntimeError(f"invalid keyframe path in {archive.name}: {info.filename}")
            video_id = match.group(1).upper()
            if video_id not in expected_videos:
                raise RuntimeError(f"keyframe belongs to unexpected video in {shard_id}: {info.filename}")
            if relative in destinations:
                raise RuntimeError(f"duplicate keyframe destination in {archive.name}: {relative}")
            destinations.add(relative)
            found_videos.add(video_id)
            entries.append((info.filename, relative, info.file_size, info.CRC))

    if len(entries) != expected_count:
        raise RuntimeError(
            f"{shard_id} frame count mismatch: archive={len(entries):,}, expected={expected_count:,}"
        )
    if found_videos != expected_videos:
        raise RuntimeError(
            f"{shard_id} video coverage mismatch: missing={sorted(expected_videos - found_videos)}"
        )
    return sorted(entries, key=lambda item: item[1]), expected_count, expected_videos


class KeyframeWorker:
    def __init__(self, archive: Path, dataset: str, pool: R2ClientPool):
        self.archive = archive
        self.dataset = dataset
        self.pool = pool
        self.local = threading.local()

    def zip_file(self) -> zipfile.ZipFile:
        zf = getattr(self.local, "zip_file", None)
        if zf is None:
            zf = zipfile.ZipFile(self.archive)
            self.local.zip_file = zf
        return zf

    def upload(self, entry: tuple[str, str, int, int]) -> tuple[str, dict]:
        source_name, relative, size, crc = entry
        key = self.pool.settings.key(f"data/extracted_keyframes/{relative}")
        if self.pool.matches(key, size):
            result = "skipped"
        else:
            payload = self.zip_file().read(source_name)
            if len(payload) != size:
                raise RuntimeError(f"ZIP size mismatch for {source_name}")
            result = self.pool.put_bytes(
                key,
                payload,
                "image/png",
                {
                    "source-dataset": self.dataset,
                    "source-crc32": f"{crc:08x}",
                },
                skip_matching=False,
            )
        return result, {
            "key": key,
            "size": size,
            "source": f"https://www.kaggle.com/datasets/{self.dataset}",
            "source_member": source_name,
            "crc32": f"{crc:08x}",
        }


def upload_keyframe_archive(
    args: argparse.Namespace,
    archive: Path,
    dataset: str,
    shard_id: str,
    pool: R2ClientPool,
    workers: int,
) -> tuple[list[dict], set[str]]:
    entries, expected_count, expected_videos = keyframe_entries(args, archive, shard_id)
    LOG.info(
        "validated %s: %d keyframes across %d videos",
        shard_id,
        expected_count,
        len(expected_videos),
    )
    worker = KeyframeWorker(archive, dataset, pool)
    records: list[dict] = []
    uploaded = 0
    skipped = 0
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker.upload, entry) for entry in entries]
        try:
            for number, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result, record = future.result()
                records.append(record)
                if result == "uploaded":
                    uploaded += 1
                else:
                    skipped += 1
                if number % 100 == 0 or number == len(entries):
                    elapsed = max(time.monotonic() - started, 0.001)
                    LOG.info(
                        "%s %d/%d uploaded=%d skipped=%d rate=%.1f objects/s",
                        shard_id,
                        number,
                        len(entries),
                        uploaded,
                        skipped,
                        number / elapsed,
                    )
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    return sorted(records, key=lambda record: record["key"]), expected_videos


def run_keyframes(
    args: argparse.Namespace,
    pool: R2ClientPool,
    stage_dir: Path,
    state_dir: Path,
) -> dict:
    datasets = configured_keyframe_datasets(args)
    shard_ids = [shard_from_dataset(dataset) for dataset in datasets]
    expected_order = [
        json.loads(path.read_text())["shard_id"]
        for path in sorted(MANIFEST_ROOT.glob("L*/part-*.json"))
    ]
    if shard_ids != expected_order:
        raise RuntimeError(f"Kaggle shard order differs from manifest: {shard_ids} != {expected_order}")

    summaries: list[dict] = []
    total_frames = 0
    all_videos: set[str] = set()
    for dataset, shard_id in zip(datasets, shard_ids, strict=True):
        if args.only_shard and shard_id != args.only_shard:
            continue
        state_path = state_dir / "keyframes" / f"{shard_id}.done.json"
        manifest_key = pool.settings.key(f"manifests/keyframes/{shard_id}.jsonl")
        if state_path.is_file():
            completed = json.loads(state_path.read_text())
            if str(completed["manifest_key"]) == manifest_key and pool.head(manifest_key) is not None:
                summaries.append(completed)
                total_frames += int(completed["object_count"])
                manifest = json.loads(shard_manifest_path(shard_id).read_text())
                all_videos.update(str(video["video_id"]) for video in manifest["videos"])
                LOG.info("completed checkpoint verified; skipping Kaggle shard %s", shard_id)
                continue
            LOG.warning("local checkpoint exists but R2 manifest is absent; reprocessing %s", shard_id)
        recovered = recovered_keyframe_summary(args, pool, manifest_key, dataset, shard_id)
        if recovered is not None:
            write_local_json(state_path, recovered)
            summaries.append(recovered)
            total_frames += int(recovered["object_count"])
            manifest = json.loads(shard_manifest_path(shard_id).read_text())
            all_videos.update(str(video["video_id"]) for video in manifest["videos"])
            LOG.info("remote worker manifest verified; skipping Kaggle shard %s", shard_id)
            continue
        manifest = json.loads(shard_manifest_path(shard_id).read_text())
        estimated = int(manifest["estimated_output_bytes"])
        slug = dataset.split("/", 1)[1]
        destination = stage_dir / f"{slug}.zip"
        existing_archive_bytes = destination.stat().st_size if destination.exists() else 0
        other_stage_bytes = directory_bytes(stage_dir) - existing_archive_bytes
        # PNGs do not compress much further.  The estimate is the expanded
        # shard size; the extra allowance covers the ZIP directory and markers.
        projected_stage_bytes = other_stage_bytes + estimated + 250_000_000
        if projected_stage_bytes > args.max_temp_bytes:
            raise RuntimeError(
                f"{shard_id} may exceed the temporary limit: "
                f"projected={projected_stage_bytes:,}, limit={args.max_temp_bytes:,} bytes"
            )
        archive = download_kaggle_dataset(dataset, stage_dir, args.max_temp_bytes)
        records, videos = upload_keyframe_archive(
            args, archive, dataset, shard_id, pool, args.keyframe_workers
        )
        upload_manifest(pool, manifest_key, records)
        summary = {
            "shard_id": shard_id,
            "dataset": dataset,
            "completed_at": utc_now(),
            "manifest_key": manifest_key,
            "object_count": len(records),
            "total_bytes": sum(record["size"] for record in records),
            "video_count": len(videos),
        }
        write_local_json(state_path, summary)
        summaries.append(summary)
        total_frames += len(records)
        all_videos.update(videos)
        archive.unlink()
        LOG.info("completed %s and removed temporary archive", shard_id)
        ensure_stage_limit(stage_dir, args.max_temp_bytes)

    if not args.only_shard:
        if total_frames != 235_588:
            raise RuntimeError(f"keyframe total mismatch: {total_frames:,} != 235,588")
        if len(all_videos) != 873:
            raise RuntimeError(f"keyframe video total mismatch: {len(all_videos)} != 873")
        LOG.info("keyframe coverage verified: %d frames across %d videos", total_frames, len(all_videos))
    return {
        "shard_count": len(summaries),
        "frame_count": total_frames,
        "video_count": len(all_videos),
        "shards": summaries,
    }


def validate_sources(args: argparse.Namespace) -> dict:
    video_urls = configured_video_urls(args)
    datasets = configured_keyframe_datasets(args)
    shard_ids = [shard_from_dataset(dataset) for dataset in datasets]
    expected_order = [
        json.loads(path.read_text())["shard_id"]
        for path in sorted(MANIFEST_ROOT.glob("L*/part-*.json"))
    ]
    if len(video_urls) != 15 or len(set(video_urls)) != 15:
        raise RuntimeError("video URL list must contain 15 unique entries")
    if len(datasets) != 28 or len(set(datasets)) != 28:
        raise RuntimeError("keyframe URL list must contain 28 unique entries")
    if shard_ids != expected_order:
        raise RuntimeError("keyframe URL order does not match the shard manifest")
    expected_videos = load_expected_videos()
    status_frames = 0
    for shard_id in shard_ids:
        status_frames += int(keyframe_source_entry(args, shard_id)["frame_count"])
    if status_frames != 235_588:
        raise RuntimeError(f"status frame total mismatch: {status_frames:,}")
    return {
        "video_sources": len(video_urls),
        "keyframe_sources": len(datasets),
        "expected_videos": len(expected_videos),
        "expected_keyframes": status_frames,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("all", "videos", "keyframes"), default="all")
    parser.add_argument("--prefix", default=os.environ.get("R2_PREFIX", "fred"))
    parser.add_argument("--source-manifest", default=str(DEFAULT_SOURCE_MANIFEST))
    parser.add_argument("--video-urls", help="optional newline-delimited override for video source URLs")
    parser.add_argument("--keyframe-urls", help="optional newline-delimited override for Kaggle dataset URLs")
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--max-temp-gb", type=float, default=30.0)
    parser.add_argument("--keyframe-workers", type=int, default=8)
    parser.add_argument("--video-part-mib", type=int, default=32)
    parser.add_argument("--only-shard", help="process one keyframe shard, such as L21_p01")
    parser.add_argument("--only-archive", help="process one source ZIP filename")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.keyframe_workers < 1 or args.keyframe_workers > 32:
        parser.error("--keyframe-workers must be from 1 through 32")
    if args.video_part_mib < 5:
        parser.error("--video-part-mib must be at least 5")
    args.max_temp_bytes = int(args.max_temp_gb * 1_000_000_000)
    args.video_part_bytes = args.video_part_mib * 1024 * 1024
    if args.max_temp_bytes > DEFAULT_MAX_TEMP_BYTES:
        parser.error("the temporary limit cannot exceed 30 GB")
    if args.only_shard:
        args.only_shard = args.only_shard.upper().replace("_P", "_p")
        if not SHARD_RE.fullmatch(args.only_shard):
            parser.error("invalid --only-shard value")
    return args


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    args = parse_args()
    summary = validate_sources(args)
    LOG.info(
        "source manifests verified: %d video archives, %d keyframe shards, %d videos, %d frames",
        summary["video_sources"],
        summary["keyframe_sources"],
        summary["expected_videos"],
        summary["expected_keyframes"],
    )
    if args.check_only:
        return 0

    args.stage_dir = args.stage_dir.resolve()
    args.state_dir = args.state_dir.resolve()
    args.stage_dir.mkdir(parents=True, exist_ok=True)
    args.state_dir.mkdir(parents=True, exist_ok=True)
    ensure_stage_limit(args.stage_dir, args.max_temp_bytes)
    settings = R2Settings.from_env(args.prefix, args.keyframe_workers)
    pool = R2ClientPool(settings)

    probe_key = settings.key(f"manifests/.upload-probes/{uuid.uuid4().hex}")
    pool.put_bytes(probe_key, b"r2-media-upload-probe\n", "text/plain", skip_matching=False)
    pool.get().delete_object(Bucket=settings.bucket, Key=probe_key)
    if pool.head(probe_key) is not None:
        raise RuntimeError("R2 probe cleanup verification failed")
    LOG.info("R2 write/read/delete probe passed; prefix=%s", settings.prefix)

    final: dict[str, object] = {
        "version": 1,
        "prefix": settings.prefix,
        "started_at": utc_now(),
        "temporary_limit_bytes": args.max_temp_bytes,
    }
    if args.phase in {"all", "videos"}:
        final["videos"] = run_videos(args, pool, args.stage_dir, args.state_dir)
    if args.phase in {"all", "keyframes"}:
        final["keyframes"] = run_keyframes(args, pool, args.stage_dir, args.state_dir)
    final["completed_at"] = utc_now()
    partial_worker = bool(args.only_archive or args.only_shard)
    if partial_worker:
        write_local_json(args.state_dir / "last-partial-upload.json", final)
        LOG.info("assigned unit complete; global manifest index left unchanged")
    else:
        index_payload = (json.dumps(final, indent=2, sort_keys=True) + "\n").encode("utf-8")
        pool.put_bytes(
            settings.key("manifests/media-upload-index.json"),
            index_payload,
            "application/json",
            skip_matching=False,
        )
        write_local_json(args.state_dir / "media-upload-index.json", final)
    ensure_stage_limit(args.stage_dir, args.max_temp_bytes)
    LOG.info("upload complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
