# local_qa.py
# 本地知识库问答 —— 文档检索 + LLM 回答

# 1. 导入必要模块（已全部调整好）
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# 2. 加载本地文档（根据你的文件路径修改）
loader = TextLoader("./docs/知识库.txt", encoding="utf-8")
documents = loader.load()

# 3. 文本分割
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
docs = text_splitter.split_documents(documents)

# 4. 构建向量存储（检索器）
#    注意：请替换为你自己的 DashScope API Key！
embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key="sk-c9b1982f0e674957ba9da72ce95922d6"
)
vectorstore = FAISS.from_documents(docs, embeddings)

# 5. 配置大语言模型（千问 Flash）
llm = ChatOpenAI(
    model="qwen-flash",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-c9b1982f0e674957ba9da72ce95922d6"
)

# 6. 创建检索问答链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

# 7. 提问并打印结果
query = "请根据文档内容回答：合同中的违约责任是如何规定的？"
result = qa_chain.invoke({"query": query})

print("=== 模型回答 ===")
print(result["result"])
print("\n=== 参考来源（文档片段） ===")
for i, doc in enumerate(result["source_documents"], 1):
    print(f"[来源 {i}] {doc.page_content[:200]}...")