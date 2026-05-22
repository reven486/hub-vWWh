from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Multimodal Document RAG"
    debug: bool = False

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_database: str = "multimodal_rag"
    sqlalchemy_database_url: str = ""

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "rag_data"
    milvus_alias: str = "default"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "rag-data"
    kafka_group_id: str = "rag-worker"

    # Model paths / device
    bge_model_name: str = "BAAI/bge-small-zh-v1.5"
    clip_model_name: str = "jinaai/jina-clip-v1"
    embedding_device: str = "cpu"
    qwen_vl_model_name: str = "Qwen/Qwen-VL-Chat"

    # File storage
    upload_dir: str = "uploads"
    processed_dir: str = "processed"

    # Vector dimensions
    bge_dim: int = 512
    clip_dim: int = 1024

    # Retrieval
    top_k: int = 5
    text_weight: float = 0.5
    image_weight: float = 0.5

    @property
    def database_url(self) -> str:
        if self.sqlalchemy_database_url:
            return self.sqlalchemy_database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    model_config = {"env_prefix": "RAG_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
