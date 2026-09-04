import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

ROOT_DIR = str((PROJECT_ROOT / "data").resolve())
FPS_VIDEO_PATH = str((PROJECT_ROOT / "data" / "fps_dict_v2.json").resolve())
SUBMISSIONS_FILE = str((Path(__file__).resolve().parent / "submissions.json").resolve())
STATEMENTS_FILE = str((Path(__file__).resolve().parent / "statement.csv").resolve())
MEDIA_BASE_URL = os.getenv("VITE_MEDIA_BASE_URL", "").rstrip("/")


def public_media_url(relative_path: str) -> str:
    """Build a public media URL while rejecting path traversal."""
    if not MEDIA_BASE_URL:
        raise RuntimeError("VITE_MEDIA_BASE_URL is not configured")

    normalized = str(relative_path).replace("\\", "/").lstrip("/")
    parts = tuple(part for part in normalized.split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError("Invalid media path")

    return f"{MEDIA_BASE_URL}/{quote('/'.join(parts), safe='/')}"
