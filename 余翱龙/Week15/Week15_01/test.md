# 多模态RAG系统测试记录

## 环境信息
- Python环境: D:\python_code\extension\.venv\Scripts\python.exe
- 服务器启动命令: `D:/python_code/extension/.venv/Scripts/python.exe -m app.main`
- 测试文档: test.pdf

---

## 测试1: 上传文档

**命令:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" -F "file=@D:/python_code/extension/HomeWork/Week15/Week15_01/test.pdf"
```

**返回:**
```json
{"doc_id":"62c31b8e-090f-4d80-ab9b-ee3045d93268","doc_name":"test.pdf","status":"parsing","message":"Document uploaded successfully"}
```

---

## 测试2: 处理文档

**命令:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/62c31b8e-090f-4d80-ab9b-ee3045d93268/process"
```

**返回:**
```json
{"message":"Document processed successfully","doc_id":"62c31b8e-090f-4d80-ab9b-ee3045d93268"}
```

**文档状态查询:**
```bash
curl http://localhost:8000/api/v1/documents/62c31b8e-090f-4d80-ab9b-ee3045d93268
```
```json
{"doc_id":"62c31b8e-090f-4d80-ab9b-ee3045d93268","doc_name":"test.pdf","status":"completed","chunk_count":4,"image_count":4}
```

---

## 测试3: 纯检索接口

**命令:**
```bash
curl -X POST "http://localhost:8000/api/v1/retrieve" -H "Content-Type: application/json" -d "{\"query\":\"test\",\"top_k\":2}"
```

**返回:**
```json
{
  "results": [
    {
      "chunk_id": "d8c06e97-694c-40d1-8f47-f7e13766f46c",
      "type": "text",
      "doc_name": "test.pdf",
      "page": 0,
      "content": "非中文单词</td><td>4365</td></tr><tr><td>问题总数</td><td colspan=\"2\">5</td><td colspan=\"2\">万字差错率</td><td colspan=\"3\">0.90/10000</td><td>结论</td><td colspan=\"2\">合格</td></tr><tr><td>评阅机器人</td><td colspan=\"4\">001",
      "image_path": null
    },
    {
      "chunk_id": "96297158-1af4-4903-9d1d-42122c34b4bf",
      "type": "image",
      "doc_name": "test.pdf",
      "page": 1,
      "content": null,
      "image_path": "data/images\\62c31b8e-090f-4d80-ab9b-ee3045d93268_0_825e1c03e1196dd575dee5d67636fcb6de27c7404489622f3489af315eebcfc2.jpg"
    }
  ]
}
```

---

## 测试4: 问答接口

**命令:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d "{\"query\":\"test\",\"top_k\":2}"
```

**返回:**
```json
{
  "answer": "抱歉，没有找到相关信息来回答您的问题。您的输入"test"为测试指令，未包含具体问题。根据**页面0的文本**，当前检索内容仅包含某项文本审核或校对任务的统计字段（如非中文单词数4365、问题总数5、万字差错率0.90/10000，以及结论"合格"）。请提供与该内容相关的具体问题，我将为您详细解答。",
  "sources": [
    {
      "chunk_id": "d8c06e97-694c-40d1-8f47-f7e13766f46c",
      "type": "text",
      "doc_name": "test.pdf",
      "page": 0,
      "content": "非中文单词</td><td>4365</td></tr><tr><td>问题总数</td><td colspan=\"2\">5</td><td colspan=\"2\">万字差错率</td><td colspan=\"3\">0.90/10000</td><td>结论</td><td colspan=\"2\">合格</td></tr><tr><td>评阅机器人</td><td colspan=\"4\">001",
      "image_path": null
    },
    {
      "chunk_id": "96297158-1af4-4903-9d1d-42122c34b4bf",
      "type": "image",
      "doc_name": "test.pdf",
      "page": 1,
      "content": null,
      "image_path": "data/images\\62c31b8e-090f-4d80-ab9b-ee3045d93268_0_825e1c03e1196dd575dee5d67636fcb6de27c7404489622f3489af315eebcfc2.jpg"
    }
  ],
  "model_used": "qwen3-vl-32b"
}
```

---

## 测试5: 详细问答

**命令:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d "{\"query\":\"report result and error rate\",\"top_k\":3}"
```

**返回:**
```json
{
  "answer": "根据页面0的文本，报告的检测结果与差错率如下：\n- **报告结果（结论）**：合格\n- **差错率（万字差错率）**：0.90/10000",
  "sources": [
    {
      "chunk_id": "d8c06e97-694c-40d1-8f47-f7e13766f46c",
      "type": "text",
      "doc_name": "test.pdf",
      "page": 0,
      "content": "非中文单词</td><td>4365</td></tr><tr><td>问题总数</td><td colspan=\"2\">5</td><td colspan=\"2\">万字差错率</td><td colspan=\"3\">0.90/10000</td><td>结论</td><td colspan=\"2">合格</td></tr><tr><td>评阅机器人</td><td colspan=\"4\">001",
      "image_path": null
    },
    {
      "chunk_id": "96297158-1af4-4903-9d1d-42122c34b4bf",
      "type": "image",
      "doc_name": "test.pdf",
      "page": 1,
      "content": null,
      "image_path": "data/images\\62c31b8e-090f-4d80-ab9b-ee3045d93268_0_825e1c03e1196dd575dee5d67636fcb6de27c7404489622f3489af315eebcfc2.jpg"
    },
    {
      "chunk_id": "04bebfa7-8578-404f-8b96-c57405931c1e",
      "type": "text",
      "doc_name": "test.pdf",
      "page": 0,
      "content": "检测说明</td></tr><tr><td colspan=\"11\">1. 检测依据: 学校模板《中国民航大学硕士学位论文模板》; 国家标准《GB7713 学位论文编写格式》, 《GB7714 参考文献著录规则》, 《GB15834 标点符号用法》, 《GB15835 出版物上数字用法》, 《GB3100 国际单位制及其应用》, 《GB3101 有关量单位符号的一般原则》, 《GB3102 空间和",
      "image_path": null
    }
  ],
  "model_used": "qwen3-vl-32b"
}
```

---

## 总结

| 功能 | 状态 |
|------|------|
| PDF上传 | ✅ 正常 |
| MinerU解析 | ✅ 正常 |
| 内容切分 | ✅ 正常 (4个chunks, 4个images) |
| 向量化 | ✅ 正常 (BGE_DIM=2560) |
| FAISS存储 | ✅ 正常 |
| 检索 | ✅ 正常 |
| 问答生成 | ✅ 正常 (qwen3.6-flash) |
| 信息来源 | ✅ 正常 (doc_name, page) |