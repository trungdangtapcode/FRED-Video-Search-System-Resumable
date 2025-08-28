import json
from .config import FRAMES_METADATA_PATH, MODEL_NAME, DEVICE

# Lazy-load and initialize once (using importlib)
from embedding import image_embedder, text_embedder, retriever_client
from text_search import text_search_client

# ima# The code snippet you provided is commented out, so it is not being executed. However, based on
# the commented lines, it seems like the intention was to create instances of
# `image_embedder.ImageEmbedder`, `text_embedder.TextEmbedder`, and
# `retriever_client.RetrieverClient` classes.
# ge_embedder_instance = image_embedder.ImageEmbedder(model_name=MODEL_NAME, device=DEVICE)

# text_embedder_instance = text_embedder.TextEmbedder(image_embedder_instance)

# retriever_client_instance = retriever_client.RetrieverClient(text_embedder_instance)

text_search_instance = text_search_client.TextSearchClient()

# Load metadata
with open(FRAMES_METADATA_PATH, 'r') as f:
    metadata = json.load(f)

def retrieve_metadata_from_text(text: str, top_k: int = 5, return_scores: bool = False):
    indexs = retriever_client_instance.retrieve(
        texts=text,
        model_name='siglip2',
        top_k=top_k
    )
    idx = indexs[0][0]
    # print("Retrieved indices:", indexs)
    
    if return_scores:
        scores = indexs[1][0]
        return [(metadata[i], scores[j], i) for j, i in enumerate(idx)]
    
    return [metadata[i] for i in idx]

def retrieve_metadata_from_asr(text: str, top_k: int = 5, return_scores: bool = False, need_pop = True):
    indexs = text_search_instance.search(
        query_text = text, 
        index_name='asr_index', 
        top_k=top_k
    )
    
    if need_pop:
        for x in indexs:
            x.pop('id')
            x.pop('text')
    
    if return_scores:
        return [(metadata[int(x['idx'])], x['score'], x['idx']) for x in indexs]

    return [metadata[int(x['idx'])] for x in indexs]

def retrieve_metadata_from_ocr(text: str, top_k: int = 5, return_scores: bool = False, need_pop = True):
    indexs = text_search_instance.search(
        query_text = text, 
        index_name='ocr_index', 
        top_k=top_k
    )
    print("OCR search ok!")
    
    if need_pop:
        for x in indexs:
            x.pop('id')
            x.pop('text')
    
    if return_scores:
        return [(metadata[int(x['idx'])], x['score'], x['idx']) for x in indexs]

    return [metadata[int(x['idx'])] for x in indexs]

def hybrid_search(query, ocr, asr, top_k=5, normalize_scores=True):
    print("Hybrid search called with \n-query:", query, "\n-ocr:", ocr, "\n=asr:", asr)
    results = []
    if query:
        result = retrieve_metadata_from_text(query, top_k=top_k, return_scores=True)
        if normalize_scores:
            max_score = max(score for _, score, _  in result) if result else 1
            min_score = min(score for _, score, _ in result) if result else 0
            results.extend([(item, (score - min_score) / (max_score - min_score), idx  if max_score > min_score else 0) for item, score, idx in result])
    # print('len results after query:', len(results))
    if ocr:
        result = retrieve_metadata_from_ocr(ocr, top_k=top_k*30, return_scores=True)
        if normalize_scores:
            max_score = max(score for _, score, _  in result) if result else 1
            min_score = min(score for _, score, _ in result) if result else 0
            print('huhu', result)
            print("hehe:",results)
            results.extend([(item, (score - min_score) / (max_score - min_score), idx  if max_score > min_score else 0) for item, score, idx in result])
            print("hehe:",results)
    # print('len results after ocr:', len(results))
    if asr:
        result = retrieve_metadata_from_asr(asr, top_k=top_k*50, return_scores=True)
        if normalize_scores:
            max_score = max(score for _, score, _  in result) if result else 1
            min_score = min(score for _, score, _ in result) if result else 0
            results.extend([(item, (score - min_score) / (max_score - min_score), idx  if max_score > min_score else 0) for item, score, idx in result])
    # print('len results after asr:', len(results))
    combined_results = {}
    # print("Results before combining:", results)
    for item, score, idx in results: # sum score, key is idx
        if idx in combined_results:
            combined_results[idx][1] += score
        else:
            combined_results[idx] = [item, score]
            
    sorted_results = sorted(combined_results.values(), key=lambda x: x[1], reverse=True)[:top_k]
    
    metadatas = [item for item, score in sorted_results]
    return metadatas
    
    
# retrieve_metadata_from_asr("hello world", top_k=5)