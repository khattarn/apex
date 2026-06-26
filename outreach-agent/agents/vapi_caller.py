import logging
import os

import requests

log = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"


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

    if not phone.startswith("+"):
        phone = f"+{phone.lstrip('0')}"

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
