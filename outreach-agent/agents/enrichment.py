"""
enrichment.py — Pre-call qualification (pain signals + pain_score) for Apex prospecting.

Drop into outreach-agent/agents/ (or outreach-agent/). Pure-ish functions; no DB coupling.
Called by the prospecting cron right after each new lead is saved.

Computes the signals derivable at prospect time:
  - new_business        (Google Places: review count + earliest-review recency)
  - review_reachability (Google Places: ~5 review texts, regex)
  - review_booking / scheduling / frontdesk (same reviews — feed the score)
  - no_online_booking   (the business website: fetch + booking-widget scan)
  - no_website          (Google Places: website empty)

Left to other parts of the system (not here):
  - after_hours_voicemail  -> telephony/AMD on the outreach call (writes back later)
  - job_ad_frontdesk       -> jobs search API (SerpAPI), v2

Places Detail fields the prospector must request so this module has its inputs:
    name, formatted_address, formatted_phone_number, website, place_id,
    user_ratings_total, rating, reviews, opening_hours, business_status
"""

import re
import time
import requests
from datetime import datetime, timezone

# ── Weights (match change9-painscore-spec.md; starting hypotheses) ──────────────
W_NEW_BUSINESS = 25
W_REACHABILITY = 20
W_NO_BOOKING   = 20
W_BOOKING_PAIN = 15
W_SCHEDULING   = 10
W_FRONTDESK    = 10
W_NO_WEBSITE   = 10

# ── Review-mining patterns ──────────────────────────────────────────────────────
_REACHABILITY = re.compile(
    r"couldn'?t get through|can'?t get through|no ?one (answers|answered|picks? up|picked up)"
    r"|nobody (answers|answered)|never answer(s|ed)? the phone|goes (straight )?to voicemail"
    r"|left (a|several|multiple|two|three)? ?messages?|never (call|called|calling) (me |us )?back"
    r"|impossible to reach|on hold (forever|for ages|for ever)|can never reach", re.I)
_BOOKING_PAIN = re.compile(
    r"hard to (book|get an appointment|get an appt)|took (weeks|months|forever|ages) to get"
    r"|can'?t get an appointment|booking (is|was) a (nightmare|hassle|pain)|couldn'?t book"
    r"|no availability|impossible to book", re.I)
_SCHEDULING = re.compile(
    r"no record of (my|the) appointment|lost my appointment|double[- ]?booked|forgot my appointment"
    r"|cancel(led|ed) (on me|last minute|my appointment)|overbooked|kept (me )?waiting|long wait", re.I)
_FRONTDESK = re.compile(
    r"front desk (was )?(rude|unhelpful|overwhelmed|a mess)|receptionist (was )?(rude|unhelpful|gone|new)"
    r"|disorgani[sz]ed|chaotic|under ?staffed|short[- ]staffed", re.I)

_REVIEW_PATTERNS = [
    ("reachability", _REACHABILITY, W_REACHABILITY),
    ("booking",      _BOOKING_PAIN, W_BOOKING_PAIN),
    ("scheduling",   _SCHEDULING,   W_SCHEDULING),
    ("frontdesk",    _FRONTDESK,    W_FRONTDESK),
]

# ── Online-booking widget signatures (no_online_booking) ────────────────────────
_BOOKING_SIGNATURES = [
    # generic
    "book online", "book now", "book an appointment", "request an appointment",
    "request appointment", "schedule online", "schedule an appointment", "online booking",
    "make an appointment",
    # scheduler vendors
    "calendly.com", "cal.com", "nexhealth", "squareup.com/appointments", "square.site",
    "acuityscheduling", "zocdoc", "jane.app", "simplepractice", "setmore", "youcanbook.me",
    "vagaro.com", "fresha.com", "booksy.com", "schedulicity", "mindbodyonline", "dentrixascend",
    "localmed", "flexbook", "engagebay", "appointmentplus",
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ApexBot/1.0)"}
_TWELVE_MONTHS = 365 * 24 * 3600


