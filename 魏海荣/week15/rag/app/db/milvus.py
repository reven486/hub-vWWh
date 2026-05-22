from typing import List, Optional, Dict, Any
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.core.config import config


class MilvusClient:
    _instance: Optional["MilvusClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        milvus_config = config.milvus
        self._host = milvus_config.get("host", "localhost")
        self._port = milvus_config.get("port", 19530)
        self._text_collection_name = milvus_config.get("collection_text", "text_chunks")
        self._image_collection_name = milvus_config.get("collection_image", "image_chunks")
        connections.connect(host=self._host, port=self._port)
        self._ensure_collections()

    def _ensure_collections(self):
        if not utility.has_collection(self._text_collection_name):
            self._create_collection(self._text_collection_name, 1024)
        if not utility.has_collection(self._image_collection_name):
            self._create_collection(self._image_collection_name, 512)

    def _create_collection(self, name: str, dim: int):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=128, is_primary=True),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="page", dtype=DataType.INT32),
        ]
        schema = CollectionSchema(fields=fields, description=f"{name} collection")
        collection = Collection(name=name, schema=schema)
        collection.create_index(field_name="embedding", index_type="IVF_FLAT", params={"nlist": 128})

    def _get_collection(self, name: str) -> Collection:
        return Collection(name)

    def insert_text(self, doc_id: str, chunk_id: str, embedding: List[float], page: int):
        collection = self._get_collection(self._text_collection_name)
        data = [[chunk_id], [doc_id], [embedding], [page]]
        collection.insert(data)
        collection.flush()

    def insert_image(self, doc_id: str, chunk_id: str, embedding: List[float], page: int):
        collection = self._get_collection(self._image_collection_name)
        data = [[chunk_id], [doc_id], [embedding], [page]]
        collection.insert(data)
        collection.flush()

    def search_text(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        collection = self._get_collection(self._text_collection_name)
        collection.load()
        search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "document_id", "page"]
        )
        return [
            {"id": hit.entity.get("id"), "document_id": hit.entity.get("document_id"), "page": hit.entity.get("page")}
            for hit in results[0]
        ]

    def search_image(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        collection = self._get_collection(self._image_collection_name)
        collection.load()
        search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "document_id", "page"]
        )
        return [
            {"id": hit.entity.get("id"), "document_id": hit.entity.get("document_id"), "page": hit.entity.get("page")}
            for hit in results[0]
        ]


milvus_client = MilvusClient()
