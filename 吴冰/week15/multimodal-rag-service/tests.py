import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_chunker():
    from services.chunker import split_text2chunks

    text = """# Introduction
This is a test paragraph.
[1] Some reference.

# References

More content here with important info."""

    chunks = split_text2chunks(text)
    assert len(chunks) > 0, "Should produce at least one chunk"
    # 应该跳过空行和 [1] 引用行和 # References
    combined = "\n".join(chunks)
    assert "[1]" not in combined, "Should filter reference lines"
    assert "# References" not in combined, "Should filter References header"
    print(f"  chunker: {len(chunks)} chunks, PASS")


def test_schemas():
    from schemas.document import DocumentUploadResponse, DocumentInfo
    from schemas.retrieval import RetrieveRequest, RetrieveResponse, RetrieveResult
    from schemas.chat import ChatRequest, ChatResponse, SourceInfo

    # 验证 schema 能正常序列化和反序列化
    doc_resp = DocumentUploadResponse(id=1, filename="test.pdf", filestate="已上传")
    assert doc_resp.id == 1
    print("  schemas.document: PASS")

    req = RetrieveRequest(query="test", top_k=3, modalities=["text", "image"])
    assert req.modalities == ["text", "image"]
    print("  schemas.retrieval: PASS")

    chat_req = ChatRequest(query="what is this?", top_k=5, stream=False)
    assert chat_req.query == "what is this?"
    print("  schemas.chat: PASS")


def test_vector_store_api():
    """测试 vector_store 模块能正常导入（不实际连接 Milvus）。"""
    from services.vector_store import insert_chunk, search, delete_by_db_id
    assert callable(insert_chunk)
    assert callable(search)
    assert callable(delete_by_db_id)
    print("  vector_store imports: PASS")


def test_qa_service_api():
    """测试 qa_service 模块能正常导入。"""
    from services.qa_service import generate_answer
    assert callable(generate_answer)
    print("  qa_service imports: PASS")


def test_pdf_parser_api():
    """测试 pdf_parser 模块能正常导入。"""
    from services.pdf_parser import parse_pdf
    assert callable(parse_pdf)
    print("  pdf_parser imports: PASS")


if __name__ == "__main__":
    print("Running tests...\n")

    test_chunker()
    test_schemas()
    test_vector_store_api()
    test_qa_service_api()
    test_pdf_parser_api()

    print("\nAll tests passed!")
