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

# ── Load copy assets ──────────────────────────────────────────────────────────

_COPY_CACHE = None

def _load_copy() -> dict:
    global _COPY_CACHE
    if _COPY_CACHE is not None:
        return _COPY_CACHE
    try:
        import yaml
        assets_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'copy.yaml')
        with open(assets_path, 'r', encoding='utf-8') as f:
            _COPY_CACHE = yaml.safe_load(f) or {}
    except Exception:
        _COPY_CACHE = {}
    return _COPY_CACHE


def _get_script(business_type: str) -> dict:
    """Return opener/insight/pain_question for a business type from copy.yaml."""
    copy = _load_copy()
    vertical = (copy.get('verticals') or {}).get(business_type)
    if not vertical:
        vertical = copy.get('defaults') or {}
    return {
        "firstMessage": vertical.get('aria_opener', ''),
        "insight":      vertical.get('aria_insight', ''),
        "pain_question": vertical.get('aria_pain_question', ''),
    }


# ── Business-type openers (legacy fallback) ───────────────────────────────────

_SCRIPTS = {
    "dentist": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — do you ever get patients trying to book after your reception closes? "
            "Most clinics miss those completely."
        ),
        "insight": (
            "Most appointment searches happen between 8 PM and midnight — "
            "when every dental clinic is closed and the phone just rings out. "
            "Those patients don't call back in the morning. They book with whoever responded first. "
            "PracticeDesk acts as your after-hours receptionist on WhatsApp — "
            "it confirms bookings, sends reminders, and handles reschedules automatically."
        ),
        "pain_question": "Right now, when a patient tries to reach you after hours — what happens to that enquiry?",
    },
    "physiotherapist": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — do you find most patients complete one session "
            "and then just don't rebook?"
        ),
        "insight": (
            "The average physio practice loses around two thousand dollars a month "
            "to patients who don't rebook — not because they don't want to, "
            "but because nobody followed up at the right moment. "
            "A WhatsApp message sent 48 hours after treatment doubles the rebooking rate. "
            "And most patients will happily rebook at 10 at night if you make it easy for them."
        ),
        "pain_question": "How are you currently following up with patients after their first appointment?",
    },
    "salon": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — how many no-shows does your salon typically deal with each week?"
        ),
        "insight": (
            "Salons that switch from phone reminders to WhatsApp "
            "typically see no-show rates drop from around 15 percent to under 5 — in the first month. "
            "The reason is simple: WhatsApp messages get read, calls go to voicemail. "
            "And clients who would never call you at 9 AM will confirm their booking at 11 PM."
        ),
        "pain_question": "Are your no-shows mostly last-minute cancellations, or people who just don't show without any notice?",
    },
    "accountant": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — is your team spending more than a few hours a week "
            "chasing clients for documents or signatures?"
        ),
        "insight": (
            "The biggest hidden cost for accounting firms isn't overhead — "
            "it's the three to five hours per week staff spend chasing clients "
            "for documents, responses, and appointment confirmations. "
            "WhatsApp automation handles all of that without anyone lifting a finger. "
            "Clients respond in minutes on WhatsApp versus days on email."
        ),
        "pain_question": "Is it mostly document collection that takes the time, or more the back-and-forth around scheduling?",
    },
    "lawyer": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — how many potential clients do you think you lose "
            "just because they couldn't reach anyone quickly?"
        ),
        "insight": (
            "Law firms lose potential clients at the very first touchpoint. "
            "Research shows 70 percent of people trying to book a consultation online "
            "abandon the process if there's no instant confirmation. "
            "Most of those enquiries come outside business hours — "
            "an AI receptionist on WhatsApp responds within seconds, day or night, "
            "and captures clients your competitors are missing."
        ),
        "pain_question": "When a new client enquiry comes in after hours, what happens to it right now?",
    },
    "doctor": {
        "firstMessage": (
            "Hi, this is Aria from PracticeDesk. "
            "Quick question — do you wish your patients could book their next appointment "
            "at any hour, even when your clinic is closed?"
        ),
        "insight": (
            "Most patients search for appointments in the evening after work — "
            "when your clinic is closed and calls go unanswered. "
            "Medical clinics that add WhatsApp booking see a 25 percent drop in no-shows "
            "and pick up a significant number of after-hours bookings they were simply missing before."
        ),
        "pain_question": "When a patient tries to reach you after hours right now — do they get any response at all?",
    },
}

_DEFAULT_SCRIPT = {
    "firstMessage": (
        "Hi, this is Aria from PracticeDesk. "
        "Quick question — do you ever miss client enquiries or bookings "
        "simply because they came in after hours?"
    ),
    "insight": (
        "Most client enquiries and booking requests happen in the evening — "
        "after your business has closed for the day. "
        "Practices that add WhatsApp as an after-hours channel typically reduce no-shows "
        "by 20 to 30 percent and pick up bookings they were simply missing before."
    ),
    "pain_question": "What's the biggest gap in how you're handling client communications right now?",
}

