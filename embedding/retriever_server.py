import faiss
import numpy as np
from flask import Flask, request, jsonify
from pathlib import Path

app = Flask(__name__)
index_map = {}  # name -> faiss index
dim_map = {}    # name -> dimension of index

def load_index(name, path, use_gpu=False):
    index = faiss.read_index(str(path))
    if use_gpu:
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)
    index_map[name] = index
    dim_map[name] = index.d

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    name = data["model_name"]
    query_embeds = np.array(data["query_embeds"], dtype=np.float32)  # shape: [N, D]
    top_k = int(data.get("top_k", 5))
  

    if name not in index_map:
        return jsonify({"error": f"Index for '{name}' not found"}), 404

    index = index_map[name]
    scores, indices = index.search(query_embeds, top_k)
    return jsonify({
        "indices": indices.tolist(),
        "scores": scores.tolist()
    })

@app.route("/load_index", methods=["POST"])
def load_index_api():
    data = request.get_json()
    print(data)
    name = data["model_name"]
    path = Path(data["index_path"])

    try:
        load_index(name, path)
        return jsonify({"status": f"Loaded index '{name}' from {path}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/build_index", methods=["POST"])
def build_index():
    data = request.get_json()
    name = data["model_name"]
    embeddings = np.array(data["embeddings"], dtype=np.float32)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    res = faiss.StandardGpuResources()
    index = faiss.index_cpu_to_gpu(res, 0, index)
    index.add(embeddings)

    index_map[name] = index
    dim_map[name] = dim

    return jsonify({"status": f"Built in-memory index for '{name}'"}), 200

@app.route("/save_index", methods=["POST"])
def save_index():
    data = request.get_json()
    name = data["model_name"]
    out_path = Path(data["output_path"])

    if name not in index_map:
        return jsonify({"error": f"Index '{name}' not found"}), 404

    cpu_index = faiss.index_gpu_to_cpu(index_map[name])
    faiss.write_index(cpu_index, str(out_path))

    return jsonify({"status": f"Index '{name}' saved to {out_path}"}), 200

@app.route("/hello", methods=["GET"])
def hello_word():
	return "Hello, this is the Retriever Server!"

if __name__ == "__main__":
    pass
    # Optional preload:
    load_index("siglip2", "/root/data/embedding/siglip2_batch1.index")
    app.run(host="0.0.0.0", port=5679, debug=True)
