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


concat_json_arrays("/root/data", "/root/data/frame_metadata.json")