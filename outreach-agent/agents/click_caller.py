"""
click_caller.py — Outbound voice campaign targeting leads who clicked an email link.

Triggered by Railway cron: POST /api/cron/click-calls  (runs hourly, Mon–Fri)

Each lead is called at most once. Calls only within 10 AM–5 PM in the lead's
local timezone. Aria offers three paths: free trial, demo booking, or human callback.
"""

import os
import requests
import logging
from utils.timezone import is_voice_window

log = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"

_SCRIPTS = {
    "dentist": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your clinic recently showed interest in our email. "
            "I'll be very quick — do you have 2 minutes?"
        ),
        "pitch": (
            "PracticeDesk is a WhatsApp AI receptionist for dental clinics. "
            "It automates appointment reminders and helps cut no-shows by up to 30 percent. "
            "Takes about 15 minutes to set up."
        ),
    },
    "salon": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your salon recently showed interest in our email. "
            "Do you have 2 quick minutes?"
        ),
        "pitch": (
            "PracticeDesk automates booking confirmations and appointment reminders "
            "on WhatsApp for salons. Most salons see fewer no-shows within the first month. "
            "Very quick to get started."
        ),
    },
    "physiotherapist": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your practice recently showed interest in our email. "
            "Do you have 2 quick minutes?"
        ),
        "pitch": (
            "PracticeDesk is a WhatsApp tool for physio practices — it automates "
            "appointment reminders, rebooking prompts, and patient follow-ups. "
            "No manual work required."
        ),
    },
    "accountant": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your firm recently showed interest in our email. "
            "Do you have 2 quick minutes?"
        ),
        "pitch": (
            "PracticeDesk automates client appointment reminders and document "
            "follow-ups on WhatsApp for accounting firms. "
            "Keeps your client pipeline moving without any manual chasing."
        ),
    },
    "lawyer": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your firm recently showed interest in our email. "
            "Do you have 2 quick minutes?"
        ),
        "pitch": (
            "PracticeDesk handles consultation bookings, client reminders, "
            "and follow-ups on WhatsApp for law firms — "
            "so your team can focus on billable work."
        ),
    },
    "doctor": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your clinic recently showed interest in our email. "
            "Do you have 2 quick minutes?"
        ),
        "pitch": (
            "PracticeDesk is a WhatsApp AI receptionist for medical clinics — "
            "it automates appointment reminders and patient follow-ups, "
            "typically reducing no-shows by 20 to 25 percent."
        ),
    },
}

_DEFAULT_SCRIPT = {
    "firstMessage": (
        "Hi, I'm Aria — an AI assistant from PracticeDesk. "
        "Someone at your business recently showed interest in our email. "
        "Do you have 2 quick minutes?"
    ),
    "pitch": (
        "PracticeDesk automates client appointment reminders and follow-ups on WhatsApp "
        "for healthcare and professional practices."
    ),
}

_SYSTEM_PROMPT = """\
You are Aria, a warm and brief outbound AI sales assistant for PracticeDesk — \
a WhatsApp-based AI receptionist for healthcare and professional practices.

Always disclose you are an AI if asked directly.

── CONTEXT ──────────────────────────────────────────────────────────────────
This is a warm call. The person recently clicked on a PracticeDesk email, \
so they have already shown genuine interest. Acknowledge this naturally early on.

── YOUR PITCH ────────────────────────────────────────────────────────────────
{pitch}

── THREE OPTIONS — present all three briefly, let them choose ────────────────
1. FREE TRIAL (lead with this): "The fastest way is to just sign up and try it yourself — \
   you get a full 14-day free trial with no obligation. \
   Go to practicedesk dot live — that's P-R-A-C-T-I-C-E-D-E-S-K dot live."

2. DEMO: "Or if you'd like a walkthrough, you can book a short 20-minute demo \
   with our founder at cal dot com slash practicedesk."

3. HUMAN CALLBACK: "And if you'd prefer to speak with a member of our team, \
   just say the word and I'll arrange a callback for you."

── HANDLING DEMO BOOKING ─────────────────────────────────────────────────────
If the prospect wants a demo:
1. Ask: "What day and time works best for you?"
2. Ask: "And what email should I send the confirmation to?"
3. Once you have both, use the book_demo tool immediately with those details.
4. After booking, confirm: "Done — you're booked for [time]. You'll get a confirmation shortly."

── HANDLING CALLBACK REQUEST ─────────────────────────────────────────────────
If the prospect says they want a human to call them back, use the request_callback tool \
immediately. Then confirm: "Done — someone from our team will be in touch with you shortly."

── HANDLING QUESTIONS OR OBSERVATIONS ───────────────────────────────────────
If a prospect has specific questions or observations during the call, acknowledge them \
and address what you can. If something is beyond what you can answer, say: \
"If you have any specific queries or observations, feel free to share them with me — \
I'll do my best to respond, or arrange for a member of our team to get back to you."

── STYLE ────────────────────────────────────────────────────────────────────
- Keep the call under 3 minutes
- One question at a time — short and focused
- If they are busy: "No problem at all — would a call another time work better?" \
  If yes, end the call gracefully. If no, thank them and end.
- If not interested: thank them warmly and end immediately
- Never be pushy or repeat yourself
"""


