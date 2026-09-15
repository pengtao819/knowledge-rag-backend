from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.services.agent_service import run_agent
import asyncio

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def agent_chat(req: AgentChatRequest):
    try:
        # 放入线程池
        result = await asyncio.wait_for(
            run_agent(req.question),
            timeout=120     # Agent 可能多轮循环，给更长的整体超时
        )

        return {
            "statusCode": 200,
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



