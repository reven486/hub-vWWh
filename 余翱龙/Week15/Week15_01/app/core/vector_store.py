import faiss
import numpy as np
import os
import pickle
from typing import List, Tuple, Optional
from dataclasses import dataclass
from app.config import settings


@dataclass
class VectorEntry:
    vector_id: int
    chunk_id: str
    chunk_type: str  # text, image
    content: str
    doc_id: str
    page: Optional[int] = None


class FAISSVectorStore:
    """FAISS向量存储封装"""

    def __init__(self, dimension: int, index_type: str = "IVF"):
        self.dimension = dimension
        self.index_type = index_type
        self.text_index: Optional[faiss.Index] = None
        self.image_index: Optional[faiss.Index] = None
        self.text_entries: List[VectorEntry] = []
        self.image_entries: List[VectorEntry] = []
        self.text_vector_ids: List[int] = []
        self.image_vector_ids: List[int] = []
        self._next_text_id = 0
        self._next_image_id = 0

    def _create_index(self, dimension: int) -> faiss.Index:
        """创建FAISS索引"""
        # 使用Flat索引，避免IVF索引的小数据集训练问题
        index = faiss.IndexFlatL2(dimension)
        return index

    def init_text_index(self):
        """初始化文本向量索引"""
        self.text_index = self._create_index(self.dimension)
        self.text_entries = []
        self.text_vector_ids = []
        self._next_text_id = 0

    def init_image_index(self):
        """初始化图像向量索引"""
        self.image_index = self._create_index(settings.CLIP_DIM)
        self.image_entries = []
        self.image_vector_ids = []
        self._next_image_id = 0

    def add_text_vectors(self, vectors: np.ndarray, entries: List[VectorEntry]) -> List[int]:
        """
        添加文本向量

        Args:
            vectors: 文本向量数组 (N, dimension)
            entries: 向量对应的entries

        Returns:
            List[int]: 分配的vector_ids
        """
        if self.text_index is None:
            self.init_text_index()

        if not self.text_index.is_trained:
            self.text_index.train(vectors.astype("float32"))

        vector_ids = []
        for i in range(len(vectors)):
            vid = self._next_text_id
            self._next_text_id += 1
            vector_ids.append(vid)
            self.text_entries.append(entries[i])
            self.text_vector_ids.append(vid)

        self.text_index.add(vectors.astype("float32"))
        return vector_ids

    def add_image_vectors(self, vectors: np.ndarray, entries: List[VectorEntry]) -> List[int]:
        """
        添加图像向量

        Args:
            vectors: 图像向量数组 (N, CLIP_DIM)
            entries: 向量对应的entries

        Returns:
            List[int]: 分配的vector_ids
        """
        if self.image_index is None:
            self.init_image_index()

        if not self.image_index.is_trained:
            self.image_index.train(vectors.astype("float32"))

        vector_ids = []
        for i in range(len(vectors)):
            vid = self._next_image_id
            self._next_image_id += 1
            vector_ids.append(vid)
            self.image_entries.append(entries[i])
            self.image_vector_ids.append(vid)

        self.image_index.add(vectors.astype("float32"))
        return vector_ids

    def search_text(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        搜索文本向量

        Args:
            query_vector: 查询向量 (dimension,)
            k: 返回前k个结果

        Returns:
            List[Tuple[vector_id, distance]]: 搜索结果
        """
        if self.text_index is None or self.text_index.ntotal == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype("float32")
        distances, indices = self.text_index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.text_entries):
                results.append((int(idx), float(dist)))
        return results

    def search_image(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        搜索图像向量

        Args:
            query_vector: 查询向量 (CLIP_DIM,)
            k: 返回前k个结果

        Returns:
            List[Tuple[vector_id, distance]]: 搜索结果
        """
        if self.image_index is None or self.image_index.ntotal == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype("float32")
        distances, indices = self.image_index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.image_entries):
                results.append((int(idx), float(dist)))
        return results

    def get_text_entry(self, index: int) -> Optional[VectorEntry]:
        """根据index获取text entry"""
        if 0 <= index < len(self.text_entries):
            return self.text_entries[index]
        return None

    def get_image_entry(self, index: int) -> Optional[VectorEntry]:
        """根据index获取image entry"""
        if 0 <= index < len(self.image_entries):
            return self.image_entries[index]
        return None

    def save(self, path: str):
        """保存索引到磁盘"""
        os.makedirs(path, exist_ok=True)

        # 保存文本索引
        if self.text_index is not None:
            faiss.write_index(self.text_index, os.path.join(path, "text_index.faiss"))

        # 保存图像索引
        if self.image_index is not None:
            faiss.write_index(self.image_index, os.path.join(path, "image_index.faiss"))

        # 保存entries
        with open(os.path.join(path, "text_entries.pkl"), "wb") as f:
            pickle.dump(self.text_entries, f)
        with open(os.path.join(path, "image_entries.pkl"), "wb") as f:
            pickle.dump(self.image_entries, f)

        # 保存状态
        state = {
            "next_text_id": self._next_text_id,
            "next_image_id": self._next_image_id
        }
        with open(os.path.join(path, "state.pkl"), "wb") as f:
            pickle.dump(state, f)

    def load(self, path: str):
        """从磁盘加载索引"""
        text_index_path = os.path.join(path, "text_index.faiss")
        image_index_path = os.path.join(path, "image_index.faiss")

        if os.path.exists(text_index_path):
            self.text_index = faiss.read_index(text_index_path)
        if os.path.exists(image_index_path):
            self.image_index = faiss.read_index(image_index_path)

        entries_path = os.path.join(path, "text_entries.pkl")
        if os.path.exists(entries_path):
            with open(entries_path, "rb") as f:
                self.text_entries = pickle.load(f)

        entries_path = os.path.join(path, "image_entries.pkl")
        if os.path.exists(entries_path):
            with open(entries_path, "rb") as f:
                self.image_entries = pickle.load(f)

        state_path = os.path.join(path, "state.pkl")
        if os.path.exists(state_path):
            with open(state_path, "rb") as f:
                state = pickle.load(f)
                self._next_text_id = state["next_text_id"]
                self._next_image_id = state["next_image_id"]


# 全局向量存储实例
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(dimension=settings.BGE_DIM)
        # 尝试加载已有索引
        if os.path.exists(settings.VECTOR_INDEX_PATH):
            _vector_store.load(settings.VECTOR_INDEX_PATH)
    return _vector_store


def init_vector_store():
    """初始化向量存储"""
    global _vector_store
    _vector_store = FAISSVectorStore(dimension=settings.BGE_DIM)
    _vector_store.init_text_index()
    _vector_store.init_image_index()
    return _vector_store