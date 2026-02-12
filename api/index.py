import os
import requests
import json
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
try:
    from .vizard_agent import VizardAgent
except ImportError:
    from vizard_agent import VizardAgent

app = Flask(__name__)

# --- CONFIG ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "bot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
VIZARD_API_KEY = os.environ.get("VIZARD_API_KEY", "")

# --- PREMIUM DASHBOARD UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biru Bhai AI | Video Factory</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #FF3D00;
            --primary-glow: rgba(255, 61, 0, 0.4);
            --secondary: #2979FF;
            --bg-dark: #0A0A0B;
            --card-bg: rgba(20, 20, 22, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --text-main: #FFFFFF;
            --text-dim: #A0A0A5;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); height: 100vh; overflow: hidden; }

        /* Background Effects */
        .bg-glow {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background: radial-gradient(circle at 10% 20%, rgba(255, 61, 0, 0.05) 0%, transparent 40%),
                        radial-gradient(circle at 90% 80%, rgba(41, 121, 255, 0.05) 0%, transparent 40%);
        }

        .main-layout { display: grid; grid-template-columns: 280px 1fr 350px; height: 100vh; }

        /* Sidebar */
        aside {
            background: rgba(13, 13, 15, 0.8);
            border-right: 1px solid var(--border);
            padding: 40px 25px;
            display: flex; flex-direction: column; gap: 40px;
        }

        .brand { font-size: 28px; font-weight: 900; letter-spacing: -1.5px; color: var(--primary); display: flex; align-items: center; gap: 12px; }
        .brand i { font-size: 22px; color: var(--text-main); }

        .nav-links { display: flex; flex-direction: column; gap: 10px; }
        .nav-item {
            padding: 14px 20px; border-radius: 12px; color: var(--text-dim); text-decoration: none;
            display: flex; align-items: center; gap: 15px; font-weight: 500; transition: 0.3s;
        }
        .nav-item:hover, .nav-item.active { background: rgba(255, 255, 255, 0.05); color: var(--text-main); }
        .nav-item.active { border-left: 4px solid var(--primary); color: var(--primary); background: rgba(255, 61, 0, 0.05); }

        /* Content Area */
        main { padding: 40px; overflow-y: auto; }
        .section-header { margin-bottom: 30px; }
        .section-header h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
        .section-header p { color: var(--text-dim); }

        /* Video Factory Card */
        .factory-card {
            background: var(--card-bg); backdrop-filter: blur(15px);
            border: 1px solid var(--border); border-radius: 24px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3); margin-bottom: 40px;
        }

        .input-group { position: relative; display: flex; gap: 15px; }
        .input-group input {
            flex: 1; background: rgba(0,0,0,0.2); border: 2px solid var(--border);
            padding: 20px 25px; border-radius: 16px; color: white; font-size: 16px; outline: none; transition: 0.3s;
        }
        .input-group input:focus { border-color: var(--primary); box-shadow: 0 0 20px var(--primary-glow); }

        .btn-factory {
            background: var(--primary); color: white; border: none; padding: 0 35px; border-radius: 16px;
            font-weight: 700; cursor: pointer; transition: 0.3s; font-size: 16px;
        }
        .btn-factory:hover { transform: translateY(-3px); box-shadow: 0 10px 20px var(--primary-glow); }

        /* Project Grid */
        .grid-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .project-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .project-card {
            background: var(--card-bg); border: 1px solid var(--border); border-radius: 20px;
            padding: 20px; display: flex; flex-direction: column; gap: 15px; position: relative;
        }
        .project-status { position: absolute; top: 15px; right: 15px; font-size: 11px; padding: 4px 10px; border-radius: 20px; background: rgba(0, 230, 118, 0.1); color: #00E676; }

        /* Right Panel (Chat) */
        .chat-panel {
            background: rgba(13, 13, 15, 0.8);
            border-left: 1px solid var(--border);
            display: flex; flex-direction: column;
        }
        .chat-header { padding: 30px; border-bottom: 1px solid var(--border); font-weight: 700; }
        #chat-messages { flex: 1; padding: 25px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { padding: 12px 18px; border-radius: 18px; max-width: 85%; font-size: 15px; line-height: 1.4; }
        .msg.ai { align-self: flex-start; background: rgba(255,255,255,0.05); color: #DDD; }
        .msg.user { align-self: flex-end; background: var(--secondary); color: white; }

        .chat-input-area { padding: 25px; border-top: 1px solid var(--border); display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; background: rgba(0,0,0,0.2); border: 1px solid var(--border); padding: 12px 18px; border-radius: 12px; color: white; outline: none; }
        .btn-chat { background: var(--text-main); color: var(--bg-dark); border: none; border-radius: 12px; padding: 0 15px; cursor: pointer; }

        /* Loader / Typing Animation */
        .typing-bubble {
            background: rgba(255,255,255,0.05);
            padding: 12px 18px;
            border-radius: 18px;
            display: flex;
            gap: 5px;
            width: fit-content;
            margin-bottom: 15px;
        }
        .dot {
            width: 8px;
            height: 8px;
            background: var(--text-dim);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    <div class="main-layout">
        <!-- Sidebar -->
        <aside>
            <div class="brand">
                <i class="fas fa-tractor"></i>
                BIRU BHAI
            </div>
            <nav class="nav-links">
                <a href="#" class="nav-item active"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a href="#" class="nav-item"><i class="fas fa-video"></i> Video Factory</a>
                <a href="#" class="nav-item"><i class="fas fa-scissors"></i> Clipper</a>
                <a href="#" class="nav-item"><i class="fas fa-magic"></i> AI Strategies</a>
                <a href="#" class="nav-item"><i class="fas fa-cog"></i> Settings</a>
            </nav>
        </aside>

        <!-- Main Content (Video Factory) -->
        <main>
            <div class="section-header">
                <h1>Video Factory 🦾</h1>
                <p>Paste your long video link and let the AI extract viral moments.</p>
            </div>

            <div class="factory-card">
                <div class="input-group">
                    <input type="text" id="video-url" placeholder="Paste YouTube Link (e.g. https://youtu.be/...)">
                    <button class="btn-factory" onclick="startFactory()">START FACTORY</button>
                </div>
            </div>

            <div class="grid-header">
                <h2>Recent Projects</h2>
                <span style="color: var(--text-dim); font-size: 14px;">Total: <span id="proj-count">0</span></span>
            </div>

            <div class="project-grid" id="project-list">
                <!-- Project Cards go here -->
                <div class="project-card">
                    <div class="project-status">READY</div>
                    <div style="font-weight: 600;">YouTube Clip Analysis</div>
                    <div style="color: var(--text-dim); font-size: 13px;">ID: #vzd_8921...</div>
                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                        <button style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: white; padding: 8px; border-radius: 8px; cursor: pointer; font-size: 12px;">View Clips</button>
                    </div>
                </div>
            </div>
        </main>

        <!-- Right Panel (AI Assistant) -->
        <div class="chat-panel">
            <div class="chat-header">Biru Bhai ka Chela 🧠</div>
            <div id="chat-messages">
                <div class="msg ai">Ram Ram ji! 👋 Main Biru Bhai ka chela hoon. Biru Bhai ne aapki sewa ke liye mujhe yahan rakha hai.<br><br>Aap batayein, aapki kya madad kar sakta hoon? Aap koi bhi video link bhej sakte hain, main turant Biru Bhai ki factory mein bhej dunga.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chat-query" placeholder="Aapka kya hukum hai..." onkeypress="handleChatEnter(event)">
                <button class="btn-chat" onclick="sendChatMessage()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-messages');

        function appendChat(text, isUser) {
            const div = document.createElement('div');
            div.className = `msg ${isUser ? 'user' : 'ai'}`;
            div.innerHTML = text.replace(/\\n/g, '<br>');
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'typing-bubble';
            div.id = 'typing-indicator';
            div.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
            chatContainer.appendChild(div);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        function hideTyping() {
            const indicator = document.getElementById('typing-indicator');
            if(indicator) indicator.remove();
        }

        async function sendChatMessage() {
            const input = document.getElementById('chat-query');
            const text = input.value.trim();
            if(!text) return;
            appendChat(text, true);
            input.value = '';
            
            showTyping();
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                hideTyping();
                appendChat(data.reply, false);
            } catch {
                hideTyping();
                appendChat("Maaf kijiyega, lagta hai koi takneeki kharabi hai.", false);
            }
        }

        function handleChatEnter(e) { if(e.key === 'Enter') sendChatMessage(); }

        async function startFactory() {
            const urlInput = document.getElementById('video-url');
            const url = urlInput.value.trim();
            if(!url) return;
            
            appendChat(`/cut ${url}`, true);
            urlInput.value = '';
            
            showTyping();
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: `/cut ${url}` })
            });
            const data = await res.json();
            hideTyping();
            appendChat(data.reply, false);
        }
    </script>
