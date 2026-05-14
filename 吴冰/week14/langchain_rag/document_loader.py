# langchain_rag/document_loader.py
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_split_pdf(file_path: str, chunk_size: int = 256, chunk_overlap: int = 20):
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", "、", ""]
    )
    
    return text_splitter.split_documents(pages)

def load_documents_from_directory(directory: str):
    loader = DirectoryLoader(directory, glob="*.pdf", loader_cls=PyPDFLoader)
    return loader.load()