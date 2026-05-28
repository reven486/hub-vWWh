"""
RAG (Retrieval-Augmented Generation) 主模块

使用 LangChain v1 构建 RAG 系统，支持：
- 多种文档加载 (PDF, HTML, TXT, MD, CSV)
- Chroma/InMemory 向量存储
- 本地 Embedding 和 Rerank 模型
- 阿里云 DashScope LLM

模块结构：
- loaders.py: 文档加载
- embadding.py: Embedding 模型
- vectorstore.py: 向量存储 (Chroma/InMemory)
"""

import os
from pathlib import Path
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

# 项目内部模块
from config import settings, get_logger
from loaders import load_documents
from embadding import get_embeddings
from vectorstore import create_vector_store, load_vector_store

logger = get_logger(__name__)


# ==================== 全局变量 ====================

# LLM 实例（延迟初始化）
_llm: Optional[ChatOpenAI] = None

# Reranker 实例（延迟初始化）
_reranker: Optional[CrossEncoder] = None


# ==================== LLM 配置 ====================

def get_llm() -> ChatOpenAI:
    """获取或创建 LLM 实例"""
    global _llm

    if _llm is None:
        # 验证配置
        if not settings.dashscope_api_key:
            api_key = os.environ.get("DASHSCOPE_API_KEY")
            if api_key:
                settings.dashscope_api_key = api_key
            else:
                raise ValueError(
                    "请设置 DASHSCOPE_API_KEY 环境变量或配置 dashscope_api_key"
                )

        logger.info(f"初始化 LLM: model={settings.dashscope_model}")

        _llm = ChatOpenAI(
            model=settings.dashscope_model,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=settings.dashscope_api_key,
            temperature=0.0,
        )

    return _llm


def get_reranker() -> CrossEncoder:
    """获取或创建 Reranker 实例"""
    global _reranker

    if _reranker is None:
        rerank_model_path = settings.rerank_model

        if not rerank_model_path or not os.path.exists(rerank_model_path):
            raise ValueError(f"Rerank 模型路径无效: {rerank_model_path}")

        logger.info(f"初始化 Reranker: model={rerank_model_path}")

        _reranker = CrossEncoder(
            rerank_model_path,
            device="cpu",
            max_length=512,
        )

    return _reranker


# ==================== Rerank 函数 ====================

def rerank_documents(
    query: str,
    documents: List[Document],
    reranker: Optional[CrossEncoder] = None,
    top_n: Optional[int] = None,
) -> List[Document]:
    """
    使用本地 rerank 模型对文档重排序

    Args:
        query: 查询问题
        documents: 待排序的文档列表
        reranker: 本地 rerank 模型（可选，默认使用全局实例）
        top_n: 返回前 N 个最相关的文档

    Returns:
        重排序后的文档列表
    """
    if not documents:
        return []

    reranker = reranker or get_reranker()
    top_n = top_n or settings.rerank_top_n

    # 构造 query-document pairs
    pairs = [(query, doc.page_content) for doc in documents]

    # 获取相关性分数
    scores = reranker.predict(pairs)

    # 按分数降序排序
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    # 返回重排序后的文档
    reranked = [documents[i] for i in sorted_indices[:top_n]]
    return reranked


# ==================== RAG Chain ====================

