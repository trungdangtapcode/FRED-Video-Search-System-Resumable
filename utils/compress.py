import json
from PIL import Image

def compress_image(input_path, output_path, quality=70, max_width=None, max_height=None):
    # if output_path exists, skip
    if Path(output_path).exists():
        return
    
    # Open image
    img = Image.open(input_path)
    
    # Optionally resize
    if max_width and max_height:
        img.thumbnail((max_width, max_height))
    
    # exist_ok=True
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
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

def compress_data_multiprocess9(input_path, output_path, quality=70, max_width=None, max_height=None):
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

def compress_from_json(json_path, folder_path):
    """
    Json example:
    [{'video_path': '/root/data/unzipped/video/L21_V001.mp4',
        'fps': 30.0,
        'timestamp': 0.0,
        'frame_idx': 0,
        'frame_path': '/root/data/extracted_keyframes/L21_V001/00000.png'},...]
    compressed to <folder_path>/L21_V001/00000.png
    """
    # open json 
    with open(json_path, "r") as f:
        frames_metadata = json.load(f)
    
    for frame_metadata in tqdm(frames_metadata):
        frame_path = frame_metadata["frame_path"]
        # '<some random path>/L21_V001/00000.png' -> <folder_path>/L21_V001/00000.png (THIS IS OUTPUT_PATH)
        output_path = frame_path.split("/")[-2:]
        output_path = "/".join([folder_path] + output_path)
        # print(f"Compressing {frame_path} -> {output_path}")
        # compress_image(frame_path, output_path, quality=70, max_width=1280//4, max_height=720//4)
        frame_metadata['compressed_frame_path'] = output_path
    
    # save json to original path
    with open(json_path, "w") as f:
        json.dump(frames_metadata, f)
    
        
if __name__ == "__main__":
    # Example usage:
    # compress_image(
    #     "/root/data/extracted_keyframes/L21_V001/00000001.jpg",
    #     "/root/data/compressed_keyframes/00000001.jpg",
    #     quality=10,
    #     max_width=1280//4,
    #     max_height=720//4
    # )

    # Compress multiple video folders in a range
    # compress_data(
    #     "/root/data/extracted_keyframes",
    #     "/root/data/compressed_keyframes",
    #     pos_begin=0,
    #     pos_end=10,  # Adjust as needed
    #     quality=10,
    #     max_width=1280//4,
    #     max_height=720//4
    # )

    # Compress all video folders using multiprocessing
    # compress_data_multiprocess(
    #     "/root/data/extracted_keyframes",
    #     "/root/data/compressed_keyframes",
    #     quality=10,
    #     max_width=1280//4,
    #     max_height=720//4
    # compress_data_multiprocess(
    #     "/root/data/extracted_keyframes",
    #     "/root/data/compressed_keyframes_btc",
    #     quality=10,
    #     max_width=1280//4,
    #     max_height=720//4
    # )
    compress_from_json(
        json_path="/root/data/frame_metadata_btc.json",
        folder_path="/root/data/compressed_keyframes_btc"
    )
