from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)
from config import settings

# 异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,      # 打印所有SQL，上传前记得关掉
    pool_pre_ping=True,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # commit后对象不过期，能继续访问属性
)

# ORM基类
class Base(DeclarativeBase):
    pass

# 会话表
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(    # 会话ID(主键)
        Integer,
        primary_key=True,
        autoincrement=True
    )
    title: Mapped[str] = mapped_column(     # 会话标题
        String(255),
        default="新对话"
    )
    created_at: Mapped[datetime] = mapped_column(    # 创建时间
        DateTime,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(   # 最后更新时间
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

# 消息表
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(    # 消息ID
        Integer,
        primary_key=True,
        autoincrement=True
    )
    conversation_id: Mapped[int] = mapped_column(   # 会话归属
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),     # 外键，删除会话时自动删除它的所有消息
        index=True
    )
    role: Mapped[str] = mapped_column(String(20))   # user/assistant
    content: Mapped[str] = mapped_column(Text)  # 消息内容
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)    # 引用来源
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())   # 创建时间

# 建表
async def init_db():
    async with engine.begin() as conn:  # 放入异步环境跑
        await conn.run_sync(Base.metadata.create_all)

# 获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session






