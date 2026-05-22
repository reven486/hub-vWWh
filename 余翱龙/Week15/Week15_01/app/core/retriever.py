import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from app.core.vector_store import get_vector_store, VectorEntry
from app.core.embedder import get_text_embedder, get_image_embedder
from app.config import settings


@dataclass
class RetrievalResult:
    chunk_id: str
    chunk_type: str  # text, image
    content: str
    doc_id: str
    doc_name: str
    page: Optional[int]
    score: float
    image_path: Optional[str] = None


class MultiModalRetriever:
    """多模态检索器 - 支持跨模态RRF融合排序"""

    def __init__(self):
        self.text_embedder = get_text_embedder()
        self.image_embedder = get_image_embedder()
        self.vector_store = get_vector_store()

    async def retrieve(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 4
    ) -> List[RetrievalResult]:
        """
        执行多模态检索

        Args:
            query: 查询文本
            doc_ids: 限定检索的文档ID列表，None表示检索所有
            top_k: 返回结果数量

        Returns:
            List[RetrievalResult]: 检索结果
        """
        # 1. 向量化查询
        query_vector = await self.text_embedder.embed_query(query)
        query_image_vector = await self.text_embedder.embed_query(query)  # 简化：使用相同向量

        # 2. 同步执行文本和图像检索
        text_results = self._search_text(query_vector, top_k * 2)
        image_results = self._search_image(query_image_vector, top_k * 2)

        # 3. RRF融合排序
        fused_results = self._rrf_fusion(text_results, image_results, k=60)

        # 4. 过滤和格式化
        results = []
        for fused in fused_results[:top_k]:
            entry, score = fused
            if doc_ids and entry.doc_id not in doc_ids:
                continue

            results.append(RetrievalResult(
                chunk_id=entry.chunk_id,
                chunk_type=entry.chunk_type,
                content=entry.content,
                doc_id=entry.doc_id,
                doc_name=entry.content.split("\n")[0] if entry.content else "",
                page=entry.page,
                score=score,
                image_path=entry.content if entry.chunk_type == "image" else None
            ))

        return results

    def _search_text(
        self,
        query_vector: np.ndarray,
        k: int
    ) -> List[Tuple[VectorEntry, float]]:
        """搜索文本向量"""
        search_results = self.vector_store.search_text(query_vector, k)

        results = []
        for vid, dist in search_results:
            entry = self.vector_store.get_text_entry(vid)
            if entry:
                # 将距离转换为相似度分数
                score = 1.0 / (1.0 + dist)
                results.append((entry, score))
        return results

    def _search_image(
        self,
        query_vector: np.ndarray,
        k: int
    ) -> List[Tuple[VectorEntry, float]]:
        """搜索图像向量"""
        search_results = self.vector_store.search_image(query_vector, k)

        results = []
        for vid, dist in search_results:
            entry = self.vector_store.get_image_entry(vid)
            if entry:
                score = 1.0 / (1.0 + dist)
                results.append((entry, score))
        return results

    def _rrf_fusion(
        self,
        text_results: List[Tuple[VectorEntry, float]],
        image_results: List[Tuple[VectorEntry, float]],
        k: int = 60
    ) -> List[Tuple[VectorEntry, float]]:
        """
        Reciprocal Rank Fusion (RRF) 融合算法

        Args:
            text_results: 文本检索结果 [(entry, score), ...]
            image_results: 图像检索结果 [(entry, score), ...]
            k: RRF参数

        Returns:
            List[Tuple[entry, fused_score]]: 融合后的排序结果
        """
        # 为每个结果分配rank
        scores = {}

        # 处理文本结果
        for rank, (entry, _) in enumerate(sorted(text_results, key=lambda x: -x[1])):
            chunk_key = f"{entry.chunk_type}_{entry.chunk_id}"
            if chunk_key not in scores:
                scores[chunk_key] = 0.0
            scores[chunk_key] += 1.0 / (k + rank + 1)

        # 处理图像结果
        for rank, (entry, _) in enumerate(sorted(image_results, key=lambda x: -x[1])):
            chunk_key = f"{entry.chunk_type}_{entry.chunk_id}"
            if chunk_key not in scores:
                scores[chunk_key] = 0.0
            scores[chunk_key] += 1.0 / (k + rank + 1)

        # 构建entry到score的映射
        entry_scores = {}
        for entry, _ in text_results + image_results:
            chunk_key = f"{entry.chunk_type}_{entry.chunk_id}"
            entry_scores[(entry.chunk_type, entry.chunk_id)] = (entry, scores[chunk_key])

        # 排序
        sorted_results = sorted(entry_scores.values(), key=lambda x: -x[1])

        return sorted_results


def get_retriever() -> MultiModalRetriever:
    return MultiModalRetriever()