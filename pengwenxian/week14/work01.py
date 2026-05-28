from collections import Counter
from pathlib import Path
import re

from langchain.messages import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI


model = ChatOpenAI(
    model="qwen-flash",  # 模型的代号
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-89beb5cc538544fc9ab0ad56bcf6f044",
)

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"


def ensure_demo_knowledge_base() -> None:
    """如果本地知识库为空，则自动创建几个最小演示文档。"""
    KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)
    if any(KNOWLEDGE_BASE_DIR.glob("*.*")):
        return

    demo_docs = {
        "langchain介绍.txt": (
            "LangChain 是一个用于开发 LLM 应用的框架，支持提示词管理、模型调用、"
            "文档加载、文本切分、检索和链式编排。"
        ),
        "rag介绍.txt": (
            "RAG 是 Retrieval-Augmented Generation 的缩写，核心流程是先检索文档，"
            "再把检索结果作为上下文交给大模型生成答案。"
        ),
        "项目说明.md": (
            "本示例演示本地知识库问答：先从 knowledge_base 目录读取文档，"
            "按块切分，再执行简单检索，最后由 LLM 基于检索结果回答。"
        ),
    }

    for file_name, content in demo_docs.items():
        (KNOWLEDGE_BASE_DIR / file_name).write_text(content, encoding="utf-8")


def load_local_documents() -> list[Document]:
    """读取 knowledge_base 目录下的 txt 和 md 文件。"""
    documents: list[Document] = []

    for file_path in KNOWLEDGE_BASE_DIR.rglob("*"):
        if file_path.suffix.lower() not in {".txt", ".md"}:
            continue

        text = file_path.read_text(encoding="utf-8")
        if not text.strip():
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={"source": str(file_path)},
            )
        )

    if not documents:
        raise ValueError("本地知识库为空，请先在 knowledge_base 目录中放入 txt 或 md 文档。")

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
    )
    return splitter.split_documents(documents)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text.lower())


def score_document(query: str, document: Document) -> float:
    """用最简单的关键词重合度做检索打分。"""
    query_counter = Counter(tokenize(query))
    doc_counter = Counter(tokenize(document.page_content))
    overlap = sum(min(query_counter[token], doc_counter[token]) for token in query_counter)
    return float(overlap)


def retrieve_documents(query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
    scored_docs = []
    for doc in documents:
        score = score_document(query, doc)
        if score > 0:
            scored_docs.append((score, doc))

    if not scored_docs:
        return documents[:top_k]

    scored_docs.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored_docs[:top_k]]


def format_context(documents: list[Document]) -> str:
    context_parts = []
    for index, doc in enumerate(documents, start=1):
        context_parts.append(
            f"资料{index}\n"
            f"来源: {doc.metadata['source']}\n"
            f"内容: {doc.page_content}"
        )
    return "\n\n".join(context_parts)


def ask_local_knowledge_base(question: str) -> str:
    raw_documents = load_local_documents()
    split_docs = split_documents(raw_documents)
    retrieved_docs = retrieve_documents(question, split_docs, top_k=3)
    context_text = format_context(retrieved_docs)

    messages = [
        SystemMessage(
            content=(
                "你是一个本地知识库问答助手。"
                "请优先根据提供的检索资料回答问题。"
                "如果资料里没有明确答案，就直接说明不知道，不要编造。"
            )
        ),
        HumanMessage(
            content=(
                f"用户问题：{question}\n\n"
                f"检索到的资料如下：\n{context_text}\n\n"
                "请基于这些资料给出简洁回答，并在最后列出参考来源。"
            )
        ),
    ]
    response = model.invoke(messages)
    return response.text()


if __name__ == "__main__":
    ensure_demo_knowledge_base()

    question = "什么是 RAG，它的基本流程是什么？"
    answer = ask_local_knowledge_base(question)

    print("问题：", question)
    print("回答：")
    print(answer)
