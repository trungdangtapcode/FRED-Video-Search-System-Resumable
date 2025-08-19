from flask import Blueprint, request, jsonify
from app.retriever_service import retrieve_metadata_from_text

main = Blueprint('main', __name__)

@main.route('/retrieve', methods=['POST'])
def retrieve():
    try:
        data = request.get_json()
        query = data.get("query")
        top_k = int(data.get("top_k", 5))

        if not query:
            return jsonify({"error": "Missing 'query' parameter"}), 400

        results = retrieve_metadata_from_text(query, top_k)
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
