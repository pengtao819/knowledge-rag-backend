import os
import re
import pdfplumber
import chromadb
import textwrap
import logging
import json
from typing import List, TypedDict, Annotated
from fastapi import UploadFile
from config import settings
from app.services.llm_client import llm, call_llm_async
from app.core.exceptions import RetrievalError
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from fastapi.responses import StreamingResponse
from app.db.database import AsyncSessionLocal
from app.services.chat_service import save_message

logger = logging.getLogger(__name__)

# 上传目录
UPLOAD_FOLDER = './uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EMBEDDING_BATCH_SIZE = 20   # 模块级常量

# 中文分隔符-优先级
CHINESE_SEPARATORS = [
    "\n\n",
    "\n",
    "。",
    "！",
    "？",
    "；",
    "，",
    ". ",   # .加空格
    "! ",   # !加空格
    "? ",
    "; ",
    ", ",
    " ",
    "",     # 超长无标点文本-兜底
]

_client = None

# 获取 Chroma 持久化客户端
def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client

def get_chroma_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={
            "hnsw:space": "cosine",
            "hnsw:num_threads": 1,          # 单线程写入，避免并发冲突
            "hnsw:sync_threshold": 10000,   # 减少自动压缩频率
        },
    )

 # 获取配置好的embedding模型
def get_embedding_model():
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        check_embedding_ctx_length=False    # 跳过文本长度检查
    )

# 上传保存PDF文档
async def save_upload_pdf(upload_file: UploadFile):
    # 拼接完整路径
    save_path = os.path.join(UPLOAD_FOLDER, upload_file.filename)

    # 写入本地文件
    with open(save_path, 'wb') as f:
        content = await upload_file.read()
        f.write(content)

    return {
        "statusCode": 200,
        "msg": "文件上传成功",
        "filename": upload_file.filename,
        "save_path": save_path
    }

# 文本处理
def clean_text(text: str) -> str:
    # 1.中英文换行 -> 空格
    text = re.sub(r'(?<=[\u4e00-\u9fff])\n(?=[A-Za-z0-9])', ' ', text)
    text = re.sub(r'(?<=[A-Za-z0-9])\n(?=[\u4e00-\u9fff])', ' ', text)
    # 2.去掉中文字符之间的空格
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    # 3.处理换行
    text = text.replace('\n\n', '<<PARA>>')
    text = text.replace('\n', '')
    text = text.replace('<<PARA>>', '\n\n')
    # 4.去掉多余空格
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

# 解析PDF文档
def parse_pdf(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    docs: List[Document] = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue

            page_text = clean_text(page_text)

            docs.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "source": filename,
                        "page": page_num,
                    },
                )
            )

    return docs

# 分块PDF文档
# 待解决问题：大文件处理太慢
def chunking_pdf(document: List[Document],chunk_size: int = 500,chunk_overlap: int = 100) -> List[Document]:
    # 先使用递归字符分块
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap必须小于chunk_size")

    splitter =  RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,          # 最大字符长度
        chunk_overlap=chunk_overlap,    # 重叠字符数
        separators=CHINESE_SEPARATORS,
        length_function=len,
        keep_separator=True,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(document)

    # 加上编号，用于后面引用来源
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx

    return chunks

# 将分块后的chunk向量化并存入chroma
def store_chunks_to_chroma(chunks: List[Document]) -> int:
    collection = get_chroma_collection()
    embedding_model = get_embedding_model()

    # 提取文本
    texts = [chunk.page_content for chunk in chunks]

    # 构造对应格式
    ids = [
        f"{chunk.metadata['source']}_p{chunk.metadata['page']}_c{chunk.metadata['chunk_index']}"
        for chunk in chunks
    ]
    metadatas = [
        {
            "source": chunk.metadata["source"],
            "page": chunk.metadata["page"],
            "chunk_index": chunk.metadata["chunk_index"],
        }
        for chunk in chunks
    ]

    # 分批调用 embedding，每批最多 20 条
    all_vectors = []
    total = len(texts)
    for i in range(0, total, EMBEDDING_BATCH_SIZE):
        batch = texts[i: i + EMBEDDING_BATCH_SIZE]
        batch_vectors = embedding_model.embed_documents(batch)
        all_vectors.extend(batch_vectors)
        logger.info("向量化进度: %d/%d", min(i + EMBEDDING_BATCH_SIZE, total), total)

    # 存入chroma（后续改）
    collection.add(
        ids=ids,            # id
        documents=texts,    # 原文
        embeddings=all_vectors, # 向量
        metadatas=metadatas  # 元数据
    )

    return len(chunks)

