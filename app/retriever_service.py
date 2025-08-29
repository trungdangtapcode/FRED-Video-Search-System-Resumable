import json
from .config import FRAMES_METADATA_PATH, MODEL_NAME, DEVICE

# Lazy-load and initialize once (using importlib)
from embedding import image_embedder, text_embedder, retriever_client
from text_search import text_search_client

# ima# The code snippet you provided is commented out, so it is not being executed. However, based on
# the commented lines, it seems like the intention was to create instances of
# `image_embedder.ImageEmbedder`, `text_embedder.TextEmbedder`, and
# `retriever_client.RetrieverClient` classes.
image_embedder_instance = image_embedder.ImageEmbedder(model_name=MODEL_NAME, device=DEVICE)

text_embedder_instance = text_embedder.TextEmbedder(image_embedder_instance)

retriever_client_instance = retriever_client.RetrieverClient(text_embedder_instance)

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
            # print('huhu', result)
            # print("hehe:",results)
            results.extend([(item, (score - min_score) / (max_score - min_score), idx  if max_score > min_score else 0) for item, score, idx in result])
            # print("hehe:",results)
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

def multi_frame_search(frame_queries, top_k=5, normalize_scores=True):
    """
    Search for videos using multiple frame descriptions.
    
    Args:
        frame_queries: List of dicts with keys 'query', 'ocr', 'asr', 'timestamp'
        top_k: Number of final results to return
        normalize_scores: Whether to normalize scores
    
    Returns:
        List of metadata entries sorted by combined scores
    """
    print("Multi-frame search called with", len(frame_queries), "frame queries")
    
    # Get results for each frame query
    all_frame_results = []
    for i, frame_query in enumerate(frame_queries):
        query = frame_query.get("query", "").strip()
        ocr = frame_query.get("ocr", "").strip()
        asr = frame_query.get("asr", "").strip()
        timestamp = frame_query.get("timestamp", 0)
        
        # Skip empty queries
        if not any([query, ocr, asr]):
            continue
            
        print(f"Processing frame {i+1}: query='{query}', ocr='{ocr}', asr='{asr}', timestamp={timestamp}")
        
        # Use hybrid search to get results with scores for this frame
        frame_results = []
        if query:
            result = retrieve_metadata_from_text(query, top_k=top_k*10, return_scores=True)
            if normalize_scores and result:
                max_score = max(score for _, score, _ in result)
                min_score = min(score for _, score, _ in result)
                frame_results.extend([(item, (score - min_score) / (max_score - min_score) if max_score > min_score else 0, idx) for item, score, idx in result])
        
        if ocr:
            result = retrieve_metadata_from_ocr(ocr, top_k=top_k*30, return_scores=True)
            if normalize_scores and result:
                max_score = max(score for _, score, _ in result)
                min_score = min(score for _, score, _ in result)
                frame_results.extend([(item, (score - min_score) / (max_score - min_score) if max_score > min_score else 0, idx) for item, score, idx in result])
        
        if asr:
            result = retrieve_metadata_from_asr(asr, top_k=top_k*50, return_scores=True)
            if normalize_scores and result:
                max_score = max(score for _, score, _ in result)
                min_score = min(score for _, score, _ in result)
                frame_results.extend([(item, (score - min_score) / (max_score - min_score) if max_score > min_score else 0, idx) for item, score, idx in result])
        
        all_frame_results.append((frame_results, timestamp))
    
    # Group results by video and combine scores for frames from the same video
    video_scores = {}
    
    for frame_results, expected_timestamp in all_frame_results:
        for item, score, idx in frame_results:
            video_path = item.get('video_path', '')
            frame_timestamp = item.get('timestamp', 0)
            
            # Create a unique key for each video
            if video_path not in video_scores:
                video_scores[video_path] = {}
            
            # Add score for this frame, considering temporal proximity if timestamp is provided
            frame_key = f"{video_path}_{idx}"
            if frame_key not in video_scores[video_path]:
                video_scores[video_path][frame_key] = {
                    'item': item,
                    'total_score': 0,
                    'frame_count': 0,
                    'timestamps': []
                }
            
            # Weight score based on temporal proximity if timestamp is specified
            temporal_weight = 1.0
            if expected_timestamp > 0:
                time_diff = abs(frame_timestamp - expected_timestamp)
                # Reduce weight for frames that are far from expected timestamp (>30 seconds)
                temporal_weight = max(0.1, 1.0 - (time_diff / 60.0))
            
            video_scores[video_path][frame_key]['total_score'] += score * temporal_weight
            video_scores[video_path][frame_key]['frame_count'] += 1
            video_scores[video_path][frame_key]['timestamps'].append(frame_timestamp)
    
    # Calculate final scores for each video by summing scores of all matching frames
    final_results = []
    for video_path, frames in video_scores.items():
        # Sum scores across all frames from this video
        video_total_score = sum(frame_data['total_score'] for frame_data in frames.values())
        frame_count = len(frames)
        
        # Bonus for videos that have matches for multiple queries
        multi_frame_bonus = min(frame_count / len(frame_queries), 1.0) * 0.5
        final_score = video_total_score + multi_frame_bonus
        
        # Use the frame with highest individual score as representative
        best_frame = max(frames.values(), key=lambda x: x['total_score'])
        final_results.append((best_frame['item'], final_score))
    
    # Sort by combined score and return top results
    sorted_results = sorted(final_results, key=lambda x: x[1], reverse=True)[:top_k]
    metadatas = [item for item, score in sorted_results]
    
    print(f"Multi-frame search completed: {len(metadatas)} results")
    return metadatas
    
    
# retrieve_metadata_from_asr("hello world", top_k=5)