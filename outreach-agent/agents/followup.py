import os
import anthropic
from database.client import get_setting

DEFAULT_FOLLOWUP_TEMPLATE = (
    "You are writing a short follow-up WhatsApp message to a {business_type} called \"{name}\" "
    "in {city}. You work for PracticeDesk, an AI-powered practice management platform. "
    "You sent them a message 3 days ago with no response — they may have been busy. "
    "Write a 1-2 sentence friendly follow-up that acknowledges they may be busy and briefly "
    "restates how PracticeDesk reduces no-shows and admin work. "
    "Do not use emojis. Keep it under 80 words. Reply with only the message text."
)


def generate_followup_message(name: str, business_type: str, city: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    template = get_setting("whatsapp_followup_template") or DEFAULT_FOLLOWUP_TEMPLATE
    prompt = template.format(name=name, business_type=business_type, city=city)

    from agents._master_prompt import compose
    from agents.agent_prompts import get_prompt
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=compose(get_prompt("followup")),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
