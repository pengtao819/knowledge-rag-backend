from fastapi import FastAPI
from app.api.rag_api import router as rag_router
from app.api.agent_api import router as agent_router
import uvicorn

app = FastAPI(title="RAG项目")

app.include_router(rag_router)
app.include_router(agent_router)


if __name__  == "__main__":
    uvicorn.run("main:app", reload=True)



