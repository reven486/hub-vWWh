本项目是一个多模态文档智能问答系统，基于包含图文混排的 PDF 知识库，能够回答涉及图像和文本的复合问题。

项目任务
多模态信息理解：同时理解用户问题和知识库中的图像、文本。
跨模态检索：从多个 PDF 中检索与查询相关的图像、图表、文本段落。
图文关联推理：关联并融合图文信息，进行逻辑推理。
答案生成：生成准确、简洁的答案，并指明信息来源（PDF 名称、页码、图表编号）。

技术栈
语言：Python
框架：FastAPI

模型：
- qwen-plus（LLM，openai库 API 调用，可配置）
- CLIP（本地，多模态检索）
- BGE（本地，文本编码）

文档解析：mineru（HTTP 调用）

中间件(可从配置文件中获取信息)：
- sqlite（元信息存储）
- milvus（向量存储与检索）
- kafka（异步任务队列，配置文件可配置）

核心 API
- POST /upload/document
    - 功能：向指定知识库上传文档(PDF\DOCX\TXT)

步骤：
获取文件信息
存储 PDF 文件(同时数据库保存，id、文件名、文件完成路径、处理状态) 
向 Kafka 待解析 topic 插入一条记录（kafka基础信息和topic 名称可配置）

- POST /chat
    - 功能：多模态问答

步骤：
获取用户提问 + 知识库 ID
对提问进行 embedding，分别检索文本（BGE + Milvus）和图像（CLIP + Milvus）
将检索到的图文内容排版后送给 qwen-plus 生成答案

后台 Worker
parse_document
功能：消费 Kafka 中的文档解析任务

步骤：
从 topic 获取文档 ID
调用 mineru HTTP 接口解析 PDF（注意：mineru 解析可能耗时较长，需考虑异步/超时处理）
对解析结果进行切分（chunk）
生成 embedding（文本用 BGE，图像用 CLIP）
存储向量到 Milvus，元信息到 sqlite


项目结构（解耦要求）
```
.
├── app/
│   ├── api/              # 路由层（upload, chat）
│   ├── core/             # 配置、异常定义
│   ├── doc/              # 文档保存位置
│   ├── models/           # Pydantic schemas
│   ├── services/         # 业务逻辑（检索、推理、解析编排等）
│   ├── workers/          # Kafka 消费 worker
│   └── db/               # Milvus/SQLite/Kafka 客户端封装
├── configs/              # 配置文件（模型路径、中间件地址等）
└── requirements.txt （暂时为空）

```
