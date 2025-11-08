import os
import requests
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def download_file(args):
    """Worker function for parallel download with tqdm"""
    url, output_dir, position, chunk_size = args
    os.makedirs(output_dir, exist_ok=True)
    local_filename = os.path.join(output_dir, url.split("/")[-1])

    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=os.path.basename(local_filename),
                position=position,
                leave=True,
            )

            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))
            progress.close()
        return f"✅ Done: {local_filename}"
    except Exception as e:
        return f"❌ Failed {url}: {e}"

def download_from_txt(txt_path="/data/root/data/urls.txt", pos_begin=None, pos_end=None, max_workers=4):
    with open(txt_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    # Apply range selection
    if pos_begin is not None or pos_end is not None:
        urls = urls[pos_begin:pos_end]

    args_list = [
        (url, "data/downloads", i, 1024 * 1024)
        for i, url in enumerate(urls)
    ]

    # Limit to available CPUs or max_workers
    workers = min(max_workers, cpu_count(), len(args_list))

    with Pool(processes=workers) as pool:
        results = pool.map(download_file, args_list)

    print("\n".join(results))

if __name__ == "__main__":
    # Example usage: download 4 files in parallel
    download_from_txt(max_workers=4)
