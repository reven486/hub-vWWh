import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # DashScope API
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")

    # Qdrant
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "multimodal_rag")
    embedding_dim: int = 1024  # DashScope text-embedding-v3

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Paths
    data_dir: Path = Path(__file__).parent.parent / "data"
    documents_dir: Path = data_dir / "documents"
    qdrant_storage: Path = data_dir / "qdrant_storage"
    metadata_db: Path = data_dir / "metadata.db"

    # RAG settings
    top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
