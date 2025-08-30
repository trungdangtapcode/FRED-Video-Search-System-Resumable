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
    
    # Add metadata_index to each result
    results = []
    for i in idx:
        frame_data = metadata[i].copy()
        frame_data['metadata_index'] = i
        results.append(frame_data)
    
    return results

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

    # Add metadata_index to each result
    results = []
    for x in indexs:
        frame_data = metadata[int(x['idx'])].copy()
        frame_data['metadata_index'] = int(x['idx'])
        results.append(frame_data)
    
    return results

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

    # Add metadata_index to each result
    results = []
    for x in indexs:
        frame_data = metadata[int(x['idx'])].copy()
        frame_data['metadata_index'] = int(x['idx'])
        results.append(frame_data)
    
    return results

def retrieve_metadata_from_image(image_data, top_k: int = 5, return_scores: bool = False):
    """
    Retrieve similar frames using an uploaded image.
    
    Args:
        image_data: Image data as bytes (from uploaded file)
        top_k: Number of results to return
        return_scores: Whether to return scores along with metadata
    
    Returns:
        List of metadata entries or tuples with scores
    """
    try:
        # Generate embedding for the uploaded image
        image_embedding = image_embedder_instance.embed_single_image(image_data)
        
        # Convert to the format expected by retriever_client
        import numpy as np
        query_embeddings = np.array([image_embedding], dtype=np.float32)
        
        # Use retriever client to search (simulating text search structure)
        import requests
        payload = {
            "model_name": 'siglip2',
            "query_embeds": query_embeddings.tolist(),
            "top_k": top_k
        }
        
        resp = requests.post("http://localhost:5679/search", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            indices = result["indices"][0]  # First query results
            scores = result["scores"][0]    # First query scores
            
            if return_scores:
                return [(metadata[i], scores[j], i) for j, i in enumerate(indices)]
            
            # Add metadata_index to each result
            results = []
            for i in indices:
                frame_data = metadata[i].copy()
                frame_data['metadata_index'] = i
                results.append(frame_data)
            
            return results
        else:
            raise RuntimeError(f"Retriever server error: {resp.text}")
            
    except Exception as e:
        print(f"Error in image search: {e}")
        raise e

def retrieve_similar_frames_by_index(frame_index: int, top_k: int = 10):
    """
    Retrieve similar frames using DINOv3 embeddings based on frame index.
    
    Args:
        frame_index: Index of the frame to find similarities for
        top_k: Number of similar frames to return
    
    Returns:
        List of metadata entries for similar frames
    """
    try:
        import requests
        
        payload = {
            "frame_index": frame_index,
            "top_k": top_k
        }
        
        resp = requests.post("http://localhost:5679/search_frame_similarity", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            similar_indices = result["indices"]
            
            # Get metadata for similar frames
            similar_frames = []
            for idx in similar_indices:
                if 0 <= idx < len(metadata):
                    frame_metadata = metadata[idx].copy()
                    # Add similarity info
                    frame_metadata['similarity_to_frame'] = frame_index
                    similar_frames.append(frame_metadata)
            
            return similar_frames
        else:
            raise RuntimeError(f"Frame similarity server error: {resp.text}")
            
    except Exception as e:
        print(f"Error in frame similarity search: {e}")
        raise e

def retrieve_similar_frames_by_metadata_index(metadata_index: int, top_k: int = 10):
    """
    Retrieve similar frames using DINOv3 embeddings based on metadata index.
    
    Args:
        metadata_index: Index of the frame in the metadata list to find similarities for
        top_k: Number of similar frames to return
    
    Returns:
        List of metadata entries for similar frames
    """
    try:
        import requests
        
        payload = {
            "metadata_index": metadata_index,
            "top_k": top_k
        }
        
        resp = requests.post("http://localhost:5679/search_frame_similarity", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            similar_indices = result["indices"]
            
            # Get metadata for similar frames and add metadata_index
            similar_frames = []
            for idx in similar_indices:
                if 0 <= idx < len(metadata):
                    frame_metadata = metadata[idx].copy()
                    # Add metadata index and similarity info
                    frame_metadata['metadata_index'] = idx
                    frame_metadata['similarity_to_metadata_index'] = metadata_index
                    similar_frames.append(frame_metadata)
            
            return similar_frames
        else:
            raise RuntimeError(f"Frame similarity server error: {resp.text}")
            
    except Exception as e:
        print(f"Error in frame similarity search: {e}")
        raise e

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
    
    # Add metadata_index to each result
    metadatas = []
    for item, score in sorted_results:
        # Find the metadata_index for this item
        for i, meta in enumerate(metadata):
            if (meta.get('video_path') == item.get('video_path') and 
                meta.get('frame_idx') == item.get('frame_idx') and
                meta.get('timestamp') == item.get('timestamp')):
                item_with_index = item.copy()
                item_with_index['metadata_index'] = i
                metadatas.append(item_with_index)
                break
        else:
            # Fallback: add without metadata_index if not found
            metadatas.append(item)
    
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
    
    # First, collect all individual frame results with their query index
    all_individual_results = []
    query_frame_results = {}  # track which videos appear in which queries
    
    for query_idx, (frame_results, expected_timestamp) in enumerate(all_frame_results):
        for item, score, idx in frame_results:
            video_path = item.get('video_path', '')
            frame_timestamp = item.get('timestamp', 0)
            
            # Weight score based on temporal proximity if timestamp is specified
            temporal_weight = 1.0
            if expected_timestamp > 0:
                time_diff = abs(frame_timestamp - expected_timestamp)
                # Reduce weight for frames that are far from expected timestamp (>30 seconds)
                temporal_weight = max(0.1, 1.0 - (time_diff / 60.0))
            
            weighted_score = score * temporal_weight
            
            # Track which videos appear in each query
            if video_path not in query_frame_results:
                query_frame_results[video_path] = set()
            query_frame_results[video_path].add(query_idx)
            
            all_individual_results.append({
                'item': item,
                'score': weighted_score,
                'idx': idx,
                'video_path': video_path,
                'query_idx': query_idx
            })
    
    # Calculate multi-query bonus for each video
    video_multi_query_bonus = {}
    for video_path, query_indices in query_frame_results.items():
        num_queries_matched = len(query_indices)
        total_queries = len(frame_queries)
        
        # Bonus grows exponentially with more matched queries
        if num_queries_matched >= 2:
            # Give significant bonus: 0.5 for 2 queries, 1.0 for 3 queries, etc.
            bonus_multiplier = (num_queries_matched - 1) * 0.5
            video_multi_query_bonus[video_path] = bonus_multiplier
            print(f"Video {video_path} matches {num_queries_matched}/{total_queries} queries, bonus: {bonus_multiplier}")
        else:
            video_multi_query_bonus[video_path] = 0.0
    
    # Apply bonus to individual frame scores
    final_results = []
    for result in all_individual_results:
        video_path = result['video_path']
        base_score = result['score']
        
        # Apply multi-query bonus
        bonus_multiplier = video_multi_query_bonus.get(video_path, 0.0)
        final_score = base_score * (1.0 + bonus_multiplier)
        
        final_results.append((result['item'], final_score))
    
    # Remove duplicates (same frame appearing in multiple queries) by keeping highest score
    unique_results = {}
    for item, score in final_results:
        frame_key = f"{item.get('video_path', '')}_{item.get('frame_idx', '')}"
        if frame_key not in unique_results or score > unique_results[frame_key][1]:
            unique_results[frame_key] = (item, score)
    
    # Sort by combined score and return top results
    sorted_results = sorted(unique_results.values(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Add metadata_index to each result
    metadatas = []
    for item, score in sorted_results:
        # Find the metadata_index for this item
        for i, meta in enumerate(metadata):
            if (meta.get('video_path') == item.get('video_path') and 
                meta.get('frame_idx') == item.get('frame_idx') and
                meta.get('timestamp') == item.get('timestamp')):
                item_with_index = item.copy()
                item_with_index['metadata_index'] = i
                metadatas.append(item_with_index)
                break
        else:
            # Fallback: add without metadata_index if not found
            metadatas.append(item)
    
    print(f"Multi-frame search completed: {len(metadatas)} results")
    return metadatas
    
    
# retrieve_metadata_from_asr("hello world", top_k=5)