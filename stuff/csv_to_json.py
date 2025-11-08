import json
import os
import csv
from collections import defaultdict

def load_fps_dict(fps_dict_path='/root/data/fps_dict.json'):
    """
    Load FPS dictionary from file
    
    Args:
        fps_dict_path (str): Path to the FPS dictionary file
    
    Returns:
        dict: FPS dictionary mapping video_id to fps value
    """
    try:
        with open(fps_dict_path, 'r', encoding='utf-8') as f:
            import ast
            content = f.read()
            # Try to evaluate as Python dict literal
            fps_dict = ast.literal_eval(content)
            return fps_dict
    except:
        try:
            # Try JSON format
            with open(fps_dict_path, 'r', encoding='utf-8') as f:
                fps_dict = json.load(f)
                return fps_dict
        except Exception as e:
            print(f"Error loading FPS dictionary: {e}")
            return {}

def calculate_timestamp(frame_idx, fps):
    """
    Calculate timestamp from frame index and fps
    
    Args:
        frame_idx (int): Frame index
        fps (float): Frames per second
    
    Returns:
        float: Timestamp in seconds
    """
    return frame_idx / fps

def convert_csv_to_json(submission_dir="/root/submission-nnn/submission", fps_dict_path='/root/data/fps_dict.json', output_json_path="zconverted_back.json"):
    """
    Convert CSV files back to JSON format
    
    Args:
        submission_dir (str): Directory containing CSV files
        fps_dict_path (str): Path to FPS dictionary file
        output_json_path (str): Output JSON file path
    
    Returns:
        dict: The reconstructed JSON data
    """
    # Load FPS dictionary
    fps_dict = load_fps_dict(fps_dict_path)
    print(f"Loaded FPS dictionary with {len(fps_dict)} entries")
    if not fps_dict:
        print("Warning: Could not load FPS dictionary. Timestamps will not be calculated.")
    
    result_json = {}
    
    # Check if submission directory exists
    if not os.path.exists(submission_dir):
        print(f"Error: Submission directory '{submission_dir}' not found")
        return {}
    
    # Process each CSV file
    csv_files = [f for f in os.listdir(submission_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(submission_dir, csv_file)
        question_base = csv_file.replace('.csv', '')
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            
            if "trake" in question_base:
                # Handle trake questions - reconstruct multiple questions from one file
                row_count = 0
                for row in reader:
                    if not row:
                        continue
                    
                    video_id = row[0]
                    video_id = video_id.replace('\ufeff', '')
                    frame_indices = [int(idx) for idx in row[1:]]
                    video_path = f"/root/data/unzipped/video/{video_id}.mp4"
                    fps = fps_dict.get(video_id, 25.0)  # Default to 25 FPS if not found
                    
                    # For trake questions, we need to determine the suffix
                    # Since we don't know the original suffixes, we'll use row index
                    if row_count == 0:
                        suffix = "0"  # First row gets suffix "0" 
                    else:
                        suffix = f"{row_count}a"  # Subsequent rows get "1a", "2a", etc.
                    
                    question_name = f"{question_base}{suffix}"
                    
                    # Create entries for this question
                    entries = []
                    for frame_idx in frame_indices:
                        timestamp = calculate_timestamp(frame_idx, fps)
                        entry = {
                            "frame_idx": frame_idx,
                            "video_path": video_path,
                            "timestamp": timestamp,
                            "submitted_at": "2025-08-31T00:00:00.000000"  # Placeholder timestamp
                        }
                        entries.append(entry)
                    
                    result_json[question_name] = entries
                    row_count += 1
                    
            else:
                # Handle kis and qa questions
                entries = []
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    
                    video_id = row[0]
                    video_id = video_id.replace('\ufeff', '')
                    frame_idx = int(row[1])
                    video_path = f"/root/data/unzipped/video/{video_id}.mp4"
                    
                    if video_id not in fps_dict:
                        raise ValueError(f"FPS for video_id '{video_id}' not found in fps_dict")
                    
                    fps = fps_dict.get(video_id, 25.0)
                    
                    timestamp = calculate_timestamp(frame_idx, fps)
                    
                    entry = {
                        "frame_idx": frame_idx,
                        "video_path": video_path,
                        "timestamp": timestamp,
                        "submitted_at": "2025-08-31T00:00:00.000000"
                    }
                    
                    # Add answer for qa questions
                    if "qa" in question_base and len(row) > 2:
                        entry["answer"] = row[2]
                    
                    entries.append(entry)
                
                result_json[question_base] = entries
    
    # Save to JSON file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully converted CSV files back to JSON: '{output_json_path}'")
    print(f"📊 Reconstructed {len(result_json)} questions")
    
    return result_json

convert_csv_to_json()