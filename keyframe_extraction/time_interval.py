import cv2
import os
from tqdm import tqdm

def extract_frames(video_path, output_folder, interval=2):
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0:
        raise ValueError("FPS could not be determined.")
    frame_interval = int(round(fps * interval))  # number of frames to skip

    # Create output folder if not exists
    os.makedirs(output_folder, exist_ok=True)

    frame_count = 0
    saved_count = 0
    metadata = []
    abs_video_path = os.path.abspath(video_path)

    print(f"Number of frames in video: {total_frames}")
    
    # Use tqdm progress bar
    with tqdm(total=total_frames, desc=f"Extracting frames {os.path.basename(video_path)}", unit="frame", leave=False) as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                filename = f"{saved_count:05d}.png"
                filepath = os.path.join(output_folder, filename)
                abs_filepath = os.path.abspath(filepath)
                
                cv2.imwrite(filepath, frame)

                timestamp = frame_count / fps
                metadata.append({
                    "video_path": abs_video_path,
                    "fps": fps,
                    "timestamp": timestamp,
                    "frame_idx": frame_count,
                    "frame_path": abs_filepath
                })

                saved_count += 1

            frame_count += 1
            pbar.update(1)

    cap.release()
    print(f"Done. Extracted {saved_count} frames to {output_folder}")
    return metadata


# Example usage:
# frames_metadata = extract_frames("input.mp4", "frames_output", 0.5)