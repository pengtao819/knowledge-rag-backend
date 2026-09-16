import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Settings():
    # embedding(百炼)
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "qwen3.7-text-embedding-flash")

    # 分块
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # chroma(改为绝对路径）
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "knowledge_base")

    # 上传
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))

    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3.8-max-0902")

    # mysql
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")


settings = Settings()
