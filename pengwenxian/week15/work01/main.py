import os
import shutil
import asyncio
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import init_db, get_db, create_document, DocumentFile
from kafka_utils import init_kafka_producer, close_kafka_producer, send_document_message, consume_messages
from milvus_utils import init_milvus, search_chunks
from llm_utils import get_embedding, generate_answer

app = FastAPI(title="Document QA Service")

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    doc_id: int
    query: str

@app.on_event("startup")
async def startup_event():
    print("Initializing services...")
    # Initialize SQLite DB
    init_db()
    # Initialize Milvus
    init_milvus()
    # Initialize Kafka producer
    await init_kafka_producer()
    # Start Kafka consumer background task
    asyncio.create_task(consume_messages())
    print("Services initialized successfully.")

@app.on_event("shutdown")
async def shutdown_event():
    await close_kafka_producer()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Read file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")
        
    unique_filename = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Save to database
    db_doc = create_document(db, file.filename, file_path)
    
    # Send message to Kafka asynchronously
    await send_document_message(db_doc.id, file_path)
    
    return {
        "message": "File uploaded successfully. Processing started.", 
        "doc_id": db_doc.id, 
        "status": db_doc.status
    }

@app.get("/status/{doc_id}")
async def get_status(doc_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(DocumentFile).filter(DocumentFile.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": db_doc.id, "status": db_doc.status, "error_message": db_doc.error_message}

@app.post("/query")
async def query_document(request: QueryRequest, db: Session = Depends(get_db)):
    # Check document status
    db_doc = db.query(DocumentFile).filter(DocumentFile.id == request.doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_doc.status != "completed":
        raise HTTPException(status_code=400, detail=f"Document is not ready for querying. Current status: {db_doc.status}")
        
    # Generate query embedding
    query_embedding = await get_embedding(request.query)
    
    # Search in Milvus
    retrieved_texts = search_chunks(query_embedding, doc_id=request.doc_id, limit=3)
    
    if not retrieved_texts:
        return {"answer": "No relevant information found in the document.", "context": []}
        
    # Generate answer using LLM
    answer = await generate_answer(request.query, retrieved_texts)
    
    return {"answer": answer, "context": retrieved_texts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
