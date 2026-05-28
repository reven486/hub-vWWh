import numpy as np
from pymilvus import (
    connections, Collection, CollectionSchema,
    FieldSchema, DataType, utility,
)

from app.core.config import settings


class MilvusRetriever:
    def __init__(self):
        self._connect()

    def _connect(self):
        connections.connect(
            alias=settings.milvus_alias,
            host=settings.milvus_host,
            port=settings.milvus_port,
        )
        self._ensure_collection()

    def _ensure_collection(self):
        if utility.has_collection(settings.milvus_collection):
            self.collection = Collection(settings.milvus_collection)
            self.collection.load()
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_id", dtype=DataType.INT64),
            FieldSchema(name="image_id", dtype=DataType.INT64),
            FieldSchema(name="page_number", dtype=DataType.INT64),
            FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=4096),
            FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="bge_vector", dtype=DataType.FLOAT_VECTOR, dim=settings.bge_dim),
            FieldSchema(name="clip_vector", dtype=DataType.FLOAT_VECTOR, dim=settings.clip_dim),
        ]
        schema = CollectionSchema(fields, description="Multimodal RAG data")
        self.collection = Collection(settings.milvus_collection, schema)
        self._create_indexes()

    def _create_indexes(self):
        bge_index = {
            "index_type": "IVF_FLAT",
            "metric_type": "IP",
            "params": {"nlist": 128},
        }
        self.collection.create_index("bge_vector", bge_index)

        clip_index = {
            "index_type": "IVF_FLAT",
            "metric_type": "IP",
            "params": {"nlist": 128},
        }
        self.collection.create_index("clip_vector", clip_index)
        self.collection.load()

    def insert_text_chunk(
        self, document_id: int, chunk_id: int, page_number: int,
        text_content: str, bge_vector: list[float], clip_vector: list[float],
    ):
        entity = [
            [document_id], [chunk_id], [0], [page_number],
            ["text"], [text_content], [""],
            [bge_vector], [clip_vector],
        ]
        self.collection.insert(entity)

    def insert_image(
        self, document_id: int, image_id: int, page_number: int,
        image_path: str, clip_vector: list[float],
    ):
        dim = len(clip_vector)
        entity = [
            [document_id], [0], [image_id], [page_number],
            ["image"], [""], [image_path],
            [[0.0] * settings.bge_dim], [clip_vector],
        ]
        self.collection.insert(entity)

    def search(
        self, bge_vector: list[float], clip_vector: list[float],
        top_k: int = None, text_weight: float = None, image_weight: float = None,
    ) -> list[dict]:
        top_k = top_k or settings.top_k
        text_weight = text_weight or settings.text_weight
        image_weight = image_weight or settings.image_weight

        self.collection.load()

        text_results = self.collection.search(
            data=[bge_vector],
            anns_field="bge_vector",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["document_id", "chunk_id", "page_number", "content_type", "text_content", "image_path"],
        )

        clip_results = self.collection.search(
            data=[clip_vector],
            anns_field="clip_vector",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["document_id", "chunk_id", "image_id", "page_number", "content_type", "text_content", "image_path"],
        )

        return self._fuse_results(text_results, clip_results, text_weight, image_weight, top_k)

    def _fuse_results(
        self, text_results, clip_results,
        text_weight: float, image_weight: float, top_k: int,
    ) -> list[dict]:
        score_map = {}

        for hits in text_results:
            for hit in hits:
                entity_id = hit.id
                fields = hit.entity
                score = text_weight * hit.score
                if entity_id not in score_map or score > score_map[entity_id]["score"]:
                    score_map[entity_id] = {
                        "id": entity_id,
                        "document_id": fields.get("document_id"),
                        "chunk_id": fields.get("chunk_id"),
                        "page_number": fields.get("page_number"),
                        "content_type": fields.get("content_type"),
                        "text_content": fields.get("text_content"),
                        "image_path": fields.get("image_path"),
                        "score": score,
                    }

        for hits in clip_results:
            for hit in hits:
                entity_id = hit.id
                fields = hit.entity
                score = image_weight * hit.score
                if entity_id not in score_map or score > score_map[entity_id]["score"]:
                    score_map[entity_id] = {
                        "id": entity_id,
                        "document_id": fields.get("document_id"),
                        "chunk_id": fields.get("chunk_id"),
                        "image_id": fields.get("image_id"),
                        "page_number": fields.get("page_number"),
                        "content_type": fields.get("content_type"),
                        "text_content": fields.get("text_content"),
                        "image_path": fields.get("image_path"),
                        "score": score,
                    }
                else:
                    existing = score_map[entity_id]
                    existing["score"] += image_weight * hit.score

        results = sorted(score_map.values(), key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document_vectors(self, document_id: int):
        self.collection.delete(f"document_id == {document_id}")
