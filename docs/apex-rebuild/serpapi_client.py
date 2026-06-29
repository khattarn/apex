"""
serpapi_client.py — thin wrapper around SerpAPI's Google Jobs engine.

Drop into outreach-agent/agents/ (or outreach-agent/utils/). Used by the job-ad scout
(_job_jobad_scout, Change #11) to find clinics hiring a receptionist, which then flow into
the Places-resolve ingestion path and get flagged pain_signal="job_ad_frontdesk".

Scope: ONLY Google Jobs. Resolving a company name → place_id/phone/website still uses the
existing Google Places path (prospector), so we don't spend SerpAPI quota on map lookups.

Env: SERPAPI_KEY
Quota: free tier ~100–250 searches/mo; paid from ~$25/1,000. Every call here = 1 search.
       Module counts calls in-process; the cron should also persist a monthly counter in the
       settings table and alert (notify_founder) as it nears the plan limit.
"""

import os
import re
import time
import requests

_ENDPOINT = "https://serpapi.com/search.json"
_CALLS = 0  # in-process counter (cron persists the real monthly total)


def calls_made() -> int:
    """Searches issued by this process since start (for logging/quota guards)."""
    return _CALLS


def search_jobs(query: str, location: str, *, gl: str = "us", hl: str = "en",
                timeout: int = 20) -> list[dict]:
    """
    Query SerpAPI Google Jobs. Returns a normalized list of job dicts:
        {company, title, location, posted_at, via, link}
    Returns [] on any failure (missing key, HTTP error, no results) — never raises.
    `gl` = country code ("us" / "ca"); `hl` = language.
    """
    global _CALLS
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "gl": gl,
        "hl": hl,
        "api_key": api_key,
    }
    try:
        resp = requests.get(_ENDPOINT, params=params, timeout=timeout)
        _CALLS += 1
        if resp.status_code != 200:
            return []
        payload = resp.json()
    except Exception:
        return []
    return _parse_jobs(payload)


def _parse_jobs(payload: dict) -> list[dict]:
    """Pure: normalize a SerpAPI google_jobs payload into our job dicts."""
    out = []
    for j in (payload.get("jobs_results") or []):
        ext = j.get("detected_extensions") or {}
        out.append({
            "company": (j.get("company_name") or "").strip(),
            "title": (j.get("title") or "").strip(),
            "location": (j.get("location") or "").strip(),
            "posted_at": ext.get("posted_at", ""),
            "via": j.get("via", ""),
            "link": j.get("share_link") or j.get("link", ""),
        })
    return out


_REL = re.compile(r"(\d+)\+?\s*(hour|day|week|month)", re.I)


def is_recent(posted_at: str, max_days: int = 30) -> bool:
    """
    Heuristic recency from Google's relative strings ("3 days ago", "today", "2 weeks ago").
    Unknown/empty → True (don't drop a lead just because the date string is missing).
    """
    s = (posted_at or "").lower().strip()
    if not s or "today" in s or "just posted" in s or "hour" in s:
        return True
    m = _REL.search(s)
    if not m:
        return True
    n, unit = int(m.group(1)), m.group(2).lower()
    days = n * {"hour": 0, "day": 1, "week": 7, "month": 30}[unit]
    return days <= max_days


def to_ingest_rows(jobs: list[dict], vertical: str, city: str) -> list[dict]:
    """
    Convert jobs → ingestion rows [{name, city, vertical}], deduped by company name.
    `city` is the searched city (used as the ingestion city; the job's own location is a fallback).
    Skips rows with no company name (e.g. agency-posted listings with a blank employer).
    """
    seen, rows = set(), []
    for j in jobs:
        name = j.get("company") or ""
        key = name.lower()
        if not name or key in seen:
            continue
        seen.add(key)
        rows.append({"name": name, "city": city or j.get("location", ""), "vertical": vertical})
    return rows


# Query → vertical map for the scout (extend as needed).
JOBAD_QUERIES = {
    "dentist": ["dental receptionist", "dental front desk", "dental office receptionist"],
    "doctor":  ["medical receptionist", "medical office receptionist", "clinic receptionist"],
}
