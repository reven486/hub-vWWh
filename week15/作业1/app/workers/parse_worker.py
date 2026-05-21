import asyncio
import logging

from app.db.kafka import get_consumer
from app.db.milvus import connect_milvus
from app.db.sqlite import init_db
from app.services.document import process_document

logger = logging.getLogger(__name__)


async def run_worker():
    await init_db()
    connect_milvus()

    consumer = await get_consumer()
    logger.info("Parse worker started, waiting for tasks...")

    try:
        async for msg in consumer:
            payload = msg.value
            doc_id = payload.get("doc_id")
            kb_id = payload.get("kb_id")

            if not doc_id or not kb_id:
                logger.warning("Invalid message payload: %s", payload)
                await consumer.commit()
                continue

            logger.info("Processing document %s for kb %s", doc_id, kb_id)
            try:
                await process_document(doc_id=doc_id, kb_id=kb_id)
                logger.info("Document %s processed successfully", doc_id)
            except Exception as e:
                logger.error("Failed to process document %s: %s", doc_id, e, exc_info=True)

            await consumer.commit()
    finally:
        await consumer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_worker())
