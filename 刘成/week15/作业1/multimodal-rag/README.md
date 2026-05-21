# Multimodal RAG System

基于 Qwen3 + Qwen-VL + DashScope + Qdrant 的多模态检索增强生成系统，支持图像+文本的混合检索与推理回答。

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM 生成 | Qwen3 API (DashScope) |
| 视觉理解 | Qwen-VL API |
| 多模态嵌入 | DashScope Embedding API |
| 向量数据库 | Qdrant |
| 框架 | FastAPI + LlamaIndex |

## 项目结构

```
multimodal-rag/
├── docker-compose.yml          # Qdrant + App 服务
├── .env.example                # 环境变量模板
├── Dockerfile.app              # App 容器化
├── pyproject.toml              # 依赖管理
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   │   ├── ingest.py           # POST /ingest, DELETE /documents/{id}
│   │   ├── query.py            # POST /query (含 SSE 流式)
│   │   ├── collection.py       # /collection/stats, /collection/reset
│   │   └── health.py           # GET /health
│   ├── services/
│   │   ├── embedding_service.py # DashScope 嵌入 API
│   │   ├── llm_service.py      # Qwen3 API
│   │   ├── vision_service.py   # Qwen-VL API
│   │   ├── qdrant_service.py   # 向量存储
│   │   └── pipeline.py         # RAG 编排
│   ├── models/
│   │   ├── schemas.py          # Pydantic 模型
│   │   └── document.py         # Document/Chunk 数据类
│   ├── ingestion/
│   │   ├── text_processor.py   # PDF/DOCX/TXT 提取
│   │   ├── image_processor.py  # 图像处理
│   │   └── chunker.py         # 文本分块
│   └── knowledge_base/
│       ├── manager.py          # SQLite CRUD
│       └── document_store.py   # 原始文件存储
├── data/                      # 文档和 Qdrant 存储
│   ├── documents/             # 原始文档
│   └── qdrant_storage/        # Qdrant 持久化
└── tests/                    # 单元测试
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY
```

### 2. 启动 Qdrant (Docker)

```bash
docker-compose up -d qdrant
```

### 3. 安装依赖

```bash
conda activate pyllm
pip install -e .
```

### 4. 运行服务

```bash
uvicorn app.main:app --reload
```

服务地址：http://localhost:8000

API 文档：http://localhost:8000/docs

## API 接口

### 文档摄取

```bash
# 上传文档 (PDF/DOCX/TXT/图片)
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@document.pdf"

# 列出所有文档
curl "http://localhost:8000/api/v1/ingest/documents"

# 删除文档
curl -X DELETE "http://localhost:8000/api/v1/ingest/documents/{doc_id}"
```

### 查询

```bash
# 文本查询
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "文档主要内容是什么？"}'

# 图像+文本混合查询 (base64)
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "这张图里有什么？", "query_image": "data:image/png;base64,..."}'
```

### 集合管理

```bash
# 查看集合统计
curl "http://localhost:8000/api/v1/collection/stats"

# 重置集合 (清空所有数据)
curl -X POST "http://localhost:8000/api/v1/collection/reset"
```

### 健康检查

```bash
curl "http://localhost:8000/api/v1/health"
```

## Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 测试

```bash
pytest tests/
```

## 数据存储

系统采用三重复存储设计：

1. **Qdrant** - 向量 + 检索用 payload
2. **SQLite** - 文档/chunk 元数据 (`data/metadata.db`)
3. **磁盘文件** - 原始文件 (`data/documents/{doc_id}/{filename}`)

## License

MIT
