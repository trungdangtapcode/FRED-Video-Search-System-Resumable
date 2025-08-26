import requests

class TextSearchClient:
    def __init__(self, server_url="http://localhost:9201"):
        self.server_url = server_url

    def search(self, query_text, index_name, top_k = 5):
        payload = {
            "index_name": index_name,
            "query": query_text,
            "top_k": top_k
        }
        print(f"{self.server_url}/query")
  
        resp = requests.post(f"{self.server_url}/query", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            return result["results"]
        else:
            raise RuntimeError(f"TextSearchServer Error: {resp.text}")
