import os, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from dotenv import load_dotenv
load_dotenv(dotenv_path=root / ".env", override=True)

sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip(" \"'")
token = os.getenv("TWILIO_AUTH_TOKEN", "").strip(" \"'")

from twilio.rest import Client
client = Client(sid, token)

print("Listing Content Templates (ContentSid):")
try:
    contents = client.content.v1.contents.list(limit=10)
    for c in contents:
        print(f"  SID: {c.sid}, FriendlyName: {c.friendly_name}, Language: {c.language}")
    if not contents:
        print("  No custom content templates found.")
except Exception as e:
    print("  Error fetching content templates:", e)

print("\nInspecting last successful WhatsApp messages sent from/to Twilio:")
try:
    messages = client.messages.list(limit=10)
    for m in messages:
        print(f"  SID: {m.sid}")
        print(f"    From: {m.from_} -> To: {m.to}")
        print(f"    Body: {m.body[:80]}...")
        print(f"    Status: {m.status}")
except Exception as e:
    print("  Error fetching messages:", e)
