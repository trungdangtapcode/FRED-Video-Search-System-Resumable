# Kaggle keyframe shard notebooks

Use `keyframe_shard_template.ipynb` as the source for every extraction job.
Create a separate Kaggle notebook for each shard so every saved output remains
independently attachable and rerunnable.

Notebook settings:

- Input: `khoahunhtngng/aic2024-round1-data`
- Accelerator: None (CPU)
- Internet: On, required to clone the pinned public repository tag
- Persistence: Files, when using an interactive session

Change only the `SHARD` value in the first code cell and make the notebook title
match it. For example:

```python
SHARD = "L25/part-003.json"
```

Use the title `aic-keyframes-L25-p03`. The notebook derives the manifest and
output paths from that value. Do not put multiple shards into one notebook run.

All available jobs are listed in `../manifests/aic25-b1/index.json`. The exact
balanced assignment for three independent runners is in
`../manifests/aic25-b1/lanes-3.json`.

Run the notebook interactively once for a small shard such as
`L23/part-001.json`. Confirm that the final cell finds `_SUCCESS.json`, then use
Save Version with Save & Run All. A saved shard output has this layout:

```text
keyframes/<Lxx>/part-NNN/
|-- keyframes/<video-id>/*.png
|-- frame_metadata/<video-id>.json
|-- extraction_status/<video-id>.done.json
|-- frames_metadata_v2.json
`-- _SUCCESS.json
```
