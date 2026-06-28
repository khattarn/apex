"""
Signal Agent — Marketing Head
Campaign intelligence, funnel analytics, projections, targets, dead-end detection.
Runs autonomous micro A/B tests. Proposes structural changes via CEO.

Role: The system's embedded marketing head. Scores every template, models the
funnel, sets achievable targets, projects revenue, flags dead ends, writes
better copy. Evolves constantly from real campaign data + geo/vertical knowledge.

Autonomy guardrails:
  - Autonomous: A/B tests ≤20 leads/variant, auto-promote at 2× reply rate,
                auto-kill at 0% reply after 30 sends, send-time shift ±2h,
                objection logging, target revision within ±20%
  - Must propose: tests >20 leads, new templates, channel changes, Aria script
                  changes, geo profile changes, target revision >20%, dead-end
                  declaration (CEO packages → Neeraj approves)
"""

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from anthropic import Anthropic
from database.client import get_client

logger = logging.getLogger(__name__)
_claude = Anthropic()

# ── Constants ─────────────────────────────────────────────────────────────────

AVG_MRR_PER_CUSTOMER = 99.0          # USD — Growth plan assumption
MONTHLY_CHURN_RATE   = 0.05          # 5% monthly churn on existing paid customers
AUTO_PROMOTE_LIFT    = 2.0           # variant must be 2× control reply rate
AUTO_KILL_MIN_SENDS  = 30
AUTO_KILL_MAX_RATE   = 0.0
DEAD_END_MIN_SENDS   = 30
DEAD_END_MAX_RATE    = 0.01          # <1% reply rate
DEAD_END_MIN_DAYS    = 45            # must have been running 45+ days
MAX_AB_LEADS         = 20            # autonomous test limit

# Default funnel rates per country/vertical when real data is insufficient (<20 sends)
# Sourced from: industry benchmarks + geo/vertical profile research
_DEFAULT_FUNNEL = {
    ("dentist",        "AU"): dict(contact=0.85, wa_reply=0.12, email_open=0.31, email_click=0.06, interest=0.40, demo=0.60, trial=0.50, conversion=0.30),
    ("dentist",        "CA"): dict(contact=0.80, wa_reply=0.02, email_open=0.26, email_click=0.05, interest=0.35, demo=0.55, trial=0.45, conversion=0.25),
    ("dentist",        "US"): dict(contact=0.80, wa_reply=0.02, email_open=0.22, email_click=0.04, interest=0.30, demo=0.50, trial=0.40, conversion=0.25),
    ("salon",          "AU"): dict(contact=0.85, wa_reply=0.10, email_open=0.28, email_click=0.05, interest=0.35, demo=0.55, trial=0.45, conversion=0.25),
    ("salon",          "CA"): dict(contact=0.80, wa_reply=0.01, email_open=0.24, email_click=0.04, interest=0.30, demo=0.50, trial=0.40, conversion=0.20),
    ("salon",          "US"): dict(contact=0.80, wa_reply=0.01, email_open=0.20, email_click=0.04, interest=0.28, demo=0.48, trial=0.38, conversion=0.20),
    ("accountant",     "AU"): dict(contact=0.82, wa_reply=0.09, email_open=0.29, email_click=0.05, interest=0.36, demo=0.58, trial=0.48, conversion=0.28),
    ("accountant",     "CA"): dict(contact=0.78, wa_reply=0.01, email_open=0.25, email_click=0.05, interest=0.32, demo=0.52, trial=0.42, conversion=0.22),
    ("accountant",     "US"): dict(contact=0.78, wa_reply=0.01, email_open=0.21, email_click=0.04, interest=0.29, demo=0.48, trial=0.38, conversion=0.20),
    ("physiotherapist","AU"): dict(contact=0.83, wa_reply=0.11, email_open=0.30, email_click=0.06, interest=0.38, demo=0.58, trial=0.48, conversion=0.28),
    ("physiotherapist","CA"): dict(contact=0.79, wa_reply=0.01, email_open=0.25, email_click=0.05, interest=0.33, demo=0.53, trial=0.43, conversion=0.23),
    ("physiotherapist","US"): dict(contact=0.79, wa_reply=0.01, email_open=0.21, email_click=0.04, interest=0.29, demo=0.49, trial=0.39, conversion=0.21),
}

