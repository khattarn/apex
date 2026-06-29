"""
email_poller.py — IMAP poller for info@practicedesk.live (GoDaddy Titan)

Runs every 15 minutes via APScheduler (7 days). Fetches UNSEEN emails,
matches senders against the leads table, and processes replies automatically:
  - status → replied
  - logs email_reply_received activity
  - sends WhatsApp + email alert to founder

Unknown senders are left UNSEEN so they remain visible in the Titan inbox.
Only lead-reply emails are marked SEEN after processing.
"""

import email
import imaplib
import logging
import os
import re
from email.header import decode_header

log = logging.getLogger(__name__)

IMAP_HOST = "imap.secureserver.net"
IMAP_PORT = 993
EMAIL_ADDR = os.getenv("GODADDY_EMAIL_ADDRESS", "info@practicedesk.live")
EMAIL_PASS = os.getenv("GODADDY_EMAIL_PASSWORD", "")


def _decode_str(value: str) -> str:
    parts = decode_header(value or "")
    out = []
    for part, charset in parts:
        if isinstance(part, bytes):
            out.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(part)
    return " ".join(out).strip()


def _extract_email(raw: str) -> str:
    """Pull bare address from 'Name <addr>' or plain 'addr'."""
    m = re.search(r"<([^>]+)>", raw)
    return (m.group(1) if m else raw).strip().lower()


def _get_body(msg) -> str:
    """Return plain-text body, up to 2000 chars."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")[:2000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")[:2000]
    return ""


def poll_email_replies() -> dict:
    """
    Connect to GoDaddy Titan, read UNSEEN emails, process replies from known leads.
    Returns { processed, skipped, errors }.
    """
    if not EMAIL_PASS:
        log.warning("email_poller: GODADDY_EMAIL_PASSWORD not set — skipping")
        return {"processed": 0, "skipped": 0, "errors": 0}

    processed = skipped = errors = 0

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL_ADDR, EMAIL_PASS)
        mail.select("INBOX")

        _, data = mail.search(None, "UNSEEN")
        msg_ids = data[0].split()

        if not msg_ids:
            mail.logout()
            return {"processed": 0, "skipped": 0, "errors": 0}

        log.info("email_poller: %d unseen email(s) to check", len(msg_ids))

        from database.client import get_client, update_lead, log_activity
        db = get_client()

        for msg_id in msg_ids:
            try:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                from_email = _extract_email(msg.get("From", ""))
                subject    = _decode_str(msg.get("Subject", ""))
                body_text  = _get_body(msg)

                if not from_email:
                    skipped += 1
                    continue

                # Look up sender in leads table
                row = (
                    db.table("leads")
                    .select("id, name, business_type, status")
                    .ilike("email", from_email)
                    .limit(1)
                    .execute()
                )

                if not row.data:
                    # Not one of our leads — leave UNSEEN so it stays visible in Titan
                    skipped += 1
                    continue

                lead    = row.data[0]
                lead_id = str(lead["id"])
                name    = lead.get("name", "")
                btype   = lead.get("business_type", "practice")

                if lead.get("status") not in ("replied", "converted", "dead"):
                    update_lead(lead_id, {"status": "replied"})

                log_activity(lead_id, "email_reply_received", {
                    "from_email": from_email,
                    "subject":    subject,
                    "body":       body_text[:500],
                    "source":     "imap_poll",
                })

                try:
                    from utils.notifier import notify_founder
                    notify_founder(
                        kind="system_alert", severity="info",
                        component="email_reply",
                        reason=(
                            f"Email reply from {name} ({btype})\n"
                            f"From: {from_email}\n"
                            f"Subject: {subject}\n\n"
                            f"{body_text[:500]}"
                        ),
                    )
                except Exception:
                    pass

                # Mark as SEEN — processed, won't re-run on next poll
                mail.store(msg_id, "+FLAGS", "\\Seen")
                processed += 1
                log.info("email_poller: reply from %s (lead %s) processed", from_email, lead_id)

            except Exception as exc:
                log.error("email_poller: error on message %s: %s", msg_id, exc)
                errors += 1

        mail.logout()

    except imaplib.IMAP4.error as exc:
        log.error("email_poller: IMAP auth/connection error: %s", exc)
        errors += 1
    except Exception as exc:
        log.error("email_poller: unexpected error: %s", exc)
        errors += 1

    return {"processed": processed, "skipped": skipped, "errors": errors}
