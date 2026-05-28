from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def get_bge_embedder():
    from app.services.embedder import BgeEmbedder
    return BgeEmbedder()


@lru_cache(maxsize=1)
def get_clip_embedder():
    from app.services.embedder import ClipEmbedder
    return ClipEmbedder()


@lru_cache(maxsize=1)
def get_retriever():
    from app.services.retriever import MilvusRetriever
    return MilvusRetriever()


def get_db():
    from app.models.database import get_session
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@lru_cache(maxsize=1)
def get_qwen_vl():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_name = settings.qwen_vl_model_name
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, device_map=settings.embedding_device,
    )
    return {"model": model, "tokenizer": tokenizer}
