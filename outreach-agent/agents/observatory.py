import os
from datetime import datetime, timezone, timedelta

from database.client import get_stats, get_client
from agents.outreach import send_whatsapp_message


def _yesterday_range():
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end   = start.replace(hour=23, minute=59, second=59)
    return start.isoformat(), end.isoformat()


def _get_yesterday_leads_added() -> int:
    db = get_client()
    start, end = _yesterday_range()
    result = (
        db.table("leads")
        .select("id", count="exact")
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    )
    return result.count or 0


def _get_yesterday_wa_sent() -> int:
    db = get_client()
    start, end = _yesterday_range()
    result = (
        db.table("lead_activities")
        .select("id", count="exact")
        .in_("type", ["wa_outreach_sent", "wa_followup_sent", "demo_booking_sent"])
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    )
    return result.count or 0


def _get_yesterday_wa_replies() -> int:
    db = get_client()
    start, end = _yesterday_range()
    result = (
        db.table("lead_activities")
        .select("id", count="exact")
        .eq("type", "wa_reply_received")
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    )
    return result.count or 0


def _get_dograh_calls_yesterday() -> tuple[int, float]:
    """Return (call_count, total_cost_usd) from outbound_call_completed activities yesterday."""
    db = get_client()
    start, end = _yesterday_range()
    try:
        result = (
            db.table("lead_activities")
            .select("detail")
            .eq("type", "outbound_call_completed")
            .gte("created_at", start)
            .lte("created_at", end)
            .execute()
        )
        rows = result.data or []
        total_cost = 0.0
        for row in rows:
            detail = row.get("detail") or {}
            cost_info = detail.get("cost_info") or {}
            if isinstance(cost_info, dict):
                total_cost += float(cost_info.get("total_cost", 0) or 0)
        return len(rows), round(total_cost, 4)
    except Exception:
        return 0, 0.0


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


def build_digest() -> str:
    stats              = get_stats()
    new_leads          = _get_yesterday_leads_added()
    wa_sent            = _get_yesterday_wa_sent()
    wa_replies         = _get_yesterday_wa_replies()
    call_count, cost   = _get_dograh_calls_yesterday()
    last_run           = _get_last_pipeline_run()

    today = datetime.now(timezone.utc).strftime("%d %b %Y")

    lines = [
        f"Apex Daily — {today}",
        "",
        f"Total leads: {stats['total_leads']}  |  Replied: {stats['replied']}  |  Converted: {stats['converted']}",
        f"Yesterday: {new_leads} new leads  |  {wa_sent} WA sent  |  {wa_replies} replies",
        f"Voice calls (yesterday): {call_count}  |  Est. cost: ${cost:.4f}",
        f"Email sequence active: {stats['in_sequence']}  |  Complete: {stats['sequence_complete']}",
        "",
        f"Last pipeline run: {last_run}",
    ]
    return "\n".join(lines)


def send_observatory_digest() -> str:
    recipient = (
        os.getenv("OBSERVATORY_WA_RECIPIENT")
        or os.getenv("FOUNDER_WHATSAPP_NUMBER")
    )
    if not recipient:
        raise RuntimeError("OBSERVATORY_WA_RECIPIENT and FOUNDER_WHATSAPP_NUMBER are both unset")
    digest = build_digest()
    send_whatsapp_message(recipient, digest)
    return digest
