import os
import pathlib
import requests

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

LOGO_URL    = "https://mpex.netlify.app/logo.png"
YOUTUBE_URL = "https://www.youtube.com/watch?v=zHVLE5ek7jY"
HOME_URL    = "https://practicedesk.netlify.app/"
HENRY_PHONE = "+13129408233"

_V2_BUTTONS = [
    {"type": "URL",          "text": "Start using for free",  "url": HOME_URL},
    {"type": "URL",          "text": "Watch Intro Video",     "url": YOUTUBE_URL},
    {"type": "PHONE_NUMBER", "text": "Call us with questions", "phone_number": HENRY_PHONE},
    {"type": "QUICK_REPLY",  "text": "Stop"},
]

TEMPLATES = {
    # ── v1 (approved, live) ──────────────────────────────────────────────────
    "apex_outreach_salon_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Came across {{2}} on Google — looks like a great salon!\n\n"
                    "Quick question: are you still managing bookings and client reminders manually on WhatsApp?\n\n"
                    "We built PracticeDesk for salons — it handles appointment bookings, sends automatic reminders, "
                    "and follows up after each visit. Most salons see 30% fewer no-shows in the first month.\n\n"
                    "Would a free 15-min demo be worth your time?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Sarah", "Glow Studio"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Yes, show me"},
                    {"type": "QUICK_REPLY", "text": "Not interested"},
                ],
            },
        ],
    },
    "apex_outreach_dentist_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi Dr. {{1}},\n\n"
                    "I found {{2}} on Google Maps. Impressive reviews!\n\n"
                    "Are missed appointments or manual patient follow-ups eating into your day?\n\n"
                    "PracticeDesk is a WhatsApp AI assistant built for dental clinics — it books appointments, "
                    "sends reminders, answers patient queries, and follows up post-treatment. No extra staff needed.\n\n"
                    "Happy to show you a quick demo — free, no commitment. Worth 15 minutes?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Sharma", "Smile Dental Clinic"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Book a demo"},
                    {"type": "QUICK_REPLY", "text": "Not now"},
                ],
            },
        ],
    },
    "apex_outreach_doctor_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi Dr. {{1}},\n\n"
                    "I came across {{2}} while researching clinics in your area.\n\n"
                    "Managing appointment queues, patient reminders, and follow-up calls manually takes hours. "
                    "Clinics lose 20-25% of appointments to no-shows every week.\n\n"
                    "PracticeDesk gives your clinic a WhatsApp AI receptionist — it books slots, confirms appointments, "
                    "answers common queries, and follows up automatically.\n\n"
                    "Would a free demo make sense for you?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Patel", "City Health Clinic"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Yes, interested"},
                    {"type": "QUICK_REPLY", "text": "Not for us"},
                ],
            },
        ],
    },
    "apex_outreach_physio_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Found {{2}} on Google — great to see physio practices growing in your area.\n\n"
                    "Do you spend time chasing patients for appointment confirmations or rebooking "
                    "follow-up sessions manually?\n\n"
                    "PracticeDesk automates all of that on WhatsApp — appointment reminders, rebooking prompts "
                    "after treatment courses, and patient Q&A. Set it once, runs itself.\n\n"
                    "Free demo — 15 minutes. Interested?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Rahul", "ActiveLife Physiotherapy"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Show me how"},
                    {"type": "QUICK_REPLY", "text": "No thanks"},
                ],
            },
        ],
    },
    "apex_outreach_accountant_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "I came across {{2}} on Google while looking at accounting firms in your area.\n\n"
                    "Do your clients still call or WhatsApp you directly for appointments, document reminders, "
                    "or status updates?\n\n"
                    "PracticeDesk handles all of that automatically — appointment booking, document nudges, "
                    "and follow-ups via WhatsApp. Keeps clients happy, keeps your team focused.\n\n"
                    "Worth a free 15-min walkthrough?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Anil", "Sharma & Associates"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Book demo"},
                    {"type": "QUICK_REPLY", "text": "Not interested"},
                ],
            },
        ],
    },
    "apex_outreach_lawyer_v1": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Found {{2}} on Google — looks like a busy practice.\n\n"
                    "Are clients still booking consultations by calling in, or are follow-ups "
                    "falling through the cracks?\n\n"
                    "PracticeDesk gives your firm a WhatsApp AI assistant — it handles consultation bookings, "
                    "sends reminders, and follows up with clients automatically. Keeps your pipeline moving "
                    "without adding admin.\n\n"
                    "Free 15-min demo — no strings. Interested?\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Mehta", "Mehta & Partners Law Firm"]]},
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "Yes, let's talk"},
                    {"type": "QUICK_REPLY", "text": "Not now"},
                ],
            },
        ],
    },

    # ── v2 (image header + CTA buttons) ──────────────────────────────────────
    "apex_outreach_dentist_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi Dr. {{1}},\n\n"
                    "I found {{2}} on Google Maps — impressive reviews!\n\n"
                    "Are missed appointments or manual patient follow-ups eating into your day?\n\n"
                    "PracticeDesk is a WhatsApp AI assistant built for dental clinics — it books appointments, "
                    "sends reminders, answers patient queries, and follows up post-treatment. No extra staff needed.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Sharma", "Smile Dental Clinic"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
    "apex_outreach_salon_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Came across {{2}} on Google — looks like a great salon!\n\n"
                    "Still managing bookings and client reminders manually on WhatsApp?\n\n"
                    "PracticeDesk automates appointment bookings, sends reminders, and follows up after each visit. "
                    "Most salons see 30% fewer no-shows in the first month.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Sarah", "Glow Studio"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
    "apex_outreach_doctor_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi Dr. {{1}},\n\n"
                    "I came across {{2}} while researching clinics in your area.\n\n"
                    "Clinics lose 20–25% of appointments to no-shows every week. Managing queues, "
                    "reminders, and follow-up calls manually takes hours your team doesn't have.\n\n"
                    "PracticeDesk gives your clinic a WhatsApp AI receptionist — books slots, confirms appointments, "
                    "answers queries, and follows up automatically.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Patel", "City Health Clinic"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
    "apex_outreach_physio_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Found {{2}} on Google — great to see physio practices growing in your area.\n\n"
                    "Do you spend time chasing patients for appointment confirmations or rebooking "
                    "follow-up sessions manually?\n\n"
                    "PracticeDesk automates all of that on WhatsApp — appointment reminders, rebooking prompts "
                    "after treatment courses, and patient Q&A. Set it once, runs itself.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Rahul", "ActiveLife Physiotherapy"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
    "apex_outreach_accountant_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "I came across {{2}} on Google while looking at accounting firms in your area.\n\n"
                    "Do your clients still call or message you directly for appointments, document reminders, "
                    "or status updates?\n\n"
                    "PracticeDesk handles all of that automatically — appointment booking, document nudges, "
                    "and follow-ups via WhatsApp. Keeps clients happy, keeps your team focused.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Anil", "Sharma & Associates"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
    "apex_outreach_lawyer_v2": {
        "language": "en",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
            },
            {
                "type": "BODY",
                "text": (
                    "Hi {{1}},\n\n"
                    "Found {{2}} on Google — looks like a busy practice.\n\n"
                    "Are clients booking consultations by calling in, or are follow-ups "
                    "falling through the cracks?\n\n"
                    "PracticeDesk gives your firm a WhatsApp AI assistant — it handles consultation bookings, "
                    "sends reminders, and follows up with clients automatically. Keeps your pipeline moving "
                    "without adding admin.\n\n"
                    "— Henry, PracticeDesk"
                ),
                "example": {"body_text": [["Mehta", "Mehta & Partners Law Firm"]]},
            },
            {"type": "BUTTONS", "buttons": _V2_BUTTONS},
        ],
    },
}

