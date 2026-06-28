import os
import time
import requests
import googlemaps

from agents.enrichment import PLACES_DETAIL_FIELDS, fetch_website_html, compute_pain

# Each business type maps to a list of search synonyms.
# find_businesses() cycles through all synonyms and deduplicates by place_id.
BUSINESS_TYPE_QUERIES = {
    "dentist":         ["dental clinic", "dentist", "dental office", "dental practice"],
    "salon":           ["hair salon", "beauty salon", "hair stylist", "hairdresser"],
    "accountant":      ["accounting firm", "accountant", "CPA firm", "tax accountant"],
    "physiotherapist": ["physiotherapy clinic", "physiotherapist", "physical therapy", "physio"],
    "lawyer":          ["law firm", "lawyer", "solicitor", "legal practice"],
}

_PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def find_businesses(business_type: str, city: str, max_results: int = 10,
                    known_place_ids: set = None) -> list[dict]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not set")

    gmaps = googlemaps.Client(key=api_key)
    synonyms = BUSINESS_TYPE_QUERIES.get(business_type, [business_type])

    # known accumulates across ALL synonym passes to prevent duplicate detail calls
    known = set(known_place_ids or [])
    results = []

    for synonym in synonyms:
        if len(results) >= max_results:
            break

        page_token = None
        while len(results) < max_results:
            try:
                if page_token:
                    raw = requests.get(
                        _PLACES_URL,
                        params={"pagetoken": page_token, "key": api_key},
                        timeout=10,
                    ).json()
                    if raw.get("status") != "OK":
                        break
                    response = raw
                else:
                    response = gmaps.places(query=f"{synonym} in {city}")
            except Exception:
                break

            places = response.get("results", [])

            for place in places:
                if len(results) >= max_results:
                    break

                place_id = place.get("place_id")
                if place_id in known:
                    continue

                # Mark seen immediately so subsequent synonyms skip it
                known.add(place_id)

                details = gmaps.place(
                    place_id,
                    fields=PLACES_DETAIL_FIELDS,
                ).get("result", {})

                website = details.get("website", "")
                website_html = fetch_website_html(website, timeout=6)
                pain = compute_pain(details, website_html)

                opening_hours = details.get("opening_hours") or {}
                hours_json = opening_hours.get("weekday_text") or None

                _pain_signal_names = [s["signal"] for s in pain["pain_signals"]]
                if not website or "no_website" in _pain_signal_names:
                    has_online_booking = None
                elif "no_online_booking" in _pain_signal_names:
                    has_online_booking = False
                else:
                    has_online_booking = True

                results.append({
                    "name":               details.get("name", place.get("name")),
                    "address":            details.get("formatted_address", ""),
                    "place_id":           place_id,
                    "phone":              details.get("formatted_phone_number", ""),
                    "website":            website,
                    "rating":             details.get("rating"),
                    "user_ratings_total": details.get("user_ratings_total"),
                    "hours_json":         hours_json,
                    "has_online_booking": has_online_booking,
                    "pain_score":         pain["pain_score"],
                    "pain_signal":        pain["pain_signal"],
                    "pain_finding":       pain["pain_finding"],
                    "pain_signals":       pain["pain_signals"],
                })

            page_token = response.get("next_page_token")
            if not page_token:
                break
            time.sleep(2)

    return results
