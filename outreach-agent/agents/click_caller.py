"""
click_caller.py — Outbound voice campaign targeting leads who clicked an email link.

Triggered hourly Mon–Fri by APScheduler inside server.py.

Each lead is called once. Calls only within 11 AM–5 PM local time.
Sophie follows a 7-phase sales playbook: open → discover → insight pitch →
trial + urgency → objection → 3-close sequence → exit.
"""

import logging
import os

from utils.timezone import is_voice_window

log = logging.getLogger(__name__)

_PRICING_USD = "Starter: $49/month · Growth: $99/month · Pro: $180/month · Setup: $180 (waived until 29 Jul 2026)"
_PRICING_CAD = "Starter: CAD $70/month · Growth: CAD $140/month · Pro: CAD $250/month · Setup: CAD $250 (waived until 29 Jul 2026)"
_PRICING_GBP = "Starter: £39/month · Growth: £79/month · Pro: £149/month · Setup: £149 (waived until 29 Jul 2026)"

def _pricing_line(market: str) -> str:
    market = (market or "").upper()
    if market == "CA":
        return _PRICING_CAD
    if market == "UK":
        return _PRICING_GBP
    return _PRICING_USD


def _get_script(business_type: str, pain_signal: str = "") -> dict:
    """opener/insight/pain_question for a business type — see voice_outreach._get_script."""
    from agents.voice_outreach import _get_script as _shared_get_script
    return _shared_get_script(business_type, pain_signal)


# ── Business-type openers (legacy fallback) ───────────────────────────────────

