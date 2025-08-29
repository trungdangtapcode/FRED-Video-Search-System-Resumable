


Using git to avoid losing code
Partion ephe is temporary and will be deleted anytime.



npm run dev
# Init
ROOT DIR: `/root`
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt-get install nodejs -y
```
## Conda env

```
conda env create -f environments/faiss.yml
conda env create -f environments/openclip.yml
conda env create -f environments/static.yml
conda env create -f environments/elasticsearch.yml
```

```
docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" 0370c61f362b  --name elasticsearch_hcmc
docker start elasticsearch_hcmc
```

# CMD

## UI
```
cd hcmc/interface
npm run dev
```

## Static server
```
cd hcmc
conda activate static
uvicorn static_server.run:app --host 0.0.0.0 --port 8069 --reload
```

## Faiss server
```
cd hcmc
conda activate faiss
python3 embedding/retriever_server.py
```

## Backend server
```
cd hcmc
conda activate openclip
python3 run.py
```

## Text seach
```
cd hcmc/text_search
conda activate elasticsearch
python run.py
```

## Submit serever
```
cd hcmc/submit_server
conda activate utils
python run.py
```