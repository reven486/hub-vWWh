import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


def load_and_split_docs(docs_dir: str) -> list:
    """从目录加载 .txt 文档并切分为小块"""
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    print(f"[文档加载] 共加载 {len(docs)} 个文档")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "，", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"[文档切分] 共切分为 {len(chunks)} 个文本块")
    return chunks


def _get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vector_store(chunks: list, persist_dir: str) -> Chroma:
    """将文本块向量化并存入 Chroma"""
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=_get_embeddings(),
        persist_directory=persist_dir,
    )
    print(f"[向量存储] 已存入 Chroma，路径: {persist_dir}")
    return vectorstore


def load_vector_store(persist_dir: str) -> Chroma:
    """从已有 Chroma 目录加载向量库"""
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=_get_embeddings(),
    )
    print(f"[向量存储] 已加载已有向量库，路径: {persist_dir}")
    return vectorstore


def _format_docs(docs):
    """将检索到的文档列表拼接为纯文本"""
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(vectorstore: Chroma):
    """
    用 LCEL 构建 RAG 链：
      {"context": retriever | format, "input": passthrough}
        → prompt → llm → output_parser
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    llm = ChatOpenAI(
        model="qwen-flash",  # 模型的代号
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-xx
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个知识库问答助手。请根据以下检索到的上下文内容回答用户问题。\n"
            "如果上下文中没有相关信息，请回答：根据知识库中的信息，无法回答该问题。\n"
            "请用中文回答，并尽量引用上下文中的原文。\n\n"
            "上下文：\n{context}"
        )),
        ("human", "{input}"),
    ])

    rag_chain = (
        {
            "context": retriever | _format_docs,
            "input": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain, retriever


def main():
    if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
        print("[初始化] 检测到已有向量库，直接加载")
        vectorstore = load_vector_store(CHROMA_PERSIST_DIR)
    else:
        print("[初始化] 未检测到向量库，开始构建")
        chunks = load_and_split_docs(KNOWLEDGE_BASE_DIR)
        vectorstore = build_vector_store(chunks, CHROMA_PERSIST_DIR)

    rag_chain, retriever = build_rag_chain(vectorstore)
    print("[RAG 链] 构建完成\n")

    print("本地知识库问答系统")

    query = input("\n请输入问题: ").strip()


    # 先检索，展示来源
    retrieved_docs = retriever.invoke(query)
    print("\n--- 检索来源 ---")
    for i, doc in enumerate(retrieved_docs, 1):
        source = doc.metadata.get("source", "unknown")
        print(f"  [{i}] {os.path.basename(source)} | {doc.page_content[:80]}...")

    # LLM 生成回答
    answer = rag_chain.invoke(query)
    print(f"\n回答: {answer}")


if __name__ == "__main__":
    main()
