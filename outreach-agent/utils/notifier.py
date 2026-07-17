"""
notify_founder() — dual-channel founder intimation (Change #5).

Email is the always-on fail-safe. WhatsApp uses two Meta UTILITY templates
submitted via submit_founder_templates.py:
  apex_daily_brief   — 1 variable: digest text (truncated to 1024 chars)
  apex_system_alert  — 3 variables: icon, component, reason

WA sends are best-effort: any error is logged at INFO and swallowed so email
delivery is never blocked by a broken WA token.
"""
import logging
import os
import requests

log = logging.getLogger(__name__)

_FOUNDER_EMAIL = os.getenv("FOUNDER_EMAIL", "khattarn3@yahoo.com")
_FOUNDER_WA    = os.getenv("FOUNDER_WHATSAPP_NUMBER", "")

_TEMPLATE_DAILY_BRIEF  = "apex_daily_ping"   # apex_daily_brief was auto-recategorized
                                              # MARKETING by Meta after approval (unappealable
                                              # once approved) and got silently throttled by
                                              # Meta's marketing-message engagement limits —
                                              # this replacement is a short UTILITY-style ping
                                              # instead of the full digest text.
_TEMPLATE_SYSTEM_ALERT = "apex_system_alert"
_TEMPLATE_CALL_OUTCOME = "apex_call_outcome"

_SEVERITY_ICONS = {"critical": "🔴", "warning": "🟠", "info": "✅", "degraded": "🟡"}


def notify_founder(
    kind: str,
    body: str = "",
    severity: str = "info",
    component: str = "",
    reason: str = "",
    label: str = "",
    lead_line: str = "",
    detail: str = "",
    summary=None,
    recording_url: str = "",
) -> None:
    """
    Send to email (always) + WhatsApp (best-effort via approved template).

    kind="daily_brief"   — body = full digest text (email only); summary = dict with
                            new_leads/calls/emails_sent counts for the short WA ping
    kind="system_alert"  — severity / component / reason filled in
    kind="call_outcome"  — label / lead_line / detail / summary / recording_url filled in
    """
    if kind == "daily_brief":
        _send_email_brief(body)
        _send_wa_brief(summary or {})
    elif kind == "system_alert":
        msg = reason or f"{severity.upper()}: {component}"
        _send_email_alert(severity, component, msg)
        _send_wa_alert(severity, component, msg)
    elif kind == "call_outcome":
        _send_email_call_outcome(label, lead_line, detail, summary, recording_url)
        _send_wa_call_outcome(label, lead_line, detail, summary, recording_url)
    else:
        log.warning("notify_founder: unknown kind=%s", kind)


# ---------------------------------------------------------------------------
# Email paths (Resend — always fires)
# ---------------------------------------------------------------------------

def _send_email_brief(body: str) -> bool:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        log.warning("notify_founder: RESEND_API_KEY not set — email brief skipped")
        return False
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%-d %b %Y")
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "from":    "Apex Observatory <observatory@practicedesk.live>",
                "to":      [_FOUNDER_EMAIL],
                "subject": f"Apex Daily — {date_str}",
                "text":    body,
            },
            timeout=15,
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            log.warning("Email brief delivery failed: HTTP %s", resp.status_code)
        return ok
    except Exception as exc:
        log.warning("Email brief delivery error: %s", exc)
        return False


def _send_email_call_outcome(
    label: str, lead_line: str, detail: str, summary: str, recording_url: str
) -> bool:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        log.warning("notify_founder: RESEND_API_KEY not set — email call_outcome skipped")
        return False
    lines = [lead_line]
    if detail:
        lines.append(detail)
    if summary:
        lines.append(f"Summary: {summary}")
    if recording_url:
        lines.append(f"Recording: {recording_url}")
    text = "\n\n".join(lines)
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "from":    "Apex Observatory <observatory@practicedesk.live>",
                "to":      [_FOUNDER_EMAIL],
                "subject": f"{label} — Apex",
                "text":    text,
            },
            timeout=15,
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            log.warning("Email call_outcome delivery failed: HTTP %s", resp.status_code)
        return ok
    except Exception as exc:
        log.warning("Email call_outcome delivery error: %s", exc)
        return False


