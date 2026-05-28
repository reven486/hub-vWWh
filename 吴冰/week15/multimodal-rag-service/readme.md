# Multimodal RAG Service

基于 PDF 文档的多模态检索增强生成（RAG）系统。支持文本和图片的跨模态检索，并结合大语言模型生成带来源引用的回答。

## 需求概述

用户上传 PDF 文档后，系统自动解析文档内容（文本 + 图片），将其分割为语义块并提取多模态向量表示。用户提问时，系统通过多路检索从文档中找到相关的文本片段和图片，再交由大语言模型生成带来源的准确回答。

### 核心能力

- **PDF 解析**：使用 MinerU 将 PDF 转换为 Markdown + 图片
- **多模态向量编码**：BGE（文本语义）+ CLIP（图文联合表示）
- **跨模态检索**：文本查文本、文本查图片、文本查图文混合
- **LLM 回答生成**：基于检索结果生成带来源引用的回答
- **异步处理**：Kafka 消息队列解耦上传与解析流程

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | REST API 服务 |
| 文本编码 | BGE (BAAI/bge-small-zh-v1.5) | 512 维文本向量 |
| 图文编码 | CLIP (jinaai/jina-clip-v2) | 1024 维图文/图像向量 |
| 向量存储 | Milvus / Zilliz Cloud | 多向量字段检索 |
| PDF 解析 | MinerU | PDF → Markdown + 图片 |
| LLM | Qwen-plus (DashScope) | 回答生成 |
| 消息队列 | Kafka | 异步文档解析 |
| 元数据 | SQLite (SQLAlchemy) | 文件管理 |

## 架构

```
┌──────────┐     ┌──────────┐     ┌─────────────┐
│ 用户上传  │───▶│  FastAPI │───▶│   Kafka     │
│   PDF    │     │  (main)  │     │  (topic)    │
└──────────┘     └──────────┘     └──────┬──────┘
                                         │
                            ┌────────────▼────────────┐
                            │    parse_worker.py       │
                            │  MinerU → Chunk → Embed  │
                            └────────────┬────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   Milvus (向量库)    │
                              │  text_vector (512)   │
                              │  clip_text (1024)    │
                              │  clip_image (1024)   │
                              └─────────────────────┘

┌──────────┐     ┌──────────┐     ┌─────────────┐
│ 用户提问  │───▶│ /retrieve│───▶│  Milvus 检索│
│          │     │  /chat   │     │  LLM 生成回答│
└──────────┘     └──────────┘     └─────────────┘
```

### 三向量检索策略

每个文档块存储三个向量字段：

| 向量字段 | 编码器 | 维度 | 检索用途 |
|---------|--------|------|---------|
| `text_vector` | BGE | 512 | 文本查文本（精确语义匹配） |
| `clip_text_vector` | CLIP text | 1024 | 文本查图文混合（跨模态） |
| `clip_image_vector` | CLIP image | 1024 | 文本查图片（图像匹配） |

检索时根据 `modalities` 参数选择检索路径：
- `["text"]`：仅 BGE text_vector 检索文本片段
- `["image"]`：CLIP clip_image_vector + clip_text_vector 双路检索图片
- `["text", "image"]`：三路联合检索，结果去重合并

## 目录结构

```
multimodal-rag-service/
├── main.py                  # FastAPI 入口
├── config.py                # 配置（模型路径、Milvus、Kafka 等）
├── requirements.txt         # Python 依赖
├── api/
│   ├── document.py          # 文件上传/列表/删除/状态查询
│   ├── retrieval.py         # 多模态检索
│   └── chat.py              # 问答接口
├── services/
│   ├── embedder.py          # BGE + CLIP 编码
│   ├── vector_store.py      # Milvus 操作（建表/插入/检索/删除）
│   ├── chunker.py           # 文本分块
│   ├── pdf_parser.py        # MinerU 解析封装
│   └── qa_service.py        # LLM 回答生成
├── workers/
│   └── parse_worker.py      # Kafka 消费者（PDF 解析流水线）
├── orm/
│   ├── database.py          # SQLite 连接
│   └── models.py            # 文件表模型
├── schemas/
│   ├── document.py          # 文档请求/响应
│   ├── retrieval.py         # 检索请求/响应
│   └── chat.py              # 聊天请求/响应
├── uploads/                 # 原始 PDF 上传目录
├── processed/               # MinerU 解析输出目录
└── static/                  # 图片静态服务目录
```

## API 接口

### 健康检查

```
GET /health
```

### 文档管理

```
POST /api/v1/documents/upload     # 上传 PDF 文件
GET  /api/v1/documents/           # 列出所有文档
GET  /api/v1/documents/{id}/status # 查询解析状态
DELETE /api/v1/documents/{id}     # 删除文档
```

### 检索

```
POST /api/v1/retrieve/
{
  "query": "深度学习中的注意力机制是什么？",
  "modalities": ["text", "image"],
  "top_k": 5
}
```

返回文本片段和匹配图片的列表，包含来源文件和相似度分数。

### 问答

```
POST /api/v1/chat/
{
  "query": "解释 Transformer 的自注意力机制",
  "top_k": 5
}
```

返回 LLM 生成的回答及来源引用。

## 快速开始

### 环境要求

- Python 3.10+
- Kafka 服务（localhost:9092）
- MinerU 解析服务（localhost:30000）
- Milvus / Zilliz Cloud 连接

### 安装

```bash
cd multimodal-rag-service
pip install -r requirements.txt
```

### 启动 API 服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务启动时自动检查并创建 Milvus collection（如不存在）。

### 启动 Kafka 消费者

```bash
python workers/parse_worker.py
```

### 配置

所有配置在 `config.py` 中，可通过环境变量覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BGE_MODEL_PATH` | BAAI/bge-small-zh-v1.5 | BGE 模型路径 |
| `CLIP_MODEL_PATH` | jinaai/jina-clip-v2 | CLIP 模型路径 |
| `MINERU_SERVICE_URL` | http://127.0.0.1:30000 | MinerU 服务地址 |
| `LLM_API_KEY` | sk-xxx | DashScope API Key |
| `LLM_MODEL` | qwen-plus | LLM 模型名 |
| `HF_ENDPOINT` | https://hf-mirror.com | HuggingFace 镜像 |
