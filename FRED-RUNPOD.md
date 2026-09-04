---
title: FRED Video Search — RunPod runtime
date: 2026-09-04
tags:
  - fred
  - runpod
  - faiss
  - cloudflare-r2
  - operations
---

# FRED Video Search — RunPod runtime

## Trạng thái chốt

- Repo chính: `/workspace/FRED-Video-Search-System-Resumable`
- Chế độ: embedding search bằng Qwen + FAISS; OCR, ASR và Elasticsearch tắt.
- FAISS index: `data/embeddings_qwen3_vl_8b.index` — 3.6 GB.
- Metadata: `data/frames_metadata_v2.json` — 68 MB.
- Index đã load: **235,588 vectors**, dimension **4096**.
- Video và keyframe không giữ local; client đọc trực tiếp từ Cloudflare R2.
- Server đang mở: UI `0.0.0.0:5174`; các backend chỉ mở trên `127.0.0.1`.

## Kiến trúc

```text
Search:             Browser -> RunPod UI proxy -> Qwen API -> FAISS -> metadata
Video/keyframe:     Browser --------------------------------> public R2
Extract submission: Browser -> submit API -> ffmpeg --------> public R2
```

RunPod chỉ giữ index, metadata, model/cache và code. Luồng xem video/keyframe thông
thường không truyền media qua RunPod. Riêng `/submit-api/extract_frame` dùng
`ffmpeg` trên RunPod đọc video R2 rồi trả JPEG.

## Cloudflare R2

- Bucket: `fred-media`
- Object prefix: `fred`
- Public runtime URL:
  `https://pub-c5e3fb17dd204ee495353209f6c82eef.r2.dev/fred/data`
- Ví dụ key:
  - `fred/data/extracted_keyframes/L21_V001/00000.png`
  - `fred/data/unzipped/video/L21_V001.mp4`
- Public endpoint đã kiểm tra hỗ trợ byte range: HTTP `206` cho cả PNG và MP4.
- S3 API `https://de5f3544d715a4b1d0fc23a56d44204e.r2.cloudflarestorage.com/fred-media`
  là endpoint private cho upload/API, không dùng làm URL media phía client.
- Runtime read không cần R2 credentials. Upload vẫn cần credentials riêng và
  tuyệt đối không commit/paste chúng vào log.

`.env` local, đã được Git ignore:

```dotenv
DATA_DIR=/workspace/FRED-Video-Search-System-Resumable/data
FRAMES_METADATA_PATH=/workspace/FRED-Video-Search-System-Resumable/data/frames_metadata_v2.json
DEVICE=cuda
RETRIEVER_URL=http://127.0.0.1:50239
HF_HOME=/workspace/FRED-Video-Search-System-Resumable/.cache/huggingface
VITE_MEDIA_BASE_URL=https://pub-c5e3fb17dd204ee495353209f6c82eef.r2.dev/fred/data
```

Frontend tự chuẩn hóa đường dẫn metadata cũ, ví dụ
`/home/.../data/extracted_keyframes/...` thành `extracted_keyframes/...`; không
còn phụ thuộc `ROOT_DIR` hard-code.

## Services và ports

| Service | Port | Vai trò |
|---|---:|---|
| Vite UI | `5174` | UI public/port preview và proxy API |
| Search API | `50313` | Qwen query encoder, embedding-only |
| FAISS retriever | `50239` | Tìm vector trong index local |
| Submit API | `13022` | Submission và trích frame từ R2 |

Static server `8069` không còn được `run_local.sh` khởi động vì media đi thẳng
tới R2.

## Vận hành

### Chạy foreground

```bash
cd /workspace/FRED-Video-Search-System-Resumable
./run_local.sh
```

Dừng bằng `Ctrl+C`; restart bằng `Ctrl+C` rồi chạy lại `./run_local.sh`.

### Chạy nền bằng tmux

```bash
tmux new-session -d -s fred \
  'cd /workspace/FRED-Video-Search-System-Resumable && exec ./run_local.sh'
```

