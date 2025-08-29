from flask import Blueprint, request, jsonify
from app.retriever_service import (
    retrieve_metadata_from_text,
    retrieve_metadata_from_ocr,
    retrieve_metadata_from_asr,
    hybrid_search,
    multi_frame_search
)

main = Blueprint('main', __name__)

"""
Expected request body structure for /retrieve endpoint:
{
    "query": "string (optional)",    # Text query for search
    "ocr": "string (optional)",      # OCR text for search  
    "asr": "string (optional)",      # ASR text for search
    "top_k": "integer (optional)"    # Number of results to return (default: 5)
}

Note: At least one of 'query', 'ocr', or 'asr' must be provided and not empty.
"""

@main.route('/retrieve', methods=['POST'])
def retrieve():
    try:
        data = request.get_json()
        
        # Extract parameters from request body
        query = data.get("query", "").strip() if data.get("query") else ""
        ocr = data.get("ocr", "").strip() if data.get("ocr") else ""
        asr = data.get("asr", "").strip() if data.get("asr") else ""
        top_k = int(data.get("top_k", 5))
        
        # Validate that at least one of query, ocr, or asr is provided and not empty
        if not any([query, ocr, asr]):
            return jsonify({
                "error": "At least one of 'query', 'ocr', or 'asr' parameters must be provided and not empty"
            }), 400
        
        # For now, using the first available text field
        # You may need to update retrieve_metadata_from_text to handle multiple text sources
        if query and not ocr and not asr:
            search_text = query
            results = retrieve_metadata_from_text(search_text, top_k)
        elif ocr and not query and not asr:
            search_text = ocr
            results = retrieve_metadata_from_ocr(search_text, top_k)
        elif asr and not query and not ocr:
            search_text = asr
            results = retrieve_metadata_from_asr(search_text, top_k)
        else:
            results = hybrid_search(query, ocr, asr, top_k, normalize_scores=True)
        
        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": f"Invalid top_k value: {str(e)}"}), 400
    except Exception as e:
        print(f"Error in /retrieve: {e}")
        # SHOW THE FUCKING TRACEBACK PLEASE
        import traceback
        traceback.print_exc()
        
        return jsonify({"error": str(e)}), 500

"""
Expected request body structure for /retrieve_multi_frame endpoint:
{
    "frames": [
        {
            "query": "string (optional)",      # Text query for frame 1
            "ocr": "string (optional)",        # OCR text for frame 1
            "asr": "string (optional)",        # ASR text for frame 1
            "timestamp": "number (optional)"   # Expected timestamp for frame 1
        },
        {
            "query": "string (optional)",      # Text query for frame 2
            "ocr": "string (optional)",        # OCR text for frame 2
            "asr": "string (optional)",        # ASR text for frame 2
            "timestamp": "number (optional)"   # Expected timestamp for frame 2
        }
        // Up to 3 frames supported
    ],
    "top_k": "integer (optional)"    # Number of results to return (default: 5)
}

Note: At least one frame must have at least one of 'query', 'ocr', or 'asr' provided and not empty.
"""

@main.route('/retrieve_multi_frame', methods=['POST'])
def retrieve_multi_frame():
    try:
        data = request.get_json()
        
        # Extract parameters from request body
        frames = data.get("frames", [])
        top_k = int(data.get("top_k", 5))
        
        # Validate frames input
        if not frames or not isinstance(frames, list):
            return jsonify({
                "error": "The 'frames' parameter must be provided as a non-empty list"
            }), 400
        
        if len(frames) > 3:
            return jsonify({
                "error": "Maximum 3 frames are supported"
            }), 400
        
        # Validate that at least one frame has content
        valid_frames = []
        for i, frame in enumerate(frames):
            if not isinstance(frame, dict):
                return jsonify({
                    "error": f"Frame {i+1} must be an object"
                }), 400
            
            query = frame.get("query", "").strip() if frame.get("query") else ""
            ocr = frame.get("ocr", "").strip() if frame.get("ocr") else ""
            asr = frame.get("asr", "").strip() if frame.get("asr") else ""
            timestamp = frame.get("timestamp", 0)
            
            if any([query, ocr, asr]):
                valid_frames.append({
                    "query": query,
                    "ocr": ocr,
                    "asr": asr,
                    "timestamp": timestamp
                })
        
        if not valid_frames:
            return jsonify({
                "error": "At least one frame must have at least one of 'query', 'ocr', or 'asr' provided and not empty"
            }), 400
        
        # Perform multi-frame search
        results = multi_frame_search(valid_frames, top_k, normalize_scores=True)
        
        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": f"Invalid top_k value: {str(e)}"}), 400
    except Exception as e:
        print(f"Error in /retrieve_multi_frame: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({"error": str(e)}), 500
