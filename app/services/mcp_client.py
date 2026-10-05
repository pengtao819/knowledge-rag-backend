import os
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MCP_SERVER_SCRIPT = os.path.join(BASE_DIR, "mcp_server", "server.py")

# MCP Server 连接配置
MCP_CONFIG = {
    "knowledge_base": {
        "command": sys.executable,
        "args": [MCP_SERVER_SCRIPT],
        "transport": "stdio",
    }
}


async def load_mcp_tools():
    """连接 MCP Server，加载所有工具为 LangChain Tool 列表。"""
    client = MultiServerMCPClient(MCP_CONFIG)
    tools = await client.get_tools()
    return tools