# 检索函数
def retrieve_chunks(question: str, top_k=3, max_distance: float = 0.65) -> List[Document]:
    try:
        collection = get_chroma_collection()
        embedding_model = get_embedding_model()

        # 将问题转向量
        query_vector = embedding_model.embed_query(question)

        # 在chroma里检索
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # 包装成Document列表
        docs = []
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            if dist > max_distance:     # 距离大于0.65（测试得来的数值），直接丢弃
                continue
            docs.append(Document(
                page_content=text,
                metadata={**meta, "distance": dist}
            ))

        logger.info("检索: question=%s, 命中 %d 条", question, len(docs))

        return docs
    except Exception as e:
        logger.exception("检索失败: %s", e)
        raise RetrievalError() from e

# RAG回答
async def rag_chat(question: str, top_k=3, history: list = None) -> dict:
    # 检索
    docs = retrieve_chunks(question, top_k)
    if not docs:
        return {
            "answer": "根据当前知识库无法确定",
            "sources": []
        }

    # 拼接上下文
    context_parts = []
    for i, doc in enumerate(docs, start=1):
        context_parts.append(f"[{i}] {doc.page_content}")
    context = "\n\n".join(context_parts)

    # 拼接历史
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m.role}: {m.content}" for m in history[-4:]
        )
        history_text = f"之前的对话：\n{history_text}\n\n"


    # 构造prompt
    system_prompt = (
        "你是一个知识库助手。请严格根据下面提供的上下文回答用户问题。"
        "如果上下文没有相关信息，就回答'根据当前知识库无法确定'。"
        "回答时请用 [1] [2] 这样的编号引用来源。"
        "不需要讨好用户，不要编造上下文中没有的内容。"
    )
    user_prompt = f"上下文：\n{context}\n\n用户问题：{question}"

    # 调用LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0   # 稳定性高，准确
    )
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    # 构造返回
    sources = [
        {
            "index": i,
            "source": doc.metadata["source"],
            "page": doc.metadata["page"],
            "chunk_index": doc.metadata["chunk_index"],
            "preview": doc.page_content[:100]
        }
        for i, doc in enumerate(docs, start=1)
    ]

    return {
        "answer": response.content,
        "sources": sources
    }

# 检索工具
@tool
def retrieve_knowledge_base(query: str) -> str:
    """从知识库中检索与用户问题相关的内容。

    当用户询问知识库中可能存在的具体信息时使用这个工具，比如概念解释、文档内容查询等。

        Args:
            query: 用户的查询问题，用自然语言描述
    """
    docs = retrieve_chunks(query)
    if not docs:
        return "知识库中未找到相关内容"

    results = []
    for i, doc in enumerate(docs, start=1):
        results.append(
            f"[{i}] 来源：{doc.metadata['source']} "
            f"第{doc.metadata['page']}页\n{doc.page_content}"
        )

    return "\n\n".join(results)

# 列举文档工具
@tool
def list_documents() -> str:
    """列出知识库中所有已上传的文档。

    当用户询问"知识库中有哪些文档"、"已经上传了什么资料"、"文档列表"等问题时使用这个工具。
    """
    collection = get_chroma_collection()
    data = collection.get(include=["metadatas"])

    if not data["metadatas"]:
        return "知识库目前没有任何文档。"

    sources = set()     # 去重
    for meta in data["metadatas"]:
        sources.add(meta["source"])

    doc_list = "\n".join(f"- {s}" for s in sources)
    return f"知识库中的文档列表：\n{doc_list}"

