#!/usr/bin/env python3
"""
Flask server for Elasticsearch indexing and querying
Hosts at 0.0.0.0:9201
"""

import json
import os
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from tqdm import tqdm

app = Flask(__name__)

# Global Elasticsearch client
es = Elasticsearch("http://localhost:9200")

def create_index_settings():
    """Create index settings with custom analyzer for OCR and ASR text"""
    return {
        "settings": {
            "analysis": {
                "char_filter": {
                    "remove_spaces": {
                        "type": "pattern_replace",
                        "pattern": "\\s+",
                        "replacement": ""
                    },
                    "ocr_fix": {
                        "type": "mapping",
                        "mappings": [
                            "0 => o",
                            "1 => l",
                            "5 => s",
                            "! => i"  # Add more OCR-specific mappings as needed
                        ]
                    }
                },
                "analyzer": {
                    "ngram_analyzer": {
                        "type": "custom",
                        "char_filter": ["remove_spaces", "ocr_fix"],
                        "tokenizer": "ngram",
                        "filter": ["lowercase"],
                        "min_gram": 2,  # Smaller n-grams for more disruption tolerance
                        "max_gram": 5   # Larger n-grams for better context
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "text": {
                    "type": "text",
                    "analyzer": "ngram_analyzer",
                    "search_analyzer": "ngram_analyzer"
                },
                "idx": {
                    "type": "keyword"
                },
                "metadata": {
                    "type": "object",
                    "enabled": False
                }
            }
        }
    }

def init_index_from_json(json_path, index_name, keyname="text"):
    """Initialize an Elasticsearch index from a JSON file"""
    try:
        # Create index settings
        index_settings = create_index_settings()
        
        # Create the index (delete if exists)
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
        es.indices.create(index=index_name, body=index_settings)
        
        print(f"Index '{index_name}' created successfully!")
        
        # Load JSON data
        if not os.path.exists(json_path):
            print(f"Warning: JSON file not found: {json_path}")
            return False
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loading {len(data)} documents into index '{index_name}'")
        
        # Prepare documents for bulk indexing
        docs = []
        for i, item in enumerate(tqdm(data, desc=f"Preparing {index_name}")):
            # Handle different JSON structures
            if isinstance(item, dict):
                # Try to get text from the specified keyname or common fields
                text = ""
                idx = i
                
                if keyname in item:
                    text = str(item[keyname])
                elif "text" in item:
                    text = str(item["text"])
                elif "asr" in item:
                    text = str(item["asr"])
                elif "ocr" in item:
                    text = str(item["ocr"])
                else:
                    # If no text field found, use the whole item as text
                    text = str(item)
                
                # Try to get idx if available
                if "idx" in item:
                    idx = item["idx"]
                elif "id" in item:
                    idx = item["id"]
                
                docs.append({
                    "_index": index_name,
                    "_id": str(idx),
                    "_source": {
                        "text": text,
                        "idx": str(idx),
                        "metadata": item
                    }
                })
            else:
                # Handle simple text items
                docs.append({
                    "_index": index_name,
                    "_id": str(i),
                    "_source": {
                        "text": str(item),
                        "idx": str(i),
                        "metadata": {}
                    }
                })
        
        # Bulk index documents
        success, failed = bulk(es, docs)
        print(f"Indexed {success} documents into '{index_name}', {len(failed)} failed.")
        
        # Refresh index for immediate querying
        es.indices.refresh(index=index_name)
        return True
        
    except Exception as e:
        print(f"Error initializing index '{index_name}': {str(e)}")
        return False

def init_all_indexes():
    """Initialize all available indexes"""
    print("Initializing Elasticsearch indexes...")
    
    # Define indexes to create
    indexes_config = [
        {
            "json_path": "/root/data/frame_asr.json",
            "index_name": "asr_index",
            "keyname": "asr"
        },
        {
            "json_path": "/root/asr_text.json",
            "index_name": "asr_text_index",
            "keyname": "text"
        },
        {
            "json_path": "/root/yt_caption_full.json",
            "index_name": "youtube_captions_index",
            "keyname": "text"
        },
        {
            "json_path": "/root/data/frame_metadata.json",
            "index_name": "metadata_index",
            "keyname": "text"
        },
        {
            "json_path": "/root/data/frame_metadata_btc.json",
            "index_name": "metadata_btc_index",
            "keyname": "text"
        }
    ]
    
    successful_indexes = []
    failed_indexes = []
    
    for config in indexes_config:
        success = init_index_from_json(
            config["json_path"], 
            config["index_name"], 
            config["keyname"]
        )
        
        if success:
            successful_indexes.append(config["index_name"])
        else:
            failed_indexes.append(config["index_name"])
    
    print(f"\nIndexing complete!")
    print(f"Successfully created indexes: {successful_indexes}")
    if failed_indexes:
        print(f"Failed to create indexes: {failed_indexes}")
    
    return successful_indexes, failed_indexes

@app.route('/query', methods=['POST'])
def query_elasticsearch():
    """Query endpoint for Elasticsearch"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        index_name = data.get("index_name")
        query_text = data.get("query")
        
        if not index_name:
            return jsonify({"error": "index_name is required"}), 400
        
        if not query_text:
            return jsonify({"error": "query is required"}), 400
        
        # Check if index exists
        if not es.indices.exists(index=index_name):
            return jsonify({"error": f"Index '{index_name}' does not exist"}), 404
        
        # Perform search
        search_body = {
            "query": {
                "match": {
                    "text": {
                        "query": query_text,
                        "fuzziness": "AUTO",
                        "operator": "or"
                    }
                }
            },
            "size": 20,  # Return top 20 results
            "highlight": {
                "fields": {
                    "text": {}
                }
            }
        }
        
        response = es.search(index=index_name, body=search_body)
        
        # Format response
        results = []
        for hit in response['hits']['hits']:
            result = {
                "score": hit['_score'],
                "id": hit['_id'],
                "text": hit['_source']['text'],
                "idx": hit['_source'].get('idx', hit['_id'])
            }
            
            # Add highlights if available
            if 'highlight' in hit:
                result['highlights'] = hit['highlight']
            
            # Add metadata if available
            if 'metadata' in hit['_source'] and hit['_source']['metadata']:
                result['metadata'] = hit['_source']['metadata']
            
            results.append(result)
        
        return jsonify({
            "total_hits": response['hits']['total']['value'],
            "max_score": response['hits']['max_score'],
            "results": results,
            "took": response['took'],
            "index_name": index_name,
            "query": query_text
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/indexes', methods=['GET'])
def list_indexes():
    """List all available indexes"""
    try:
        # Get all indexes
        indexes = es.indices.get_alias("*")
        index_info = []
        
        for index_name in indexes.keys():
            # Skip system indexes
            if not index_name.startswith('.'):
                try:
                    stats = es.indices.stats(index=index_name)
                    doc_count = stats['indices'][index_name]['total']['docs']['count']
                    index_info.append({
                        "name": index_name,
                        "doc_count": doc_count
                    })
                except:
                    index_info.append({
                        "name": index_name,
                        "doc_count": "unknown"
                    })
        
        return jsonify({
            "indexes": index_info,
            "total_indexes": len(index_info)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Elasticsearch connection
        es_health = es.cluster.health()
        return jsonify({
            "status": "healthy",
            "elasticsearch": es_health['status'],
            "cluster_name": es_health['cluster_name']
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "Elasticsearch Flask Server",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "This help message",
            "GET /health": "Health check",
            "GET /indexes": "List all indexes",
            "POST /query": "Query Elasticsearch index"
        },
        "query_example": {
            "url": "/query",
            "method": "POST",
            "body": {
                "index_name": "asr_index",
                "query": "search text here"
            }
        }
    })

if __name__ == '__main__':
    print("Starting Elasticsearch Flask Server...")
    print("Initializing indexes...")
    
    # Initialize all indexes on startup
    successful, failed = init_all_indexes()
    
    print(f"\nServer starting on http://0.0.0.0:9201")
    print(f"Available endpoints:")
    print(f"  GET  /          - API documentation")
    print(f"  GET  /health    - Health check")
    print(f"  GET  /indexes   - List all indexes")
    print(f"  POST /query     - Query endpoint")
    print(f"\nExample query:")
    print(f"curl -X POST http://localhost:9201/query -H 'Content-Type: application/json' -d '{{\"index_name\": \"asr_index\", \"query\": \"your search text\"}}'")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=9201, debug=False)
