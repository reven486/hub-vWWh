import os
import yaml
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class LLMConfig(BaseModel):
    model: str = "qwen-plus"
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    max_tokens: int = 2048
    temperature: float = 0.7


class BGEConfig(BaseModel):
    model_name: str = "BAAI/bge-large-zh-v1.5"
    device: str = "cpu"


class CLIPConfig(BaseModel):
    model_name: str = "openai/clip-vit-base-patch32"
    device: str = "cpu"


class ModelsConfig(BaseModel):
    bge: BGEConfig = BGEConfig()
    clip: CLIPConfig = CLIPConfig()


class MineruConfig(BaseModel):
    base_url: str = "http://localhost:8888"
    timeout: int = 300
    parse_endpoint: str = "/api/v1/extract"


class SQLiteConfig(BaseModel):
    db_path: str = "app/doc/metadata.db"


class MilvusConfig(BaseModel):
    host: str = "localhost"
    port: int = 19530
    text_collection: str = "text_chunks"
    image_collection: str = "image_chunks"
    text_dim: int = 1024
    image_dim: int = 512


class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    parse_topic: str = "document_parse"
    consumer_group: str = "parse_workers"
    auto_offset_reset: str = "earliest"


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    llm: LLMConfig = LLMConfig()
    models: ModelsConfig = ModelsConfig()
    mineru: MineruConfig = MineruConfig()
    sqlite: SQLiteConfig = SQLiteConfig()
    milvus: MilvusConfig = MilvusConfig()
    kafka: KafkaConfig = KafkaConfig()


def _resolve_env(value: str) -> str:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    return value


def _resolve_dict(d: dict) -> dict:
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _resolve_dict(v)
        elif isinstance(v, str):
            result[k] = _resolve_env(v)
        else:
            result[k] = v
    return result


@lru_cache
def get_settings() -> Settings:
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        raw = _resolve_dict(raw)
        return Settings(**raw)
    return Settings()
