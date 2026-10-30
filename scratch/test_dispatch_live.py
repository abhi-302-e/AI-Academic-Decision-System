import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from dotenv import load_dotenv
load_dotenv(dotenv_path=root / ".env", override=True)

import sms_service

test_target = "+919059514176"

print(f"Testing direct WhatsApp dispatch to {test_target}...")
wa_res = sms_service.send_academic_update_sms(
    phone_number=test_target,
    message_body="[AI Academic System] Hello! This is a test academic notification sent via Twilio WhatsApp Gateway.",
    recipient_name="Student",
    send_whatsapp=True
)
print("WhatsApp Result:", wa_res)

print(f"\nTesting direct SMS dispatch to {test_target}...")
sms_res = sms_service.send_academic_update_sms(
    phone_number=test_target,
    message_body="[AI Academic System] Hello! This is a test academic notification sent via Twilio SMS Gateway.",
    recipient_name="Student",
    send_whatsapp=False
)
print("SMS Result:", sms_res)
