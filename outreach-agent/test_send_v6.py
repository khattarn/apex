"""
test_send_v6.py — Send v6 test messages to Neeraj's two numbers.

Run AFTER v6 templates are approved (~5 min after submit_v6_templates.py).

    python test_send_v6.py

Sends one message per vertical to +919810982019, then one dentist message
to +14168931395 so both numbers are verified before enabling cron.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from agents.outreach import send_template_message
from agents.template_manager import LOGO_URL

INDIA_NUMBER  = "+919810982019"
CANADA_NUMBER = "+14168931395"

# (template_name, greeting_param, business_param, image_url)
TESTS = [
    ("apex_outreach_dentist_v6",    "Neeraj", "Apex Test Dental Clinic",   LOGO_URL),
    ("apex_outreach_salon_v6",      "Neeraj", "Apex Test Salon",           LOGO_URL),
    ("apex_outreach_doctor_v6",     "Neeraj", "Apex Test Medical Centre",  LOGO_URL),
    ("apex_outreach_physio_v6",     "Neeraj", "Apex Test Physiotherapy",   LOGO_URL),
    ("apex_outreach_accountant_v6", "Neeraj", "Apex Test Accounting",      LOGO_URL),
    ("apex_outreach_lawyer_v6",     "Neeraj", "Apex Test Law Firm",        LOGO_URL),
]


def main():
    if not os.getenv("WHATSAPP_ACCESS_TOKEN"):
        print("ERROR: WHATSAPP_ACCESS_TOKEN not set")
        sys.exit(1)

    print("=== Sending v6 test messages ===\n")

    # All 6 verticals → India number
    for template, greeting, biz, img in TESTS:
        print(f"  {INDIA_NUMBER}  ←  {template} ...", end=" ", flush=True)
        try:
            send_template_message(INDIA_NUMBER, template, [greeting, biz], image_url=img)
            print("OK")
        except Exception as exc:
            print(f"FAIL: {exc}")

    print()

    # Dentist only → Canada number (as representative check)
    template, greeting, biz, img = TESTS[0]
    print(f"  {CANADA_NUMBER}  ←  {template} ...", end=" ", flush=True)
    try:
        send_template_message(CANADA_NUMBER, template, [greeting, biz], image_url=img)
        print("OK")
    except Exception as exc:
        print(f"FAIL: {exc}")

    print("\nDone. Check both phones, then switch VERTICAL_TEMPLATE = _V6 in wa_broadcast.py")


if __name__ == "__main__":
    main()