_CA_TOKENS = {
    "ON","QC","BC","AB","MB","SK","NS","NB","NL","PE","NT","YT","NU",
    "ONTARIO","QUEBEC","ALBERTA","MANITOBA","SASKATCHEWAN",
    "BRITISH COLUMBIA","NOVA SCOTIA","NEW BRUNSWICK","NEWFOUNDLAND",
    "PRINCE EDWARD ISLAND","CANADA",
}
_AU_STATES = {"NSW","VIC","QLD","WA","SA","TAS","ACT","NT","AUSTRALIA"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_country(phone: str, address: str = "") -> str:
    phone = re.sub(r"[^\d+]", "", phone or "")
    addr  = (address or "").upper()
    if phone.startswith("+61") or phone.startswith("0061"):
        return "AU"
    if any(t in addr for t in _AU_STATES):
        return "AU"
    if phone.startswith("+91"):
        return "IN"
    if phone.startswith("+1") or (phone.startswith("1") and len(phone) == 11):
        return "CA" if any(t in addr for t in _CA_TOKENS) else "US"
    if "CANADA" in addr:
        return "CA"
    return "US"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _period_label() -> str:
    """Current month as YYYY-MM."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _quarter_label() -> str:
    """Current quarter as YYYY-QN."""
    d = datetime.now(timezone.utc)
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def _write_journal(entry_type: str, summary: str, detail: dict = None):
    get_client().table("system_journal").insert({
        "entry_type": entry_type,
        "summary":    summary,
        "detail":     detail or {},
        "created_at": _now(),
    }).execute()


# ── 1. Template Scoring ───────────────────────────────────────────────────────

def score_templates() -> list[dict]:
    """
    Reads leads + lead_activities + email_sends.
    Scores every WA template (by business_type × country) and every email
    template (by email_number × business_type × country).
    Writes results to template_scores table.
    Returns list of score dicts.
    """
    db = get_client()
    scores = []

    # ── WA template scoring ────────────────────────────────────────────────
    leads = db.table("leads").select(
        "id,business_type,phone,address,status,outreach_sent,created_at"
    ).eq("outreach_sent", True).execute().data or []

    wa_reply_rows = db.table("lead_activities").select("lead_id").eq(
        "type", "wa_reply_received"
    ).execute().data or []
    replied_ids = {str(r["lead_id"]) for r in wa_reply_rows}

    interest_rows = db.table("lead_activities").select("lead_id").eq(
        "type", "demo_booking_sent"
    ).execute().data or []
    interested_ids = {str(r["lead_id"]) for r in interest_rows}

    # Group leads by business_type × country
    groups: dict[tuple, list] = {}
    for lead in leads:
        country = _detect_country(lead.get("phone",""), lead.get("address",""))
        key = (lead.get("business_type","unknown"), country)
        groups.setdefault(key, []).append(lead)

    for (btype, country), group_leads in groups.items():
        sends   = len(group_leads)
        replies = sum(1 for l in group_leads if str(l["id"]) in replied_ids)
        interested = sum(1 for l in group_leads if str(l["id"]) in interested_ids)
        reply_rate = round(replies / sends, 4) if sends else 0.0

        template_name = f"wa_{btype}_v1"
        status = _score_status(template_name, country, "wa", sends, reply_rate)

        record = {
            "template_name": template_name,
            "channel":       "wa",
            "business_type": btype,
            "country":       country,
            "sends":         sends,
            "replies":       replies,
            "reply_rate":    reply_rate,
            "opens":         0,
            "open_rate":     0.0,
            "clicks":        0,
            "click_rate":    0.0,
            "status":        status,
            "scored_at":     _now(),
        }
        db.table("template_scores").upsert(record, on_conflict="template_name,channel,business_type,country").execute()
        scores.append(record)
        logger.info("WA score: %s/%s — %d sends %.1f%% reply [%s]", btype, country, sends, reply_rate*100, status)

    # ── Email template scoring ─────────────────────────────────────────────
    email_sends = db.table("email_sends").select("*").execute().data or []

    # Get lead country for each email send
    lead_map = {str(l["id"]): l for l in
                db.table("leads").select("id,business_type,phone,address").execute().data or []}

    email_groups: dict[tuple, dict] = {}
    for es in email_sends:
        lead = lead_map.get(str(es.get("lead_id","")))
        if not lead:
            continue
        btype   = lead.get("business_type","unknown")
        country = _detect_country(lead.get("phone",""), lead.get("address",""))
        step    = es.get("email_number") or es.get("sequence_step") or 1
        key     = (f"email_seq_step{step}_{btype}", btype, country, "email")
        if key not in email_groups:
            email_groups[key] = {"sends":0,"opens":0,"clicks":0,"replies":0}
        email_groups[key]["sends"]   += 1
        email_groups[key]["opens"]   += 1 if es.get("opened_at") else 0
        email_groups[key]["clicks"]  += 1 if es.get("clicked_at") else 0
        email_groups[key]["replies"] += 1 if es.get("replied_at") else 0

    for (tname, btype, country, channel), stats in email_groups.items():
        s = stats["sends"]
        record = {
            "template_name": tname,
            "channel":       channel,
            "business_type": btype,
            "country":       country,
            "sends":         s,
            "replies":       stats["replies"],
            "reply_rate":    round(stats["replies"]/s, 4) if s else 0.0,
            "opens":         stats["opens"],
            "open_rate":     round(stats["opens"]/s, 4) if s else 0.0,
            "clicks":        stats["clicks"],
            "click_rate":    round(stats["clicks"]/s, 4) if s else 0.0,
            "status":        "active",
            "scored_at":     _now(),
        }
        db.table("template_scores").upsert(record, on_conflict="template_name,channel,business_type,country").execute()
        scores.append(record)

    return scores


def _score_status(template_name: str, country: str, channel: str, sends: int, rate: float) -> str:
    """Determine template health status."""
    if sends < 10:
        return "active"   # insufficient data
    if sends >= AUTO_KILL_MIN_SENDS and rate == AUTO_KILL_MAX_RATE:
        return "killed"
    if sends >= DEAD_END_MIN_SENDS and rate < DEAD_END_MAX_RATE:
        return "dead_end_candidate"
    return "active"


# ── 2. Funnel Metrics ─────────────────────────────────────────────────────────

def compute_funnel_metrics() -> list[dict]:
    """
    Computes conversion rates at every funnel stage per business_type × country.
    Writes to funnel_metrics table. Returns list of computed metric dicts.
    """
    db = get_client()
    period = _period_label()

    leads = db.table("leads").select("*").execute().data or []
    wa_replies = {str(r["lead_id"]) for r in
                  db.table("lead_activities").select("lead_id")
                  .eq("type","wa_reply_received").execute().data or []}
    demo_interests = {str(r["lead_id"]) for r in
                      db.table("lead_activities").select("lead_id")
                      .eq("type","demo_booking_sent").execute().data or []}
    demos_booked = {str(r["lead_id"]) for r in
                    db.table("lead_activities").select("lead_id")
                    .eq("type","demo_booked").execute().data or []}
    calls_placed = {str(r["lead_id"]) for r in
                    db.table("lead_activities").select("lead_id")
                    .in_("type",["outbound_call","voice_followup_placed"]).execute().data or []}

    # Email stats
    email_sends = db.table("email_sends").select("lead_id,opened_at,clicked_at").execute().data or []
    email_opened  = {str(e["lead_id"]) for e in email_sends if e.get("opened_at")}
    email_clicked = {str(e["lead_id"]) for e in email_sends if e.get("clicked_at")}

    # Group leads
    groups: dict[tuple, list] = {}
    for lead in leads:
        country = _detect_country(lead.get("phone",""), lead.get("address",""))
        key = (lead.get("business_type","unknown"), country)
        groups.setdefault(key, []).append(lead)

    results = []
    for (btype, country), group in groups.items():
        ids = {str(l["id"]) for l in group}

        total      = len(group)
        contacted  = sum(1 for l in group if l.get("outreach_sent"))
        wa_replied = len(ids & wa_replies)
        em_opened  = len(ids & email_opened)
        em_clicked = len(ids & email_clicked)
        interested = len(ids & demo_interests)
        demos      = len(ids & demos_booked)
        converted  = sum(1 for l in group if l.get("status") == "converted")
        called     = len(ids & calls_placed)

        def rate(num, denom):
            return round(num / denom, 4) if denom else 0.0

        row = {
            "business_type":      btype,
            "country":            country,
            "channel":            "all",
            "period":             period,
            "prospects":          total,
            "contacts":           contacted,
            "wa_replies":         wa_replied,
            "email_opens":        em_opened,
            "email_clicks":       em_clicked,
            "interested":         interested,
            "demos":              demos,
            "calls_placed":       called,
            "converted":          converted,
            "contact_rate":       rate(contacted, total),
            "wa_reply_rate":      rate(wa_replied, contacted),
            "email_open_rate":    rate(em_opened, contacted),
            "email_click_rate":   rate(em_clicked, em_opened),
            "interest_rate":      rate(interested, max(wa_replied + em_clicked, 1)),
            "demo_rate":          rate(demos, max(interested, 1)),
            "conversion_rate":    rate(converted, max(demos, 1)),
            "computed_at":        _now(),
        }
        db.table("funnel_metrics").upsert(
            row, on_conflict="business_type,country,period"
        ).execute()
        results.append(row)
        logger.info(
            "Funnel %s/%s: %d prospects → %d contacted → %d wa_replied → %d demos → %d converted",
            btype, country, total, contacted, wa_replied, demos, converted,
        )

    return results


# ── 3. Dead-End Detection ─────────────────────────────────────────────────────

def detect_dead_ends() -> list[dict]:
    """
    Flags business_type × country × channel combinations that have enough
    data to call a dead end:
      - ≥30 sends, <1% reply/engagement, running ≥45 days
    Writes proposals to system_journal. Does not act autonomously.
    Returns list of detected dead ends.
    """
    db = get_client()
    scores = db.table("template_scores").select("*").execute().data or []
    dead_ends = []

    for s in scores:
        sends = s.get("sends", 0)
        rate  = s.get("reply_rate") or s.get("open_rate") or 0.0
        scored_at = s.get("scored_at") or _now()

        try:
            age_days = (datetime.now(timezone.utc) -
                        datetime.fromisoformat(scored_at.replace("Z","+00:00"))).days
        except Exception:
            age_days = 0

        if sends >= DEAD_END_MIN_SENDS and rate < DEAD_END_MAX_RATE and age_days >= DEAD_END_MIN_DAYS:
            entry = {
                "template":     s.get("template_name"),
                "channel":      s.get("channel"),
                "business_type":s.get("business_type"),
                "country":      s.get("country"),
                "sends":        sends,
                "rate":         rate,
                "age_days":     age_days,
                "verdict":      "dead_end",
                "rationale":    (
                    f"{sends} sends over {age_days} days with {rate*100:.1f}% reply rate. "
                    f"This channel×vertical×country combination is not working. "
                    f"Recommend stopping and reallocating effort."
                ),
            }
            dead_ends.append(entry)

            # Write proposal to journal — CEO will surface to Neeraj
            _write_journal(
                "signal_dead_end_detected",
                f"Dead end: {s.get('channel')} outreach to {s.get('business_type')}s in {s.get('country')} — {sends} sends, {rate*100:.1f}% reply",
                entry,
            )
            logger.warning("Dead end detected: %s/%s/%s", s.get("channel"), s.get("business_type"), s.get("country"))

    return dead_ends


# ── 4. Projections — The Forward View ────────────────────────────────────────

def generate_projections(prospects_per_month: int = 50) -> list[dict]:
    """
    Models what the business can achieve at the given monthly prospecting volume.
    Runs for each business_type × country combination with data.
    Generates 3-month, 6-month, 12-month projections with base/optimistic/pessimistic scenarios.
    Writes plain-English summary to system_journal.
    Returns list of projection dicts written to Supabase.
    """
    db = get_client()

    # Get funnel metrics — prefer real data, fall back to defaults
    metrics_rows = db.table("funnel_metrics").select("*").execute().data or []
    metrics_map: dict[tuple, dict] = {}
    for m in metrics_rows:
        key = (m.get("business_type",""), m.get("country",""))
        metrics_map[key] = m

    projections = []

    # All combinations we have knowledge for
    all_keys = set(_DEFAULT_FUNNEL.keys())
    for key in metrics_map:
        all_keys.add(key)

    for (btype, country) in sorted(all_keys):
        real = metrics_map.get((btype, country), {})
        defaults = _DEFAULT_FUNNEL.get((btype, country), _DEFAULT_FUNNEL.get(("dentist","AU")))

        # Use real data if we have meaningful sample, else defaults
        sample = real.get("contacts", 0)
        use_real = sample >= 20

        rates = {
            "contact":      real.get("contact_rate",    defaults["contact"])    if use_real else defaults["contact"],
            "wa_reply":     real.get("wa_reply_rate",   defaults["wa_reply"])   if use_real else defaults["wa_reply"],
            "email_open":   real.get("email_open_rate", defaults["email_open"]) if use_real else defaults["email_open"],
            "email_click":  real.get("email_click_rate",defaults["email_click"])if use_real else defaults["email_click"],
            "interest":     real.get("interest_rate",   defaults["interest"])   if use_real else defaults["interest"],
            "demo":         real.get("demo_rate",       defaults["demo"])       if use_real else defaults["demo"],
            "conversion":   real.get("conversion_rate", defaults["conversion"]) if use_real else defaults["conversion"],
        }

        for scenario_label, multiplier in [("base", 1.0), ("optimistic", 1.20), ("pessimistic", 0.80)]:
            r = {k: v * multiplier for k, v in rates.items()}
            r["contact"]  = min(r["contact"], 1.0)
            r["interest"] = min(r["interest"], 1.0)

            contacted  = prospects_per_month * r["contact"]
            wa_replied = contacted * r["wa_reply"]
            em_clicked = contacted * r["email_open"] * r["email_click"]
            engaged    = wa_replied + em_clicked * 0.7  # clicks are slightly weaker than replies
            interested = engaged * r["interest"]
            demos_mo   = interested * r["demo"]
            paid_new   = demos_mo * 0.5 * r["conversion"]  # 50% trial rate assumed

            # Cumulative paid customers accounting for churn
            paid_3  = _cumulative_paid(paid_new, 3)
            paid_6  = _cumulative_paid(paid_new, 6)
            paid_12 = _cumulative_paid(paid_new, 12)

            row = {
                "business_type":      btype,
                "country":            country,
                "scenario":           scenario_label,
                "horizon":            "3_6_12_months",
                "monthly_prospects":  prospects_per_month,
                "data_source":        "real_data" if use_real else "benchmark_defaults",
                "contact_rate":       round(r["contact"], 4),
                "wa_reply_rate":      round(r["wa_reply"], 4),
                "email_open_rate":    round(r["email_open"], 4),
                "email_click_rate":   round(r["email_click"], 4),
                "interest_rate":      round(r["interest"], 4),
                "demo_rate":          round(r["demo"], 4),
                "conversion_rate":    round(r["conversion"], 4),
                "demos_per_month":    round(demos_mo, 2),
                "paid_new_per_month": round(paid_new, 2),
                "paid_3mo":           round(paid_3, 1),
                "paid_6mo":           round(paid_6, 1),
                "paid_12mo":          round(paid_12, 1),
                "mrr_3mo":            round(paid_3  * AVG_MRR_PER_CUSTOMER, 0),
                "mrr_6mo":            round(paid_6  * AVG_MRR_PER_CUSTOMER, 0),
                "mrr_12mo":           round(paid_12 * AVG_MRR_PER_CUSTOMER, 0),
                "confidence":         "medium" if use_real else "low",
                "generated_at":       _now(),
            }
            db.table("projections").upsert(
                row, on_conflict="business_type,country,scenario"
            ).execute()
            projections.append(row)

    # Write a plain-English summary to journal
    _write_projections_summary(projections, prospects_per_month)
    return projections


def _cumulative_paid(paid_per_month: float, months: int) -> float:
    """Compound paid customers over N months accounting for churn."""
    total = 0.0
    for _ in range(months):
        total = total * (1 - MONTHLY_CHURN_RATE) + paid_per_month
    return total


def _write_projections_summary(projections: list[dict], monthly_prospects: int):
    """Ask Claude to write a plain-English projection brief for CEO → Neeraj."""
    # Pick base scenario only for summary
    base = [p for p in projections if p["scenario"] == "base"]
    if not base:
        return

    lines = []
    for p in sorted(base, key=lambda x: x["mrr_12mo"], reverse=True)[:6]:
        lines.append(
            f"{p['business_type'].title()} in {p['country']}: "
            f"{p['demos_per_month']:.1f} demos/mo → "
            f"${p['mrr_3mo']:.0f} MRR at 3mo | ${p['mrr_6mo']:.0f} at 6mo | ${p['mrr_12mo']:.0f} at 12mo"
            f" [{p['confidence']} confidence]"
        )

    data_summary = "\n".join(lines)

    prompt = f"""You are Signal, the marketing head for PracticeDesk — a practice management AI for dentists, salons, accountants, and physiotherapists in Australia, Canada, and the USA.

The following are revenue projections based on {monthly_prospects} leads prospected per month:

{data_summary}

Write a concise, plain-English brief (max 200 words) for the founder covering:
1. The best opportunity to focus on right now (highest realistic MRR in 6 months)
2. What lever has the highest impact if improved (reply rate, demo rate, etc.)
3. What monthly prospecting volume is needed to hit $5,000 MRR in 12 months
4. One honest risk or caveat about these projections

Be direct and specific. No preamble. Just the brief."""

    try:
        resp = _claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role":"user","content":prompt}],
        )
        summary = resp.content[0].text.strip()
    except Exception as exc:
        summary = f"Projection summary unavailable: {exc}"

    _write_journal("signal_projections", f"Signal Projections — {_period_label()}", {
        "summary": summary,
        "monthly_prospects": monthly_prospects,
        "top_opportunity": base[0]["business_type"] + "/" + base[0]["country"] if base else "unknown",
    })
    logger.info("Projections written: %d combinations", len(base))


# ── 5. Targets ────────────────────────────────────────────────────────────────

def set_targets() -> list[dict]:
    """
    Sets achievable targets for the current quarter based on funnel projections.
    Target = current_rate × 1.15 (15% improvement — stretch but realistic).
    Skips any combination that already has an active target this quarter.
    """
    db = get_client()
    quarter = _quarter_label()
    set_targets_list = []

    scores = db.table("template_scores").select("*").execute().data or []
    metrics = db.table("funnel_metrics").select("*").execute().data or []

    # Don't re-set if already set this quarter
    existing = {
        (r["business_type"], r["country"], r["metric"])
        for r in db.table("targets").select("business_type,country,metric,period")
        .eq("period", quarter).execute().data or []
    }

    for m in metrics:
        btype   = m.get("business_type")
        country = m.get("country")
        contacts = m.get("contacts", 0)
        if contacts < 10:
            continue  # not enough data to set meaningful targets

        metric_map = {
            "wa_reply_rate":   m.get("wa_reply_rate", 0),
            "email_open_rate": m.get("email_open_rate", 0),
            "email_click_rate":m.get("email_click_rate", 0),
            "demo_rate":       m.get("demo_rate", 0),
        }

        for metric, current_val in metric_map.items():
            if (btype, country, metric) in existing:
                continue
            target_val = round(current_val * 1.15, 4)  # 15% stretch
            row = {
                "business_type": btype,
                "country":       country,
                "channel":       "all",
                "metric":        metric,
                "period":        quarter,
                "target_value":  target_val,
                "actual_value":  current_val,
                "variance":      round(current_val - target_val, 4),
                "status":        "active",
                "set_by":        "signal",
                "rationale":     f"Set at 115% of current {metric} ({current_val*100:.1f}% → target {target_val*100:.1f}%)",
                "created_at":    _now(),
                "updated_at":    _now(),
            }
            db.table("targets").upsert(
                row, on_conflict="business_type,country,metric,period"
            ).execute()
            set_targets_list.append(row)

    return set_targets_list


def update_targets() -> list[dict]:
    """
    Compares current actuals to targets. Updates status:
      on_track   — within 10% of target
      behind     — 10-30% below target
      missed     — >30% below target for 2+ consecutive periods
      exceeded   — above target
      dead_end   — consistently 0 or near-0 (propose abandoning)

    Autonomous: can revise target ±20% without approval.
    Must propose: target revision >20%, dead_end declaration.
    """
    db = get_client()
    quarter = _quarter_label()
    updates = []

    targets = db.table("targets").select("*").eq("period", quarter).execute().data or []
    metrics = {
        (m["business_type"], m["country"]): m
        for m in db.table("funnel_metrics").select("*").execute().data or []
    }

    for target in targets:
        btype   = target["business_type"]
        country = target["country"]
        metric  = target["metric"]
        target_val = target.get("target_value", 0)
        actual = metrics.get((btype, country), {}).get(metric, 0)

        if target_val == 0:
            new_status = "active"
        elif actual >= target_val:
            new_status = "exceeded"
        elif actual >= target_val * 0.90:
            new_status = "on_track"
        elif actual >= target_val * 0.70:
            new_status = "behind"
        else:
            new_status = "missed"

        variance = round(actual - target_val, 4)
        db.table("targets").update({
            "actual_value": round(actual, 4),
            "variance":     variance,
            "status":       new_status,
            "updated_at":   _now(),
        }).eq("id", target["id"]).execute()

        if new_status in ("missed", "dead_end"):
            _write_journal(
                "signal_target_missed",
                f"Target missed: {metric} for {btype}/{country} — target {target_val*100:.1f}%, actual {actual*100:.1f}%",
                {"target_id": target["id"], "btype": btype, "country": country, "metric": metric},
            )

        updates.append({**target, "actual_value": actual, "status": new_status, "variance": variance})

    return updates


# ── 6. Dead-End Auto Actions ──────────────────────────────────────────────────

async def evaluate_ab_tests() -> list[dict]:
    """
    Checks running A/B tests. Auto-promotes winners (2× lift ≥ 20 sends).
    Auto-kills zero-reply templates (0% after 30 sends).
    """
    db = get_client()
    actions = []
    tests = db.table("ab_tests").select("*").eq("status","running").execute().data or []

    for t in tests:
        c_sends   = t.get("control_sends", 0)
        v_sends   = t.get("variant_sends", 0)
        c_replies = t.get("control_replies", 0)
        v_replies = t.get("variant_replies", 0)

        if c_sends + v_sends < 20:
            continue  # not enough data

        c_rate = c_replies / max(c_sends, 1)
        v_rate = v_replies / max(v_sends, 1)

        if v_sends >= 10 and c_sends >= 10 and v_rate >= c_rate * AUTO_PROMOTE_LIFT:
            db.table("ab_tests").update({
                "status": "variant_won",
                "winner": "variant",
                "lift":   round(v_rate / max(c_rate, 0.001), 2),
                "concluded_at": _now(),
            }).eq("id", t["id"]).execute()
            _write_journal(
                "signal_auto_promote",
                f"Auto-promoted variant: {t['template_name']} — {v_rate*100:.1f}% vs {c_rate*100:.1f}% control",
                {"test_id": t["id"], "lift": round(v_rate/max(c_rate,0.001),2)},
            )
            actions.append({"action":"promoted","test":t["template_name"],"lift":round(v_rate/max(c_rate,0.001),2)})

        elif c_sends >= AUTO_KILL_MIN_SENDS and c_rate == 0.0:
            db.table("ab_tests").update({
                "status": "control_killed",
                "concluded_at": _now(),
            }).eq("id", t["id"]).execute()
            _write_journal(
                "signal_auto_kill",
                f"Auto-killed zero-reply template: {t['template_name']} — {c_sends} sends, 0 replies",
                {"test_id": t["id"], "sends": c_sends},
            )
            actions.append({"action":"killed","test":t["template_name"]})

    return actions


# ── 7. Copy Generation ────────────────────────────────────────────────────────

def generate_improved_template(
    channel: str,
    business_type: str,
    country: str,
    current_template: str,
    performance_data: dict,
) -> str:
    """
    Generates an improved template informed by geo + vertical intelligence.
    Output is a PROPOSAL — written to system_journal, not deployed until approved.
    """
    from knowledge import GEO_PROFILES, get_vertical_profile

    geo      = GEO_PROFILES.get(country, {})
    vertical = get_vertical_profile(business_type, country)

    tone       = geo.get("tone", {}).get("style", "professional")
    ch_rank    = geo.get("channel_rank", {})
    trust      = ", ".join(geo.get("trust_signals", [])[:2])
    pain       = "; ".join(vertical.get("pain_points", [])[:2])
    pitch      = vertical.get("pitch_angle", {}).get("primary", "")
    sw_note    = vertical.get("software_landscape", {}).get("signal_implication", "")
    wa_warning = geo.get("wa_warning", "")

    length_guide = {
        "wa":    "2-3 short sentences. Conversational. No corporate language.",
        "email": "Subject line + 3-4 short paragraphs. Scannable.",
        "voice": "15-20 seconds when read aloud. One clear hook.",
        "sms":   "160 characters max.",
    }.get(channel, "appropriate length for channel")

    prompt = f"""You are Signal, marketing head for PracticeDesk — AI practice management for {business_type}s.

GEO INTELLIGENCE — {country}:
Tone: {tone}
Channel preference: {', '.join(f'{k}={v}' for k,v in sorted(ch_rank.items(),key=lambda x:x[1]))}
Trust signals: {trust}
{f'WARNING: {wa_warning}' if wa_warning and channel=='wa' else ''}

VERTICAL INTELLIGENCE — {business_type.title()}:
Key pain points: {pain}
Primary pitch: {pitch}
Software note: {sw_note}

CURRENT TEMPLATE (underperforming):
{current_template}

PERFORMANCE:
Reply rate: {performance_data.get('reply_rate','unknown')}
Open rate: {performance_data.get('open_rate','unknown')}
Sends: {performance_data.get('sends','unknown')}
Failure reason: {performance_data.get('failure_reason','not identified')}

Write an improved {channel} message. Length: {length_guide}
Output ONLY the message text."""

    resp = _claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role":"user","content":prompt}],
    )
    improved = resp.content[0].text.strip()

    # Write as proposal — not deployed until CEO/Neeraj approves
    _write_journal(
        "signal_copy_proposal",
        f"Signal proposes new {channel} template for {business_type}/{country}",
        {
            "channel":current_template, "business_type":business_type, "country":country,
            "current_template":current_template, "proposed_template":improved,
            "performance_data":performance_data,
        },
    )
    return improved


# ── 8a. Email A/B Hook Experiment ────────────────────────────────────────────

def register_hook_ab_test() -> dict:
    """Upsert the email subject-hook A/B test row. No-op if already registered.

    Control  = subject_a (moment-based hook: 'Most practices miss 60% of after-hours calls')
    Variant  = subject_b (timeline hook: 'CDCP window closes in 6 months')

    Benchmarks show timeline hooks outperform moment-based 2.3×;
    we test that signal on the live list before hardcoding the assumption.
    """
    db = get_client()
    existing = (
        db.table("ab_tests").select("id, status")
        .eq("template_name", "email_subject_hook").eq("channel", "email")
        .execute().data
    )
    if existing:
        return {"status": "already_registered", "id": existing[0]["id"]}
    result = db.table("ab_tests").insert({
        "template_name": "email_subject_hook",
        "channel":       "email",
        "business_type": "all",
        "country":       "all",
        "control_copy":  "subject_a — moment-based hook (e.g. 'Most practices miss 60% of after-hours calls')",
        "variant_copy":  "subject_b — timeline hook (e.g. 'CDCP window closes in 6 months')",
        "status":        "running",
        "autonomous":    True,
        "rationale":     "Benchmark data shows timeline hooks 2.3x moment-based; testing on live list before hardcoding.",
    }).execute()
    return result.data[0] if result.data else {}


def _sync_email_ab_stats() -> None:
    """Refresh ab_tests control/variant counters from email_sends + reply activity.

    Called from generate_weekly_report() so Signal's evaluate_ab_tests() has
    current data to auto-promote or auto-kill the hook experiment.
    """
    db = get_client()
    test_rows = (
        db.table("ab_tests").select("id")
        .eq("template_name", "email_subject_hook").eq("status", "running")
        .execute().data
    )
    if not test_rows:
        return
    test_id = test_rows[0]["id"]

    sends = db.table("email_sends").select("variant, lead_id").execute().data or []
    a_lead_ids = {str(r["lead_id"]) for r in sends if (r.get("variant") or "").upper() == "A"}
    b_lead_ids = {str(r["lead_id"]) for r in sends if (r.get("variant") or "").upper() == "B"}

    replies = db.table("lead_activities").select("lead_id").eq("type", "wa_reply_received").execute().data or []
    reply_ids = {str(r["lead_id"]) for r in replies}

    db.table("ab_tests").update({
        "control_sends":   len(a_lead_ids),
        "variant_sends":   len(b_lead_ids),
        "control_replies": len(a_lead_ids & reply_ids),
        "variant_replies": len(b_lead_ids & reply_ids),
    }).eq("id", test_id).execute()
    logger.info(
        "Signal email A/B stats synced — A: %d sends / %d replies; B: %d sends / %d replies",
        len(a_lead_ids), len(a_lead_ids & reply_ids),
        len(b_lead_ids), len(b_lead_ids & reply_ids),
    )


# ── 8. Weekly Report (Marketing Head Brief) ───────────────────────────────────

def generate_weekly_report() -> dict:
    """
    Signal's full weekly brief — the Marketing Head report.
    Covers: what's working, what's not, targets vs actuals,
    dead ends to stop, top projection, one recommendation.
    Written to system_journal for CEO to surface to Neeraj.
    """
    logger.info("Signal weekly report starting...")

    scores  = score_templates()
    funnel  = compute_funnel_metrics()
    dead    = detect_dead_ends()
    projs   = generate_projections()
    set_targets()
    target_updates = update_targets()

    # Summarise for Claude
    top_score = sorted([s for s in scores if s.get("sends",0)>=10],
                       key=lambda x: x.get("reply_rate",0), reverse=True)[:3]
    missed_targets = [t for t in target_updates if t.get("status") in ("missed","behind")]
    best_proj = sorted([p for p in projs if p.get("scenario")=="base"],
                       key=lambda x: x.get("mrr_6mo",0), reverse=True)[:1]

    top_score_txt = "\n".join(
        f"- {s['business_type']}/{s['country']} WA: {s.get('reply_rate',0)*100:.1f}% reply ({s.get('sends',0)} sends)"
        for s in top_score
    ) or "Insufficient data"

    dead_txt = "\n".join(
        f"- {d['channel']}/{d['business_type']}/{d['country']}: {d['sends']} sends, {d['rate']*100:.1f}% rate, {d['age_days']} days"
        for d in dead
    ) or "None detected"

    missed_txt = "\n".join(
        f"- {t['business_type']}/{t['country']} {t['metric']}: target {t['target_value']*100:.1f}%, actual {t['actual_value']*100:.1f}%"
        for t in missed_targets
    ) or "All targets on track"

    best_proj_txt = (
        f"{best_proj[0]['business_type']}/{best_proj[0]['country']}: "
        f"${best_proj[0]['mrr_6mo']:.0f} MRR at 6 months"
        if best_proj else "No projection data yet"
    )

    prompt = f"""You are Signal, the marketing head for PracticeDesk. Write the weekly marketing brief.

TOP PERFORMING TEMPLATES:
{top_score_txt}

TARGETS MISSED OR BEHIND:
{missed_txt}

DEAD ENDS DETECTED:
{dead_txt}

BEST PROJECTION (base case):
{best_proj_txt}

Write a tight weekly marketing brief (max 250 words) covering:
1. What's working — the one thing to keep doing
2. What to fix — the most important underperforming metric
3. What to stop — any dead ends
4. The number to watch this week (one specific metric)
5. One decision that needs Neeraj's call

Be direct. No preamble. Use plain English."""

    try:
        resp = _claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role":"user","content":prompt}],
        )
        brief = resp.content[0].text.strip()
    except Exception as exc:
        brief = f"Weekly report generation failed: {exc}"

    report = {
        "period":         _period_label(),
        "scores_computed":len(scores),
        "funnel_computed":len(funnel),
        "dead_ends":      len(dead),
        "projections":    len(projs),
        "targets_behind": len(missed_targets),
        "brief":          brief,
    }

    _write_journal(
        "signal_weekly_report",
        f"Signal Weekly Brief — {_period_label()}",
        report,
    )

    # Refresh email A/B hook counters so evaluate_ab_tests() has current data.
    try:
        _sync_email_ab_stats()
    except Exception as _e:
        logger.warning("Signal: could not sync email A/B stats: %s", _e)

    logger.info("Signal weekly report complete: %d scores, %d dead ends, %d targets behind",
                len(scores), len(dead), len(missed_targets))
    return report


# ── 10. Email Delivery ────────────────────────────────────────────────────────

def send_signal_email(report: dict) -> bool:
    """Email Signal's weekly brief to the founder via Resend."""
    resend_key    = os.environ.get("RESEND_API_KEY")
    founder_email = os.environ.get("FOUNDER_EMAIL", "khattarn3@yahoo.com")
    if not resend_key:
        logger.warning("Signal email: RESEND_API_KEY not set")
        return False

    brief = report.get("brief", "No brief generated.")
    period = report.get("period", _period_label())

    scores_line   = f"Templates scored: {report.get('scores_computed', 0)}"
    dead_line     = f"Dead ends detected: {report.get('dead_ends', 0)}"
    behind_line   = f"Targets behind/missed: {report.get('targets_behind', 0)}"
    projs_line    = f"Projection combos: {report.get('projections', 0)}"

    body = f"""Signal Weekly Brief — {period}

{brief}

───────────────────────────
{scores_line}
{dead_line}
{behind_line}
{projs_line}

Full data: system_journal table in Supabase → entry_type = signal_weekly_report
"""

    try:
        import requests as _req
        resp = _req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
            json={
                "from":    "Signal <signal@practicedesk.live>",
                "to":      [founder_email],
                "subject": f"Signal Weekly Brief — {period}",
                "text":    body,
            },
            timeout=15,
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            logger.warning("Signal email: Resend returned %d — %s", resp.status_code, resp.text[:200])
        return ok
    except Exception as exc:
        logger.warning("Signal email delivery failed: %s", exc)
        return False


# ── 9. Performance Feedback Brief (for Content Agent + VP Marketing) ──────────

def get_performance_feedback_brief() -> dict:
    """
    Compile a structured performance feedback brief for VP Marketing and Content Agent.
    Reads template_scores, funnel_metrics, and detected dead ends.
    Returns: winning patterns, underperformers, dead ends, recommended content actions.
    """
    db = get_client()

    scores = db.table("template_scores").select("*").execute().data or []
    targets_missed = db.table("targets").select("*").in_(
        "status", ["missed", "behind"]
    ).execute().data or []
    dead_ends = detect_dead_ends()

    winning = sorted(
        [
            s for s in scores
            if s.get("sends", 0) >= 10
            and (s.get("reply_rate") or s.get("open_rate") or 0) >= 0.05
        ],
        key=lambda x: x.get("reply_rate") or x.get("open_rate") or 0,
        reverse=True,
    )[:5]

    underperforming = sorted(
        [
            s for s in scores
            if s.get("sends", 0) >= 10
            and (s.get("reply_rate") or s.get("open_rate") or 0) < 0.03
            and s.get("status") != "killed"
        ],
        key=lambda x: x.get("sends", 0),
        reverse=True,
    )[:5]

    return {
        "generated_at":              _now(),
        "winning_templates":         winning,
        "underperforming_templates": underperforming,
        "dead_ends":                 dead_ends[:3],
        "targets_missed":            targets_missed[:5],
        "recommended_actions":       _generate_feedback_actions(winning, underperforming, dead_ends),
    }


def _generate_feedback_actions(
    winning: list[dict],
    underperforming: list[dict],
    dead_ends: list[dict],
) -> list[str]:
    """Produce human-readable recommended content actions from Signal data."""
    actions = []
    for s in underperforming[:3]:
        rate = (s.get("reply_rate") or s.get("open_rate") or 0) * 100
        actions.append(
            f"Refresh {s.get('channel')} template for {s.get('business_type')}/{s.get('country')}"
            f" — {rate:.1f}% rate on {s.get('sends')} sends, new angle needed"
        )
    if winning:
        top = winning[0]
        rate = (top.get("reply_rate") or top.get("open_rate") or 0) * 100
        actions.append(
            f"Replicate winning pattern from {top.get('business_type')}/{top.get('country')}"
            f" ({rate:.1f}% {top.get('channel')} rate) across underperforming verticals"
        )
    for d in dead_ends[:2]:
        actions.append(
            f"Stop {d['channel']} for {d['business_type']}/{d['country']}"
            f" — {d['sends']} sends, {d['rate']*100:.1f}% after {d['age_days']} days"
        )
    return actions
