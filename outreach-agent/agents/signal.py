"""
Signal Agent — Campaign Intelligence
Reads campaign data, mines transcripts, scores templates, proposes improvements.
Runs autonomous A/B tests within guardrails. Proposes structural changes via CEO.

Autonomy guardrails:
  - Autonomous: A/B tests ≤20 leads per variant, auto-promote at 2× reply rate,
                auto-kill at 0% after 30 sends, send-time shift ±2h, objection logging
  - Must propose: tests >20 leads, new templates, channel changes, Aria script changes,
                  geo/vertical profile changes, >3 concurrent A/B tests

STATUS: Skeleton — knowledge base seeded. Scheduling and full logic: next session.
"""

import logging
import json
from datetime import datetime, timezone
from anthropic import Anthropic
from database.client import supabase
from knowledge import GEO_PROFILES, get_vertical_profile, get_combined_context

logger = logging.getLogger(__name__)
client = Anthropic()

# ── Autonomous action thresholds ───────────────────────────────────────────────
AUTO_PROMOTE_THRESHOLD = 2.0      # Variant reply rate must be 2× control to auto-promote
AUTO_KILL_MIN_SENDS = 30          # Minimum sends before auto-kill is considered
AUTO_KILL_REPLY_THRESHOLD = 0.0   # 0% reply rate triggers auto-kill
MAX_AB_LEADS_PER_VARIANT = 20     # Max leads per variant without approval
MAX_CONCURRENT_AB_TESTS = 3       # Max simultaneous A/B tests Signal can run autonomously
SEND_TIME_SHIFT_MAX_HOURS = 2     # Max hours Signal can shift send window without approval


# ── Context Builder ────────────────────────────────────────────────────────────

def build_signal_context(business_type: str, country: str) -> str:
    """
    Builds the geo + vertical intelligence block Signal injects into every
    copy generation or analysis prompt.
    """
    ctx = get_combined_context(business_type, country, GEO_PROFILES)
    geo = ctx.get("geo", {})
    vertical = ctx.get("vertical", {})

    if not geo or not vertical:
        return f"No profile found for {business_type}/{country}. Use general best practices."

    channel_rank = geo.get("channel_rank", {})
    sorted_channels = sorted(channel_rank.items(), key=lambda x: x[1])
    channel_order = " > ".join(f"{ch}" for ch, _ in sorted_channels)

    software = vertical.get("software_landscape", {})
    dominant_sw = software.get("dominant", "unknown")
    sw_implication = software.get("signal_implication", "")

    pain_points = vertical.get("pain_points", [])
    pitch = vertical.get("pitch_angle", {})
    objections = vertical.get("objections", {})
    regulatory = geo.get("regulatory", {})

    context_block = f"""
=== SIGNAL CONTEXT: {business_type.upper()} in {country} ===

GEO — {geo.get('country', country)}
Channel preference: {channel_order}
Cold call receptivity: {geo.get('cold_call_receptivity', 'unknown')}
Tone: {geo.get('tone', {}).get('style', 'professional')}
Optimal email window: {geo.get('optimal_contact_windows', {}).get('email', 'business hours')}
Optimal voice window: {geo.get('optimal_contact_windows', {}).get('voice', 'business hours')}
Trust signals: {', '.join(geo.get('trust_signals', [])[:3])}
Regulatory note: {json.dumps(regulatory.get('email', {}).get('consent', 'check local law'), ensure_ascii=False)}

VERTICAL — {vertical.get('vertical', business_type)}
Dominant software: {dominant_sw}
Software implication: {sw_implication}
Top pain points: {'; '.join(pain_points[:3])}
Primary pitch: {pitch.get('primary', '')}
Avoid: {pitch.get('avoid', '')}

TOP OBJECTIONS:
{chr(10).join(f"  Q: {q}{chr(10)}  A: {a}" for q, a in list(objections.items())[:3])}

Signal notes: {vertical.get('signal_notes', '')}
=== END CONTEXT ===
"""
    return context_block.strip()


# ── Template Scoring ───────────────────────────────────────────────────────────

