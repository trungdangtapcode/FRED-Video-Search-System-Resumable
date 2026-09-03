import faiss
import numpy as np
import os
from flask import Flask, request, jsonify
from pathlib import Path

app = Flask(__name__)
index_map = {}  # name -> faiss index
dim_map = {}    # name -> dimension of index

# Global variables for DINOv3 embeddings
# No need for dinov3_embeddings global variable since we'll use the FAISS index directly

def load_index(name, path, use_gpu=False):
    index = faiss.read_index(str(path))
    if use_gpu:
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)
    index_map[name] = index
    dim_map[name] = index.d

def load_dinov3_index(path=None):
    """Load DINOv3 FAISS index directly"""
    if path is None:
        path = Path(__file__).resolve().parents[1] / "data" / "embeddings_dinov3_v2.index"
    try:
        load_index("dinov3", path, use_gpu=False)
        print(f"Loaded DINOv3 index from {path}")
        return True
    except Exception as e:
        print(f"Failed to load DINOv3 index: {e}")
        return False

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    name = data["model_name"]
    query_embeds = np.array(data["query_embeds"], dtype=np.float32)  # shape: [N, D]
    top_k = int(data.get("top_k", 5))
  

    if name not in index_map:
        return jsonify({"error": f"Index for '{name}' not found"}), 404

    index = index_map[name]
    if query_embeds.ndim != 2 or query_embeds.shape[1] != index.d:
        return jsonify({
            "error": f"Expected query shape [N, {index.d}], got {list(query_embeds.shape)}"
        }), 400
    if top_k < 1:
        return jsonify({"error": "top_k must be positive"}), 400
    scores, indices = index.search(query_embeds, top_k)
    print("indices: ", indices)
    print("num of vector in db: ", index.ntotal)
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

@app.route("/search_frame_similarity", methods=["POST"])
def search_frame_similarity():
    """
    Search for similar frames using DINOv3 embeddings.
    Input: metadata_index (index in the metadata list)
    Output: top_k similar frame indices
    """
    data = request.get_json()
    metadata_index = int(data["metadata_index"])  # Index in the metadata list
    top_k = int(data.get("top_k", 10))
    
    if "qwen3_vl" not in index_map:
        return jsonify({"error": "Qwen3-VL index not loaded"}), 500
    
    try:
        embedding_index = index_map["qwen3_vl"]
        
        # Check if metadata_index is valid
        if metadata_index >= embedding_index.ntotal or metadata_index < 0:
            return jsonify({"error": f"Metadata index {metadata_index} out of range [0, {embedding_index.ntotal-1}]"}), 400
        
        # Get the embedding for the specified frame from the index
        # We need to reconstruct the embedding from the index
        query_embedding = embedding_index.reconstruct(metadata_index)
        query_embedding = query_embedding.reshape(1, -1)  # Shape: [1, D]
        
        # Search for similar frames
        scores, indices = embedding_index.search(query_embedding, top_k + 1)  # +1 to include self
        
        # Remove the query frame itself from results
        result_indices = []
        result_scores = []
        for i, idx in enumerate(indices[0]):
            if idx != metadata_index:  # Skip self
                result_indices.append(int(idx))
                result_scores.append(float(scores[0][i]))
            if len(result_indices) >= top_k:
                break
        
        return jsonify({
            "indices": result_indices,
            "scores": result_scores,
            "query_metadata_index": metadata_index
        })
        
    except Exception as e:
        print(f"Error in frame similarity search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/hello", methods=["GET"])
def hello_word():
		return "Hello, this is the Retriever Server!"


@app.route("/health", methods=["GET"])
def health():
    index = index_map.get("qwen3_vl")
    return jsonify({
        "status": "ok" if index is not None else "not_ready",
        "vectors": 0 if index is None else index.ntotal,
        "dimension": None if index is None else index.d,
    }), 200 if index is not None else 503

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    index_path = Path(
        os.getenv(
            "EMBEDDING_INDEX_PATH",
            project_root / "data" / "embeddings_qwen3_vl_8b.index",
        )
    )
    load_index("qwen3_vl", index_path)
    print(f"Loaded {index_map['qwen3_vl'].ntotal} Qwen3-VL vectors from {index_path}")
    app.run(
        host=os.getenv("RETRIEVER_HOST", "127.0.0.1"),
        port=int(os.getenv("RETRIEVER_PORT", "50239")),
        debug=False,
    )
