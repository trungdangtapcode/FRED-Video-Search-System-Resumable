import os
import zipfile
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def unzip_file(args):
    """Worker function for parallel unzip with tqdm"""
    zip_path, output_dir, position = args
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            file_list = zip_ref.infolist()
            total_files = len(file_list)

            progress = tqdm(
                total=total_files,
                unit="file",
                desc=os.path.basename(zip_path),
                position=position,
                leave=True,
            )

            os.makedirs(output_dir, exist_ok=True)
            for file_info in file_list:
                zip_ref.extract(file_info, output_dir)
                progress.update(1)

            progress.close()
        return f"✅ Unzipped: {zip_path}"
    except Exception as e:
        return f"❌ Failed {zip_path}: {e}"

def unzip_from_dir(zip_dir="/data/root/data/downloads", output_dir="/data/root/data/unzipped", max_workers=4):
    # Find all .zip files
    zip_files = [
        os.path.join(zip_dir, f)
        for f in os.listdir(zip_dir)
        if f.endswith(".zip")
    ]

    args_list = [
        (zip_file, output_dir, i)
        for i, zip_file in enumerate(zip_files)
    ]

    workers = min(max_workers, cpu_count(), len(args_list))

    with Pool(processes=workers) as pool:
        results = pool.map(unzip_file, args_list)

    print("\n".join(results))

if __name__ == "__main__":
    # Example: unzip all .zip files in parallel
    unzip_from_dir(max_workers=4)
