import streamlit as st
import requests

# 后端接口地址
API_BASE = "http://localhost:8000"

# 页面配置
st.set_page_config(
    page_title="知识库智能问答",
    page_icon="📚",
    layout="wide",
)

st.title("知识库智能问答")
st.caption("基于 RAG 的私有文档问答系统 · FastAPI + Chroma + 通义千问")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# 侧边栏
with st.sidebar:
    st.header("操作面板")

    # 模式切换
    mode = st.radio(
        "问答模式",
        options=["RAG 模式", "Agent 模式"],
        help="RAG 模式：固定检索+生成链路；Agent 模式：LLM 自主决策是否调用工具",
    )

    st.divider()
    st.subheader("上传文档")
    uploaded_file = st.file_uploader("选择 PDF 文件", type=["pdf"])
    if uploaded_file is not None:
        if st.button("上传并解析", use_container_width=True):
            with st.spinner("正在解析、分块、向量化..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }
                    resp = requests.post(
                        f"{API_BASE}/rag/upload",
                        files=files,
                        timeout=600,  # 大 PDF 分块慢，给 10 分钟
                        proxies={"http": None, "https": None},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    st.success(
                        f"✅ {data.get('filename')}\n\n"
                        f"- 页数：{data.get('pages')}\n"
                        f"- 分块数：{data.get('chunks')}\n"
                        f"- 入库数：{data.get('stored_to_chroma')}"
                    )
                except Exception as e:
                    st.error(f"上传失败：{e}")

    st.divider()

    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

    st.divider()
    st.markdown("**当前会话 ID**")
    st.code(st.session_state.conversation_id or "未开始")

# 渲染历史对话
# 遍历 session_state 里存的每条消息，逐条渲染成聊天气泡
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果这条消息带了引用来源，用折叠面板展示
        if msg.get("sources"):
            with st.expander(f"引用来源（{len(msg['sources'])} 条）"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f"**[{i}] {src.get('source', '未知')}** "
                        f"· 第 {src.get('page', '?')} 页"
                    )
                    st.caption(src.get("preview", ""))

# 输入框
# st.chat_input 固定在页面底部，回车即提交
question = st.chat_input("输入你的问题...")

if question:
    # 1. 先把用户消息显示出来
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2. 调后端接口拿回答
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                if mode == "Agent 模式":
                    payload = {"question": question}
                else:
                    payload = {"question": question, "top_k": 3}

                if st.session_state.conversation_id:
                    payload["conversation_id"] = st.session_state.conversation_id

                endpoint = "/agent/chat" if mode == "Agent 模式" else "/rag/chat"

                resp = requests.post(
                    f"{API_BASE}{endpoint}",
                    json=payload,
                    timeout=200,
                    proxies={"http": None, "https": None},
                )
                resp.raise_for_status()
                data = resp.json()

                answer = data.get("answer", "（无回答）")
                sources = data.get("sources", [])

                # 保存会话 ID（多轮对话用）
                if data.get("conversation_id"):
                    st.session_state.conversation_id = data["conversation_id"]

                # 3. 显示回答
                st.markdown(answer)

                # 4. 显示引用来源
                if sources:
                    with st.expander(f"引用来源（{len(sources)} 条）"):
                        for i, src in enumerate(sources, 1):
                            st.markdown(
                                f"**[{i}] {src.get('source', '未知')}** "
                                f"· 第 {src.get('page', '?')} 页"
                            )
                            st.caption(src.get("preview", ""))

                # 5. 存进历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except requests.exceptions.Timeout:
                error_msg = "请求超时。可能是文档检索或模型生成太慢，请稍后重试。"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

            except Exception as e:
                error_msg = f"请求失败：{e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

