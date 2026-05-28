import asyncio
import logging
from app.db.kafka import kafka_client
from app.db.sqlite import sqlite_client
from app.services.parsing import parsing_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentParserWorker:
    def __init__(self):
        self._running = False

    async def process_document(self, document_id: str):
        logger.info(f"Processing document: {document_id}")
        try:
            doc_info = sqlite_client.get_document(document_id)
            if not doc_info:
                logger.error(f"Document not found: {document_id}")
                return

            file_path = doc_info["file_path"]
            parse_result = await parsing_service.parse_pdf(file_path)
            parsing_service.process_document(document_id, parse_result)
            logger.info(f"Document processed successfully: {document_id}")

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            sqlite_client.update_document_status(document_id, "failed")

    def run(self):
        self._running = True
        consumer = kafka_client.create_consumer()
        logger.info("Document parser worker started")

        for message in consumer:
            if not self._running:
                break
            document_id = message.value
            logger.info(f"Received parse task: {document_id}")
            asyncio.run(self.process_document(document_id))


if __name__ == "__main__":
    worker = DocumentParserWorker()
    worker.run()
