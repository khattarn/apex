import os
import requests

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
    copy = _load_copy()
    vertical = (copy.get('verticals') or {}).get(business_type)
    if not vertical:
        vertical = copy.get('defaults') or {}
    return {
        "firstMessage": vertical.get('aria_opener', ''),
        "insight":      vertical.get('aria_insight', ''),
        "pain_question": vertical.get('aria_pain_question', ''),
    }


# ── Fallback scripts (copy.yaml missing or empty) ────────────────────────────

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

# ── 7-phase system prompt (matches click_caller.py) ──────────────────────────

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
  → End warmly.

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
  → End immediately.

═══════════════════════════════════════════════════════════════════════════════
CALLBACK HANDLING (any point in the call — see ABSOLUTE RULE at top)
═══════════════════════════════════════════════════════════════════════════════
"No problem at all — when would be a better time to reach you?"
→ Once they give a time: use schedule_callback immediately.
→ Confirm: "Perfect — I'll call you then. Have a great day."
→ END THE CALL. Do not add another sentence. Do not pitch anything.

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


def _build_tools(server_url: str) -> list:
    return [
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
                        "preferred_time": {"type": "string", "description": "Preferred day and time, e.g. 'Friday at 2pm'"},
                        "attendee_email": {"type": "string", "description": "Prospect's email for the calendar invite"},
                        "attendee_name":  {"type": "string", "description": "Prospect's name"},
                    },
                    "required": ["preferred_time", "attendee_email"],
                },
            },
            "server": {"url": f"{server_url}/api/webhooks/vapi"},
        },
    ]


def place_outbound_call(phone: str, business_type: str, business_name: str) -> dict:
    api_key    = os.getenv("VAPI_API_KEY")
    server_url = os.getenv("SERVER_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError("VAPI_API_KEY must be set")

    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    # Auto-route: +91 numbers use the India Vobiz number when configured
    if cleaned.startswith("+91") and os.getenv("INDIA_VAPI_PHONE_NUMBER_ID"):
        phone_number_id = os.getenv("INDIA_VAPI_PHONE_NUMBER_ID")
    else:
        phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

    if not phone_number_id:
        raise RuntimeError("VAPI_PHONE_NUMBER_ID (or INDIA_VAPI_PHONE_NUMBER_ID for +91) must be set")

    script = _get_script(business_type.lower())
    if not script["firstMessage"]:
        script = _DEFAULT_SCRIPT

    prompt = _SYSTEM_PROMPT.format(
        insight=script["insight"],
        pain_question=script["pain_question"],
    )

    assistant = {
        "name": "Aria — PracticeDesk Outreach",
        "firstMessage": script["firstMessage"],
        "model": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "systemPrompt": prompt,
            "temperature": 0.65,
            "tools": _build_tools(server_url) if server_url else [],
        },
        "voice": {
            "provider": "cartesia",
            "voiceId": "248be419-c632-4f23-adf1-5324ed7dbf1d",   # Helpful Woman — warm, clear
            "model": "sonic-2",
        },
        "endCallMessage": "Thanks for your time. Have a wonderful day!",
        "endCallPhrases": [
            "goodbye", "bye", "not interested",
            "remove me", "don't call again",
        ],
        "maxDurationSeconds": 330,
        "silenceTimeoutSeconds": 20,
        "backgroundSound": "off",
    }

    if server_url:
        assistant["serverUrl"] = f"{server_url}/api/webhooks/vapi"
        assistant["artifactPlan"] = {"recordingEnabled": True}

    payload = {
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": cleaned,
            "name": business_name,
        },
        "assistant": assistant,
    }

    response = requests.post(
        f"{VAPI_BASE}/call/phone",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=15,
    )

    if not response.ok:
        raise RuntimeError(f"Vapi API error {response.status_code}: {response.json()}")

    return response.json()
