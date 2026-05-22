# Multimodal RAG 系统实现计划

## Context

用户需要构建一个多模态 RAG 系统，支持图像+文本的混合检索与推理回答。选择全部通过 **Qwen3 API** 调用（DashScope/阿里云百炼），不再自托管 vLLM/LLaVA 等 GPU 推理服务。

**简化后的技术选型**：
- LLM 生成：Qwen3 系列 API（DashScope）
- 视觉理解：Qwen-VL API（Qwen3-VL）
- 多模态嵌入：**DashScope Embedding API**（text-embedding-v3 或 multimodal-embedding-v1）— 不再自建 CLIP 服务
- 向量数据库：Qdrant（保留）
- 框架：FastAPI + LlamaIndex

---

## 项目结构

```
C:\Users\huang\Desktop\multimodal-rag\
├── docker-compose.yml                # 2个容器：qdrant, app
├── .env.example                      # DASHSCOPE_API_KEY
├── pyproject.toml
├── Dockerfile.app
├── data/
│   ├── documents/                    # 原始文档存储（PDF/DOCX/图片等）
│   └── qdrant_storage/               # Qdrant 持久化数据
├── app/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py
│   ├── api/
│   │   ├── router.py
│   │   ├── ingest.py                 # POST /ingest
│   │   ├── query.py                  # POST /query
│   │   ├── collection.py             # 集合管理
│   │   └── health.py                 # GET /health
│   ├── services/
│   │   ├── embedding_service.py      # DashScope Embedding API
│   │   ├── llm_service.py            # Qwen3 API (LLM 生成)
│   │   ├── vision_service.py         # Qwen-VL API (视觉理解)
│   │   ├── qdrant_service.py         # Qdrant 存取
│   │   └── pipeline.py               # RAG 编排
│   ├── models/
│   │   ├── schemas.py                # Pydantic 模型
│   │   └── document.py               # Document/TextChunk/ImageChunk
│   └── ingestion/
│       ├── chunker.py
│       ├── text_processor.py         # PDF/DOCX/TXT 提取
│       └── image_processor.py        # 图像加载、base64
│   └── knowledge_base/
│       ├── __init__.py
│       ├── manager.py                # 知识库元数据管理（SQLite）
│       └── document_store.py         # 原始文档持久化存储
└── tests/
    ├── test_ingestion.py
    ├── test_query.py
    └── test_pipeline.py
```

---

## 实现步骤

### Phase 1 — 基础设施
1. 创建项目骨架、pyproject.toml
2. 编写 docker-compose.yml（2个容器：qdrant, app；DashScope 走 API 不需要容器）
3. 实现 config.py（环境变量：DASHSCOPE_API_KEY, QDRANT_URL 等）
4. 初始化 SQLite 数据库表结构（documents/chunks/indexes）
5. 验证 Qdrant 正常启动并创建 `multimodal_rag` collection

### Phase 2 — 知识库基础
6. 实现 knowledge_base/document_store.py（原始文件持久化到 data/documents/）
7. 实现 knowledge_base/manager.py（SQLite CRUD：add/get/list/delete_document）

### Phase 3 — 摄取管道
8. 实现 qdrant_service.py（collection 创建、upsert、ANN search、delete by document_id）
9. 实现 text_processor.py（PDF/DOCX/TXT 文本提取）
10. 实现 image_processor.py（图像加载、resize、base64 编码）
11. 实现 chunker.py（文本语义分块、图像作为独立块，输出 TextChunk/ImageChunk）
12. 实现 embedding_service.py（调用 DashScope Embedding API，支持 text 和 image 两种输入）
13. 实现 ingest 完整流程：文件上传 → 解析 → 分块 → 嵌入 → 批量 upsert 到 Qdrant → 更新 SQLite 元数据
14. 实现 DELETE /documents/{doc_id}（删除 Qdrant points + 磁盘文件 + SQLite 记录）

### Phase 4 — 查询管道
15. 实现 llm_service.py（Qwen3 API /v1/chat/completions 调用）
16. 实现 vision_service.py（Qwen-VL API 图像理解）
17. 实现 pipeline.py：
    - 查询嵌入（文本或图像 → 向量）
    - Qdrant ANN 检索 top-K
    - 若查询含图像，用 Qwen-VL 生成图像描述作为额外 context
    - 组装 prompt（检索到的文本/图像描述 + 用户问题）
    - 调用 Qwen3 生成最终答案
18. 实现 POST /query（文本查询 + 图像+文本混合查询）
19. 添加 SSE 流式输出支持

### Phase 5 — 收尾
20. 实现 GET /collection/stats（Qdrant 集合统计）
21. 实现 POST /collection/reset（清空整个 collection 和 SQLite 数据）
22. 实现 GET /health（检查 Qdrant + DashScope API 连通性）
23. 集成测试（ingest → query 全流程）

---

