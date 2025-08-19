from .time_interval import extract_frames
from tqdm import tqdm
import os

def extract_videos(input_folder, output_folder, pos_begin = None, pos_end = None, **kwargs):
    """
    2
    Extract frames from multiple videos at specified intervals and save them to the output folder.
    
    :param video_paths: List of paths to video files.
    :param output_folder: Folder where extracted frames will be saved.
    :param interval: Time interval in seconds between extracted frames.
    :return: List of metadata dictionaries for each extracted frame.
    """
    all_metadata = []
    video_paths = []
    for f in os.listdir(input_folder):
        if f.endswith(('.mp4', '.avi', '.mov')):
            video_paths.append(os.path.join(input_folder, f))
    video_paths.sort()  # Sort the video paths for consistent processing
    if pos_end != None:
        pos_end = min(pos_end, len(video_paths))
    if pos_begin is not None or pos_end is not None:
        video_paths = video_paths[pos_begin:pos_end]
    elif pos_begin is not None:
        video_paths = video_paths[pos_begin:]
    elif pos_end is not None:
        video_paths = video_paths[:pos_end]

    # with tqdm(total=len(video_paths), desc=f"Processing videos", unit="video") as pbar:
    for video_path in video_paths:
        output_subfolder = os.path.join(output_folder, os.path.splitext(os.path.basename(video_path))[0])
        os.makedirs(output_subfolder, exist_ok=True)
        metadata = extract_frames(video_path, output_subfolder, **kwargs)
        all_metadata.extend(metadata)
        # pbar.update(1)
        # # Set pbar desc
        # pbar.set_description(f"Processing {os.path.basename(video_path)}")

    return all_metadata