# ── Full 7-phase system prompt ────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are Aria, a confident and warm outbound sales executive for PracticeDesk — \
a WhatsApp-based AI receptionist for healthcare and professional practices.

If asked directly whether you are an AI or a bot, answer honestly: yes, you are.
Maximum call length: 5 minutes. Never exceed this.

═══════════════════════════════════════════════════════════════════════════════
⚠️  ABSOLUTE RULE — CALLBACK REQUESTS
═══════════════════════════════════════════════════════════════════════════════
If the prospect says ANYTHING like "call me back", "can you call back", \
"not a good time", "I'm busy", or gives you a callback time — you MUST:
  1. Ask for (or confirm) a specific time if not already given.
  2. Use the schedule_callback tool immediately.
  3. Confirm: "Perfect — I'll call you [day/time]. Have a great day."
  4. END THE CALL. No exceptions.

NEVER say "this will just take a sec", "it'll only be a moment", \
or any phrase that attempts to continue the call after a callback request. \
Pushing past a callback request destroys trust and loses the prospect permanently.

═══════════════════════════════════════════════════════════════════════════════
PHASE 1 — OPENING  (target: 20 seconds)
═══════════════════════════════════════════════════════════════════════════════
The prospect recently clicked on a PracticeDesk email, so this is a warm call. \
Your opening message is pre-set. After they respond:
- If they signal they are busy or ask for a callback → trigger the ABSOLUTE RULE above immediately.
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
CALLBACK HANDLING (any point in the call — see ABSOLUTE RULE at top)
═══════════════════════════════════════════════════════════════════════════════
"No problem at all — when would be a better time to reach you?"
→ Once they give a time: use schedule_callback immediately.
→ Confirm: "Perfect — I'll call you then. Have a great day."
→ END THE CALL. Do not add another sentence. Do not pitch anything.

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


def _normalize_phone(phone: str, city: str = "") -> str:
    """Convert a local phone number to E.164 format using city context for country code."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return ""
    # Already has country code (starts with +)
    if phone.strip().startswith("+"):
        return f"+{digits}"
    from utils.timezone import CITY_TZ
    tz = CITY_TZ.get(city, "")
    if "Australia" in tz:
        # Strip leading 0 (area code zero), prepend +61
        if digits.startswith("0"):
            digits = digits[1:]
        return f"+61{digits}"
    elif "Europe/London" in tz:
        # UK: strip leading 0, prepend +44
        if digits.startswith("0"):
            digits = digits[1:]
        return f"+44{digits}"
    elif "America" in tz:
        # North America: 10-digit → prepend +1
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
    # Fallback
    return f"+{digits}"


def _build_assistant(business_type: str, server_url: str) -> dict:
    script = _get_script(business_type.lower())
    # Fall back to legacy hardcoded dict if yaml returned empty strings
    if not script["firstMessage"]:
        script = _SCRIPTS.get(business_type.lower(), _DEFAULT_SCRIPT)
    prompt = _SYSTEM_PROMPT.format(
        insight=script["insight"],
        pain_question=script["pain_question"],
    )

    tools = [
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
                        "preferred_day":  {"type": "string", "description": "Day of the week, e.g. 'Monday'"},
                        "preferred_time": {"type": "string", "description": "Time of day, e.g. '2pm', 'morning'"},
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
                    "Call only after you have both the prospect's preferred time AND email."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preferred_time":  {"type": "string", "description": "Preferred day and time, e.g. 'Friday at 2pm'"},
                        "attendee_email":  {"type": "string", "description": "Prospect's email for the calendar invite"},
                        "attendee_name":   {"type": "string", "description": "Prospect's name"},
                    },
                    "required": ["preferred_time", "attendee_email"],
                },
            },
            "server": {"url": f"{server_url}/api/webhooks/vapi"},
        },
    ]

    return {
        "name": "Aria — PracticeDesk Sales",
        "firstMessage": script["firstMessage"],
        "model": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "systemPrompt": prompt,
            "temperature": 0.65,
            "tools": tools,   # tools belong inside model, not at assistant level
        },
        "voice": {
            "provider": "openai",
            "voiceId": "nova",
            "speed": 1.15,
        },
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
    api_key    = os.getenv("VAPI_API_KEY")
    server_url = os.getenv("SERVER_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError("VAPI_API_KEY not set")
    if not server_url:
        raise RuntimeError("SERVER_BASE_URL not set")

    phone   = lead.get("phone", "")
    city    = lead.get("city", "")
    cleaned = _normalize_phone(phone, city)
    if not cleaned or cleaned in ("+", ""):
        raise RuntimeError(f"Could not normalise phone '{phone}' for {lead.get('name')}")

    # Auto-route: +91 numbers use the India Vobiz number when configured
    if cleaned.startswith("+91") and os.getenv("INDIA_VAPI_PHONE_NUMBER_ID"):
        phone_number_id = os.getenv("INDIA_VAPI_PHONE_NUMBER_ID")
    else:
        phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

    if not phone_number_id:
        raise RuntimeError("VAPI_PHONE_NUMBER_ID (or INDIA_VAPI_PHONE_NUMBER_ID for +91) not set")

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
