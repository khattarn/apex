import os
import requests

_RESEND_URL = "https://api.resend.com/emails"


class QuotaExceededError(RuntimeError):
    """Raised when Resend returns 429 daily_quota_exceeded."""


def send_email(to: str, subject: str, html: str) -> dict:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("OUTREACH_FROM_EMAIL", "Henry from PracticeDesk <info@practicedesk.live>")
    # reply_to must match from_email so replies land in one predictable inbox.
    # Override separately only if needed; never split from/reply-to across two addresses.
    reply_to = os.getenv("OUTREACH_REPLY_TO", from_email)

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set")

    resp = requests.post(
        _RESEND_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"from": from_email, "to": [to], "subject": subject, "html": html, "reply_to": reply_to},
        timeout=15,
    )

    if resp.status_code == 429:
        raise QuotaExceededError(f"Resend daily quota exceeded — try again tomorrow")

    if not resp.ok:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")

    return resp.json()
