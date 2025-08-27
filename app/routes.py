from flask import Blueprint, request, jsonify
from app.retriever_service import (
    retrieve_metadata_from_text,
    retrieve_metadata_from_ocr,
    retrieve_metadata_from_asr,
    hybrid_search
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
