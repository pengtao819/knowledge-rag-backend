from fastapi import FastAPI
from app.api.rag_api import router as rag_router
from app.api.agent_api import router as agent_router
from app.db.database import init_db
from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    yield

app = FastAPI(title="RAG项目")

app.include_router(rag_router)
app.include_router(agent_router)


# if __name__  == "__main__":
#     uvicorn.run("main:app", reload=True)



