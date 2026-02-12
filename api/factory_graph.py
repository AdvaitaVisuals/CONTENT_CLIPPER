import os
import re
import json
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI
try:
    from .vizard_agent import VizardAgent
except ImportError:
    from vizard_agent import VizardAgent
import sqlite3

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    text: str
    sender: str
    source: str
    intent: str
    url: Optional[str]
    project_id: Optional[str]
    response: str
    clips: List[dict]

# --- UTILS ---
DB_PATH = 'biru_factory.db'

def log_to_db(source, sender, url, project_id, status='processing'):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (source, sender, url, project_id, status) VALUES (?, ?, ?, ?, ?)", 
                       (source, sender, url, project_id, status))
        conn.commit()
        conn.close()
    except: pass

# --- NODES ---

def analyzer_node(state: AgentState):
    text = state["text"]
    # Look specifically for video platforms
    video_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|vimeo\.com/|instagram\.com/reels?/|tiktok\.com/)[^\s<>"]+'
    urls = re.findall(video_pattern, text)
    
    # Fallback to any URL
    if not urls:
        urls = re.findall(r'https?://[^\s<>"]+', text)
    
    is_clipping_intent = any(kw in text.lower() for kw in ["clip", "cut", "banao", "bana", "video", "process", "factory", "nikal", "karo"])
    
    intent = "chat"
    detected_url = None
    
    if urls:
        detected_url = urls[0]
        # If it's just the URL or has clipping keywords, send to factory
        if is_clipping_intent or len(text.strip()) < (len(detected_url) + 10):
            intent = "clipping"
        
    return {"intent": intent, "url": detected_url}

def video_factory_node(state: AgentState):
    if not os.environ.get("VIZARD_API_KEY"):
        return {"response": "❌ Bhai, Vizard API Key missing hai. Admin ko bolo."}
    
    vizard = VizardAgent(api_key=os.environ.get("VIZARD_API_KEY"))
    project_id = vizard.submit_video(state["url"])
    
    if project_id:
        log_to_db(state["source"], state["sender"], state["url"], project_id)
        # Return status for caller to handle threading (or handle here if needed)
        return {
            "project_id": project_id,
            "response": f"🚀 **Bhai, factory shuru!**\n\nAapka video process hone bhej diya hai.\nProject ID: `{project_id}`\nMain nazar rakh raha hoon!"
        }
    else:
        return {"response": "❌ Bhai, factory mein koi dikakat aayi hai. Dubara try karo."}

def chat_node(state: AgentState):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are 'Biru Bhai ka Chela'. Understand Hindi, Urdu, English. Respond in short, respectful Hindi ('Aap', 'Bhai'). Your job is Video Clipping Factory. If someone asks about task status, tell them to check the Monitor Dashboard."},
            {"role": "user", "content": state["text"]}
        ]
    )
    return {"response": res.choices[0].message.content}

# --- GRAPH ASSEMBLY ---

def create_factory_graph():
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("clipper", video_factory_node)
    workflow.add_node("chat", chat_node)
    
    # Define Edges
    workflow.set_entry_point("analyzer")
    
    def route_intent(state):
        if state["intent"] == "clipping":
            return "clipper"
        return "chat"
    
    workflow.add_conditional_edges(
        "analyzer",
        route_intent,
        {
            "clipper": "clipper",
            "chat": "chat"
        }
    )
    
    workflow.add_edge("clipper", END)
    workflow.add_edge("chat", END)
    
    return workflow.compile()

# Singleton instance
factory_app = create_factory_graph()

def run_factory_agent(text, sender, source="web"):
    initial_state = {
        "text": text,
        "sender": sender,
        "source": source,
        "intent": "",
        "url": None,
        "project_id": None,
        "response": "",
        "clips": []
    }
    final_output = factory_app.invoke(initial_state)
    return final_output
