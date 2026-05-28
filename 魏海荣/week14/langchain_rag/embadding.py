"""
Embeddings 模块

提供统一的 Embedding 模型接口，用于将文本转换为向量。

支持的 Embedding 模型：
- OpenAI Embeddings (text-embedding-3-small, text-embedding-3-large)
- 可扩展支持其他 embedding 模型

参考：
- https://reference.langchain.com/python/langchain_core/embeddings/
- https://reference.langchain.com/python/langchain_openai/embeddings/
"""

from typing import Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from config import settings, get_logger

logger = get_logger(__name__)


def get_embeddings(
    model: Optional[str] = None,
    batch_size: Optional[int] = None,
    **kwargs,
) -> Embeddings:
    """
    获取 Embedding 模型实例
    
    Args:
        model: 模型名称，默认使用配置中的 embedding_model
        batch_size: 批处理大小，默认使用配置值
        **kwargs: 其他传递给模型的参数
        
    Returns:
        Embeddings 实例
    """
    # 使用配置中的默认值
    model = model or settings.embedding_model
    batch_size = batch_size or settings.embedding_batch_size
    
    logger.info(f"🔢 创建 Embedding 模型: {model}")
    logger.debug(f"   batch_size: {batch_size}")
    
    try:
        # 创建 OpenAI Embeddings 实例
        embeddings = HuggingFaceEmbeddings(
            model=settings.embedding_model,
            # chunk_size 参数控制批处理大小
            model_kwargs={"device": "cpu"}
        )
        
        logger.debug(f"✅ Embedding 模型创建成功")
        return embeddings
        
    except Exception as e:
        logger.error(f"❌ 创建 Embedding 模型失败: {e}")
        raise
