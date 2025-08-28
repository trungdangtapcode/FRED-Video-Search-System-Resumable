import os
from dotenv import load_dotenv

load_dotenv()

# Modify as needed
FRAMES_METADATA_PATH = os.getenv("FRAMES_METADATA_PATH", "/root/data/frames_metadata.json")
VIDEOS_METADATA_PATH = os.getenv("VIDEOS_METADATA_PATH", "/root/data/videos_metadata.json")
# MODEL_NAME = "hf-hub:timm/PE-Core-bigG-14-448"
MODEL_NAME = "hf-hub:timm/ViT-gopt-16-SigLIP2-384"
DEVICE = "cuda"

print("FRAMES_METADATA_PATH:", FRAMES_METADATA_PATH)	