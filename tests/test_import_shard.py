import json
import tempfile
import unittest
from pathlib import Path

from keyframe_extraction.import_shard import import_shard


class ImportShardTests(unittest.TestCase):
    def test_imports_and_rewrites_a_shard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            video_id = "L21_V001"
            video = root / "data" / "unzipped" / "video" / f"{video_id}.mp4"
            video.parent.mkdir(parents=True)
            video.write_bytes(b"video")

            staging = root / "staging"
            payload = staging / "unexpected-root-name" / "data"
            frames = payload / "extracted_keyframes" / video_id
            frames.mkdir(parents=True)
            (frames / "00000.png").write_bytes(b"png")
            metadata_dir = payload / "frame_metadata"
            metadata_dir.mkdir()
            (metadata_dir / f"{video_id}.json").write_text(
                json.dumps([{
                    "video_path": "data/unzipped/video/L21_V001.mp4",
                    "fps": 30.0,
                    "timestamp": 0.0,
                    "frame_idx": 0,
                    "frame_path": "data/extracted_keyframes/L21_V001/00000.png",
                }]),
                encoding="utf-8",
            )
            status_dir = payload / "extraction_status"
            status_dir.mkdir()
            (status_dir / f"{video_id}.done.json").write_text(
                json.dumps({
                    "version": 1,
                    "video_id": video_id,
                    "source": {"path": "/kaggle/input/video.mp4", "size": 1, "mtime_ns": 1},
                    "interval_seconds": 2.0,
                    "frame_count": 1,
                }),
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({
                    "shard_id": "L21_p01",
                    "interval_seconds": 2.0,
                    "videos": [{"video_id": video_id, "filename": f"{video_id}.mp4"}],
                }),
                encoding="utf-8",
            )

            summary = import_shard(staging, manifest, project_root=root, cleanup=True)

            self.assertEqual(summary["frame_count"], 1)
            imported = json.loads(
                (root / "data" / "frame_metadata" / f"{video_id}.json").read_text()
            )
            self.assertEqual(imported[0]["video_path"], str(video.resolve()))
            self.assertEqual(
                imported[0]["frame_path"],
                str((root / "data" / "extracted_keyframes" / video_id / "00000.png").resolve()),
            )
            self.assertFalse((staging / "unexpected-root-name").exists())


if __name__ == "__main__":
    unittest.main()
