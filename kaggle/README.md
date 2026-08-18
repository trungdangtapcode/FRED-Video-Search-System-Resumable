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
`data/extraction_status`, so every archive can be extracted at the repository
root without a shard wrapper or filename collisions.

The plan contains 873 videos in 28 shards. Metadata paths inside each tar are
repository-relative, for example
`data/extracted_keyframes/L21_V001/00000.png`.
