import os
import json

def concat_json_arrays(path, output_path=None):
    """
    Concatenate JSON arrays from files named frame_metadata0.json ... frame_metadata8.json.
    
    Args:
        path (str): Directory containing the JSON files.
    
    Returns:
        list: Combined JSON array.
    """
    combined = []

    for i in range(9):  # from 0 to 8
        file_path = os.path.join(path, f"frame_metadata{i}.json")
        
        if not os.path.exists(file_path):
            print(f"⚠️ Skipping missing file: {file_path}")
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    combined.extend(data)
                else:
                    print(f"⚠️ File {file_path} does not contain a JSON array.")
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding {file_path}: {e}")
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=4)
        print(f"✅ Combined JSON saved to {output_path}")
    
    return combined

def concat_json_arrays_paths(file_paths, output_path=None):
    """
    Concatenate JSON arrays from a list of file paths.
    
    Args:
        file_paths (list): List of file paths to JSON files.
    
    Returns:
        list: Combined JSON array.
    """
    combined = []

    for file_path in file_paths:
        
        if not os.path.exists(file_path):
            print(f"⚠️ Skipping missing file: {file_path}")
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    combined.extend(data)
                else:
                    print(f"⚠️ File {file_path} does not contain a JSON array.")
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding {file_path}: {e}")
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=4)
        print(f"✅ Combined JSON saved to {output_path}")
    
    return combined

def update_frame_metadata_compressed(json_path):
    with open(json_path, "r") as f:
        frame_metadata = json.load(f)
        
    for frame in frame_metadata[:]:
        path = frame["frame_path"] #/root/data/extracted_keyframes/L21_V001/00000.png
        # convert to /root/data/compressed_keyframes/L21_V001/00000.png
        path = path.replace("extracted_keyframes", "compressed_keyframes")
        frame['compressed_frame_path'] = path
    json_path2 = frame_metadata
    with open(json_path2, "w") as f:
        json.dump(frame_metadata, f)

concat_json_arrays_paths(["/data/root/data/frames_metadata.json","/data/root/data/frame_metadata_batch2.json"], "/data/root/data/frames_metadata_v2.json")
# concat_json_arrays("/root/data", "/root/data/frame_metadata.json")