"""
Comprehensive API Test Suite for Multimodal Document RAG

Tests all endpoints: health, knowledge bases CRUD, document upload, chat, and edge cases.
"""

import sys
import time
import json
import traceback

import requests

BASE_URL = "http://localhost:8001"

# ── Test state ──────────────────────────────────────────────────────────────
passed = 0
failed = 0
failures = []


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"\n         {detail}"
        print(msg)
        failures.append((name, detail))


def check_status(actual: int, expected: int | set | list, name: str, body=None):
    """Assert status code and return parsed JSON body (or None)."""
    if isinstance(expected, int):
        expected_set = {expected}
    else:
        expected_set = set(expected)

    ok = actual in expected_set
    detail = f"expected status {expected_set}, got {actual}"
    if body is not None and not ok:
        # Show response body on failure
        detail += f" | body: {body[:200] if isinstance(body, str) else json.dumps(body, ensure_ascii=False)[:200]}"
    report(name, ok, detail if not ok else "")
    return ok


def run():
    print("=" * 60)
    print("Comprehensive API Test Suite")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────────────────
    # 1. Health
    # ──────────────────────────────────────────────────────────────────────
    print("\n[1] Health")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        check_status(r.status_code, 200, "GET /health")
        body = r.json()
        if body.get("status") != "ok":
            report("GET /health status field", False, f"expected 'ok', got {body.get('status')}")
        else:
            report("GET /health status field", True)
    except Exception as e:
        report("GET /health", False, str(e))

    # ──────────────────────────────────────────────────────────────────────
    # 2. Knowledge Bases CRUD
    # ──────────────────────────────────────────────────────────────────────
    kb_ids_to_cleanup = []

    print("\n[2] Knowledge Bases CRUD")

    # 2a. Create KB
    try:
        payload = {"name": "test-kb-api", "description": "API test knowledge base"}
        r = requests.post(f"{BASE_URL}/knowledge-bases", json=payload, timeout=10)
        ok = check_status(r.status_code, 201, "POST /knowledge-bases (create)")
        if ok:
            body = r.json()
            kb_ids_to_cleanup.append(body["id"])
            if body.get("name") != "test-kb-api":
                report("POST /knowledge-bases name field", False, f"expected 'test-kb-api', got {body.get('name')}")
            else:
                report("POST /knowledge-bases name field", True)
            if "id" not in body:
                report("POST /knowledge-bases has id", False, "id field missing")
            else:
                report("POST /knowledge-bases has id", True)
    except Exception as e:
        report("POST /knowledge-bases (create)", False, str(e))

    # 2b. List KBs
    try:
        r = requests.get(f"{BASE_URL}/knowledge-bases", timeout=10)
        ok = check_status(r.status_code, 200, "GET /knowledge-bases (list)")
        if ok:
            body = r.json()
            if not isinstance(body, list):
                report("GET /knowledge-bases is list", False, f"got {type(body)}")
            elif len(body) == 0:
                report("GET /knowledge-bases non-empty", False, "list is empty after creating one")
            else:
                report("GET /knowledge-bases non-empty", True)
    except Exception as e:
        report("GET /knowledge-bases (list)", False, str(e))

    # 2c. Get single KB
    if kb_ids_to_cleanup:
        kb_id = kb_ids_to_cleanup[0]
        try:
            r = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}", timeout=10)
            ok = check_status(r.status_code, 200, f"GET /knowledge-bases/{kb_id} (get by id)")
            if ok:
                body = r.json()
                if body.get("id") != kb_id:
                    report("GET /knowledge-bases/{id} id match", False, f"expected {kb_id}, got {body.get('id')}")
                else:
                    report("GET /knowledge-bases/{id} id match", True)
        except Exception as e:
            report(f"GET /knowledge-bases/{kb_id} (get by id)", False, str(e))

    # 2d. Create duplicate → 409
    try:
        payload = {"name": "test-kb-api", "description": "duplicate"}
        r = requests.post(f"{BASE_URL}/knowledge-bases", json=payload, timeout=10)
        check_status(r.status_code, 409, "POST /knowledge-bases (duplicate -> 409)")
    except Exception as e:
        report("POST /knowledge-bases (duplicate -> 409)", False, str(e))

    # 2e. Delete KB
    if kb_ids_to_cleanup:
        kb_id = kb_ids_to_cleanup[0]
        try:
            r = requests.delete(f"{BASE_URL}/knowledge-bases/{kb_id}", timeout=10)
            check_status(r.status_code, 204, f"DELETE /knowledge-bases/{kb_id} (delete)")
        except Exception as e:
            report(f"DELETE /knowledge-bases/{kb_id} (delete)", False, str(e))

        # 2f. Get deleted KB → 404
        try:
            r = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}", timeout=10)
            check_status(r.status_code, 404, f"GET /knowledge-bases/{kb_id} (after delete -> 404)")
        except Exception as e:
            report(f"GET /knowledge-bases/{kb_id} (after delete -> 404)", False, str(e))

    # ──────────────────────────────────────────────────────────────────────
    # 3. Document Upload
    # ──────────────────────────────────────────────────────────────────────
    print("\n[3] Document Upload")

    # Create a KB to use for upload tests
    upload_kb_id = None
    try:
        r = requests.post(f"{BASE_URL}/knowledge-bases", json={"name": "upload-test-kb", "description": "For upload testing"}, timeout=10)
        if r.status_code == 201:
            upload_kb_id = r.json()["id"]
            print(f"  Created KB {upload_kb_id} for upload tests")
    except Exception:
        pass

    if upload_kb_id is None:
        # Maybe it already exists from a previous run
        try:
            r = requests.get(f"{BASE_URL}/knowledge-bases", timeout=10)
            for kb in r.json():
                if kb["name"] == "upload-test-kb":
                    upload_kb_id = kb["id"]
                    print(f"  Reusing existing KB {upload_kb_id} for upload tests")
                    break
        except Exception:
            pass

    if upload_kb_id is None:
        report("SETUP: create KB for upload", False, "Could not create KB, skipping upload tests that need one")
    else:
        # 3a. Upload valid PDF → 201
        try:
            # Create minimal valid PDF
            pdf_bytes = (
                b"%PDF-1.4\n"
                b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
                b"xref\n"
                b"0 4\n"
                b"0000000000 65535 f \n"
                b"0000000009 00000 n \n"
                b"0000000058 00000 n \n"
                b"0000000115 00000 n \n"
                b"trailer<</Size 4/Root 1 0 R>>\n"
                b"startxref\n"
                b"190\n"
                b"%%EOF"
            )
            files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
            data = {"knowledge_base_id": upload_kb_id}
            r = requests.post(f"{BASE_URL}/upload/document", files=files, data=data, timeout=30)
            ok = check_status(r.status_code, 201, "POST /upload/document (valid PDF)")
            if ok:
                body = r.json()
                doc_id = body.get("id")
                if body.get("filename") != "test_doc.pdf":
                    report("POST /upload/document filename field", False, f"expected 'test_doc.pdf', got {body.get('filename')}")
                else:
                    report("POST /upload/document filename field", True)
                if body.get("knowledge_base_id") != upload_kb_id:
                    report("POST /upload/document KB id match", False, f"expected {upload_kb_id}, got {body.get('knowledge_base_id')}")
                else:
                    report("POST /upload/document KB id match", True)
                if "status" not in body:
                    report("POST /upload/document status field", False, "status field missing")
                else:
                    report("POST /upload/document status field", True)
        except Exception as e:
            report("POST /upload/document (valid PDF)", False, str(e))

        # 3b. Upload non-PDF file → 400
        try:
            files = {"file": ("test.txt", b"this is not a pdf", "text/plain")}
            data = {"knowledge_base_id": upload_kb_id}
            r = requests.post(f"{BASE_URL}/upload/document", files=files, data=data, timeout=30)
            check_status(r.status_code, 400, "POST /upload/document (non-PDF -> 400)")
        except Exception as e:
            report("POST /upload/document (non-PDF -> 400)", False, str(e))

        # 3c. Upload to non-existent KB → 404
        try:
            pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF"
            files = {"file": ("dummy.pdf", pdf_bytes, "application/pdf")}
            data = {"knowledge_base_id": 99999}
            r = requests.post(f"{BASE_URL}/upload/document", files=files, data=data, timeout=30)
            check_status(r.status_code, 404, "POST /upload/document (bad KB id -> 404)")
        except Exception as e:
            report("POST /upload/document (bad KB id -> 404)", False, str(e))

        # 3d. Upload with missing knowledge_base_id → 422
        try:
            pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF"
            files = {"file": ("dummy.pdf", pdf_bytes, "application/pdf")}
            r = requests.post(f"{BASE_URL}/upload/document", files=files, timeout=30)
            check_status(r.status_code, 422, "POST /upload/document (missing KB id -> 422)")
        except Exception as e:
            report("POST /upload/document (missing KB id -> 422)", False, str(e))

    # 3e. List all documents
    try:
        r = requests.get(f"{BASE_URL}/upload/documents", timeout=10)
        ok = check_status(r.status_code, 200, "GET /upload/documents (list all)")
        if ok:
            body = r.json()
            if not isinstance(body, list):
                report("GET /upload/documents is list", False, f"got {type(body)}")
            else:
                report("GET /upload/documents is list", True)
    except Exception as e:
        report("GET /upload/documents (list all)", False, str(e))

    # 3f. Filter documents by KB
    if upload_kb_id:
        try:
            r = requests.get(f"{BASE_URL}/upload/documents", params={"knowledge_base_id": upload_kb_id}, timeout=10)
            ok = check_status(r.status_code, 200, f"GET /upload/documents?knowledge_base_id={upload_kb_id}")
            if ok:
                body = r.json()
                all_match = all(d.get("knowledge_base_id") == upload_kb_id for d in body)
                if not all_match:
                    report("GET /upload/documents filtered KB id", False, "not all results match KB id")
                else:
                    report("GET /upload/documents filtered KB id", True)
        except Exception as e:
            report(f"GET /upload/documents?knowledge_base_id={upload_kb_id}", False, str(e))

    # ──────────────────────────────────────────────────────────────────────
    # 4. Chat
    # ──────────────────────────────────────────────────────────────────────
    print("\n[4] Chat")

    # 4a. Chat with non-existent KB → 404
    try:
        payload = {"knowledge_base_id": 99999, "question": "What is RAG?", "top_k": 3}
        r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=15)
        check_status(r.status_code, 404, "POST /chat (bad KB id -> 404)")
    except Exception as e:
        report("POST /chat (bad KB id -> 404)", False, str(e))

    # 4b. Chat with a real KB (may load models -- slow)
    # Note: may return 503 if backend models (CLIP/BGE/Milvus) are unavailable
    CHAT_OK_STATUSES = {200, 503}
    if upload_kb_id:
        try:
            payload = {"knowledge_base_id": upload_kb_id, "question": "What is the capital of France?", "top_k": 3}
            print("  POST /chat (loading models may take a while, timeout=120s)...")
            start = time.time()
            r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=120)
            elapsed = time.time() - start
            ok = check_status(r.status_code, CHAT_OK_STATUSES, f"POST /chat (real KB) [{elapsed:.1f}s]")
            if r.status_code == 200:
                body = r.json()
                if "answer" not in body:
                    report("POST /chat has answer field", False, "answer field missing")
                else:
                    report("POST /chat has answer field", True)
                if "sources" not in body:
                    report("POST /chat has sources field", False, "sources field missing")
                else:
                    report("POST /chat has sources field", True)
            elif r.status_code == 503:
                body = r.json()
                has_detail = "detail" in body
                report("POST /chat 503 response has detail", has_detail,
                       f"body keys: {list(body.keys())}" if not has_detail else "")
        except requests.Timeout:
            report("POST /chat (real KB) [timeout]", False, "Request timed out after 120s")
        except Exception as e:
            report("POST /chat (real KB)", False, str(e))

    # ──────────────────────────────────────────────────────────────────────
    # 5. Edge Cases & Validation
    # ──────────────────────────────────────────────────────────────────────
    print("\n[5] Edge Cases & Validation")

    # 5a. Empty body on POST /knowledge-bases → 422
    try:
        r = requests.post(f"{BASE_URL}/knowledge-bases", json={}, timeout=10)
        check_status(r.status_code, 422, "POST /knowledge-bases empty body -> 422")
    except Exception as e:
        report("POST /knowledge-bases empty body -> 422", False, str(e))

    # 5b. Missing name field → 422
    try:
        r = requests.post(f"{BASE_URL}/knowledge-bases", json={"description": "no name"}, timeout=10)
        check_status(r.status_code, 422, "POST /knowledge-bases missing name -> 422")
    except Exception as e:
        report("POST /knowledge-bases missing name -> 422", False, str(e))

    # 5c. Invalid type for kb_id (string instead of int)
    try:
        r = requests.get(f"{BASE_URL}/knowledge-bases/abc", timeout=10)
        check_status(r.status_code, 422, "GET /knowledge-bases/abc (string id -> 422)")
    except Exception as e:
        report("GET /knowledge-bases/abc (string id -> 422)", False, str(e))

    # 5d. Invalid type for knowledge_base_id in chat
    try:
        payload = {"knowledge_base_id": "abc", "question": "test"}
        r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)
        check_status(r.status_code, 422, "POST /chat string KB id -> 422")
    except Exception as e:
        report("POST /chat string KB id -> 422", False, str(e))

    # 5e. Missing question field
    try:
        payload = {"knowledge_base_id": 1}
        r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)
        check_status(r.status_code, 422, "POST /chat missing question -> 422")
    except Exception as e:
        report("POST /chat missing question -> 422", False, str(e))

    # ──────────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────────
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failures:
        print("\nFAILURE DETAILS:")
        for name, detail in failures:
            print(f"  - {name}")
            if detail:
                print(f"    {detail}")

    return failed == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
