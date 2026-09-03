import numpy as np
import faiss
import os

def convert_numpy_to_faiss_index(npy_dir, index_dir, type='dot'):
    """
    Converts a .npy file to a FAISS index and saves it.

    Parameters:
        npy_dir (str): Path to the .npy file containing feature vectors.
        index_dir (str): Path where the FAISS index file will be saved.
        type (str): Distance type to use - 'dot' (default) or 'l2'.
    """
    if not os.path.exists(npy_dir):
        raise FileNotFoundError(f"Input .npy file not found: {npy_dir}")

    # Load vectors
    vectors = np.load(npy_dir).astype('float32')  # FAISS requires float32
    dim = vectors.shape[1]

    # Select index type
    if type == 'dot':
        index = faiss.IndexFlatIP(dim)
    elif type == 'l2':
        index = faiss.IndexFlatL2(dim)
    else:
        raise ValueError(f"Unsupported type '{type}'. Use 'dot' or 'l2'.")

    # Add vectors to index
    index.add(vectors)

    # Save index
    faiss.write_index(index, index_dir)
    print(f"FAISS index saved to: {index_dir}")

def concat_numpy(npy_files, output_file):
    """
    Concatenates multiple .npy files into a single .npy file.

    Parameters:
        npy_files (list of str): List of paths to .npy files to concatenate.
        output_file (str): Path where the concatenated .npy file will be saved.
    """
    arrays = []
    for file in npy_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"Input .npy file not found: {file}")
        arrays.append(np.load(file))
    
    concatenated_array = np.concatenate(arrays, axis=0)
    np.save(output_file, concatenated_array)
    print(f"Concatenated .npy file saved to: {output_file}")

def normalize_embeddings(embeddings):
    """
    Normalizes embeddings to unit length.

    Parameters:
        embeddings (np.ndarray): Array of shape (N, D) where N is the number of embeddings and D is their dimension.

    Returns:
        np.ndarray: Normalized embeddings.
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

if __name__ == "__main__":
    raise SystemExit(
        "Use embedding/convert_npy_to_faiss.py for validated Qwen3-VL conversion."
    )