## 知识库管理

知识库不仅仅是向量检索，还包括文档的完整生命周期管理：

### 文档存储（Document Store）
- 原始文件持久化到 `data/documents/` 目录，按 `source_file` 组织子目录
- 文件名格式：`{document_id}/{original_filename}`，保证唯一性
- 同时记录到 SQLite 数据库（`data/metadata.db`）维护元数据

### 元数据数据库（SQLite Schema）
```sql
-- documents 表：记录每个上传的文档
CREATE TABLE documents (
    id TEXT PRIMARY KEY,              -- UUID
    source_file TEXT NOT NULL,       -- 原始文件名
    doc_type TEXT NOT NULL,          -- pdf/docx/txt/png/jpg
    file_path TEXT NOT NULL,         -- 磁盘存储路径
    file_size INTEGER,               -- 文件大小
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER DEFAULT 0,   -- 分块数量
    status TEXT DEFAULT 'processing' -- processing/completed/failed
);

-- chunks 表：记录每个分块的信息
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,             -- UUID
    document_id TEXT NOT NULL,       -- 关联 documents.id
    chunk_type TEXT NOT NULL,         -- text / image
    chunk_index INTEGER NOT NULL,     -- 块在文档中的顺序
    content_text TEXT,                -- 文本内容（或图像的 base64 前缀）
    page INTEGER,                    -- 页码（PDF/DOCX）
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- indexes 表：记录向量索引信息
CREATE TABLE indexes (
    document_id TEXT PRIMARY KEY,
    qdrant_points_count INTEGER,
    last_indexed_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

### 知识库操作（Knowledge Base Manager）
| 操作 | 说明 |
|---|---|
| `add_document(file)` | 保存原始文件，写入 documents 表，触发分块流程 |
| `get_document(id)` | 获取文档元数据 |
| `list_documents()` | 列出所有已入库文档 |
| `delete_document(id)` | 删除 Qdrant 中的关联 points，删除磁盘文件，删除 SQLite 记录 |
| `rebuild_index(id)` | 重新分块、重新嵌入、更新 Qdrant |

---

## 核心设计决策

1. **DashScope 统一嵌入**：使用 DashScope 的 `text-embedding-v3` 或 `multimodal-embedding-v1` API，所有文本和图像块统一嵌入到同一向量空间，一次 ANN 检索同时返回两种类型的相关块
2. **Qdrant 单 collection + named vector**：`multimodal_rag` 集合，向量名 `embedding`，维度 1024 或 1536（取决于 DashScope 返回维度），Cosine 距离
3. **chunk payload schema**（存 Qdrant payload）：
   ```json
   {
     "chunk_id": "uuid",
     "document_id": "uuid",
     "chunk_type": "text" | "image",
     "content": "<text>" | "<base64>",
     "source_file": "report.pdf",
     "page": 3,
     "chunk_index": 0,
     "mime_type": "image/png",
     "original_width": 1920,
     "original_height": 1080
   }
   ```
4. **Qwen3 + Qwen-VL 分工**：查询时若包含图像，用 Qwen-VL 先理解图像内容得到文本描述，再将描述作为 context 与检索块一起发给 Qwen3 生成最终答案
5. **三重复存储**：Qdrant（向量+检索用 payload）、SQLite（文档/chunk 元数据）、磁盘文件（data/documents/ 原始文件）

---

## 关键文件

| 文件 | 作用 |
|---|---|
| `multimodal-rag/docker-compose.yml` | 定义 qdrant + app 服务 |
| `multimodal-rag/app/config.py` | 环境变量加载（DASHSCOPE_API_KEY, QDRANT_URL） |
| `multimodal-rag/app/knowledge_base/manager.py` | 知识库元数据 CRUD（SQLite） |
| `multimodal-rag/app/knowledge_base/document_store.py` | 原始文件持久化存储 |
| `multimodal-rag/app/services/qdrant_service.py` | 向量存储核心操作 |
| `multimodal-rag/app/services/pipeline.py` | RAG 编排核心 |
| `multimodal-rag/app/services/embedding_service.py` | DashScope Embedding API |
| `multimodal-rag/app/services/llm_service.py` | Qwen3 LLM API |
| `multimodal-rag/app/services/vision_service.py` | Qwen-VL 视觉理解 API |
| `multimodal-rag/app/models/schemas.py` | API 请求/响应 Pydantic 模型 |

---

## 验证方式

1. 启动服务：`docker compose up -d`
2. 检查 Qdrant 健康：`GET /health`
3. 摄取测试：上传一张图 + 一个文本文件调用 `POST /ingest`，验证 Qdrant 中 points 数量增加
4. 文本查询测试：发送文本问题 `POST /query`，验证返回答案和引用块
5. 混合查询测试：发送图像 + 文本问题，验证 Qwen-VL 参与图像理解
6. 运行单元测试：`pytest tests/`