import logging
import os

log = logging.getLogger(__name__)


def alert_founder(job_name: str, exc: Exception) -> None:
    """WA alert to founder when a scheduled job fails. Never raises."""
    recipient = os.getenv("OBSERVATORY_WA_RECIPIENT") or os.getenv("FOUNDER_WHATSAPP_NUMBER")
    if not recipient:
        log.warning("alert_founder: no recipient env var set (OBSERVATORY_WA_RECIPIENT)")
        return
    try:
        from agents.outreach import send_whatsapp_message
        msg = (
            f"🚨 *Apex Job Failed*\n"
            f"Job: {job_name}\n"
            f"Error: {type(exc).__name__}: {str(exc)[:300]}"
        )
        send_whatsapp_message(recipient, msg)
    except Exception as e:
        log.error("alert_founder could not deliver: %s", e)
