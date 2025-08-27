import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

def init_elasticsearch(json_path, index_name="asr_index", keyname="asr"):
    print('[!] Initializing Elasticsearch index...', json_path, index_name, keyname, sep=' | ')
    # Connect to Elasticsearch (running in Docker)
    es = Elasticsearch("http://localhost:9200", request_timeout=100)

    # Define index settings with custom analyzer
    index_settings = {
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
                }
            }
        }
    }

    # Create the index (deletes if exists, for testing)
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body=index_settings)

    print("Index created successfully!")


    # load path
    with open(json_path, 'r') as f:
        data = json.load(f)

    print("len: ",len(data))


    docs = []
    from tqdm import tqdm
    for frame in tqdm(data):
        # print(frame_asr)
        idx = frame["idx"]
        text = frame[keyname]
        docs.append({
            "_index": index_name,
            "_id": str(idx),
            "_source": {
                "text": text
            },
        })

    success, failed = bulk(es, docs)
    print(f"Indexed {success} documents, {len(failed)} failed.")

    # Refresh index for immediate querying
    es.indices.refresh(index=index_name)

 
if __name__ == "__main__":
    asr_json_path = "/root/data/frame_asr.json"
    init_elasticsearch(asr_json_path)
 
    