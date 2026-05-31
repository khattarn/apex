import os
from supabase import create_client

_client = None


def get_client():
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


def get_leads(business_type=None, status=None, city=None, outreach_sent=None, limit=25, offset=0, search=None):
    db = get_client()
    query = db.table("leads").select("*", count="exact")
    if business_type:
        query = query.eq("business_type", business_type)
    if status:
        query = query.eq("status", status)
    if city:
        query = query.ilike("city", f"%{city}%")
    if outreach_sent is not None:
        query = query.eq("outreach_sent", outreach_sent)
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


def get_stats():
    db = get_client()
    leads = db.table("leads").select("status, business_type, city").execute().data
    total = len(leads)
    by_status = {}
    by_type = {}
    by_city = {}
    for lead in leads:
        s = lead.get("status", "new")
        bt = lead.get("business_type") or "unknown"
        city = lead.get("city") or "unknown"
        by_status[s] = by_status.get(s, 0) + 1
        by_type[bt] = by_type.get(bt, 0) + 1
        by_city[city] = by_city.get(city, 0) + 1
    return {
        "total_leads": total,
        "contacted": by_status.get("contacted", 0),
        "replied": by_status.get("replied", 0),
        "converted": by_status.get("converted", 0),
        "by_business_type": by_type,
        "by_city": by_city,
    }


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


def get_setting(key):
    db = get_client()
    result = db.table("settings").select("value").eq("key", key).execute()
    return result.data[0]["value"] if result.data else None


def save_setting(key, value):
    db = get_client()
    from datetime import datetime, timezone
    db.table("settings").upsert({
        "key": key,
        "value": value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def clear_all_leads():
    db = get_client()
    db.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def reset_outreach_flags():
    db = get_client()
    db.table("leads").update({"outreach_sent": False, "status": "new"}).eq("outreach_sent", True).execute()
