<p align="center">
  <h1 align="center">📚 Knowledge RAG Backend</h1>
  <p align="center">
    一个<b>能看懂、能跑起来、能学明白</b>的 RAG 实战项目
    <br>
    用一份清晰的代码，走完「PDF → 向量库 → 检索 → 生成 → 引用 → 评测」的完整闭环
  </p>
  <p align="center">
    <a href="README.md"><b>中文</b></a> | <a href="README_EN.md">English</a>
  </p>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="LangChain" src="https://img.shields.io/badge/LangChain%20%2B%20LangGraph-1C3C3C?logo=langchain&logoColor=white">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-Protocol-blueviolet">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

<p align="center">
  <a href="https://github.com/pengtao819/knowledge-rag-backend">
    <img alt="GitHub stars" src="https://badgen.net/github/stars/pengtao819/knowledge-rag-backend">
  </a>
  <a href="https://github.com/pengtao819/knowledge-rag-backend">
    <img alt="GitHub forks" src="https://badgen.net/github/forks/pengtao819/knowledge-rag-backend">
  </a>
</p>

---

## 为什么做这个项目

大语言模型有三个绕不开的硬伤：

| LLM 的硬伤 | 结果是 | 这个项目的解法 |
| --- | --- | --- |
| 知识有截止日期 | 训练之后发生的事它不知道 | 上传私有 PDF，由检索实时补充知识 |
| 无法访问私有数据 | 你的资料它一概不知 | 本地 Chroma 向量库，支持多知识库隔离 |
| 容易一本正经地编造（幻觉） | 答案不可信，不敢用 | 三层防幻觉 + 实测阈值，知识库外拒答率 100% |

它**不追求功能最全**，而是追求「你能读得懂、跑得起来、改得动」——这正是它和那些组件重重、代码量巨大的企业级项目最大的区别。

👉 **适合人群**：正在学 AI 应用开发、想找一个「完整但有迹可循」的 RAG 项目来读代码、跑通、再改造的同学。

---

## 目录

