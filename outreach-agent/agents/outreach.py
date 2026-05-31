import os
import requests


def send_whatsapp_message(phone: str, message: str) -> bool:
    phone_number_id = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not phone_number_id or not access_token:
        raise RuntimeError("OUTREACH_WA_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN must be set")

    # Normalise phone — strip spaces, dashes; ensure leading +
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

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
