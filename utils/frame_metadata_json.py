import json
import os
import csv

def keyframes_to_json(video_path, keyframe_folder_path, keyframe_metadata_csv_path):
    """
    Args:
        video_path (_type_): _description_
        keyframe_folder_path (_type_): _description_
        keyframe_metadata_csv_path (_type_): _description_
    Outputs example:
        [{'video_path': '/root/data/unzipped/video/L21_V001.mp4',
        'fps': 30.0,
        'timestamp': 0.0,
        'frame_idx': 0,
        'frame_path': '/root/data/extracted_keyframes/L21_V001/00000.png'},...]

    """
    # load csv (n,pts_time,fps,frame_idx)
    keyframe_metadata = []
    with open(keyframe_metadata_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['video_path'] = video_path
            # remove column 'n' and rename pts_time to timestamp
            row.pop('n')
            row['timestamp'] = float(row.pop('pts_time'))
            keyframe_metadata.append(row)
    
    keyframe_paths = sorted(os.listdir(keyframe_folder_path))
    if len(keyframe_metadata) != len(keyframe_paths):
        raise ValueError(f"Number of keyframes ({len(keyframe_paths)}) does not match number of metadata entries ({len(keyframe_metadata)}) video: {video_path}")
    
    for frame_data, frame_path in zip(keyframe_metadata, keyframe_paths):
        frame_data['frame_path'] = os.path.join(keyframe_folder_path, frame_path)
    
    
    return keyframe_metadata

# Example:
# keyframes_to_json("/root/data/unzipped/video/V21_V001.mp4",
#     "/root/data/unzipped/keyframes/L21_V001",
#     "/root/data/unzipped/map-keyframes/L21_V001.csv"
# )

def videos_to_json(videos_folder_path, keyframes_folder_path, videos_csv_path):
    """
    Args:
        videos_folder_path (_type_): _description_
        keyframes_folder_path (_type_): _description_
        output_json_path (_type_): _description_ 
    Outputs example:
        [{'video_path': '/root/data/unzipped/video/L21_V001.mp4',
        'fps': 30.0,
        'timestamp': 0.0,
        'frame_idx': 0,
        'frame_path': '/root/data/extracted_keyframes/L21_V001/00000.png'},...]

    """
    all_keyframe_metadata = []
    print(len([x for x in os.listdir(videos_folder_path) if x.endswith(".mp4") and "converted" not in x and "partial" not in x]), len(os.listdir(keyframes_folder_path)), len(os.listdir(videos_csv_path)))
    assert len([x for x in os.listdir(videos_folder_path) if x.endswith(".mp4") and "converted" not in x and "partial" not in x]) == len(os.listdir(keyframes_folder_path)) == len(os.listdir(videos_csv_path)), "Number of videos, keyframe folders, and csv files must match"
    
    for video_file, keyframes_path, keyframe_csv_file in zip(
            sorted([x for x in os.listdir(videos_folder_path) if x.endswith(".mp4") and "converted" not in x and "partial" not in x]), 
            sorted(os.listdir(keyframes_folder_path)),
            sorted(os.listdir(videos_csv_path)) ):
        videos_path = os.path.join(videos_folder_path, video_file)
        keyframe_folder_path = os.path.join(keyframes_folder_path, keyframes_path)
        keyframe_metadata_csv_path = os.path.join(videos_csv_path, keyframe_csv_file)
        video_keyframe_metadata = keyframes_to_json(videos_path, keyframe_folder_path, keyframe_metadata_csv_path)
        all_keyframe_metadata.extend(video_keyframe_metadata)
    return all_keyframe_metadata

tmp = videos_to_json("/data/root/data/unzipped/video","/data/root/data/unzipped/keyframes","/data/root/data/unzipped/map-keyframes-b2")
import json
output_path = "/data/root/data/frame_metadata_batch2.json"
with open(output_path, "w") as f:
    json.dump(tmp, f)