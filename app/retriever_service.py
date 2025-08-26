import json
from .config import FRAMES_METADATA_PATH, MODEL_NAME, DEVICE

# Lazy-load and initialize once (using importlib)
from embedding import image_embedder, text_embedder, retriever_client
from text_search import text_search_client

# image_embedder_instance = image_embedder.ImageEmbedder(model_name=MODEL_NAME, device=DEVICE)

# text_embedder_instance = text_embedder.TextEmbedder(image_embedder_instance)

# retriever_client_instance = retriever_client.RetrieverClient(text_embedder_instance)

text_search_instance = text_search_client.TextSearchClient()

# Load metadata
with open(FRAMES_METADATA_PATH, 'r') as f:
    metadata = json.load(f)

def retrieve_metadata_from_text(text: str, top_k: int = 5):
    indexs = retriever_client_instance.retrieve(
        texts=text,
        model_name='siglip2',
        top_k=top_k
    )
    idx = indexs[0][0]
    return [metadata[i] for i in idx]

def retrieve_metadata_from_asr(text: str, top_k: int = 5, need_pop = True):
    indexs = text_search_instance.search(
        query_text = text, 
        index_name='asr_index', 
        top_k=top_k
    )
    
    if need_pop:
        for x in indexs:
            x.pop('id')
            x.pop('text')
    
    print(indexs)

    return [metadata[int(x['idx'])] for x in indexs]
    
    
# retrieve_metadata_from_asr("hello world", top_k=5)