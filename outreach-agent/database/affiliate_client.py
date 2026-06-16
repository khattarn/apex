"""
Database layer for Agent 11 — Affiliate Tracker.
Tables: affiliates, referrals, commissions
"""

import random
import string
from database.client import get_client


# ── Affiliates ────────────────────────────────────────────────────────────────

def get_existing_handles() -> list[str]:
    """Return all instagram handles already in the affiliates table."""
    rows = get_client().table("affiliates").select("instagram_handle").execute().data or []
    return [r["instagram_handle"] for r in rows]


def save_affiliate(data: dict) -> dict | None:
    """Insert a new affiliate. Silently skips if the handle already exists."""
    db = get_client()
    handle = data.get("instagram_handle", "")
    if not handle:
        return None
    existing = db.table("affiliates").select("id").eq("instagram_handle", handle).execute().data
    if existing:
        return None
    from datetime import datetime, timezone
    data = {**data, "scraped_at": datetime.now(timezone.utc).isoformat()}
    result = db.table("affiliates").insert(data).execute()
    return result.data[0] if result.data else None


def get_affiliates(status: str | None = None, limit: int = 100, offset: int = 0) -> dict:
    db = get_client()
    query = db.table("affiliates").select("*", count="exact")
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"data": result.data or [], "count": result.count or 0}


def get_affiliate_by_id(affiliate_id: str) -> dict | None:
    result = get_client().table("affiliates").select("*").eq("id", affiliate_id).single().execute()
    return result.data


def update_affiliate(affiliate_id: str, data: dict) -> dict | None:
    from datetime import datetime, timezone
    data = {**data, "updated_at": datetime.now(timezone.utc).isoformat()}
    result = get_client().table("affiliates").update(data).eq("id", affiliate_id).execute()
    return result.data[0] if result.data else None


def _generate_referral_code(name: str) -> str:
    """Generate a unique referral code like RAHUL4F2A."""
    base = "".join(c for c in name.upper() if c.isalpha())[:6] or "AFF"
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{base}{suffix}"


def onboard_affiliate(affiliate_id: str, upi_id: str, bar_enrollment: str = "") -> dict | None:
    """Promote a prospect to active affiliate — generates referral code."""
    affiliate = get_affiliate_by_id(affiliate_id)
    if not affiliate:
        return None

    code = _generate_referral_code(affiliate.get("name", "AFF"))
    # Ensure uniqueness
    db = get_client()
    while db.table("affiliates").select("id").eq("referral_code", code).execute().data:
        code = _generate_referral_code(affiliate.get("name", "AFF"))

    from datetime import datetime, timezone
    return update_affiliate(affiliate_id, {
        "status": "active",
        "upi_id": upi_id,
        "bar_enrollment": bar_enrollment,
        "referral_code": code,
        "onboarded_at": datetime.now(timezone.utc).isoformat(),
    })


def get_affiliate_stats() -> dict:
    db = get_client()
    rows = db.table("affiliates").select("status").execute().data or []
    counts: dict[str, int] = {}
    for r in rows:
        s = r.get("status", "prospect")
        counts[s] = counts.get(s, 0) + 1
    return {
        "total": len(rows),
        "prospect": counts.get("prospect", 0),
        "invited": counts.get("invited", 0),
        "active": counts.get("active", 0),
        "inactive": counts.get("inactive", 0),
    }


# ── Referrals ─────────────────────────────────────────────────────────────────

def get_referrals(affiliate_id: str | None = None) -> list[dict]:
    db = get_client()
    query = db.table("referrals").select("*").order("created_at", desc=True)
    if affiliate_id:
        query = query.eq("affiliate_id", affiliate_id)
    return query.execute().data or []


def record_referral(referral_code: str, user_email: str, user_name: str = "") -> dict | None:
    """Called when a new user signs up via ?ref=CODE at LegalAidAI."""
    db = get_client()
    affiliate = db.table("affiliates").select("id").eq("referral_code", referral_code).execute().data
    if not affiliate:
        return None
    result = db.table("referrals").insert({
        "affiliate_id": affiliate[0]["id"],
        "referral_code": referral_code,
        "user_email": user_email,
        "user_name": user_name,
    }).execute()
    return result.data[0] if result.data else None


def record_conversion(referral_id: str, commission_type: str = "conversion") -> dict | None:
    """Called when a referred user makes their first payment."""
    db = get_client()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    referral_res = db.table("referrals").update({
        "converted_to_paid": True,
        "conversion_date": now,
    }).eq("id", referral_id).execute()
    referral = referral_res.data[0] if referral_res.data else None
    if not referral:
        return None

    # Get affiliate's UPI for the commission record
    aff = db.table("affiliates").select("id, upi_id").eq("id", referral["affiliate_id"]).execute().data
    upi_id = aff[0]["upi_id"] if aff else ""

    comm_result = db.table("commissions").insert({
        "affiliate_id": referral["affiliate_id"],
        "referral_id": referral_id,
        "amount": 500,
        "type": commission_type,
        "status": "pending",
        "upi_id": upi_id,
    }).execute()
    return comm_result.data[0] if comm_result.data else None


# ── Commissions ───────────────────────────────────────────────────────────────

def get_commissions(status: str | None = None) -> list[dict]:
    db = get_client()
    query = (
        db.table("commissions")
        .select("*, affiliates(name, instagram_handle, upi_id), referrals(user_email, user_name)")
        .order("created_at", desc=True)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


def mark_commission_paid(commission_id: str, notes: str = "") -> dict | None:
    from datetime import datetime, timezone
    result = get_client().table("commissions").update({
        "status": "paid",
        "paid_date": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }).eq("id", commission_id).execute()
    return result.data[0] if result.data else None
