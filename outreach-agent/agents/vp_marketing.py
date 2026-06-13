"""
VP Marketing Agent — Agent 12
Orchestrates all outbound marketing for PracticeDesk + LegalAidAI.

Role in the org:
  CEO (Neeraj) → VP Marketing → Agents 1, 2, 3, 6, 8 (Content), 9, 11
                             ← Signal (performance reports)
                             → Content Agent (commissions)

Responsibilities:
  - Generate comprehensive campaign plans across all verticals and markets
  - Process Signal weekly reports and decide what content to refresh
  - Commission specific content from Agent 8 (Content Agent)
  - Own the content queue: what to create, in what order, for what reason
  - Recommend what to stop (dead ends flagged by Signal)

Autonomy:
  - Autonomous: generate plans, commission content, refresh underperformers
  - Must escalate to CEO: new products, new verticals, pricing changes, brand rule changes
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import anthropic

from agents.content_agent import generate_content, ContentRequest, PRODUCT_MODULES, ContentResult

_MODEL = "claude-sonnet-4-6"
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

_SYSTEM_PROMPT = """\
You are the VP Marketing Agent for Apex — an AI-native internal platform that sells and operates two SaaS products:

1. PracticeDesk ($49–$180/mo) — AI office assistant for dentists, salons, accountants, physiotherapists, lawyers.
   Markets: AU (primary), US, CA, IN (expanding)

2. LegalAidAI / Nyaya Saathi (₹2,500–₹5,000/mo) — AI legal platform for India.
   Modules: Advocate (primary revenue), Corporate (high-value, human close), Citizen (freemium/social)

You directly supervise:
  Agent 1 (Prospector) · Agent 2 (Personalizer) · Agent 3 (Outreach)
  Agent 6 (Follow-up) · Agent 8 (Content) · Agent 9 (Re-engagement) · Agent 11 (Affiliate)

You report to the CEO — Neeraj Khattar.

