import requests

# Credentials
WHATSAPP_TOKEN = "EAAT70fWiKnsBQnJ4ZCxrBSRXyZAL5iZBkDAQwjWw437waHIOkcDJdNksc2ZCq9VmWYelWFKSCNURMgDiVsT3fVvOk1vjrOUyabEGnuLuNK83oeruAZAz8XJJkIFlEZA7IiSQ52uZBLqCZAW85rYbwwH1BxKYgEHWoUFVPmbaTGyXT4c4cT3y5BkCaekzySpxIigrP3tzNA1ZB9h9xTPmHRDKlaZCc7Yi4Jmt4I6mb5Mg6AZAlEFrgrAF3Sq1j1s88bdDeCnaxcjeXgkXPGgQ0ugfPbTeYZCJ7AZDZD"
PHONE_ID = "971582372711272"
TO_NUMBER = "919599003069" # <--- Apna number yahan dalein (with country code)

def send_test_message():
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "text",
        "text": {"body": "🔥 Arre bhai! Biru Bhai Factory se message aaya hai. System UP hai! 🦾"}
    }
    
    print(f"Sending message to {TO_NUMBER}...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ Success! Check your WhatsApp.")
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    if "X" in TO_NUMBER:
        print("Bhai, pehle 'TO_NUMBER' mein apna number toh daalo!")
    else:
        send_test_message()
