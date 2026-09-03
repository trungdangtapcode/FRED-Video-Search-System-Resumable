from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_DIR = str((PROJECT_ROOT / "data").resolve())
FPS_VIDEO_PATH = str((PROJECT_ROOT / "data" / "fps_dict_v2.json").resolve())
SUBMISSIONS_FILE = str((Path(__file__).resolve().parent / "submissions.json").resolve())
STATEMENTS_FILE = str((Path(__file__).resolve().parent / "statement.csv").resolve())
