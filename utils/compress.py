from PIL import Image

def compress_image(input_path, output_path, quality=70, max_width=None, max_height=None):
    # Open image
    img = Image.open(input_path)
    
    # Optionally resize
    if max_width and max_height:
        img.thumbnail((max_width, max_height))
    
    # Save with reduced quality
    img.save(output_path, optimize=True, quality=quality)



from pathlib import Path
from itertools import chain
from tqdm import tqdm
from multiprocessing import Process

def compress_video(folder_path, output_folder, quality=70, max_width=None, max_height=None):
    folder_path = Path(folder_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    for img_file in tqdm(sorted(list(chain(folder_path.glob("*.jpg"), folder_path.glob("*.png"))))):
        output_path = output_folder / img_file.name
        compress_image(img_file, output_path, quality, max_width, max_height)

def compress_data(input_path, output_path, pos_begin, pos_end, quality=70, max_width=None, max_height=None):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get sorted list of subfolders (e.g., L21_V001, L21_V002, ...)
    subfolders = sorted([f for f in input_path.iterdir() if f.is_dir()])

    pos_begin = max(0, pos_begin)
    pos_end = min(len(subfolders), pos_end)

    for subfolder in subfolders[pos_begin:pos_end]:
        out_subfolder = output_path / subfolder.name
        print(f"Compressing {subfolder.name} -> {out_subfolder}")
        compress_video(subfolder, out_subfolder, quality=quality, max_width=max_width, max_height=max_height)

def compress_data_multiprocess(input_path, output_path, quality=70, max_width=None, max_height=None):
    input_path = Path(input_path)
    subfolders = sorted([f for f in input_path.iterdir() if f.is_dir()])
    n = len(subfolders)

    processes = []
    for x in range(9):  # 9 processes
        pos_begin = x * 100
        pos_end = min(n, x * 100 + 100)  # up to 100 per process
        if pos_begin >= n:
            break
        p = Process(
            target=compress_data,
            args=(input_path, output_path, pos_begin, pos_end, quality, max_width, max_height)
        )
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()
        
compress_data_multiprocess(
    "/root/data/extracted_keyframes",
    "/root/data/compressed_keyframes",
    quality=10,
    max_width=1280//4,
    max_height=720//4
)
