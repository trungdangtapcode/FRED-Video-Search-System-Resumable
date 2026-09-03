import json
import tempfile
import unittest
from pathlib import Path

from keyframe_extraction.finalize import finalize_artifacts


class FinalizeArtifactsTest(unittest.TestCase):
    def test_validates_and_writes_runtime_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "video"
            output_root = root / "frames"
            metadata_dir = root / "metadata"
            status_dir = root / "status"
            source_dir.mkdir()
            metadata_dir.mkdir()
            status_dir.mkdir()
            video = source_dir / "L21_V001.mp4"
            video.write_bytes(b"video")
            frame_dir = output_root / video.stem
            frame_dir.mkdir(parents=True)
            frame = frame_dir / "00000.png"
            frame.write_bytes(b"png")
            metadata = [{
                "video_path": str(video.resolve()),
                "fps": 25.0,
                "timestamp": 0.0,
                "frame_idx": 0,
                "frame_path": str(frame.resolve()),
            }]
            (metadata_dir / "L21_V001.json").write_text(json.dumps(metadata), encoding="utf-8")
            stat = video.stat()
            status = {
                "version": 1,
                "video_id": "L21_V001",
                "source": {
                    "path": str(video.resolve()),
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                },
                "interval_seconds": 2.0,
                "fps": 25.0,
                "frame_count": 1,
            }
            (status_dir / "L21_V001.done.json").write_text(json.dumps(status), encoding="utf-8")

            merged = root / "frames_metadata_v2.json"
            fps_dict = root / "fps_dict_v2.json"
            summary = finalize_artifacts(
                source_dir, output_root, metadata_dir, status_dir, merged, fps_dict
            )

            self.assertEqual(summary["video_count"], 1)
            self.assertEqual(summary["frame_count"], 1)
            self.assertEqual(json.loads(fps_dict.read_text()), {"L21_V001": 25.0})
            self.assertEqual(len(json.loads(merged.read_text())), 1)


if __name__ == "__main__":
    unittest.main()