def create_rag_chain(
    retriever,
    use_rerank: bool = True,
    rerank_top_n: Optional[int] = 3,
):
    """
    创建 RAG 问答链

    Args:
        retriever: 向量库检索器
        use_rerank: 是否启用 rerank（默认 True）
        rerank_top_n: rerank 后返回的文档数量

    Returns:
        RAG Chain (Runnable)
    """
    # 获取 effective top_n，避免在内部函数中修改外部变量
    effective_top_n = rerank_top_n if rerank_top_n is not None else settings.rerank_top_n

    def retrieve_and_rerank(query: str) -> List[Document]:
        """检索 + 重排序"""
        docs = retriever.invoke(query)

        if use_rerank and len(docs) > 1:
            docs = rerank_documents(query, docs, top_n=effective_top_n)

        return docs

    def format_docs(docs: List[Document]) -> str:
        """格式化检索到的文档"""
        return "\n\n".join(
            f"[来源 {i+1}] {doc.page_content}" for i, doc in enumerate(docs)
        )

    def combine_context(x: dict) -> str:
        """组合问题和上下文"""
        return (
            f"根据以下参考内容回答问题。如果参考内容中没有相关信息，请如实说明。\n\n"
            f"参考内容：\n{x['context']}\n\n"
            f"问题：{x['question']}"
        )

    # 构建 RAG Chain
    rag_chain = (
        {
            "context": lambda x: format_docs(retrieve_and_rerank(x)),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(combine_context)
        | get_llm()
        | StrOutputParser()
    )

    return rag_chain


# ==================== 主程序 ====================

def initialize_rag(
    docs_path: str = "./docs",
    force_recreate: bool = False,
) -> tuple:
    """
    初始化 RAG 系统

    Args:
        docs_path: 文档路径（文件或目录）
        force_recreate: 是否强制重新创建向量库

    Returns:
        (vectorstore, retriever, rag_chain)
    """
    logger.info("=" * 50)
    logger.info("RAG 系统初始化...")
    logger.info("=" * 50)

    # 1. 加载文档
    logger.info(f"加载文档: {docs_path}")
    try:
        docs = load_documents(docs_path)
        if not docs:
            logger.warning("未加载到任何文档，使用示例数据")
            docs = _get_sample_documents()
    except Exception as e:
        logger.warning(f"文档加载失败: {e}，使用示例数据")
        docs = _get_sample_documents()

    logger.info(f"文档加载完成: {len(docs)} 个文档块")

    # 2. 文本分割
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(docs)
    logger.info(f"文本分割完成: {len(chunks)} 个文本块")

    # 3. 获取 Embedding 模型
    embeddings = get_embeddings()
    logger.info("Embedding 模型加载完成")

    # 4. 创建或加载向量库
    vectorstore_path = Path(settings.vector_store_path)

    if force_recreate or not vectorstore_path.exists():
        logger.info(f"创建新的向量库: {settings.vector_store_type}")
        vectorstore = create_vector_store(
            documents=chunks,
            embeddings=embeddings,
            store_type=settings.vector_store_type,
        )
    else:
        logger.info(f"加载已有向量库: {settings.vector_store_type}")
        vectorstore = load_vector_store(
            persist_directory=str(vectorstore_path),
            embeddings=embeddings,
            store_type=settings.vector_store_type,
        )

    # 5. 创建检索器
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": settings.top_k},
        search_type="similarity"
    )
    logger.info("检索器创建完成")

    # 6. 创建 RAG Chain
    rag_chain = create_rag_chain(retriever, use_rerank=True)
    logger.info("RAG Chain 创建完成（Rerank 已启用）")

    logger.info("=" * 50)
    logger.info("RAG 系统初始化完成！")
    logger.info("=" * 50)

    return vectorstore, retriever, rag_chain


def _get_sample_documents() -> List[Document]:
    """获取示例文档（当没有真实文档时使用）"""
    return [
        Document(
            page_content="LangChain 是一个用于构建 LLM 应用的框架，它提供了丰富的组件和工具，包括模型调用、提示词模板、内存、索引等。",
            metadata={"source": "sample_langchain.txt"},
        ),
        Document(
            page_content="RAG (Retrieval-Augmented Generation) 是一种结合检索和生成的技术，可以提高 LLM 回答的准确性，减少幻觉。",
            metadata={"source": "sample_rag.txt"},
        ),
        Document(
            page_content="向量数据库用于存储文档的向量表示，便于快速相似性搜索。常见的向量数据库包括 Chroma、Milvus、Weaviate 等。",
            metadata={"source": "sample_vector_db.txt"},
        ),
        Document(
            page_content="BGE (BAAI General Embedding) 是一个开源的中英文文本嵌入模型，由 BAAI 开发，支持多种语言的文本向量化。",
            metadata={"source": "sample_bge.txt"},
        ),
    ]


# ==================== CLI 接口 ====================

def main():
    """CLI 主程序"""
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    # 初始化 RAG
    vectorstore, retriever, rag_chain = initialize_rag()

    # 问答测试
    questions = [
        "什么是 LangChain?",
        "RAG 是什么意思?",
        "向量数据库的作用是什么?",
        "BGE 模型有什么特点?",
    ]

    print("\n" + "=" * 50)
    print("开始问答测试：")
    print("=" * 50 + "\n")

    for q in questions:
        print(f"问题: {q}")
        print("-" * 40)
        try:
            answer = rag_chain.invoke(q)
            print(f"回答: {answer}")
        except Exception as e:
            print(f"回答失败: {e}")
        print()


if __name__ == "__main__":
    main()
