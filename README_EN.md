<p align="center">
  <h1 align="center">📚 Knowledge RAG Backend</h1>
  <p align="center">
    A RAG project you can <b>read, run, and actually understand</b>
    <br>
    One clean codebase that walks through the whole pipeline: PDF → vector store → retrieve → generate → cite → evaluate
  </p>
  <p align="center">
    <a href="README.md">中文</a> | <a href="README_EN.md"><b>English</b></a>
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

## Why this project

Large language models have three inescapable weaknesses:

| LLM weakness | Consequence | How this project solves it |
| --- | --- | --- |
| Knowledge cutoff | It doesn't know what happened after training | Upload private PDFs, retrieval adds the missing knowledge |
| No access to private data | It knows nothing about your documents | Local Chroma vector store with multi-knowledge-base isolation |
| Confident hallucination | Answers can't be trusted | Three-layer anti-hallucination + measured thresholds → 100% out-of-scope refusal |

It does **not** aim to have every feature. It aims to be something you can **read, run, and modify** — which is exactly what sets it apart from heavyweight enterprise projects with overwhelming codebases.

👉 **Who it's for**: students and developers learning AI application development, who want a *complete but traceable* RAG project to read, run, and extend.

---

## Table of contents

- [Demo](#demo)
- [Core features](#core-features)
- [Tech stack](#tech-stack)
- [How it differs from other projects](#how-it-differs-from-other-projects)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [API](#api)
- [Evaluation results](#evaluation-results)
- [Key design decisions](#key-design-decisions)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Project structure](#project-structure)
- [Contributing](#contributing)

---

## Demo

### Streamlit frontend · RAG mode (with citations)

![rag-mode](docs/streamlit-rag.png)

### Streamlit frontend · Agent mode (autonomous tool calling)

![agent-mode](docs/streamlit-agent.png)

### Interface demo: RAG chat

![rag-chat](docs/rag-chat.png)

### Interface demo: Agent chat

![agent-chat](docs/agent-chat.png)

### One-command deployment

![docker](docs/docker.png)

### Dynamic MCP tool loading

The Agent dynamically loads tools from a standalone MCP Server over the MCP protocol, mixing them with locally defined tools.

![mcp](docs/mcp-load.png)

---

## Core features

- 📄 **PDF processing** — upload → parse → clean → chunk → embed
- 🔍 **Two-stage retrieval** — vector recall top-20 → rerank top-3 for better precision
- 🛡️ **Three-layer anti-hallucination** — distance filter + prompt constraint + citations; out-of-scope questions reliably get "I don't know"
- 🤖 **LangGraph Agent** — the LLM autonomously chooses tools via function calling, with a bounded state-graph loop
- 🔌 **MCP integration** — tools are decoupled from the Agent; add new tools without touching the Agent code
- 💬 **Multi-turn dialogue** — persistent sessions + pronoun resolution ("What does it do?" → "What does RAG do?")
- ⚡ **Streaming output** — SSE token-by-token responses
- 🗂️ **Multi-knowledge-base isolation** — one Chroma collection per knowledge base
- ⏱️ **Engineering details** — full async, timeouts, retries, layered error handling
- 📊 **Measurable evaluation** — 30 test questions, three iterations, real numbers
- 🐳 **One-command Docker deploy** — `docker compose up --build`

---

## Tech stack

| Area | Technology | Notes |
| --- | --- | --- |
| Web framework | FastAPI | Fully async, built-in Swagger |
| AI orchestration | LangChain + LangGraph | Retrieval chain + Agent state graph |
| LLM | Qwen (OpenAI-compatible) | `LLM_MODEL` is configurable — swap in any OpenAI-compatible model |
| Embedding | Alibaba Cloud (DashScope) | `qwen3.7-text-embedding-flash` |
| Rerank | Alibaba Cloud (DashScope) | `qwen3.7-text-rerank` |
| Vector store | Chroma | Local persistence, zero extra services |
| Relational DB | MySQL + SQLAlchemy 2.0 | Async + aiomysql, stores conversations |
| PDF parsing | pdfplumber | Includes Chinese text cleaning + NFKC normalization |
| Retries | tenacity | Exponential backoff |
| Tool protocol | MCP | Tools decoupled from the Agent |
| Containerization | Docker + Compose | Full stack in one command |

---

## How it differs from other projects

| Project | Positioning | Ease of reading / running |
| --- | --- | --- |
| **Knowledge RAG Backend** | A clean, complete RAG **teaching project** | ✅ Low — simple structure, well-commented |
| LangChain-Chatchat | Local KB chat based on the LangChain ecosystem | Medium |
| RAGFlow | Enterprise-grade deep document understanding | High — heavy components, huge codebase |
| Dify | Low-code LLM app platform | Low, but the core is a black box |

In one sentence: **other projects let you *use* RAG; this one lets you *understand* RAG.** It also gives you something most RAG demos lack — a reusable evaluation methodology.

---

## Architecture

```mermaid
flowchart LR
    U[User / Streamlit frontend] -->|HTTP| A["FastAPI routing layer<br/>/rag · /agent"]
    A --> S[Service layer]

    S --> R["rag_service<br/>retrieve + generate"]
    S --> Ag["agent_service<br/>LangGraph Agent"]
    S --> C["chat_service<br/>session persistence"]

    R -->|vector search + rerank| Ch[("Chroma vector store")]
    R -->|Embedding / LLM / Rerank| D["DashScope API<br/>OpenAI-compatible"]
    Ag -->|dynamic tool loading| M["MCP Server<br/>FastMCP"]
    M --> Ch
    Ag --> D
    C --> DB[("MySQL<br/>conversation persistence")]
```

---

## Quick start

### Option 1: Docker (recommended)

No need to install Python or MySQL manually — one command brings up the whole stack.

```bash
git clone https://github.com/pengtao819/knowledge-rag-backend.git
cd knowledge-rag-backend

# 1. Configure environment variables
cp .env.example .env
#    Edit .env with your DashScope API key and MySQL root password

# 2. Build and run
docker compose up --build
```

Then open the API docs at <http://127.0.0.1:8000/docs>.

### Option 2: Local development

Requirements: Python 3.10+, MySQL 8.0+

```bash
# 1. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database
#    CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. Configure environment variables
cp .env.example .env   # fill in your API key and DB connection string

# 5. Run
uvicorn main:app --reload
```

Environment variables (a complete template lives in `.env.example`):

```bash
# DashScope (one key shared by Embedding + LLM + Rerank)
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding-flash

# LLM (OpenAI-compatible); swap in any compatible model
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.8-max-0902

# MySQL
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/rag_db?charset=utf8mb4

# Required for Docker deployment
MYSQL_ROOT_PASSWORD=your_password
```

> 💡 Free to try: sign up for the Alibaba Cloud DashScope console and claim the free quota for new users — the whole project runs without paying anything.

### Run the Streamlit frontend (optional)

The repo ships a Streamlit frontend (`frontend/app.py`) with a GUI for uploading documents, RAG / Agent Q&A, and switching knowledge bases:

```bash
# Make sure the backend is running (Docker or local), then:
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Your browser opens `http://localhost:8501`; the frontend connects to the backend at `http://localhost:8000` by default.

---

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/rag/upload` | Upload a PDF: parse, chunk, embed |
| POST | `/rag/chat` | RAG Q&A (multi-turn) |
| POST | `/rag/chat/stream` | Streaming RAG Q&A (SSE) |
| POST | `/agent/chat` | Agent-mode Q&A (LLM autonomously calls tools) |
| GET | `/rag/history/{conversation_id}` | Fetch a conversation's history |
| GET | `/rag/conversations` | List conversations |
| GET | `/rag/collections` | List knowledge bases |

### Example: RAG Q&A

```bash
curl -X POST 'http://127.0.0.1:8000/rag/chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What is RAG",
    "top_k": 3
  }'
```

Response (answer cites its sources):

```json
{
  "statusCode": 200,
  "question": "What is RAG",
  "answer": "RAG stands for Retrieval-Augmented Generation…… [1][2]",
  "sources": [
    { "index": 1, "source": "text.pdf", "page": 1, "chunk_index": 0, "preview": "……" }
  ]
}
```

**Multi-turn**: omit `conversation_id` on the first request, save the returned session id, then pass it on later requests:

```json
{ "question": "What does it do", "conversation_id": 9 }
```

The system resolves "it" from the conversation history.

---

## Evaluation results

> "Being able to prove how good it is" is the most commonly missing — and most educational — part of any RAG project. Full experiment log: [docs/experiment_log.md](docs/experiment_log.md).

### Custom test set (30 questions, Happy-LLM technical doc)

| Metric | Value |
| --- | --- |
| Answer accuracy | 95.65% |
| Retrieval hit rate | 95.65% |
| Out-of-scope refusal rate | 100.00% |

### Public test set (100 questions, CRUD-RAG Chinese benchmark)

| Metric | Value |
| --- | --- |
| Answer accuracy | 85.00% |
| Retrieval hit rate | 90.00% |

Evaluation uses a **strict RAG criterion**: an answer only counts if it is supported by the retrieved context — a much more honest measure than keyword matching.

---

## Key design decisions

The most instructive (and counter-intuitive) decisions in this project. Full pitfalls log: [docs/experiment_log.md](docs/experiment_log.md).

### 1. NFKC normalization: the invisible Chinese-PDF trap

pdfplumber turns the Chinese character「力」(force) into the Kangxi radical「⼒」while extracting text — visually identical, but totally different code points, so your query never matches the stored text.

**Fix**: add Unicode NFKC normalization during cleaning:

```python
import unicodedata
text = unicodedata.normalize('NFKC', text)
```

### 2. Chinese-friendly chunking

Default English separators work poorly for Chinese. Custom priority:

```
["\n\n", "\n", "。", "！", "？", "；", "，", ". ", " ", ""]
```

Chunk size 500, overlap 100 — retrieval quality improves noticeably.

### 3. Two-stage retrieval: coarse recall, fine rerank

- Vector recall top-20 (fast, low precision)
- Distance threshold filters out clearly irrelevant items
- Rerank model scores each (query, document) pair, keeps top-3 for the LLM
- Falls back to the original order if rerank fails

### 4. Three-layer anti-hallucination

| Layer | Measure | Effect |
| --- | --- | --- |
| Retrieval | Cosine distance threshold (measured 0.65) | Irrelevant content never reaches the LLM |
| Prompt | Explicit "say you don't know" instruction | Constrains LLM behavior |
| Output | Citation numbers map to real sources | User can verify |

The threshold isn't a guess — measured: answered questions distance ≤ 0.57, unanswered distance ≥ 0.76.

### 5. LangGraph Agent

A state graph orchestrates the Agent; the LLM picks tools via function calling:

```
START → agent_node ─┬→ tool_node → agent_node (loop, capped at 8)
                    └→ END
```

- Local tools: `retrieve_knowledge_base` (semantic search), `list_documents`
- MCP tools: `list_documents`, `get_document_stats` (loaded dynamically from a standalone MCP Server)
- If the loop cap is hit mid-tool-call, a final bare-LLM call produces the answer

### 6. Decoupling tools from the Agent with MCP

The traditional approach hardcodes tools inside the Agent — adding one means editing code and restarting.

After the refactor, tools live in a standalone MCP Server loaded via `langchain-mcp-adapters`. Adding weather lookup or DB query later only means adding one MCP Server; the Agent stays untouched.

### 7. Multi-knowledge-base isolation

Each knowledge base maps to its own Chroma collection, physically isolated:

- A `contextvar` carries the current knowledge-base name (set at request start, read inside tools)
- The tool function takes no "knowledge base" argument — otherwise the LLM interferes with the choice
- The frontend lists collections via `GET /rag/collections`

### 8. Engineering basics: async + timeout + retry

- Full `async/await`, blocking libraries isolated via `run_in_threadpool`
- LLM calls: tenacity exponential backoff, 3 retries, 30s timeout
- Whole-request timeouts via `asyncio.wait_for` (RAG 180s / Agent 120s)

---

## Known limitations

Stated honestly — these are also its improvement directions (👈 PRs welcome):

1. Code-like content (code blocks / default parameter values) retrieves poorly
2. multi_hop cross-section questions may retrieve incompletely
3. MCP tools always hit the default knowledge base (the MCP Server is a separate process; `contextvar` doesn't cross over)
4. LLM internal-knowledge leakage (an open problem in RAG)
5. Large files process slowly; high-concurrency untested

---

## Roadmap

- [ ] AST / code-block aware chunking for better code retrieval
- [ ] Iterative retrieval for multi_hop questions (retrieve → read → retrieve again)
- [ ] MCP tools supporting multi-knowledge-base switching
- [ ] Dynamic `max_tokens` per question type
- [ ] Queued uploads for large files
- [ ] Unit / integration test coverage
- [ ] Frontend wired to SSE streaming output for faster first-token response

---

## Project structure

```
├── main.py                  # FastAPI entrypoint, lifespan registration
├── config.py                # Config management (.env loading)
├── requirements.txt
├── Dockerfile               # Image build
├── docker-compose.yml       # Service orchestration (API + MySQL)
├── .env.example             # Environment variable template
├── app/
│   ├── api/                 # Routing layer (rag_api / agent_api)
│   ├── services/            # Business logic (rag / agent / chat / llm / mcp)
│   ├── db/                  # Database layer
│   ├── core/                # Logging, exceptions
│   └── schemas/             # Pydantic models
├── frontend/
│   ├── app.py               # Streamlit frontend
│   └── requirements.txt     # Frontend dependencies
├── mcp_server/
│   └── server.py            # Standalone MCP Server (FastMCP tools)
├── scripts/                 # Data & evaluation scripts
├── data/                    # Test sets and KB text
├── results/                 # Evaluation report output
└── docs/                    # Screenshots + experiment log
```

---

## Contributing

Contributions are very welcome — even a bug report or an extra comment. See [CONTRIBUTING.md](CONTRIBUTING.md).

Quick steps:

1. Fork this repo
2. Create a branch: `git checkout -b feature/xxx`
3. Commit: `git commit -m 'feat: xxx'`
4. Push and open a Pull Request

---

## License

[MIT License](LICENSE) © 2026

---

## If this helped you

If this project helped you understand RAG, please ⭐ Star it — for a learner-oriented open source project, that's the best encouragement, and it helps other students like you find it.