# 知识库智能问答后端系统

基于 FastAPI + LangChain + LangGraph 的知识库智能问答后端系统，支持 PDF 上传解析、RAG 检索问答、Agent 自主工具调用、多轮对话与持久化。

## 项目背景

大语言模型存在三个硬伤：知识有截止日期、无法访问私有数据、容易产生幻觉。本系统通过 RAG（检索增强生成）技术，让 LLM 能够基于用户上传的私有文档回答问题，并附上引用来源，可追溯、可验证。

## 效果展示

### Streamlit 前端 - RAG 模式

![rag-mode](docs/streamlit-rag.png)

### Streamlit 前端 - Agent 模式（带引用来源）

![agent-mode](docs/streamlit-agent.png)

### Docker 一键部署

![docker](docs/docker.png)

## 核心功能

- **文档处理**：上传 PDF，自动解析、清洗、分块、向量化入库
- **RAG 问答**：语义检索 + 阈值过滤 + LLM 生成，回答带引用来源
- **流式输出**：SSE 流式返回回答，提升首字响应体验
- **防幻觉机制**：三层防护，知识库外的问题稳定返回"无法确定"
- **LangGraph Agent**：LLM 自主决策调用工具（知识库检索、文档列表查询）
- **多轮对话**：会话持久化 + 问题改写，支持指代词消解
- **异步架构**：全链路异步 + 超时 + 重试 + 全局异常处理
- **可观测性**：结构化日志 + 业务异常分层
- **Docker 一键部署**：`docker compose up --build` 启动 FastAPI + MySQL + Chroma 完整服务栈
- **RAG 评估体系**：30 条测试问题量化评估，回答准确率 95.65%，知识库外拒答率 100%

## 技术栈

| 模块       | 技术                                     |
| ---------- | ---------------------------------------- |
| Web 框架   | FastAPI（异步）                          |
| AI 编排    | LangChain、LangGraph                     |
| 大模型     | 通义千问 qwen3.8-max（OpenAI 兼容接口）  |
| Embedding  | 阿里云百炼 qwen3.7-text-embedding-flash  |
| 向量数据库 | Chroma（本地持久化）                     |
| 关系数据库 | MySQL + SQLAlchemy 2.0（异步）+ aiomysql |
| PDF 解析   | pdfplumber                              |
| 重试机制   | tenacity                                 |
| 日志       | Python logging + RotatingFileHandler     |
| 容器化     | Docker + Docker Compose                  |


## 系统架构


```
┌─────────────┐
│  用户请求    │
└──────┬──────┘
       │
   ┌───▼────────────────────────┐
   │   FastAPI 路由层            │
   │   /upload  /chat  /agent   │
   └───┬────────────────────────┘
       │
   ┌───▼────────────────────────┐
   │   Service 业务层            │
   │   ├─ rag_service (RAG)     │
   │   ├─ agent_service (Agent) │
   │   ├─ chat_service (持久化)  │
   │   └─ llm_client (LLM 封装)  │
   └───┬────────────────────────┘
       │
   ┌───▼──────┐  ┌──────────┐  ┌────────┐
   │  Chroma  │  │  MySQL   │  │  LLM   │
   │ 向量数据库 │  │  对话持久化│  │  百炼API│
   └──────────┘  └──────────┘  └────────┘
```

