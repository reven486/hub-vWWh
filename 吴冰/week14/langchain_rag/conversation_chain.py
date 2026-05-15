# langchain_rag/conversation_chain.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_rag.vector_store import get_vector_store

def create_conversational_rag_chain(knowledge_id: int = None):
    llm = ChatOpenAI(
        model="qwen3.5-flash",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-03ac2881f43840dabf5573be9c2b907b"
    )
    
    vector_store = get_vector_store(knowledge_id=knowledge_id)
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "现在的时间是{time}。你是一个专家，你擅长回答用户提问，帮我结合给定的资料，回答下面的问题。\n如果问题无法从资料中获得，请回答无法回答。\n\n资料：\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"],
            "time": lambda x: str(__import__("datetime").datetime.now())
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def chat_with_memory(chain, question: str, chat_history: list = None):
    history = chat_history or []
    result = chain.invoke({"question": question, "chat_history": history})
    return result
