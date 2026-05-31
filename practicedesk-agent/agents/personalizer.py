import os
import anthropic
from database.client import get_setting

DEFAULT_TEMPLATE = (
    "You are writing a short, friendly WhatsApp message to a {business_type} called \"{name}\" "
    "in {city}. You work for PracticeDesk, an AI-powered practice management platform. "
    "Write a 2-3 sentence message that introduces PracticeDesk, mentions one specific pain point "
    "for their business type, and ends with a soft call to action. Do not use emojis. "
    "Keep it under 150 words. Reply with only the message text."
)


def generate_message(name: str, business_type: str, city: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    template = get_setting("whatsapp_prompt_template") or DEFAULT_TEMPLATE
    prompt = template.format(name=name, business_type=business_type, city=city)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
