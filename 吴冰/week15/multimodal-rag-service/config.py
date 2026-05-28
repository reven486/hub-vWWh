import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 文件存储路径
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# SQLite 数据库
DB_PATH = os.path.join(BASE_DIR, "db.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Milvus / Zilliz Cloud
MILVUS_URI = "https://in03-5cb3b56f3af9ebc.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn"
MILVUS_TOKEN = "9027d285f74e5ce113bf24162fc5cabe04b67db3ee25055f4748ea23785f00d0fa9b8217c108a04dc77c4a703b5860a7d39d7a7b"
COLLECTION_NAME = "rag_data_new"

# Kafka
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "rag-data"

# BGE 文本编码模型
BGE_MODEL_PATH = os.environ.get("BGE_MODEL_PATH", "BAAI/bge-small-zh-v1.5")
BGE_DIM = 512

# CLIP 图文编码模型
CLIP_MODEL_PATH = os.environ.get("CLIP_MODEL_PATH", "jinaai/jina-clip-v2")
CLIP_DIM = 1024

# MinerU 解析服务地址
MINERU_SERVICE_URL = os.environ.get("MINERU_SERVICE_URL", "http://127.0.0.1:30000")
MINERU_TIMEOUT = 600

# LLM（OpenAI 兼容 API）
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-711c186f74494136ba26035be25a7cb8")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")

# 检索参数
DEFAULT_TOP_K = 5
CHUNK_SIZE = 256

# HuggingFace 镜像
os.environ["HF_ENDPOINT"] = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
