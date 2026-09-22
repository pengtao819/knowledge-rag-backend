from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from config import settings
from app.services.rag_service import retrieve_knowledge_base,list_documents
from app.services.llm_client import llm, call_llm_async

MAX_LOOPS = 5   # agent最大调用次数

# 工具列表
TOOLS = [retrieve_knowledge_base, list_documents]

# 工具名 → 函数对象，tool_node 用它来执行
TOOLS_MAP = {
    "retrieve_knowledge_base": retrieve_knowledge_base,
    "list_documents": list_documents,
}

class AgentState(TypedDict):
    # 对话消息列表，全程累积
    # add_messages 新消息追加而不是覆盖
    messages: Annotated[list, add_messages]
    loop_count: int     # 计循环次数

# 决策
async def agent_node(state: AgentState) -> dict:
    # 把工具绑定到 LLM
    llm_with_tools = llm.bind_tools(TOOLS)

    # 把完整消息历史传进去，LLM 判断下一步
    response = await call_llm_async(llm_with_tools, state["messages"])

    # 返回的消息会被追加到 state["messages"]
    return {
        "messages": [response],
        "loop_count": state.get("loop_count", 0) + 1
    }

# 执行
def tool_node(state: AgentState) -> dict:
    # 最后一条消息是 agent_node 刚生成的 AIMessage
    last_message = state["messages"][-1]
    tool_messages = []

    # LLM 可能一次调多个工具，循环处理
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        tool_func = TOOLS_MAP.get(tool_name)

        if tool_func is None:
            # LLM 编了一个不存在的工具名
            result = f"未知工具：{tool_name}"
        else:
            try:
                result = tool_func.invoke(tool_args)
            except Exception as e:
                # 工具内部报错，错误信息给 LLM
                result = f"工具执行失败：{e}"

        # 包装成 ToolMessage，tool_call_id 要和 tool_calls 里的 id 对应
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_id)
        )

    return {"messages": tool_messages}

# 判断走向
def should_continue(state: AgentState) -> str:
    # 超出最大循环次数，强制结束
    if state.get("loop_count", 0) == MAX_LOOPS:
        return "end"

    # 看最后一条消息
    last_message = state["messages"][-1]

    # 有 tool_calls → LLM 想调工具，去 tool 节点
    if last_message.tool_calls:
        return "tools"

    # 没有 → LLM 给出最终回答，结束
    return "end"

# 创建图
def build_agent_graph():
    graph_builder = StateGraph(AgentState)

    # 注册节点
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    # 连边
    graph_builder.add_edge(START, "agent")
    # agent执行后，决定去哪
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    graph_builder.add_edge("tools", "agent")

    # 编译
    return graph_builder.compile()

agent_graph = build_agent_graph()

async def run_agent(question: str, history: list = None) -> dict:
    # 初始消息：历史对话 + 当前问题，让 Agent 支持多轮（指代词消解）
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

    # 执行图，传入初始状态
    final_state = await agent_graph.ainvoke(initial_state)

    # 最后一条消息就是最终回答
    final_message = final_state["messages"][-1]

    # 循环保护触发时，最后一条可能是带 tool_calls 的 AIMessage
    if hasattr(final_message, "tool_calls") and final_message.tool_calls:
        answer = "抱歉，处理超时，请换个方式提问。"
    else:
        answer = final_message.content

    return {
        "answer": answer,
        "messages_count": len(final_state["messages"]),
        "loop_count": final_state["loop_count"]
    }