</body>
</html>
"""

# --- UTILS ---
def send_wa_message(to, text):
    if not PHONE_ID or not WHATSAPP_TOKEN: return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, headers=headers, json=payload)

def handle_logic(text):
    if text.startswith("/cut"):
        if not VIZARD_API_KEY:
            return "❌ Maaf kijiye, Vizard API Key missing hai. Aap admin se sampark karein."
        
        parts = text.split()
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            return "❌ Aap kripya link toh bhejिये! Jaise ki: `/cut https://youtu.be/...`"

        try:
            vizard = VizardAgent(api_key=VIZARD_API_KEY)
            project_id = vizard.submit_video(url)
            if project_id:
                return f"🚀 **Hukum sar aankhon par!**\\nAapka video maine Biru Bhai ki factory mein bhej diya hai.\\n**Project ID:** `{project_id}`\\n\\nKripya thoda dhairya rakhein, kaam shuru ho gaya hai."
            else:
                return "❌ Maaf kijiye, submission mein koi dikakat aayi hai."
        except Exception as e:
            return f"❌ Kshama kijiye, error aaya hai: {str(e)}"
    
    if not OPENAI_API_KEY: return "Ram Ram! Main Biru Bhai ka chela hoon, par bina OpenAI key ke main baatein nahi kar sakta."
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are 'Biru Bhai ka Chela' (Biru Bhai's Assistant/Disciple). You are extremely respectful and always address the user as 'Aap' (honorific). Your tone should be polite and formal, but with a slight Desi/Haryanvi touch that reflects your loyalty to Biru Bhai. You help users process videos using Vizard AI. Example: 'Aap kaise hain?', 'Aap batayein kya hukum hai?'"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Arre maaf kijiye, error aa gaya: {str(e)}"

# --- ROUTES ---
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_UI)

@app.route("/api/chat", methods=["POST"])
def web_chat():
    data = request.json
    reply = handle_logic(data.get("message", ""))
    return jsonify({"reply": reply})

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    data = request.json
    try:
        value = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
        if "messages" in value:
            msg = value["messages"][0]
            reply = handle_logic(msg.get("text", {}).get("body", ""))
            send_wa_message(msg["from"], reply)
    except: pass
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
