"""
wa_broadcast.py — Scheduled WA broadcast to new (uncontacted) leads.

Runs hourly Mon–Fri via APScheduler. Only sends when the lead's local
time is within the WA window (8:30 AM – 7 PM). Caps at MAX_PER_RUN
per invocation so we never flood the Meta API or a single city at once.
"""

import logging
from collections import defaultdict

from agents.outreach import send_template_message, send_whatsapp_message
from agents.personalizer import generate_message
from agents.template_manager import LOGO_URL
from database.client import get_client, log_activity, mark_contacted
from utils.timezone import is_wa_window

# Maps business_type → (template_name, image_url | None).
_V1: dict[str, tuple[str, str | None]] = {
    "dentist":         ("apex_outreach_dentist_v1",    None),
    "salon":           ("apex_outreach_salon_v1",      None),
    "accountant":      ("apex_outreach_accountant_v1", None),
    "physiotherapist": ("apex_outreach_physio_v1",     None),
    "lawyer":          ("apex_outreach_lawyer_v1",     None),
    "doctor":          ("apex_outreach_doctor_v1",     None),
}

# v3 = logo header + Henry sign-off + Stop quick-reply + 3 CTA buttons (pending approval)
_V3: dict[str, tuple[str, str | None]] = {
    "dentist":         ("apex_outreach_dentist_v3",    LOGO_URL),
    "salon":           ("apex_outreach_salon_v3",      LOGO_URL),
    "accountant":      ("apex_outreach_accountant_v3", LOGO_URL),
    "physiotherapist": ("apex_outreach_physio_v3",     LOGO_URL),
    "lawyer":          ("apex_outreach_lawyer_v3",     LOGO_URL),
    "doctor":          ("apex_outreach_doctor_v3",     LOGO_URL),
}

# v3 approved 2026-06-13 — logo + Henry + Stop button.
VERTICAL_TEMPLATE = _V3

_STOP_WORDS = {
    "dental", "dentistry", "clinic", "salon", "spa", "studio", "center", "centre",
    "physiotherapy", "physio", "therapy", "accounting", "accountants", "accountant",
    "law", "legal", "firm", "associates", "partners", "office", "medical",
    "health", "care", "services", "group", "practice", "dr.", "dr",
}


def _greeting_name(business_name: str) -> str:
    """Extract a short first-word greeting from a business name, skipping generic suffixes."""
    words = [w for w in business_name.split() if w.lower().rstrip(".,") not in _STOP_WORDS]
    return words[0] if words else business_name.split()[0]

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
            btype = lead.get("business_type", "").lower()
            entry = VERTICAL_TEMPLATE.get(btype)

            if entry:
                template_name, image_url = entry
                greeting = _greeting_name(lead["name"])
                send_template_message(phone, template_name, [greeting, lead["name"]], image_url=image_url)
                stored_message = f"[Template: {template_name}] {greeting} / {lead['name']}"
            else:
                # Fallback for verticals without an approved template (free-form, session only)
                log.warning("No approved template for vertical '%s', using free-form", btype)
                stored_message = generate_message(
                    name=lead["name"],
                    business_type=btype,
                    city=city,
                )
                send_whatsapp_message(phone, stored_message)

            mark_contacted(str(lead["id"]), stored_message)
            used_template = template_name if entry else "free_form"
            log_activity(str(lead["id"]), "wa_outreach_sent", {
                "trigger": "broadcast_cron",
                "city": city,
                "template": used_template,
            })
            sent += 1
            log.info("WA broadcast sent to %s (%s) via %s", lead["name"], city, used_template)
        except Exception as exc:
            log.error("WA broadcast failed for lead %s: %s", lead.get("id"), exc)
            errors += 1

    return {
        "sent": sent,
        "skipped_outside_hours": skipped_hours,
        "skipped_no_phone": skipped_no_phone,
        "errors": errors,
    }
