from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    MINERU_API_KEY: str = ""
    BGE_API_KEY: str = ""
    QWEN_API_KEY: str = ""

    # API URLs
    MINERU_API_URL: str = "https://mineru.net/api/v4/extract/task"
    BGE_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Vector dimensions
    BGE_DIM: int = 2560
    CLIP_DIM: int = 2560

    # FAISS index path
    VECTOR_INDEX_PATH: str = "data/vectors"

    # Document paths
    DOCUMENT_PATH: str = "data/documents"
    IMAGE_PATH: str = "data/images"

    # Chunk settings
    CHUNK_MAX_CHARS: int = 500
    CHUNK_OVERLAP: int = 50

    # Database
    DATABASE_URL: str = "sqlite:///data/rag.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()