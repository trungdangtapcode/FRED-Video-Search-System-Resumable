import json
import os
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from init_elasticsearch import init_elasticsearch

app = Flask(__name__)

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200", request_timeout=100)

def initialize_all_indexes():
    """Initialize multiple Elasticsearch indexes."""
    print("Initializing Elasticsearch indexes...")
    
    # Define indexes to create
    indexes_config = [
        {
            "json_path": "/data/root/data/frame_asr_v3.json",
            "index_name": "asr_index",
            "keyname": "asr"
        },
        {
            "json_path": "/data/root/meilisearch/ocr/OCR/idx_ocr_b1_b2.json",
            "index_name": "ocr_index",
            "keyname": "ocr"
        }
    ]
    
    for config in indexes_config:
        try:
            init_elasticsearch(
                config["json_path"],
                config["index_name"],
                config["keyname"]
            )
        except Exception as e:
            print(f"Error initializing {config['index_name']}: {str(e)}")
    
    print("All indexes initialized successfully!")

@app.route('/query', methods=['POST'])
def query_elasticsearch():
    """Query endpoint for Elasticsearch."""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        index_name = data.get('index_name')
        query_text = data.get('query')
        top_k = int(data.get('top_k', 20))
        
        if not index_name or not query_text:
            return jsonify({
                "error": "Both 'index_name' and 'query' are required"
            }), 400
        
        # Check if index exists
        if not es.indices.exists(index=index_name):
            return jsonify({
                "error": f"Index '{index_name}' does not exist"
            }), 404
        
        # Perform search
        search_query = {
            "query": {
                "match": {
                    "text": {
                        "query": query_text,
                        "fuzziness": "AUTO"
                    }
                }
            },
            "size": top_k,  # Return top 20 results
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }
        
        response = es.search(index=index_name, body=search_query)
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "id": hit['_id'],
                "score": hit['_score'],
                "text": hit['_source']['text'],
                "idx": hit['_source'].get('idx', hit['_id'])
            })
        
        return jsonify({
            "index_name": index_name,
            "query": query_text,
            "total_hits": response['hits']['total']['value'],
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check Elasticsearch connection
        if es.ping():
            return jsonify({"status": "healthy", "elasticsearch": "connected"})
        else:
            return jsonify({"status": "unhealthy", "elasticsearch": "disconnected"}), 503
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route('/indexes', methods=['GET'])
def list_indexes():
    """List all available indexes."""
    try:
        indexes = list(es.indices.get_alias("*").keys())
        return jsonify({"indexes": indexes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask application...")
    
    # Initialize all indexes on startup
    try:
        initialize_all_indexes()
    except Exception as e:
        print(f"Warning: Error during index initialization: {str(e)}")
    
    # Start Flask server
    print("Starting Flask server on 0.0.0.0:9201...")
    app.run(host='0.0.0.0', port=9201, debug=False)