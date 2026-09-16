from pydantic import BaseModel


# ===== 请求模型 =====

class ChatRequest(BaseModel):
    question: str
    top_k: int = 3
    conversation_id: int | None = None


class AgentChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


# ===== 响应模型（可选） =====

class SourceItem(BaseModel):
    index: int
    source: str
    page: int
    chunk_index: int
    preview: str


class ChatResponse(BaseModel):
    statusCode: int = 200
    question: str
    answer: str
    sources: list[SourceItem] = []