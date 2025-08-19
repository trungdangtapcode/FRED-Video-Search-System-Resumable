import json
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import open_clip


class ImageEmbedder:
    def __init__(self, model_name: str, device: str = "cuda", batch_size: int = 32):
        self.device = torch.device(device)
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, device=self.device)
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.eval()
        self.batch_size = batch_size

    def _load_json(self, json_path: str, pos_start=None, pos_end=None):
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Apply optional slicing
        if pos_start is not None or pos_end is not None:
            pos_start = pos_start or 0
            pos_end = pos_end or len(data)
            data = data[pos_start:pos_end]

        return data

    def _load_and_preprocess_images(self, frame_paths):
        images = []
        for path in frame_paths:
            try:
                img = Image.open(path).convert("RGB")
                img = self.preprocess(img)
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
        # Ensure output directory exists
        npy_dir = Path(npy_output_dir)
        npy_dir.mkdir(parents=True, exist_ok=True)

        # Load data
        data = self._load_json(json_path, pos_start, pos_end)

        # Collect frame paths
        frame_paths = [item["frame_path"] for item in data]

        all_embeddings = []

        # Process in batches
        for i in tqdm(range(0, len(frame_paths), self.batch_size), desc="Embedding images"):
            batch_paths = frame_paths[i:i + self.batch_size]
            images = self._load_and_preprocess_images(batch_paths)

            # Remove failed images
            valid_images = [img for img in images if img is not None]
            if not valid_images:
                continue

            imgs_tensor = torch.stack(valid_images).to(self.device)

            with torch.no_grad(), torch.cuda.amp.autocast():
                embeddings = self.model.encode_image(imgs_tensor, normalize=True).cpu().numpy()

            all_embeddings.append(embeddings)

        if all_embeddings:
            all_embeddings = np.concatenate(all_embeddings, axis=0)
            output_file = npy_dir / (Path(json_path).stem + "_embeddings.npy")
            np.save(output_file, all_embeddings)
            print(f"Saved {len(all_embeddings)} embeddings to {output_file}")
        else:
            print("No valid images found to embed.")

        return all_embeddings

