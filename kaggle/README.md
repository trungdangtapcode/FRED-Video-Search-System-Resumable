# Kaggle keyframe shards

## Upload existing keyframe datasets directly to R2

Use [`r2_upload_keyframe_shard.ipynb`](r2_upload_keyframe_shard.ipynb) when the
keyframes already exist as a Kaggle dataset. This is the preferred path for the
28 published keyframe datasets because it does not route their contents through
the application VPS or copy them into `/kaggle/working`.

For each worker notebook:

1. Use a CPU notebook and enable Internet.
2. Attach exactly one keyframe dataset listed in
   `../manifests/aic-2026/media-sources.json`.
3. Add and enable the Kaggle User Secrets `R2_ACCESS_KEY_ID`,
   `R2_SECRET_ACCESS_KEY`, `R2_S3_CLIENT_URL`, and `R2_BUCKET`. Do not put their
   values in a notebook cell or notebook output. `R2_TOKEN` is not used by the
   S3-compatible client.
4. Copy the notebook and change only `SHARD_ID`, for example `L30_p01`.
5. Choose **Save Version -> Save & Run All**. Success ends with `DONE Lxx_pyy`
   and produces a small `Lxx_pyy.r2-summary.json` notebook output.

Distinct shards may run concurrently. Never intentionally assign the same
shard to two active notebooks: it is safe because matching objects are skipped,
but it wastes Kaggle and R2 requests. Each worker writes only
`fred/manifests/keyframes/Lxx_pyy.jsonl`; it never writes the shared global
manifest. The upload is resumable through R2 `HEAD` checks and needs no
`ListBucket` permission.

The direct-upload notebook validates the expected frame count, video count,
path format, duplicate destinations, and PNG signatures before uploading. R2
objects use the repository-native layout:

```text
fred/data/extracted_keyframes/L21_V001/00000.png
fred/data/extracted_keyframes/L21_V001/00001.png
...
fred/manifests/keyframes/L21_p01.jsonl
```

## Extract keyframes on Kaggle

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
