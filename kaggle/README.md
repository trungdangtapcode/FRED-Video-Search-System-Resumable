# Kaggle keyframe shards

Dataset: `truonghaha/aic-2026-dataset`. Use a CPU notebook with Internet on.

Duplicate `keyframe_shard_template.ipynb` once per entry in
`../manifests/aic-2026/index.json`. Name notebooks `aic-keyframes-lxx-pnn` and
change only this line:

```python
SHARD = "L21/part-001.json"
```

Choose **Save Version -> Save & Run All**. A successful notebook output has two
files such as `L21_p01.tar` and `L21_p01.tar.sha256`. The tar contains the shared
layout `data/extracted_keyframes`, `data/frame_metadata`, and
`data/extraction_status`, so archives can be extracted into the same directory.

The plan contains 754 videos in 25 shards. `../manifests/aic-2026/lanes-3.json`
assigns the jobs to three equal 36.93-hour lanes.
