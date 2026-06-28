import logging
import os
from datetime import datetime, timezone, timedelta

from database.client import get_stats, get_client

log = logging.getLogger(__name__)


def _last_24h_range():
    now   = datetime.now(timezone.utc)
    start = (now - timedelta(hours=24)).isoformat()
    end   = now.isoformat()
    return start, end


def _get_last_pipeline_run() -> str:
    db = get_client()
    result = (
        db.table("campaign_runs")
        .select("created_at, business_type, city, mode, messages_sent")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return "No runs yet"
    run = result.data[0]
    ts = run.get("created_at", "")[:16].replace("T", " ")
    return f"{ts} UTC — {run.get('city', '?')} {run.get('business_type', '?')} ({run.get('mode', '?')})"


def _count_activities(types: list[str], start: str, end: str) -> int:
    db = get_client()
    result = (
        db.table("lead_activities")
        .select("id", count="exact")
        .in_("type", types)
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    )
    return result.count or 0


def _get_calls_detail(start: str, end: str) -> tuple[int, int, float]:
    """Returns (aria_calls, voice_followup_calls, total_cost)."""
    db = get_client()
    try:
        rows = (
            db.table("lead_activities")
            .select("type, detail")
            .in_("type", ["outbound_call_completed", "voice_followup_placed", "outbound_call_placed"])
            .gte("created_at", start)
            .lte("created_at", end)
            .execute()
            .data or []
        )
        aria = sum(1 for r in rows if r.get("type") in ("outbound_call_completed", "outbound_call_placed"))
        vf   = sum(1 for r in rows if r.get("type") == "voice_followup_placed")
        cost = 0.0
        for r in rows:
            detail   = r.get("detail") or {}
            cost_info = detail.get("cost_info") or {}
            if isinstance(cost_info, dict):
                cost += float(cost_info.get("total_cost", 0) or 0)
        return aria, vf, round(cost, 4)
    except Exception:
        return 0, 0, 0.0


def _get_emails_detail(start: str, end: str) -> tuple[int, int, int]:
    """Returns (sent, opened, clicked) in last 24h."""
    db = get_client()
    try:
        rows = (
            db.table("email_sends")
            .select("opened_at, clicked_at")
            .gte("created_at", start)
            .lte("created_at", end)
            .execute()
            .data or []
        )
        sent    = len(rows)
        opened  = sum(1 for r in rows if r.get("opened_at"))
        clicked = sum(1 for r in rows if r.get("clicked_at"))
        return sent, opened, clicked
    except Exception:
        return 0, 0, 0


def _get_wa_replies_detail(start: str, end: str) -> tuple[int, int, int]:
    """Returns (total_replies, interested, not_interested) in last 24h."""
    db = get_client()
    try:
        rows = (
            db.table("lead_activities")
            .select("detail")
            .eq("type", "wa_reply_received")
            .gte("created_at", start)
            .lte("created_at", end)
            .execute()
            .data or []
        )
        interested     = sum(1 for r in rows if (r.get("detail") or {}).get("intent") == "interested")
        not_interested = sum(1 for r in rows if (r.get("detail") or {}).get("intent") == "not_interested")
        return len(rows), interested, not_interested
    except Exception:
        return 0, 0, 0


def _get_leads_added(start: str, end: str) -> int:
    db = get_client()
    result = (
        db.table("leads")
        .select("id", count="exact")
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    )
    return result.count or 0


def build_digest() -> str:
    start, end = _last_24h_range()
    stats = get_stats()

    new_leads                    = _get_leads_added(start, end)
    wa_broadcast                 = _count_activities(["wa_outreach_sent"], start, end)
    wa_followup                  = _count_activities(["wa_followup_sent"], start, end)
    demo_sent                    = _count_activities(["demo_booking_sent"], start, end)
    aria_calls, vf_calls, cost   = _get_calls_detail(start, end)
    emails_sent, opened, clicked = _get_emails_detail(start, end)
    replies, interested, not_int = _get_wa_replies_detail(start, end)
    last_run                     = _get_last_pipeline_run()

    today = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    lines = [
        f"Apex Daily — {today}",
        "",
        "── LAST 24 HOURS ──────────────────────",
        f"Leads added:           {new_leads}",
        f"WA broadcast sent:     {wa_broadcast}",
        f"WA follow-up sent:     {wa_followup}",
        f"Demo booking msgs:     {demo_sent}",
        f"Aria outbound calls:   {aria_calls}",
        f"Voice follow-up calls: {vf_calls}",
        f"  Est. call cost:      ${cost:.4f}",
        f"Emails sent:           {emails_sent}  (opened: {opened} · clicked: {clicked})",
        f"WA replies received:   {replies}  (interested: {interested} · not interested: {not_int})",
        "",
        "── CUMULATIVE TOTALS ───────────────────",
        f"Total leads:  {stats['total_leads']}  |  Replied: {stats['replied']}  |  Converted: {stats['converted']}",
        f"Email seq active: {stats.get('in_sequence', 0)}  |  Complete: {stats.get('sequence_complete', 0)}",
        "",
        "── LAST PIPELINE RUN ───────────────────",
        last_run,
    ]
    return "\n".join(lines)


def _store_digest(digest: str) -> None:
    """Persist digest to settings table so it's readable from the dashboard."""
    try:
        db = get_client()
        db.table("settings").upsert({
            "key":        "last_observatory_digest",
            "value":      digest,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as exc:
        log.warning("Observatory: could not store digest in settings: %s", exc)


def send_observatory_digest() -> str:
    digest = build_digest()

    # Always persist to DB — readable from dashboard
    _store_digest(digest)

    # Dual-channel delivery: email always fires; WA via approved template (best-effort)
    from utils.notifier import notify_founder
    notify_founder(kind="daily_brief", body=digest)

    return digest
