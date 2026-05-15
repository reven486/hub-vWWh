import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从环境变量或 .env 文件加载配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== 环境配置 ====================
    debug: bool = Field(
        default=False,
        description="调试模式开关"
    )

    # ==================== DashScope API 配置 ====================
    dashscope_api_key: Optional[str] = Field(
        default=None,
        description="阿里云 DashScope API 密钥（建议通过环境变量 DASHSCOPE_API_KEY 设置）"
    )

    dashscope_model: str = Field(
        default="qwen-flash",
        description="默认使用的 DashScope 模型"
    )

    # ==================== 本地模型配置 ====================
    embedding_model: str = Field(
        default="/Users/haironwei/Desktop/simpleCode/task/第6周：RAG工程化实现/models/BAAI/bge-small-zh-v1.5",
        description="本地 Embedding 模型路径"
    )

    rerank_model: str = Field(
        default="/Users/haironwei/Desktop/simpleCode/task/第6周：RAG工程化实现/models/BAAI/bge-reranker-base",
        description="本地 Rerank 模型路径"
    )

    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Embedding 批处理大小"
    )

    # ==================== 文本分块配置 ====================
    chunk_size: int = Field(
        default=500,
        ge=100,
        le=4096,
        description="文本分块大小（字符数）"
    )

    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="文本分块重叠大小（字符数）"
    )

    # ==================== 向量库配置 (Chroma) ====================
    vector_store_type: str = Field(
        default="chroma",
        description="向量库类型：chroma, faiss, inmemory"
    )

    vector_store_path: str = Field(
        default="./data/chroma_db",
        description="Chroma 向量库存储路径"
    )

    collection_name: str = Field(
        default="rag_documents",
        description="Chroma collection 名称"
    )

    # ==================== 检索配置 ====================
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="初始检索返回的文档数量"
    )

    rerank_top_n: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Rerank 后返回的文档数量"
    )

    # ==================== 日志配置 ====================
    log_level: str = Field(
        default="INFO",
        description="日志级别: DEBUG, INFO, WARNING, ERROR"
    )

    log_file: str = Field(
        default="logs/app.log",
        description="日志文件路径"
    )

    log_rotation: str = Field(
        default="100 MB",
        description="日志轮转大小"
    )

    log_retention: str = Field(
        default="7 days",
        description="日志保留时间"
    )


# 创建全局配置实例
settings = Settings()


def validate_settings() -> None:
    """验证配置的辅助函数"""
    errors = []

    # 检查必要的 API Key
    if not settings.dashscope_api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if api_key:
            settings.dashscope_api_key = api_key
        else:
            errors.append("dashscope_api_key 未设置（建议通过环境变量 DASHSCOPE_API_KEY 设置）")

    if errors:
        error_msg = "; ".join(errors)
        if settings.debug:
            print(f"⚠️  配置警告: {error_msg}")
        else:
            raise ValueError(error_msg)


def get_settings() -> Settings:
    """获取配置实例的工厂函数（方便后续扩展）"""
    return settings