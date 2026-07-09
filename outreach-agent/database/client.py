import os
from supabase import create_client

_client = None

# Email sequence: (template_number, day_from_start)
EMAIL_SEQUENCE = [
    (1,  0),
    (2,  3),
    (3,  6),
    (4,  9),
    (5, 12),
    (6, 30),
]


def get_client():
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


# ── Leads ─────────────────────────────────────────────────────────────────────

def get_leads(business_type=None, status=None, city=None, outreach_sent=None,
              email_engagement=None, voice_called=None, limit=25, offset=0, search=None,
              source=None):
    db = get_client()

    # Resolve voice_called filter via lead_activities lookup
    called_ids = None
    if voice_called is not None:
        rows = db.table("lead_activities").select("lead_id").in_("type", ["outbound_call", "voice_followup_placed"]).execute().data or []
        called_ids = list({str(r["lead_id"]) for r in rows})

    query = db.table("leads").select("*", count="exact")
    if business_type:
        query = query.eq("business_type", business_type)
    if status:
        query = query.eq("status", status)
    if city:
        query = query.ilike("city", f"%{city}%")
    if source:
        query = query.eq("source", source)
    if outreach_sent is True:
        query = query.eq("outreach_sent", True)
    elif outreach_sent is False:
        query = query.or_("outreach_sent.eq.false,outreach_sent.is.null")
    if email_engagement == "clicked":
        query = query.eq("email_clicked", True)
    elif email_engagement == "opened":
        query = query.eq("email_opened", True).or_("email_clicked.eq.false,email_clicked.is.null")
    elif email_engagement == "sent":
        query = query.eq("email_sent", True)
    if voice_called is True and called_ids:
        query = query.in_("id", called_ids)
    elif voice_called is True and called_ids is not None and len(called_ids) == 0:
        return {"data": [], "count": 0}  # no calls placed yet
    elif voice_called is False and called_ids is not None:
        if called_ids:
            query = query.not_.in_("id", called_ids)
    if search:
        query = query.or_(f"name.ilike.%{search}%,city.ilike.%{search}%")
    result = (
        query.order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {"data": result.data, "count": result.count}


def get_lead_by_id(lead_id):
    db = get_client()
    result = db.table("leads").select("*").eq("id", lead_id).single().execute()
    return result.data


def get_lead_by_place_id(place_id):
    db = get_client()
    result = db.table("leads").select("*").eq("place_id", place_id).execute()
    return result.data[0] if result.data else None


def get_existing_place_ids(business_type: str, city: str) -> set:
    """Return all place_ids already in the DB for this business type + city combo."""
    db = get_client()
    result = (
        db.table("leads")
        .select("place_id")
        .eq("business_type", business_type)
        .ilike("city", f"%{city}%")
        .execute()
    )
    return {row["place_id"] for row in result.data if row.get("place_id")}


def save_lead(data):
    db = get_client()
    result = db.table("leads").insert(data).execute()
    return result.data[0] if result.data else None


def update_lead(lead_id, data):
    db = get_client()
    result = db.table("leads").update(data).eq("id", lead_id).execute()
    return result.data[0] if result.data else None


def delete_lead(lead_id):
    db = get_client()
    db.table("leads").update({"status": "dead"}).eq("id", lead_id).execute()


def mark_contacted(lead_id, message):
    from datetime import datetime, timezone
    update_lead(lead_id, {
        "status": "contacted",
        "outreach_sent": True,
        "outreach_message": message,
        "outreach_date": datetime.now(timezone.utc).isoformat(),
    })


# ── Enrichment ────────────────────────────────────────────────────────────────

def get_leads_for_enrichment(limit=100):
    """Only leads that have never been attempted for email scraping."""
    db = get_client()
    result = (
        db.table("leads")
        .select("id, name, website, email")
        .not_.is_("website", "null")
        .neq("website", "")
        .eq("scrape_attempted", False)
        .limit(limit)
        .execute()
    )
    return result.data


def mark_scrape_attempted(lead_id: str, email: str | None):
    """Mark a lead as attempted. If email found, queue it for Email 1."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "scrape_attempted": True,
        "scrape_attempted_at": now,
    }
    if email:
        update["email"] = email
        update["next_email_due_at"] = now  # eligible for Email 1 immediately
        update["email_sequence_step"] = 0
        update["email_sequence_paused"] = False
    update_lead(lead_id, update)


# ── Email sequence ────────────────────────────────────────────────────────────

def get_leads_due_for_email(limit=50):
    """Leads where next_email_due_at <= now, not paused, not dead, have email, not bounced."""
    from datetime import datetime, timezone
    db = get_client()
    now = datetime.now(timezone.utc).isoformat()
    result = (
        db.table("leads")
        .select("*")
        .lte("next_email_due_at", now)
        .eq("email_sequence_paused", False)
        .eq("email_bounced", False)
        .neq("status", "dead")
        .not_.is_("email", "null")
        .neq("email", "")
        .limit(limit)
        .execute()
    )
    return result.data


def email_sequence_cap(lead: dict) -> int:
    """Job-ad leads run a shorter 3-email sequence (Change #11); everyone else uses the full cadence."""
    return 3 if lead.get("pain_signal") == "job_ad_frontdesk" else len(EMAIL_SEQUENCE)


def advance_email_sequence(lead_id: str, step_just_sent: int, sequence_length: int = None):
    """Update sequence state after sending step N. Sets next_email_due_at for step N+1."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    next_step = step_just_sent + 1
    cap = sequence_length or len(EMAIL_SEQUENCE)

    update = {
        "email_sequence_step": step_just_sent,
        "email_last_sent_at": now.isoformat(),
        "email_sent": True,
        "email_sent_date": now.isoformat(),
        # Reset per-email engagement so opens/clicks reflect the current email only
        "email_opened": False,
        "email_opened_at": None,
        "email_clicked": False,
        "email_clicked_at": None,
        "email_clicked_link": None,
    }

    if next_step <= cap:
        current_days = EMAIL_SEQUENCE[step_just_sent - 1][1]
        next_days    = EMAIL_SEQUENCE[next_step - 1][1]
        interval     = next_days - current_days
        update["next_email_due_at"] = (now + timedelta(days=interval)).isoformat()
    else:
        update["email_sequence_paused"] = True
        update["next_email_due_at"]     = None

    update_lead(lead_id, update)

    # First email = first contact — promote status from new → contacted
    if step_just_sent == 1:
        get_client().table("leads").update({"status": "contacted"}).eq("id", lead_id).eq("status", "new").execute()


def mark_emailed(lead_id: str):
    """Mark a manually-sent email and advance the sequence from wherever the lead currently is."""
    db = get_client()
    row = db.table("leads").select("email_sequence_step").eq("id", lead_id).single().execute()
    current_step = (row.data.get("email_sequence_step") or 0) if row.data else 0
    advance_email_sequence(lead_id, current_step + 1)


def pause_sequence(lead_id: str, reason: str = ""):
    update_lead(lead_id, {"email_sequence_paused": True, "next_email_due_at": None})
    if reason:
        log_activity(lead_id, "sequence_paused", {"reason": reason})


# ── Activity log ──────────────────────────────────────────────────────────────

def log_activity(lead_id, activity_type: str, detail: dict = None):
    if not lead_id:
        return  # system-level events without a lead are not persisted (no FK to satisfy)
    from datetime import datetime, timezone
    try:
        get_client().table("lead_activities").insert({
            "lead_id": str(lead_id),
            "type": activity_type,
            "detail": detail or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass  # non-critical


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats():
    db = get_client()
    leads = db.table("leads").select(
        "status, business_type, city, email_sent, outreach_sent, "
        "email_opened, email_clicked, email_sequence_step, email_sequence_paused"
    ).execute().data
    total = len(leads)
    by_status = {}
    by_type   = {}
    by_city   = {}
    emailed = wa_sent = email_opened = email_clicked = 0
    in_sequence = sequence_complete = 0

    for lead in leads:
        s  = lead.get("status", "new")
        bt = lead.get("business_type") or "unknown"
        city = lead.get("city") or "unknown"
        by_status[s]   = by_status.get(s, 0) + 1
        by_type[bt]    = by_type.get(bt, 0) + 1
        by_city[city]  = by_city.get(city, 0) + 1
        if lead.get("email_sent"):        emailed += 1
        if lead.get("outreach_sent"):     wa_sent += 1
        if lead.get("email_opened"):      email_opened += 1
        if lead.get("email_clicked"):     email_clicked += 1
        step   = lead.get("email_sequence_step") or 0
        paused = lead.get("email_sequence_paused") or False
        if step > 0 and not paused:  in_sequence += 1
        if paused and step >= len(EMAIL_SEQUENCE): sequence_complete += 1

    # Count leads Sophie has called (any placement activity)
    sophie_called_rows = db.table("lead_activities").select("lead_id").in_("type", ["outbound_call", "voice_followup_placed"]).execute().data or []
    sophie_called = len({str(r["lead_id"]) for r in sophie_called_rows})

    return {
        "total_leads":       total,
        "emailed":           emailed,
        "wa_sent":           wa_sent,
        "email_opened":      email_opened,
        "email_clicked":     email_clicked,
        "sophie_called":     sophie_called,
        "replied":           by_status.get("replied", 0),
        "converted":         by_status.get("converted", 0),
        "in_sequence":       in_sequence,
        "sequence_complete": sequence_complete,
        "by_business_type":  by_type,
        "by_city":           by_city,
    }


# ── Campaigns ─────────────────────────────────────────────────────────────────

def get_campaigns(limit=50):
    db = get_client()
    result = (
        db.table("campaign_runs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def save_campaign_run(data):
    db = get_client()
    result = db.table("campaign_runs").insert(data).execute()
    return result.data[0] if result.data else None


def update_campaign_run(run_id: str, data: dict):
    get_client().table("campaign_runs").update(data).eq("id", run_id).execute()


def save_email_send(lead_id: str, campaign_run_id: str, resend_email_id: str,
                    email_number: int, sequence_step: int, market: str | None = None):
    """Record a sent email and store resend_email_id on the lead for webhook lookup."""
    try:
        payload = {
            "lead_id": lead_id,
            "campaign_run_id": campaign_run_id,
            "resend_email_id": resend_email_id,
            "email_number": email_number,
            "sequence_step": sequence_step,
        }
        if market:
            payload["market"] = market
        get_client().table("email_sends").insert(payload).execute()
    except Exception:
        pass
    update_lead(lead_id, {"resend_email_id": resend_email_id})


def get_emails_sent_today(market: str | None = None) -> int:
    """Count email_sends since UTC midnight, optionally filtered by market (e.g. CASL CA cap)."""
    from datetime import datetime, timezone
    db = get_client()
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    query = db.table("email_sends").select("id", count="exact").gte("sent_at", start)
    if market:
        query = query.eq("market", market)
    return query.execute().count or 0


def get_email_send_by_resend_id(resend_email_id: str):
    result = (
        get_client()
        .table("email_sends")
        .select("lead_id, campaign_run_id")
        .eq("resend_email_id", resend_email_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def record_email_opened(lead_id: str, campaign_run_id: str | None, opened_at=None):
    from datetime import datetime, timezone
    ts = opened_at or datetime.now(timezone.utc).isoformat()
    update_lead(lead_id, {"email_opened": True, "email_opened_at": ts})
    if campaign_run_id:
        db = get_client()
        row = db.table("campaign_runs").select("emails_opened").eq("id", campaign_run_id).single().execute()
        current = (row.data.get("emails_opened") or 0) if row.data else 0
        db.table("campaign_runs").update({"emails_opened": current + 1}).eq("id", campaign_run_id).execute()


def record_email_clicked(lead_id: str, campaign_run_id: str | None, link: str = "", clicked_at=None):
    from datetime import datetime, timezone
    ts = clicked_at or datetime.now(timezone.utc).isoformat()
    update_lead(lead_id, {"email_clicked": True, "email_clicked_at": ts, "email_clicked_link": link})
    if campaign_run_id:
        db = get_client()
        row = db.table("campaign_runs").select("emails_clicked").eq("id", campaign_run_id).single().execute()
        current = (row.data.get("emails_clicked") or 0) if row.data else 0
        db.table("campaign_runs").update({"emails_clicked": current + 1}).eq("id", campaign_run_id).execute()


def get_leads_due_callback() -> list[dict]:
    """
    Return leads that have a callback_scheduled activity whose callback_at is now or past,
    and have not yet received an outbound_call after that scheduled time.
    """
    from datetime import datetime, timezone
    db = get_client()
    now = datetime.now(timezone.utc)

    # All scheduled callbacks
    rows = (
        db.table("lead_activities")
        .select("lead_id, detail, created_at")
        .eq("type", "callback_scheduled")
        .execute()
        .data
    ) or []

    due_lead_ids = []
    for row in rows:
        detail = row.get("detail") or {}
        callback_at = detail.get("callback_at", "")
        if not callback_at:
            continue
        try:
            # callback_at is stored in the lead's local timezone offset (e.g. "-04:00"),
            # not UTC — comparing the raw ISO strings against `now` (always "+00:00")
            # is a string compare, not a time compare, and misfires by the size of the
            # offset. Parse both to aware datetimes and compare the actual instants.
            cb_dt = datetime.fromisoformat(callback_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if cb_dt <= now:
            due_lead_ids.append(str(row["lead_id"]))

    if not due_lead_ids:
        return []

    # Exclude any that already received an outbound_call after scheduling
    called_rows = (
        db.table("lead_activities")
        .select("lead_id")
        .eq("type", "outbound_call")
        .in_("lead_id", due_lead_ids)
        .execute()
        .data
    ) or []
    already_called = {str(r["lead_id"]) for r in called_rows}

    remaining = [lid for lid in due_lead_ids if lid not in already_called]
    if not remaining:
        return []

    result = (
        db.table("leads")
        .select("id, name, phone, city, business_type, status")
        .in_("id", remaining)
        .not_.in_("status", ["dead", "converted"])
        .execute()
        .data
    ) or []
    return result


def get_clicked_uncalled_leads() -> list[dict]:
    """
    Return leads that:
      - clicked an email (email_clicked=true)
      - are not dead or converted
      - clicked before today's UTC date (next-working-day rule — never call same day)
      - have not already received an outbound_call activity
    """
    from datetime import date as _date
    today_utc = _date.today().isoformat()  # "YYYY-MM-DD"

    db = get_client()

    clicked = (
        db.table("leads")
        .select("id, name, phone, city, business_type, status, email_clicked_at")
        .eq("email_clicked", True)
        .not_.in_("status", ["dead", "converted"])
        .execute()
        .data
    ) or []

    # Only call leads whose click was recorded before today (UTC) — ensures next-working-day minimum gap
    clicked = [
        r for r in clicked
        if r.get("email_clicked_at") and r["email_clicked_at"][:10] < today_utc
    ]

    if not clicked:
        return []

    clicked_ids = [str(r["id"]) for r in clicked]

    already_called_rows = (
        db.table("lead_activities")
        .select("lead_id")
        .in_("type", ["outbound_call", "voice_followup_placed"])
        .in_("lead_id", clicked_ids)
        .execute()
        .data
    ) or []
    already_called = {str(r["lead_id"]) for r in already_called_rows}

    return [r for r in clicked if str(r["id"]) not in already_called]


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key):
    db = get_client()
    result = db.table("settings").select("value").eq("key", key).execute()
    return result.data[0]["value"] if result.data else None


def save_setting(key, value):
    from datetime import datetime, timezone
    get_client().table("settings").upsert({
        "key": key,
        "value": value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


# ── Follow-up queries ─────────────────────────────────────────────────────────

def get_lead_by_phone(phone: str):
    """Look up a lead by phone number. Tries exact match then last-9-digit suffix."""
    db = get_client()
    digits = "".join(c for c in phone if c.isdigit())
    result = db.table("leads").select("*").or_(
        f"phone.eq.{phone},phone.ilike.%{digits[-9:]}%"
    ).limit(1).execute()
    return result.data[0] if result.data else None


def get_leads_for_followup(limit=20) -> list:
    """Leads that were WA-contacted 3+ days ago, haven't replied/died, and haven't had a follow-up sent."""
    from datetime import datetime, timezone, timedelta
    db = get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    sent_result = db.table("lead_activities").select("lead_id").eq("type", "wa_followup_sent").execute()
    already_sent = {str(r["lead_id"]) for r in sent_result.data}

    result = (
        db.table("leads")
        .select("*")
        .eq("status", "contacted")
        .eq("outreach_sent", True)
        .lte("outreach_date", cutoff)
        .not_.is_("phone", "null")
        .neq("phone", "")
        .limit(limit * 5)  # over-fetch to cover already-sent leads, then filter in Python
        .execute()
    )
    leads = [l for l in result.data if str(l["id"]) not in already_sent]
    return leads[:limit]


def get_voice_priority_calls_today() -> int:
    """Count outbound_call activities placed by the voice priority queue since UTC midnight —
    used to turn voice_dial_cap into a real daily cap (the job runs hourly, so without this
    each run independently allows up to `cap` fresh leads, letting the real daily total run
    several times past the configured cap)."""
    from datetime import datetime, timezone
    db = get_client()
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    rows = (
        db.table("lead_activities")
        .select("detail")
        .eq("type", "outbound_call")
        .gte("created_at", start)
        .execute()
        .data or []
    )
    return sum(1 for r in rows if (r.get("detail") or {}).get("trigger") == "voice_priority_queue")


def get_voice_priority_queue(cap: int = 50) -> list[dict]:
    """
    Returns up to `cap` leads ranked for voice outreach in this priority order:
      Tier 1: clicked an email (email_clicked=True, click was before today UTC)
      Tier 2: opened but not clicked (email_opened=True, email_clicked=False/null)
      Tier 3: emailed >24h ago, not opened
      Tier 4: never contacted (no email sent, no WA sent)
    Within each tier: sorted by pain_score DESC.
    Excludes leads already called (outbound_call or voice_followup_placed).
    Excludes dead/converted leads and leads with no phone.
    """
    from datetime import datetime, timezone, timedelta
    db = get_client()
    today_utc   = datetime.now(timezone.utc).date().isoformat()
    cutoff_24h  = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    called_rows = (
        db.table("lead_activities")
        .select("lead_id")
        .in_("type", ["outbound_call", "voice_followup_placed"])
        .execute()
        .data or []
    )
    called_ids = {str(r["lead_id"]) for r in called_rows}

    candidates = (
        db.table("leads")
        .select(
            "id, name, phone, city, market, business_type, status, "
            "email_clicked, email_clicked_at, email_opened, email_sent, "
            "email_last_sent_at, outreach_sent, pain_score, pain_signal, pain_finding"
        )
        .not_.in_("status", ["dead", "converted"])
        .not_.is_("phone", "null")
        .neq("phone", "")
        .limit(cap * 10)
        .execute()
        .data or []
    )

    def _tier(lead: dict) -> int:
        if lead.get("email_clicked") and (lead.get("email_clicked_at") or "")[:10] < today_utc:
            return 1
        if lead.get("email_opened") and not lead.get("email_clicked"):
            return 2
        last_sent = lead.get("email_last_sent_at") or ""
        if lead.get("email_sent") and last_sent and last_sent < cutoff_24h:
            return 3
        if not lead.get("email_sent") and not lead.get("outreach_sent"):
            return 4
        return 99

    scored = []
    for lead in candidates:
        if str(lead["id"]) in called_ids:
            continue
        tier = _tier(lead)
        if tier == 99:
            continue
        pain = lead.get("pain_score") or 0
        scored.append((tier, -pain, lead))

    scored.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in scored[:cap]]


def get_leads_for_voice_followup(limit=10) -> list:
    """Leads that were WA-contacted 5+ days ago, haven't replied/died, and haven't had a voice call placed."""
    from datetime import datetime, timezone, timedelta
    db = get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

    placed_result = db.table("lead_activities").select("lead_id").eq("type", "voice_followup_placed").execute()
    already_placed = {str(r["lead_id"]) for r in placed_result.data}

    result = (
        db.table("leads")
        .select("*")
        .eq("status", "contacted")
        .eq("outreach_sent", True)
        .lte("outreach_date", cutoff)
        .not_.is_("phone", "null")
        .neq("phone", "")
        .limit(limit * 5)
        .execute()
    )
    leads = [l for l in result.data if str(l["id"]) not in already_placed]
    return leads[:limit]


# ── WA Inbox ─────────────────────────────────────────────────────────────────

PHONE_NUMBER_LABELS = {
    "1122821020915109": "IN",
    "1131796990021193": "US",
}


def save_wa_inbox(data: dict) -> dict | None:
    db = get_client()
    result = db.table("wa_inbox").insert(data).execute()
    return result.data[0] if result.data else None


def update_wa_inbox(inbox_id: str, data: dict) -> None:
    get_client().table("wa_inbox").update(data).eq("id", inbox_id).execute()


def get_wa_inbox(limit: int = 100, status: str | None = None) -> list[dict]:
    db = get_client()
    query = (
        db.table("wa_inbox")
        .select("*")
        .order("received_at", desc=True)
        .limit(limit)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


def get_wa_inbox_unread_count() -> int:
    result = get_client().table("wa_inbox").select("id", count="exact").eq("status", "new").execute()
    return result.count or 0


# ── Content Approvals ─────────────────────────────────────────────────────────

def save_approval(data: dict) -> dict | None:
    db = get_client()
    result = db.table("content_approvals").insert(data).execute()
    return result.data[0] if result.data else None


def get_approvals(status: str | None = None, limit: int = 100) -> list[dict]:
    db = get_client()
    query = (
        db.table("content_approvals")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


def update_approval(approval_id: str, data: dict) -> dict | None:
    from datetime import datetime, timezone
    if data.get("status") in ("approved", "rejected"):
        data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    db = get_client()
    result = db.table("content_approvals").update(data).eq("id", approval_id).execute()
    return result.data[0] if result.data else None


def get_approvals_pending_count() -> int:
    result = get_client().table("content_approvals").select("id", count="exact").eq("status", "pending").execute()
    return result.count or 0


# ── Danger zone ───────────────────────────────────────────────────────────────

def clear_all_leads():
    db = get_client()
    db.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def reset_outreach_flags():
    db = get_client()
    db.table("leads").update({"outreach_sent": False, "status": "new"}).eq("outreach_sent", True).execute()
