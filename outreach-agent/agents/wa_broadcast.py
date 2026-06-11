"""
wa_broadcast.py — Scheduled WA broadcast to new (uncontacted) leads.

Runs hourly Mon–Fri via APScheduler. Only sends when the lead's local
time is within the WA window (8:30 AM – 7 PM). Caps at MAX_PER_RUN
per invocation so we never flood the Meta API or a single city at once.
"""

import logging
from collections import defaultdict

from agents.outreach import send_whatsapp_message
from agents.personalizer import generate_message
from database.client import get_client, log_activity, mark_contacted
from utils.timezone import is_wa_window

log = logging.getLogger(__name__)

MAX_PER_RUN = 30


def _get_pending_leads(limit: int = 300) -> list[dict]:
    db = get_client()
    return (
        db.table("leads")
        .select("id, name, phone, city, business_type, status")
        .or_("outreach_sent.eq.false,outreach_sent.is.null")
        .not_.in_("status", ["dead", "converted"])
        .not_.is_("phone", "null")
        .neq("phone", "")
        .limit(limit)
        .execute()
        .data
    ) or []


def pending_by_city() -> dict[str, int]:
    """Return {city: count} for all pending broadcast leads (for Live Activity)."""
    leads = _get_pending_leads(limit=2000)
    counts: dict[str, int] = defaultdict(int)
    for l in leads:
        counts[l.get("city", "unknown")] += 1
    return dict(counts)


def run_wa_broadcast() -> dict:
    leads = _get_pending_leads(limit=300)
    sent = skipped_hours = skipped_no_phone = errors = 0

    for lead in leads:
        if sent >= MAX_PER_RUN:
            break

        city = lead.get("city", "")
        if not is_wa_window(city):
            skipped_hours += 1
            continue

        phone = lead.get("phone", "")
        if not phone:
            skipped_no_phone += 1
            continue

        try:
            message = generate_message(
                name=lead["name"],
                business_type=lead.get("business_type", ""),
                city=city,
            )
            send_whatsapp_message(phone, message)
            mark_contacted(str(lead["id"]), message)
            log_activity(str(lead["id"]), "wa_outreach_sent", {
                "trigger": "broadcast_cron",
                "city": city,
            })
            sent += 1
            log.info("WA broadcast sent to %s (%s)", lead["name"], city)
        except Exception as exc:
            log.error("WA broadcast failed for lead %s: %s", lead.get("id"), exc)
            errors += 1

    return {
        "sent": sent,
        "skipped_outside_hours": skipped_hours,
        "skipped_no_phone": skipped_no_phone,
        "errors": errors,
    }
