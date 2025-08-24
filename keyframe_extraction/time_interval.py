import os
import cv2
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

SHOW_TQDM = True

def extract_frames(video_path, output_folder, interval=2, position=0):
    """Extract frames from a single video at given interval (seconds)."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0:
        raise ValueError("FPS could not be determined.")
    frame_interval = int(round(fps * interval))

    os.makedirs(output_folder, exist_ok=True)

    frame_count, saved_count = 0, 0
    metadata = []
    abs_video_path = os.path.abspath(video_path)

    if not SHOW_TQDM:
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
        cap.release()
        return metadata

    with tqdm(
        total=total_frames,
        desc=f"Frames {os.path.basename(video_path)}",
        unit="frame",
        position=position,
        leave=True
    ) as pbar:
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
    return metadata


# Example usage:
# frames_metadata = extract_frames("input.mp4", "frames_output", 0.5)