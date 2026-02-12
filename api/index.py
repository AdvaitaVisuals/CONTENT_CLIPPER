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
VIZARD_API_KEY = os.environ.get("VIZARD_API_KEY", "")

DB_PATH = '/tmp/biru_factory.db' if os.environ.get("VERCEL") else 'biru_factory.db'

# --- DB HELPERS ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    if not cursor.fetchone():
        cursor.execute('''CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, sender TEXT, url TEXT, project_id TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, clips_json TEXT, provider TEXT, external_id TEXT)''')
    else:
        # Migration for existing tables
        try: cursor.execute("ALTER TABLE tasks ADD COLUMN provider TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE tasks ADD COLUMN external_id TEXT")
        except: pass
    conn.commit()
    conn.close()

def update_db_task(project_id, status, clips=None, provider=None, external_id=None, error_msg=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        final_status = status
        if error_msg:
            final_status = f"failed: {str(error_msg)[:100]}"
            
        # Dynamically build the UPDATE query
        fields = ["status=?"]
        params = [final_status]
        
        if clips is not None:
            fields.append("clips_json=?")
            params.append(json.dumps(clips))
        
        if provider:
            fields.append("provider=?")
            params.append(provider)
            
        if external_id:
            fields.append("external_id=?")
            params.append(external_id)
            
        params.append(project_id)
        query = f"UPDATE tasks SET {', '.join(fields)} WHERE project_id=?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
    except Exception as e: print(f"❌ [DB UPDATE ERROR] {e}")

init_db()

# --- VIZARD PROCESSING (CLOUD) ---
def run_vizard_processor(project_id, url, sender):
    import traceback
    print(f"☁️ [FACTORY] Submitting to Vizard AI: {project_id}")
    
    # VALIDATE API KEY
    if not VIZARD_API_KEY:
        print("❌ [CONFIG ERROR] Vizard API Key missing.")
        update_db_task(project_id, "failed", error_msg="MISSING VIZARD_API_KEY. Add it to Vercel Environment Variables.")
        return

    try:
        from agents.vizard_agent import VizardAgent
        agent = VizardAgent(api_key=VIZARD_API_KEY)
        
        # Submit to Vizard
        vizard_id = agent.submit_video(url)
        
        if vizard_id:
            print(f"✅ [VIZARD] Submitted. ID: {vizard_id}")
            update_db_task(project_id, "processing", provider="vizard", external_id=vizard_id)
        else:
            print(f"❌ [VIZARD] Failed to submit.")
            update_db_task(project_id, "failed", error_msg="Vizard API rejected submission (Check Quota/URL)")
            
    except Exception as e:
        traceback.print_exc()
        err_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ [VIZARD ERROR] {err_msg}")
        update_db_task(project_id, "failed", error_msg=err_msg)

# --- LOCAL PROCESSING LOGIC (Full 8-Agent Pipeline) ---
def run_local_processor(project_id, url, sender):
    import traceback
    print(f"🚜 [FACTORY] Starting Full 8-Agent Pipeline: {project_id}")
    update_db_task(project_id, "processing", provider="local")

    try:
        if os.environ.get("VERCEL"):
            print("❌ [FAIL] Cannot run Local Engine on Vercel. Use Vizard Mode.")
            update_db_task(project_id, "failed", error_msg="Local Engine Blocked on Vercel. Please use Cloud Mode.")
            return

        from orchestrator import ArtistOrchestrator
        orch = ArtistOrchestrator(output_base="output", vizard_api_key=VIZARD_API_KEY)
        result = orch.process(
            video_source=url,
            project_id=project_id,
            use_cloud=False
        )

        if result.get("status") in ("completed", "completed_with_warnings"):
            print(f"✅ [DONE] Project {project_id} - {result.get('clips_count', 0)} clips")

            # Collect clip files for DB
            clips = []
            work_dir = os.path.join("output", project_id)
            clips_dir = os.path.join(work_dir, "clips")
            reels_dir = os.path.join(work_dir, "reels")

            for d in [reels_dir, clips_dir]:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        if f.endswith(".mp4"):
                            clips.append({"title": f, "videoUrl": f"/outputs/{project_id}/{f}"})

            update_db_task(project_id, "completed", clips=clips)

            # WhatsApp notification with strategy summary
            if sender and sender != "Admin_Web":
                summary = orch.get_whatsapp_summary(project_id)
                send_wa_message(sender, summary)
        else:
            errors = ", ".join(result.get("errors", [])[:2])
            print(f"❌ [FAIL] Project {project_id}: {errors}")
            update_db_task(project_id, "failed", error_msg=errors)

    except Exception as e:
        traceback.print_exc()
        err_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ [LOCAL ERROR] {err_msg}")
        update_db_task(project_id, "failed", error_msg=err_msg)

def start_processing_thread(project_id, sender, url, use_cloud=False):
    target = run_vizard_processor if use_cloud else run_local_processor
    thread = threading.Thread(target=target, args=(project_id, url, sender))
    thread.daemon = True
    thread.start()

def send_wa_message(to, text):
    if not PHONE_ID or not WHATSAPP_TOKEN: return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, headers=headers, json=payload)

