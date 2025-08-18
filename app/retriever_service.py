import json
from .config import FRAMES_METADATA_PATH, MODEL_NAME, DEVICE

# Lazy-load and initialize once (using importlib)
from embedding import image_embedder, text_embedder, retriever_client

image_embedder_instance = image_embedder.ImageEmbedder(model_name=MODEL_NAME, device=DEVICE)

text_embedder_instance = text_embedder.TextEmbedder(image_embedder_instance)

retriever_client_instance = retriever_client.RetrieverClient(text_embedder_instance)


# Load metadata
with open(FRAMES_METADATA_PATH, 'r') as f:
    metadata = json.load(f)

def retrieve_metadata_from_text(text: str, top_k: int = 5):
    indexs = retriever_client_instance.retrieve(
        texts=text,
        model_name='clipcore',
        top_k=top_k
    )
    idx = indexs[0][0]
    return [metadata[i] for i in idx]
