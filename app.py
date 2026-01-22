import streamlit as st
from langgraph_database_backend import (
    chatbot,
    retrieve_all_threads,
    save_thread_title,
    get_all_thread_titles,
    clear_chat
)
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from datetime import datetime
import time

# ==========================================
# Helpers
# ==========================================

def now_time():
    return datetime.now().strftime("%H:%M")

def generate_thread_id():
    return str(uuid.uuid4())

def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])

def generate_unique_thread_title(user_message):
    words = user_message.split()
    base = " ".join(words[:5]).capitalize() + ("..." if len(words) > 5 else "")
    existing = st.session_state["thread_titles"].values()

    if base not in existing:
        return base

    i = 2
    while f"{base} ({i})" in existing:
        i += 1
    return f"{base} ({i})"

def add_thread(thread_id, title="New Chat"):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)
        st.session_state["thread_titles"][thread_id] = title
        save_thread_title(thread_id, title)

def reset_chat():
    tid = generate_thread_id()
    st.session_state["thread_id"] = tid
    st.session_state["message_history"] = []
    add_thread(tid, "New Chat")

# ==========================================
# Session State
# ==========================================

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

if "thread_titles" not in st.session_state:
    st.session_state["thread_titles"] = get_all_thread_titles()

add_thread(st.session_state["thread_id"], "New Chat")

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>
html, body {
    background-color: #0e1117;
    color: #e5e7eb;
    font-family: Inter, sans-serif;
}

.stSidebar {
    background-color: #0b0f14;
    border-right: 1px solid #1f2937;
}

.chat-container {
    max-width: 900px;
    margin: auto;
    padding: 1rem;
}

.message {
    max-width: 75%;
    padding: 0.75rem 1rem;
    border-radius: 14px;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    line-height: 1.55;
}

.user {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white;
    margin-left: auto;
}

.assistant {
    background-color: #1f2937;
    color: #e5e7eb;
    margin-right: auto;
}

.timestamp {
    font-size: 0.7rem;
    color: #9ca3af;
    margin-top: 2px;
}

.typing {
    font-size: 0.85rem;
    color: #9ca3af;
    padding-left: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# Sidebar
# ==========================================

st.sidebar.markdown("### 🤖 LangGraph Assistant")
st.sidebar.caption("Persistent AI conversations")
st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("➕ New"):
        reset_chat()
with col2:
    if st.button("🗑️ Clear"):
        clear_chat(st.session_state["thread_id"])
        st.session_state["message_history"] = []

st.sidebar.divider()
st.sidebar.subheader("Conversations")

for thread in st.session_state["chat_threads"][::-1]:
    title = st.session_state["thread_titles"].get(thread, "New Chat")
    if st.sidebar.button(title, key=thread):
        st.session_state["thread_id"] = thread
        msgs = load_conversation(thread)
        st.session_state["message_history"] = [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
                "time": now_time()
            }
            for m in msgs
        ]

# ==========================================
# Chat Rendering
# ==========================================

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state["message_history"]:
    cls = "user" if msg["role"] == "user" else "assistant"
    st.markdown(
        f"""
        <div class="message {cls}">
            {msg["content"]}
            <div class="timestamp">{msg["time"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# Input + Streaming
# ==========================================

user_input = st.chat_input("Type your message...")

if user_input:
    # Save user message
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input,
        "time": now_time()
    })
    st.markdown(
        f"""
                    <div class="message user">
                        {user_input}
                        <div class="timestamp">{now_time()}</div>
                    </div>
                    """,
        unsafe_allow_html=True
    )


    # Auto title
    tid = st.session_state["thread_id"]
    if st.session_state["thread_titles"].get(tid) == "New Chat":
        title = generate_unique_thread_title(user_input)
        st.session_state["thread_titles"][tid] = title
        save_thread_title(tid, title)

    # Typing indicator
    typing_placeholder = st.empty()
    for dots in ["", ".", "..", "..."]:
        typing_placeholder.markdown(
            f"<div class='typing'>Assistant typing{dots}</div>",
            unsafe_allow_html=True
        )
        time.sleep(0.25)

    typing_placeholder.empty()

    # Stream response correctly

    full_reply = ""

    config = {"configurable": {"thread_id": tid}}

    for chunk, _ in chatbot.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages"
    ):
        if isinstance(chunk, AIMessage):
            full_reply += chunk.content


    st.markdown(
        f"""
                    <div class="message assistant">
                        {full_reply}
                    </div>
                    """,
        unsafe_allow_html=True
    )

    # Store ONLY TEXT
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": full_reply,
        "time": now_time()
    })
