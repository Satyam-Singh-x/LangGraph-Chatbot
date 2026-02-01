# ====================== langgraph_database_backend.py ======================
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv
import sqlite3
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests
import os
import base64
from datetime import datetime
# -------------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------------
# Initialize Gemini Model
# -------------------------------------------------------------------------
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0
)

# -------------------------------------------------------------------------
# TOOLS
# -------------------------------------------------------------------------
search_tool = DuckDuckGoSearchRun()

@tool(description="Perform basic arithmetic operations: add, sub, mul, div")
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    try:
        if operation == 'add':
            result = first_num + second_num
        elif operation == 'sub':
            result = first_num - second_num
        elif operation == 'mul':
            result = first_num * second_num
        elif operation == 'div':
            result = first_num / second_num
        else:
            return {'error': f"unsupported operation {operation}"}
        return {'first_num': first_num, 'second_num': second_num, 'operation': operation, 'result': result}
    except Exception as e:
        return {'error': str(e)}


@tool
def get_current_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool(description="Fetch latest stock price using Alpha Vantage API")
def get_stock_price(symbol: str) -> dict:
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=882S313O93X8BHQA'
    response = requests.get(url)
    return response.json()

@tool(description="Fetch current weather information using OpenWeatherMap API")
def get_weather(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "Missing OpenWeather API key."}
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            return {"error": data.get("message", "Failed to fetch weather data")}
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def find_local_events(city: str):
    """
    find local events for the given city using SERP API.

    args:
    city(str): city name(e.g. Delhi, Dehradun)_


    """
    try:
        url = f"https://serpapi.com/search.json?engine=google_events&q=Events in {city}&api_key={os.getenv('SERP_API_KEY')}"
        res = requests.get(url)
        return res.json()
    except Exception as e:
        return{"error": str(e)}


@tool
def get_news(topic: str):
    """Fetch latest news headlines"""

    url =f"https://newsapi.org/v2/everything?q={topic}&pageSize=5&sortBy=publishedAt&apiKey={os.getenv('NEWS_API')}"


    res = requests.get(url)
    data = res.json()

    if res.status_code != 200:
        return {"error": True, "message": data.get("message", "News error")}

    return data.get("articles", [])

# -------------------------------------------------------------------------
# Bind tools to LLM
# -------------------------------------------------------------------------
tools = [search_tool, get_stock_price, calculator, get_weather, find_local_events,get_news]
llm_with_tools = llm.bind_tools(tools)

# -------------------------------------------------------------------------
# Define LangGraph State with image integration
# -------------------------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

tool_node = ToolNode(tools)

# -------------------------------------------------------------------------
# Setup SQLite Checkpointer for LangGraph
# -------------------------------------------------------------------------
DB_PATH = "chatbot.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node('tools', tool_node)
graph.add_edge(START, "chat_node")
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

# -------------------------------------------------------------------------
# Database setup for thread titles and state
# -------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS stategraph (
        thread_id TEXT PRIMARY KEY,
        state_data TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS threads (
        thread_id TEXT PRIMARY KEY,
        title TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_thread_title(thread_id, title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO threads (thread_id, title)
        VALUES (?, ?)
        ON CONFLICT(thread_id) DO UPDATE SET title = excluded.title;
    """, (thread_id, title))
    conn.commit()
    conn.close()

def get_all_thread_titles():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT thread_id, title FROM threads")
    data = dict(c.fetchall())
    conn.close()
    return data

def retrieve_all_threads():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT thread_id FROM threads")
    threads = [row[0] for row in c.fetchall()]
    conn.close()
    return threads

def clear_chat(thread_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM stategraph WHERE thread_id = ?", (thread_id,))
    conn.commit()
    conn.close()

def clear_all_chats():
    """Delete all chats and threads from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM stategraph")
    c.execute("DELETE FROM threads")
    conn.commit()
    conn.close()
clear_all_chats()
