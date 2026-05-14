# langchain_rag/embeddings.py
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings(model_name: str = "BAAI/bge-small-zh-v1.5"):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True}
    )