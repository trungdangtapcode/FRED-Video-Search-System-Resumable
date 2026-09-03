import json
import os
import csv
from collections import defaultdict

FPS_PATH = "/home/nguyentnt/a/FRED-Video-Search-System-Resumable/data/fps_dict_v2.json"

with open(FPS_PATH, "r") as f:
    fps_dict = json.load(f)


def extract_video_id(video_path):
    """Extract video ID from video path"""
    return video_path.split("/")[-1].split(".")[0]


def get_frame_idx(entry):
    idx = entry["frame_idx"]
    if (idx>=0):
        if "timestamp" in entry and entry["timestamp"] is not None:
            video_id = extract_video_id(entry["video_path"])
            fps = fps_dict.get(video_id, None)
            if fps is not None:
                calculated_idx = round(fps * entry["timestamp"])
                if abs(calculated_idx - idx) > 2:
                    print(f"⚠️ Warning: frame_idx {idx} does not match calculated {calculated_idx} for video {video_id} at timestamp {entry['timestamp']}")
        return idx
    video_id = extract_video_id(entry["video_path"])
    fps = fps_dict.get(video_id, None)
    timestamp = entry["timestamp"]
    if fps is None or timestamp is None:
        raise ValueError(f"Cannot determine frame_idx for entry: {entry}")
    print(f"⚠️ Warning: frame_idx missing or negative for entry {entry}, calculating from timestamp {timestamp} and fps {fps}")
    idx = round(fps * timestamp)
    return idx

def process_json_to_csv(json_data, output_dir="submission"):
    """
    Convert JSON data to CSV files in the specified format
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Group trake questions by prefix
    trake_groups = defaultdict(list)
    
    for question, entries in json_data.items():
        if "trake" in question:
            # Extract prefix (everything up to and including "trake")
            prefix = question.split("trake")[0] + "trake"
            trake_groups[prefix].append((question, entries))
        elif "kis" in question:
            # Handle kis questions - output video_id, frame_idx
            csv_path = os.path.join(output_dir, f"{question}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for entry in entries:
                    video_id = extract_video_id(entry["video_path"])
                    writer.writerow([video_id, get_frame_idx(entry)])
        elif "qa" in question:
            # Handle qa questions - output video_id, frame_idx, answer
            csv_path = os.path.join(output_dir, f"{question}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for entry in entries:
                    video_id = extract_video_id(entry["video_path"])
                    writer.writerow([video_id, get_frame_idx(entry), entry["answer"]])
    
    # Handle trake questions
    for prefix, question_entries in trake_groups.items():
        csv_path = os.path.join(output_dir, f"{prefix}.csv")
        
        # Sort questions by their suffix (the part after "trake")
        question_entries.sort(key=lambda x: x[0].split("trake")[1] if x[0].split("trake")[1] else "")
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Process each trake question separately
            for question, entries in question_entries:
                # Group entries by video_path for this specific question
                video_data = defaultdict(list)
                
                for entry in entries:
                    video_id = extract_video_id(entry["video_path"])

                    video_data[video_id].append(get_frame_idx(entry))
                
                # Write one row per video for this specific trake question
                for video_id, frame_indices in video_data.items():
                    # Sort frame indices for consistent output
                    frame_indices.sort()
                    writer.writerow([video_id] + frame_indices)
                    
def convert_json_to_csv(json_file_path, output_dir="submission"):
    """
    Main function to convert JSON file to CSV files
    
    Args:
        json_file_path (str): Path to the input JSON file
        output_dir (str): Output directory for CSV files (default: "submission")
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if input file exists
        if not os.path.exists(json_file_path):
            print(f"Error: JSON file '{json_file_path}' not found")
            return False
        
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data
        process_json_to_csv(data, output_dir)
        print(f"✅ Successfully converted '{json_file_path}' to CSV files in '{output_dir}' folder")
        
        # List created files
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        print(f"📁 Created {len(csv_files)} CSV files:")
        for file in sorted(csv_files):
            print(f"   - {file}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_file_path}': {e}")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    """Example usage"""
    # Example with test data
    example_data = {
        "query-p1-3-kis": [
            {
                "video_path": "/root/data/unzipped/video/L30_V096.mp4",
                "timestamp": 39.256184,
                "frame_idx": 981,
                "submitted_at": "2025-08-29T15:22:09.705193"
            }
        ],
        "query-p1-3-qa": [
            {
                "video_path": "/root/data/unzipped/video/L30_V096.mp4",
                "timestamp": 39.256184,
                "frame_idx": 981,
                "submitted_at": "2025-08-29T15:22:09.705193",
                "answer": "90 triệu đồng"
            }
        ],
        "query-p1-6-trake0": [
            {
                "frame_idx": 2123,
                "submitted_at": "2025-08-29T15:21:02.264063",
                "timestamp": 84.927331,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            },
            {
                "frame_idx": 4119,
                "submitted_at": "2025-08-29T15:21:28.628723",
                "timestamp": 164.777429,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            },
            {
                "frame_idx": 4643,
                "submitted_at": "2025-08-29T15:20:23.126161",
                "timestamp": 185.728521,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            }
        ],
        "query-p1-6-trake2a": [
            {
                "frame_idx": 2120,
                "submitted_at": "2025-08-29T15:21:02.264063",
                "timestamp": 84.927331,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            },
            {
                "frame_idx": 4119,
                "submitted_at": "2025-08-29T15:21:28.628723",
                "timestamp": 164.777429,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            },
            {
                "frame_idx": 4643,
                "submitted_at": "2025-08-29T15:20:23.126161",
                "timestamp": 185.728521,
                "video_path": "/root/data/unzipped/video/L26_V406.mp4"
            }
        ]
    }
    
    # Create example JSON file for testing
    with open("example_data.json", "w", encoding="utf-8") as f:
        json.dump(example_data, f, indent=2, ensure_ascii=False)
    
    # Convert the example file
    convert_json_to_csv("example_data.json")

# Legacy function for backward compatibility
def process_json_file(json_file_path="/home/nguyentnt/a/FRED-Video-Search-System-Resumable/submit_server/submissions.json", output_dir="submission/submission"):
    """
    Legacy function - use convert_json_to_csv instead
    """
    return convert_json_to_csv(json_file_path, output_dir)

process_json_file()
# if __name__ == "__main__":
#     main()
    
#     # Uncomment the line below to process a JSON file instead of example data
#     # process_json_file("your_input_file.json")