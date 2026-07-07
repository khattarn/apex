"""
ingest.py — Manual ingestion for curated lead lists (press, social, AI research, job ads).

Use when you have a curated list and want to seed directly rather than running a Maps
text-search sweep.

Flow per row:
  Find Place from text → Place Details → dedupe → compute_pain (force override)
  → save_lead → mark_scrape_attempted (wires email sequence)

Row dict: {name, city, vertical, address?, phone?, email?}
  phone  — pre-researched fallback if Places returns nothing
  email  — pre-researched; if supplied, skips inline regex scrape

ingest_rows() is the shared core; ingest_new_businesses() and ingest_job_ad_leads() are
thin wrappers that force the pain_signal/pain_finding/source for their scenario.
Pass dry_run=True to resolve + enrich without writing to Supabase or the email sequence —
useful for previewing a batch before committing it.
"""

import os
import re
import requests
import googlemaps

from agents.enrichment import (
    PLACES_DETAIL_FIELDS, fetch_website_html, compute_pain, detect_online_booking,
)
from database.client import (
    get_lead_by_place_id, save_lead, mark_scrape_attempted, log_activity,
)

_FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_EMAIL_EXCLUDE = ("sentry", "example.com", "schema.org", "wix.", "w3.org", "pixel")


def _find_place_id(name: str, city: str, api_key: str) -> str | None:
    resp = requests.get(
        _FIND_PLACE_URL,
        params={
            "input":     f"{name} {city}",
            "inputtype": "textquery",
            "fields":    "place_id",
            "key":       api_key,
        },
        timeout=10,
    ).json()
    candidates = resp.get("candidates", [])
    return candidates[0]["place_id"] if candidates else None


def ingest_rows(
    rows: list[dict],
    *,
    pain_signal: str,
    pain_finding,
    source: str,
    market: str = "CA",
    force_pain_score: int | None = None,
    dry_run: bool = False,
) -> dict:
    """
    rows: [{name, city, vertical, address?, phone?, email?}]
    pain_finding: str, or callable(row) -> str, for per-row wording (e.g. "recently opened in {city}")
    force_pain_score: overrides the computed heuristic score (e.g. to guarantee top-of-queue ranking)
    dry_run: resolve + enrich but skip save_lead / mark_scrape_attempted / log_activity —
             returns the same shape so callers can preview before committing.
    Returns {saved: [...], skipped: [...], unresolved: [...]}
    Each saved entry: {name, city, place_id, phone, email, pain_signal, pain_finding, dry_run?}
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set")

    gmaps = googlemaps.Client(key=api_key)
    saved, skipped, unresolved = [], [], []

    for row in rows:
        name          = row["name"]
        city          = row["city"]
        vertical      = row["vertical"]
        known_phone   = row.get("phone", "")
        known_email   = row.get("email", "")

        # 1. Resolve via Find Place from text
        place_id = _find_place_id(name, city, api_key)
        if not place_id:
            unresolved.append({
                "name": name, "city": city, "vertical": vertical,
                "reason": "no Google Maps match — not yet indexed",
            })
            continue

        # 2. Dedupe by place_id
        if get_lead_by_place_id(place_id):
            skipped.append({
                "name": name, "city": city, "place_id": place_id,
                "reason": "already in leads",
            })
            continue

        # 3. Place Details
        details = gmaps.place(place_id, fields=PLACES_DETAIL_FIELDS).get("result", {})
        website = details.get("website", "")

        # 4. Pain heuristic (gives pain_signals list for has_online_booking + a fallback score)
        html = fetch_website_html(website, timeout=6)
        pain = compute_pain(details, html)
        pain_score = pain["pain_score"] if force_pain_score is None else force_pain_score

        # 5. Forced pain signal — confirmed externally, no heuristic needed
        finding = pain_finding(row) if callable(pain_finding) else pain_finding

        # 6. has_online_booking column (uses heuristic result)
        pain_signal_names = [s["signal"] for s in pain["pain_signals"]]
        if not website or "no_website" in pain_signal_names:
            has_online_booking = None
        elif "no_online_booking" in pain_signal_names:
            has_online_booking = False
        else:
            has_online_booking = True

        # 7. Phone: Places is canonical; fall back to pre-researched value
        phone = details.get("formatted_phone_number") or known_phone

        # 8. Email: use pre-researched value; only regex-scrape if not provided
        email = known_email or None
        if not email and html:
            for m in _EMAIL_RE.finditer(html):
                candidate = m.group(0).lower()
                if not any(x in candidate for x in _EMAIL_EXCLUDE):
                    email = m.group(0)
                    break

        if dry_run:
            saved.append({
                "name":         details.get("name", name),
                "city":         city,
                "place_id":     place_id,
                "phone":        phone,
                "email":        email,
                "pain_signal":  pain_signal,
                "pain_finding": finding,
                "dry_run":      True,
            })
            continue

        # 9. Save lead
        opening_hours = details.get("opening_hours") or {}
        lead = save_lead({
            "name":               details.get("name", name),
            "address":            details.get("formatted_address", row.get("address", "")),
            "place_id":           place_id,
            "phone":              phone,
            "website":            website,
            "rating":             details.get("rating"),
            "user_ratings_total": details.get("user_ratings_total"),
            "hours_json":         opening_hours.get("weekday_text") or None,
            "has_online_booking": has_online_booking,
            "pain_score":         pain_score,
            "pain_signal":        pain_signal,
            "pain_finding":       finding,
            "pain_signals":       pain["pain_signals"],
            "business_type":      vertical,
            "city":               city,
            "market":             market,
            "status":             "new",
            "source":             source,
        })
        if not lead:
            unresolved.append({
                "name": name, "city": city, "place_id": place_id,
                "reason": "DB save failed",
            })
            continue

        # 10. Wire into email sequence (sets next_email_due_at if email found)
        mark_scrape_attempted(lead["id"], email)
        log_activity(lead["id"], "ingested", {"source": source})

        saved.append({
            "name":         lead["name"],
            "city":         city,
            "place_id":     place_id,
            "phone":        phone,
            "email":        email,
            "pain_signal":  pain_signal,
            "pain_finding": finding,
        })

    return {"saved": saved, "skipped": skipped, "unresolved": unresolved}


def ingest_new_businesses(rows: list[dict], dry_run: bool = False) -> dict:
    """Recently-opened businesses — forces pain_signal='new_business'."""
    return ingest_rows(
        rows,
        pain_signal="new_business",
        pain_finding=lambda row: f"recently opened in {row['city']}",
        source="new_business_manual",
        market="CA",
        dry_run=dry_run,
    )


def ingest_job_ad_leads(
    rows: list[dict],
    dry_run: bool = False,
    source: str = "job_ad_indeed",
    pain_finding: str = "actively hiring a front-desk receptionist (seen on Indeed)",
) -> dict:
    """
    Clinics actively hiring a front-desk receptionist (seen on a job board — manual
    Indeed batches use the defaults; the SerpAPI cron passes source="job_ad_serpapi"
    and the shorter finding text since Google Jobs aggregates multiple boards, not
    just Indeed).
    force_pain_score=100 keeps these at the top of the pain_score-ranked voice
    priority queue (see database.client.get_voice_priority_queue) — phone-first via
    Sophie per docs/apex-rebuild/job-ad-outreach.md. market='CA' also puts them on the
    lighter CASL email cadence (agents/email_personalizer.py._first_email_number).
    """
    return ingest_rows(
        rows,
        pain_signal="job_ad_frontdesk",
        pain_finding=pain_finding,
        source=source,
        market="CA",
        force_pain_score=100,
        dry_run=dry_run,
    )