_SCRIPTS = {
    "dentist": {
        "firstMessage": (
            "Hi, this is Sophie from PracticeDesk. "
            "Quick question — when a patient calls after you've closed for the day, "
            "or when the front desk is slammed, what happens to that call right now?"
        ),
        "insight": (
            "Here's what we see: most patients searching in the evening won't leave a voicemail — "
            "they call the next practice. "
            "So the lost booking never even shows up as a missed call. "
            "It's invisible, which is why it's easy to under-rate."
        ),
        "pain_question": (
            "When the phone rings and no one can grab it — after hours, or mid-treatment — "
            "where does that call go today? Voicemail, or just missed?"
        ),
    },
    "physiotherapist": {
        "firstMessage": (
            "Hi, this is Sophie from PracticeDesk. "
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
            "Hi, this is Sophie from PracticeDesk. "
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
            "Hi, this is Sophie from PracticeDesk. "
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
            "Hi, this is Sophie from PracticeDesk. "
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
            "Hi, this is Sophie from PracticeDesk. "
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
        "Hi, this is Sophie from PracticeDesk. "
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
You are Sophie, a confident and warm outbound sales executive for PracticeDesk — \
an AI office assistant across phone, WhatsApp, and email for healthcare and \
professional practices.

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
GENTLE-TONE RULES (non-negotiable)
═══════════════════════════════════════════════════════════════════════════════
1. Warmth or a compliment before the pain — never open with the problem cold.
2. Normalise it — "this happens to almost every busy practice", "totally normal".
3. Point at the patient's experience, not the clinic's failing.
4. No numbers as a weapon in the opener.
5. Ask permission, give an easy yes — "mind if I share?", "worth thirty seconds?"
6. Back off instantly if they bristle — pivot to a soft offer to email instead.

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
PHASE 4 — TRIAL OFFER  (target: 20 seconds)
═══════════════════════════════════════════════════════════════════════════════
"PracticeDesk is an AI office assistant that answers every call, WhatsApp and \
email for you, 24/7 — books the appointment and drops it in your dashboard for \
a one-click confirm. Nothing is final without you. Practices see about 30% fewer \
no-shows in the first month. Worth a look?"

Pricing if asked:
  Starter: $49/month · Growth: $99/month · Pro: $180/month
  Setup fee: $180 — waived until 29 Jul 2026 (introductory offer — always mention this)

═══════════════════════════════════════════════════════════════════════════════
PHASE 5 — OBJECTION HANDLING  (one round only, target: 30 seconds)
═══════════════════════════════════════════════════════════════════════════════
Handle only ONE objection. If there are more, acknowledge them briefly and move \
straight to Phase 6.

"We have a receptionist":
  "Perfect — this works alongside them, not instead. It covers after-hours and \
   overflow, the calls that currently hit voicemail. Your receptionist keeps the \
   chair-side work."

"We're too busy to set it up":
  "That's the part people are surprised by — it's about fifteen minutes, and \
   it's answering calls the same evening."

"I don't want AI dealing with patients":
  "It never confirms anything on its own. It collects the booking and you approve \
   it with one click. You stay in control of every patient."

"Just email me":
  "Happy to — I'll send a 90-second video. Can I also book you a quick look so \
   you see it taking a live booking? No pressure."

"Not interested":
  Thank them warmly and end the call immediately. Never retry.

═══════════════════════════════════════════════════════════════════════════════
PHASE 6 — CLOSE SEQUENCE  (target: 40 seconds, stop at first yes)
═══════════════════════════════════════════════════════════════════════════════
"I'll set you up with the free 14-day trial — no card, live in fifteen minutes — \
and send a calendar link so we can switch it on together. What email's best?"

If they hesitate:
  "Would it be completely crazy to just try it free for 14 days \
   and see the numbers yourself?"

After two attempts with no yes: move to Phase 7.

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
  "No problem at all. I'll send a short note so you have it if the timing changes. \
   Thanks for the twenty seconds — have a good one."
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
- 1–2 sentences per turn. Never monologue.
- Use their exact words when referencing their pain — it signals you listened.
- Conversational fillers ("sure", "got it", "fair enough") are fine.
- Never apologise for calling — you're offering genuine value.
- Avoid filler words: "absolutely", "certainly", "of course", "great question".
- If they mention a competitor, acknowledge it briefly and return to their pain.
- Warm, slightly informal. Aim "helpful colleague", not "call centre".
"""


def _is_india(phone: str, market: str = "") -> bool:
    if (market or "").upper() == "IN":
        return True
    digits = "".join(c for c in phone if c.isdigit())
    # Only unambiguous India indicators — never the bare-10-digit check which
    # catches most NANP area codes (613, 647, 604, 713…) and misroutes them to Dograh.
    return (
        (digits.startswith("91") and len(digits) == 12) or
        digits.startswith("0091")
    )


def place_click_call(lead: dict) -> dict:
    """Trigger an outbound call for an email-clicked lead.
    CA  → Vapi + SignalWire Alberta (+15872090343).
    US/AU/UK → Vapi free number (+13129408233).
    India → Dograh + Vobiz (only remaining Dograh path).
    """
    from utils.timezone import is_canadian
    from agents.vapi_caller import place_sophie_call
    from agents.email_personalizer import detect_market
    phone = lead.get("phone", "")
    if not phone:
        raise RuntimeError(f"Lead {lead.get('id')} has no phone number")

    city       = lead.get("city", "")
    address    = lead.get("address", "") or ""
    # lead.market (the DB column) is unpopulated for almost all leads — compute
    # it fresh from phone+address instead of trusting the stored column.
    market     = detect_market(phone, address)
    business_type = lead.get("business_type", "")
    business_name = lead.get("name", "")
    lead_id    = str(lead.get("id", ""))

    # India: still on Dograh + Vobiz
    if _is_india(phone, market):
        from agents.dograh_caller import place_outbound_call as _dograh_call
        return _dograh_call(
            phone=phone, business_type=business_type,
            business_name=business_name, lead_id=lead_id,
            city=city, trigger="email_click",
        )

    script = _get_script(business_type, lead.get("pain_signal", ""))
    phone_number_id = (
        os.getenv("VAPI_CA_PHONE_NUMBER_ID", "a513803a-5229-4ac1-881d-6c89ae708738")
        if is_canadian(city, market)
        else os.getenv("VAPI_PLATFORM_PHONE_ID", "50d7061b-ac77-4a4f-b2d5-7430df39b9d5")
    )
    return place_sophie_call(
        phone=phone,
        business_name=business_name,
        business_type=business_type,
        city=city,
        opener=script.get("firstMessage", ""),
        insight=script.get("insight", ""),
        pain_question=script.get("pain_question", ""),
        lead_id=lead_id,
        phone_number_id=phone_number_id,
        pain_signal=lead.get("pain_signal", ""),
        pain_finding=lead.get("pain_finding", ""),
        pricing_line=_pricing_line(market),
        address=lead.get("address", ""),
    )


_TIER_LABELS = {1: "clicked", 2: "opened", 3: "emailed_24h", 4: "never_contacted"}


def _lead_tier_label(lead: dict, today_utc: str, cutoff_24h: str) -> str:
    if lead.get("email_clicked") and (lead.get("email_clicked_at") or "")[:10] < today_utc:
        return "clicked"
    if lead.get("email_opened") and not lead.get("email_clicked"):
        return "opened"
    last_sent = lead.get("email_last_sent_at") or ""
    if lead.get("email_sent") and last_sent and last_sent < cutoff_24h:
        return "emailed_24h"
    return "never_contacted"


def run_click_campaign() -> dict:
    """
    Voice priority queue — ranked by engagement tier then pain_score.
    Tier order: clicked > opened (no click) > emailed >24h (no open) > never-contacted.
    Cap: voice_dial_cap setting (default 50). Respects 11am–5pm local window.
    """
    from datetime import datetime, timezone, timedelta
    from database.client import get_voice_priority_queue, get_voice_priority_calls_today, get_setting, log_activity
    from utils.monitoring import upsert_heartbeat

    try:
        cap = int(get_setting("voice_dial_cap") or 50)
    except Exception:
        cap = 50

    # voice_dial_cap is a daily cap, but this job runs hourly — subtract what's
    # already gone out today so repeated runs can't each independently use the
    # full cap.
    already_called_today = get_voice_priority_calls_today()
    remaining_cap = max(0, cap - already_called_today)

    today_utc  = datetime.now(timezone.utc).date().isoformat()
    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    leads = get_voice_priority_queue(cap=remaining_cap) if remaining_cap else []
    called, skipped_tz, skipped_no_phone, errors = 0, 0, 0, 0

    from agents.email_personalizer import detect_market

    for lead in leads:
        if not lead.get("phone"):
            skipped_no_phone += 1
            continue

        # lead.market (DB column) is unpopulated for almost all leads — compute
        # fresh from phone+address so ambiguous city names (e.g. "Newcastle" is
        # NSW Australia, Washington State, and Newcastle upon Tyne UK) resolve
        # to the correct timezone window instead of defaulting to the wrong one.
        market = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
        if not is_voice_window(lead.get("city", ""), market):
            skipped_tz += 1
            continue

        tier = _lead_tier_label(lead, today_utc, cutoff_24h)
        try:
            call = place_click_call(lead)
            log_activity(str(lead["id"]), "outbound_call", {
                "dograh_run_id": call.get("workflow_run_id", ""),
                "trigger":       "voice_priority_queue",
                "tier":          tier,
                "pain_signal":   lead.get("pain_signal", ""),
                "phone":         lead["phone"],
            })
            called += 1
            log.info("Priority call placed: lead=%s tier=%s pain=%s", lead["id"], tier, lead.get("pain_score"))
        except Exception as exc:
            log.error("Priority call failed: lead=%s: %s", lead.get("id"), exc)
            errors += 1

    upsert_heartbeat("click_calls", {"called": called, "skipped_tz": skipped_tz, "errors": errors})
    return {
        "called": called,
        "skipped_outside_hours": skipped_tz,
        "skipped_no_phone": skipped_no_phone,
        "errors": errors,
    }
