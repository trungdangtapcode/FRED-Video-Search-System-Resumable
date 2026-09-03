import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    from embedding.concat_embedding_shards import (
        ShardSpec,
        concatenate,
        load_layout,
        validate_shards,
    )
except ImportError:  # The keyframe-only environment does not need NumPy.
    np = None


@unittest.skipIf(np is None, "NumPy is required")
class ConcatEmbeddingShardsTests(unittest.TestCase):
    def test_repository_layout_matches_all_frames(self):
        specs = load_layout()
        self.assertEqual(len(specs), 28)
        self.assertEqual(sum(spec.rows for spec in specs), 235_588)

    def test_validates_and_concatenates_in_spec_order(self):
        specs = [
            ShardSpec("first", 2, ("L21_V001",)),
            ShardSpec("second", 1, ("L21_V002",)),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            np.save(root / "first.npy", np.array([[1, 2], [3, 4]], dtype=np.float16))
            np.save(root / "second.npy", np.array([[5, 6]], dtype=np.float16))
            arrays = validate_shards(specs, root, dimension=2)
            output = root / "combined.npy"

            rows, dimension, dtype = concatenate(arrays, output, chunk_size=1)

            self.assertEqual((rows, dimension, dtype), (3, 2, np.dtype("float16")))
            np.testing.assert_array_equal(
                np.load(output),
                np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float16),
            )

    def test_rejects_zero_row_placeholder(self):
        specs = [ShardSpec("waiting", 2, ("L21_V001",))]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            np.save(root / "waiting.npy", np.empty((0, 1536), dtype=np.float32))
            with self.assertRaisesRegex(RuntimeError, "placeholders not replaced"):
                validate_shards(specs, root, dimension=1536)

    def test_preserves_intentional_zero_shard_as_sparse_range(self):
        specs = [ShardSpec("missing", 2, ("L21_V001",), allow_zero=True)]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            np.save(root / "missing.npy", np.zeros((2, 4), dtype=np.float32))
            arrays = validate_shards(specs, root, dimension=4)
            output = root / "combined.npy"

            rows, dimension, dtype = concatenate(arrays, output, chunk_size=1)

            self.assertEqual((rows, dimension, dtype), (2, 4, np.dtype("float32")))
            np.testing.assert_array_equal(np.load(output), np.zeros((2, 4)))


if __name__ == "__main__":
    unittest.main()
