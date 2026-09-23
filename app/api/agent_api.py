from fastapi import APIRouter, HTTPException, Depends
from app.services.agent_service import run_agent
from app.db.database import get_db
from app.services.chat_service import (
    create_conversation,
    save_message,
    get_history,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.models import AgentChatRequest
import asyncio

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/chat")
async def agent_chat(req: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        if not req.conversation_id:
            conv = await create_conversation(db, title=req.question)
            conversation_id = conv.id
            history = []
        else:
            conversation_id = req.conversation_id
            history = await get_history(db, conversation_id, limit=10)

        await save_message(db, conversation_id, "user", req.question)

        # 传入历史，让 Agent 也能结合上下文理解指代词、支持多轮
        result = await asyncio.wait_for(
            run_agent(req.question, history),
            timeout=120     # Agent 可能多轮循环，给更长的整体超时
        )

        await save_message(
            db,
            conversation_id,
            "assistant",
            result["answer"],
            sources=result.get("sources"),  # 从 None 改成实际值
        )

        return {
            "statusCode": 200,
            "conversation_id": conversation_id,
            "question": req.question,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "messages_count": result["messages_count"],
            "loop_count": result["loop_count"]
        }

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent 处理超时，请重试")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败：{str(e)}")
