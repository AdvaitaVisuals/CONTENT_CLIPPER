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

# --- HTML UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biru Bhai AI | Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #FF3D00;
            --secondary: #2979FF;
            --bg: #050505;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        
        body { 
            background: var(--bg); 
            color: white; 
            overflow: hidden;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* Background Glows */
        .glow {
            position: absolute;
            width: 400px;
            height: 400px;
            background: var(--primary);
            filter: blur(150px);
            opacity: 0.15;
            z-index: -1;
            animation: pulse 10s infinite alternate;
        }
        .glow-top { top: -10%; left: -10%; }
        .glow-bottom { bottom: -10%; right: -10%; background: var(--secondary); }

        @keyframes pulse {
            0% { transform: scale(1); opacity: 0.1; }
            100% { transform: scale(1.5); opacity: 0.2; }
        }

        /* Main Container */
        .container {
            width: 90%;
            max-width: 1000px;
            height: 85vh;
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 30px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            position: relative;
        }

        /* Header */
        header {
            padding: 25px 40px;
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(90deg, #FF3D00, #FFEA00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #AAA;
        }

        .pulse-dot {
            width: 10px;
            height: 10px;
            background: #00E676;
            border-radius: 50%;
            box-shadow: 0 0 10px #00E676;
            animation: blink 1.5s infinite;
        }

        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        /* Chat Area */
        #chat-window {
            flex: 1;
            padding: 30px 40px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 20px;
            font-size: 16px;
            line-height: 1.5;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .ai-msg {
            align-self: flex-start;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-bottom-left-radius: 5px;
        }

        .user-msg {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--secondary), #00B0FF);
            color: white;
            border-bottom-right-radius: 5px;
        }

        /* Input Area */
        .input-area {
            padding: 30px 40px;
            border-top: 1px solid var(--glass-border);
            display: flex;
            gap: 15px;
        }

        input {
            flex: 1;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--glass-border);
            padding: 18px 25px;
            border-radius: 15px;
            color: white;
            font-size: 16px;
            outline: none;
            transition: 0.3s;
        }

        input:focus { border-color: var(--secondary); background: rgba(255,255,255,0.06); }

        button {
            background: white;
            color: black;
            border: none;
            padding: 0 30px;
            border-radius: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }

        button:hover { background: var(--secondary); color: white; transform: translateY(-2px); }

        /* Loader */
        .typing { font-style: italic; color: #888; font-size: 13px; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="glow glow-top"></div>
    <div class="glow glow-bottom"></div>

    <div class="container">
        <header>
            <div class="logo">BIRU BHAI AI</div>
            <div class="status">
                <div class="pulse-dot"></div>
                FACTORY ONLINE
            </div>
        </header>

        <div id="chat-window">
            <div class="message ai-msg">Ram Ram bhai! 👋 Main hoon Biru Bhai AI. <br><br>Mere se chat bhi kar sake hai aur `/cut URL` bhej ke clips bhi banwa sake hai. Bata ke sewa karu?</div>
        </div>

        <div class="input-area">
            <input type="text" id="user-input" placeholder="Aaun de message... (e.g. /cut https://youtu.be/...)" onkeypress="handleEnter(event)">
            <button onclick="sendMessage()">SEND</button>
        </div>
    </div>

    <script>
        const chatWindow = document.getElementById('chat-window');
        const userInput = document.getElementById('user-input');

        function appendMessage(text, isUser) {
            const div = document.createElement('div');
            div.className = `message ${isUser ? 'user-msg' : 'ai-msg'}`;
            div.innerHTML = text.replace(/\\n/g, '<br>');
            chatWindow.appendChild(div);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        function handleEnter(e) { if (e.key === 'Enter') sendMessage(); }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            appendMessage(text, true);
            userInput.value = '';

            const typing = document.createElement('div');
            typing.className = 'typing';
            typing.innerText = 'Biru Bhai soch raha hai...';
            chatWindow.appendChild(typing);

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                typing.remove();
                appendMessage(data.reply, false);
            } catch (err) {
                typing.remove();
                appendMessage("Arre bhai, network mein thodi gadbad hai!", false);
            }
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
    """Core logic shared between WhatsApp and Web UI"""
    if text.startswith("/cut"):
        if not VIZARD_API_KEY:
            return "❌ Vizard API Key missing hai bhai! Admin se bolo setup kare."
        
        parts = text.split()
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            return "❌ Bhai link toh bhej! Example: `/cut https://youtu.be/...`"

        vizard = VizardAgent(api_key=VIZARD_API_KEY)
        project_id = vizard.submit_video(url)
        if project_id:
            return f"🚀 **Vizard AI active!**\\nYour project has been submitted.\\n**Project ID:** `{project_id}`\\n\\nProcessing shuru ho gayi hai, thoda sabar rakho!"
        else:
            return "❌ Vizard submission fail ho gaya. Link sahi hai kya?"
    
    # AI Chat
    if not OPENAI_API_KEY:
        return "👋 Main hoon Biru Bhai! AI baatein karne ke liye OpenAI key mang rahi hai."
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Biru Bhai AI. Speak in Desi Hindi/Haryanvi style. You help people with Vizard AI clips."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error ho gaya bhai: {str(e)}"

# --- ROUTES ---
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_UI)

@app.route("/api/chat", methods=["POST"])
def web_chat():
    data = request.json
    user_text = data.get("message", "")
    reply = handle_logic(user_text)
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
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        if "messages" in value:
            message = value["messages"][0]
            sender = message["from"]
            text = message.get("text", {}).get("body", "")
            if text:
                reply = handle_logic(text)
                send_wa_message(sender, reply)
    except:
        pass
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
