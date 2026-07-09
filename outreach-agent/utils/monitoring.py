"""
Agent health monitoring — Change #4.

Public API:
  upsert_heartbeat(job, result)  — call on successful cron job completion
  run_watchdog()                 — hourly: cadence check + dependency probes + alerts
  probe_dependencies()           — ping each external service; returns {name: {ok, detail}}
  check_cadences()               — list overdue jobs with de-dup

SQL to create the backing table (run once in Supabase dashboard):
  database/migrations/001_agent_health.sql
"""
import logging
import os
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

# Maximum gap (hours) between successful runs before raising an alert.
# Set generously to avoid false positives across weekends / scheduled quiet periods.
CADENCE_HOURS: dict[str, int] = {
    "email_campaign":       14,   # runs at 22:00 and 13:00 UTC
    "wa_broadcast":         26,   # hourly Mon–Fri
    "wa_followup":          26,   # daily 9am UTC
    "voice_followup":       26,   # hourly Mon–Fri
    "observatory":          26,   # daily 1:30 UTC
    "prospect_cron":        26,   # daily 12:00 UTC
    "jobad_scout":          26,   # daily 14:00 UTC
    "signal_weekly":        200,  # Monday 6am UTC
    "click_calls":          26,   # hourly Mon–Fri
    "scheduled_callbacks":  6,    # every 15 min Mon–Fri — a stuck run means a promised callback is missed
}

_SEVERITY_CRITICAL = "critical"
_SEVERITY_WARNING  = "warning"
_SEVERITY_INFO     = "info"
_DEDUP_HOURS       = 6   # minimum gap between repeat alerts for the same job


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def upsert_heartbeat(job: str, result: dict) -> None:
    """
    Call at the END of a cron job's success path with counts/stats.
    Also fires a ✅ resolved notification if the job had a prior unresolved alert.
    """
    try:
        from database.client import get_client
        db = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Read existing row to check for a prior alert that needs resolving
        existing = db.table("agent_health").select("last_alert_kind").eq("job", job).execute()
        prior_alert_kind = None
        if existing.data:
            prior_alert_kind = existing.data[0].get("last_alert_kind")

        db.table("agent_health").upsert({
            "job":             job,
            "last_success_at": now,
            "last_run_at":     now,
            "last_result":     result,
            "last_alert_at":   None,   # clear dedup timer — job is healthy again
            "last_alert_kind": None,
            "updated_at":      now,
        }, on_conflict="job").execute()

        # Fire a resolved notification if this run clears a prior alert
        if prior_alert_kind:
            try:
                from utils.notifier import notify_founder
                notify_founder(
                    kind="system_alert",
                    severity="info",
                    component=job,
                    reason=f"✅ {job} recovered — completed successfully after prior {prior_alert_kind} alert.",
                )
            except Exception as exc:
                log.info("resolved notify skipped: %s", exc)

    except Exception as exc:
        log.warning("upsert_heartbeat failed for %s: %s", job, exc)


# ---------------------------------------------------------------------------
# Cadence check
# ---------------------------------------------------------------------------

def check_cadences() -> list[dict]:
    """
    Compare last_success_at vs expected cadence for every tracked job.
    Returns a list of {job, severity, message} for any overdue jobs.
    De-duped: a job is skipped if it was already alerted within _DEDUP_HOURS.
    """
    rows = _load_health_rows()
    by_job = {r["job"]: r for r in rows}
    now    = datetime.now(timezone.utc)
    alerts = []

    for job, max_hours in CADENCE_HOURS.items():
        row = by_job.get(job)
        if row is None:
            continue  # never ran — skip (no false positive on first deploy)

        last_success = row.get("last_success_at")
        if not last_success:
            continue

        last_success = _parse_ts(last_success)
        gap_hours = (now - last_success).total_seconds() / 3600

        if gap_hours <= max_hours:
            continue  # within cadence — all good

        # De-dup: skip if already alerted recently
        last_alert = _parse_ts(row.get("last_alert_at"))
        if last_alert and (now - last_alert).total_seconds() < _DEDUP_HOURS * 3600:
            continue

        hours_overdue = int(gap_hours)
        alerts.append({
            "job":      job,
            "severity": _SEVERITY_CRITICAL,
            "message":  (
                f"🔴 {job} last succeeded {hours_overdue}h ago "
                f"(expected every {max_hours}h). "
                f"Likely cause: scheduler did not restart after last deploy."
            ),
        })

    return alerts


def _mark_alerted(job: str, kind: str) -> None:
    try:
        from database.client import get_client
        db = get_client()
        now = datetime.now(timezone.utc).isoformat()
        db.table("agent_health").upsert({
            "job":             job,
            "last_alert_at":   now,
            "last_alert_kind": kind,
            "updated_at":      now,
        }, on_conflict="job").execute()
    except Exception as exc:
        log.warning("_mark_alerted failed: %s", exc)


