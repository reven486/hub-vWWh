本次作业完成以下内容，主要是对langchain，langgraph的学习以及练习

1:  基于学习的langchain 的框架，开发对本地知识库进行问答的逻辑，只需要包括文档检索 + llm回答流程(参考项目2)；

2: 定义一个skill，包含对股票的可视化功能，对于股票的周波动、日波动绘制在一个图中，并基于大小给出一个买入卖出的最佳时间建议；


### Skill介绍

> Skill: 虽然先前没有系统地了解过skill是什么, 但是已经使用过很多次了.
> 实际上, Skill 本质上就是教 AI 按固定流程做事的操作说明书，一旦写好，就能像函数一样反复调用。

此处介绍来自 [菜鸟教程](https://www.runoob.com/ai-agent/skills-agent.html) 

一个 Skill 本质上就是一个 Markdown 文件（文件名固定为 `SKILL.md`）

```bash
my-skill/
└── SKILL.md   （唯一必需）
```

基本模板:
```md
---
name: pdf-processing
description: 从 PDF 中提取文本和表格，填写表单，并合并文档
---

# PDF 处理

## 使用场景
当需要对 PDF 文件进行操作时使用，例如：

- 提取 PDF 文本或表格数据
- 填写 PDF 表单
- 合并多个 PDF 文件

## 提取文本
- 使用 `pdfplumber` 提取文本型 PDF 内容  
- 扫描版 PDF 需配合 OCR 工具  

## 填写表单
- 读取 PDF 表单字段  
- 按输入数据填充并生成新文件  
```

更复杂的SKILL文件组织:

```bash
my-skill/
├── SKILL.md      # 必需：指令 + 元数据
├── scripts/      # 可选：可执行代码
├── references/   # 可选：文档资料
└── assets/       # 可选：模板、资源
```

更进一步的, 对于复杂项目:

```bash
~/.claude/skills/react-component-review/
  ├── SKILL.md                  # 核心指令 + 元数据（建议控制在 400 行内）
  │
  ├── templates/                # 常用模板（Claude 按需读取）
  │   ├── functional.tsx.md
  │   └── class-component.md
  │
  ├── examples/                 # 优秀/反例（给 Claude 看标准）
  │   ├── good.md
  │   └── anti-pattern.md
  │
  ├── references/               # 规范、规则、禁用词表
  │   ├── hooks-rules.md
  │   └── naming-convention.md
  │
  └── scripts/                  # 可执行脚本（需开启 code execution）
      ├── validate-props.py
      └── check-cycle-deps.sh
```

### MCP介绍
> 同样来自菜鸟教程

MCP 的核心是 模型上下文，即 LLM 在运行过程中所需的所有外部信息和工具。

<img width="800" height="450" alt="image" src="https://github.com/user-attachments/assets/caf25530-fa51-4777-ad28-464657ca45b5" />

协议的关键部分是消息, 主要有以下三种:
1. 请求（Requests）
请求消息用于从客户端向服务器发起操作，或者从服务器向客户端发起操作。

请求消息的结构如下：
```bash
{
  "jsonrpc": "2.0",
  "id": "string | number",
  "method": "string",
  "params": {
    "[key: string]": "unknown"
  }
}
```
+ jsonrpc：协议版本，固定为"2.0"。
+ id：请求的唯一标识符，可以是字符串或数字。
+ method：要调用的方法名称，是一个字符串。
+ params：方法的参数，是一个可选的键值对对象，其中键是字符串，值可以是任意类型。
2. 响应（Responses）
响应消息是对请求的答复，从服务器发送到客户端，或者从客户端发送到服务器。

响应消息的结构如下：
```bash
{
  "jsonrpc": "2.0",
  "id": "string | number",
  "result": {
    "[key: string]": "unknown"
  },
  "error": {
    "code": "number",
    "message": "string",
    "data": "unknown"
  }
}
```
+ jsonrpc：协议版本，固定为"2.0"。
+ id：与请求中的id相对应，用于标识响应所对应的请求。
+ result：如果请求成功，result字段包含操作的结果，是一个键值对对象。
+ error：如果请求失败，error字段包含错误信息，其中：
+ code：错误代码，是一个数字。
+ message：错误描述，是一个字符串。
+ data：可选的附加错误信息，可以是任意类型。
3. 通知（Notifications）
通知消息是一种单向消息，不需要接收方回复。

通知消息的结构如下：
```bash
{
  "jsonrpc": "2.0",
  "method": "string",
  "params": {
    "[key: string]": "unknown"
  }
}
```
+ jsonrpc：协议版本，固定为"2.0"。
+ method：要调用的方法名称，是一个字符串。
+ params：方法的参数，是一个可选的键值对对象，其中键是字符串，值可以是任意类型。
4. 说明
+ 请求和响应：请求和响应是一对一的，客户端发送请求后，服务器会返回一个响应。id字段用于关联请求和响应。
+ 通知：通知是单向的，发送方不需要等待接收方的回复。通知通常用于事件推送或状态更新等场景。
+ 错误处理：如果请求失败，响应中会包含error字段，提供错误代码和描述，帮助开发者快速定位问题。


MCP 的关键特性
1. 标准化接口：定义统一的接口和协议，确保 LLM 与外部资源的兼容性。
2. 动态集成：支持 LLM 动态访问和集成外部数据源和工具。
3. 上下文感知：支持动态管理对话上下文，提升多轮对话的连贯性。
4. 开放性和可扩展性：支持第三方开发者为 LLM 应用扩展功能和资源。