async def score_templates(business_type: str = None, country: str = None) -> list:
    """
    Reads lead_activities and email_sends to score active templates.
    Returns ranked list with reply_rate, open_rate, sample_size per template.
    """
    # TODO: implement full scoring logic
    # Query: SELECT template_id, COUNT(*) sent, SUM(replied) replies FROM lead_activities
    #        WHERE business_type=? AND country=? GROUP BY template_id
    logger.info(f"Template scoring — {business_type}/{country} — not yet implemented")
    return []


# ── A/B Test Management ────────────────────────────────────────────────────────

async def create_ab_test(
    template_name: str,
    control_copy: str,
    variant_copy: str,
    business_type: str,
    country: str,
    channel: str,
    max_leads: int = MAX_AB_LEADS_PER_VARIANT,
    rationale: str = "",
) -> dict:
    """
    Creates an A/B test record. Signal runs this autonomously if max_leads ≤ 20.
    Larger tests are written as proposals to CEO instead.
    """
    if max_leads > MAX_AB_LEADS_PER_VARIANT:
        return await _propose_ab_test_to_ceo(
            template_name, control_copy, variant_copy, business_type, country, channel, max_leads, rationale
        )

    test = {
        "template_name": template_name,
        "channel": channel,
        "business_type": business_type,
        "country": country,
        "control_copy": control_copy,
        "variant_copy": variant_copy,
        "control_sends": 0,
        "variant_sends": 0,
        "control_replies": 0,
        "variant_replies": 0,
        "status": "running",
        "autonomous": True,
        "rationale": rationale,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table("ab_tests").insert(test).execute()
    logger.info(f"A/B test created autonomously: {template_name} ({business_type}/{country})")
    return result.data[0] if result.data else {}


async def evaluate_ab_tests() -> list:
    """
    Checks all running A/B tests. Auto-promotes winners, auto-kills losers.
    Called by Signal's weekly job.
    """
    actions = []
    tests = supabase.table("ab_tests").select("*").eq("status", "running").execute().data or []

    for test in tests:
        control_rate = test["control_replies"] / max(test["control_sends"], 1)
        variant_rate = test["variant_replies"] / max(test["variant_sends"], 1)
        total_sends = test["control_sends"] + test["variant_sends"]

        if total_sends < 20:
            continue  # Not enough data yet

        if variant_rate >= control_rate * AUTO_PROMOTE_THRESHOLD and test["variant_sends"] >= 10:
            actions.append(await _auto_promote(test, control_rate, variant_rate))

        elif (control_rate == AUTO_KILL_REPLY_THRESHOLD
              and test["control_sends"] >= AUTO_KILL_MIN_SENDS):
            actions.append(await _auto_kill(test))

    return actions


async def _auto_promote(test: dict, control_rate: float, variant_rate: float) -> dict:
    """Autonomously promote variant to primary. Log to system_journal."""
    supabase.table("ab_tests").update({"status": "variant_won"}).eq("id", test["id"]).execute()
    supabase.table("system_journal").insert({
        "entry_type": "signal_auto_promote",
        "summary": f"Signal auto-promoted variant for {test['template_name']} ({test['business_type']}/{test['country']})",
        "detail": {
            "control_reply_rate": round(control_rate, 3),
            "variant_reply_rate": round(variant_rate, 3),
            "lift": round(variant_rate / max(control_rate, 0.001), 2),
            "test_id": test["id"],
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    logger.info(f"Signal auto-promoted: {test['template_name']} — variant rate {variant_rate:.1%} vs control {control_rate:.1%}")
    return {"action": "promoted", "test": test["template_name"]}


async def _auto_kill(test: dict) -> dict:
    """Autonomously kill a zero-reply template. Fall back to last known working."""
    supabase.table("ab_tests").update({"status": "control_killed"}).eq("id", test["id"]).execute()
    supabase.table("system_journal").insert({
        "entry_type": "signal_auto_kill",
        "summary": f"Signal auto-killed zero-reply template: {test['template_name']} ({test['business_type']}/{test['country']})",
        "detail": {"sends": test["control_sends"], "replies": 0, "test_id": test["id"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    logger.info(f"Signal auto-killed template: {test['template_name']} — 0% reply after {test['control_sends']} sends")
    return {"action": "killed", "test": test["template_name"]}


async def _propose_ab_test_to_ceo(
    template_name, control_copy, variant_copy, business_type, country, channel, max_leads, rationale
) -> dict:
    """Large test requires CEO → Neeraj approval. Write to system_journal as proposal."""
    proposal = {
        "type": "ab_test_proposal",
        "template_name": template_name,
        "channel": channel,
        "business_type": business_type,
        "country": country,
        "control_copy": control_copy,
        "variant_copy": variant_copy,
        "max_leads_per_variant": max_leads,
        "rationale": rationale,
    }
    supabase.table("system_journal").insert({
        "entry_type": "signal_proposal",
        "summary": f"Signal proposes A/B test for {template_name} — {max_leads} leads/variant. Needs approval.",
        "detail": proposal,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    logger.info(f"Signal A/B proposal written to journal: {template_name}")
    return {"action": "proposed", "template": template_name, "awaiting": "ceo_approval"}


# ── Copy Generation ────────────────────────────────────────────────────────────

async def generate_improved_template(
    channel: str,
    business_type: str,
    country: str,
    current_template: str,
    performance_data: dict,
) -> str:
    """
    Generates an improved template using geo + vertical context.
    Output is a PROPOSAL — not deployed until CEO/Neeraj approves.
    """
    context = build_signal_context(business_type, country)

    prompt = f"""You are Signal, the campaign intelligence agent for PracticeDesk — a practice management AI for {business_type}s.

Your job: write an improved {channel} outreach message that outperforms the current template.

{context}

CURRENT TEMPLATE (underperforming):
{current_template}

PERFORMANCE DATA:
- Reply rate: {performance_data.get('reply_rate', 'unknown')}
- Open rate: {performance_data.get('open_rate', 'unknown')}
- Sends: {performance_data.get('sends', 'unknown')}
- Top reason for failure (if known): {performance_data.get('failure_reason', 'unknown')}

TASK:
Write a new {channel} message for {business_type}s in {country} that addresses the failure mode.
Apply the geo and vertical intelligence above strictly.
Output ONLY the message text — no explanation, no preamble.
Keep it to the appropriate length for {channel} ({
    '160 characters max' if channel == 'sms' else
    '3–4 short paragraphs' if channel == 'email' else
    '2–3 sentences, conversational' if channel == 'wa' else
    'natural spoken language, 15–20 seconds when read aloud' if channel == 'voice' else
    'appropriate length'
})."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ── Transcript Mining ──────────────────────────────────────────────────────────

async def mine_transcripts(business_type: str = None, country: str = None, limit: int = 50) -> dict:
    """
    Pulls Vapi call transcripts and extracts:
    - Phase where call ended
    - Objections raised
    - Language that produced positive responses
    - Dropout moments

    TODO: implement Vapi transcript API call.
    """
    logger.info(f"Transcript mining — {business_type}/{country} — not yet implemented")
    return {"objections": [], "dropout_moments": [], "winning_phrases": []}


# ── Geo Research Job ───────────────────────────────────────────────────────────

async def refresh_geo_intelligence(country: str):
    """
    Monthly web research job. Fires search queries for country-specific
    B2B outreach preferences, updates geo_profiles if significant changes found.
    Proposes profile updates via CEO — does not apply autonomously.

    TODO: implement web search integration.
    """
    queries = [
        f"B2B cold calling effectiveness {country} small business 2026",
        f"WhatsApp business adoption {country} professional services",
        f"email marketing open rates {country} small business",
        f"best days times cold outreach {country} healthcare professionals",
    ]
    logger.info(f"Geo intelligence refresh queued for {country}: {len(queries)} queries")
    # TODO: fire web searches, synthesise with Claude Sonnet, write proposal to system_journal


# ── Weekly Report ──────────────────────────────────────────────────────────────

async def generate_weekly_report() -> dict:
    """
    Produces Signal's weekly brief for CEO:
    - Template scores
    - A/B test outcomes
    - Autonomous actions taken (promotions, kills)
    - Proposals awaiting approval
    - Top 3 recommended changes

    Scheduled: Monday 6am UTC
    NOT yet scheduled — add to APScheduler in server.py when ready.
    TODO: scheduler.add_job(generate_weekly_report, "cron", day_of_week="mon", hour=6)
    """
    logger.info("Signal weekly report — not yet scheduled")
    return {}
