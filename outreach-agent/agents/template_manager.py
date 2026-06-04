import os
import requests

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"

TEMPLATES = {
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
                    "— Neeraj, PracticeDesk"
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
                    "— Neeraj, PracticeDesk"
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
                    "— Neeraj, PracticeDesk"
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
                    "— Neeraj, PracticeDesk"
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
                    "— Neeraj, PracticeDesk"
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
                    "— Neeraj, PracticeDesk"
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
}

TEMPLATE_DISPLAY_NAMES = {
    "apex_outreach_salon_v1": "Salon",
    "apex_outreach_dentist_v1": "Dentist",
    "apex_outreach_doctor_v1": "Doctor / GP",
    "apex_outreach_physio_v1": "Physiotherapist",
    "apex_outreach_accountant_v1": "Accountant",
    "apex_outreach_lawyer_v1": "Lawyer",
}


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


def submit_template(name: str) -> dict:
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template '{name}'. Available: {list(TEMPLATES.keys())}")

    payload = {"name": name, **TEMPLATES[name]}
    url = f"{GRAPH_API_BASE}/{_waba_id()}/message_templates"
    response = requests.post(url, json=payload, headers=_headers(), timeout=15)
    data = response.json()

    if response.status_code in (200, 201):
        return {
            "name": name,
            "display_name": TEMPLATE_DISPLAY_NAMES[name],
            "status": "PENDING",
            "meta_id": data.get("id"),
        }

    error = data.get("error", {})
    # subcode 2388085 = template already exists — not an error
    if error.get("error_subcode") == 2388085:
        return {"name": name, "display_name": TEMPLATE_DISPLAY_NAMES[name], "status": "ALREADY_EXISTS"}

    raise RuntimeError(f"Meta API error: {error.get('message', response.text)}")


def submit_all_templates() -> list[dict]:
    results = []
    for name in TEMPLATES:
        try:
            results.append(submit_template(name))
        except Exception as exc:
            results.append({
                "name": name,
                "display_name": TEMPLATE_DISPLAY_NAMES[name],
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
                "display_name": TEMPLATE_DISPLAY_NAMES[name],
                "status": t.get("status", "UNKNOWN"),
                "rejected_reason": t.get("rejected_reason"),
                "category": t.get("category", defn["category"]),
                "language": t.get("language", defn["language"]),
            })
        else:
            results.append({
                "name": name,
                "display_name": TEMPLATE_DISPLAY_NAMES[name],
                "status": "NOT_SUBMITTED",
                "rejected_reason": None,
                "category": defn["category"],
                "language": defn["language"],
            })

    return results
