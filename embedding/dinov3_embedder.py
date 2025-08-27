import json
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from transformers import AutoImageProcessor, AutoModel
from transformers.image_utils import load_image


class DinoV3ImageEmbedder:
    def __init__(self, model_name: str = "facebook/dinov3-vit7b16-pretrain-lvd1689m", device: str = "cuda", batch_size: int = 32):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name,
            device_map="auto" if self.device.type == "cuda" else None,
            torch_dtype=torch.bfloat16 if self.device.type == "cuda" else torch.float32
        )
        self.model.eval()
        self.batch_size = batch_size

    def _load_json(self, json_path: str, pos_start=None, pos_end=None):
        with open(json_path, 'r') as f:
            data = json.load(f)
        if pos_start is not None or pos_end is not None:
            pos_start = pos_start or 0
            pos_end = pos_end or len(data)
            data = data[pos_start:pos_end]
        return data

    def _load_images(self, frame_paths):
        images = []
        for path in frame_paths:
            try:
                img = Image.open(path).convert("RGB")
                images.append(img)
            except Exception as e:
                print(f"Failed to load image {path}: {e}")
                images.append(None)
        return images

    def embed_images_from_json(
        self,
        json_path: str,
        npy_output_dir: str,
        pos_start: int = None,
        pos_end: int = None,
    ):
        npy_dir = Path(npy_output_dir)
        npy_dir.mkdir(parents=True, exist_ok=True)

        data = self._load_json(json_path, pos_start, pos_end)
        frame_paths = [item["frame_path"] for item in data]
        all_embeddings = []

        for i in tqdm(range(0, len(frame_paths), self.batch_size), desc="Embedding images"):
            batch_paths = frame_paths[i:i + self.batch_size]
            images = self._load_images(batch_paths)
            valid_items = [(img, path) for img, path in zip(images, batch_paths) if img is not None]

            if not valid_items:
                continue

            imgs, valid_paths = zip(*valid_items)
            # Preprocess images without padding (DINOv3 processor does not support it)
            inputs = self.processor(images=list(imgs), return_tensors="pt").to(self.model.device)

            with torch.inference_mode():
                outputs = self.model(**inputs)
                pooled_output = outputs.pooler_output.to(dtype=torch.float32).cpu().numpy()

            all_embeddings.append(pooled_output)

        if all_embeddings:
            all_embeddings = np.concatenate(all_embeddings, axis=0)
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = npy_dir / (Path(json_path).stem + f"_embeddings_{timestamp}.npy")
            np.save(output_file, all_embeddings)
            print(f"Saved {len(all_embeddings)} embeddings to {output_file}")
        else:
            print("No valid images found to embed.")

        return all_embeddings
