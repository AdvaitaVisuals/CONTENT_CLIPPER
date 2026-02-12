import requests
import json

url = "http://127.0.0.1:5000/webhook"
headers = {"Content-Type": "application/json"}

# Simulated WhatsApp Webhook Payload
payload = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "PHONE_NUMBER",
                            "phone_number_id": "PHONE_NUMBER_ID"
                        },
                        "contacts": [
                            {
                                "profile": {
                                    "name": "User Name"
                                },
                                "wa_id": "PHONE_NUMBER"
                            }
                        ],
                        "messages": [
                            {
                                "from": "919876543210",
                                "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSRUI1QjJDRjRDRUY5RjIwURE1AA==",
                                "timestamp": "1699999999",
                                "text": {
                                    "body": "Hello Biru Bhai"
                                },
                                "type": "text"
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
