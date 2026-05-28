# langchain_rag/vector_store.py
from langchain_community.vectorstores import FAISS
from langchain_rag.embeddings import get_embeddings
import os

VECTOR_STORE_DIR = "vector_stores"

def get_vector_store(knowledge_id: int = None):
    embeddings = get_embeddings()

    store_path = os.path.join(VECTOR_STORE_DIR, f"faiss_store_{knowledge_id}")

    if os.path.exists(store_path):
        return FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
    else:
        return FAISS(embedding_function=embeddings, index=None, docstore=None, index_to_docstore_id=None)

def add_documents_to_store(store, documents, knowledge_id: int):
    for doc in documents:
        doc.metadata["knowledge_id"] = knowledge_id

    if store.index is None:
        store = FAISS.from_documents(documents, store.embedding_function)
    else:
        store.add_documents(documents)

    store_path = os.path.join(VECTOR_STORE_DIR, f"faiss_store_{knowledge_id}")
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    store.save_local(store_path)

    return store
