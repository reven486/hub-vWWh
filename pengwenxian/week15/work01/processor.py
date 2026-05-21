import os
from database import SessionLocal, update_document_status, FileStatus
from mineru_utils import parse_with_mineru
from milvus_utils import insert_chunks
from llm_utils import get_embedding

async def process_document(doc_id: int, file_path: str):
    """
    Background task triggered by Kafka consumer.
    1. Parse document with Mineru.
    2. Split into chunks.
    3. Generate embeddings.
    4. Store in Milvus.
    5. Update database status.
    """
    db = SessionLocal()
    try:
        # Update status to processing
        update_document_status(db, doc_id, FileStatus.PROCESSING.value)
        
        # 1. Parse document
        parsed_text = parse_with_mineru(file_path)
        
        # 2. Split into chunks (Simple chunking by paragraphs or fixed length)
        # For simplicity, we split by paragraphs here.
        chunks = [chunk.strip() for chunk in parsed_text.split('\n\n') if chunk.strip()]
        if not chunks:
            chunks = [parsed_text]
            
        # 3. Generate embeddings
        embeddings = []
        for chunk in chunks:
            emb = await get_embedding(chunk)
            embeddings.append(emb)
            
        # 4. Store in Milvus
        insert_chunks(doc_id, chunks, embeddings)
        
        # 5. Update database status to completed
        update_document_status(db, doc_id, FileStatus.COMPLETED.value)
        print(f"Document {doc_id} processed successfully.")
        
    except Exception as e:
        print(f"Error processing document {doc_id}: {e}")
        update_document_status(db, doc_id, FileStatus.FAILED.value, error_message=str(e))
    finally:
        db.close()
