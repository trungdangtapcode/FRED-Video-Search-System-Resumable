import os
from dotenv import load_dotenv

load_dotenv()

# Modify as needed
FRAMES_METADATA_PATH = os.getenv("FRAMES_METADATA_PATH", "metadata/metadata.json")
MODEL_NAME = "hf-hub:timm/PE-Core-bigG-14-448"
DEVICE = "cuda"

print("FRAMES_METADATA_PATH:", FRAMES_METADATA_PATH)	