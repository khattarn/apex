import os
import requests


def send_whatsapp_message(phone: str, message: str, phone_number_id: str | None = None) -> bool:
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

    # Normalise phone — strip spaces, dashes; ensure leading +
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    # Auto-route: +91 numbers use the Indian WA number when configured
    if phone_number_id is None:
        if cleaned.startswith("+91") and os.getenv("INDIA_WA_PHONE_NUMBER_ID"):
            phone_number_id = os.getenv("INDIA_WA_PHONE_NUMBER_ID")
        else:
            phone_number_id = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID")

    if not phone_number_id or not access_token:
        raise RuntimeError("WhatsApp phone_number_id and WHATSAPP_ACCESS_TOKEN must be set")

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": cleaned,
        "type": "text",
        "text": {"body": message},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response.status_code == 200:
        return True

    error = response.json().get("error", {})
    raise RuntimeError(f"WhatsApp API error {response.status_code}: {error.get('message', response.text)}")


def send_template_message(
    phone: str,
    template_name: str,
    body_params: list[str],
    phone_number_id: str | None = None,
    image_url: str | None = None,
) -> bool:
    """Send a Meta-approved template message. Use for all business-initiated contacts.

    Pass image_url for templates that have an IMAGE header component (v2 templates).
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    if phone_number_id is None:
        if cleaned.startswith("+91") and os.getenv("INDIA_WA_PHONE_NUMBER_ID"):
            phone_number_id = os.getenv("INDIA_WA_PHONE_NUMBER_ID")
        else:
            phone_number_id = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID")

    if not phone_number_id or not access_token:
        raise RuntimeError("WhatsApp phone_number_id and WHATSAPP_ACCESS_TOKEN must be set")

    components = []
    if image_url:
        components.append({
            "type": "header",
            "parameters": [{"type": "image", "image": {"link": image_url}}],
        })
    components.append({
        "type": "body",
        "parameters": [{"type": "text", "text": p} for p in body_params],
    })

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": cleaned,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": components,
        },
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response.status_code == 200:
        return True

    error = response.json().get("error", {})
    raise RuntimeError(f"WhatsApp template API error {response.status_code}: {error.get('message', response.text)}")
