

(25 vs -1)

Using git to avoid losing code
Partion ephe is temporary and will be deleted anytime.



npm run dev

## Before running on another machine

Update the following machine-specific absolute paths after cloning the repository:

1. In `interface/src/constants/index.ts`, set `ROOT_DIR` to the new machine's
   absolute `data/` directory.
2. In `submit.py`, update `FPS_PATH` and the default `json_file_path` in
   `process_json_file()` to point to the new machine's `data/fps_dict_v2.json`
   and `submit_server/submissions.json` files.

For example, if the repository is cloned to `/workspace/FRED-Video-Search-System-Resumable`,
use `/workspace/FRED-Video-Search-System-Resumable/data` as the data root. Do not
commit credentials or machine-specific secrets; provide those through environment
variables.

### Files deliberately excluded from Git

The root `.gitignore` excludes virtual environments, Node dependencies, build
output, runtime logs, temporary/backup files, generated archives, submissions,
datasets, embedding arrays, FAISS indexes, and model weights. These files are
machine-local or generated and must not be committed to GitHub.

Before migrating, back up required runtime state separately (for example, to
R2). At minimum, preserve `submit_server/submissions.json`,
`submit_server/statement.csv`, `data/frames_metadata_v2.json`,
`data/fps_dict_v2.json`, and `data/embeddings_qwen3_vl_8b.index`. Recreate the
Python virtual environments and `interface/node_modules` from their requirement
and lock files on the destination machine.

# Init
ROOT DIR: `/root`
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt-get install nodejs -y
```

## Create screen

### Clear existing screen
```bash
killall screen
screen
```

### Create screen

```bash
screen -S ui
screen -S static
screen -S faiss
screen -S backend
screen -S textsearch
screen -S submit
screen -S translate
```

## Conda env

```
conda env create -f environments/faiss.yml
conda env create -f environments/openclip.yml
conda env create -f environments/static.yml
conda env create -f environments/elasticsearch.yml
conda env create -f environments/utils.yml
```

```
apt install docker.io
docker pull elasticsearch:9.1.2
docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:9.1.2  --name elasticsearch_hcmc
docker start elasticsearch_hcmc
```
```
docker run -d \ --name elasticsearch_hcmc \ -p 9200:9200 \ -e "discovery.type=single-node" \ -e "xpack.security.enabled=false" \ elasticsearch:9.1.2
docker run -d --name elasticsearch_hcmc -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:9.1.2
```
```bash
docker run -d \
  --name elasticsearch_hcmc \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:9.1.2
```

# CMD

## UI (4 const), 103.155.161.181:13020
`interface/src/constants/index.ts`
```ts
export const API_ENDPOINTS = {
  SEARCH: 'http://103.155.161.183:5000/retrieve',
  STATIC_SERVER: 'http://103.155.161.181:13021',
  SUBMIT_SERVER: 'http://103.155.161.183:5001',
  TRANSLATE_BASE_URL: 'http://103.155.161.183:5002',
  SEARCH_BASE_URL: 'http://103.155.161.183:5000'
} as const;
export const ROOT_DIR = "/data/root"
```
```
screen -r ui
cd hcmc/interface
npm run dev -- --port 13020
```

## Static server (1 const), 103.155.161.181:13021
```
ROOT_DIR = "/data/root"
```
```
screen -r static
cd hcmc
conda activate static
uvicorn static_server.run:app --host 0.0.0.0 --port 8069 --reload
```

## Faiss server (2 const), 111.237.107.89:50239
`embedding/retriever_server.py`
```python
load_index("siglip2", "/data/root/data/embeddings_siglip_v2.index")

app.run(host="0.0.0.0", port=50239, debug=True)
```
```
screen -r faiss
cd hcmc
conda activate faiss
python3 embedding/retriever_server.py
```

## Backend server (1 const), 111.237.107.89:50313 
`run.py`
```python
app.run(host="0.0.0.0", port=5000, debug=False)
```
`embedding/retriever_service.py`
```python
SEARCH_URL = "http://localhost:50239"
```
`app/config.py`
```python
load_dotenv()

# Modify as needed
FRAMES_METADATA_PATH = os.getenv("FRAMES_METADATA_PATH", "/data/data/frames_metadata_v2.json")
# VIDEOS_METADATA_PATH = os.getenv("VIDEOS_METADATA_PATH", "/root/data/videos_metadata.json")
# MODEL_NAME = "hf-hub:timm/PE-Core-bigG-14-448"
MODEL_NAME = "hf-hub:timm/ViT-gopt-16-SigLIP2-384"
DEVICE = "cuda"

print("FRAMES_METADATA_PATH:", FRAMES_METADATA_PATH)	
```
```
screen -r backend
cd hcmc
conda activate openclip
python3 run.py
```

## Text seach (1 const), 111.237.107.89:50298  
```python
app.run(host='0.0.0.0', port=9201, debug=False)
```
```
screen -r textsearch
cd hcmc/text_search
conda activate elasticsearch
python run.py
```

## Submit server (2 const), 103.155.161.181:13022
`submit_server/run.py`
```
SUBMISSIONS_FILE = 'submissions.json'

PORT = 5001
```
```
screen -r submit
cd hcmc/submit_server
conda activate utils
python run.py
```

## Translate server, 103.155.161.181:13023
`translate_server/run.py`
```python
app.run(host='0.0.0.0', port=5002, debug=False)
```
```
screen -r translate
cd hcmc/translate_server
conda activate utils
python run.py
```

cd hcmc/submission
rm  submission.zip && zip -r submission.zip submission
cd ../..

---

config
