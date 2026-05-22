import os
import uuid
import shutil
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.database import Document, Chunk, Image
from app.core.parser import get_parser, ParseResult
from app.core.chunker import create_chunker, Chunk as ChunkData
from app.core.embedder import get_text_embedder, get_image_embedder
from app.core.vector_store import get_vector_store, VectorEntry, init_vector_store
from app.config import settings


class DocumentService:
    """文档处理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.parser = get_parser()
        self.chunker = create_chunker()
        self.text_embedder = get_text_embedder()
        self.image_embedder = get_image_embedder()
        self.vector_store = get_vector_store()

    async def upload_document(self, file: UploadFile) -> Document:
        """
        上传并处理PDF文档

        Args:
            file: 上传的文件

        Returns:
            Document: 创建的文档记录
        """
        doc_id = str(uuid.uuid4())

        # 保存文件
        file_path = os.path.join(settings.DOCUMENT_PATH, f"{doc_id}_{file.filename}")
        os.makedirs(settings.DOCUMENT_PATH, exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 创建文档记录
        doc = Document(
            doc_id=doc_id,
            doc_name=file.filename,
            doc_path=file_path,
            status="parsing"
        )
        self.db.add(doc)
        self.db.commit()

        return doc

    async def process_document(self, doc_id: str) -> bool:
        """
        解析并向量化文档

        Args:
            doc_id: 文档ID

        Returns:
            bool: 处理是否成功
        """
        doc = self.db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc:
            return False

        try:
            # 1. 解析PDF
            parse_result = await self.parser.parse(doc.doc_path, doc_id)

            # 2. 切分内容
            chunks = self.chunker.chunk_document(parse_result.markdown, parse_result.images)

            # 3. 向量化并存储
            await self._index_chunks(doc_id, chunks, parse_result.images)

            # 4. 更新文档状态
            doc.status = "completed"
            self.db.commit()

            # 5. 保存向量索引
            self.vector_store.save(settings.VECTOR_INDEX_PATH)

            return True

        except Exception as e:
            doc.status = "failed"
            self.db.commit()
            raise e

    async def _index_chunks(
        self,
        doc_id: str,
        chunks: List[ChunkData],
        images: List
    ):
        """索引chunks到向量存储"""
        # 分离文本和图像chunks
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        image_chunks = [c for c in chunks if c.chunk_type == "image_caption"]

        # 处理文本chunks
        if text_chunks:
            texts = [c.content for c in text_chunks]
            vectors = await self.text_embedder.embed_texts(texts)

            text_entries = [
                VectorEntry(
                    vector_id=-1,
                    chunk_id=c.chunk_id,
                    chunk_type=c.chunk_type,
                    content=c.content,
                    doc_id=doc_id,
                    page=c.page
                )
                for c in text_chunks
            ]

            vector_ids = self.vector_store.add_text_vectors(vectors, text_entries)

            # 保存到数据库
            for chunk, vid in zip(text_chunks, vector_ids):
                db_chunk = Chunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    vector_id=vid,
                    page=chunk.page
                )
                self.db.add(db_chunk)

        # 处理图像chunks
        if image_chunks:
            image_paths = [img.image_path for img in images]
            if image_paths:
                vectors = await self.image_embedder.embed_images(image_paths)

                image_entries = [
                    VectorEntry(
                        vector_id=-1,
                        chunk_id=img.image_id,
                        chunk_type="image",
                        content=img.image_path,
                        doc_id=doc_id,
                        page=img.page
                    )
                    for img in images
                ]

                vector_ids = self.vector_store.add_image_vectors(vectors, image_entries)

                # 保存到数据库
                for img, vid in zip(images, vector_ids):
                    db_image = Image(
                        image_id=img.image_id,
                        doc_id=doc_id,
                        image_path=img.image_path,
                        caption=img.caption,
                        vector_id=vid,
                        page=img.page
                    )
                    self.db.add(db_image)

        self.db.commit()

    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档信息"""
        return self.db.query(Document).filter(Document.doc_id == doc_id).first()

    def get_chunks(self, doc_id: str) -> List[Chunk]:
        """获取文档的chunks"""
        return self.db.query(Chunk).filter(Chunk.doc_id == doc_id).all()

    def get_images(self, doc_id: str) -> List[Image]:
        """获取文档的图像"""
        return self.db.query(Image).filter(Image.doc_id == doc_id).all()

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        doc = self.db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc:
            return False

        # 删除文件
        if os.path.exists(doc.doc_path):
            os.remove(doc.doc_path)

        # 删除数据库记录
        self.db.query(Chunk).filter(Chunk.doc_id == doc_id).delete()
        self.db.query(Image).filter(Image.doc_id == doc_id).delete()
        self.db.delete(doc)
        self.db.commit()

        return True