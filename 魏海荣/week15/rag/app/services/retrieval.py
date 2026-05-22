from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import config
from app.db.milvus import milvus_client


class RetrievalService:
    def __init__(self):
        self._bge_model = None
        self._clip_model = None

    @property
    def bge_model(self):
        if self._bge_model is None:
            model_name = config.models.get("bge", {}).get("model_name", "BAAI/bge-large-zh")
            self._bge_model = SentenceTransformer(model_name)
        return self._bge_model

    @property
    def clip_model(self):
        if self._clip_model is None:
            model_name = config.models.get("clip", {}).get("model_name", "openai/clip-vit-base-patch32")
            self._clip_model = SentenceTransformer(model_name)
        return self._clip_model

    def encode_text(self, text: str) -> List[float]:
        embedding = self.bge_model.encode(text)
        return embedding.tolist()

    def encode_image(self, image_path: str) -> List[float]:
        embedding = self.clip_model.encode(image_path)
        return embedding.tolist()

    def search_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.encode_text(query)
        return milvus_client.search_text(query_embedding, top_k)

    def search_image(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.clip_model.encode(query).tolist()
        return milvus_client.search_image(query_embedding, top_k)

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "text_results": self.search_text(query, top_k),
            "image_results": self.search_image(query, top_k)
        }


retrieval_service = RetrievalService()
