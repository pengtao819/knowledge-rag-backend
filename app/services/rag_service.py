import os
import re
import pdfplumber
import chromadb
from typing import List
from fastapi import UploadFile
from config import settings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 上传目录
UPLOAD_FOLDER = './uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        metadata={"hnsw:space": "cosine"},  # 用余弦相似度
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

    # 批量向量化
    vectors = embedding_model.embed_documents(texts)

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

    # 存入chroma（后续改）
    collection.add(
        ids=ids,            # id
        documents=texts,    # 原文
        embeddings=vectors, # 向量
        metadatas=metadatas  # 元数据
    )

    return len(chunks)

# 检索函数
def retrieve_chunks(question: str, top_k=3, max_distance: float = 0.65) -> List[Document]:
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

    # 加这行，看实际 distance
    print("=== 查询:", question, "===")
    for text, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"distance={dist:.4f} | {text[:50]}")

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

    return docs

# RAG回答
def rag_chat(question: str, top_k=3) -> dict:
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
    response = llm.invoke([
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










