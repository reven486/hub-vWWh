import dashscope
import numpy as np
from typing import List, Optional
from app.config import settings


class TextEmbedder:
    """BGE文本向量化"""

    def __init__(self, api_key: Optional[str] = None):
        dashscope.api_key = api_key or settings.BGE_API_KEY
        self.dimension = settings.BGE_DIM

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        调用dashscope API将文本向量化

        Args:
            texts: 文本列表

        Returns:
            np.ndarray: 文本向量数组
        """
        if not dashscope.api_key:
            raise ValueError("BGE_API_KEY is not set")

        input_list = [{"text": text} for text in texts]

        response = dashscope.MultiModalEmbedding.call(
            model="qwen3-vl-embedding",
            input=input_list
        )

        if response.status_code != 200:
            raise Exception(f"Embedding API error: {response.message}")

        embeddings = []
        for item in response.output["embeddings"]:
            embeddings.append(item["embedding"])

        return np.array(embeddings, dtype="float32")

    async def embed_query(self, query: str) -> np.ndarray:
        """嵌入单个查询"""
        vectors = await self.embed_texts([query])
        return vectors[0]


class ImageEmbedder:
    """CLIP图像向量化"""

    def __init__(self, api_key: Optional[str] = None):
        dashscope.api_key = api_key or settings.BGE_API_KEY
        self.dimension = settings.CLIP_DIM

    async def embed_images(self, image_paths: List[str]) -> np.ndarray:
        """
        调用dashscope API将图像向量化

        Args:
            image_paths: 图像路径列表

        Returns:
            np.ndarray: 图像向量数组
        """
        if not dashscope.api_key:
            raise ValueError("API key is not set")

        input_list = [{"image": path} for path in image_paths]

        response = dashscope.MultiModalEmbedding.call(
            model="qwen3-vl-embedding",
            input=input_list
        )

        if response.status_code != 200:
            raise Exception(f"Embedding API error: {response.message}")

        embeddings = []
        for item in response.output["embeddings"]:
            embeddings.append(item["embedding"])

        return np.array(embeddings, dtype="float32")


def get_text_embedder() -> TextEmbedder:
    return TextEmbedder()


def get_image_embedder() -> ImageEmbedder:
    return ImageEmbedder()