def _send_email_alert(severity: str, component: str, message: str) -> bool:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        log.warning("notify_founder: RESEND_API_KEY not set — email alert skipped")
        return False
    icon = _SEVERITY_ICONS.get(severity, "⚪")
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "from":    "Apex Observatory <observatory@practicedesk.live>",
                "to":      [_FOUNDER_EMAIL],
                "subject": f"{icon} Apex Alert — {component}",
                "text":    message,
            },
            timeout=15,
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            log.warning("Email alert delivery failed: HTTP %s", resp.status_code)
        return ok
    except Exception as exc:
        log.warning("Email alert delivery error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# WhatsApp paths (best-effort, via Meta UTILITY templates)
# ---------------------------------------------------------------------------

def _wa_headers() -> dict:
    # WHATSAPP_ACCESS_TOKEN is the outreach number token (matches agents/outreach.py).
    # WHATSAPP_TOKEN is a legacy var for the India/PracticeDesk number — do not use here.
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _wa_phone_id() -> str:
    return os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", "")


def _send_wa_brief(summary: dict) -> bool:
    if not _FOUNDER_WA or not _wa_phone_id():
        return False
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%-d %b %Y")
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{_wa_phone_id()}/messages",
            headers=_wa_headers(),
            json={
                "messaging_product": "whatsapp",
                "to":   _FOUNDER_WA,
                "type": "template",
                "template": {
                    "name":     _TEMPLATE_DAILY_BRIEF,
                    "language": {"code": "en"},
                    "components": [{
                        "type": "body",
                        # body: "Apex Daily Report — {{1}}\n\nNew leads: {{2}} |
                        # Calls placed: {{3}} | Emails sent: {{4}}\n\nFull report
                        # sent to your inbox and available on the Apex dashboard."
                        "parameters": [
                            {"type": "text", "text": date_str},
                            {"type": "text", "text": str(summary.get("new_leads", 0))},
                            {"type": "text", "text": str(summary.get("calls", 0))},
                            {"type": "text", "text": str(summary.get("emails_sent", 0))},
                        ],
                    }],
                },
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.info(
            "WA brief template not yet approved or failed (HTTP %s) — email is the record",
            resp.status_code,
        )
        return False
    except Exception as exc:
        log.info("WA brief send skipped: %s", exc)
        return False


def _send_wa_call_outcome(
    label: str, lead_line: str, detail: str, summary: str, recording_url: str
) -> bool:
    if not _FOUNDER_WA or not _wa_phone_id():
        return False
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{_wa_phone_id()}/messages",
            headers=_wa_headers(),
            json={
                "messaging_product": "whatsapp",
                "to":   _FOUNDER_WA,
                "type": "template",
                "template": {
                    "name":     _TEMPLATE_CALL_OUTCOME,
                    "language": {"code": "en"},
                    "components": [{
                        "type": "body",
                        # Body: "Outcome: {{1}}\nLead: {{2}}\nDetail: {{3}}\nCall summary: {{4}}\nRecording link: {{5}}"
                        "parameters": [
                            {"type": "text", "text": label or "-"},
                            {"type": "text", "text": lead_line or "-"},
                            {"type": "text", "text": detail or "-"},
                            {"type": "text", "text": (summary or "-")[:500]},
                            {"type": "text", "text": recording_url or "-"},
                        ],
                    }],
                },
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.info(
            "WA call_outcome template not yet approved or failed (HTTP %s) — email is the record",
            resp.status_code,
        )
        return False
    except Exception as exc:
        log.info("WA call_outcome send skipped: %s", exc)
        return False


def _send_wa_alert(severity: str, component: str, message: str) -> bool:
    if not _FOUNDER_WA or not _wa_phone_id():
        return False
    icon = _SEVERITY_ICONS.get(severity, "⚪")
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{_wa_phone_id()}/messages",
            headers=_wa_headers(),
            json={
                "messaging_product": "whatsapp",
                "to":   _FOUNDER_WA,
                "type": "template",
                "template": {
                    "name":     _TEMPLATE_SYSTEM_ALERT,
                    "language": {"code": "en"},
                    "components": [{
                        "type": "body",
                        # {{1}}=severity, {{2}}=component, {{3}}=reason
                        # body: "Apex Platform Alert\n\nSeverity: {{1}}\nComponent: {{2}}\n\n{{3}}\n\nCheck Railway logs..."
                        "parameters": [
                            {"type": "text", "text": severity.upper()},
                            {"type": "text", "text": component},
                            {"type": "text", "text": message[:500]},
                        ],
                    }],
                },
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.info(
            "WA alert template not yet approved or failed (HTTP %s) — email is the record",
            resp.status_code,
        )
        return False
    except Exception as exc:
        log.info("WA alert send skipped: %s", exc)
        return False
