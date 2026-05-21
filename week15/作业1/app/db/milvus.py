from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from app.core.config import get_settings


def connect_milvus():
    settings = get_settings()
    connections.connect(host=settings.milvus.host, port=settings.milvus.port)


def _ensure_text_collection() -> Collection:
    settings = get_settings()
    name = settings.milvus.text_collection
    dim = settings.milvus.text_dim
    if not utility.has_collection(name):
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
            FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, description="Text chunk embeddings")
        col = Collection(name, schema)
        col.create_index(
            "embedding",
            {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}},
        )
    else:
        col = Collection(name)
    col.load()
    return col


def _ensure_image_collection() -> Collection:
    settings = get_settings()
    name = settings.milvus.image_collection
    dim = settings.milvus.image_dim
    if not utility.has_collection(name):
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
            FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, description="Image chunk embeddings")
        col = Collection(name, schema)
        col.create_index(
            "embedding",
            {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}},
        )
    else:
        col = Collection(name)
    col.load()
    return col


def insert_text_vectors(chunk_ids: list[str], kb_ids: list[str], embeddings: list[list[float]]):
    col = _ensure_text_collection()
    col.insert([chunk_ids, kb_ids, embeddings])
    col.flush()


def insert_image_vectors(chunk_ids: list[str], kb_ids: list[str], embeddings: list[list[float]]):
    col = _ensure_image_collection()
    col.insert([chunk_ids, kb_ids, embeddings])
    col.flush()


def search_text_vectors(kb_id: str, query_embedding: list[float], top_k: int = 5) -> list[str]:
    col = _ensure_text_collection()
    results = col.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
        expr=f'kb_id == "{kb_id}"',
        output_fields=["chunk_id"],
    )
    return [hit.entity.get("chunk_id") for hit in results[0]]


def search_image_vectors(kb_id: str, query_embedding: list[float], top_k: int = 3) -> list[str]:
    col = _ensure_image_collection()
    results = col.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
        expr=f'kb_id == "{kb_id}"',
        output_fields=["chunk_id"],
    )
    return [hit.entity.get("chunk_id") for hit in results[0]]
