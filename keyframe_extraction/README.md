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

`--start` and `--limit` split by video count only. For datasets whose video
durations vary, build duration-balanced manifests instead:

```bash
.venv/bin/python -m keyframe_extraction.plan \
  --input data/unzipped/video \
  --output manifests/generated \
  --target-hours 5.75 \
  --interval 2
```

The planner keeps the filename prefix before the first underscore (`L21`,
`L22`, and so on) as a group, then creates contiguous `part-001` manifests
inside each group. Pass `--mix-groups` only when preserving those boundaries is
not important.

Run one shard by passing its manifest. `--run-dir` keeps every artifact for the
shard below one output directory:

```bash
.venv/bin/python -m keyframe_extraction \
  --input data/unzipped/video \
  --manifest manifests/generated/L25/part-003.json \
  --run-dir data/runs/L25/part-003 \
  --workers 4
```

The checked-in `manifests/aic25-b1` plan contains all 873 videos in 28 shards
targeting about 10 GB of PNG output per shard.
`kaggle/keyframe_shard_template.ipynb` is the ready-to-import Kaggle notebook;
duplicate it and change only its `SHARD` setting. The underlying command is:

```bash
python -m keyframe_extraction \
  --input /kaggle/input/datasets/truonghaha/aic-2026-dataset \
  --manifest manifests/aic25-b1/L25/part-003.json \
  --output /kaggle/working/data/extracted_keyframes \
  --metadata-dir /kaggle/working/data/frame_metadata \
  --status-dir /kaggle/working/data/extraction_status \
  --workers 4 \
  --no-merge
```

Rerunning the same command skips every video whose frames, metadata, source
signature, interval, and completion manifest are still valid.

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
