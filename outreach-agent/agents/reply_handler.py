import os
import anthropic

_INTENT_PROMPT = """\
You received a WhatsApp reply to a sales outreach message for PracticeDesk — an AI-powered \
practice management platform for health and professional practices.

Reply text:
"{message}"

Classify the sender's intent into EXACTLY one of these words and nothing else:
interested
not_interested
question
out_of_office
"""

_REPLY_PROMPT = """\
You are Henry, a helpful assistant from PracticeDesk — an AI-powered practice management \
platform for {business_type}s.

A prospect called "{business_name}" has sent this WhatsApp message:
"{message}"

Write a short, helpful reply (2–3 sentences). Answer their question directly using what you \
know about PracticeDesk: it automates appointment reminders, booking confirmations, and \
client follow-ups via WhatsApp. Do not use emojis. End with a soft invitation to book a \
free demo. Reply with only the message text.
"""

_DEMO_MESSAGE = (
    "Hi {name}, thanks for your interest in PracticeDesk! "
    "You can book a free 15-minute demo here — I'll walk you through how it works for your practice: {url}"
)


def classify_intent(message: str) -> str:
    """Returns one of: interested | not_interested | question | out_of_office."""
    from agents._master_prompt import MASTER_PROMPT_LITE
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=MASTER_PROMPT_LITE,
        messages=[{"role": "user", "content": _INTENT_PROMPT.format(message=message)}],
    )
    intent = result.content[0].text.strip().lower()
    valid = {"interested", "not_interested", "question", "out_of_office"}
    return intent if intent in valid else "question"


def generate_reply(message: str, business_name: str, business_type: str) -> str:
    """Generate a helpful reply to a prospect's question."""
    from agents._master_prompt import compose
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = _REPLY_PROMPT.format(
        business_type=business_type,
        business_name=business_name,
        message=message,
    )
    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=compose(),
        messages=[{"role": "user", "content": prompt}],
    )
    return result.content[0].text.strip()


def get_demo_message(business_name: str) -> str:
    url = os.getenv("CAL_BOOKING_URL", "https://cal.com/neeraj-khattar-3zszap/practicedesk-demo")
    return _DEMO_MESSAGE.format(name=business_name, url=url)
