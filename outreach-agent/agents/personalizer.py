import os
import anthropic
from database.client import get_setting

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


def generate_message(name: str, business_type: str, city: str) -> str:
    # DB setting in Settings UI overrides yaml (allows quick edits without redeploy)
    db_template = get_setting("whatsapp_prompt_template")
    if db_template:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        prompt = db_template.format(name=name, business_type=business_type, city=city)
        from agents._master_prompt import compose
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=compose(),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # Load template from assets/copy.yaml
    copy = _load_copy()
    verticals = copy.get('verticals', {})
    vertical = verticals.get(business_type) or copy.get('defaults', {})
    template = vertical.get('wa_message', '')

    if template:
        return template.format(name=name, city=city).strip()

    # Final fallback: Claude with generic prompt
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    fallback_prompt = (
        f"Write a short WhatsApp message to a {business_type} called \"{name}\" in {city}. "
        "You work for PracticeDesk, an AI-powered practice management platform. "
        "Mention one specific pain point for their business type and end with a soft call to action. "
        "Keep it under 150 words. Reply with only the message text."
    )
    from agents._master_prompt import compose
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=compose(),
        messages=[{"role": "user", "content": fallback_prompt}],
    )
    return msg.content[0].text.strip()
