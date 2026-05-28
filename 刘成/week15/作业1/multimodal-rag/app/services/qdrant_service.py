from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings


class QdrantService:
    def __init__(self, url: Optional[str] = None, collection_name: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.embedding_dim = settings.embedding_dim
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=self.url)
        return self._client

    def create_collection(self, recreate: bool = False):
        """Create the multimodal_rag collection with named vector"""
        if recreate:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "embedding": models.VectorParams(
                    size=self.embedding_dim,
                    distance=models.Distance.COSINE,
                )
            },
        )

    def collection_exists(self) -> bool:
        """Check if collection exists"""
        try:
            self.client.get_collection(self.collection_name)
            return True
        except (UnexpectedResponse, Exception):
            return False

    def upsert_points(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ):
        """Batch upsert points to collection"""
        points = [
            models.PointStruct(
                id=point_id,
                vector={"embedding": vector},
                payload=payload,
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        query_filter: Optional[models.Filter] = None,
    ) -> list[dict]:
        """ANN search - returns list of {id, score, payload}"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=("embedding", query_vector),
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def delete_by_document_id(self, document_id: str):
        """Delete all points associated with a document"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def get_collection_info(self) -> dict:
        """Get collection statistics"""
        info = self.client.get_collection(self.collection_name)
        return {
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "collection_name": self.collection_name,
        }

    def reset_collection(self):
        """Delete all points in the collection"""
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
            self.create_collection()


qdrant_service = QdrantService()
