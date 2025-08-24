from .time_interval import extract_frames
from tqdm import tqdm
import os
from multiprocessing import Pool, cpu_count

def process_video(args):
    """Wrapper for multiprocessing"""
    video_path, output_folder, interval, position = args
    output_subfolder = os.path.join(output_folder, os.path.splitext(os.path.basename(video_path))[0])
    os.makedirs(output_subfolder, exist_ok=True)
    return extract_frames(video_path, output_subfolder, interval=interval, position=position)
def extract_videos(input_folder, output_folder, pos_begin=None, pos_end=None, interval=2, max_workers=2):
    """Extract frames from multiple videos in parallel with progress bars."""
    video_paths = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.endswith(('.mp4', '.avi', '.mov'))
    ]
    # Ensure consistent order
    video_paths.sort()

    # Apply range selection
    if pos_end is not None:
        pos_end = min(pos_end, len(video_paths))
    else: 
        pos_end = len(video_paths)
    if pos_begin is not None or pos_end is not None:
        video_paths = video_paths[pos_begin:pos_end]

    args_list = [
        (video_path, output_folder, interval, i)
        for i, video_path in enumerate(sorted(video_paths))
    ]
    
    if max_workers > 1:
        workers = min(max_workers, cpu_count(), len(args_list))

        all_metadata = []
        with Pool(processes=workers) as pool:
            results = pool.map(process_video, args_list)
            for meta in results:
                all_metadata.extend(meta)

        return all_metadata
    else: # single thread
        all_metadata = []
        for args in args_list:
            meta = process_video(args)
            all_metadata.extend(meta)
        return all_metadata


import json
if __name__ == "__main__":
    # Example: extract frames every 2s, process up to 4 videos in parallel
    x = 8
    length = 100
    
    frame_metadata = extract_videos("/root/data/unzipped/video", "/root/data/extracted_keyframes", interval=2, max_workers=1
        , pos_begin=x*length, pos_end=(x+1)*length)
    with open(f"/root/data/frame_metadata{x}.json", "w") as f:
        json.dump(frame_metadata, f, indent=4)