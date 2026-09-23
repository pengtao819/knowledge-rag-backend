from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from langchain_openai import ChatOpenAI
from openai import APITimeoutError, APIConnectionError, RateLimitError
from config import settings


# 配置
LLM_TIMEOUT = 60       # 单次 LLM 调用超时（秒）
MAX_RETRIES = 2        # 最大重试次数

def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0,
        timeout=LLM_TIMEOUT,
        max_retries=0,   # 关掉 SDK 自带重试，统一用 tenacity 管
        max_tokens=1024  # 限制输出长度
    )

# 模块级 LLM 实例，全局复用
llm = create_llm()

# 只对这几类异常重试，其他异常直接抛出
RETRYABLE_EXCEPTIONS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
)

@retry(
    stop=stop_after_attempt(MAX_RETRIES),                       # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=1, max=10),         # 间隔 1s → 2s → 4s ...
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),        # 只重试这些异常
    reraise=True,                                                # 重试用尽后抛原异常
)
async def call_llm_async(llm_instance, messages):
    # 带重试的异步 LLM 调用
    return await llm_instance.ainvoke(messages)