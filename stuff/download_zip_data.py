import os
import zipfile
from queue import Queue
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore
from typing import Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from tqdm import tqdm

from download_logger import DownloadLogger

def make_session(max_workers: int) -> requests.Session:
    """Create session with connection pooling"""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        pool_connections=max_workers,
        pool_maxsize=max_workers,
        max_retries=retry,
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def download_worker(
    url: str,
    download_dir: str,
    unzip_queue: Queue,
    session: requests.Session,
    host_semaphore: Semaphore,
    chunk_size: int,
    position: int,
    logger: DownloadLogger,
):
    """Download and put in queue for unzipping"""
    filename = os.path.basename(urlparse(url).path)
    out_path = os.path.join(download_dir, filename)
    tmp_path = out_path + ".part"

    with host_semaphore:
        try:
            # Check if already downloaded
            if logger.is_download_complete(url) and os.path.exists(out_path):
                # Queue for unzip check (unzip_worker will check if needed)
                if not logger.is_unzip_complete(out_path):
                    unzip_queue.put((out_path, filename))
                    return f"✅ Queued existing for unzip: {filename}"
                else:
                    return f"✅ Skipped (already extracted): {filename}"

            logger.log_download(url, "downloading")

            os.makedirs(download_dir, exist_ok=True)

            # Check resume
            resume_pos = 0
            mode = "wb"
            headers = {}
            if os.path.exists(tmp_path):
                resume_pos = os.path.getsize(tmp_path)
                headers["Range"] = f"bytes={resume_pos}-"
                mode = "ab"

            response = session.get(
                url,
                stream=True,
                headers=headers,
                timeout=(10, 300),
                allow_redirects=True,
            )
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            if resume_pos:
                total_size += resume_pos

            progress = tqdm(
                total=total_size,
                initial=resume_pos,
                unit="B",
                unit_scale=True,
                desc=f"⬇️  {filename}",
                position=position,
                leave=True,
            )

            with open(tmp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))

            progress.close()
            os.replace(tmp_path, out_path)

            logger.log_download(url, "completed", os.path.getsize(out_path))

            # Queue for immediate unzipping
            unzip_queue.put((out_path, filename))

            return f"✅ Downloaded: {filename}"

        except Exception as e:
            logger.log_download(url, "failed", error=str(e))
            return f"❌ Failed {filename}: {e}"


def unzip_worker(
    unzip_queue: Queue,
    output_dir: str,
    position: int,
    logger: DownloadLogger,
    keep_zip: bool = False,
):
    """Continuously unzip from queue"""
    while True:
        item = unzip_queue.get()
        if item is None:  # Poison pill
            break

        zip_path, filename = item

        try:
            if logger.is_unzip_complete(zip_path):
                unzip_queue.task_done()
                continue

            logger.log_unzip(zip_path, "extracting")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)

                progress = tqdm(
                    total=total_files,
                    unit="file",
                    desc=f"📦 {filename}",
                    position=position,
                    leave=True,
                )

                os.makedirs(output_dir, exist_ok=True)
                for file_info in file_list:
                    zip_ref.extract(file_info, output_dir)
                    progress.update(1)

                progress.close()

            logger.log_unzip(zip_path, "completed", total_files)

            # Optionally delete zip after extraction
            if not keep_zip:
                os.remove(zip_path)

        except Exception as e:
            logger.log_unzip(zip_path, "failed", error=str(e))
        finally:
            unzip_queue.task_done()


def producer_consumer_pipeline(
    txt_path: str = "urls.txt",
    download_dir: str = "../data/downloads",
    extract_dir: str = "../data/unzipped",
    download_workers: int = 8,
    unzip_workers: int = 4, 
    per_host_limit: int = 6,
    chunk_size: int = 8 * 1024 * 1024,
    log_file: str = "download_log.json",
    keep_zip: bool = False,
    resume: bool = True,
):
    """Download and unzip in parallel pipeline"""
    logger = DownloadLogger(log_file)
    unzip_queue = Queue(maxsize=5)  # Limit queue size to avoid memory issues

    with open(txt_path, "r") as f:
        all_urls = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    if not all_urls:
        print("No URLs found")
        return

    # Filter based on resume
    if resume:
        urls = [
            url
            for url in all_urls
            if not logger.is_unzip_complete(
                os.path.join(download_dir, os.path.basename(urlparse(url).path))
            )
        ]
        print(f"\n📋 Pipeline: {len(urls)}/{len(all_urls)} files to process")
    else:
        urls = all_urls
        print(f"\n📋 Fresh pipeline: {len(urls)} files to process")

    if len(urls) == 0:
        print("✅ All files already processed!")
        logger.print_summary()
        return

    hosts = set(urlparse(u).netloc for u in urls)
    host_semaphores: Dict[str, Semaphore] = {
        h: Semaphore(per_host_limit) for h in hosts
    }

    session = make_session(download_workers)

    # Start unzip workers
    unzip_executor = ThreadPoolExecutor(max_workers=unzip_workers)
    for i in range(unzip_workers):
        unzip_executor.submit(
            unzip_worker,
            unzip_queue,
            extract_dir,
            i + download_workers,
            logger,
            keep_zip,
        )

    # Start download workers
    results = []
    with ThreadPoolExecutor(max_workers=download_workers) as download_executor:
        futures = {}
        for i, url in enumerate(urls):
            host = urlparse(url).netloc
            fut = download_executor.submit(
                download_worker,
                url,
                download_dir,
                unzip_queue,
                session,
                host_semaphores[host],
                chunk_size,
                i,
                logger,
            )
            futures[fut] = url

        for fut in futures:
            try:
                results.append(fut.result())
            except Exception as e:
                url = futures[fut]
                results.append(
                    f"❌ Exception {os.path.basename(urlparse(url).path)}: {e}"
                )

    # Wait for all unzips to complete
    unzip_queue.join()

    # Stop unzip workers
    for _ in range(unzip_workers):
        unzip_queue.put(None)
    unzip_executor.shutdown(wait=True)

    print("\n" + "\n".join(results))
    logger.print_summary()
    logger.print_failed_items()


if __name__ == "__main__":
    producer_consumer_pipeline(
        txt_path="urls.txt",
        keep_zip=True,
        resume=True,
    )