- [效果预览](#效果预览)
- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [和其它项目的区别](#和其它项目的区别)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [API 接口](#api-接口)
- [评测结果](#评测结果)
- [核心设计与踩坑](#核心设计与踩坑)
- [已知局限](#已知局限)
- [Roadmap](#roadmap)
- [目录结构](#目录结构)
- [贡献](#贡献)

---

## 效果预览

### Streamlit 前端 · RAG 模式（带引用来源）

![rag-mode](docs/streamlit-rag.png)

### Streamlit 前端 · Agent 模式（自主调用工具）

![agent-mode](docs/streamlit-agent.png)

### 接口演示：RAG 问答

![rag-chat](docs/rag-chat.png)

### 接口演示：Agent 问答

![agent-chat](docs/agent-chat.png)

### Docker 一键部署

![docker](docs/docker.png)

### MCP 工具动态加载

Agent 通过 MCP 协议，从独立的 MCP Server 动态加载工具，和代码里写死的本地工具混合调度。

![mcp](docs/mcp-load.png)

---

## 核心特性

- 📄 **PDF 文档处理** — 上传即解析，自动清洗、分块、向量化入库
- 🔍 **两阶段检索** — 向量召回 Top-20 粗筛 → Rerank 精排 Top-3，检索精度更高
- 🛡️ **三层防幻觉** — 检索阈值过滤 + Prompt 约束 + 引用编号，知识库外的问题稳定回「无法确定」
- 🤖 **LangGraph Agent** — LLM 通过 Function Calling 自主决定调用哪个工具，状态图编排、循环有上限
- 🔌 **MCP 协议接入** — 工具与 Agent 解耦，新增工具无需改动 Agent 代码
- 💬 **多轮对话** — 会话持久化 + 指代词改写（「它有什么作用」→「RAG 有什么作用」）
- ⚡ **流式输出** — SSE 逐字返回，提升首字响应体验
- 🗂️ **多知识库隔离** — 每个知识库独立 Chroma collection，互不干扰
- ⏱️ **工程化细节** — 全链路异步 + 超时 + 重试 + 分层异常处理
- 📊 **可量化评测** — 30 条测试问题、三轮迭代对比，不靠「感觉还行」
- 🐳 **Docker 一键部署** — `docker compose up --build`，API + MySQL + Chroma 一起拉起

---

## 技术栈

| 模块 | 技术 | 说明 |
| --- | --- | --- |
| Web 框架 | FastAPI | 全异步，自带 Swagger 文档 |
| AI 编排 | LangChain + LangGraph | 检索链 + Agent 状态图 |
| 大模型 | 通义千问（OpenAI 兼容） | `LLM_MODEL` 可配置，换任意 OpenAI 兼容模型 |
| Embedding | 阿里云百炼 | `qwen3.7-text-embedding-flash` |
| Rerank | 阿里云百炼 | `qwen3.7-text-rerank` |
| 向量数据库 | Chroma | 本地持久化，零额外服务 |
| 关系数据库 | MySQL + SQLAlchemy 2.0 | 异步 + aiomysql，存会话 |
| PDF 解析 | pdfplumber | 含中文清洗 + NFKC 规范化 |
| 重试机制 | tenacity | 指数退避 |
| 工具协议 | MCP | 工具与 Agent 解耦 |
| 容器化 | Docker + Compose | 一条命令起完整服务栈 |

---

## 和其它项目的区别

| 项目 | 定位 | 上手 / 读懂难度 |
| --- | --- | --- |
| **Knowledge RAG Backend** | 代码清晰、链路完整的 RAG **教学实战项目** | ✅ 低，结构简单、注释齐全 |
| LangChain-Chatchat | LangChain 生态的本地知识库问答 | 中，模块多 |
| RAGFlow | 企业级深度文档理解引擎 | 高，组件重、代码量巨大 |
| Dify | 低代码 LLM 应用平台 | 低，但核心是黑盒，学不到原理 |

一句话概括：**别的项目让你「用」RAG，这个项目让你「看懂并对它有了掌控感」**。它同时给出了一个写 RAG 项目时最容易缺失的东西——一套能复用的评测方法。

---

## 系统架构

```mermaid
flowchart LR
    U[用户 / Streamlit 前端] -->|HTTP| A["FastAPI 路由层<br/>/rag · /agent"]
    A --> S[Service 业务层]

    S --> R["rag_service<br/>检索 + 生成"]
    S --> Ag["agent_service<br/>LangGraph Agent"]
    S --> C["chat_service<br/>会话持久化"]

    R -->|向量检索 + Rerank| Ch[("Chroma 向量库")]
    R -->|Embedding / LLM / Rerank| D["阿里云百炼 API<br/>OpenAI 兼容"]
    Ag -->|动态加载工具| M["MCP Server<br/>FastMCP"]
    M --> Ch
    Ag --> D
    C --> DB[("MySQL<br/>对话持久化")]
```

---

## 快速开始

### 方式一：Docker 一键部署（推荐）

无需手动装 Python、MySQL，一条命令拉起完整服务栈。

```bash
git clone https://github.com/pengtao819/knowledge-rag-backend.git
cd knowledge-rag-backend

# 1. 配置环境变量
cp .env.example .env
#   编辑 .env，填入你的百炼 API Key 和 MySQL root 密码

# 2. 一键启动
docker compose up --build
```

启动后访问接口文档：<http://127.0.0.1:8000/docs>

### 方式二：本地开发

环境要求：Python 3.10+、MySQL 8.0+

```bash
# 1. 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建数据库
#    CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. 配置环境变量
cp .env.example .env   # 填入你的 API Key 和数据库连接串

# 5. 启动
uvicorn main:app --reload
```

需要的环境变量示例（`.env.example` 里有完整模板）：

```bash
# 阿里云百炼（Embedding + LLM + Rerank 共用同一个 Key）
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding-flash

# LLM（OpenAI 兼容接口，可换成任意兼容模型）
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.8-max-0902

# MySQL
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/rag_db?charset=utf8mb4

# Docker 部署时还需要
MYSQL_ROOT_PASSWORD=你的密码
```

> 💡 免费体验：可先在阿里云百炼控制台开通并领取新用户的免费额度，跑通整个项目不用花钱。

### 启动 Streamlit 前端（可选）

仓库自带一个 Streamlit 前端（`frontend/app.py`），提供图形界面进行文档上传、RAG / Agent 问答、知识库切换：

```bash
# 先保证后端已启动（Docker 或本地均可），再：
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

浏览器会自动打开 `http://localhost:8501`，前端默认连接 `http://localhost:8000` 的后端接口。

---

## API 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/rag/upload` | 上传 PDF，解析、分块、向量化入库 |
| POST | `/rag/chat` | RAG 问答（支持多轮对话） |
| POST | `/rag/chat/stream` | RAG 流式问答（SSE） |
| POST | `/agent/chat` | Agent 模式问答（LLM 自主决策调工具） |
| GET | `/rag/history/{conversation_id}` | 查询指定会话的历史消息 |
| GET | `/rag/conversations` | 查询会话列表 |
| GET | `/rag/collections` | 查询知识库列表 |

### 示例：RAG 问答

```bash
curl -X POST 'http://127.0.0.1:8000/rag/chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "什么是 RAG",
    "top_k": 3
  }'
```

响应（回答附引用编号，可追溯来源）：

```json
{
  "statusCode": 200,
  "question": "什么是 RAG",
  "answer": "RAG 是检索增强生成…… [1][2]",
  "sources": [
    { "index": 1, "source": "text.pdf", "page": 1, "chunk_index": 0, "preview": "……" }
  ]
}
```

**多轮对话**：第一次请求不传 `conversation_id`，响应后自行保存返回的会话 ID；后续请求带上它即可延续上下文：

```json
{ "question": "它有什么作用", "conversation_id": 9 }
```

系统会自动结合历史，理解「它」指代什么。

---

## 评测结果

> 「能证明自己好在哪里」是一个 RAG 项目最容易被忽略、也最有学习价值的部分。项目的完整实验记录见 [docs/experiment_log.md](docs/experiment_log.md)。

### 自建测试集（30 条，Happy-LLM 技术文档）

| 指标 | 数值 |
| --- | --- |
| 回答准确率 | 95.65% |
| 检索命中率 | 95.65% |
| 知识库外拒答率 | 100.00% |

### 公开测试集（100 条，CRUD-RAG 中文基准）

| 指标 | 数值 |
| --- | --- |
| 回答准确率 | 85.00% |
| 检索命中率 | 90.00% |

评估采用**严格 RAG 判定标准**（答案必须在检索上下文中找到支撑，否则算错）——相比只比关键字的「宽松评估」，更能反映系统真实能力。

---

## 核心设计与踩坑

下面是这个项目最值得学、也最「反直觉」的几个设计点。完整踩坑记录见 [docs/experiment_log.md](docs/experiment_log.md)。

### 1. 中文 PDF 里的「隐形坑」：NFKC 规范化

pdfplumber 提取中文时，会把「力」提取成康熙部首「⼒」——肉眼一样，计算机却当成两个字符，导致向量库里的文本和你的提问匹配不上。

**解法**：清洗环节加入 Unicode NFKC 规范化，一行代码修复：

```python
import unicodedata
text = unicodedata.normalize('NFKC', text)
```

### 2. 中文友好的分块

默认英文分隔符对中文效果差，改用自定义优先级：

```
["\n\n", "\n", "。", "！", "？", "；", "，", ". ", " ", ""]
```

块大小 500、重叠 100，中文检索质量显著提升。

### 3. 两阶段检索：先粗筛，再精排

- 向量检索召回 Top-20（快但不精确）
- 距离阈值过滤掉明显无关项
- Rerank 模型对 `(query, document)` 逐对打分，取 Top-3 给 LLM
- Rerank 失败时回退到原始顺序，保证可用性

### 4. 三层防幻觉

| 层级 | 措施 | 效果 |
| --- | --- | --- |
| 检索层 | 余弦距离阈值过滤（实测 0.65） | 不相关内容不进 LLM |
| Prompt 层 | 明确「没答案就说不知道」 | 约束 LLM 行为 |
| 输出层 | 引用编号对应真实来源 | 用户可核对 |

阈值不是拍脑袋——基于实测：有答案问题 distance ≤ 0.57，无答案问题 distance ≥ 0.76。

### 5. LangGraph Agent

用状态图编排 Agent，LLM 通过 Function Calling 自主决定调哪个工具：

```
START → agent_node ─┬→ tool_node → agent_node（循环，最多 8 次）
                    └→ END
```

- 本地工具：`retrieve_knowledge_base`（语义检索）、`list_documents`（列文档）
- MCP 工具：`list_documents`、`get_document_stats`（从独立 MCP Server 动态加载）
- 达到循环上限仍未结束时，兜底再调一次不带工具的 LLM 给出最终答案

### 6. MCP 工具与 Agent 解耦

传统做法把工具硬编码在 Agent 里，加新工具要改代码、重启服务。

改造后：工具封装成独立 MCP Server，通过 `langchain-mcp-adapters` 动态加载。以后加天气查询、数据库查询等能力，只需新增一个 MCP Server，Agent 端零改动。

### 7. 多知识库隔离

每个知识库对应一个独立的 Chroma collection，物理隔离：

- 用 `contextvar` 传递当前知识库名，请求开始 set、工具内部 get
- 不给工具函数加「知识库」参数——否则 LLM 会插手指向选择
- 前端通过 `GET /rag/collections` 拉取列表，侧边栏切换

### 8. 工程化：异步 + 超时 + 重试

- 全链路 `async/await`，同步阻塞库用 `run_in_threadpool` 隔离
- LLM 调用：tenacity 指数退避重试 3 次，单次超时 30 秒
- 整体请求：`asyncio.wait_for` 超时控制（RAG 180s / Agent 120s）

---

## 已知局限

如实说明，这些也是它的改进方向（👈 欢迎 PR）：

1. 代码类内容（代码块/参数默认值）检索较弱
2. multi_hop 跨章节问题检索可能不完整
3. MCP 工具固定访问默认知识库（MCP Server 是独立进程，`contextvar` 传不过去）
4. LLM 内部知识干扰（RAG 领域的开放难题）
5. 大文件处理偏慢；高并发场景未做压测

---

## Roadmap

- [ ] 按 AST / 代码块分块，改善代码类检索
- [ ] multi_hop 问题迭代检索（retrieve → read → retrieve again）
- [ ] MCP 工具支持多知识库切换
- [ ] 按问题类型动态设置 `max_tokens`
- [ ] 上传队列化，解决大文件慢的问题
- [ ] 单元测试 / 集成测试覆盖
- [ ] 前端接入流式输出（SSE），首字响应更快

---

## 目录结构

```
├── main.py                  # FastAPI 入口，lifespan 注册
├── config.py                # 配置管理（.env 加载）
├── requirements.txt
├── Dockerfile               # 镜像构建
├── docker-compose.yml       # 服务编排（API + MySQL）
├── .env.example             # 环境变量模板
├── app/
│   ├── api/                 # 路由层（rag_api / agent_api）
│   ├── services/            # 业务逻辑（rag / agent / chat / llm / mcp）
│   ├── db/                  # 数据库层
│   ├── core/                # 日志、异常
│   └── schemas/             # Pydantic 模型
├── frontend/
│   ├── app.py               # Streamlit 前端
│   └── requirements.txt     # 前端依赖
├── mcp_server/
│   └── server.py            # 独立 MCP Server（FastMCP 定义工具）
├── scripts/                 # 数据与评估脚本
├── data/                    # 测试集与知识库文本
├── results/                 # 评估报告输出
└── docs/                    # 截图 + 实验记录
```

---

## 贡献

这个项目欢迎，也很需要你的贡献——哪怕只是报告一个 Bug、补充一段注释。完整指引见 [CONTRIBUTING.md](CONTRIBUTING.md)。

简单步骤：

1. Fork 本仓库
2. 新建功能分支：`git checkout -b feature/xxx`
3. 提交改动：`git commit -m 'feat: xxx'`
4. 推送到远程并提 Pull Request

---

## License

[MIT License](LICENSE) © 2026

---

## 如果对你有帮助

如果这个项目帮你搞懂了 RAG，请点一个 ⭐ Star——这对一个面向学习者的开源项目是最大的鼓励，也会让更多和你一样的同学看到它。