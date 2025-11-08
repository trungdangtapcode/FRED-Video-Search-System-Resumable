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
    # Example usage
    # convert_numpy_to_faiss_index("/root/data/embedding/dinov3/frames_metadata_embeddings_20250827_120247.npy",
    #         "/root/data/embedding/dinov3_batch1.index")
    # concat_numpy([
    #     "/root/data/embedding/frame_metadata_embeddings2.npy",
    #     "/root/data/embedding/frame_metadata_btc_embeddings20250827_141708.npy"
    # ], "/root/data/embedding/siglip2_batch1.npy")
    # convert_numpy_to_faiss_index("/root/data/embedding/siglip2_batch1.npy",
    #         "/root/data/embedding/siglip2_batch1.index", type='dot')
    # convert_numpy_to_faiss_index("/root/data/embedding/siglip2_batch1_pseudo.npy",
    #                 "/root/data/embedding/siglip2_batch1_pseudo.index", type='dot')
    # normalized_embeddings = normalize_embeddings(np.load("/root/data/embedding/dinov3/dinov3_batch1.npy"))
    # np.save("/root/data/embedding/dinov3/dinov3_batch1_normalized.npy", normalized_embeddings)
    # convert_numpy_to_faiss_index("/root/data/embedding/dinov3/dinov3_batch1_normalized.npy",
    #                 "/root/data/embedding/dinov3_batch1_normalized.index", type='dot')
    convert_numpy_to_faiss_index("/data/root/data/embedding/embeddings_dinov3_v2.npy",
                    "/data/root/data/embeddings_dinov3_v2.index", type='dot')
    # convert_numpy_to_faiss_index("/data/root/data/embedding/embeddings_siglip_v2.npy",
    #                 "/data/root/data/embeddings_siglip_v2.index", type='dot')