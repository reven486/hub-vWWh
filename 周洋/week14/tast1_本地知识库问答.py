"""
RAG 本地知识库问答
流程: 加载文档 → 分割 → 向量化存储 → 检索 → LLM 回答
"""

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ========== 1. 初始化模型和向量化 ==========
model = ChatOpenAI(
    model="qwen-flash",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-9c6195bf91f7435d88ea4b819073c92c"
)

embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key="sk-9c6195bf91f7435d88ea4b819073c92c",
)

# ========== 2. 加载本地文档 ==========
loader = DirectoryLoader(
    path="knowledge_base",
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
documents = loader.load()
print(f"共加载 {len(documents)} 个文档")

# ========== 3. 文档分割 ==========
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
chunks = text_splitter.split_documents(documents)
print(f"分割为 {len(chunks)} 个文本块")

# ========== 4. 创建向量库 ==========
vector_store = FAISS.from_documents(chunks, embeddings)

# ========== 5. 创建检索器 ==========
retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}  # 检索最相关的 3 个文本块
)

# ========== 6. 构建 RAG 问答链 ==========
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 helpful assistant。请基于以下检索到的上下文来回答问题。"
               "如果上下文中没有相关信息，就说你不知道，不要编造。\n\n"
               "上下文:\n{context}"),
    ("human", "{input}"),
])

combine_docs_chain = create_stuff_documents_chain(model, prompt)
rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

# ========== 7. 问答循环 ==========
print("\n知识库问答已启动（输入 q 退出）\n")

while True:
    question = input("问题: ")
    if question.lower() == "q":
        break

    result = rag_chain.invoke({"input": question})

    print(f"\n--- 检索到的相关片段 ---")
    for i, doc in enumerate(result["context"]):
        print(f"[{i+1}] {doc.page_content[:100]}...")
    print(f"\n回答: {result['answer']}\n")
