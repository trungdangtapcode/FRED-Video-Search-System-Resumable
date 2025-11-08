import subprocess
from pathlib import Path
from tqdm import tqdm

input_folder = Path("/data/root/data/unzipped/video")
output_folder = input_folder / "converted"
output_folder.mkdir(exist_ok=True)

video_exts = {'.mp4', '.mkv', '.webm', '.mov'}

def is_av1(video_path):
    """Check if the video codec is AV1."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name",
             "-of", "default=nw=1:nk=1", str(video_path)],
            capture_output=True, text=True
        )
        return result.stdout.strip().lower() == "av1"
    except Exception as e:
        print(f"[ERROR] Codec check failed for {video_path}: {e}")
        return False

def get_duration(video_path):
    """Get video duration in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
        return max(0, duration - 0.5)  # trim last 0.5s
    except Exception as e:
        print(f"[ERROR] Failed to get duration for {video_path}: {e}")
        return None

def convert_av1_trimmed(input_path, output_path, duration):
    """Convert AV1 to H.264, trimming last 0.5s."""
    try:
        subprocess.run([
            "ffmpeg",
            "-i", str(input_path),
            "-t", str(duration),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            str(output_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg failed on {input_path.name}: {e}")

# Process files
video_files = [f for f in input_folder.iterdir() if f.suffix.lower() in video_exts]

for video in tqdm(video_files, desc="Processing videos"):
    if not is_av1(video):
        print(f"[SKIP] Not AV1: {video.name}")
        continue

    output_path = output_folder / (video.stem + ".mp4")
    if output_path.exists():
        print(f"[SKIP] Already converted: {output_path.name}")
        continue

    duration = get_duration(video)
    if duration is None or duration == 0:
        print(f"[ERROR] Skipping due to invalid duration: {video.name}")
        continue

    print(f"[CONVERT] {video.name} -> {output_path.name} (duration: {duration:.2f}s)")
    convert_av1_trimmed(video, output_path, duration)
