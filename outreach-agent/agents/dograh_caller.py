import logging
import os

import requests

log = logging.getLogger(__name__)

DOGRAH_BASE = "https://app.dograh.com/api/v1/public"
_WORKFLOW_SOPHIE_DEFAULT = "3a93c3b2-7b3c-4b1e-9480-7fe5b9191472"


def _normalize_phone(phone: str, city: str = "") -> str:
    """Convert a local number to E.164 using city context for the country code."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return ""
    if phone.strip().startswith("+"):
        return f"+{digits}"
    from utils.timezone import CITY_TZ
    tz = CITY_TZ.get(city, "")
    if "Australia" in tz:
        if digits.startswith("0"):
            digits = digits[1:]
        return f"+61{digits}"
    elif "Europe/London" in tz:
        if digits.startswith("0"):
            digits = digits[1:]
        return f"+44{digits}"
    elif "America" in tz:
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
    return f"+{digits}"


def place_outbound_call(
    phone: str,
    business_type: str,
    business_name: str,
    lead_id: str = "",
    city: str = "",
    trigger: str = "cold",
) -> dict:
    """
    Trigger a Dograh outbound call via Sophie's workflow.
    Returns the Dograh response dict which contains workflow_run_id.
    """
    api_key = os.getenv("DOGRAH_API_KEY", "")
    if not api_key:
        raise RuntimeError("DOGRAH_API_KEY must be set")

    workflow_uuid = os.getenv("DOGRAH_WORKFLOW_UUID_SOPHIE", _WORKFLOW_SOPHIE_DEFAULT)

    cleaned = _normalize_phone(phone, city)
    if not cleaned or cleaned in ("+", ""):
        raise RuntimeError(f"Could not normalise phone '{phone}'")

    india_telephony_id   = os.getenv("DOGRAH_INDIA_TELEPHONY_CONFIG_ID", "")   # 477 — Vobiz +91
    default_telephony_id = os.getenv("DOGRAH_DEFAULT_TELEPHONY_CONFIG_ID", "") # 478 — Twilio AU/US

    if cleaned.startswith("+91") and india_telephony_id:
        telephony_id = india_telephony_id
    elif default_telephony_id:
        telephony_id = default_telephony_id
    else:
        telephony_id = None

    # Build initial_context — Sophie can reference these via {{initial_context.field}}
    initial_context: dict = {
        "practice_name": business_name,
        "practice_type": business_type,
        "contact_name": business_name,
        "city": city,
        "trigger": trigger,
    }
    if lead_id:
        initial_context["lead_id"] = lead_id

    # Enrich with per-vertical copy (opener / insight / pain_question from copy.yaml)
    try:
        from agents.voice_outreach import _get_script
        script = _get_script(business_type.lower())
        if script.get("firstMessage"):
            initial_context["opener"] = script["firstMessage"]
        if script.get("insight"):
            initial_context["insight"] = script["insight"]
        if script.get("pain_question"):
            initial_context["pain_question"] = script["pain_question"]
    except Exception:
        pass

    payload: dict = {
        "phone_number": cleaned,
        "initial_context": initial_context,
    }
    if telephony_id:
        payload["telephony_configuration_id"] = telephony_id

    resp = requests.post(
        f"{DOGRAH_BASE}/agent/workflow/{workflow_uuid}",
        json=payload,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(f"Dograh API error {resp.status_code}: {resp.text}")

    log.info(
        "Dograh call triggered: lead=%s phone=%s trigger=%s",
        lead_id or "?",
        cleaned,
        trigger,
    )
    return resp.json()