## 目录结构
```

├── main.py                       # FastAPI 入口，lifespan 注册
├── config.py                     # 配置管理（.env 加载）
├── requirements.txt
├── Dockerfile                    # 镜像构建
├── docker-compose.yml            # 服务编排（API + MySQL）
├── .dockerignore
├── .env.example                  # 环境变量模板
├── app/
│   ├── api/                      # 路由层
│   ├── services/                 # 业务逻辑
│   ├── db/                       # 数据库层
│   ├── core/                     # 日志、异常
│   └── schemas/                  # Pydantic 模型
├── scripts/                      # 数据与评估脚本
│   ├── extract_pdf_text.py       # 提取 PDF 全文
│   ├── diagnose_pdf.py           # 诊断 PDF 文本质量
│   ├── verify_eval_set.py        # 验证测试集 keywords
│   ├── run_evaluation.py         # 跑评估，算三项指标
│   └── show_badcases.py          # 展示错误案例
├── data/                         # 测试集与知识库文本
│   └── eval_questions.json       # 30 条测试问题
├── results/                      # 评估报告输出
│   └── eval_report.json
└── docs/                         # 文档
    └── experiment_log.md         # 实验记录

```

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd <project-dir>
```

### 3. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. 创建数据库

```sql
CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的配置：

```bash
cp .env.example .env
```

`.env` 内容示例：

```bash
# 阿里云百炼（Embedding + LLM 共用同一个 Key）
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding-flash

# LLM
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.8-max-0902

# MySQL
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/rag_db?charset=utf8mb4

# 分块参数
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# Chroma
CHROMA_COLLECTION=knowledge_base
```

### 6. Docker 部署（推荐）
确保 Docker Desktop 已启动，然后：
```bash
docker compose up --build
```

### 7. 本地开发（可选）
```bash
uvicorn main:app --reload
```

启动后访问：
- 接口文档：http://127.0.0.1:8000/docs

## API 接口

| 方法 | 路径                            | 说明                                 |
| ---- |-------------------------------| ------------------------------------ |
| POST | `/rag/upload`                 | 上传 PDF，解析、分块、向量化入库     |
| POST | `/rag/chat`                   | RAG 问答（支持多轮对话）             |
| POST | `/rag/chat/stream`            | RAG 流式问答（SSE）                  |
| POST | `/agent/chat`                 | Agent 模式问答（LLM 自主决策调工具） |
| GET  | `/rag/history/{conversation_id}` | 查询指定会话历史消息                 |
| GET  | `/rag/conversations`          | 查询会话列表                         |

### 示例：RAG 问答

**请求**

```bash
curl -X POST 'http://127.0.0.1:8000/rag/chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "什么是RAG",
    "top_k": 3
  }'
```

**响应**

```json
{
  "statusCode": 200,
  "question": "什么是RAG",
  "answer": "RAG 是检索增强生成... [1][2]",
  "sources": [
    {
      "index": 1,
      "source": "text.pdf",
      "page": 1,
      "chunk_index": 0,
      "preview": "..."
    }
  ]
}
```

**多轮对话**：第一次请求返回 `conversation_id`，后续请求带上它即可延续对话：

```json
{
  "question": "它有什么作用",
  "conversation_id": 9
}
```

系统会自动结合历史理解"它"指的是什么。

## 关键技术点

### 1. PDF 文本清洗

pdfplumber 提取的文本存在两类问题：

- 中文行内换行导致句子断裂
- 中英文边界缺少空格

通过正则清洗：删除中文行内换行、保留段落换行、中英文边界补空格。

### 2. 中文友好的分块

使用 `RecursiveCharacterTextSplitter` + 自定义分隔符优先级：

```
["\n\n", "\n", "。", "！", "？", "；", "，", ". ", " ", ""]
```

块大小 500 字符，重叠 100 字符。相比默认英文分隔符，中文检索质量显著提升。

### 3. 三层防幻觉机制

| 层级      | 措施                          | 效果               |
| --------- | ----------------------------- | ------------------ |
| 检索层    | 余弦距离阈值过滤（实测 0.65） | 不相关内容不进 LLM |
| Prompt 层 | 明确要求"没答案就说不知道"    | 约束 LLM 行为      |
| 输出层    | 引用编号对应真实来源          | 用户可核对         |

阈值基于实测：有答案问题 distance ≤ 0.57，无答案问题 distance ≥ 0.76。

### 4. 多轮对话的问题改写

