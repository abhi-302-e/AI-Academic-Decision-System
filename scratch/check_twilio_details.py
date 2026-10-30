import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip(" \"'")
token = os.getenv("TWILIO_AUTH_TOKEN", "").strip(" \"'")

from twilio.rest import Client
try:
    client = Client(sid, token)
    print("Checking Twilio Messaging Services:")
    services = client.messaging.v1.services.list(limit=5)
    for s in services:
        print(f"  Service SID: {s.sid}, Name: {s.friendly_name}")
        phone_nums = client.messaging.v1.services(s.sid).phone_numbers.list()
        for p in phone_nums:
            print(f"    Phone in service: {p.phone_number} ({p.sid})")

    print("\nChecking Twilio WhatsApp Senders:")
    # In Twilio Sandbox, the standard WhatsApp number is whatsapp:+14155238886
    # Let's inspect messages or usage records if any
    try:
        messages = client.messages.list(limit=5)
        print("Recent Messages Sent/Received:")
        for m in messages:
            print(f"  SID: {m.sid}, From: {m.from_}, To: {m.to}, Status: {m.status}")
    except Exception as me:
        print("Error listing messages:", me)

except Exception as e:
    print("Twilio error:", e)
