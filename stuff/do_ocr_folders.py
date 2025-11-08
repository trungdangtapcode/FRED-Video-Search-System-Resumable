import os
import json
from glob import glob
from tqdm import tqdm
import subprocess
import sys
import tempfile
import shutil
from demo.batch_demo import setup_cfg, load_images
from demo.batch_predictor import BatchPredictor
from adet.utils.visualizer import group_words_into_lines, split_line_by_x_gap

def get_all_images(folder):
    exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    image_paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(exts):
                image_paths.append(os.path.join(root, file))
    return sorted(image_paths)

def batch_ocr_images(image_paths, config_file, weights, output_json_path):
    """
    Run demo.py on a list of images and save the output JSON.
    Args:
        image_paths: list of image file paths
        config_file: path to config yaml
        weights: path to model weights
        output_json_path: where to save the recognized_words.json
    Returns:
        Dict of {image_path: [lines]}
    """
    import subprocess
    import sys
    all_results = {}
    cmd = [
        sys.executable, 'demo/demo.py',
        '--config-file', config_file,
        '--input', *image_paths,
        '--output', output_json_path,
        '--opts', 'MODEL.WEIGHTS', weights
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    # Read recognized_words.json from output_json_path
    if os.path.exists(output_json_path):
        with open(output_json_path, 'r', encoding='utf-8') as f:
            batch_results = json.load(f)
        all_results.update(batch_results)
    return all_results

if __name__ == "__main__":
    root_dir = "/media/tin/HDD500GB/hcmcAIC25/data/Keyframes_L21/keyframes/"  # Change to your folder containing all videos/subfolders
    output_dir = "./ocr_jsons"        # Change to your desired output folder
    config_file = "configs/Bridge/TotalText/R_50_poly.yaml"  # Change to your config
    weights = "checkpoints/Bridge_tt.pth"    # Change to your weights
    os.makedirs(output_dir, exist_ok=True)

    for video_folder in tqdm(os.listdir(root_dir)):
        video_path = os.path.join(root_dir, video_folder)
        if not os.path.isdir(video_path):
            continue
        print("===========",video_path,"===========")
        image_paths = get_all_images(video_path)
        if not image_paths:
            continue
        print(f"Processing {video_folder} with {len(image_paths)} images...")
        output_json = os.path.join(output_dir, f"{video_folder}.json")
        ocr_results = batch_ocr_images(image_paths, config_file, weights, output_json)
        print(f"Saved OCR results to {output_json}")
