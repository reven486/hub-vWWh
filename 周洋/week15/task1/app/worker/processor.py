import json
import os
import asyncio

from app.core.config import settings
from app.models.database import Document, DocumentStatus, TextChunk, ImageRecord, get_session


async def process_document(document_id: int):
    db = get_session()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.processing
        db.commit()

        from app.services.parser import PdfParser
        from app.services.embedder import BgeEmbedder, ClipEmbedder
        from app.services.retriever import MilvusRetriever

        parser = PdfParser()
        bge = BgeEmbedder()
        clip = ClipEmbedder()
        retriever = MilvusRetriever()

        doc_dir = os.path.join(settings.processed_dir, str(document_id))
        parse_result = parser.parse(doc.file_path, doc_dir)

        if not parse_result.get("success"):
            doc.status = DocumentStatus.failed
            doc.error_message = parse_result.get("error", "Unknown parse error")
            db.commit()
            return

        markdown = parse_result.get("markdown", "")
        image_paths = parse_result.get("image_paths", [])

        # Chunk the markdown text
        chunks = _chunk_text(markdown, chunk_size=256)
        for idx, chunk_text in enumerate(chunks):
            bge_vec = bge.embed_text([chunk_text])[0]
            clip_vec = clip.embed_text([chunk_text])[0]

            chunk_record = TextChunk(
                document_id=document_id,
                page_number=1,
                chunk_index=idx,
                content=chunk_text,
                char_count=len(chunk_text),
            )
            db.add(chunk_record)
            db.flush()

            retriever.insert_text_chunk(
                document_id=document_id,
                chunk_id=chunk_record.id,
                page_number=1,
                text_content=chunk_text,
                bge_vector=bge_vec,
                clip_vector=clip_vec,
            )

        # Process images
        for img_idx, img_path in enumerate(image_paths):
            clip_vec = clip.embed_image([img_path])[0]

            img_record = ImageRecord(
                document_id=document_id,
                page_number=1,
                image_path=img_path,
                image_index=img_idx,
            )
            db.add(img_record)
            db.flush()

            retriever.insert_image(
                document_id=document_id,
                image_id=img_record.id,
                page_number=1,
                image_path=img_path,
                clip_vector=clip_vec,
            )

        doc.status = DocumentStatus.completed
        doc.page_count = max(
            max((c.page_number for c in chunks), default=0),
            max((i.page_number for i in image_paths), default=0) if image_paths else 0,
        )
        db.commit()

    except Exception as e:
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.failed
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


def _chunk_text(text: str, chunk_size: int = 256, overlap: int = 32) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def send_parse_event(document_id: int):
    try:
        from aiokafka import AIOKafkaProducer
        import asyncio

        async def send():
            producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
            await producer.start()
            try:
                message = json.dumps({"document_id": document_id}).encode("utf-8")
                await producer.send(settings.kafka_topic, message)
            finally:
                await producer.stop()

        asyncio.run(send())
    except Exception:
        pass


async def consume_parse_events():
    from aiokafka import AIOKafkaConsumer

    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            doc_id = data.get("document_id")
            if doc_id:
                await process_document(doc_id)
    finally:
        await consumer.stop()


def run_worker():
    asyncio.run(consume_parse_events())
