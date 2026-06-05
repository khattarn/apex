"""
click_caller.py — Outbound voice campaign targeting leads who clicked an email link.

Triggered hourly Mon–Fri by APScheduler inside server.py.

Each lead is called once. Calls only within 10 AM–5 PM local time.
Aria follows a 7-phase sales playbook: open → discover → insight pitch →
trial + urgency → objection → 3-close sequence → exit.
"""

import os
import requests
import logging
from utils.timezone import is_voice_window

log = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"

# ── Business-type openers ─────────────────────────────────────────────────────

_SCRIPTS = {
    "dentist": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your clinic recently showed some interest in our email. "
            "I'll be very quick — do you have about 3 minutes?"
        ),
        "insight": (
            "Here's something most dental clinics don't realise — "
            "patients who no-show actually had a reminder. They just ignored the phone call. "
            "Research shows 73 percent of them respond to a WhatsApp message within 15 minutes. "
            "Your staff are using the wrong channel."
        ),
        "pain_question": "What's your biggest headache with no-shows right now — is it mostly the lost revenue, or the wasted chair time?",
    },
    "physiotherapist": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your practice recently showed interest in our email. "
            "Do you have about 3 minutes?"
        ),
        "insight": (
            "Here's something that might surprise you — "
            "the average physio practice loses around two thousand dollars a month "
            "to patients who complete one session and simply don't rebook. "
            "A WhatsApp follow-up sent 48 hours after treatment doubles the rebooking rate. "
            "And it takes zero staff time if it's automated."
        ),
        "pain_question": "Would you say your biggest challenge is patients not rebooking, or more the time your staff spends on phone reminders?",
    },
    "salon": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your salon recently showed interest in our email. "
            "Do you have about 3 minutes?"
        ),
        "insight": (
            "Salons that switch appointment reminders from phone calls to WhatsApp "
            "typically see no-show rates drop from around 15 percent down to under 5 percent — "
            "in the first month. The difference is simply read rates. "
            "WhatsApp messages get opened. Calls go to voicemail."
        ),
        "pain_question": "How are you currently handling reminders — is it mostly your team calling clients manually?",
    },
    "accountant": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your firm recently showed interest in our email. "
            "Do you have about 3 minutes?"
        ),
        "insight": (
            "The biggest hidden cost for accounting firms isn't overhead — "
            "it's the three to five hours per week staff spend chasing clients "
            "for documents, signatures, and appointment confirmations. "
            "WhatsApp automation handles all of that without anyone lifting a finger."
        ),
        "pain_question": "Is client follow-up taking up a lot of your team's time, or is appointment scheduling the bigger issue?",
    },
    "lawyer": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your firm recently showed interest in our email. "
            "Do you have about 3 minutes?"
        ),
        "insight": (
            "Law firms lose potential clients at the very first touchpoint. "
            "Studies show 70 percent of people who try to book a consultation online "
            "abandon the process if there's no instant confirmation. "
            "An AI receptionist that responds on WhatsApp within seconds captures clients "
            "your competitors are losing."
        ),
        "pain_question": "Is your main challenge with new client intake, or more the ongoing communication with existing clients?",
    },
    "doctor": {
        "firstMessage": (
            "Hi, I'm Aria — an AI assistant from PracticeDesk. "
            "Someone at your clinic recently showed interest in our email. "
            "Do you have about 3 minutes?"
        ),
        "insight": (
            "Medical clinics that implement WhatsApp appointment reminders "
            "see a 25 percent drop in no-shows in the first month. "
            "No-shows cost the average clinic over a hundred thousand dollars a year in lost revenue. "
            "That's a significant number to recover just by changing your reminder channel."
        ),
        "pain_question": "Is no-show rate your main concern, or is it more the administrative burden on your reception team?",
    },
}

_DEFAULT_SCRIPT = {
    "firstMessage": (
        "Hi, I'm Aria — an AI assistant from PracticeDesk. "
        "Someone at your business recently showed interest in our email. "
        "Do you have about 3 minutes?"
    ),
    "insight": (
        "Practices and businesses that automate client communications on WhatsApp "
        "typically reduce no-shows by 20 to 30 percent and save their staff several hours a week — "
        "just by moving reminders and follow-ups off the phone and onto a channel clients actually use."
    ),
    "pain_question": "What's the biggest challenge with client communications for you right now?",
}

# ── Full 7-phase system prompt ────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are Aria, a confident and warm outbound AI sales executive for PracticeDesk — \
a WhatsApp-based AI receptionist for healthcare and professional practices.

