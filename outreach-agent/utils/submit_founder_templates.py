"""
Submit the two founder-notification UTILITY templates to Meta.

Run once from outreach-agent/:
    python utils/submit_founder_templates.py

Templates:
  apex_daily_brief   — daily digest with one body variable (the text)
  apex_system_alert  — alert with three variables: icon, component, reason

Both target the OUTREACH number (Phone Number ID: OUTREACH_WA_PHONE_NUMBER_ID),
NOT the PracticeDesk customer number.

After submission, check status in Meta Business Suite > WhatsApp > Message Templates.
Approval typically takes a few hours. Until approved, Observatory and alerter fall
back to email-only (notify_founder() handles this gracefully).
"""
import json
import os
import sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────
PHONE_NUMBER_ID = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", "")
WA_TOKEN        = os.getenv("WHATSAPP_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN", "")
APP_ID          = os.getenv("META_APP_ID", "1325858332273520")   # from Meta Developer Console

if not (PHONE_NUMBER_ID and WA_TOKEN):
    print("ERROR: set OUTREACH_WA_PHONE_NUMBER_ID and WHATSAPP_TOKEN env vars")
    sys.exit(1)

# ── Template definitions ───────────────────────────────────────────────────────
TEMPLATES = [
    {
        "name":     "apex_daily_brief",
        "category": "UTILITY",
        "language": "en",
        "components": [
            {
                "type": "BODY",
                "text": "Apex Daily Digest\n\n{{1}}",
                "example": {
                    "body_text": [[
                        "Apex Daily — 28 Jun 2026\n\n── LAST 24 HOURS ──\nLeads added: 3\nEmails sent: 12\n..."
                    ]]
                },
            }
        ],
    },
    {
        "name":     "apex_system_alert",
        "category": "UTILITY",
        "language": "en",
        "components": [
            {
                "type": "BODY",
                "text": "Apex Alert {{1}}\n\n{{2}}: {{3}}",
                "example": {
                    "body_text": [["🔴", "email_campaign", "32% failure rate — check Resend quota"]]
                },
            }
        ],
    },
]


def submit(template: dict) -> dict:
    url  = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/message_templates"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"},
        json=template,
        timeout=15,
    )
    return {"template": template["name"], "status": resp.status_code, "body": resp.json()}


if __name__ == "__main__":
    for tpl in TEMPLATES:
        result = submit(tpl)
        print(f"\n── {result['template']} ──────────────────")
        print(f"HTTP {result['status']}")
        print(json.dumps(result["body"], indent=2))
    print("\nDone. Check Meta Business Suite for approval status (usually a few hours).")