STRATEGIC PRINCIPLES:
- AU is the highest-performing WA market — always prioritise it.
- Advocate module drives LegalAidAI revenue — always prioritise it over Corporate and Citizen.
- When Signal flags a dead end, recommend stopping immediately — don't keep spending.
- Content Agent generates drafts; you review the queue before deployment.
- Never commission content for new products or verticals without CEO approval.
- Be specific and actionable — vague strategy has no value. Name the vertical, the market, the metric.
"""


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CampaignPlan:
    generated_at: str
    strategic_brief: str       # VP Marketing's full strategic assessment from Claude
    content_queue: list[dict]  # ordered commissions for Content Agent
    signal_context: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class CommissionResult:
    commission: dict
    content: str
    input_tokens: int = 0
    output_tokens: int = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_brief(product: str) -> str:
    path = KNOWLEDGE_DIR / "brand" / f"{product}-brief.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _format_signal_context(feedback: dict) -> str:
    lines = []

    winning = feedback.get("winning_templates", [])
    if winning:
        lines.append("WINNING (keep + replicate pattern):")
        for w in winning[:3]:
            rate = (w.get("reply_rate") or w.get("open_rate") or 0) * 100
            lines.append(
                f"  {w.get('business_type')}/{w.get('country')} {w.get('channel')}: "
                f"{rate:.1f}% — {w.get('sends')} sends"
            )

    under = feedback.get("underperforming_templates", [])
    if under:
        lines.append("UNDERPERFORMING (commission content refresh):")
        for u in under[:3]:
            rate = (u.get("reply_rate") or u.get("open_rate") or 0) * 100
            lines.append(
                f"  {u.get('business_type')}/{u.get('country')} {u.get('channel')}: "
                f"{rate:.1f}% — {u.get('sends')} sends"
            )

    dead = feedback.get("dead_ends", [])
    if dead:
        lines.append("DEAD ENDS (recommend stopping):")
        for d in dead[:2]:
            lines.append(
                f"  {d.get('channel')}/{d.get('business_type')}/{d.get('country')}: "
                f"{d.get('sends')} sends, {d.get('rate', 0)*100:.1f}% after {d.get('age_days')} days"
            )

    actions = feedback.get("recommended_actions", [])
    if actions:
        lines.append("SIGNAL RECOMMENDED ACTIONS:")
        for a in actions[:4]:
            lines.append(f"  • {a}")

    return "\n".join(lines) if lines else "No Signal performance data available yet."


def _build_queue_from_signal(signal_feedback: dict) -> list[dict]:
    """Urgent refreshes from Signal underperformers — these go to front of queue."""
    queue = []
    under = signal_feedback.get("underperforming_templates", []) if signal_feedback else []
    for u in under[:3]:
        btype = u.get("business_type", "dentist")
        # Determine which product owns this business_type
        product = next(
            (p for p, mods in PRODUCT_MODULES.items() if btype in mods),
            "practicedesk",
        )
        queue.append({
            "priority":     "urgent",
            "product":      product,
            "module":       btype,
            "content_type": "wa_template" if u.get("channel") == "wa" else "email",
            "tone":         "pain_first",
            "market":       u.get("country", "AU"),
            "language":     "en",
            "reason":       (
                f"Signal: underperforming — "
                f"{(u.get('reply_rate') or u.get('open_rate') or 0)*100:.1f}% "
                f"on {u.get('sends')} sends. Fresh angle required."
            ),
        })
    return queue


def _build_standard_queue() -> list[dict]:
    """Full standard content plan for all verticals and markets."""
    queue = []

    # PracticeDesk — AU primary, then US/CA
    for module in ["dentist", "salon", "accountant", "physiotherapist", "lawyer"]:
        for ct, tone in [("wa_template", "pain_first"), ("email", "outcome_first"), ("voice_guidance", "conversational")]:
            queue.append({
                "priority":     "standard",
                "product":      "practicedesk",
                "module":       module,
                "content_type": ct,
                "tone":         tone,
                "market":       "AU",
                "language":     "en",
                "reason":       f"PracticeDesk AU comprehensive suite — {module}",
            })
        # US/CA WA reply rates are low — email + voice only
        for market in ["US", "CA"]:
            for ct, tone in [("email", "outcome_first"), ("voice_guidance", "conversational")]:
                queue.append({
                    "priority":     "low",
                    "product":      "practicedesk",
                    "module":       module,
                    "content_type": ct,
                    "tone":         tone,
                    "market":       market,
                    "language":     "en",
                    "reason":       f"PracticeDesk {market} — email + voice (WA low-adoption market)",
                })

    # LegalAidAI — Advocate first
    for module, priority in [("advocate", "standard"), ("corporate", "standard"), ("citizen", "low")]:
        for ct, tone in [("wa_template", "structured"), ("email", "structured"), ("voice_guidance", "conversational")]:
            if module == "corporate" and ct == "wa_template":
                continue  # Corporate is email + voice only (B2B, no WA broadcast)
            queue.append({
                "priority":     priority,
                "product":      "legalaidai",
                "module":       module,
                "content_type": ct,
                "tone":         tone,
                "market":       "IN",
                "language":     "en",
                "reason":       f"LegalAidAI {module} content plan",
            })
        # Hindi WA for Advocate (peer-to-peer, high WA penetration)
        if module == "advocate":
            queue.append({
                "priority":     "standard",
                "product":      "legalaidai",
                "module":       "advocate",
                "content_type": "wa_template",
                "tone":         "conversational",
                "market":       "IN",
                "language":     "hi",
                "reason":       "LegalAidAI Advocate — Hindi WA template (peer-to-peer channel in IN)",
            })

    return queue


# ── Core functions ────────────────────────────────────────────────────────────

def generate_campaign_plan(
    signal_feedback: dict = None,
    additional_brief: str = "",
) -> CampaignPlan:
    """
    VP Marketing generates a comprehensive campaign plan for all verticals.
    Signal feedback prioritises urgent refreshes; remaining items follow strategic defaults.
    Returns CampaignPlan with strategic brief + ordered content queue.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    signal_ctx = _format_signal_context(signal_feedback) if signal_feedback else "No Signal data — using benchmark strategy."
    pd_brief = _load_brief("practicedesk")
    la_brief = _load_brief("legalaidai")

    user_msg = f"""Generate the current campaign plan.

## PracticeDesk Brand Brief
{pd_brief[:2000]}

## LegalAidAI Brand Brief
{la_brief[:2000]}

## Signal Performance Data
{signal_ctx}

{"## CEO / Additional Brief\n" + additional_brief if additional_brief else ""}

---

Devise a comprehensive campaign plan covering all active verticals:

PracticeDesk: dentist · salon · accountant · physiotherapist · lawyer × AU (primary) / US / CA
LegalAidAI:   advocate · corporate · citizen × IN (English + Hindi WA for Advocate)

Your response must include:

### STRATEGIC ASSESSMENT
3–5 sentences: current performance state, highest-priority opportunity, key risk or constraint.

### CONTENT QUEUE
Ordered priority list for Agent 8 (Content Agent). For each item state:
PRIORITY: urgent / standard / low
Product | Module | Type | Tone | Market | Language | Reason (one line)

### WHAT TO STOP
Any dead channels or underperforming combinations to pause immediately.

### THIS WEEK'S FOCUS
The single most important action across all agents this week.

### WINNING PATTERN
If Signal shows a winner — name the pattern and how to replicate it across verticals.
"""

    resp = client.messages.create(
        model=_MODEL,
        max_tokens=2500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    plan_text = resp.content[0].text.strip()

    # Build queue: urgent Signal refreshes first, then standard plan
    urgent = _build_queue_from_signal(signal_feedback) if signal_feedback else []
    standard = _build_standard_queue()
    # De-duplicate: remove standard items already covered by urgent
    urgent_keys = {(q["product"], q["module"], q["content_type"], q["market"]) for q in urgent}
    standard = [q for q in standard if (q["product"], q["module"], q["content_type"], q["market"]) not in urgent_keys]

    return CampaignPlan(
        generated_at=datetime.now(timezone.utc).isoformat(),
        strategic_brief=plan_text,
        content_queue=urgent + standard,
        signal_context=signal_ctx,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
    )


def execute_commission(commission: dict, signal_context: str = "") -> CommissionResult:
    """
    Execute one content commission — calls Agent 8 (Content Agent).
    Passes Signal context so Content Agent can improve on underperformers.
    Result is returned for VP Marketing review; not auto-deployed.
    """
    req = ContentRequest(
        product=commission["product"],
        module=commission["module"],
        content_type=commission["content_type"],
        tone=commission.get("tone", "structured"),
        market=commission.get("market", "AU"),
        language=commission.get("language", "en"),
        brief=commission.get("reason", ""),
        signal_feedback=signal_context,
    )
    result = generate_content(req)
    return CommissionResult(
        commission=commission,
        content=result.content,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
