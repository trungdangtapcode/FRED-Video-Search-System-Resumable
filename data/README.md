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
|-- compressed_keyframes/   Optimized frames served by the UI
|-- frame_metadata/         Resumable per-video frame metadata
|-- extraction_status/      Per-video completion manifests and locks
|-- embedding/              Intermediate embedding arrays
|-- frames_metadata_v2.json Frame-to-video metadata used by the backend
|-- fps_dict_v2.json        Video FPS lookup used for submissions
`-- embeddings_siglip_v2.index
                            FAISS search index
```

The current local dataset contains the L21 videos and the available
`media-info` JSON files. Frame metadata, keyframes, FPS metadata, and the FAISS
index must still be generated or supplied before the full search stack can run.
