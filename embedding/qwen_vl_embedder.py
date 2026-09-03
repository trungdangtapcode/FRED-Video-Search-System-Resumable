"""Query encoder matching the Qwen3-VL embeddings stored in the FAISS index."""

from __future__ import annotations

from io import BytesIO
from typing import Sequence

import numpy as np
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer


class QwenVLEmbedder:
    """Load Qwen3-VL once and encode text or image queries as 4096-D vectors."""

    def __init__(self, model_name: str, revision: str, device: str = "cuda") -> None:
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("DEVICE requests CUDA, but PyTorch cannot see a CUDA GPU")

        dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
        self.model = SentenceTransformer(
            model_name,
            revision=revision,
            device=device,
            model_kwargs={
                "torch_dtype": dtype,
                "attn_implementation": "sdpa",
            },
        )

    def embed_texts(
        self, texts: str | Sequence[str], normalize: bool = True
    ) -> np.ndarray:
        inputs = [texts] if isinstance(texts, str) else list(texts)
        if not inputs:
            raise ValueError("At least one text query is required")
        embeddings = self.model.encode(
            inputs,
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        result = np.asarray(embeddings, dtype=np.float32)
        if normalize:
            result /= np.linalg.norm(result, axis=1, keepdims=True)
        return result

    def embed_single_image(self, image_data: bytes) -> np.ndarray:
        with Image.open(BytesIO(image_data)) as source:
            image = source.convert("RGB")
        embeddings = self.model.encode(
            [image],
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        result = np.asarray(embeddings[0], dtype=np.float32)
        result /= np.linalg.norm(result)
        return result
