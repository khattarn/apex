"""
CEO Agent — Apex Platform v2.0
Orchestrator: system state, directives, WA interface, agent factory, journal.

STATUS: Placeholder — structure defined, not yet scheduled or configured.
Wire up in server.py after Signal and Brain are live.
"""

import logging
from datetime import datetime, timezone
from database.client import supabase

logger = logging.getLogger(__name__)

FOUNDER_WA_NUMBER = "+919810982019"


# ── Journal ───────────────────────────────────────────────────────────────────

async def write_journal(entry_type: str, summary: str, detail: dict = None):
    """Write an entry to the system journal."""
    supabase.table("system_journal").insert({
        "entry_type": entry_type,
        "summary": summary,
        "detail": detail or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


# ── System Status ─────────────────────────────────────────────────────────────

async def get_system_status() -> dict:
    """
    Read agent_registry, recent lead_activities, email queue depth.
    Returns a structured snapshot of system health.
    Not yet scheduled — call manually or via /api/ceo/status.
    """
    # TODO: implement when agent_registry table is live
    return {"status": "not_configured", "message": "CEO agent not yet activated."}


# ── Heartbeat ─────────────────────────────────────────────────────────────────

async def run_heartbeat():
    """
    Hourly system check. Reads all agent last_run_at from agent_registry.
    Alerts via WA only when something is broken — not noise, only signal.
    NOT yet scheduled — add to APScheduler in server.py when ready.
    """
    # TODO: scheduler.add_job(run_heartbeat, "interval", hours=1)
    logger.info("CEO heartbeat — not yet configured")


# ── Directive Queue ───────────────────────────────────────────────────────────

async def issue_directive(agent: str, directive: str, params: dict = None):
    """
    Write a directive to agent_directives table.
    Directives: PAUSE | ADJUST_INTERVAL | CHANGE_TEMPLATE | TARGET | ABORT_LEAD
    Each agent must call check_directives() before running.
    """
    supabase.table("agent_directives").insert({
        "agent": agent,
        "directive": directive,
        "params": params or {},
        "status": "pending",
        "issued_by": "ceo",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    await write_journal("directive_issued", f"Directive {directive} issued to {agent}", params)


async def check_directives(agent_name: str) -> list:
    """
    Each agent calls this before running.
    Returns list of active directives relevant to that agent.
    """
    result = supabase.table("agent_directives") \
        .select("*") \
        .eq("agent", agent_name) \
        .eq("status", "pending") \
        .execute()
    return result.data or []


async def mark_directive_applied(directive_id: str):
    supabase.table("agent_directives").update({
        "status": "applied",
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", directive_id).execute()


# ── WA Interface (Founder Channel) ────────────────────────────────────────────

async def handle_founder_message(message_text: str) -> str:
    """
    Routes inbound WA messages from FOUNDER_WA_NUMBER to CEO context.
    Called from reply_handler.py when sender == FOUNDER_WA_NUMBER.
    Uses Claude Sonnet to answer in plain English.
    NOT yet wired into reply_handler — wire when tables are live.
    """
    # TODO: import anthropic, build context from system_journal + agent_registry,
    # call Claude Sonnet, return plain-English answer
    return "CEO Agent not yet configured. Coming soon."


# ── Agent Factory ─────────────────────────────────────────────────────────────

async def draft_agent_spec(capability_description: str) -> dict:
    """
    When a new agent is needed, CEO drafts the specification.
    Brain validates. Claude writes code. Neeraj approves via WA.
    NOT yet implemented.
    """
    # TODO: implement Phase 3
    return {}
