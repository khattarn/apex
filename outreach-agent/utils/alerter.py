import logging

log = logging.getLogger(__name__)


def alert_founder(job_name: str, exc: Exception) -> None:
    """
    Notify founder when a scheduled job fails. Never raises.
    Delegates to notify_founder() for dual-channel delivery (email + WA template).
    """
    try:
        from utils.notifier import notify_founder
        notify_founder(
            kind="system_alert",
            severity="critical",
            component=job_name,
            reason=f"🚨 {job_name} failed — {type(exc).__name__}: {str(exc)[:300]}",
        )
    except Exception as e:
        log.error("alert_founder could not deliver: %s", e)
