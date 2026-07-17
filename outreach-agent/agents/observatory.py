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
    """Returns (sophie_calls, voice_followup_calls, total_cost)."""
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
        sophie = sum(1 for r in rows if r.get("type") in ("outbound_call_completed", "outbound_call_placed"))
        vf   = sum(1 for r in rows if r.get("type") == "voice_followup_placed")
        cost = 0.0
        for r in rows:
            detail   = r.get("detail") or {}
            cost_info = detail.get("cost_info") or {}
            if isinstance(cost_info, dict):
                cost += float(cost_info.get("total_cost", 0) or 0)
        return sophie, vf, round(cost, 4)
    except Exception:
        return 0, 0, 0.0


def _get_emails_detail(start: str, end: str) -> tuple[int, int, int]:
    """Returns (sent, opened, clicked) in last 24h."""
    db = get_client()
    try:
        rows = (
            db.table("email_sends")
            .select("opened_at, clicked_at")
            .gte("sent_at", start)
            .lte("sent_at", end)
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


def _get_sprint_funnel(start: str, end: str) -> dict:
    """Returns demos booked and email replies in the last 24h."""
    db = get_client()
    demos = (
        db.table("lead_activities")
        .select("id", count="exact")
        .in_("type", ["demo_booked", "demo_booking_sent"])
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    ).count or 0
    email_replies = (
        db.table("lead_activities")
        .select("id", count="exact")
        .eq("type", "email_reply_received")
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    ).count or 0
    trial_starts = (
        db.table("lead_activities")
        .select("id", count="exact")
        .in_("type", ["booked_demo_manually", "demo_booked"])
        .gte("created_at", start)
        .lte("created_at", end)
        .execute()
    ).count or 0
    return {"demos": demos, "email_replies": email_replies, "trial_starts": trial_starts}


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


def _get_call_log(start: str, end: str, limit: int = 25) -> tuple[list[dict], int]:
    """Per-call detail for every Sophie outbound call completed in the window."""
    db = get_client()
    try:
        rows = (
            db.table("lead_activities")
            .select("lead_id, detail, created_at")
            .eq("type", "outbound_call_completed")
            .gte("created_at", start)
            .lte("created_at", end)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )
    except Exception:
        return [], 0
    if not rows:
        return [], 0

    lead_ids = list({r["lead_id"] for r in rows if r.get("lead_id")})
    leads_by_id = {}
    if lead_ids:
        lead_rows = (
            db.table("leads")
            .select("id, name, business_type, city")
            .in_("id", lead_ids)
            .execute()
            .data or []
        )
        leads_by_id = {l["id"]: l for l in lead_rows}

    calls = []
    for r in rows[:limit]:
        lead   = leads_by_id.get(r.get("lead_id"), {})
        detail = r.get("detail") or {}
        cost   = (detail.get("cost_info") or {}).get("total_cost", 0)
        calls.append({
            "time":          (r.get("created_at") or "")[11:16],
            "name":          lead.get("name") or "Unknown lead",
            "business_type": lead.get("business_type") or "",
            "city":          lead.get("city") or "",
            "outcome":       detail.get("call_outcome") or "unknown",
            "ended_reason":  detail.get("ended_reason") or "",
            "cost":          float(cost or 0),
            "recording_url": detail.get("recording_url") or "",
        })
    return calls, len(rows)


def build_digest() -> tuple[str, dict]:
    start, end = _last_24h_range()
    stats = get_stats()

    new_leads                    = _get_leads_added(start, end)
    wa_broadcast                 = _count_activities(["wa_outreach_sent"], start, end)
    wa_followup                  = _count_activities(["wa_followup_sent"], start, end)
    sophie_calls, vf_calls, cost = _get_calls_detail(start, end)
    emails_sent, opened, clicked = _get_emails_detail(start, end)
    replies, interested, not_int = _get_wa_replies_detail(start, end)
    sprint                       = _get_sprint_funnel(start, end)
    last_run                     = _get_last_pipeline_run()
    call_log, call_log_total     = _get_call_log(start, end)

    today = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    lines = [
        f"Apex Daily — {today}",
        "",
        "── SPRINT FUNNEL (last 24h) ────────────",
        f"Prospected (new leads):  {new_leads}",
        f"Emailed:                 {emails_sent}  (opened: {opened} · clicked: {clicked})",
        f"Replies — WA: {replies}  (interested: {interested})  |  Email: {sprint['email_replies']}",
        f"Demos booked:            {sprint['demos']}",
        f"Trial starts:            {sprint['trial_starts']}",
        "",
        "── OUTREACH (last 24h) ─────────────────",
        f"WA broadcast sent:       {wa_broadcast}",
        f"WA follow-up sent:       {wa_followup}",
        f"Sophie outbound calls:   {sophie_calls}",
        f"Voice follow-up calls:   {vf_calls}",
        f"  Est. call cost:        ${cost:.4f}",
        "",
        "── OUTBOUND CALL LOG (last 24h) ────────",
    ]
    if call_log:
        for c in call_log:
            loc = ", ".join(p for p in (c["business_type"], c["city"]) if p)
            lines.append(
                f"{c['time']} UTC  {c['name']} ({loc}) — {c['outcome']} "
                f"[{c['ended_reason']}]  ${c['cost']:.4f}"
            )
            if c["recording_url"]:
                lines.append(f"           {c['recording_url']}")
        if call_log_total > len(call_log):
            lines.append(f"... and {call_log_total - len(call_log)} more (see dashboard)")
    else:
        lines.append("No outbound calls completed.")
    lines += [
        "",
        "── CUMULATIVE TOTALS ───────────────────",
        f"Total leads:  {stats['total_leads']}  |  Replied: {stats['replied']}  |  Converted: {stats['converted']}",
        f"Email seq active: {stats.get('in_sequence', 0)}  |  Complete: {stats.get('sequence_complete', 0)}",
        "",
        "── LAST PIPELINE RUN ───────────────────",
        last_run,
    ]
    summary = {
        "new_leads":  new_leads,
        "calls":      sophie_calls + vf_calls,
        "emails_sent": emails_sent,
    }
    return "\n".join(lines), summary


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
    digest, summary = build_digest()

    # Always persist to DB — readable from dashboard
    _store_digest(digest)

    # Dual-channel delivery: email always fires (full digest incl. call log);
    # WA sends a short ping (see notifier.py) since the full digest triggered
    # Meta's marketing-message classifier and got silently throttled.
    from utils.notifier import notify_founder
    notify_founder(kind="daily_brief", body=digest, summary=summary)

    return digest
