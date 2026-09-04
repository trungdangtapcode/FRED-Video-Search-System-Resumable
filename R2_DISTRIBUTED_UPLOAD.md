# Distributed R2 media upload

This guide is for helpers uploading assigned source-video archives or keyframe
shards. Each helper must be assigned a different unit. The uploader converts
the archive into the repository layout while keeping at most one ZIP on local
disk.

## Destination format

R2 objects are stored as individual files, not as ZIP files:

```text
fred/data/unzipped/video/L21_V001.mp4
fred/data/unzipped/video/L21_V002.mp4
...
```

The uploader also writes one completion manifest for each source archive:

```text
fred/manifests/videos/Videos_L21_a.zip.jsonl
```

Object keys must never contain a local prefix such as `/home/user/`. Do not
rename videos, change letter case, upload ZIPs under `fred/data`, or create a
different R2 prefix.

## Coordinator rules

1. Assign each archive to exactly one person.
2. Give every person separate R2 S3 credentials with Object Read and Write
   access limited to the target bucket. Do not send credentials in a group
   chat or commit them to Git.
3. Each person uses their own Kaggle API token. `R2_TOKEN` is not needed.
4. Do not assign `media-info-aic25-b1.zip`; it is already uploaded.
5. A helper must run only one uploader process per repository checkout because
   all runs share `data/r2_upload_stage`.

Assignable video archives:

```text
Videos_L21_a.zip
Videos_L22_a.zip
Videos_L23_a.zip
Videos_L24_a.zip
Videos_L25_a.zip
Videos_L26_a.zip
Videos_L26_b.zip
Videos_L26_c.zip
Videos_L26_d.zip
Videos_L26_e.zip
Videos_L27_a.zip
Videos_L28_a.zip
Videos_L29_a.zip
Videos_L30_a.zip
```

## One-time worker setup

Python 3.10 or newer and `curl` are required.

```bash
git clone https://github.com/trungdangtapcode/FRED-Video-Search-System-Resumable.git
cd FRED-Video-Search-System-Resumable

python3 -m venv .venv-r2
.venv-r2/bin/python -m pip install boto3 requests kaggle
```

The coordinator should privately supply the four R2 values. Quote every value:

```bash
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
export R2_S3_CLIENT_URL="https://ACCOUNT_ID.r2.cloudflarestorage.com"
export R2_BUCKET="..."

# Each helper creates and uses their own Kaggle token.
export KAGGLE_API_TOKEN="..."
```

Never paste the output of `env`, `export`, or `set` into a log or chat because
those commands can disclose credentials.

## Upload one assigned video archive

Replace `Videos_L26_c.zip` with the exact archive assigned by the coordinator:

```bash
.venv-r2/bin/python utils/upload_media_to_r2.py \
  --phase videos \
  --only-archive Videos_L26_c.zip \
  --prefix fred \
  --max-temp-gb 30 \
  2>&1 | tee Videos_L26_c.upload.log
```

For a connection that may close, run the command inside `tmux`:

```bash
tmux new -s r2-video-L26-c
```

Then run the upload command inside that terminal. Detach without stopping it
with `Ctrl-B`, then `D`. Reattach with:

```bash
tmux attach -t r2-video-L26-c
```

If interrupted, run the exact same upload command again. The source ZIP resumes
from its partial download, and correctly sized R2 objects are skipped. The ZIP
is deleted automatically only after every MP4 and the archive manifest have
been verified.

Success ends with messages similar to:

```text
completed and removed temporary archive Videos_L26_c.zip
assigned unit complete; global manifest index left unchanged
upload complete
```

Send the coordinator the archive name and those final three log lines. Do not
manually delete a partial staging file unless the coordinator asks.

## Multiple archives on one worker

Run assigned archives sequentially so temporary storage remains bounded:

```bash
for archive in Videos_L26_c.zip Videos_L26_d.zip; do
  .venv-r2/bin/python utils/upload_media_to_r2.py \
    --phase videos \
    --only-archive "$archive" \
    --prefix fred \
    --max-temp-gb 30 \
    2>&1 | tee "$archive.upload.log" || break
done
```

## Upload one assigned keyframe shard

Keyframe workers also need their own Kaggle token:

```bash
export KAGGLE_API_TOKEN="..."
```

Replace `L30_p01` with the exact shard assigned by the coordinator:

```bash
.venv-r2/bin/python utils/upload_media_to_r2.py \
  --phase keyframes \
  --only-shard L30_p01 \
  --prefix fred \
  --max-temp-gb 30 \
  --keyframe-workers 8 \
  2>&1 | tee L30_p01.upload.log
```

This downloads one Kaggle dataset ZIP, validates its expected video and frame
counts, and uploads individual objects such as:

```text
fred/data/extracted_keyframes/L30_V001/00000.png
```

It writes the completion manifest `fred/manifests/keyframes/L30_p01.jsonl` and
deletes the ZIP only after every PNG has been verified. If interrupted, rerun
the exact same command. Do not upload Kaggle ZIPs directly into R2.

To process multiple assigned shards, run them sequentially. Using reverse order
helps avoid overlap with a coordinator working from `L21_p01` upward:

```bash
for shard in L30_p01 L29_p02 L29_p01; do
  .venv-r2/bin/python utils/upload_media_to_r2.py \
    --phase keyframes \
    --only-shard "$shard" \
    --prefix fred \
    --max-temp-gb 30 \
    --keyframe-workers 8 \
    2>&1 | tee "$shard.upload.log" || break
done
```

## Final coordinator verification

After helpers finish, the coordinator runs:

```bash
python3 utils/upload_media_to_r2.py \
  --phase all \
  --prefix fred \
  --max-temp-gb 30
```

The coordinator reads each known worker manifest directly from R2, validates
its paths and counts, skips completed archives and shards, fills any missing
units, verifies global coverage, and writes:

```text
fred/manifests/media-upload-index.json
```

The expected final coverage is 873 MP4 files and 235,588 PNG keyframes.
