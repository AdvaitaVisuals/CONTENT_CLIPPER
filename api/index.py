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

# --- PREMIUM DASHBOARD UI (SPA Version) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biru Bhai AI | Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #FF3D00;
            --primary-glow: rgba(255, 61, 0, 0.4);
            --secondary: #2979FF;
            --bg-dark: #080809;
            --card-bg: rgba(25, 25, 28, 0.6);
            --border: rgba(255, 255, 255, 0.1);
            --text-main: #FFFFFF;
            --text-dim: #94949E;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); height: 100vh; overflow: hidden; }

        .bg-glow {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background: radial-gradient(circle at 10% 20%, rgba(255, 61, 0, 0.05) 0%, transparent 40%),
                        radial-gradient(circle at 90% 80%, rgba(41, 121, 255, 0.05) 0%, transparent 40%);
        }

        /* Top Navigation Header */
        header {
            height: 80px;
            background: rgba(13, 13, 15, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 40px;
            position: fixed; top: 0; width: 100%; z-index: 100;
        }

        .brand { font-size: 26px; font-weight: 900; letter-spacing: -1px; color: var(--primary); display: flex; align-items: center; gap: 12px; cursor: pointer; }
        .brand i { color: white; font-size: 20px; }

        nav { display: flex; gap: 30px; }
        .nav-link { 
            color: var(--text-dim); text-decoration: none; font-weight: 600; font-size: 15px; 
            transition: 0.3s; padding: 8px 15px; border-radius: 8px; cursor: pointer;
        }
        .nav-link:hover, .nav-link.active { color: white; background: rgba(255,255,255,0.05); }
        .nav-link.active { color: var(--primary); }

        .main-container {
            display: grid; grid-template-columns: 1fr 380px; 
            height: calc(100vh - 80px); margin-top: 80px;
        }

        /* Content Sections */
        .content-area { padding: 40px; overflow-y: auto; }
        .section { display: none; animation: fadeIn 0.4s ease-out; }
        .section.active { display: block; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* Dashboard Home View */
        .dash-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; margin-top: 30px; }
        .dash-card {
            background: var(--card-bg); border: 1px solid var(--border); border-radius: 20px;
            padding: 35px; border-radius: 24px; cursor: pointer; transition: 0.3s;
            display: flex; flex-direction: column; gap: 20px;
        }
        .dash-card:hover { transform: translateY(-5px); border-color: var(--primary); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .dash-card i { font-size: 32px; color: var(--primary); }
        .dash-card h3 { font-size: 22px; font-weight: 700; }
        .dash-card p { color: var(--text-dim); line-height: 1.5; font-size: 14px; }

        /* Video Factory UI */
        .factory-box { background: var(--card-bg); padding: 40px; border-radius: 24px; border: 1px solid var(--border); margin-top: 20px; }
        .url-input-container { display: flex; gap: 15px; }
        .url-input-container input {
            flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--border); padding: 18px 25px;
            border-radius: 14px; color: white; font-size: 16px; outline: none; transition: 0.3s;
        }
        .url-input-container input:focus { border-color: var(--primary); box-shadow: 0 0 15px var(--primary-glow); }
        .btn-action { 
            background: var(--primary); color: white; border: none; padding: 0 30px; border-radius: 14px; 
            font-weight: 700; cursor: pointer; transition: 0.3s; 
        }
        .btn-action:hover { transform: scale(1.05); box-shadow: 0 5px 15px var(--primary-glow); }

        /* Right Chat Panel */
        .chat-panel {
            background: rgba(10, 10, 12, 0.95);
            border-left: 1px solid var(--border);
            display: flex; flex-direction: column;
        }
        .chat-header { padding: 25px 30px; border-bottom: 1px solid var(--border); font-weight: 700; display: flex; align-items: center; gap: 10px; }
        .chat-header .status-dot { width: 8px; height: 8px; background: #00E676; border-radius: 50%; box-shadow: 0 0 10px #00E676; }
        
        #chat-messages { flex: 1; padding: 25px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { padding: 14px 18px; border-radius: 18px; max-width: 85%; font-size: 15px; line-height: 1.4; }
        .msg.ai { align-self: flex-start; background: rgba(255,255,255,0.05); color: #DDD; border-bottom-left-radius: 4px; }
        .msg.user { align-self: flex-end; background: var(--secondary); color: white; border-bottom-right-radius: 4px; }
        
        /* Typing Animation */
        .typing { display: flex; gap: 4px; padding: 12px; }
        .dot { width: 6px; height: 6px; background: #888; border-radius: 50%; animation: blink 1.4s infinite both; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1); } }

        .chat-input { padding: 20px; border-top: 1px solid var(--border); display: flex; gap: 10px; }
        .chat-input input { flex: 1; background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 12px 18px; border-radius: 10px; color: white; outline: none; }
        .btn-send { background: white; color: black; border: none; border-radius: 10px; padding: 0 15px; cursor: pointer; transition: 0.3s; }
        .btn-send:hover { background: var(--primary); color: white; }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    
    <header>
        <div class="brand" onclick="showSection('dash')">
            <i class="fas fa-tractor"></i>
            BIRU BHAI
        </div>
        <nav>
            <div class="nav-link active" id="nav-dash" onclick="showSection('dash')">Dashboard</div>
            <div class="nav-link" id="nav-factory" onclick="showSection('factory')">Video Factory</div>
            <div class="nav-link" id="nav-clipper" onclick="showSection('clipper')">Clipper</div>
            <div class="nav-link" id="nav-strategies" onclick="showSection('strategies')">Strategies</div>
            <div class="nav-link" id="nav-settings" onclick="showSection('settings')">Settings</div>
        </nav>
    </header>

    <div class="main-container">
        <!-- Content Area -->
        <main class="content-area">
            
            <!-- Dashboard Home -->
            <div id="section-dash" class="section active">
                <h1 style="font-size: 36px; font-weight: 800; margin-bottom: 30px;">Ram Ram Bhai! 👋</h1>
                <div class="dash-grid">
                    <div class="dash-card" onclick="showSection('factory')">
                        <i class="fas fa-video"></i>
                        <h3>Video Factory</h3>
                        <p>Long videos se viral clips nikalne ke liye yahan YouTube link bhejिये. Biru Bhai ki factory turant kaam shuru kar degi.</p>
                    </div>
                    <div class="dash-card" onclick="showSection('clipper')">
                        <i class="fas fa-scissors"></i>
                        <h3>Clip Editor</h3>
                        <p>Clips ko review karein, trim kareine aur viral tags add karein. Automation ka asli maza yahan hai.</p>
                    </div>
                    <div class="dash-card" onclick="showSection('strategies')">
                        <i class="fas fa-magic"></i>
                        <h3>AI Strategies</h3>
                        <p>Agli viral strategy kya honi chahiye? Humare AI se salah lein aur apna content plan karein.</p>
                    </div>
                    <div class="dash-card" onclick="showSection('settings')">
                        <i class="fas fa-cog"></i>
                        <h3>System Settings</h3>
                        <p>WhatsApp API, Vizard Keys aur OpenAI tokens ko configure karein. Poora control aapke hath mein.</p>
                    </div>
                </div>
            </div>

            <!-- Video Factory -->
            <div id="section-factory" class="section">
                <h1 style="font-size: 32px; font-weight: 800; margin-bottom: 10px;">Video Factory 🦾</h1>
                <p style="color: var(--text-dim); margin-bottom: 30px;">Aapka ek link, Biru Bhai ke sau viral clips.</p>
                <div class="factory-box">
                    <div class="url-input-container">
                        <input type="text" id="v-url" placeholder="Paste YouTube/Video URL here...">
                        <button class="btn-action" onclick="runFactory()">PROCESS NOW</button>
                    </div>
                </div>
                <div style="margin-top: 40px;">
                    <h2 style="margin-bottom: 20px;">Live Processing Queue</h2>
                    <div style="background: var(--card-bg); padding: 30px; border-radius: 18px; border: 1px dashed var(--border); text-align: center; color: var(--text-dim);">
                        Abhi koi active task nahi hai. Link daalein aur magic dekhein!
                    </div>
                </div>
            </div>

            <!-- Other placeholders -->
            <div id="section-clipper" class="section">
                <h1>Clip Management ✂️</h1>
                <p style="color: var(--text-dim); margin-top: 20px;">Yahan aapke saare processed clips show honge. (Work in Progress)</p>
            </div>
            <div id="section-strategies" class="section">
                <h1>Viral Strategies 📈</h1>
                <p style="color: var(--text-dim); margin-top: 20px;">AI abhi trend ka analysis kar raha hai. Jaldi hi update milega!</p>
            </div>
            <div id="section-settings" class="section">
                <h1>Configuration ⚙️</h1>
                <p style="color: var(--text-dim); margin-top: 20px;">Aap apne environment variables Vercel se manage kar sakte hain.</p>
            </div>

        </main>

        <!-- Right Panel (Chela) -->
        <div class="chat-panel">
            <div class="chat-header">
                <div class="status-dot"></div>
                Biru Bhai ka Chela
            </div>
            <div id="chat-messages">
                <div class="msg ai">Ram Ram Bhai! 👋 Main Biru Bhai ka chela hoon. Aap batao kya kaam karna hai?</div>
            </div>
            <div class="chat-input">
                <input type="text" id="c-input" placeholder="Kuch poochiye..." onkeypress="handleEnter(event)">
                <button class="btn-send" onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

    <script>
        function showSection(id) {
            // Hide all sections
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            
            // Show selected
            document.getElementById('section-'+id).classList.add('active');
            document.getElementById('nav-'+id).classList.add('active');
        }

        const msgBox = document.getElementById('chat-messages');

        function appendMsg(text, isUser) {
            const div = document.createElement('div');
            div.className = `msg ${isUser ? 'user' : 'ai'}`;
            div.innerHTML = text.replace(/\\n/g, '<br>');
            msgBox.appendChild(div);
            msgBox.scrollTop = msgBox.scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'msg ai typing';
            div.id = 'typing-dot';
            div.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
            msgBox.appendChild(div);
            msgBox.scrollTop = msgBox.scrollHeight;
        }

        function hideTyping() {
            const d = document.getElementById('typing-dot');
            if(d) d.remove();
        }

        async function sendChat() {
            const inp = document.getElementById('c-input');
            const txt = inp.value.trim();
            if(!txt) return;
            appendMsg(txt, true);
            inp.value = '';
            
            showTyping();
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: txt })
                });
                const d = await res.json();
                hideTyping();
                appendMsg(d.reply, false);
            } catch {
                hideTyping();
                appendMsg("Kshama kijiye, chela thoda thak gaya hai!", false);
            }
        }

        function handleEnter(e) { if(e.key === 'Enter') sendChat(); }

        async function runFactory() {
            const uInput = document.getElementById('v-url');
            const url = uInput.value.trim();
            if(!url) return;
            appendMsg(`/cut ${url}`, true);
            uInput.value = '';
            
            showTyping();
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: `/cut ${url}` })
            });
            const d = await res.json();
            hideTyping();
            appendMsg(d.reply, false);
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
            return "❌ Bhai, Vizard API Key nahi mil rahi. Admin se bolo."
        parts = text.split()
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            return "❌ Bhai, pehle link toh bhej!"
        try:
            vizard = VizardAgent(api_key=VIZARD_API_KEY)
            project_id = vizard.submit_video(url)
            if project_id:
                return f"🚀 **Bhai, factory shuru!**\\nVideo bhej diya hai. Project ID: `{project_id}`"
            else:
                return "❌ Bhai, link bhenjne mein dikakat aayi hai."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    if not OPENAI_API_KEY: return "Ram Ram Bhai! OpenAI key nahi hai, chat kaise karun?"
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are 'Biru Bhai ka Chela'. \n\nCAPABILITIES:\n1. Understand Hindi, Urdu, and English perfectly.\n\nRESPONSE RULES:\n1. Always respond in short, respectful Hindi/Desi style using 'Aap'.\n2. Address the user as 'Bhai'. Example: 'Bhai, batao kya kaam karna hai?'\n3. Keep messages VERY SHORT. No long explanations or Urdu honorifics like 'Hukum/Maaf'.\n4. Your main job is converting video links into 5-10 viral clips using `/cut <URL>`.\n5. If a user sends a voice note, just reply to the content directly without repeating what they said."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Maaf kijiye, chela error de gaya: {str(e)}"

