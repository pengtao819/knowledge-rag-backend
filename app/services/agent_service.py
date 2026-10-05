from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from app.services.rag_service import retrieve_knowledge_base,new_request_id,pop_sources
from app.services.llm_client import llm, call_llm_async
from app.services.mcp_client import load_mcp_tools


MAX_LOOPS = 8   # agent最大调用次数

class AgentState(TypedDict):
    # 对话消息列表，全程累积
    # add_messages 新消息追加而不是覆盖
    messages: Annotated[list, add_messages]
    loop_count: int     # 计循环次数


# 创建图
def build_agent_graph_with_tools(tools: list):
    """构建带指定工具列表的 Agent 图。"""
    tools_map = {t.name: t for t in tools}

    async def agent_node(state: AgentState) -> dict:
        llm_with_tools = llm.bind_tools(tools)
        response = await call_llm_async(llm_with_tools, state["messages"])
        return {
            "messages": [response],
            "loop_count": state.get("loop_count", 0) + 1,
        }

    async def tool_node(state: AgentState) -> dict:
        last_message = state["messages"][-1]
        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            tool_func = tools_map.get(tool_name)
            if tool_func is None:
                result = f"未知工具：{tool_name}"
            else:
                try:
                    result = await tool_func.ainvoke(tool_args)
                except Exception as e:
                    result = f"工具执行失败：{e}"
            tool_messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_id)
            )
        return {"messages": tool_messages}

    def should_continue(state: AgentState) -> str:
        if state.get("loop_count", 0) == MAX_LOOPS:
            return "end"
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return "end"

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "end": END}
    )
    graph_builder.add_edge("tools", "agent")
    return graph_builder.compile()


async def run_agent(question: str, history: list = None) -> dict:
    # 生成请求 ID，初始化收集器
    rid = new_request_id()

    try:
        # 加载 MCP 工具
        mcp_tools = await load_mcp_tools()

        # 合并原有工具 + MCP 工具
        all_tools = [retrieve_knowledge_base] + mcp_tools

        # 构建一个带 MCP 工具的 Agent 图
        graph = build_agent_graph_with_tools(all_tools)

        # 初始消息：历史对话 + 当前问题
        messages = []
        if history:
            for m in history:
                if m.role == "user":
                    messages.append(HumanMessage(content=m.content))
                else:
                    messages.append(AIMessage(content=m.content))
        messages.append(HumanMessage(content=question))

        initial_state = {
            "messages": messages,
            "loop_count": 0
        }

        # 执行图
        final_state = await graph.ainvoke(initial_state)

        # 取出本次请求收集的 sources
        sources = pop_sources(rid)

        # 最后一条消息
        final_message = final_state["messages"][-1]

        if hasattr(final_message, "tool_calls") and final_message.tool_calls:
            # 达到循环上限时，LLM 还在调工具。
            # 补救：再调一次不带工具的 LLM，让它基于已有上下文给出最终答案。
            final_response = await call_llm_async(llm, final_state["messages"])
            answer = final_response.content
        else:
            answer = final_message.content

        return {
            "answer": answer,
            "sources": sources,
            "messages_count": len(final_state["messages"]),
            "loop_count": final_state["loop_count"]
        }
    finally:
        # 兜底清理，防止内存泄漏
        pop_sources(rid)






