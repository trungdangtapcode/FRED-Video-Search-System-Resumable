
import json

SUBMISSIONS_FILE = '/data/root/hcmc/submit_server/submissions.json'
VIDEO_FPS_FILE = "/data/root/data/fps_dict_v2.json"

with open(SUBMISSIONS_FILE, "r") as f:
	fsubmissions = json.load(f)
with open(VIDEO_FPS_FILE, "r") as f:
	video_fps = json.load(f)

submissions = []
for submission in fsubmissions.values():
	submissions.extend(submission)

for submission in submissions:
	video_id = submission['video_path'].split("/")[-1].split(".")[0]  # L21_V001
	fps = video_fps.get(video_id, None)
	assert fps is not None, f"FPS not found for video {video_id}"
	calculated_fps = submission['frame_idx'] / submission['timestamp'] if  submission['timestamp'] > 0 else submission['frame_idx']
	# assert abs(calculated_fps - fps) < 1e-1, f"FPS mismatch for video {video_id}: {calculated_fps} vs {fps}"
	if abs(calculated_fps - fps) >= 1e-1:
		print(f"⚠️ FPS mismatch for video {video_id}: {calculated_fps} vs {fps}")
