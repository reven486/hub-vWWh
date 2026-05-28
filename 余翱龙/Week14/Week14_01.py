# 安装依赖
# pip install langchain langchain-community faiss-cpu sentence-transformers pypdf

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# ===================== 1. 构建 RAG 检索工具 =====================
# 加载文档
loader = TextLoader("text.txt", encoding="utf-8")
docs = loader.load()

# 文本分块
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
splits = splitter.split_documents(docs)

# 向量库
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(splits, embedding)
retriever = vectorstore.as_retriever()

# 封装成 Agent 可用的工具
def retrieve_doc(query: str) -> str:
    """根据问题从文档中检索知识"""
    results = retriever.get_relevant_documents(query)
    return "\n".join([doc.page_content for doc in results])

# 定义工具列表
tools = [
    Tool(
        name="文档检索工具",
        func=retrieve_doc,
        description="当你需要从文档中查找知识时使用这个工具"
    )
]

# ===================== 2. 本地大模型（Ollama） =====================
llm = Ollama(model="qwen2.5:0.5b")

# ===================== 3. 使用 create_react_agent 构建 Agent =====================
# 官方标准提示词模板
prompt = PromptTemplate.from_template("""
根据下面的文档回答问题，不要编造信息。
你可以使用工具检索文档内容。

可用工具：
{tools}

问题：{input}
思考：{agent_scratchpad}
""")

# 创建 Agent（核心：create_react_agent）
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# 执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

# ===================== 4. 测试 =====================
if __name__ == "__main__":
    question = "你的问题"
    result = agent_executor.invoke({"input": question})
    print("\n===== 最终答案 =====")
    print(result["output"])