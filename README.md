🧠 LangGraph Multi-Thread Chatbot (Ollama + Qwen 2.5)



A production-grade, ChatGPT-style chatbot built using LangGraph, Ollama (Qwen 2.5), and Streamlit, featuring persistent multi-thread conversations, agentic tool calling, and a clean modern UI.

Demo Screenshots are added.

🚀 Overview


This project implements a stateful conversational AI system with:

Multiple persistent chat threads

Automatic thread title generation

Tool-calling agent powered by LangGraph

Local LLM inference using Ollama

SQLite-based memory and checkpoints

Real-time streaming responses

ChatGPT-like professional frontend

The system is fully local-first, extensible, and suitable for portfolio, demos, or internal tools.

Demo video Link: https://youtu.be/e3pjGZ_ms3Q?si=4iUSqW7isewMpblC


🧩 System Architecture


├── Frontend (Streamlit)

│   ├── ChatGPT-style UI

│   ├── Thread switching

│   ├── Streaming responses
│

├── Backend (LangGraph)

│   ├── Qwen 2.5 (Ollama)

│   ├── Tool-calling agent

│   ├── SQLite checkpointing
│
└── Database (SQLite)

    ├── Conversation states
    
    └── Thread titles



✨ Features

💬 Chat Interface

Modern ChatGPT-like UI

Distinct user / assistant message bubbles

Streaming assistant responses

Fixed, compact input bar

Dark, professional theme

🧵 Multi-Thread Conversations

Unlimited chat threads

Auto-generated thread titles from first user message

Switch between conversations instantly

Clear individual chat threads

Thread metadata persisted in SQLite

🧠 Stateful Memory with LangGraph

Each thread maintains independent memory

Conversation state survives reloads

Uses LangGraph SQLite checkpointer

Deterministic, graph-based agent flow


🤖 Local LLM (Ollama)

Model: qwen2.5:latest

Fully local inference (no cloud dependency)

Chat-based model with tool-calling support

Low latency and privacy-friendly

🛠️ Tool-Calling Agent Capabilities

The agent automatically decides when to invoke tools using LangGraph’s tools_condition.



Tool	Description

🔍 DuckDuckGo Search	Real-time web search

🧮 Calculator	Add, subtract, multiply, divide

🕒 Current Date & Time	Fetch live system datetime

📈 Stock Price	Alpha Vantage stock data

🌤️ Weather	OpenWeatherMap API

📍 Local Events	SERP API (Google Events)

📰 News	NewsAPI topic-based headlines


All tools are bound using llm.bind_tools() and executed via ToolNode.

📡 Streaming Responses

Token-level streaming from LangGraph

Smooth real-time output in Streamlit

Non-blocking UI

🗄️ Persistence & Database

SQLite used for:

LangGraph state checkpoints

Chat thread titles

Thread-specific memory

Manual clear options for chats



🧪 Tech Stack

Python

Streamlit – Frontend UI

LangGraph – Agent orchestration

LangChain Core – Messages & tools

Ollama – Local LLM runtime

Qwen 2.5 – Chat model

SQLite – Persistence

⚙️ Environment Variables

Create a .env file:

OPENWEATHER_API_KEY=your_openweather_api_key
SERP_API_KEY=your_serp_api_key
NEWS_API=your_newsapi_key


Ollama runs locally — no API key required for the LLM.

▶️ Running the App
1️⃣ Start Ollama
ollama pull qwen2.5
ollama run qwen2.5

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Launch Streamlit
streamlit run app.py

🧠 LangGraph Flow
START
  ↓
chat_node (LLM)
  ↓
tools_condition

  ├── ToolNode (if tool needed)
  
  └── chat_node


This enables reason → tool → reason loops automatically.

🧼 Design Principles

Local-first, privacy-friendly

Clean separation of UI and logic

Agent-centric architecture

Easily extensible tool system

Minimal frontend logic

🔮 Future Enhancements

RAG with PDFs / documents

Tool usage visualization in UI

Chat export

User authentication

Model switching (LLaMA, Mistral, etc.)

Dockerized deployment

📄 License

MIT License