用户第二句常带指代词（"它"、"这个"）。直接向量化无实体语义，检索失败。系统先让 LLM 结合历史改写问题：

```
"它有什么作用" → "RAG有什么作用"
```

用改写后的问题检索，命中率明显提升。

### 5. LangGraph Agent

用状态图编排 Agent 流程：

```
START → agent_node ─┬→ tool_node → agent_node（循环）
                    └→ END
```

- LLM 通过 Function Calling 自主决定调用哪个工具
- 条件边根据 LLM 输出决定循环还是结束
- 最大循环次数保护，防止死循环

集成工具：
- `retrieve_knowledge_base`：语义检索
- `list_documents`：列出所有文档

支持多轮对话：历史消息会注入到 Agent 的消息列表，结合上下文理解指代词。

### 6. 异步 + 超时 + 重试

- 全链路 `async/await`，同步阻塞库用 `run_in_threadpool` 隔离
- 单次 LLM 调用：tenacity 指数退避重试 3 次，超时 30 秒
- 整体请求：`asyncio.wait_for` 超时控制（RAG 60s / Agent 120s）

### 7. 分层错误处理

- `AppError` 业务异常基类，子类自带 HTTP 状态码
- 全局异常处理器统一捕获，业务异常记 WARNING，未知异常记 ERROR + 完整堆栈
- 不向前端暴露内部堆栈，避免信息泄露

### 8. RAG 评估体系

构造 30 条测试问题，覆盖四类场景，量化评估系统表现：

| 类别 | 数量 | 目的 |
|---|---|---|
| simple_fact | 15 | 单一事实查询 |
| comparison | 5 | 对比类问题 |
| multi_hop | 5 | 跨章节综合 |
| out_of_scope | 5 | 测试拒答能力 |

三项指标：**回答准确率 95.65%、检索命中率 95.65%、知识库外拒答率 100%**。

完整实验记录见 [docs/experiment_log.md](docs/experiment_log.md)，包含三轮迭代对比、4 条错误案例分析、4 条踩坑记录。

### 9. PDF 提取的 CJK 字符规范化

pdfplumber 提取中文时会把标准汉字转成"康熙部首"异体字（如"力" → "⼒"），肉眼一样但计算机认为是不同字符，导致向量库里的文本和用户查询匹配不上。

解决方案：清洗环节加入 Unicode NFKC 规范化：

```python
import unicodedata
text = unicodedata.normalize('NFKC', text)
```
修复后重新分块，chunk 数从 626 变成 594，中文关键词匹配率从 60% 提升到 100%。

## 评估结果

在 Happy-LLM 技术文档（171 页，594 chunks）上构造 30 条测试问题，覆盖单一事实、对比、跨章节综合、知识库外四类场景。

| 指标 | 数值 |
|---|---|
| 回答准确率 | 95.65% |
| 检索命中率 | 95.65% |
| 知识库外拒答率 | 100.00% |

详细的评估方法、三轮迭代对比、错误案例分析与踩坑记录见 [docs/experiment_log.md](docs/experiment_log.md)。




## 项目亮点

- **完整的 RAG 链路**：从 PDF 解析到向量化、检索、生成、引用的闭环
- **可量化的防幻觉**：基于实测 distance 分布定阈值，不是拍脑袋
- **多轮对话**：问题改写 + 历史上下文，真正支持连续对话
- **Agent 能力**：不只是固定 RAG 链路，LLM 能自主选择工具
- **生产级考量**：异步、超时、重试、日志、异常处理，接近线上项目
- **可量化的成果**：30 条测试问题、三项量化指标、三轮迭代对比，不靠"感觉还行"

## 后续规划

- [x] Docker 部署
- [x] RAG 评估体系
- [ ] Streamlit 前端（可在线 Demo）
- [ ] 检索重排序（Rerank）
- [ ] 多 Agent 协作
- [ ] MCP 协议接入
