"""
vapi_bridge.py — Bridge call via Vapi + Vobiz India number.

Flow:
1. Vapi calls founder's mobile (+919262171423 as caller ID)
2. Founder answers → Vapi says "Connecting you to your lead now."
3. Vapi immediately executes transferCall → calls destination
4. Vobiz bridges founder and destination
5. Both parties talk directly
"""

import logging
import os
import threading
import time
import uuid

import requests

log = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"
VAPI_INDIA_PHONE_ID = "55328e0f-b12b-4108-a3b2-ee282aa7bed9"  # +919262171423 via Vobiz

_bridges: dict[str, dict] = {}


def _vapi_headers() -> dict:
    return {"Authorization": f"Bearer {os.getenv('VAPI_API_KEY', '')}"}


def start_bridge(destination: str) -> str:
    bridge_id = uuid.uuid4().hex[:8]
    founder = os.getenv("FOUNDER_WHATSAPP_NUMBER", "+919810982019")

    # Ensure E.164 with + for Vapi
    dest = destination if destination.startswith("+") else f"+{destination}"

    status: dict = {
        "state": "starting",
        "destination": dest,
        "founder": founder,
        "started_at": time.time(),
    }
    _bridges[bridge_id] = status

    def _run():
        try:
            status["state"] = "calling_founder"

            payload = {
                "phoneNumberId": VAPI_INDIA_PHONE_ID,
                "customer": {"number": founder},
                "assistant": {
                    "firstMessage": "Connecting you to your lead now. Please hold.",
                    "model": {
                        "provider": "anthropic",
                        "model": "claude-haiku-4-5-20251001",
                        "messages": [{
                            "role": "system",
                            "content": (
                                f"You are a call transfer assistant. "
                                f"Your only job: immediately call the transferCall function "
                                f"to transfer this call to {dest}. "
                                f"Do not say anything. Do not wait. Transfer immediately."
                            )
                        }],
                        "tools": [{
                            "type": "transferCall",
                            "destinations": [{
                                "type": "number",
                                "number": dest,
                                "message": "Connecting now."
                            }]
                        }]
                    },
                    "voice": {"provider": "azure", "voiceId": "en-IN-NeerjaNeural"},
                    "endCallFunctionEnabled": False,
                    "backgroundSound": "off",
                }
            }

            resp = requests.post(
                f"{VAPI_BASE}/call/phone",
                json=payload,
                headers=_vapi_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            call = resp.json()
            vapi_call_id = call.get("id")
            status["vapi_call_id"] = vapi_call_id
            log.info("Vapi call started: %s", vapi_call_id)

            # Poll until call ends
            deadline = time.time() + 120
            while time.time() < deadline:
                time.sleep(3)
                try:
                    info = requests.get(
                        f"{VAPI_BASE}/call/{vapi_call_id}",
                        headers=_vapi_headers(),
                        timeout=10,
                    ).json()

                    vapi_status = info.get("status", "")
                    ended_reason = info.get("endedReason", "")
                    log.debug("Vapi status: %s ended: %s", vapi_status, ended_reason)

                    if vapi_status in ("queued", "ringing"):
                        status["state"] = "calling_founder"
                    elif vapi_status == "in-progress":
                        status["state"] = "answered"
                    elif vapi_status == "ended":
                        if ended_reason in ("customer-did-not-answer", "no-answer"):
                            status["state"] = "no_answer"
                            status["error"] = "Your mobile was not answered"
                        elif "transfer" in ended_reason:
                            status["state"] = "connected"
                        else:
                            # Call ended after being answered — transfer likely went through
                            status["state"] = "connected"
                        break

                except Exception as e:
                    log.warning("Poll error: %s", e)

        except Exception as exc:
            log.exception("vapi_bridge error: %s", exc)
            status["state"] = "error"
            status["error"] = str(exc)

    threading.Thread(target=_run, daemon=True).start()
    return bridge_id


def get_bridge_status(bridge_id: str) -> dict:
    return _bridges.get(bridge_id, {"state": "not_found"})
