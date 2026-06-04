import os
import requests

_RESEND_URL = "https://api.resend.com/emails"


def send_email(to: str, subject: str, html: str) -> dict:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("OUTREACH_FROM_EMAIL", "Neeraj at PracticeDesk <neeraj@practicedesk.live>")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set")

    resp = requests.post(
        _RESEND_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"from": from_email, "to": [to], "subject": subject, "html": html, "reply_to": "info@practicedesk.live"},
        timeout=15,
    )

    if not resp.ok:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")

    return resp.json()
