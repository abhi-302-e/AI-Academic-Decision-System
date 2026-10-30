import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip(" \"'")
token = os.getenv("TWILIO_AUTH_TOKEN", "").strip(" \"'")
from_num = os.getenv("TWILIO_FROM_NUMBER", "").strip(" \"'")
wa_num = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip(" \"'")

print("Twilio Environment Variables:")
print(f"  SID: {sid[:6]}...{sid[-4:]}" if len(sid) > 10 else f"  SID: {sid}")
print(f"  TOKEN: {token[:4]}...{token[-4:]}" if len(token) > 8 else f"  TOKEN: {token}")
print(f"  FROM: {from_num}")
print(f"  WA: {wa_num}")

from twilio.rest import Client
try:
    client = Client(sid, token)
    account = client.api.v2010.accounts(sid).fetch()
    print(f"Twilio Account Status: {account.friendly_name} (Status: {account.status})")
    
    incoming = client.incoming_phone_numbers.list(limit=5)
    print("Owned Twilio Phone Numbers:")
    for num in incoming:
        print(f"  - {num.phone_number} ({num.friendly_name})")
    if not incoming:
        print("  - No purchased incoming phone numbers found.")
except Exception as e:
    print("Twilio API check error:", e)
