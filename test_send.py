import requests

# Credentials (UPDATED)
WHATSAPP_TOKEN = "EAAT70fWiKnsBQh5wqF6QHuwrPcZA7fJ44ToEYWpAi4eAbcqZBwTZBUi5TKmeQZAEHNqUrPjecws65ZATJtt4fRsIeHWG8TzGqmtcq14SNzMNVvZBUW5MllXPxJnn8YRVV8MY3aKQZBYZCIQzrdFP6Ee5OZAIByGNBFJoBLEOMteBL0TPPYOrVGjuZAnBGxgcvSHq3MIq09dWI2qM78AXsMfj9b5kVL4vWd2FKZCCjsfqHjATnZBs7eJPFed3Vzkpb2QLGEsR3kPxSQHcMgIO1Kl529eN0Fps"
PHONE_ID = "971582372711272"
TO_NUMBER = "919599003069" 

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
        "text": {"body": "🔥 Hukum sar aankhon par! Naye Token se message aa gaya hai. Biru Bhai ka Chela active hai! 🦾"}
    }
    
    print(f"Sending message to {TO_NUMBER}...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ Success! Check your WhatsApp.")
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_message()
