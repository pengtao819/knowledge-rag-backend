from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.services.agent_service import run_agent
from app.db.database import get_db
from app.services.agent_service import run_agent
from app.services.chat_service import (
    create_conversation,
    save_message,
)
import asyncio

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None

@router.post("/chat")
async def agent_chat(req: AgentChatRequest):
    try:
        if not req.conversation_id:
            conv = await create_conversation(db, title=req.question)
            conversation_id = conv.id
        else:
            conversation_id = req.conversation_id

        await save_message(db, conversation_id, "user", req.question)

        # 放入线程池
        result = await asyncio.wait_for(
            run_agent(req.question),
            timeout=120     # Agent 可能多轮循环，给更长的整体超时
        )

        await save_message(
            db,
            conversation_id,
            "assistant",
            result["answer"],
            sources=None,  # Agent 暂时没有 sources 结构
        )

        return {
            "statusCode": 200,
            "conversation_id": conversation_id,
            "question": req.question,
            "answer": result["answer"],
            "messages_count": result["messages_count"],
            "loop_count": result["loop_count"]
        }


    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent 处理超时，请重试")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败：{str(e)}")



