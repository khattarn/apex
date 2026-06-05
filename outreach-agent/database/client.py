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
              limit=25, offset=0, search=None):
    db = get_client()
    query = db.table("leads").select("*", count="exact")
    if business_type:
        query = query.eq("business_type", business_type)
    if status:
        query = query.eq("status", status)
    if city:
        query = query.ilike("city", f"%{city}%")
    if outreach_sent is True:
        query = query.eq("outreach_sent", True)
    elif outreach_sent is False:
        # NULL rows also count as "not sent"
        query = query.or_("outreach_sent.eq.false,outreach_sent.is.null")
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
    """Leads where next_email_due_at <= now, not paused, not dead, have email."""
    from datetime import datetime, timezone
    db = get_client()
    now = datetime.now(timezone.utc).isoformat()
    result = (
        db.table("leads")
        .select("*")
        .lte("next_email_due_at", now)
        .eq("email_sequence_paused", False)
        .neq("status", "dead")
        .not_.is_("email", "null")
        .neq("email", "")
        .limit(limit)
        .execute()
    )
    return result.data


def advance_email_sequence(lead_id: str, step_just_sent: int):
    """Update sequence state after sending step N. Sets next_email_due_at for step N+1."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    next_step = step_just_sent + 1

    update = {
        "email_sequence_step": step_just_sent,
        "email_last_sent_at": now.isoformat(),
        "email_sent": True,
        "email_sent_date": now.isoformat(),
    }

    if next_step <= len(EMAIL_SEQUENCE):
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
    """Legacy single-send mark — also advances sequence from step 0 → 1."""
    advance_email_sequence(lead_id, 1)


def pause_sequence(lead_id: str, reason: str = ""):
    update_lead(lead_id, {"email_sequence_paused": True, "next_email_due_at": None})
    if reason:
        log_activity(lead_id, "sequence_paused", {"reason": reason})


# ── Activity log ──────────────────────────────────────────────────────────────

def log_activity(lead_id: str, activity_type: str, detail: dict = None):
    from datetime import datetime, timezone
    try:
        get_client().table("lead_activities").insert({
            "lead_id": lead_id,
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

    return {
        "total_leads":       total,
        "emailed":           emailed,
        "wa_sent":           wa_sent,
        "email_opened":      email_opened,
        "email_clicked":     email_clicked,
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
                    email_number: int, sequence_step: int):
    """Record a sent email and store resend_email_id on the lead for webhook lookup."""
    try:
        get_client().table("email_sends").insert({
            "lead_id": lead_id,
            "campaign_run_id": campaign_run_id,
            "resend_email_id": resend_email_id,
            "email_number": email_number,
            "sequence_step": sequence_step,
        }).execute()
    except Exception:
        pass
    update_lead(lead_id, {"resend_email_id": resend_email_id})


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


# ── Danger zone ───────────────────────────────────────────────────────────────

def clear_all_leads():
    db = get_client()
    db.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def reset_outreach_flags():
    db = get_client()
    db.table("leads").update({"outreach_sent": False, "status": "new"}).eq("outreach_sent", True).execute()
