import logging
import os

import requests

log = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"


def _to_e164(phone: str, address: str = "") -> str:
    """Normalize any phone format to E.164. Handles (xxx) xxx-xxxx, +1xxx, bare 10-digit, etc.

    A bare 10-digit number is ambiguous — NANP local format (504) 482-1000 and
    Australian local format (07) 5606 0211 both come out to 10 digits once
    punctuation is stripped. Blindly prefixing +1 silently mis-dials every AU
    lead (e.g. "0756060211" -> "+10756060211", which Vapi rejects as invalid
    E.164). Use the lead's address, when available, to disambiguate.
    """
    digits = "".join(c for c in phone if c.isdigit())
    if phone.strip().startswith("+"):
        return f"+{digits}"
    is_au = "australia" in (address or "").lower()
    if len(digits) == 10:
        if is_au:
            local = digits[1:] if digits.startswith("0") else digits  # drop AU trunk 0
            return f"+61{local}"
        return f"+1{digits}"   # bare NANP: (504) 482-1000
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) >= 11 and not digits.startswith("1"):
        return f"+{digits}"        # international without +
    return f"+{digits}"


def _headers() -> dict:
    api_key = os.getenv("VAPI_API_KEY", "")
    if not api_key:
        raise RuntimeError("VAPI_API_KEY must be set")
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def place_emma_call(
    phone: str,
    call_type: str,
    patient_name: str,
    appointment_time: str = "",
) -> dict:
    """
    Trigger Emma (dental patient care) via Vapi outbound call.
    call_type: appointment_reminder | six_month_recall | post_treatment_checkin | no_show_followup
    Caller ID shown to patient: +12895141951 (Bright Smile Dental Ontario)
    """
    assistant_id   = os.getenv("VAPI_EMMA_ASSISTANT_ID",   "82e848d2-a520-499a-ac32-40d103e41efd")
    phone_number_id = os.getenv("VAPI_DENTAL_OUTBOUND_PHONE_ID", "9bff5610-ae74-4921-ad83-55d108a2b0ee")

    phone = _to_e164(phone)

    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customer": {"number": phone},
        "assistantOverrides": {
            "variableValues": {
                "call_type":        call_type,
                "patient_name":     patient_name,
                "appointment_time": appointment_time,
            }
        },
    }

    resp = requests.post(
        f"{VAPI_BASE}/call",
        json=payload,
        headers=_headers(),
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(f"Vapi API error {resp.status_code}: {resp.text}")

    data = resp.json()
    log.info("Vapi Emma call triggered: phone=%s call_type=%s call_id=%s", phone, call_type, data.get("id"))
    return data


def place_sophie_call(
    phone: str,
    business_name: str,
    business_type: str,
    city: str = "",
    opener: str = "",
    insight: str = "",
    pain_question: str = "",
    lead_id: str = "",
    phone_number_id: str = "",
    pain_signal: str = "",
    pain_finding: str = "",
    pricing_line: str = "Starter: $49/month · Growth: $99/month · Pro: $180/month · Setup: $180 (waived until 29 Jul 2026)",
    address: str = "",
) -> dict:
    """
    Trigger Sophie (PracticeDesk outbound sales) via Vapi.
    Pass phone_number_id to override the default number (e.g. use CA number for Canadian leads).
    Pass pricing_line with the market-correct currency string — CA callers get CAD prices.
    Default caller ID: +13129408233 (Vapi free number, US/AU).
    CA caller ID: +15872090343 (SignalWire 587 Alberta).
    """
    from database.client import get_setting
    if str(get_setting("sophie_calls_paused") or "").lower() == "true":
        raise RuntimeError("Sophie outbound calls are paused (settings.sophie_calls_paused=true)")

    assistant_id    = os.getenv("VAPI_SOPHIE_ASSISTANT_ID",   "bfecad5e-dce4-469f-8570-d44efc49de15")
    if not phone_number_id:
        phone_number_id = os.getenv("VAPI_PLATFORM_PHONE_ID", "50d7061b-ac77-4a4f-b2d5-7430df39b9d5")

    phone = _to_e164(phone, address)

    server_url = os.getenv(
        "RAILWAY_PUBLIC_DOMAIN",
        "https://serene-passion-production-cd82.up.railway.app",
    )
    if not server_url.startswith("http"):
        server_url = f"https://{server_url}"

    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customer": {"number": phone},
        "metadata": {"lead_id": lead_id},
        "maxDurationSeconds": 300,
        "assistantOverrides": {
            "server": {"url": f"{server_url}/api/webhooks/vapi"},
            # "transcript" (content-based) catches both classic voicemail greetings and
            # scripted AI/automated answering systems — "audio" (beep-only) would miss
            # the latter entirely, since there's no beep to detect (see the Adelaide
            # Family Dental "Artorial AI" test call, 2026-07-10).
            "voicemailDetection": {
                "provider": "vapi",
                "type": "transcript",
            },
            "endCallPhrases": ["goodbye", "have a great day", "take care"],
            "variableValues": {
                "practice_name":  business_name,
                "practice_type":  business_type,
                "city":           city,
                "opener":         opener,
                "insight":        insight,
                "pain_question":  pain_question,
                "pain_signal":    pain_signal,
                "pain_finding":   pain_finding,
                "pricing_line":   pricing_line,
            },
        },
    }

    resp = requests.post(
        f"{VAPI_BASE}/call",
        json=payload,
        headers=_headers(),
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(f"Vapi API error {resp.status_code}: {resp.text}")

    data = resp.json()
    log.info("Vapi Sophie call triggered: lead=%s phone=%s call_id=%s", lead_id or "?", phone, data.get("id"))
    return data
