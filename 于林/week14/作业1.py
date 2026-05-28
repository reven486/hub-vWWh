class RAG:
    def __init__(self):
        self.embedding_model = config["rag"]["embedding_model"]
        self.rerank_model = config["rag"]["rerank_model"]

        self.use_rerank = config["rag"]["use_rerank"]

        self.embedding_dims = config["models"]["embedding_model"][
            config["rag"]["embedding_model"]
        ]["dims"]

        self.chunk_size = config["rag"]["chunk_size"]
        self.chunk_overlap = config["rag"]["chunk_overlap"]
        self.chunk_candidate = config["rag"]["chunk_candidate"]

        self.client = OpenAI(
            api_key=config["rag"]["llm_api_key"],
            base_url=config["rag"]["llm_base"]
        )
        self.llm_model = config["rag"]["llm_model"]
        self.llm = ChatOpenAI(
            model="qwen-flash",  # 模型的代号
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="sk-4fedee4ece6541d3b17a7173f0b3c16f"
        )
    # def chat(self, messages: List[Dict], top_p: float, temperature: float) -> Any:
    #     completion = self.client.chat.completions.create(
    #         model=self.llm_model,
    #         messages=messages,
    #         top_p=top_p,
    #         temperature=temperature
    #     )
    #     return completion.choices[0].message
    # 将上面函数改写成

    def chat(self, messages: List[Dict], top_p: float, temperature: float) -> Any:
        llm = self.llm.bind(top_p=top_p, temperature=temperature)
        return llm.invoke(messages)