def get_media_url(media_id):
    url = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.json().get("url")

def download_media(media_url, save_path):
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(media_url, headers=headers)
    with open(save_path, "wb") as f:
        f.write(r.content)

def transcribe_audio(file_path):
    if not OPENAI_API_KEY: return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        audio_file = open(file_path, "rb")
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        print(f"Transcription Error: {e}")
        return None

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
            sender = msg["from"]
            
            # 1. HANDLE VOICE NOTE
            if "audio" in msg:
                audio_id = msg["audio"]["id"]
                media_url = get_media_url(audio_id)
                if media_url:
                    # Save temporarily in /tmp for Vercel
                    temp_path = f"/tmp/{audio_id}.ogg"
                    download_media(media_url, temp_path)
                    text = transcribe_audio(temp_path)
                    if text:
                        reply = handle_logic(text)
                        send_wa_message(sender, reply)
                    else:
                        send_wa_message(sender, "❌ Bhai, awaaz samajh nahi aayi. Dubara bolo.")
                    if os.path.exists(temp_path): os.remove(temp_path)
                else:
                    send_wa_message(sender, "❌ Maaf kijiye, audio download nahi ho paya.")

            # 2. HANDLE TEXT
            elif "text" in msg:
                text = msg.get("text", {}).get("body", "")
                reply = handle_logic(text)
                send_wa_message(sender, reply)
    except Exception as e: 
        print(f"Webhook Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