def _build_assistant(business_type: str, server_url: str) -> dict:
    script = _SCRIPTS.get(business_type.lower(), _DEFAULT_SCRIPT)
    prompt = _SYSTEM_PROMPT.format(pitch=script["pitch"])

    return {
        "name": "Aria — PracticeDesk Click Campaign",
        "firstMessage": script["firstMessage"],
        "model": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "systemPrompt": prompt,
            "temperature": 0.6,
        },
        "voice": {
            "provider": "openai",
            "voiceId": "nova",   # warm female voice for outbound
            "speed": 1.15,
        },
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "request_callback",
                    "description": (
                        "Call this tool when the prospect explicitly says they want "
                        "a human team member to call them back."
                    ),
                    "parameters": {"type": "object", "properties": {}},
                },
                "server": {"url": f"{server_url}/api/webhooks/vapi"},
            },
            {
                "type": "function",
                "function": {
                    "name": "book_demo",
                    "description": (
                        "Book a PracticeDesk demo on Cal.com for the prospect. "
                        "Call this once you have their preferred time AND email address."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preferred_time": {
                                "type": "string",
                                "description": "Prospect's preferred day and time, e.g. 'Friday at 2pm' or 'Monday morning'",
                            },
                            "attendee_email": {
                                "type": "string",
                                "description": "Prospect's email address for the calendar invite",
                            },
                            "attendee_name": {
                                "type": "string",
                                "description": "Prospect's name",
                            },
                        },
                        "required": ["preferred_time", "attendee_email"],
                    },
                },
                "server": {"url": f"{server_url}/api/webhooks/vapi"},
            },
        ],
        "serverUrl": f"{server_url}/api/webhooks/vapi",
        "artifactPlan": {"recordingEnabled": True},
        "endCallMessage": "Thanks for your time. Have a wonderful day!",
        "endCallPhrases": [
            "goodbye", "bye", "not interested",
            "remove me", "don't call again",
        ],
        "maxDurationSeconds": 210,
        "silenceTimeoutSeconds": 20,
        "backgroundSound": "off",
    }


def place_click_call(lead: dict) -> dict:
    """Place one outbound Vapi call for a clicked lead. Returns Vapi call object."""
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    server_url = os.getenv("SERVER_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError("VAPI_API_KEY not set")
    if not phone_number_id:
        raise RuntimeError("VAPI_PHONE_NUMBER_ID not set")
    if not server_url:
        raise RuntimeError("SERVER_BASE_URL not set")

    phone = lead.get("phone", "")
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    payload = {
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": cleaned,
            "name": lead.get("name", ""),
        },
        "assistant": _build_assistant(
            lead.get("business_type", ""),
            server_url,
        ),
        "metadata": {"lead_id": str(lead.get("id", ""))},
    }

    resp = requests.post(
        f"{VAPI_BASE}/call/phone",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=15,
    )

    if not resp.ok:
        raise RuntimeError(f"Vapi error {resp.status_code}: {resp.text}")

    return resp.json()


def run_click_campaign() -> dict:
    """
    Main entry point called by the cron endpoint.
    Finds all clicked-but-uncalled leads that are in their local 10 AM–5 PM window
    and places one Vapi call per lead.
    Returns a summary dict.
    """
    from database.client import get_clicked_uncalled_leads, log_activity

    leads = get_clicked_uncalled_leads()
    called, skipped_tz, skipped_no_phone, errors = 0, 0, 0, 0

    for lead in leads:
        city   = lead.get("city", "")
        market = lead.get("market", "")

        if not is_voice_window(city, market):
            skipped_tz += 1
            continue

        phone = lead.get("phone", "")
        if not phone:
            skipped_no_phone += 1
            continue

        try:
            call = place_click_call(lead)
            log_activity(str(lead["id"]), "outbound_call", {
                "vapi_call_id": call.get("id", ""),
                "trigger": "email_click",
                "phone": phone,
            })
            called += 1
            log.info("Placed click-call to lead %s (%s)", lead["id"], phone)
        except Exception as exc:
            log.error("Click-call failed for lead %s: %s", lead.get("id"), exc)
            errors += 1

    return {
        "called": called,
        "skipped_outside_hours": skipped_tz,
        "skipped_no_phone": skipped_no_phone,
        "errors": errors,
    }
