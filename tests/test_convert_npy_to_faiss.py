import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import faiss
    import numpy as np
except ImportError:  # The lightweight keyframe environment does not need these.
    faiss = None
    np = None


@unittest.skipIf(faiss is None or np is None, "FAISS and NumPy are required")
class ConvertNpyToFaissTests(unittest.TestCase):
    def test_validates_normalizes_and_writes_index(self):
        project_root = Path(__file__).resolve().parents[1]
        script = project_root / "embedding" / "convert_npy_to_faiss.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            metadata_path = temp / "metadata.json"
            npy_path = temp / "vectors.npy"
            index_path = temp / "vectors.index"
            metadata_path.write_text(json.dumps([
                {"frame_path": "/frames/L21_V001/00000.png"},
                {"frame_path": "/frames/L21_V001/00001.png"},
                {"frame_path": "/frames/L21_V002/00000.png"},
            ]))
            np.save(npy_path, np.full((3, 4), 2.0, dtype=np.float16))

            subprocess.run([
                sys.executable,
                str(script),
                str(npy_path),
                "--metadata", str(metadata_path),
                "--output", str(index_path),
                "--expected-dimension", "4",
            ], check=True, capture_output=True, text=True)

            index = faiss.read_index(str(index_path))
            self.assertEqual((index.ntotal, index.d), (3, 4))
            self.assertAlmostEqual(float(np.linalg.norm(index.reconstruct(0))), 1.0)

    def test_preserves_explicitly_allowed_zero_vector(self):
        project_root = Path(__file__).resolve().parents[1]
        script = project_root / "embedding" / "convert_npy_to_faiss.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            metadata_path = temp / "metadata.json"
            npy_path = temp / "vectors.npy"
            index_path = temp / "vectors.index"
            metadata_path.write_text(json.dumps([
                {"frame_path": "/frames/L21_V001/00000.png"},
                {"frame_path": "/frames/L21_V001/00001.png"},
            ]))
            np.save(npy_path, np.array([[1, 0, 0, 0], [0, 0, 0, 0]], dtype=np.float32))

            subprocess.run([
                sys.executable,
                str(script),
                str(npy_path),
                "--metadata", str(metadata_path),
                "--output", str(index_path),
                "--expected-dimension", "4",
                "--allow-zero-vectors",
            ], check=True, capture_output=True, text=True)

            index = faiss.read_index(str(index_path))
            np.testing.assert_array_equal(index.reconstruct(1), np.zeros(4))


if __name__ == "__main__":
    unittest.main()