```bash
tmux attach -t fred
tmux kill-session -t fred
```

Restart tmux:

```bash
tmux kill-session -t fred 2>/dev/null || true
tmux new-session -d -s fred \
  'cd /workspace/FRED-Video-Search-System-Resumable && exec ./run_local.sh'
```

Không chạy hai instance cùng lúc vì sẽ xung đột port.

## Status và health check

```bash
curl http://127.0.0.1:50313/health
curl http://127.0.0.1:50239/health
curl http://127.0.0.1:13022/health
curl -I http://127.0.0.1:5174
```

```bash
ss -ltnp | grep -E ':(5174|50313|50239|13022)'
```

FAISS khỏe sẽ trả gần giống:

```json
{"status":"ok","vectors":235588,"dimension":4096}
```

`tmux has-session -t fred` chỉ kiểm tra được instance chạy bằng tmux; trạng thái
port/health check đáng tin hơn.

## Logs

Thư mục: `.runtime/`

```bash
tail -f .runtime/*.log
tail -f .runtime/frontend.log
tail -f .runtime/backend.log
tail -f .runtime/retriever.log
tail -f .runtime/submit.log
```

## Môi trường đã cài

- System: Node `20.20.2`, npm `10.8.2`, ffmpeg `4.4.2`, zip/unzip, tmux.
- `.venv-services` (Python 3.11): Flask/FastAPI/FAISS và `python-dotenv`.
- `.venv-openclip` (Python 3.11): PyTorch `2.8.0+cu126`, torchvision
  `0.23.0+cu126`, Qwen dependencies; RTX 3090/CUDA đã nhận.
- `.venv-keyframes` (Python 3.12): keyframe pipeline; Python 3.12 cần cho NumPy
  `2.5.2` của pipeline này.
- `.venv-r2`: boto3, requests, Kaggle uploader.
- `.venv-translate`: translation dependencies.
- `interface/node_modules`: đã cài; production build pass; npm audit 0 lỗi.
- `.venv-elasticsearch`: đã bỏ khỏi workspace, tạm chuyển tới
  `/tmp/fred-venv-elasticsearch-unused`; code Elasticsearch legacy vẫn còn trong
  repo nhưng không thuộc runtime hiện tại.

## Tài nguyên

- Volume `/workspace`: 40 GB; lúc chốt dùng 26 GB, còn khoảng 15 GB.
- Qwen model cache: khoảng 16 GB tại `.cache/huggingface`.
- Qwen runtime dùng khoảng 15.6 GB VRAM trên RTX 3090.
- `.venv-openclip`: khoảng 6.3 GB; các venv khác nhỏ hơn nhiều.
- Có khoảng 600 MB môi trường cài dở/trùng ở repo `/root/FRED-Video-Search-System-Resumable`;
  chưa xóa vì đó không phải workspace chính.

## Đã kiểm thử

- Frontend TypeScript/Vite production build: pass.
- Python environments: `pip check` pass.
- Keyframe/import/finalize tests: 13 pass.
- FAISS/embedding safe-target tests: 7 pass.
- Search thật qua UI proxy: HTTP 200, trả kết quả metadata.
- Keyframe của kết quả search đọc từ R2: HTTP 206, `image/png`.
- Video R2: HTTP 206, `video/mp4`.
- Trích frame qua submit API từ video R2: HTTP 200, `image/jpeg`.

## Lưu ý

- Các Flask server hiện là development server; cần WSGI/reverse proxy nếu public
  production lâu dài.
- Lần chạy đầu model được tải từ Hugging Face không có token nên có cảnh báo rate
  limit; model hiện đã cache.
- `run_local.sh` từ chối chạy nếu thiếu FAISS index hoặc các port đã bị chiếm.
- Không sửa/xóa thay đổi upload hiện có của người dùng trong `kaggle/README.md` và
  `kaggle/r2_upload_keyframe_shard.ipynb`.
