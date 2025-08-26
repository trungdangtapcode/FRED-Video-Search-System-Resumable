import requests

class TextSearchClient:
    def __init__(self, server_url="http://localhost:9202"):
        self.server_url = server_url

    def search(self, query_text, index_name):
        payload = {
            "index_name": index_name,
            "query": query_text
        }

        resp = requests.post(f"{self.server_url}/query", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            return result
        else:
            raise RuntimeError(f"TextSearchServer Error: {resp.text}")
