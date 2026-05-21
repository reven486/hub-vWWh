from typing import Optional
from pathlib import Path

from app.models.document import Chunk, ChunkType
from app.models.schemas import RetrievedChunk
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.vision_service import vision_service
from app.services.qdrant_service import qdrant_service
from app.ingestion.text_processor import text_processor
from app.ingestion.image_processor import image_processor
from app.ingestion.chunker import chunker
from app.knowledge_base.manager import kb_manager
from app.knowledge_base.document_store import document_store
from app.config import settings


class RAGPipeline:
    """RAG orchestration for both ingestion and query"""

    def ingest_document(
        self,
        file_content: bytes,
        filename: str,
    ) -> dict:
        """
        Full ingestion pipeline:
        1. Save file to disk
        2. Extract text/images
        3. Chunk
        4. Embed
        5. Upsert to Qdrant
        6. Update SQLite metadata
        """
        from app.models.schemas import DocStatus

        # Determine doc_type from extension
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext in {"pdf", "docx", "doc", "txt"}:
            doc_type = ext
        elif ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
            doc_type = ext
        else:
            doc_type = "unknown"

        # Create document record
        doc_id = kb_manager.add_document(
            source_file=filename,
            doc_type=doc_type,
            file_path="",  # Will update after save
            file_size=len(file_content),
        )

        # Save file to disk
        file_path = document_store.base_dir / doc_id / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_content)

        # Process based on type
        chunks: list[Chunk] = []

        if doc_type in {"pdf", "docx", "doc", "txt"}:
            # Text processing
            text_pages = text_processor.process(file_path, doc_type)
            for page_data in text_pages:
                text_chunks = chunker.chunk_text(
                    text=page_data["text"],
                    document_id=doc_id,
                    source_file=filename,
                    page=page_data["page"],
                )
                chunks.extend(text_chunks)

        elif doc_type in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
            # Image processing
            image_data = image_processor.process_image(file_path)
            image_chunk = chunker.chunk_image(
                document_id=doc_id,
                source_file=filename,
                base64_data=image_data["base64"],
                mime_type=image_data["mime_type"],
                original_width=image_data["original_width"],
                original_height=image_data["original_height"],
            )
            chunks.append(image_chunk)

        # Update file path in metadata
        kb_manager.update_document_status(doc_id, DocStatus.PROCESSING, len(chunks))

        # Embed chunks
        text_contents = []
        image_contents = []

        for chunk in chunks:
            if chunk.chunk_type == ChunkType.TEXT:
                text_contents.append(chunk.content)
            else:
                image_contents.append(chunk.content)

        embeddings = []
        embedding_types = []

        if text_contents:
            text_embeddings = embedding_service.embed_text(text_contents)
            embeddings.extend(text_embeddings)
            embedding_types.extend(["text"] * len(text_embeddings))

        if image_contents:
            image_embeddings = embedding_service.embed_image(image_contents)
            embeddings.extend(image_embeddings)
            embedding_types.extend(["image"] * len(image_embeddings))

        # Upsert to Qdrant
        ids = [chunk.id for chunk in chunks]
        payloads = [chunk.to_payload() for chunk in chunks]

        qdrant_service.upsert_points(ids, embeddings, payloads)

        # Update metadata
        kb_manager.update_document_status(doc_id, DocStatus.COMPLETED, len(chunks))
        kb_manager.update_index(doc_id, len(chunks))

        # Save chunks to SQLite
        for chunk in chunks:
            kb_manager.add_chunk(
                doc_id=doc_id,
                chunk_type=chunk.chunk_type.value,
                chunk_index=chunk.chunk_index,
                content_text=chunk.content[:1000] if len(chunk.content) > 1000 else chunk.content,
                page=chunk.page,
            )

        return {
            "document_id": doc_id,
            "chunk_count": len(chunks),
            "status": DocStatus.COMPLETED,
        }

    def query(
        self,
        query_text: Optional[str] = None,
        query_image: Optional[str] = None,  # base64
        top_k: int = 5,
    ) -> dict:
        """
        Query pipeline:
        1. If query contains image, use Qwen-VL to describe it
        2. Embed query (text or image description)
        3. ANN search in Qdrant
        4. Assemble prompt with retrieved chunks
        5. Call Qwen3 for final answer
        """
        image_description = None

        # Step 1: If query has image, get description via Qwen-VL
        if query_image:
            image_description = vision_service.describe_image(
                image_base64=query_image,
                prompt="请详细描述这张图片的内容，包括其中的文字、图表、布局等所有细节。",
            )

        # Step 2: Embed query
        if query_text and image_description:
            # Combine text query with image description
            combined_text = f"用户问题：{query_text}\n\n图片内容描述：{image_description}"
            query_vector = embedding_service.embed_text([combined_text])[0]
        elif query_text:
            query_vector = embedding_service.embed_text([query_text])[0]
        elif image_description:
            query_vector = embedding_service.embed_text([image_description])[0]
        else:
            raise ValueError("Either query_text or query_image must be provided")

        # Step 3: ANN search
        results = qdrant_service.search(query_vector, top_k=top_k)

        # Step 4: Assemble retrieved chunks
        retrieved_chunks = []
        context_parts = []

        for result in results:
            payload = result["payload"]
            retrieved_chunk = RetrievedChunk(
                chunk_id=payload["chunk_id"],
                document_id=payload["document_id"],
                chunk_type=payload["chunk_type"],
                content=payload["content"],
                score=result["score"],
                source_file=payload["source_file"],
                page=payload.get("page"),
            )
            retrieved_chunks.append(retrieved_chunk)

            # Build context for LLM
            if payload["chunk_type"] == "text":
                context_parts.append(f"[文档: {payload['source_file']}, 页码: {payload.get('page', 'N/A')}]\n{payload['content']}")
            else:
                context_parts.append(f"[图片: {payload['source_file']}]\n{payload.get('content', '')[:200]}...")

        # Step 5: Generate answer with Qwen3
        context = "\n\n---\n\n".join(context_parts)

        if query_text:
            prompt = f"""基于以下检索到的上下文内容，回答用户的问题。如果上下文中没有相关信息，请说明无法回答。

上下文：
{context}

用户问题：{query_text}
"""
        else:
            prompt = f"""基于以下检索到的图片描述和上下文内容，回答用户的问题。

上下文：
{context}

请生成回答。
"""

        answer = llm_service.generate(
            prompt=prompt,
            system_prompt="你是一个有用的AI助手，基于给定的上下文来回答问题。",
        )

        return {
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "has_image_query": query_image is not None,
        }

    def query_stream(
        self,
        query_text: Optional[str] = None,
        query_image: Optional[str] = None,
        top_k: int = 5,
    ):
        """Streaming query for SSE support"""
        image_description = None

        if query_image:
            image_description = vision_service.describe_image(
                image_base64=query_image,
                prompt="请详细描述这张图片的内容，包括其中的文字、图表、布局等所有细节。",
            )

        if query_text and image_description:
            combined_text = f"用户问题：{query_text}\n\n图片内容描述：{image_description}"
            query_vector = embedding_service.embed_text([combined_text])[0]
        elif query_text:
            query_vector = embedding_service.embed_text([query_text])[0]
        elif image_description:
            query_vector = embedding_service.embed_text([image_description])[0]
        else:
            raise ValueError("Either query_text or query_image must be provided")

        results = qdrant_service.search(query_vector, top_k=top_k)

        context_parts = []
        for result in results:
            payload = result["payload"]
            if payload["chunk_type"] == "text":
                context_parts.append(f"[文档: {payload['source_file']}, 页码: {payload.get('page', 'N/A')}]\n{payload['content']}")
            else:
                context_parts.append(f"[图片: {payload['source_file']}]\n{payload.get('content', '')[:200]}...")

        context = "\n\n---\n\n".join(context_parts)

        if query_text:
            prompt = f"""基于以下检索到的上下文内容，回答用户的问题。如果上下文中没有相关信息，请说明无法回答。

上下文：
{context}

用户问题：{query_text}
"""
        else:
            prompt = f"""基于以下检索到的图片描述和上下文内容，回答用户的问题。

上下文：
{context}

请生成回答。
"""

        for chunk in llm_service.generate_stream(
            prompt=prompt,
            system_prompt="你是一个有用的AI助手，基于给定的上下文来回答问题。",
        ):
            yield chunk


rag_pipeline = RAGPipeline()
