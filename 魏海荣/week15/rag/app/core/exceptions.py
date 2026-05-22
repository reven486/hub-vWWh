class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DocumentNotFoundError(AppException):
    """Document not found"""
    def __init__(self, document_id: str):
        super().__init__(f"Document not found: {document_id}", "DOC_NOT_FOUND")


class DocumentProcessingError(AppException):
    """Document processing failed"""
    def __init__(self, document_id: str, reason: str):
        super().__init__(f"Document processing failed: {reason}", "DOC_PROCESSING_ERROR")


class KnowledgeBaseNotFoundError(AppException):
    """Knowledge base not found"""
    def __init__(self, knowledge_base_id: str):
        super().__init__(f"Knowledge base not found: {knowledge_base_id}", "KB_NOT_FOUND")


class EmbeddingError(AppException):
    """Embedding generation failed"""
    def __init__(self, reason: str):
        super().__init__(f"Embedding error: {reason}", "EMBEDDING_ERROR")


class RetrievalError(AppException):
    """Retrieval failed"""
    def __init__(self, reason: str):
        super().__init__(f"Retrieval error: {reason}", "RETRIEVAL_ERROR")


class ParseError(AppException):
    """Parse error"""
    def __init__(self, reason: str):
        super().__init__(f"Parse error: {reason}", "PARSE_ERROR")
