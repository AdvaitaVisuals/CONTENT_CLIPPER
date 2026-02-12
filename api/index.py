import os
import requests
import json
import re
import threading
import time
import sqlite3
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from openai import OpenAI

import sys
# Add project root to sys.path so we can import 'agents'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LangGraph Integration
try:
    from api.factory_graph import run_factory_agent
except ImportError:
    try:
        from factory_graph import run_factory_agent
    except ImportError:
        # Last resort for direct execution
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from api.factory_graph import run_factory_agent

app = Flask(__name__)

@app.route('/outputs/<project_id>/<path:filename>')
def serve_output(project_id, filename):
    work_dir = f"output_{project_id}"
    reels_dir = os.path.join(work_dir, "reels")
    return send_from_directory(os.path.abspath(reels_dir), filename)

# --- CONFIG ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_ID = os.environ.get("PHONE_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "bot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VIZARD_API_KEY = os.environ.get("VIZARD_API_KEY")

DB_PATH = 'biru_factory.db'

# --- DB HELPERS ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, sender TEXT, url TEXT, project_id TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, clips_json TEXT)''')
    conn.commit()
    conn.close()

def update_db_task(project_id, status, clips=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if clips:
            cursor.execute("UPDATE tasks SET status=?, clips_json=? WHERE project_id=?", (status, json.dumps(clips), project_id))
        else:
            cursor.execute("UPDATE tasks SET status=? WHERE project_id=?", (status, project_id))
        conn.commit()
        conn.close()
    except Exception as e: print(f"❌ [DB UPDATE ERROR] {e}")

init_db()

# --- LOCAL PROCESSING LOGIC ---
def run_local_processor(project_id, url, sender):
    print(f"🚜 [FACTORY] Starting Local Engine for Project: {project_id}")
    update_db_task(project_id, "processing")
    
    try:
        # We run the process_video.py as a subprocess to keep it clean
        # Output will be in output/reels
        import subprocess
        
        # We create a TEMP directory for this project to avoid collisions if multiple tasks
        work_dir = f"output_{project_id}"
        os.makedirs(work_dir, exist_ok=True)
        
        cmd = ["python", "process_video.py", url, "--output_dir", work_dir]
        print(f"🏃 [RUNNING]: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Feed progress to console but also keep moving
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print(f"✅ [DONE] Project {project_id} finished successfully.")
            
            # Check for clips in reels folder
            reels_dir = os.path.join(work_dir, "reels")
            clips = []
            if os.path.exists(reels_dir):
                for f in os.listdir(reels_dir):
                    if f.endswith(".mp4"):
                        # In the real world, we'd need to serve this file via ngrok/public URL
                        # For now, we simulate the structure
                        clips.append({
                            "title": f,
                            "videoUrl": f"/outputs/{project_id}/{f}" # Mock URL
                        })
            
            update_db_task(project_id, "completed", clips=clips)
            
            if sender and sender != "Admin_Web":
                send_wa_message(sender, f"✅ **Bhai, factory ka maal ready hai!** (Local Engine)\nClips generate ho gayi hain. Dashboard check karo.")
        else:
            print(f"❌ [FAIL] Project {project_id} error: {stderr}")
            update_db_task(project_id, "failed")
            if sender and sender != "Admin_Web":
                send_wa_message(sender, "❌ Bhai, factory mein error aa gaya. Local logs check karo.")

    except Exception as e:
        print(f"❌ [CORE ERROR] {e}")
        update_db_task(project_id, "failed")

def poll_and_send_clips(project_id, sender, url=None):
    # This is a wrapper for the local processor now
    thread = threading.Thread(target=run_local_processor, args=(project_id, url, sender))
    thread.daemon = True
    thread.start()

def send_wa_message(to, text):
    if not PHONE_ID or not WHATSAPP_TOKEN: return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, headers=headers, json=payload)

# --- CORE HANDLER (LANGRAPH) ---
def handle_universal(text, sender, source):
    # RUN LANGRAPH AGENT
    output = run_factory_agent(text, sender, source)
    
    response = output.get("response", "Bhai dimaag ghum gaya mera.")
    project_id = output.get("project_id")
    url = output.get("url")
    
    # If a new project was started, trigger local processor
    if project_id:
        poll_and_send_clips(project_id, sender, url)
    
    # Also log to terminal
    print(f"🤖 [CHELA]: {response}")
    return response

# --- DASHBOARD UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biru Bhai Admin | Monitoring Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --primary: #FF3D00; --bg: #080809; --card: #121214; --border: rgba(255,255,255,0.08); --dim: #94949E; }
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Outfit', sans-serif; }
        body { background: var(--bg); color: white; display: flex; height: 100vh; overflow: hidden; }

        /* Sidebar */
        aside { width: 280px; border-right: 1px solid var(--border); padding: 30px; display: flex; flex-direction: column; background: #0A0A0B; }
        .logo { font-size: 24px; font-weight: 900; color: var(--primary); margin-bottom: 50px; display:flex; align-items:center; gap:10px; }
        .nav { display: flex; flex-direction: column; gap: 10px; flex: 1; }
        .nav-item { padding: 15px; border-radius: 12px; color: var(--dim); text-decoration: none; font-weight: 600; transition: 0.3s; cursor: pointer; display:flex; align-items:center; gap:12px; }
        .nav-item:hover, .nav-item.active { color: white; background: rgba(255,255,255,0.05); }
        .nav-item.active { color: var(--primary); }

        /* Main Content */
        main { flex: 1; padding: 40px; overflow-y: auto; background: radial-gradient(circle at top right, rgba(255, 61, 0, 0.03), transparent); }
        h1 { font-size: 32px; font-weight: 800; margin-bottom: 30px; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 25px; transition: 0.3s; }
        .card:hover { border-color: var(--primary); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }

        /* Monitor Table */
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { text-align: left; color: var(--dim); font-size: 13px; padding-bottom: 15px; border-bottom: 1px solid var(--border); }
        td { padding: 18px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
        .badge { padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 11px; text-transform: uppercase; }
        .badge.completed { background: rgba(0,255,127,0.1); color: #00FF7F; }
        .badge.processing, .badge.submitting { background: rgba(255,165,0,0.1); color: orange; }

        /* Progress Bar */
        .progress-container { width: 100%; background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 5px; position: relative; }
        .progress-bar { height: 100%; background: var(--primary); width: 0%; transition: width 0.5s ease; border-radius: 4px; box-shadow: 0 0 10px var(--primary); }
        .progress-text { font-size: 10px; color: var(--dim); margin-top: 4px; font-weight: 600; }

        /* Chat Panel */
        .chat-panel { width: 380px; border-left: 1px solid var(--border); background: #0D0D0F; display: flex; flex-direction: column; }
        .chat-head { padding: 25px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .chat-msgs { flex: 1; padding: 25px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { padding: 12px 18px; border-radius: 16px; font-size: 14px; line-height: 1.5; max-width: 85%; }
        .msg.ai { background: rgba(255,255,255,0.05); align-self: flex-start; }
        .msg.user { background: var(--primary); align-self: flex-end; }
        .chat-input { padding: 20px; border-top: 1px solid var(--border); display: flex; gap: 10px; }
        .chat-input input { flex: 1; background: rgba(0,0,0,0.2); border: 1px solid var(--border); color: white; padding: 12px; border-radius: 10px; outline: none; }
    </style>
</head>
<body>
    <aside>
        <div class="logo"><i class="fas fa-tractor"></i> BIRU ADMIN</div>
        <div class="nav">
            <div class="nav-item active" onclick="go('factory')"><i class="fas fa-industry"></i> Factory</div>
            <div class="nav-item" onclick="go('dash')"><i class="fas fa-desktop"></i> Monitor</div>
            <div class="nav-item" onclick="go('clipper')"><i class="fas fa-scissors"></i> Results</div>
            <div class="nav-item" onclick="go('strat')"><i class="fas fa-magic"></i> AI Strategy</div>
        </div>
    </aside>

    <main>
        <div id="p-factory" class="page active">
            <h1>Video Factory 🏭</h1>
            <div class="card" style="max-width: 600px;">
                <p style="color:var(--dim); margin-bottom:15px;">Enter a YouTube URL to start the clipping engine manually.</p>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="factory-url" placeholder="Paste YouTube Link here..." style="flex:1; padding:12px; background:rgba(0,0,0,0.3); border:1px solid var(--border); color:white; border-radius:8px;">
                    <button onclick="submitFactory()" style="background:var(--primary); color:white; border:none; padding:12px 25px; border-radius:8px; cursor:pointer; font-weight:700;">START 🚀</button>
                </div>
                <div id="factory-status" style="margin-top:20px; color:#00FF7F; font-weight:600;"></div>
            </div>
        </div>

        <div id="p-dash" class="page" style="display:none;">
            <h1>Process Monitoring Log 📡</h1>
            <div class="card" style="width: 100%;">
                <table>
                    <thead>
                        <tr><th>TIME</th><th>FROM</th><th>SOURCE</th><th>PROJECT</th><th>STATUS / PROGRESS</th></tr>
                    </thead>
                    <tbody id="log-body"></tbody>
                </table>
            </div>
        </div>

        <div id="p-clipper" class="page" style="display:none;">
            <h1>Factory Results 🎞️</h1>
            <div id="clip-results"></div>
        </div>

        <div id="p-strat" class="page" style="display:none;">
            <h1>Viral Strategy Engine 🧠</h1>
            <div class="card">
                <p style="color:var(--dim); margin-bottom:20px;">AI is analyzing latest trends for you.</p>
                <button onclick="askStrategy()" style="background:var(--primary); color:white; border:none; padding:12px 20px; border-radius:8px; cursor:pointer; font-weight:700;">Generate Viral Strategy</button>
                <div id="strat-box" style="margin-top:25px; background:rgba(255,255,255,0.02); padding:20px; border-radius:12px; color:#DDD; line-height:1.6;"></div>
            </div>
        </div>
    </main>

    <div class="chat-panel">
        <div class="chat-head">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:8px; height:8px; background:#00FF7F; border-radius:50%; box-shadow:0 0 10px #00FF7F;"></div>
                <span style="font-weight:700;">Biru ka Chela</span>
            </div>
        </div>
        <div class="chat-msgs" id="chat-msgs">
            <div class="msg ai">Ram Ram Bhai! Main yahan hun. Kuch poocho?</div>
        </div>
        <div class="chat-input">
            <input type="text" id="chat-in" placeholder="Type command..." onkeypress="if(event.key=='Enter')send()">
            <button onclick="send()" style="background:none; border:none; color:white; cursor:pointer;"><i class="fas fa-paper-plane"></i></button>
        </div>
    </div>

    <script>
        function go(p) {
            document.querySelectorAll('.page').forEach(x=>x.style.display='none');
            // Remove active from all nav items
            document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));
            // Show target page
            document.getElementById('p-'+p).style.display='block';
            
            // Highlight nav item (simple hack: find by text content or index)
            // For now, assume clicked element handles it via 'event', or we re-select based on index
            // But since 'go' is called inline, 'event.currentTarget' works if triggered by click
            if(window.event) window.event.currentTarget.classList.add('active');
            
            if(p=='dash') refresh();
            if(p=='clipper') refreshClips();
        }

        async function submitFactory() {
            const url = document.getElementById('factory-url').value;
            if(!url) return alert("URL to daalo bhai!");
            
            document.getElementById('factory-status').innerText = "Working on it...";
            
            // We simulate a chat message "Clip this: URL"
            const r = await fetch('/api/chat', {
                method:'POST', 
                headers:{'Content-Type':'application/json'}, 
                body:JSON.stringify({message: "Clip this video: " + url})
            });
            const d = await r.json();
            document.getElementById('factory-status').innerText = "✅ Started! Check Monitoring tab.";
            document.getElementById('factory-url').value = "";
            append(d.reply, false); // Add to chat log too
        }

        async function refresh() {
            const r = await fetch('/api/tasks');
            const data = await r.json();
            document.getElementById('log-body').innerHTML = data.map(t => {
                let progress = 0;
                if(t.status === 'completed') progress = 100;
                else if(t.status === 'processing') progress = Math.min(95, Math.floor(Math.random() * 40) + 30); // Mocking for now
                else if(t.status === 'submitting') progress = 15;
                
                return `
                <tr>
                    <td>${t.timestamp.split(' ')[1]}</td>
                    <td>${t.sender}</td>
                    <td>${t.source}</td>
                    <td><a href="${t.url}" target="_blank" style="color:var(--text-dim); text-decoration:none; font-size:11px;">${t.url.substring(0,30)}...</a><br><code>${t.project_id}</code></td>
                    <td>
                        <span class="badge ${t.status}">${t.status}</span>
                        ${t.status !== 'completed' && t.status !== 'failed' ? `
                        <div class="progress-container">
                            <div class="progress-bar" style="width: ${progress}%"></div>
                        </div>
                        <div class="progress-text">Processing: ${progress}%</div>
                        ` : ''}
                    </td>
                </tr>
            `}).join('');
        }

        async function refreshClips() {
            const r = await fetch('/api/tasks');
            const data = await r.json();
            const list = document.getElementById('clip-results');
            const filtered = data.filter(t => t.clips_json);
            if(!filtered.length) { list.innerHTML = "No clips yet."; return; }
            list.innerHTML = filtered.map(t => {
                const clips = JSON.parse(t.clips_json);
                return `
                    <div class="card" style="margin-bottom:20px;">
                        <h3 style="margin-bottom:15px;">Project: ${t.project_id}</h3>
                        ${clips.map(c => `
                            <div style="padding:15px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                                <span>${c.title}</span>
                                <a href="${c.videoUrl}" style="color:var(--primary); font-weight:700;" target="_blank">Download</a>
                            </div>
                        `).join('')}
                    </div>
                `;
            }).join('');
        }

        async function send() {
            const i = document.getElementById('chat-in');
            const v = i.value.trim(); if(!v) return;
            append(v, true); i.value='';
            const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:v})});
            const d = await r.json();
            append(d.reply, false);
            refresh();
        }

        function append(t, u) {
            const b = document.getElementById('chat-msgs');
            const d = document.createElement('div');
            d.className = `msg ${u?'user':'ai'}`;
            d.innerHTML = t.replace(/\\n/g, '<br>');
            b.appendChild(d); b.scrollTop = b.scrollHeight;
        }

        async function askStrategy() {
            const b = document.getElementById('strat-box');
            b.innerHTML = "Bhai analysis ho rha hai...";
            const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:"Bhai mast viral strategy btao reels ke liye short mein"})});
            const d = await r.json();
            b.innerHTML = d.reply;
        }

        setInterval(() => { if(document.getElementById('p-dash').style.display!='none') refresh(); }, 8000);
        refresh();
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_UI)

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY timestamp DESC LIMIT 30")
        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    reply = handle_universal(data.get("message", ""), "Admin_Web", "web")
    return jsonify({"reply": reply})

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN: return request.args.get("hub.challenge"), 200
        return "Forbidden", 403
    
    data = request.json
    try:
        msg_val = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = msg_val["from"]
        
        # 2. Handle Text
        if "text" in msg_val:
            text = msg_val["text"]["body"]
            print(f"📩 [WA-MSG] {sender} said: {text}")
            reply = handle_universal(text, sender, "whatsapp")
            send_wa_message(sender, reply)
            
    except Exception as e: 
        print(f"Webhook error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
