# Data layout

This directory contains local datasets and generated search artifacts. Its
contents are intentionally excluded from Git, except for this file.

```text
data/
|-- downloads/              Original ZIP archives
|-- unzipped/
|   |-- video/              Source videos
|   |-- media-info/         Per-video source metadata
|   |-- keyframes/          Optional supplied keyframes
|   `-- map-keyframes/      Optional supplied keyframe CSV maps
|-- extracted_keyframes/    Frames generated from source videos
|-- compressed_keyframes/   Optional optimized copies of extracted frames
|-- frame_metadata/         Resumable per-video frame metadata
|-- extraction_status/      Per-video completion manifests and locks
|-- embedding/              Intermediate embedding arrays
|-- frames_metadata_v2.json Frame-to-video metadata used by the backend
|-- fps_dict_v2.json        Video FPS lookup used for submissions
`-- embeddings_qwen3_vl_8b.index
                            4096-D Qwen3-VL cosine FAISS index
```

The current local dataset contains all 873 source videos and `media-info` JSON
files from L21 through L30. The imported two-second keyframe set contains
235,588 PNGs across the same 873 video IDs. `frames_metadata_v2.json` and
`fps_dict_v2.json` are generated and ready for the backend and submission
tools. The current FAISS index contains 235,588 aligned 4,096-dimensional
Qwen3-VL rows from all 28 real shards; no zero placeholder rows remain.

`compressed_keyframes` is intentionally not generated: the current UI and
embedding tools read `frame_path` directly, and a compressed copy would consume
additional shared storage. The validated final FAISS index is kept under
`data/`; the temporary combined NPY is removed after each successful rebuild to
avoid wasting shared storage.

## Downloaded embedding shards

The 28 real shard arrays are under `data/embedding/shards/`, with their Kaggle
sources recorded in `manifests/aic-2026/embedding-shards.json`. Every shard is
a float32, two-dimensional array with 4,096 columns and the exact row count
recorded for that shard.

After all downloads finish, run these commands from the repository root:

```bash
# Validate all 28 real shards.
.venv-services/bin/python embedding/concat_embedding_shards.py --check-only

# Concatenate them in the verified global lexicographic frame order.
.venv-services/bin/python embedding/concat_embedding_shards.py

# Normalize vectors and build the cosine-similarity FAISS index.
.venv-services/bin/python embedding/convert_npy_to_faiss.py

# Start the UI, API, FAISS retriever, static server, and submission server.
./run_local.sh
```

The concatenation and conversion scripts process arrays in chunks. They reject
unreplaced placeholders, missing shards, wrong row counts, wrong dimensions,
NaN/Inf values, zero-length embeddings, and output read-back failures.
