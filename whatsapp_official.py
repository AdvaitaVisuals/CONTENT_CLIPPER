import os
import requests
import subprocess
import shutil
import time
from flask import Flask, request, jsonify
from openai import OpenAI
from agents.vizard_agent import VizardAgent
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CONFIG ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "bot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ADMIN_NUMBER = os.environ.get("ADMIN_NUMBER", "919599003069")
VIZARD_API_KEY = os.environ.get("VIZARD_API_KEY", "")

# Initialize
client_ai = OpenAI(api_key=OPENAI_API_KEY)
vizard_agent = VizardAgent(api_key=VIZARD_API_KEY)

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
    requests.post(url, headers=headers, json=payload)

def send_wa_video(to, video_url, caption):
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": {"link": video_url, "caption": caption}
    }
    requests.post(url, headers=headers, json=payload)

def talk_with_openai(user_message):
    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Biru Bhai AI, a funny and helpful assistant. Use a bit of Haryanvi/Desi style in your Hindi responses. You help users create viral reels using Vizard AI."},
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
                if not VIZARD_API_KEY:
                    send_wa_message(sender, "❌ Vizard API Key missing hai bhai! Admin se bolo setup kare.")
                    return "OK"

                parts = text.split()
                url = parts[1] if len(parts) > 1 else ""
                
                if not url:
                    send_wa_message(sender, "❌ Bhai link toh bhej! Example: /cut <URL>")
                    return "OK"

                send_wa_message(sender, "🚀 *Vizard AI active!* Video submit kar raha hoon, thoda sabar rakho... 🦾")

                project_id = vizard_agent.submit_video(url)
                if project_id:
                    send_wa_message(sender, f"✅ *Success!* Project ID: `{project_id}`\nAbhi Vizard process kar raha hai. Jaise hi clips ready ho jayenge, main polling shuru kar dunga ya aap web dashboard pe dekh sakte ho.")
                    
                    # Optional: Small wait and poll once for instant clips if video is small
                    # But for now, we just tell them it's submitted to avoid timeout on Vercel
                else:
                    send_wa_message(sender, "❌ Vizard submission fail ho gaya. Link check karo.")

            # 2. CHAT WITH OPENAI
            else:
                ai_reply = talk_with_openai(text)
                send_wa_message(sender, ai_reply)

    except Exception as e:
        print(f"Error handling webhook: {e}")

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)