# ---------------------------------------------------------------------------
# Dependency probes
# ---------------------------------------------------------------------------

def probe_dependencies() -> dict[str, dict]:
    """
    Lightweight ping of each external service.
    Returns {name: {"ok": bool, "detail": str}}.
    Never raises — any exception is caught and returned as ok=False.
    """
    import requests as _req

    results: dict[str, dict] = {}

    # ── Supabase ──────────────────────────────────────────────────────────────
    try:
        from database.client import get_client
        get_client().table("leads").select("id", count="exact").limit(1).execute()
        results["supabase"] = {"ok": True, "detail": ""}
    except Exception as exc:
        results["supabase"] = {"ok": False, "detail": str(exc)[:150]}

    # ── Anthropic ─────────────────────────────────────────────────────────────
    # Raw HTTP — avoids sdk version skew (.models was added in later releases).
    # 200 = up + key valid; 401 = up + key wrong; 5xx / exception = down.
    try:
        r = _req.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key":         os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
            },
            timeout=8,
        )
        ok = r.status_code in (200, 401)
        results["anthropic"] = {"ok": ok, "detail": f"HTTP {r.status_code}"}
    except Exception as exc:
        results["anthropic"] = {"ok": False, "detail": str(exc)[:150]}

    # ── Resend ────────────────────────────────────────────────────────────────
    try:
        r = _req.get(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {os.getenv('RESEND_API_KEY', '')}"},
            timeout=8,
        )
        results["resend"] = {"ok": r.status_code < 500, "detail": f"HTTP {r.status_code}"}
    except Exception as exc:
        results["resend"] = {"ok": False, "detail": str(exc)[:150]}

    # ── Google Maps ───────────────────────────────────────────────────────────
    try:
        r = _req.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": "-33.87,151.21", "radius": "100", "type": "dentist",
                "key": os.getenv("GOOGLE_MAPS_API_KEY", ""),
            },
            timeout=8,
        )
        status = r.json().get("status", "UNKNOWN")
        results["google_maps"] = {
            "ok": status in ("OK", "ZERO_RESULTS"),
            "detail": status,
        }
    except Exception as exc:
        results["google_maps"] = {"ok": False, "detail": str(exc)[:150]}

    # ── Meta WhatsApp (outreach number) ───────────────────────────────────────
    try:
        phone_id = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", "")
        token    = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        r = _req.get(
            f"https://graph.facebook.com/v19.0/{phone_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        results["meta_wa"] = {"ok": r.status_code == 200, "detail": f"HTTP {r.status_code}"}
    except Exception as exc:
        results["meta_wa"] = {"ok": False, "detail": str(exc)[:150]}

    return results


# ---------------------------------------------------------------------------
# Watchdog (called hourly by scheduler)
# ---------------------------------------------------------------------------

def run_watchdog() -> list[str]:
    """
    Hourly: check cadences + probe dependencies + fire tiered alerts.
    Returns list of overdue job names so the caller can auto-recover them.
    Lazy-imports notify_founder so this module loads even before notifier.py exists.
    """
    try:
        from utils.notifier import notify_founder
    except ImportError:
        log.warning("run_watchdog: utils.notifier not available yet — alerts skipped")
        return []

    # Cadence overdue check
    alerts = check_cadences()
    overdue_jobs = []
    for alert in alerts:
        log.warning("Watchdog cadence alert: %s", alert["message"])
        notify_founder(
            kind="system_alert",
            severity=alert["severity"],
            component=alert["job"],
            reason=alert["message"] + " Auto-recovery triggered.",
        )
        _mark_alerted(alert["job"], alert["severity"])
        overdue_jobs.append(alert["job"])

    # Dependency probes
    deps = probe_dependencies()
    down = [name for name, s in deps.items() if not s["ok"]]
    for name in down:
        detail = deps[name]["detail"]
        reason = f"🔴 {name} is unreachable — {detail}"
        log.error("Watchdog dependency down: %s", reason)
        notify_founder(
            kind="system_alert",
            severity=_SEVERITY_CRITICAL,
            component=name,
            reason=reason,
        )

    log.info(
        "Watchdog complete: %d cadence alert(s), %d dependency down",
        len(alerts), len(down),
    )
    return overdue_jobs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_health_rows() -> list[dict]:
    try:
        from database.client import get_client
        return get_client().table("agent_health").select("*").execute().data or []
    except Exception as exc:
        log.warning("_load_health_rows failed: %s", exc)
        return []


def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
