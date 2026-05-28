from fastapi import FastAPI, HTTPException
from schema import ChatRequest, ChatResponse
import time

# 初始化 FastAPI 应用
app = FastAPI(title="多模态 RAG Chatbot API")


# --- 模拟功能函数 (Mock) ---

def mock_retrieve_context(query: str, image_url: str):
    """模拟向量数据库检索"""
    print(f"🔍 正在检索: {query}")
    time.sleep(1)  # 模拟网络延迟
    return [
        "图表显示2019年伊利和蒙牛占据了市场主导地位。",
        "图片中的数据来源标注为 Euromonitor。"
    ]


def mock_call_llm(query: str, context: list):
    """模拟大模型生成回答"""
    print("🤖 正在生成回答...")
    time.sleep(1.5)
    return f"根据检索到的信息，针对您的问题“{query}”，答案是：图表显示伊利和蒙牛占据主导地位。"


# --- API 接口 ---

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. 检索
        context = mock_retrieve_context(request.user_query, request.image_url)
        # 2. 生成
        answer = mock_call_llm(request.user_query, context)

        return ChatResponse(answer=answer, sources=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"status": "running", "message": "API is ready."}


# ==========================================
# 下面是新增的网页界面代码 (Frontend)
# ==========================================
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# 创建一个简单的 HTML 页面
html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>多模态 RAG 聊天机器人</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            input, button { padding: 10px; margin: 5px; width: 100%; box-sizing: border-box; }
            #response { margin-top: 20px; padding: 10px; border: 1px solid #ccc; min-height: 50px; }
        </style>
    </head>
    <body>
        <h1>🤖 多模态 RAG 聊天机器人</h1>
        <input id="query" type="text" placeholder="请输入你的问题..." />
        <input id="image" type="text" placeholder="请输入图片 URL (可选)..." />
        <button onclick="sendQuery()">发送</button>
        <div id="response">等待回复...</div>

        <script>
            async function sendQuery() {
                const query = document.getElementById('query').value;
                const image = document.getElementById('image').value;
                const responseDiv = document.getElementById('response');

                responseDiv.innerText = "正在思考...";

                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_query: query, image_url: image })
                });
                const data = await res.json();
                responseDiv.innerText = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    return html_content