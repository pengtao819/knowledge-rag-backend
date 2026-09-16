import os
import asyncio
import json
import logging
from pydantic import BaseModel
from app.services.rag_service import rag_chat
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from app.services.rag_service import save_upload_pdf, parse_pdf, chunking_pdf, store_chunks_to_chroma
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.rag_service import rag_chat, rewrite_question
from app.services.chat_service import create_conversation, save_message, get_history, list_conversations
from app.core.exceptions import ConversationNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG知识库"])
UPLOAD_FOLDER = './uploads'

class ChatRequest(BaseModel):
    question: str
    top_k: int = 3
    conversation_id: int | None = None

# PDF处理
@router.post("/upload")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="仅支持PDF文件")

        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file_exist = os.path.exists(save_path)

        if not file_exist:
            # 文件不存在：保存到磁盘
            with open(save_path, "wb") as f:
                f.write(await file.read())
            msg = "文件不存在，已保存并解析"
        else:
            # 文件已存在：不保存，直接使用旧文件解析
            msg = "同名文件已存在，跳过保存，直接解析已有文件"   # 下次改成按文件内容判断

        # 解析
        docs = await run_in_threadpool(parse_pdf, file.filename)
        if not docs:
            raise HTTPException(status_code=400, detail="PDF未提取到文本")

        # 分块
        chunks = await run_in_threadpool(chunking_pdf, docs)
        if not chunks:
            raise HTTPException(status_code=400, datail="分块结果为空")

        # 向量化并存入chroma
        stored_count = await run_in_threadpool(store_chunks_to_chroma, chunks)

        return {
            "filename": file.filename,
            "pages": len(docs),
            "chunks": len(chunks),
            "stored_to_chroma": stored_count,
            "msg": msg
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF处理失败：{str(e)}")

# RAG检索
@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    logger.info("收到问答请求: question=%s, conversation_id=%s", req.question, req.conversation_id)

    if req.conversation_id:
        conv_exists = await get_history(db, req.conversation_id, limit=1)
        if not conv_exists:
            raise ConversationNotFoundError(f"会话 {req.conversation_id} 不存在")

    # 如果没有conversation_id就新建会话
    if not req.conversation_id:
        conv = await create_conversation(db, title=req.question)
        conversation_id = conv.id
        history = []
    else:
        conversation_id = req.conversation_id
        history = await get_history(db, conversation_id, limit=10)

    # 保存用户消息
    await save_message(db, conversation_id, "user", req.question)

    # 问题改写（有指代词才改）
    rewritten = await rewrite_question(req.question, history)

    # 调用RAG回答问题
    result = await asyncio.wait_for(
        rag_chat(rewritten, req.top_k, history),
        timeout=60      # 整个请求不超过60秒
    )

    # 保存助手回答
    await save_message(
        db,conversation_id,"assistant",
        result["answer"],sources=result["sources"]
    )

    logger.info("问答完成: conversation_id=%s, sources=%d", conversation_id, len(result["sources"]))

    return{
        "statusCode": 200,
        "question": req.question,
        "answer": result["answer"],
        "sources": result["sources"]
    }

@router.get("history/{conversation_id}")
async def history(conversation_id: int, db: AsyncSession = Depends(get_db)):
    messages = await get_history(db, conversation_id)

    return {
        "statusCode": 200,
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources else None,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    }

@router.get("/conversations")
async def get_conversation_list(db: AsyncSession = Depends(get_db)):
    convs = await list_conversations(db)
    return {
        "statusCode": 200,
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in convs
        ]
    }