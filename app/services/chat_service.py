import json
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import Conversation, Message

async def create_conversation(db: AsyncSession, title: str = "新对话") -> Conversation:
    # 新建一个会话
    conv = Conversation(title=title[:30])   # 选取标题
    db.add(conv)
    await db.commit()   # 提交事务
    await db.refresh(conv)

    return conv

async def save_message(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    sources: list | None = None
) -> Message:
    # 保存一条消息， sources转成JSON字符串
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=json.dumps(sources, ensure_ascii=False) if sources else None
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_history(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 20
) -> list[Message]:
    # 取某个会话的历史消息，按时间正序
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())     # 时间正序
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def list_conversations(db: AsyncSession, limit: int=20) -> list[Conversation]:
    # 列出最近会话
    stmt = select(Conversation).order_by(desc(Conversation.updated_at)).limit(limit)    # 按updated_at倒序，最近活跃的排前面
    result = await db.execute(stmt)
    return list(result.scalars().all())









