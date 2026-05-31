import os
import googlemaps

BUSINESS_TYPE_QUERIES = {
    "dentist": "dental clinic",
    "salon": "hair salon",
    "accountant": "accounting firm",
    "physiotherapist": "physiotherapy clinic",
    "lawyer": "law firm",
}


def find_businesses(business_type: str, city: str, max_results: int = 10) -> list[dict]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not set")

    gmaps = googlemaps.Client(key=api_key)
    query = BUSINESS_TYPE_QUERIES.get(business_type, business_type)
    results = []
    page_token = None

    while len(results) < max_results:
        kwargs = {"query": f"{query} in {city}"}
        if page_token:
            kwargs["page_token"] = page_token

        response = gmaps.places(**kwargs)
        places = response.get("results", [])

        for place in places:
            if len(results) >= max_results:
                break

            place_id = place.get("place_id")
            details = gmaps.place(
                place_id,
                fields=["name", "formatted_address", "formatted_phone_number", "website", "place_id"],
            ).get("result", {})

            results.append({
                "name": details.get("name", place.get("name")),
                "address": details.get("formatted_address", ""),
                "place_id": place_id,
                "phone": details.get("formatted_phone_number", ""),
                "website": details.get("website", ""),
            })

        page_token = response.get("next_page_token")
        if not page_token:
            break

    return results