def fetch_website_html(url: str, timeout: int = 6) -> str | None:
    """Fetch a business website's HTML (home + /contact). Best-effort; None on failure."""
    if not url:
        return None
    base = url.rstrip("/")
    html_parts = []
    for u in (base, base + "/contact"):
        try:
            r = requests.get(u, headers=_HEADERS, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                html_parts.append(r.text)
        except Exception:
            continue
    return "\n".join(html_parts) if html_parts else None


def detect_online_booking(html: str | None) -> tuple[bool | None, str | None]:
    """
    Returns (has_booking, signature). has_booking is None when unknown
    (no html fetched) so the caller can avoid a false 'no booking' signal.
    """
    if not html:
        return None, None
    low = html.lower()
    for sig in _BOOKING_SIGNATURES:
        if sig in low:
            return True, sig
    return False, None


def _snippet(text: str, m: re.Match, width: int = 60) -> str:
    s = max(0, m.start() - width // 2)
    e = min(len(text), m.end() + width // 2)
    return text[s:e].strip().replace("\n", " ")


def mine_reviews(reviews: list[dict]) -> list[dict]:
    """reviews: Google Places review objects [{text, time, ...}]. Returns matched hits."""
    hits = []
    for rv in reviews or []:
        text = rv.get("text") or ""
        for category, pat, weight in _REVIEW_PATTERNS:
            m = pat.search(text)
            if m:
                hits.append({
                    "category": category,
                    "weight": weight,
                    "quote": _snippet(text, m),
                    "time": rv.get("time"),
                })
    return hits


def detect_new_business(user_ratings_total, reviews: list[dict]) -> tuple[bool, str | None]:
    """Low review count + recent earliest review => likely newly opened."""
    if user_ratings_total is None:
        return False, None
    if user_ratings_total < 5:
        return True, f"only {user_ratings_total} Google reviews so far"
    if user_ratings_total < 15:
        times = [rv.get("time") for rv in (reviews or []) if rv.get("time")]
        if times and (datetime.now(timezone.utc).timestamp() - min(times)) < _TWELVE_MONTHS:
            return True, f"{user_ratings_total} reviews, first one within the last year"
    return False, None


def compute_pain(place_details: dict, website_html: str | None) -> dict:
    """
    Returns {pain_score, pain_signal, pain_finding, pain_signals}.
    pain_signal is one of the canonical opener keys (new_business | review_reachability |
    no_online_booking) or None. Telephony/job-ad signals are added elsewhere.
    """
    signals: list[dict] = []
    score = 0

    total   = place_details.get("user_ratings_total")
    reviews = place_details.get("reviews") or []
    website = place_details.get("website") or ""

    # 1) new_business
    is_new, new_detail = detect_new_business(total, reviews)
    if is_new:
        score += W_NEW_BUSINESS
        signals.append({"signal": "new_business", "weight": W_NEW_BUSINESS, "detail": new_detail})

    # 2) review mining
    review_hits = mine_reviews(reviews)
    reachability_hit = next((h for h in review_hits if h["category"] == "reachability"), None)
    for h in review_hits:
        score += h["weight"]
        signals.append({"signal": f"review_{h['category']}", "weight": h["weight"], "detail": h["quote"]})

    # 3) online booking
    has_booking, sig = detect_online_booking(website_html)
    if has_booking is False:
        score += W_NO_BOOKING
        signals.append({"signal": "no_online_booking", "weight": W_NO_BOOKING,
                        "detail": "no booking widget found on site — patients book by calling"})

    # 4) no website at all
    if not website:
        score += W_NO_WEBSITE
        signals.append({"signal": "no_website", "weight": W_NO_WEBSITE, "detail": "no website listed"})

    # Choose the opener signal + finding (priority: new_business > reachability > no_online_booking)
    pain_signal, pain_finding = None, None
    if is_new:
        pain_signal, pain_finding = "new_business", new_detail
    elif reachability_hit:
        pain_signal = "review_reachability"
        pain_finding = "a review mentions trouble getting through on the phone"
    elif has_booking is False:
        pain_signal = "no_online_booking"
        pain_finding = "patients can only book by calling — no online booking on the site"

    return {
        "pain_score": min(100, score),
        "pain_signal": pain_signal,
        "pain_finding": pain_finding,
        "pain_signals": signals,
    }


# Field list the prospector must pass to Places Details so this module has inputs.
PLACES_DETAIL_FIELDS = [
    "name", "formatted_address", "formatted_phone_number", "website", "place_id",
    "user_ratings_total", "rating", "reviews", "opening_hours", "business_status",
]
