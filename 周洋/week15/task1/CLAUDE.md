# Multimodal Document RAG Guide

## Project Overview
Multimodal Document Retrieval-Augmented Generation system that processes PDF documents containing mixed text and images, enabling cross-modal retrieval and Q&A over document knowledge bases.

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **PDF Parsing**: MinerU
- **Embedding Models**: BGE (text), Jina CLIP (multimodal)
- **Vector DB**: Milvus (self-hosted via Docker)
- **Message Queue**: Kafka (async document processing pipeline)
- **Metadata Storage**: MySQL via SQLAlchemy
- **LLM**: Qwen-VL (multimodal Q&A)

## Project Structure

```
multimodal-document-rag/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py # Knowledge base CRUD
│   │   ├── upload.py         # Document upload API
│   │   └── chat.py           # Q&A chat API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Settings via env vars
│   │   └── dependencies.py   # FastAPI dependency injection
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py       # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embedder.py       # BGE + CLIP embedding
│   │   ├── parser.py         # MinerU PDF parsing
│   │   └── retriever.py      # Milvus vector search
│   └── worker/
│       ├── __init__.py
│       └── processor.py      # Kafka consumer worker
├── processed/                # MinerU output dir
├── uploads/                  # Uploaded PDFs
├── docker-compose.yml        # Kafka, Zookeeper, Milvus
├── requirements.txt
├── CLAUDE.md
└── docs/
    └── requirements.md
```

## Architecture
```
Upload PDF → Kafka Topic → Worker (MinerU parse → chunk → embed → Milvus)
User Query → Embed (BGE + CLIP) → Milvus Search → Score Fusion → LLM (Qwen-VL) → Answer
```

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start worker
python -m app.worker.processor
```

### Infrastructure
```bash
# Start Kafka + Zookeeper + Milvus
docker-compose up -d
```

### Code Quality
```bash
# Lint & format
ruff check .
ruff format .
```

## Design Principles

### Document Processing (Offline)
- PDF parsing is GPU-intensive and slow → always async via Kafka
- MinerU output: markdown + extracted images stored locally
- Chunk strategy: 256-char sliding window with image reference preservation
- Dual embedding: BGE for text retrieval, CLIP for multimodal retrieval

### Retrieval Strategy
- Query is embedded with both BGE and CLIP
- Search milvus for: bge_vector (text), clip_vector (text + image)
- Fuse text and image scores with configurable weights
- Return top-K results sorted by fused score

### Q&A Pipeline
- Retrieved chunks + images form the context
- Qwen-VL receives: user question + retrieved text + image references
- Answer cites source file and page
- Fallback to retrieved text summary if Qwen-VL unavailable

### Key Conventions
- All vector dims: BGE=512, CLIP=1024
- Collection naming: `rag_data`
- File states: `uploaded` → `processing` → `completed` / `failed`
- Kafka topic: `rag-data` for document processing events
- Never commit model weights or credentials to git
