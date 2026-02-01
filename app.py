import streamlit as st
from chatbot_ollama import chatbot, retrieve_all_threads, save_thread_title, get_all_thread_titles,clear_chat
from langchain_core.messages import HumanMessage,AIMessage
import uuid

# ==========================================
# Utility Functions
# ==========================================

def generate_thread_id():
    return str(uuid.uuid4())

def load_conversation(thread_id):
    """Load messages for a given thread. Return empty list if no messages exist."""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

def generate_unique_thread_title(user_message):
    """Generate a unique and meaningful thread title based on the user input."""
    words = user_message.split()
    base_title = " ".join(words[:5]).capitalize() + ("..." if len(words) > 5 else "")
    existing_titles = st.session_state['thread_titles'].values()
    if base_title not in existing_titles:
        return base_title

    counter = 2
    new_title = f"{base_title} ({counter})"
    while new_title in existing_titles:
        counter += 1
        new_title = f"{base_title} ({counter})"
    return new_title

def add_thread(thread_id, title="New Chat"):
    """Register a new thread."""
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_titles'][thread_id] = title
        save_thread_title(thread_id, title)

def reset_chat():
    """Start a new thread."""
    thread_id = generate_thread_id()
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id, "New Chat")

# ==========================================
# Session Setup
# ==========================================
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_titles' not in st.session_state:
    st.session_state['thread_titles'] = get_all_thread_titles()

add_thread(st.session_state['thread_id'], "New Chat")

# ==========================================
# Custom CSS for Classy ChatGPT UI
# ==========================================
st.markdown("""
<style>
/* ================= GLOBAL ================= */
html, body {
    background-color: #0e1117;
    color: #e5e7eb;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont;
}

/* Center chat like ChatGPT */
.block-container {
    max-width: 880px;
    margin: auto;
    padding-top: 1.2rem;
    padding-bottom: 6rem;
}

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"] {
    background-color: #0b0f14;
    border-right: 1px solid #1f2937;
}

/* ================= CHAT ================= */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
}

/* User message */
.user-bubble {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: #ffffff;
    padding: 0.75rem 1rem;
    border-radius: 14px 14px 4px 14px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.55;
    margin-left: auto;
    word-wrap: break-word;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}

/* Assistant message */
.assistant-bubble {
    background-color: #1f2937;
    color: #e5e7eb;
    padding: 0.75rem 1rem;
    border-radius: 14px 14px 14px 4px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.55;
    margin-right: auto;
    word-wrap: break-word;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}


/* ================= CHAT INPUT ================= */
div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 0;
    left: 260px;              /* sidebar width */
    right: 0;
    padding: 0.75rem 1rem;
    background: linear-gradient(transparent, #0e1117 45%);
    z-index: 100;
}

/* Input box */
div[data-testid="stChatInput"] textarea {
    max-width: 880px;
    margin: auto;
    display: block;
    background-color: #111827;
    color: #e5e7eb;
    border-radius: 12px;
    border: 1px solid #1f2937;
    padding: 0.55rem 0.85rem;   /* smaller height */
    font-size: 0.9rem;
}

/* Focus */
div[data-testid="stChatInput"] textarea:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 1px #2563eb;
}
</style>
""", unsafe_allow_html=True)



# ==========================================
# Sidebar UI
# ==========================================
st.sidebar.title('💬 LangGraph Chatbot')
if st.sidebar.button('➕ New Chat'):
    reset_chat()

# Clear Chat button
if st.sidebar.button('🗑️ Clear Chat'):
    clear_chat(st.session_state['thread_id'])
    st.session_state['message_history'] = []

st.sidebar.header('My Conversations')

for thread in st.session_state['chat_threads'][::-1]:
    title = st.session_state['thread_titles'].get(thread, "New Chat")
    btn_class = "thread-button thread-active" if thread == st.session_state['thread_id'] else "thread-button"
    if st.sidebar.button(title, key=thread):
        st.session_state['thread_id'] = thread
        messages = load_conversation(thread)
        st.session_state['message_history'] = [
            {'role': 'user' if isinstance(m, HumanMessage) else 'assistant', 'content': m.content}
            for m in messages
        ]

# ==========================================
# Main Chat Section
# ==========================================
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state['message_history']:
    if message['role'] == 'user':
        st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">{message["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)

    # Update title in DB
    thread_id = st.session_state['thread_id']
    if st.session_state['thread_titles'].get(thread_id, "New Chat") in ["New Chat", ""]:
        title = generate_unique_thread_title(user_input)
        st.session_state['thread_titles'][thread_id] = title
        save_thread_title(thread_id, title)

    # Generate assistant response
    config = {'configurable': {'thread_id': thread_id}}
    with st.spinner("Thinking..."):
        def ai_only_stream():
            for message_chunk,metadata in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                config=config,
                stream_mode='messages'

            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content


        ai_message=st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