Always disclose you are an AI if asked directly.
Maximum call length: 5 minutes. Never exceed this.

═══════════════════════════════════════════════════════════════════════════════
PHASE 1 — OPENING  (target: 20 seconds)
═══════════════════════════════════════════════════════════════════════════════
The prospect recently clicked on a PracticeDesk email, so this is a warm call. \
Your opening message is pre-set. After they respond:
- If they say they are busy → go to CALLBACK HANDLING immediately.
- If they say they have a moment → continue to Phase 2.

═══════════════════════════════════════════════════════════════════════════════
PHASE 2 — DISCOVERY  (target: 60 seconds, maximum 2 questions)
═══════════════════════════════════════════════════════════════════════════════
Ask these two questions, one at a time. Listen carefully — use their exact words \
in your pitch.

Question 1 (situation): "How do you currently handle appointment reminders — \
phone calls, texts, something else?"

Question 2 (pain): {pain_question}

Do not ask more than 2 questions. Move on once you have their core pain.

═══════════════════════════════════════════════════════════════════════════════
PHASE 3 — INSIGHT PITCH  (target: 45 seconds)
═══════════════════════════════════════════════════════════════════════════════
Lead with the industry insight. Then connect directly to the pain they just told \
you about. Do not list features — make one sharp connection.

Insight: {insight}

Then connect: "Based on what you just told me about [their pain word], \
that's exactly the problem PracticeDesk solves — [one-sentence solution]."

═══════════════════════════════════════════════════════════════════════════════
PHASE 4 — TRIAL OFFER + URGENCY  (target: 20 seconds)
═══════════════════════════════════════════════════════════════════════════════
"You can sign up right now and be live within 15 minutes — \
there's a 14-day free trial, no obligation at all. \
I should mention these are introductory prices that will be going up as we grow, \
so right now is genuinely a good time to lock in."

Pricing if asked:
  Starter: $49/month · Growth: $99/month · Pro: $180/month

═══════════════════════════════════════════════════════════════════════════════
PHASE 5 — OBJECTION HANDLING  (one round only, target: 30 seconds)
═══════════════════════════════════════════════════════════════════════════════
Handle only ONE objection. If there are more, acknowledge them briefly and move \
straight to Phase 6.

"Too expensive":
  "At $49 a month, that's less than the cost of one missed appointment. \
   If PracticeDesk saves you even two no-shows a month, it more than pays for itself."

"No time to set up":
  "Setup takes 15 minutes — and we walk you through every step. \
   Most practices are live before lunch."

"Need to think about it":
  Acknowledge briefly, then go straight to Close 2 in Phase 6.

"Not the right person / need to check with partner":
  "Of course — who would be the right person? I'm happy to give them a call, \
   or I can send you both a short overview."

"Not interested":
  Thank them warmly and end the call immediately. Never retry.

═══════════════════════════════════════════════════════════════════════════════
PHASE 6 — CLOSE SEQUENCE  (target: 40 seconds, stop at first yes)
═══════════════════════════════════════════════════════════════════════════════
Attempt all three closes in order. Stop the moment you get a yes.

CLOSE 1 — Assumptive (Zig Ziglar):
  "Based on everything we've discussed, can I assume you're convinced \
   and you'll sign up for the trial today?"

CLOSE 2 — Conditional (The Perfect Close):
  "What would need to happen for you to sign up today?"
  → If they name something you can address, address it, then ask Close 1 again.
  → If they can't name anything, move to Close 3.

CLOSE 3 — Invitation (Chris Voss):
  "Would it be completely crazy to just try it free for 14 days \
   and see the numbers yourself?"

After 3 closes with no yes: do NOT push further. Move to Phase 7.

═══════════════════════════════════════════════════════════════════════════════
PHASE 7 — EXIT  (target: 20 seconds)
═══════════════════════════════════════════════════════════════════════════════

IF THEY SAID YES (signed up or want to):
  "Wonderful. Go to practicedesk dot live to get started — \
   I'll also send you the link right now."
  → Use the send_signup_link tool, then end warmly.

IF THEY WANT A DEMO:
  "Happy to arrange that. What day and time works best for you?"
  "And what email should I send the calendar invite to?"
  → Once you have both, use the book_demo tool.
  → After booking: "Done — you're booked. You'll get a confirmation shortly."

IF THEY WANT A HUMAN CALLBACK:
  → Use the request_callback tool.
  → Confirm: "Done — someone from our team will be in touch shortly."

