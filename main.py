from fastapi import FastAPI
from app.api.rag_api import router as rag_router
from app.api.agent_api import router as agent_router
from app.db.database import init_db
from contextlib import asynccontextmanager
from app.core.logging import setup_logging
from fastapi import Request
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError
import uvicorn

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # 启动时执行
    await init_db()
    yield

app = FastAPI(title="RAG项目", lifespan=lifespan)

app.include_router(rag_router)
app.include_router(agent_router)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    # 业务异常:预期内，用warning记录
    logger.warning("业务异常: %s | path=%s", exc.detail, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"statusCode": exc.status_code, "detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    # 未预期的异常：记 error + 完整堆栈
    logger.exception("未处理异常 | path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"statusCode": 500, "detail": "服务器内部错误"},
    )

# if __name__  == "__main__":
#     uvicorn.run("main:app", reload=True)



