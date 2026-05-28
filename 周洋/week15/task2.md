# MinerU 使用方式总结

## MinerU 的本质

MinerU 是一个文档解析工具集，包含两种技术路线：

1. **MinerU-pipeline（传统流水线）** — 串联多个独立专用模型（布局检测、OCR、公式识别、表格识别），每个环节各用一个模型，不是视觉模型。
2. **MinerU2.5 VLM（视觉语言模型）** — 1.2B 参数的多模态模型，将流水线的多个步骤合并到一个模型中完成。输入 PDF 页面渲染图，直接输出结构化文本（Markdown/LaTeX/HTML）。

---

## MinerU 的三种使用方式

### 1️⃣ CLI 命令行工具（开源 Python 包）

```bash
# 默认 pipeline 模式
mineru -p file.pdf -o ./output

# VLM 模式（需额外部署模型服务）
mineru -p file.pdf -o ./output -b vlm-http-client
```

- 底层调用 `magic-pdf` Python 包
- `-b vlm-http-client` 指定 MinerU2.5 VLM 作为后端（对应论文中的模型）
- 默认模式走传统 pipeline，无需额外部署
- 详细用法在 GitHub README 中，官网文档未重点介绍

### 2️⃣ REST API（mineru.net 云服务）

| API 类型 | 是否需要 Token | 限制 |
|----------|---------------|------|
| **精准解析 API**（异步提交→轮询） | 需要 | 200MB / 200页 / 批量50文件 |
| **Agent 轻量 API**（异步提交→轮询） | 不需要（IP限流） | 10MB / 20页 |

- `POST /api/v4/extract/task` — 创建解析任务
- `GET /api/v4/extract/task/{task_id}` — 查询结果
- 官网文档主要介绍这部分

### 3️⃣ Python SDK 直接调用

```python
from magic_pdf.pipe import UNIPipe
# 直接导入使用，不经过 CLI
```

---

## 项目中实际使用的模式

文件 `offline_precess_worker.py` 中使用的是 **CLI 命令行工具** 的默认 pipeline 模式：

```python
subprocess.check_output(f"mineru -p {file_path} -o ./processed", shell=True)
```

注释中包含了切换 VLM 模式的选项：

```python
# subprocess.check_output(f"mineru -p {file_path} -o ./processed -b vlm-http-client")
```

---

---

# MinerU vs pdfplumber 对比

## pdfplumber 是什么

pdfplumber 是一个轻量级 PDF 文本提取库，基于 `pdfminer.six` 构建，专注于**从 PDF 中提取文本和表格**，不做版面分析、公式识别、图片提取。

---

## 两种工具对比

| 维度 | pdfplumber | MinerU |
|------|-----------|--------|
| **定位** | 轻量 PDF 文本/表格提取库 | 专业文档解析工具集 |
| **输出** | 纯文本、原始表格数据 | Markdown（含格式、图片路径、表格、公式） |
| **版面分析** | ❌ 无，按阅读顺序提取文本 | ✅ 完整布局检测（标题/页眉页脚/多栏/公式等） |
| **公式识别** | ❌ 不支持 | ✅ 支持（LaTeX 输出） |
| **表格识别** | ⚠️ `.extract_table()` 提取原始单元格 | ✅ 完整表格结构还原为 Markdown/HTML |
| **图片提取** | ❌ 不支持 | ✅ 提取并保存为图片文件 |
| **阅读顺序** | ❌ 按 PDF 内部流顺序 | ✅ 智能排序 |
| **旋转/复杂排版** | ❌ 容易乱 | ✅ 支持 |
| **模型依赖** | ❌ 无，纯规则解析 | ✅ 依赖深度学习模型（pipeline 或 VLM） |
| **速度** | ⚡ 极快（毫秒级） | 🐢 较慢（秒级，需 GPU 推理） |
| **安装体积** | 小 | 大（含模型权重） |
| **适合场景** | 快速提取文本、简单结构化 | 高精度文档解析、RAG 数据预处理 |

---

## 项目中 pdfplumber 的典型用法

### 1. 打开 PDF 并提取每页文本

```python
import pdfplumber

pdf = pdfplumber.open("document.pdf")
print("pages: ", len(pdf.pages))

for page in pdf.pages:
    text = page.extract_text()  # 提取纯文本
    # text = page.extract_text(layout=True)  # 保留布局的文本
```

### 2. 提取表格数据

```python
with pdfplumber.open("table.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()  # 返回列表嵌套列表
        for table in tables:
            for row in table:
                print(row)
```

---

## 对比总结

- **pdfplumber**：轻量、快速、无模型依赖，适合**简单 PDF 的纯文本提取**。缺点是无法处理复杂版面（多栏、公式、页眉页脚混排），输出不带格式。
- **MinerU**：重量级、精度高、带版面分析和格式还原，适合**复杂 PDF 的高精度解析**。输出 Markdown 可直接用于 RAG 的文档切块。

**在实际 RAG 项目中的选择建议：**
- PDF 内容以纯文本为主、排版简单的 → pdfplumber 足够
- PDF 包含公式、表格、复杂多栏排版、需要结构化输出的 → MinerU
- 也可以两者组合：先用 MinerU 做粗粒度解析，再用 pdfplumber 做某些字段的细粒度提取
