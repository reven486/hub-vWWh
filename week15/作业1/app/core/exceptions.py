from fastapi import HTTPException


class DocumentNotFoundError(HTTPException):
    def __init__(self, doc_id: str):
        super().__init__(status_code=404, detail=f"Document {doc_id} not found")


class KnowledgeBaseNotFoundError(HTTPException):
    def __init__(self, kb_id: str):
        super().__init__(status_code=404, detail=f"Knowledge base {kb_id} not found")


class UnsupportedFileTypeError(HTTPException):
    def __init__(self, filename: str):
        super().__init__(status_code=400, detail=f"Unsupported file type: {filename}")


class DocumentParseError(Exception):
    def __init__(self, doc_id: str, reason: str):
        super().__init__(f"Failed to parse document {doc_id}: {reason}")
        self.doc_id = doc_id
        self.reason = reason


class EmbeddingError(Exception):
    pass


class RetrievalError(Exception):
    pass
