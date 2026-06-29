"""
cal_booking.py — Cal.com integration for Sophie's automatic demo booking.

Required env vars:
  CAL_API_KEY        — from cal.com/settings/developer/api-keys
  CAL_EVENT_TYPE_ID  — integer ID of the "PracticeDesk Demo" event type
                       (optional: auto-fetched if not set, but set it to avoid an API call)

When Sophie's book_demo tool fires:
  1. Parse the prospect's preferred time (natural language → datetime)
  2. Fetch available Cal.com slots around that time
  3. Book the nearest available slot
  4. Send WhatsApp confirmation to the prospect's phone
"""

import os
import re
import logging
import requests
from datetime import datetime, timedelta
import pytz

log = logging.getLogger(__name__)

CAL_BASE = "https://api.cal.com/v2"
CAL_API_VERSION = "2024-06-14"   # version that supports list response format
CAL_BOOKING_URL = "https://cal.com/neeraj-khattar-3zszap/practicedesk-demo"


def _cal_headers() -> dict:
    version = os.getenv("CAL_API_VERSION", CAL_API_VERSION)
    return {
        "Authorization": f"Bearer {os.getenv('CAL_API_KEY', '')}",
        "cal-api-version": version,
        "Content-Type": "application/json",
    }


def get_event_type_id() -> int | None:
    """Return CAL_EVENT_TYPE_ID from env, or fetch the first event type from Cal.com."""
    env_id = os.getenv("CAL_EVENT_TYPE_ID", "")
    if env_id.isdigit():
        return int(env_id)

    resp = requests.get(f"{CAL_BASE}/event-types", headers=_cal_headers(), timeout=10)
    if not resp.ok:
        log.error("Cal.com event-types fetch failed: %s", resp.text)
        return None

    data = resp.json().get("data", {})
    # API returns either a list or a nested {eventTypeGroups: [...]}
    if isinstance(data, list):
        event_types = data
    else:
        groups = data.get("eventTypeGroups", [])
        event_types = groups[0].get("eventTypes", []) if groups else []

    return event_types[0]["id"] if event_types else None


def parse_preferred_time(text: str, tz_name: str = "America/Toronto") -> datetime:
    """
    Convert natural language like "Friday at 2pm" or "Monday afternoon"
    to the next occurrence of that day/time in the given timezone.
    Defaults to next weekday morning if no useful info is found.
    """
    DAYS    = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}
    PERIODS = {"morning": 10, "noon": 12, "lunch": 12, "afternoon": 14, "evening": 17}

    text_lower = text.lower()
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)

    # Specific time e.g. "2pm", "3:30pm"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text_lower)
    if time_match:
        h = int(time_match.group(1))
        m = int(time_match.group(2) or 0)
        if time_match.group(3) == 'pm' and h != 12:
            h += 12
        elif time_match.group(3) == 'am' and h == 12:
            h = 0
        target_hour, target_min = h, m
    else:
        target_hour = next((h for p, h in PERIODS.items() if p in text_lower), 10)
        target_min = 0

    # Target weekday
    target_day = next((num for name, num in DAYS.items() if name in text_lower), None)

    if target_day is not None:
        days_until = (target_day - now.weekday()) % 7
        if days_until == 0 and (now.hour > target_hour or (now.hour == target_hour and now.minute >= target_min)):
            days_until = 7
        target_dt = now + timedelta(days=days_until)
    else:
        # Default: tomorrow, skipping weekends
        target_dt = now + timedelta(days=1)
        while target_dt.weekday() >= 5:
            target_dt += timedelta(days=1)

    return target_dt.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)


def get_available_slots(event_type_id: int, around: datetime, tz_name: str, window_days: int = 5) -> list[str]:
    """Return sorted list of available slot ISO strings within window_days of `around`."""
    start = around.isoformat()
    end   = (around + timedelta(days=window_days)).isoformat()

    resp = requests.get(
        f"{CAL_BASE}/slots/available",
        params={"eventTypeId": event_type_id, "startTime": start, "endTime": end, "timeZone": tz_name},
        headers=_cal_headers(),
        timeout=10,
    )
    if not resp.ok:
        log.error("Cal.com slots error: %s", resp.text)
        return []

    # API returns {"data": {"slots": {"2026-06-08": [{"time":"..."}, ...], ...}}}
    payload = resp.json().get("data", {})
    slots_by_date = payload.get("slots", payload)   # handle both v1 and v2 response shapes
    slots: list[str] = []
    for date_slots in slots_by_date.values():
        if isinstance(date_slots, list):
            for slot in date_slots:
                t = slot.get("time", "") if isinstance(slot, dict) else slot
                if t:
                    slots.append(t)
    return sorted(slots)


def _nearest_slot(slots: list[str], target: datetime) -> str | None:
    """Return the first available slot at or after `target`."""
    target_iso = target.isoformat()
    after = [s for s in slots if s >= target_iso]
    return after[0] if after else (slots[-1] if slots else None)


def book_demo(
    attendee_name: str,
    attendee_email: str,
    preferred_time: str,
    attendee_phone: str = "",
    attendee_tz: str = "America/Toronto",
) -> dict:
    """
    Book a PracticeDesk demo on Cal.com.
    Returns: {ok: bool, start_time: str, booking_uid: str, meeting_url: str, error: str}
    """
    if not os.getenv("CAL_API_KEY"):
        return {"ok": False, "error": "CAL_API_KEY not set"}

    event_type_id = get_event_type_id()
    if not event_type_id:
        return {"ok": False, "error": "Cal.com event type not found"}

    target_dt  = parse_preferred_time(preferred_time, attendee_tz)
    slots      = get_available_slots(event_type_id, target_dt, attendee_tz)
    chosen     = _nearest_slot(slots, target_dt)

    if not chosen:
        return {"ok": False, "error": "No available slots in the next 5 days"}

    resp = requests.post(
        f"{CAL_BASE}/bookings",
        json={
            "eventTypeId": event_type_id,
            "start": chosen,
            "attendee": {
                "name": attendee_name,
                "email": attendee_email,
                "timeZone": attendee_tz,
                "phoneNumber": attendee_phone,
            },
        },
        headers=_cal_headers(),
        timeout=15,
    )

    if not resp.ok:
        log.error("Cal.com booking POST failed: %s", resp.text)
        return {"ok": False, "error": f"Booking API error {resp.status_code}"}

    booking = resp.json().get("data", {})
    uid = booking.get("uid", "")
    fallback_url = os.getenv("CAL_BOOKING_URL", CAL_BOOKING_URL)
    return {
        "ok": True,
        "start_time": chosen,
        "booking_uid": uid,
        "meeting_url": booking.get("meetingUrl") or f"https://cal.com/booking/{uid}" or fallback_url,
    }


def send_booking_whatsapp(phone: str, name: str, friendly_time: str) -> None:
    """Send a WhatsApp confirmation message to the prospect after booking."""
    if not phone:
        return
    try:
        wa_token  = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        phone_id  = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", "")
        if not wa_token or not phone_id:
            return

        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned

        msg = (
            f"Hi {name}, your PracticeDesk demo is confirmed for {friendly_time}. "
            f"You'll receive a calendar invite shortly. "
            f"Looking forward to connecting! — Henry, PracticeDesk"
        )
        requests.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": cleaned,
                "type": "text",
                "text": {"body": msg},
            },
            headers={"Authorization": f"Bearer {wa_token}"},
            timeout=10,
        )
    except Exception as exc:
        log.warning("Booking WA send failed: %s", exc)
