# langchain_rag/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from langchain_rag.document_loader import load_and_split_pdf
from langchain_rag.vector_store import get_vector_store, add_documents_to_store
from langchain_rag.qa_chain import create_qa_chain, query_with_rag
from langchain_rag.conversation_chain import create_conversational_rag_chain
import shutil
import os
import traceback

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

conversation_chains = {}

@app.post("/v1/document")
async def add_document(
    knowledge_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{knowledge_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        documents = load_and_split_pdf(file_path)

        store = get_vector_store()
        add_documents_to_store(store, documents, knowledge_id)

        return {"status": "success", "message": "文档添加成功", "docs_count": len(documents)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "trace": traceback.format_exc()}
        )

@app.post("/chat")
async def chat(
    knowledge_id: int = Form(...),
    question: str = Form(...),
    session_id: str = Form(None)
):
    try:
        if session_id not in conversation_chains:
            conversation_chains[session_id] = create_conversational_rag_chain(knowledge_id)

        chain = conversation_chains[session_id]
        answer = chain.invoke({"question": question, "chat_history": []})

        return {"answer": answer}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "trace": traceback.format_exc()}
        )

@app.post("/query")
async def query(
    knowledge_id: int = Form(...),
    question: str = Form(...)
):
    try:
        qa_chain = create_qa_chain(knowledge_id)
        result = query_with_rag(qa_chain, question)

        return {
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "trace": traceback.format_exc()}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6006)
