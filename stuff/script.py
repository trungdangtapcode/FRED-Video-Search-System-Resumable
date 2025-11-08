# import json
# frame_metadata_path = "/root/data/frames_metadata.json"
# with open(frame_metadata_path, "r") as f:
#     frame_metadata = json.load(f)
    
# import importlib
# from hcmc.embedding import dinov3_embedder
# importlib.reload(dinov3_embedder)
# import datetime

# image_embedder_instance = dinov3_embedder.DinoV3ImageEmbedder()

# image_embedder_instance.batch_size = 128
# npy_array = image_embedder_instance.embed_images_from_json(
# 	json_path = "/root/data/frames_metadata.json",
# 	npy_output_dir = "/root/data/embedding/dinov3",
# 	pos_end=None
# )

import importlib
from hcmc.embedding import image_embedder
importlib.reload(image_embedder)
import datetime

image_embedder_instance = image_embedder.ImageEmbedder(model_name="hf-hub:timm/ViT-gopt-16-SigLIP2-384")

image_embedder_instance.batch_size = 128

npy_array = image_embedder_instance.embed_images_from_json(
	json_path = "/root/data/frame_metadata_btc.json",
	npy_output_dir = "/root/data/embedding",
)