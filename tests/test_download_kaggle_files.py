import tempfile
import unittest
from pathlib import Path

from keyframe_extraction.download_kaggle_files import _safe_target


class SafeTargetTest(unittest.TestCase):
    def test_accepts_nested_dataset_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                _safe_target(root, "L25_p01/data/frame_metadata/L25_V001.json"),
                root / "L25_p01/data/frame_metadata/L25_V001.json",
            )

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../outside", "/absolute", "nested/../../outside"):
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        _safe_target(root, name)


if __name__ == "__main__":
    unittest.main()
