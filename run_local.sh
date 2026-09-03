#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="$project_root/.runtime"
index_path="$project_root/data/embeddings_qwen3_vl_8b.index"

if [[ ! -f "$index_path" ]]; then
  echo "Missing $index_path"
  echo "Convert the incoming NPY with embedding/convert_npy_to_faiss.py first."
  exit 1
fi

for port in 50239 50313 8069 13022 5174; do
  if ss -H -ltn "sport = :$port" | grep -q .; then
    echo "Port $port is already in use; refusing to start a conflicting service."
    exit 1
  fi
done

mkdir -p "$runtime_dir"
pids=()

cleanup() {
  if ((${#pids[@]})); then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$project_root"
PYTHONUNBUFFERED=1 .venv-services/bin/python embedding/retriever_server.py \
  >"$runtime_dir/retriever.log" 2>&1 &
pids+=("$!")

PYTHONUNBUFFERED=1 .venv-services/bin/python -m static_server.run \
  >"$runtime_dir/static.log" 2>&1 &
pids+=("$!")

PYTHONUNBUFFERED=1 .venv-services/bin/python submit_server/run.py \
  >"$runtime_dir/submit.log" 2>&1 &
pids+=("$!")

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  PYTHONUNBUFFERED=1 .venv-openclip/bin/python run.py \
  >"$runtime_dir/backend.log" 2>&1 &
pids+=("$!")

(
  cd interface
  npm run dev -- --host 127.0.0.1 --port 5174
) >"$runtime_dir/frontend.log" 2>&1 &
pids+=("$!")

echo "Local embedding search is starting:"
echo "  UI:        http://localhost:5174"
echo "  API:       http://localhost:50313"
echo "  Retriever: http://localhost:50239"
echo "  Static:    http://localhost:8069"
echo "  Submit:    http://localhost:13022"
echo "Logs: $runtime_dir"
echo "Press Ctrl+C to stop all five services."

if ! wait -n "${pids[@]}"; then
  echo "A FRED service exited unexpectedly; stopping the remaining services."
else
  echo "A FRED service stopped; stopping the remaining services."
fi
exit 1