IF NOT READY (soft no):
  "Completely understand. Would it help if I called you back at a better time? \
   What day and time works for you?"
  → Use the schedule_callback tool with their preferred day and time.
  → Confirm: "Perfect — I'll call you then. Have a great day."

IF HARD NO:
  "Thank you for your time, [Name]. Take care."
  → End immediately, mark as not interested.

═══════════════════════════════════════════════════════════════════════════════
CALLBACK HANDLING (if busy at the start)
═══════════════════════════════════════════════════════════════════════════════
"No problem at all — when would be a better time to reach you? \
 I can call you back on [day] at [time]."
→ Use the schedule_callback tool.
→ Confirm: "Wonderful — I'll call you then. Sorry to have caught you at a bad time."

═══════════════════════════════════════════════════════════════════════════════
QUESTIONS OR OBSERVATIONS
═══════════════════════════════════════════════════════════════════════════════
If the prospect has specific questions or observations, address what you can. \
For anything beyond your knowledge: \
"If you have any specific queries or observations, feel free to share them — \
I'll do my best to respond, or arrange for a member of our team to get back to you."

═══════════════════════════════════════════════════════════════════════════════
STYLE RULES
═══════════════════════════════════════════════════════════════════════════════
- One question at a time. Never stack two questions.
- Use their exact words when referencing their pain — it signals you listened.
- Speak at a confident, natural pace. Do not rush.
- Never repeat the same close twice in a row.
- Never apologise for calling — you're offering genuine value.
- Avoid filler words: "absolutely", "certainly", "of course", "great question".
- If they mention a competitor, acknowledge it briefly and return to their pain.
"""


def _build_assistant(business_type: str, server_url: str) -> dict:
    script = _SCRIPTS.get(business_type.lower(), _DEFAULT_SCRIPT)
    prompt = _SYSTEM_PROMPT.format(
        insight=script["insight"],
        pain_question=script["pain_question"],
    )

    return {
        "name": "Aria — PracticeDesk Sales",
        "firstMessage": script["firstMessage"],
        "model": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "systemPrompt": prompt,
            "temperature": 0.65,
        },
        "voice": {
            "provider": "openai",
            "voiceId": "nova",
            "speed": 1.15,
        },
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "schedule_callback",
                    "description": (
                        "Schedule a callback for a prospect who is busy or not ready to decide. "
                        "Call this when they agree to a specific callback day and time."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preferred_day":  {"type": "string", "description": "Day of the week, e.g. 'Monday', 'Thursday'"},
                            "preferred_time": {"type": "string", "description": "Time of day, e.g. '2pm', '10am', 'morning'"},
                        },
                        "required": ["preferred_day", "preferred_time"],
                    },
                },
                "server": {"url": f"{server_url}/api/webhooks/vapi"},
            },
            {
                "type": "function",
                "function": {
                    "name": "request_callback",
                    "description": "Flag that the prospect wants a human team member to call them back.",
                    "parameters": {"type": "object", "properties": {}},
                },
                "server": {"url": f"{server_url}/api/webhooks/vapi"},
            },
            {
                "type": "function",
                "function": {
                    "name": "book_demo",
                    "description": (
                        "Book a PracticeDesk demo on Cal.com. "
                        "Call only after you have the prospect's preferred time AND email."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preferred_time": {
                                "type": "string",
                                "description": "Preferred day and time, e.g. 'Friday at 2pm'",
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
        "maxDurationSeconds": 330,   # 5.5 min hard cap
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
    Main entry point called by the APScheduler job.
    Finds clicked-but-uncalled leads in their 10 AM–5 PM window and places calls.
    """
    from database.client import get_clicked_uncalled_leads, log_activity

    leads = get_clicked_uncalled_leads()
    called, skipped_tz, skipped_no_phone, errors = 0, 0, 0, 0

    for lead in leads:
        if not is_voice_window(lead.get("city", ""), lead.get("market", "")):
            skipped_tz += 1
            continue

        if not lead.get("phone"):
            skipped_no_phone += 1
            continue

        try:
            call = place_click_call(lead)
            log_activity(str(lead["id"]), "outbound_call", {
                "vapi_call_id": call.get("id", ""),
                "trigger": "email_click",
                "phone": lead["phone"],
            })
            called += 1
            log.info("Placed click-call to lead %s (%s)", lead["id"], lead["phone"])
        except Exception as exc:
            log.error("Click-call failed for lead %s: %s", lead.get("id"), exc)
            errors += 1

    return {
        "called": called,
        "skipped_outside_hours": skipped_tz,
        "skipped_no_phone": skipped_no_phone,
        "errors": errors,
    }
