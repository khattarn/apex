"""
Submit the founder-notification UTILITY templates to Meta.

Run once from outreach-agent/:
    python utils/submit_founder_templates.py

Templates:
  apex_daily_ping    — short daily-report ping, four variables: date, new_leads,
                       calls, emails_sent. Replaces apex_daily_brief (below),
                       which Meta auto-recategorized MARKETING after approval —
                       category can't be edited post-approval, and MARKETING
                       templates get silently throttled by Meta's per-recipient
                       engagement limits when the founder never replies. The
                       full digest text still goes out over email every run.
  apex_daily_brief   — LEGACY, do not use — stuck as MARKETING category, kept
                       here only so its history isn't lost. See apex_daily_ping.
  apex_system_alert  — alert with three variables: icon, component, reason
  apex_call_outcome  — actionable Sophie call outcome with five variables:
                       label, lead_line, detail, summary, recording_url

All target the OUTREACH number (Phone Number ID: OUTREACH_WA_PHONE_NUMBER_ID),
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
        # Submitted 2026-07-16 as the UTILITY replacement for apex_daily_brief.
        "name":     "apex_daily_ping",
        "category": "UTILITY",
        "language": "en",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Apex Daily Report — {{1}}\n\n"
                    "New leads: {{2}} | Calls placed: {{3}} | Emails sent: {{4}}\n\n"
                    "Full report sent to your inbox and available on the Apex dashboard."
                ),
                "example": {
                    "body_text": [["16 Jul 2026", "8", "42", "37"]]
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
    {
        # NOTE: submitted directly via the WABA endpoint (not phone_number_id) on 2026-07-04
        # because {{n}}/word-ratio validation rejected a shorter, emoji-heavy body. Status: PENDING.
        "name":     "apex_call_outcome",
        "category": "UTILITY",
        "language": "en",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Apex Lead Alert\n\n"
                    "Outcome: {{1}}\n"
                    "Lead: {{2}}\n"
                    "Detail: {{3}}\n"
                    "Call summary: {{4}}\n"
                    "Recording link: {{5}}\n\n"
                    "This lead had a live conversation with your AI sales agent. Please review and follow up promptly."
                ),
                "example": {
                    "body_text": [[
                        "Callback scheduled",
                        "Texas Dental Center, dentist, Houston, phone 8328319101",
                        "Call back Monday at 2pm",
                        "Aria followed up on an email click about reducing no-shows and the clinic asked for a callback at a specific time",
                        "https://storage.vapi.ai/019ea7f6-62c1-7777-ac38-e381716ed848-mono.wav",
                    ]]
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
