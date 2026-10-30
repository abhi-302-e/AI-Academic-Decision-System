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

# Inspect message SM2da99a22d4175ac2f2b666f6e4110a55
msg = client.messages("SM2da99a22d4175ac2f2b666f6e4110a55").fetch()
print("Full Body:", msg.body)
print("Date Sent:", msg.date_sent)
print("Status:", msg.status)

# Try replying within the active 24-hr session window
try:
    reply = client.messages.create(
        from_="whatsapp:+17372508034",
        to="whatsapp:+919059514176",
        body="[AI Academic System] Hello! Your attendance for CSE101 is 82.5% (PRESENT). Advisory: Complete quiz 2."
    )
    print("Session reply success! SID:", reply.sid, "Status:", reply.status)
except Exception as e:
    print("Direct body attempt error:", e)

# Try with ContentSid from Twilio trial defaults if needed
# Or standard sandbox template: "Your appointment is coming up on..."
