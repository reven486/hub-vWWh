"""端到端 API 测试脚本。需要：pip install requests"""
import requests
import time

BASE = "http://127.0.0.1:8000"
TEST_PDF = "test.pdf"  # 准备一个 PDF 文件


def check_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    print("  /health: OK")


def test_upload():
    with open(TEST_PDF, "rb") as f:
        r = requests.post(f"{BASE}/api/v1/documents/upload", files={"file": ("test.pdf", f, "application/pdf")})
    print(f"  POST /upload: {r.status_code} -> {r.json()}")
    assert r.status_code == 200
    return r.json()["id"]


def test_list():
    r = requests.get(f"{BASE}/api/v1/documents/")
    print(f"  GET /documents: {r.status_code}, {len(r.json())} files")
    assert r.status_code == 200


def test_status(doc_id):
    r = requests.get(f"{BASE}/api/v1/documents/{doc_id}/status")
    print(f"  GET /status: {r.json()}")
    assert r.status_code == 200


def test_retrieve():
    r = requests.post(f"{BASE}/api/v1/retrieve/", json={"query": "test query", "top_k": 3})
    print(f"  POST /retrieve: {r.status_code} -> {len(r.json().get('results', []))} results")
    assert r.status_code == 200


def test_chat():
    r = requests.post(f"{BASE}/api/v1/chat/", json={"query": "what is this document about?", "top_k": 3})
    data = r.json()
    print(f"  POST /chat: {r.status_code}")
    print(f"    answer: {data.get('answer', '')[:100]}...")
    print(f"    sources: {len(data.get('sources', []))}")
    assert r.status_code == 200


def test_delete(doc_id):
    r = requests.delete(f"{BASE}/api/v1/documents/{doc_id}")
    print(f"  DELETE /{doc_id}: {r.status_code}")
    assert r.status_code == 200


if __name__ == "__main__":
    print("=== Full API Test ===\n")

    print("[1] Health check")
    check_health()

    print("\n[2] Upload PDF")
    doc_id = test_upload()

    print("\n[3] List documents")
    test_list()

    print("\n[4] Check status")
    test_status(doc_id)

    print("\n[5] Wait for parsing (30s)...")
    time.sleep(30)

    print("\n[6] Retrieve")
    test_retrieve()

    print("\n[7] Chat")
    test_chat()

    print("\n[8] Delete")
    test_delete(doc_id)

    print("\n=== All API tests passed! ===")