# 指代词列表，问题里出现这些词就需要改写
PRONOUNS = ["它", "他", "她", "这个", "那个", "上述", "该", "此", "这"]

def need_rewrite(question: str) -> bool:
    # 判断问题里有没有指代词
    return any(p in question for p in PRONOUNS)

async def rewrite_question(question: str, history: list) -> str:
  # 没有历史 或 问题里没指代词 → 原样返回，不改写
    if not history or not need_rewrite(question):
        return question

    logger.info("问题改写: %s", question)

    # 把最近 4 条历史拼成文本
    history_text = "\n".join(
        f"{m.role}: {m.content}" for m in history[-4:]
    )


    prompt = textwrap.dedent(f"""
        你是一个问题改写助手。请根据历史对话，把用户当前问题中的指代词替换成具体的内容。
        历史对话： {history_text}
        用户当前问题：{question}
        要求：
        1. 当前问题中的"它"、"这个"、"那个"、"上述"等指代词，必须根据历史对话还原成具体名词。
        2. 如果当前问题没有指代词，原样返回。
        3. 只输出改写后的问题，不要任何解释、标点补充或前缀。

        示例：
        历史对话： user: 什么是RAG assistant: RAG是检索增强生成技术...
        用户当前问题：它有什么作用
        改写后：RAG有什么作用

        现在请改写：
        改写后：
        """).strip()

    response = await call_llm_async(llm, [HumanMessage(content=prompt)])
    result = response.content.strip()

    # 清理 LLM 可能加的前缀
    if result.startswith("改写后："):
        result = result[4:].strip()
    if result.startswith("改写后:"):
        result = result[4:].strip()

    logger.info("改写完成: %s → %s", question, result)

    return result

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

async def rag_chat_stream(question: str, history: list, conversation_id: int, top_k: int = 5):
    try:
        docs = retrieve_chunks(question, top_k)
        sources = [
            {
                "index": i,
                "source": doc.metadata["source"],
                "page": doc.metadata["page"],
                "chunk_index": doc.metadata["chunk_index"],
                "preview": doc.page_content[:100],
            }
            for i, doc in enumerate(docs, start=1)
        ]
        yield _sse({"type": "sources", "data": sources})

        if not docs:
            answer = "根据当前知识库无法确定。"
            yield _sse({"type": "token", "data": answer})
            yield _sse({"type": "done", "conversation_id": conversation_id})
            async with AsyncSessionLocal() as db:
                await save_message(db, conversation_id, "assistant", answer, sources=[])
            return

        context = "\n\n".join(f"[{i}] {d.page_content}" for i, d in enumerate(docs, start=1))

        history_text = ""
        if history:
            history_text = "\n".join(f"{m.role}: {m.content}" for m in history[-4:])
            history_text = f"之前的对话：\n{history_text}\n\n"

        system_prompt = (
            "你是一个知识库助手。请严格根据下面提供的上下文回答用户问题。"
            "如果上下文没有相关信息，就回答'根据当前知识库无法确定'。"
            "回答时请用 [1] [2] 这样的编号引用来源。"
            "不要编造上下文中没有的内容。"
        )
        user_prompt = f"{history_text}上下文：\n{context}\n\n用户问题：{question}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        full_answer = ""
        async for chunk in llm.astream(messages):
            if chunk.content:
                full_answer += chunk.content
                yield _sse({"type": "token", "data": chunk.content})

        async with AsyncSessionLocal() as db:
            await save_message(db, conversation_id, "assistant", full_answer, sources=sources)

        yield _sse({"type": "done", "conversation_id": conversation_id})

    except Exception as e:
        logger.exception("流式问答失败")
        yield _sse({"type": "error", "data": str(e)})




