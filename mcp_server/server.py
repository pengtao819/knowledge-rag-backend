from mcp.server.fastmcp import FastMCP
from pathlib import Path
import os
import chromadb

mcp = FastMCP("KnowledgeBaseMCP")

BASE_DIR = Path(__file__).resolve().parent.parent

# Chroma 持久化路径（与主项目共用同一个向量库目录）
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))
COLLECTION = os.getenv("CHROMA_COLLECTION", "knowledge_base")


@mcp.tool()
def list_documents(collection_name: str = "knowledge_base") -> str:
    """列出知识库中已上传的所有文档。

    当用户问"知识库有哪些文档""上传了什么资料"时使用。

    Args:
        collection_name: 知识库名称，默认为 knowledge_base
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(collection_name)

    results = collection.get(include=["metadatas"])
    doc_count = {}
    for meta in results["metadatas"]:
        name = meta.get("source", "unknown")
        doc_count[name] = doc_count.get(name, 0) + 1

    if not doc_count:
        return "知识库为空，暂无文档。"

    lines = [f"- {name}：{count} 个分块" for name, count in doc_count.items()]
    return "知识库中的文档：\n" + "\n".join(lines)


@mcp.tool()
def get_document_stats(collection_name: str = "knowledge_base") -> str:
    """返回知识库的统计信息：文档数、总 chunk 数。

    当用户问"知识库有多大""总共有多少内容"时使用。

    Args:
        collection_name: 知识库名称，默认为 knowledge_base
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(collection_name)

    results = collection.get(include=["metadatas"])
    total_chunks = len(results["metadatas"])
    unique_docs = len(set(m.get("source", "") for m in results["metadatas"]))

    return f"知识库统计：\n- 文档数量：{unique_docs}\n- 总分块数：{total_chunks}"


if __name__ == "__main__":
    mcp.run(transport="stdio")