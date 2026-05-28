import numpy as np
from sentence_transformers import SentenceTransformer
from PIL import Image

from app.core.config import settings


class BgeEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(
            settings.bge_model_name,
            device=settings.embedding_device,
        )
        self.dim = settings.bge_dim

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a_np = np.array(a, dtype=np.float32)
        b_np = np.array(b, dtype=np.float32)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np) + 1e-10))


class ClipEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(
            settings.clip_model_name,
            device=settings.embedding_device,
        )
        self.dim = settings.clip_dim

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_image(self, images: list[str | Image.Image]) -> list[list[float]]:
        pil_images = []
        for img in images:
            if isinstance(img, str):
                pil_images.append(Image.open(img).convert("RGB"))
            else:
                pil_images.append(img.convert("RGB"))
        embeddings = self.model.encode(pil_images, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
