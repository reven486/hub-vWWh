# langchain_rag/qa_chain.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_rag.vector_store import get_vector_store

def create_qa_chain(knowledge_id: int = None):
    llm = ChatOpenAI(
        model="qwen3.5-flash",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-03ac2881f43840dabf5573be9c2b907b",
        temperature=0.7,
        top_p=0.9
    )
    
    vector_store = get_vector_store(knowledge_id=knowledge_id)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    prompt_template = """现在的时间是{time}。你是一个专家，你擅长回答用户提问，帮我结合给定的资料，回答下面的问题。
如果问题无法从资料中获得，或无法从资料中进行回答，请回答无法回答。如果提问不符合逻辑，请回答无法回答。
如果问题可以从资料中获得，则请逐步回答。

资料：
{context}

问题：{question}
"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["time", "context", "question"]
    )
    
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough(), "time": lambda x: str(__import__("datetime").datetime.now())}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def query_with_rag(chain, question: str):
    result = chain.invoke(question)
    return {"answer": result, "sources": []}
