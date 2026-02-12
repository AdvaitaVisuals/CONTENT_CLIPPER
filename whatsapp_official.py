import os
import requests
import subprocess
import shutil
from flask import Flask, request, jsonify
from openai import OpenAI
from agents import UnderstandingAgent, ViralCutterAgent
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CONFIG ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "bot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ADMIN_NUMBER = os.environ.get("ADMIN_NUMBER", "919599003069")

# Initialize
client_ai = OpenAI(api_key=OPENAI_API_KEY)
understanding_agent = UnderstandingAgent()
viral_cutter = ViralCutterAgent()

# --- UTILS ---
def send_wa_message(to, text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    print(f"Sending message to {to}...")
    r = requests.post(url, headers=headers, json=payload)
    print(f"Response: {r.status_code} - {r.text}")

def send_wa_video(to, media_id, caption):
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": {"id": media_id, "caption": caption}
    }
    requests.post(url, headers=headers, json=payload)

def upload_to_meta(file_path):
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"), "video/mp4"),
        "type": (None, "video/mp4"),
        "messaging_product": (None, "whatsapp"),
    }
    response = requests.post(url, headers=headers, files=files)
    return response.json().get("id")

def talk_with_openai(user_message):
    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Biru Bhai AI, a funny and helpful assistant. Use a bit of Haryanvi/Desi style in your Hindi responses. You help users create viral reels."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Arre bhai, dimaag kaam nahi kar raha thoda... (Error: {str(e)})"

# --- WEBHOOK ---
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        print(f"GET Request: mode={mode}, token={token}, challenge={challenge}")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Verification Success!")
            return challenge, 200
        print("❌ Verification Failed!")
        return "Forbidden", 403

    data = request.json
    print(f"Webhook Received: {data}")
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        if "messages" in value:
            message = value["messages"][0]
            sender = message["from"]
            text = message.get("text", {}).get("body", "")

            if not text: return "OK"

            # 1. COMMAND DETECT
            if text.startswith("/cut"):
                parts = text.split()
                url = parts[1] if len(parts) > 1 else ""
                count = int(parts[2]) if len(parts) > 2 else 3

                if not url:
                    send_wa_message(sender, "❌ Bhai link toh bhej! Example: /cut <link>")
                    return "OK"

                send_wa_message(sender, f"🚀 *Processing Video!* (Target: {count} clips)\nBiru Bhai Factory shuru ho gayi hai... 🦾")

                output_temp = "output/wa_official_temp"
                os.makedirs(output_temp, exist_ok=True)

                try:
                    command = ['yt-dlp', '-f', 'best[ext=mp4]/best', '-o', f'{output_temp}/%(title)s.%(ext)s', '--no-playlist', url]
                    subprocess.run(command, check=True)
                    files = [os.path.join(output_temp, f) for f in os.listdir(output_temp) if f.endswith('.mp4')]
                    video_path = max(files, key=os.path.getmtime)

                    audio_path = understanding_agent.extract_audio(video_path)
                    transcription = understanding_agent.transcribe_with_timestamps(audio_path)
                    beat_analysis = understanding_agent.detect_beat_drops(audio_path)
                    
                    understanding_data = {
                        "lyrics_segments": understanding_agent.tag_emotions(transcription.get('segments', [])),
                        "beat_analysis": beat_analysis
                    }
                    
                    clip_specs = viral_cutter.generate_clip_specs(understanding_data)
                    for i, spec in enumerate(clip_specs[:count]):
                        clip_path = os.path.join("output", "clips", f"wa_official_{i+1}.mp4")
                        os.makedirs(os.path.dirname(clip_path), exist_ok=True)
                        viral_cutter.cut_video(video_path, spec, clip_path)
                        
                        if os.path.exists(clip_path):
                            media_id = upload_to_meta(clip_path)
                            if media_id:
                                send_wa_video(sender, media_id, f"✅ Clip #{i+1}: {spec.viral_reason}")
                    
                    send_wa_message(sender, "🏁 *Task Complete!* Maze karo. 🚜")
                except Exception as e:
                    send_wa_message(sender, f"❌ Error: {str(e)}")
                finally:
                    if os.path.exists(output_temp):
                        shutil.rmtree(output_temp, ignore_errors=True)

            # 2. CHAT WITH OPENAI
            else:
                ai_reply = talk_with_openai(text)
                send_wa_message(sender, ai_reply)

    except Exception as e:
        print(f"Error handling webhook: {e}")

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
