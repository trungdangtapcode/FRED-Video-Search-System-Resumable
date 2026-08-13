# Keyframe extraction CLI

Run commands from the repository root. By default, the extractor reads
`data/unzipped/video`, saves one PNG every two seconds, and uses up to four
worker processes:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-keyframes.txt
.venv/bin/python -m keyframe_extraction
```

Process one video or a sorted subset:

```bash
.venv/bin/python -m keyframe_extraction --video L21_V001 --workers 1
.venv/bin/python -m keyframe_extraction --start 0 --limit 10 --workers 4
```

Completed videos are skipped when the source file, interval, frame files,
metadata, and completion manifest still match. Use `--force` to replace a
completed result. A failed video does not discard results from other workers.

Generated files:

```text
data/extracted_keyframes/<video-id>/*.png
data/frame_metadata/<video-id>.json
data/extraction_status/<video-id>.done.json
data/frames_metadata_v2.json
```

Run `.venv/bin/python -m keyframe_extraction --help` for all options.