# v3 = v2 components + Stop quick-reply button (created after 24h edit limit hit on v2)
# Note: editing v3 to reorder buttons stripped the IMAGE header — templates are header-less.
for _k in [k for k in list(TEMPLATES) if k.endswith("_v2")]:
    TEMPLATES[_k.replace("_v2", "_v3")] = TEMPLATES[_k]

# v4 = final canonical version: logo header + correct button order (homepage first, YouTube second)
# _V2_BUTTONS already has the correct order. v4 entries are identical to v3 definitions.
for _k in [k for k in list(TEMPLATES) if k.endswith("_v2")]:
    TEMPLATES[_k.replace("_v2", "_v4")] = TEMPLATES[_k]

TEMPLATE_DISPLAY_NAMES = {
    "apex_outreach_salon_v1":      "Salon (v1)",
    "apex_outreach_dentist_v1":    "Dentist (v1)",
    "apex_outreach_doctor_v1":     "Doctor / GP (v1)",
    "apex_outreach_physio_v1":     "Physiotherapist (v1)",
    "apex_outreach_accountant_v1": "Accountant (v1)",
    "apex_outreach_lawyer_v1":     "Lawyer (v1)",
    "apex_outreach_salon_v2":      "Salon (v2 + logo)",
    "apex_outreach_dentist_v2":    "Dentist (v2 + logo)",
    "apex_outreach_doctor_v2":     "Doctor / GP (v2 + logo)",
    "apex_outreach_physio_v2":     "Physiotherapist (v2 + logo)",
    "apex_outreach_accountant_v2": "Accountant (v2 + logo)",
    "apex_outreach_lawyer_v2":     "Lawyer (v2 + logo)",
    "apex_outreach_salon_v3":      "Salon (v3 + logo + stop)",
    "apex_outreach_dentist_v3":    "Dentist (v3 + logo + stop)",
    "apex_outreach_doctor_v3":     "Doctor / GP (v3 + logo + stop)",
    "apex_outreach_physio_v3":     "Physiotherapist (v3 + logo + stop)",
    "apex_outreach_accountant_v3": "Accountant (v3 + logo + stop)",
    "apex_outreach_lawyer_v3":     "Lawyer (v3 + logo + stop)",
}

