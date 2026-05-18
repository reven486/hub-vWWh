"""知识库问答：基于 FAISS 检索 + 通义千问生成回答。

运行前请先执行 `python ingest.py` 构建向量库。
"""
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

VECTOR_STORE_DIR = Path(__file__).parent / "vector_store"

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个严谨的知识库问答助手。请只依据下面提供的上下文回答问题。"
        "如果上下文不足以回答，直接回答“我不知道”，不要编造。"
        "回答使用中文，简洁准确。\n\n"
        "上下文：\n{context}",
    ),
    ("human", "{question}"),
])


def format_docs(docs) -> str:
    return "\n\n".join(
        f"[来源: {d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs
    )


def build_chain(top_k: int = 4):
    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            f"未找到向量库 {VECTOR_STORE_DIR}，请先运行 `python ingest.py`"
        )

    embeddings = DashScopeEmbeddings(model="text-embedding-v3")

    # FAISS 的 C++ I/O 在 Windows 上不支持非 ASCII 路径，先把索引复制到临时 ASCII 目录再加载。
    with tempfile.TemporaryDirectory(prefix="faiss_") as tmp:
        for f in VECTOR_STORE_DIR.iterdir():
            shutil.copy2(str(f), str(Path(tmp) / f.name))
        vector_store = FAISS.load_local(
            tmp,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    llm = ChatTongyi(model="qwen-plus", temperature=0)

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )


def main():
    chain = build_chain()
    print("知识库问答已就绪，输入问题（空行退出）：")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            break
        answer = chain.invoke(question)
        print(f"\n{answer}")


if __name__ == "__main__":
    main()
