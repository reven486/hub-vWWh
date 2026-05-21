import dashscope
from dashscope import TextEmbedding, MultiModalEmbedding
from typing import Optional
import base64

from app.config import settings


class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.dashscope_api_key
        dashscope.api_key = self.api_key

    def embed_text(self, texts: list[str], model: str = "text-embedding-v3") -> list[list[float]]:
        """Get text embeddings using DashScope Text Embedding API"""
        response = TextEmbedding.call(
            model=model,
            input=texts,
        )

        if response.status_code != 200:
            raise ValueError(f"Embedding API error: {response.code} - {response.message}")

        embeddings = [item["embedding"] for item in response.output["embeddings"]]
        return embeddings

    def embed_image(self, images: list[str], model: str = "multimodal-embedding-v1") -> list[list[float]]:
        """Get image embeddings using DashScope MultiModal Embedding API"""
        response = MultiModalEmbedding.call(
            model=model,
            input=[{"image": img} for img in images],
        )

        if response.status_code != 200:
            raise ValueError(f"Embedding API error: {response.code} - {response.message}")

        embeddings = [item["embedding"] for item in response.output["embeddings"]]
        return embeddings

    def embed_texts_with_image(
        self,
        texts: Optional[list[str]] = None,
        images: Optional[list[str]] = None,
        model: str = "multimodal-embedding-v1",
    ) -> tuple[list[list[float]], list[str]]:
        """
        Get embeddings for mixed text and image inputs.
        Returns (embeddings, input_types) where input_types indicates which embedding corresponds to text/image.
        """
        inputs = []
        input_types = []

        if texts:
            for text in texts:
                inputs.append({"text": text})
                input_types.append("text")

        if images:
            for image in images:
                inputs.append({"image": image})
                input_types.append("image")

        if not inputs:
            raise ValueError("No text or image inputs provided")

        response = MultiModalEmbedding.call(model=model, input=inputs)

        if response.status_code != 200:
            raise ValueError(f"Embedding API error: {response.code} - {response.message}")

        embeddings = [item["embedding"] for item in response.output["embeddings"]]
        return embeddings, input_types

    def check_api_health(self) -> bool:
        """Check if DashScope API is accessible"""
        try:
            self.embed_text(["health check"])
            return True
        except Exception:
            return False


embedding_service = EmbeddingService()