_V2_NAMES = {k for k in TEMPLATES if k.endswith("_v2")}
_V3_NAMES = {k for k in TEMPLATES if k.endswith("_v3")}
_V4_NAMES = {k for k in TEMPLATES if k.endswith("_v4")}


def _headers():
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN must be set")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _waba_id():
    waba_id = os.getenv("OUTREACH_WA_BUSINESS_ACCOUNT_ID")
    if not waba_id:
        raise RuntimeError("OUTREACH_WA_BUSINESS_ACCOUNT_ID must be set")
    return waba_id


def upload_image_for_template(image_path: str, app_id: str = "1325858332273520") -> str:
    """Upload image via Meta Resumable Upload API. Returns the h: handle."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN must be set")

    path = pathlib.Path(image_path)
    if not path.exists():
        raise RuntimeError(f"Image not found: {image_path}")

    file_size = path.stat().st_size

    # Create upload session via App ID (system-user tokens use app-id endpoint)
    create_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{app_id}/uploads",
        params={
            "file_name": path.name,
            "file_length": file_size,
            "file_type": "image/png",
            "access_token": token,
        },
        timeout=15,
    )
    create_data = create_resp.json()
    if not create_resp.ok:
        raise RuntimeError(f"Upload session creation failed: {create_data}")

    session_id = create_data["id"]

    # Upload binary
    with open(path, "rb") as f:
        binary = f.read()

    upload_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{session_id}",
        headers={
            "Authorization": f"OAuth {token}",
            "file_offset": "0",
            "Content-Type": "application/octet-stream",
        },
        data=binary,
        timeout=30,
    )
    upload_data = upload_resp.json()
    if not upload_resp.ok:
        raise RuntimeError(f"Image upload failed: {upload_data}")

    handle = upload_data.get("h")
    if not handle:
        raise RuntimeError(f"No handle in upload response: {upload_data}")

    return handle


def submit_template(name: str, logo_handle: str | None = None) -> dict:
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template '{name}'. Available: {list(TEMPLATES.keys())}")

    defn = TEMPLATES[name]
    import copy, json as _json
    components = copy.deepcopy(defn["components"])

    # Inject logo handle into IMAGE header example for v2/v3/v4 templates
    if name in (_V2_NAMES | _V3_NAMES | _V4_NAMES) and logo_handle:
        for comp in components:
            if comp.get("type") == "HEADER" and comp.get("format") == "IMAGE":
                comp["example"] = {"header_handle": [logo_handle]}
                break

    payload = {
        "name": name,
        "language": defn["language"],
        "category": defn["category"],
        "components": components,
    }
    url = f"{GRAPH_API_BASE}/{_waba_id()}/message_templates"
    response = requests.post(url, json=payload, headers=_headers(), timeout=15)
    data = response.json()

    if response.status_code in (200, 201):
        return {
            "name": name,
            "display_name": TEMPLATE_DISPLAY_NAMES.get(name, name),
            "status": "PENDING",
            "meta_id": data.get("id"),
        }

    error = data.get("error", {})
    if error.get("error_subcode") == 2388085:
        return {"name": name, "display_name": TEMPLATE_DISPLAY_NAMES.get(name, name), "status": "ALREADY_EXISTS"}

    raise RuntimeError(f"Meta API error: {error.get('message', response.text)}")


def submit_all_templates() -> list[dict]:
    results = []
    for name in TEMPLATES:
        try:
            results.append(submit_template(name))
        except Exception as exc:
            results.append({
                "name": name,
                "display_name": TEMPLATE_DISPLAY_NAMES.get(name, name),
                "status": "ERROR",
                "error": str(exc),
            })
    return results


def get_template_statuses() -> list[dict]:
    url = f"{GRAPH_API_BASE}/{_waba_id()}/message_templates"
    response = requests.get(
        url,
        params={"fields": "name,status,rejected_reason,category,language", "limit": 100},
        headers=_headers(),
        timeout=15,
    )

    if not response.ok:
        error = response.json().get("error", {})
        raise RuntimeError(f"Meta API error: {error.get('message', response.text)}")

    fetched = {t["name"]: t for t in response.json().get("data", []) if t["name"] in TEMPLATES}

    results = []
    for name, defn in TEMPLATES.items():
        if name in fetched:
            t = fetched[name]
            results.append({
                "name": name,
                "display_name": TEMPLATE_DISPLAY_NAMES.get(name, name),
                "status": t.get("status", "UNKNOWN"),
                "rejected_reason": t.get("rejected_reason"),
                "category": t.get("category", defn["category"]),
                "language": t.get("language", defn["language"]),
            })
        else:
            results.append({
                "name": name,
                "display_name": TEMPLATE_DISPLAY_NAMES.get(name, name),
                "status": "NOT_SUBMITTED",
                "rejected_reason": None,
                "category": defn["category"],
                "language": defn["language"],
            })

    return results
