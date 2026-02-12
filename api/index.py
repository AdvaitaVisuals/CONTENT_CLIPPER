import os
import requests
import json
from flask import Flask, request
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
ADMIN_NUMBER = os.environ.get("ADMIN_NUMBER", "919599003069")

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

def talk_with_openai(user_message):
    if not OPENAI_API_KEY:
        return "Bhai, OpenAI Key nahi mil rahi. Admin se bolo fix kare!"
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Biru Bhai AI. Speak in Desi Hindi/Haryanvi style. You help people with Vizard AI clips."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error ho gaya bhai: {str(e)}"

@app.route("/", methods=["GET"])
def home():
    return "Biru Bhai AI is Live! 🚜", 200

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
        if "messages" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender = message["from"]
            text = message.get("text", {}).get("body", "")

            if not text: return "OK"

            if text.startswith("/cut"):
                if not VIZARD_API_KEY:
                    send_wa_message(sender, "❌ Vizard API Key missing!")
                    return "OK"
                
                vizard = VizardAgent(api_key=VIZARD_API_KEY)
                url = text.split()[1] if len(text.split()) > 1 else ""
                
                if not url:
                    send_wa_message(sender, "❌ Link bhej bhai!")
                else:
                    send_wa_message(sender, "🚀 *Vizard AI* ko video bhej diya hai! Project ID ka wait karo...")
                    project_id = vizard.submit_video(url)
                    if project_id:
                        send_wa_message(sender, f"✅ Done! Project ID: `{project_id}`")
                    else:
                        send_wa_message(sender, "❌ Kuch gadbad hui submission mein.")
            else:
                reply = talk_with_openai(text)
                send_wa_message(sender, reply)
    except:
        pass

    return "OK", 200

# For local testing only
if __name__ == "__main__":
    app.run(port=5000)
