import faiss
import numpy as np
import torch
from pathlib import Path

class TextToImageRetriever:
    def __init__(
        self,
        text_embedder,
        image_embeddings_path=None,
        faiss_index_path=None,
        use_gpu=True
    ):
        self.text_embedder = text_embedder
        self.use_gpu = use_gpu

        if faiss_index_path is not None:
            self.index = self._load_faiss_index(faiss_index_path, use_gpu)
            self.image_embeddings = None  # optional
        elif image_embeddings_path is not None:
            self.image_embeddings = np.load(image_embeddings_path).astype(np.float32)
            self.index = self._build_faiss_index(self.image_embeddings, use_gpu)
        else:
            raise ValueError("You must provide either image_embeddings_path or faiss_index_path.")

    def _build_faiss_index(self, embeddings, use_gpu):
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # For normalized cosine similarity

        if use_gpu:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)

        index.add(embeddings)
        return index

    def _load_faiss_index(self, index_path, use_gpu):
        index = faiss.read_index(str(index_path))
        if use_gpu:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
        return index

    def save_index(self, path: str):
        """
        Save the current FAISS index to disk (CPU only).
        """
        cpu_index = faiss.index_gpu_to_cpu(self.index) if self.use_gpu else self.index
        faiss.write_index(cpu_index, str(path))

    def retrieve(self, query_texts, top_k=5):
        """
        query_texts: list of strings
        returns: List of (index, score) for each query
        """
        text_embeddings = self.text_embedder.embed_texts(query_texts, normalize=True).astype(np.float32)
        scores, indices = self.index.search(text_embeddings, top_k)

        results = []
        for idxs, sims in zip(indices, scores):
            results.append(list(zip(idxs.tolist(), sims.tolist())))
        return results
