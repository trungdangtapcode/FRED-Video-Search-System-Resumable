import torch
import numpy as np
from .image_embedder import ImageEmbedder

class TextEmbedder:
    def __init__(self, image_embedder: ImageEmbedder):
        self.model = image_embedder.model
        self.tokenizer = image_embedder.tokenizer
        self.device = image_embedder.device

    def embed_texts(self, texts, normalize=True):
        """
        texts: List of strings
        returns: numpy array of text embeddings
        """
        tokens = self.tokenizer(texts, context_length=self.model.context_length).to(self.device)

        with torch.no_grad(), torch.cuda.amp.autocast():
            text_embeddings = self.model.encode_text(tokens, normalize=normalize).cpu().numpy()

        return text_embeddings
