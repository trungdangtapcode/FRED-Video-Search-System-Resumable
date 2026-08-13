import json
import tempfile
import unittest
from pathlib import Path

from keyframe_extraction.pipeline import (
    ExtractionJob,
    MANIFEST_VERSION,
    build_jobs,
    discover_videos,
    extract_video_job,
    merge_completed_metadata,
    run_jobs,
    validate_completed_job,
)


class DiscoverVideosTests(unittest.TestCase):
    def test_filters_sorts_selects_and_slices(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("B.mp4", "A.MOV", "ignore.txt", "C.mkv"):
                (root / name).touch()

            videos = discover_videos(root, start=1, limit=1)
            self.assertEqual([path.name for path in videos], ["B.mp4"])

            videos = discover_videos(root, selected_videos=["C"])
            self.assertEqual([path.name for path in videos], ["C.mkv"])

    def test_rejects_missing_selected_video(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "Videos not found: missing"):
                discover_videos(Path(temp_dir), selected_videos=["missing"])


class ResumeAndMergeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.video = self.root / "video" / "L21_V001.mp4"
        self.video.parent.mkdir()
        self.video.write_bytes(b"video")
        self.output_root = self.root / "frames"
        self.metadata_dir = self.root / "metadata"
        self.status_dir = self.root / "status"
        self.job = ExtractionJob(
            video_path=str(self.video.resolve()),
            output_root=str(self.output_root.resolve()),
            metadata_dir=str(self.metadata_dir.resolve()),
            status_dir=str(self.status_dir.resolve()),
            interval=2.0,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_completed_job(self, frame_count=2):
        self.job.output_dir.mkdir(parents=True)
        self.job.metadata_path.parent.mkdir(parents=True)
        self.job.status_path.parent.mkdir(parents=True)
        metadata = []
        for index in range(frame_count):
            frame_path = self.job.output_dir / f"{index:05d}.png"
            frame_path.write_bytes(b"png")
            metadata.append(
                {
                    "video_path": str(self.video.resolve()),
                    "fps": 25.0,
                    "timestamp": index * 2.0,
                    "frame_idx": index * 50,
                    "frame_path": str(frame_path.resolve()),
                }
            )
        self.job.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        stat = self.video.stat()
        manifest = {
            "version": MANIFEST_VERSION,
            "video_id": self.job.video_id,
            "source": {
                "path": str(self.video.resolve()),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            },
            "interval_seconds": 2.0,
            "frame_count": frame_count,
        }
        self.job.status_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_completed_job_can_resume(self):
        self._write_completed_job()
        self.assertEqual(validate_completed_job(self.job), (True, 2))

        changed_job = ExtractionJob(**{**self.job.__dict__, "interval": 5.0})
        self.assertEqual(validate_completed_job(changed_job), (False, 0))

    def test_missing_or_empty_frame_invalidates_manifest(self):
        self._write_completed_job()
        (self.job.output_dir / "00001.png").write_bytes(b"")
        self.assertEqual(validate_completed_job(self.job), (False, 0))

    def test_merge_is_sorted_by_video_manifest(self):
        self._write_completed_job(frame_count=2)
        output = self.root / "frames_metadata_v2.json"

        videos, frames, intervals = merge_completed_metadata(
            self.metadata_dir, self.status_dir, output
        )

        self.assertEqual((videos, frames, intervals), (1, 2, [2.0]))
        merged = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["frame_idx"], 0)


class OpenCvIntegrationTests(unittest.TestCase):
    @staticmethod
    def _write_video(cv2, np, path, frame_count=20):
        path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"MJPG"),
            10.0,
            (64, 48),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not create test video: {path}")
        for index in range(frame_count):
            writer.write(np.full((48, 64, 3), index * 10, dtype=np.uint8))
        writer.release()

    def test_extracts_then_skips_completed_video(self):
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV and NumPy are required for the integration test")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            video_path = root / "video" / "sample.avi"
            self._write_video(cv2, np, video_path)

            job = ExtractionJob(
                video_path=str(video_path.resolve()),
                output_root=str((root / "frames").resolve()),
                metadata_dir=str((root / "metadata").resolve()),
                status_dir=str((root / "status").resolve()),
                interval=0.5,
            )

            first = extract_video_job(job)
            second = extract_video_job(job)

            self.assertEqual((first.status, first.frame_count), ("completed", 4))
            self.assertEqual((second.status, second.frame_count), ("skipped", 4))
            self.assertEqual(validate_completed_job(job), (True, 4))

    def test_processes_multiple_videos_concurrently(self):
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV and NumPy are required for the integration test")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "video"
            self._write_video(cv2, np, input_dir / "A.avi")
            self._write_video(cv2, np, input_dir / "B.avi")
            jobs = build_jobs(
                discover_videos(input_dir),
                output_root=root / "frames",
                metadata_dir=root / "metadata",
                status_dir=root / "status",
                interval=0.5,
                force=False,
            )

            first = run_jobs(jobs, workers=2)
            second = run_jobs(jobs, workers=2)

            self.assertEqual([result.status for result in first], ["completed"] * 2)
            self.assertEqual([result.frame_count for result in first], [4, 4])
            self.assertEqual([result.status for result in second], ["skipped"] * 2)


if __name__ == "__main__":
    unittest.main()
