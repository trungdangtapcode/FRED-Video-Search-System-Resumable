import requests
import numpy as np

class RetrieverClient:
    def __init__(self, text_embedder, server_url="http://localhost:5679"):
        self.text_embedder = text_embedder
        self.server_url = server_url

    def retrieve(self, texts, model_name, top_k=5):
        embeddings = self.text_embedder.embed_texts(texts, normalize=True).astype(np.float32)

        payload = {
            "model_name": model_name,
            "query_embeds": embeddings.tolist(),
            "top_k": top_k
        }

        # print('query sent to:', self.server_url)
        # print('payload:', payload)
        resp = requests.post(f"{self.server_url}/search", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            return result["indices"], result["scores"]
        else:
            raise RuntimeError(f"RetrieverServer Error: {resp.text}")
