import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")).resolve()

FRAMES_METADATA_PATH = os.getenv(
    "FRAMES_METADATA_PATH", str(DATA_DIR / "frames_metadata_v2.json")
)
MODEL_NAME = os.getenv(
    "MODEL_NAME", "Qwen/Qwen3-VL-Embedding-8B"
)
MODEL_REVISION = os.getenv(
    "MODEL_REVISION", "2c4565515e0f265c6511776e7193b22c0968ddc7"
)
DEVICE = os.getenv("DEVICE", "cuda")
RETRIEVER_URL = os.getenv("RETRIEVER_URL", "http://localhost:50239")

print("FRAMES_METADATA_PATH:", FRAMES_METADATA_PATH)
