import os
import subprocess
from pathlib import Path
from tqdm import tqdm

# Set your input/output directories
input_folder = Path("/path/to/your/videos")  # Change this!
output_folder = input_folder / "converted"
output_folder.mkdir(exist_ok=True)

# Supported video extensions
video_exts = {'.mp4', '.mkv', '.webm', '.mov'}

def is_av1(video_path):
    """Check if the video codec is AV1 using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name",
             "-of", "default=nw=1:nk=1", str(video_path)],
            capture_output=True, text=True
        )
        codec = result.stdout.strip().lower()
        return codec == "av1"
    except Exception as e:
        print(f"Error checking codec for {video_path}: {e}")
        return False

def convert_av1_to_h264(input_path, output_path):
    """Convert AV1 video to H.264 using ffmpeg."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_path),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",  # Re-encode audio to AAC
            str(output_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed on {input_path}: {e}")

# Loop through all video files
video_files = [f for f in input_folder.iterdir() if f.suffix.lower() in video_exts]

for video in tqdm(video_files, desc="Processing videos"):
    if is_av1(video):
        output_path = output_folder / (video.stem + "_converted.mp4")
        print(f"Converting AV1 video: {video.name} -> {output_path.name}")
        convert_av1_to_h264(video, output_path)
    else:
        print(f"Skipping non-AV1 video: {video.name}")


# ffmpeg -err_detect ignore_err -i /data/root/data/unzipped/video/K01_V004.mp4 \
# -c:v libx264 -crf 23 -preset fast \
# -c:a aac -b:a 128k \
# /data/root/data/unzipped/video/K01_V004_converted.mp4