@app.route("/api/sync_vizard/<project_id>", methods=["GET"])
def sync_vizard(project_id):
    """Checks Vizard status, updates DB, and notifies WhatsApp if needed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,))
        task = cur.fetchone()
        conn.close()
        
        if not task or task['provider'] != 'vizard' or task['status'] == 'completed':
            return jsonify({"status": task['status'] if task else "unknown"})
            
        # Check Vizard
        from agents.vizard_agent import VizardAgent
        agent = VizardAgent(api_key=VIZARD_API_KEY)
        v_status = agent.status_check(task['external_id'])

        if v_status == "completed":
            v_clips = agent.get_clips(task['external_id'])
            clips = []
            for c in v_clips:
                clips.append({
                    "title": c.get("title", "Vizard Clip"),
                    "videoUrl": c.get("videoUrl", ""),
                    "viralScore": c.get("viralScore", "")
                })
            
            update_db_task(project_id, "completed", clips=clips)
            
            # --- WHATSAPP NOTIFICATION ---
            if task['source'] == 'whatsapp' and task['sender']:
                msg = f"✅ *Factory Task Complete!* (Project: {project_id})\n\n"
                msg += f"Bhai, Vizard ne {len(clips)} clips bana di hain. View karne ke liye dashboard pe jao ya ye download link dekho:\n"
                if clips:
                    msg += f"📥 Top Clip: {clips[0]['videoUrl']}"
                send_wa_message(task['sender'], msg)
            
            return jsonify({"status": "completed", "clips": clips})
        elif v_status == "error":
            update_db_task(project_id, "failed", error_msg="Vizard processing error")
            return jsonify({"status": "failed"})

        return jsonify({"status": "processing_remote"})
        
    except Exception as e:
        print(f"❌ [SYNC ERROR] {e}")
        return jsonify({"error": str(e)}), 500

# --- CORE HANDLER ---
def handle_universal(text, sender, source, use_cloud=False):
    # RUN LANGRAPH AGENT
    output = run_factory_agent(text, sender, source)
    
    response = output.get("response", "Bhai dimaag ghum gaya mera.")
    project_id = output.get("project_id")
    url = output.get("url")
    
    # Force Cloud if on Vercel
    if os.environ.get("VERCEL"):
        use_cloud = True

    # LOG TO DB - ALWAYS, for chat sync (storing msg in 'url' field and reply in 'status' for sync)
    if not project_id:
        from api.factory_graph import log_to_db # Ensure import for pure chat logging
        log_to_db(source, sender, text, f"CHAT_{int(time.time())}", status=response)

    # If a new project was started
    if project_id:
        if use_cloud:
            response += "\n\n(☁️ Charging into Cloud Engine - Vizard AI)"
            if os.environ.get("VERCEL"):
                # VERCEL FIX: Run Synchronously! Background threads die instantly on Serverless.
                print("⚡ [VERCEL] Running Vizard Submission Synchronously...")
                # Update status with current response for the logger
                update_db_task(project_id, response, provider="vizard") 
                run_vizard_processor(project_id, url, sender)
            else:
                update_db_task(project_id, "submitting", provider="vizard")
                start_processing_thread(project_id, sender, url, use_cloud)
        else:
            if os.environ.get("VERCEL"):
                response += "\n\n⚠️ Local Engine blocked on Vercel. Using Cloud."
                update_db_task(project_id, response, provider="vizard")
                run_vizard_processor(project_id, url, sender)
            else:
                update_db_task(project_id, "submitting", provider="local")
                start_processing_thread(project_id, sender, url, use_cloud=False)
    
    print(f"🤖 [{source}] replying to {sender}: {response[:50]}...")
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
        td { padding: 18px 0; border-bottom: 1px solid var(--border); font-size: 14px; vertical-align: top; }
        .badge { padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 11px; text-transform: uppercase; display: inline-block; margin-bottom: 5px; }
        .badge.completed { background: rgba(0,255,127,0.1); color: #00FF7F; }
        .badge.failed { background: rgba(255,0,0,0.1); color: #FF4444; }
        .badge.processing, .badge.submitting { background: rgba(255,165,0,0.1); color: orange; }
        .error-msg { font-size: 11px; color: #FF4444; display: block; max-width: 250px; white-space: normal; }

        /* Progress Bar */
        .progress-container { width: 100%; background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 5px; position: relative; }
        .progress-bar { height: 100%; background: var(--primary); width: 0%; transition: width 0.5s ease; border-radius: 4px; box-shadow: 0 0 10px var(--primary); }
        .progress-text { font-size: 10px; color: var(--dim); margin-top: 4px; font-weight: 600; }

        /* Results UI */
        .clip-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .clip-card { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 20px; position: relative; }
        .delete-btn { position: absolute; top: 15px; right: 15px; color: var(--dim); cursor: pointer; transition: 0.3s; }
        .delete-btn:hover { color: #FF4444; }

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
        <div class="logo"><i class="fas fa-tractor"></i> BIRU ADMIN (v3.1)</div>
        <div class="nav">
            <div class="nav-item active" onclick="go('factory')"><i class="fas fa-industry"></i> Factory</div>
            <div class="nav-item" onclick="go('dash')"><i class="fas fa-desktop"></i> Monitor</div>
            <div class="nav-item" onclick="go('clipper')"><i class="fas fa-scissors"></i> Results</div>
            <div class="nav-item" onclick="go('strat')"><i class="fas fa-magic"></i> AI Strategy</div>
        </div>
    </aside>

    <div class="chat-panel">
        <div class="chat-head">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:8px; height:8px; background:#00FF7F; border-radius:50%; box-shadow:0 0 10px #00FF7F;"></div>
                <span style="font-weight:700;">Biru ka Chela</span>
            </div>
        </div>
        <div class="chat-msgs" id="chat-msgs">
            <div class="msg ai">Ram Ram Bhai! Welcome to Biru Bhai 3.0. Main aapka video factory assistant hoon.</div>
        </div>
        <div class="chat-input">
            <input type="text" id="chat-in" placeholder="Type command..." onkeypress="if(event.key=='Enter')send()">
            <button onclick="send()" style="background:none; border:none; color:white; cursor:pointer;"><i class="fas fa-paper-plane"></i></button>
        </div>
    </div>

    <!-- MAIN CONTENT AREA -->
    <main>
        <!-- FACTORY PAGE -->
        <div id="p-factory" class="page active">
            <h1>Video Factory 🏭</h1>
            <div class="card" style="max-width: 800px;">
                <p style="color:var(--dim); margin-bottom:15px;">Paste a YouTube link to start the Clipping Engine.</p>
                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <input type="text" id="factory-url" placeholder="https://youtube.com/watch?v=..." style="flex:1; padding:12px; background:rgba(0,0,0,0.3); border:1px solid var(--border); color:white; border-radius:8px;">
                    <button onclick="submitFactory()" style="background:var(--primary); color:white; border:none; padding:12px 25px; border-radius:8px; cursor:pointer; font-weight:700;">START 🚀</button>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <input type="checkbox" id="use-cloud" checked> 
                    <label for="use-cloud" style="color:var(--dim); font-size:14px; cursor:pointer;">Use Cloud Engine (Vizard AI) - <b>Recommended for Vercel</b></label>
                </div>
            </div>
        </div>

        <!-- MONITOR PAGE -->
        <div id="p-dash" class="page" style="display:none;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
                <h1>Process Monitoring Log 📡</h1>
                <button onclick="refresh()" style="background:none; border:1px solid var(--border); color:var(--dim); padding:8px 15px; border-radius:8px; cursor:pointer;"><i class="fas fa-sync"></i> Sync</button>
            </div>
            <div class="card" style="width: 100%;">
                <table>
                    <thead>
                        <tr><th>TIME</th><th>FROM</th><th>SOURCE</th><th>PROJECT</th><th>STATUS / PROGRESS</th><th>ACTIONS</th></tr>
                    </thead>
                    <tbody id="log-body"></tbody>
                </table>
            </div>
        </div>

        <!-- RESULTS PAGE -->
        <div id="p-clipper" class="page" style="display:none;">
            <h1>Clipped Results 🎬</h1>
            <div id="clip-results" class="clip-grid">Loading results...</div>
        </div>

        <!-- STRATEGY PAGE -->
        <div id="p-strat" class="page" style="display:none;">
            <h1>Viral Strategy Engine 🧠</h1>
            <div class="grid">
                <div class="card">
                    <h3>📈 Trend Intelligence</h3>
                    <button onclick="askBot('Analyze current Haryanvi trends and give a report')" style="background:var(--primary); width:100%; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:700; margin-bottom:10px; margin-top:20px;">📊 ANALYZE TRENDS</button>
                    <div id="trend-box" style="margin-top:15px; font-size:14px; color:#DDD;"></div>
                </div>

                <div class="card">
                    <h3>📅 Content Calendar</h3>
                    <button onclick="askBot('Generate a content calendar for next week based on my clips')" style="background:#00FF7F; width:100%; color:black; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:700; margin-bottom:10px; margin-top:20px;">🗓️ MAKE CALENDAR</button>
                    <div id="calendar-box" style="margin-top:15px; font-size:14px; color:#DDD;"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        function go(p) {
            document.querySelectorAll('.page').forEach(x=>x.style.display='none');
            document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));
            document.getElementById('p-'+p).style.display='block';
            
            // Highlight nav item
            const items = document.querySelectorAll('.nav-item');
            if(p === 'factory') items[0].classList.add('active');
            if(p === 'dash') items[1].classList.add('active');
            if(p === 'clipper') items[2].classList.add('active');
            if(p === 'strat') items[3].classList.add('active');
            
            if(p=='dash') refresh();
            if(p=='clipper') refreshClips();
        }

        async function submitFactory() {
            const url = document.getElementById('factory-url').value;
            const useCloud = document.getElementById('use-cloud').checked;
            if(!url) return alert("URL to daalo bhai!");
            
            const r = await fetch('/api/chat', {
                method:'POST', 
                headers:{'Content-Type':'application/json'}, 
                body:JSON.stringify({ message: "Clip this video: " + url, use_cloud: useCloud })
            });
            const d = await r.json();
            document.getElementById('factory-url').value = "";
            append(d.reply, false); 
            go('dash');
        }

        async function deleteTask(pid) {
            if(!confirm("Bhai, delete kar doon?")) return;
            const r = await fetch('/api/delete_task/' + pid, { method: 'DELETE' });
            if(r.ok) {
                refresh();
                refreshClips();
            }
        }

        async function refresh() {
            const r = await fetch('/api/tasks');
            const data = await r.json();
            
            data.forEach(t => {
                const statusBase = t.status.split(':')[0].trim().toLowerCase();
                if(statusBase === 'processing' && t.provider === 'vizard') fetch('/api/sync_vizard/' + t.project_id);
            });

            document.getElementById('log-body').innerHTML = data.map(t => {
                let progress = 0;
                let statusParts = t.status.split(':');
                let statusMain = statusParts[0].trim().toUpperCase();
                let statusError = statusParts.length > 1 ? statusParts.slice(1).join(':').trim() : "";
                
                let statusClass = statusMain.toLowerCase();
                if(statusClass === 'completed') progress = 100;
                else if(statusClass === 'processing' || statusClass === 'submitting') progress = 45; 
                
                return `
                <tr>
                    <td>${t.timestamp.split(' ')[1]}</td>
                    <td>${t.sender}</td>
                    <td>${t.provider ? t.provider.toUpperCase() : 'LOCAL'}</td>
                    <td><a href="${t.url}" target="_blank" style="color:var(--dim); text-decoration:none; font-size:11px;">${t.url.substring(0,25)}...</a><br><code>${t.project_id}</code></td>
                    <td>
                        <span class="badge ${statusClass}">${statusMain}</span>
                        ${statusError ? `<div class="error-msg">${statusError}</div>` : ''}
                        ${statusClass === 'processing' || statusClass === 'submitting' ? `
                        <div class="progress-container"><div class="progress-bar" style="width: ${progress}%"></div></div>
                        ` : ''}
                    </td>
                    <td>
                        <i class="fas fa-trash delete-btn" onclick="deleteTask('${t.project_id}')"></i>
                    </td>
                </tr>
            `}).join('');
        }

        let lastChatCount = 0;
        async function refreshChats() {
            const r = await fetch('/api/recent_chats');
            const data = await r.json();
            const box = document.getElementById('chat-msgs');
            
            // Only re-render if count changed to avoid flickering
            if(data.length === lastChatCount) return;
            lastChatCount = data.length;

            box.innerHTML = data.map(c => `
                <div class="msg user" style="${c.sender === 'Admin_Web' ? '' : 'background: #333'}">
                    <div style="font-size:10px; opacity:0.6; margin-bottom:4px;">${c.sender} (${c.source})</div>
                    ${c.msg_text}
                </div>
                <div class="msg ai">${c.ai_reply}</div>
            `).join('');
            box.scrollTop = box.scrollHeight;
        }

        async function refreshClips() {
            const r = await fetch('/api/tasks');
            const data = await r.json();
            const list = document.getElementById('clip-results');
            
            if(!data.length) { list.innerHTML = "<p style='color:var(--dim)'>No tasks found.</p>"; return; }
            
            list.innerHTML = data.map(t => {
                const clips = t.clips_json ? JSON.parse(t.clips_json) : [];
                return `
                    <div class="clip-card">
                        <i class="fas fa-trash delete-btn" onclick="deleteTask('${t.project_id}')"></i>
                        <h3 style="margin-bottom:10px; font-size:16px;">${t.project_id}</h3>
                        <p style="font-size:12px; color:var(--dim); margin-bottom:15px;">Source: ${t.provider || 'Local'}</p>
                        
                        ${clips.length > 0 ? clips.map(c => `
                            <div style="padding:10px 0; border-top:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:13px;">${c.title}</span>
                                <a href="${c.videoUrl}" style="color:var(--primary); font-weight:700; font-size:12px;" target="_blank">VIEW</a>
                            </div>
                        `).join('') : `<p style="color:orange; font-size:13px;">Status: ${t.status}</p>`}
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

        async function askBot(prompt) {
            let container = 'trend-box';
            if(prompt.includes('calendar')) container = 'calendar-box';
            const box = document.getElementById(container);
            box.innerText = "Analyzing...";
            const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message: prompt})});
            const d = await r.json();
            box.innerText = d.reply;
        }

        setInterval(() => { 
            if(document.getElementById('p-dash').style.display!='none') refresh(); 
            refreshChats();
        }, 5000);
        refresh();
        refreshChats();
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
        
        # PROACTIVE SYNC: Trigger Vizard check if needed
        # Since we're in a browser polling loop, we can trigger background syncs
        import requests
        for t in data:
            status_clean = str(t['status']).split(':')[0].lower()
            if t['provider'] == 'vizard' and status_clean not in ('completed', 'failed'):
                 # Check locally if it's running 
                 threading.Thread(target=requests.get, args=(f"http://localhost:5000/api/sync_vizard/{t['project_id']}",)).start()

        return jsonify(data)
    except Exception as e:
        print(f"Error in get_tasks: {e}")
        return jsonify([])

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    use_cloud = data.get("use_cloud", False)
    reply = handle_universal(data.get("message", ""), "Admin_Web", "web", use_cloud=use_cloud)
    return jsonify({"reply": reply})

@app.route("/api/project/<project_id>", methods=["GET"])
def get_project_detail(project_id):
    """Get full orchestrator pipeline result for a project"""
    try:
        from orchestrator import ArtistOrchestrator
        orch = ArtistOrchestrator(output_base="output")
        status = orch.get_project_status(project_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        print(f"🔹 [WEBHOOK VERIFY] mode={mode}, token={'***' if token else 'MISSING'}, challenge={challenge}", flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ [WEBHOOK] Verification SUCCESS", flush=True)
            from flask import Response
            return Response(challenge, status=200, content_type="text/plain")

        print(f"❌ [WEBHOOK] Verification FAILED. Expected token: '{VERIFY_TOKEN}', Got: '{token}'", flush=True)
        return "Forbidden", 403

    data = request.json
    print(f"🔹 [WEBHOOK RAW]: {json.dumps(data)[:300]}", flush=True)

    try:
        if "entry" in data and data["entry"]:
            entry = data["entry"][0]
            if "changes" in entry and entry["changes"]:
                changes = entry["changes"][0]
                if "value" in changes and changes["value"]:
                    val = changes["value"]

                    # Skip status updates (delivery receipts etc.)
                    if "statuses" in val:
                        print("🔹 [INFO] Status update received (delivery/read receipt). Skipping.", flush=True)
                        return "OK", 200

                    if "messages" in val and val["messages"]:
                        msg_val = val["messages"][0]
                        sender = msg_val["from"]

                        if "text" in msg_val:
                            text = msg_val["text"]["body"]
                            print(f"📩 [WA-MSG] {sender} said: {text}", flush=True)

                            # For WhatsApp on Vercel: process but don't block on Vizard
                            reply = handle_universal(text, sender, "whatsapp", use_cloud=True)
                            send_wa_message(sender, reply)
                            print(f"📤 [REPLY SENT] to {sender}", flush=True)
                        else:
                            print(f"🔹 [INFO] Non-text message type: {msg_val.get('type', 'unknown')}", flush=True)
                    else:
                        print("🔹 [INFO] No 'messages' in value.", flush=True)
                else:
                    print("🔹 [INFO] No 'value' in changes.", flush=True)
            else:
                print("🔹 [INFO] No 'changes' in entry.", flush=True)
        else:
            print("🔹 [INFO] No 'entry' in data.", flush=True)

    except Exception as e:
        print(f"❌ [WEBHOOK ERROR]: {e}", flush=True)
        import traceback
        traceback.print_exc()

    return "OK", 200

@app.route("/api/recent_chats", methods=["GET"])
def get_recent_chats():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Fetch last 50 interactions, including those without URLs (pure chats)
        cur.execute("SELECT sender, source, url as msg_text, status as ai_reply, timestamp FROM tasks ORDER BY timestamp DESC LIMIT 50")
        data = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(data[::-1]) # Return in chronological order for chat
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/delete_task/<project_id>", methods=["DELETE"])
def delete_task(project_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    """Diagnostic endpoint to verify deployment and config"""
    return jsonify({
        "status": "ok",
        "version": "v3.0",
        "config": {
            "WHATSAPP_TOKEN": "SET" if WHATSAPP_TOKEN else "MISSING",
            "PHONE_ID": "SET" if PHONE_ID else "MISSING",
            "VERIFY_TOKEN": VERIFY_TOKEN,
            "VIZARD_API_KEY": "SET" if VIZARD_API_KEY else "MISSING",
            "OPENAI_API_KEY": "SET" if OPENAI_API_KEY else "MISSING",
            "ON_VERCEL": bool(os.environ.get("VERCEL"))
        }
    })

if __name__ == "__main__":
    app.run(port=5000)
