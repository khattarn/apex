import os
import re
import random
from agents.email_templates import TEMPLATES, DEMO_LINK, PRODUCT_URL, INBOUND_PHONE, INBOUND_PHONE_RAW, YOUTUBE_INTRO

# Canadian provinces — used to distinguish +1 CA from +1 US
_CA_TOKENS = {
    "ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "NT", "YT", "NU",
    "ONTARIO", "QUEBEC", "ALBERTA", "MANITOBA", "SASKATCHEWAN",
    "BRITISH COLUMBIA", "NOVA SCOTIA", "NEW BRUNSWICK", "NEWFOUNDLAND",
    "PRINCE EDWARD ISLAND", "CANADA",
}

# Australian state abbreviations
_AU_STATES = {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT", "AUSTRALIA"}


def detect_market(phone: str, address: str = "") -> str:
    phone = re.sub(r"[^\d+]", "", phone or "")
    addr = (address or "").upper()

    if phone.startswith("+61") or phone.startswith("0061"):
        return "AU"
    if any(tok in addr for tok in _AU_STATES):
        return "AU"

    if phone.startswith("+1") or (phone.startswith("1") and len(phone) == 11):
        if any(tok in addr for tok in _CA_TOKENS):
            return "CA"
        return "US"

    if "CANADA" in addr:
        return "CA"
    return "US"  # safe default for unrecognised numbers


def extract_state(address: str) -> str:
    """Pull a 2-3 letter state/province code from an address string."""
    if not address:
        return ""
    # Matches patterns like ", NSW 2000" or ", CA 90210" or ", ON M5V"
    m = re.search(r",\s+([A-Z]{2,3})\s+[\dA-Z]", address)
    if m:
        return m.group(1)
    return ""


def _pain_line(name: str, city: str, market: str, review_count: int = 0) -> str:
    if market == "AU":
        base = f"Noticed {name} on Google"
        return f"{base} — {review_count} reviews tells me you have real patients who depend on you." if review_count else f"{base} — clearly a practice your patients trust."
    if market == "CA":
        return f"Found {name} on Google while looking at dental practices in {city} — clearly a practice your patients trust."
    # US default
    base = f"Searched for dental practices in {city} and {name} came up"
    return f"{base} — {review_count} reviews tells me your patients value what you do." if review_count else f"{base}."


def _review_line(name: str, review_count: int) -> str:
    if review_count:
        return f"{review_count} Google reviews tells me {name} has real patients who care about you. They deserve to reach you every time they call."
    return f"{name}'s patients deserve to reach you every time they call."


def _first_email_number(market: str) -> int:
    if market == "CA":
        return 6
    return 1  # Email 2 used when review pain found — not yet implemented


def pick_subject(email_num: int) -> tuple[str, str]:
    """Returns (variant_letter, subject_string). A/B split on first two variants."""
    subjects = TEMPLATES[email_num]["subjects"]
    chosen_text, chosen_variant = random.choice(subjects[:2])
    return chosen_variant, chosen_text


def _tracking_base() -> str:
    return os.getenv(
        "RAILWAY_PUBLIC_URL",
        "https://serene-passion-production-cd82.up.railway.app"
    )


def _btn(href: str, label: str, bg: str, color: str, border: str) -> str:
    return (
        f'<a href="{href}" style="display:inline-block;background:{bg};color:{color};'
        f'font-size:11px;font-weight:600;padding:8px 14px;border-radius:5px;'
        f'text-decoration:none;border:1.5px solid {border};white-space:nowrap;">'
        f'{label}</a>'
    )


def _render(email_num: int, variables: dict) -> str:
    body = TEMPLATES[email_num]["body"]
    for key, val in variables.items():
        body = body.replace("{" + key + "}", str(val))

    market    = variables.get("MARKET", "US")
    lead_id   = variables.get("LEAD_ID", "")
    footer    = _build_footer(variables, market)
    base      = _tracking_base()
    pixel     = (f'<img src="{base}/track/open/{lead_id}" width="1" height="1" '
                 f'style="display:none;" alt="" />')

    # Wrap demo link with click tracking
    raw_demo     = variables.get("DEMO_LINK", DEMO_LINK)
    tracked_demo = f"{base}/track/click/{lead_id}?url={raw_demo}"
    body = body.replace(f'href="{raw_demo}"', f'href="{tracked_demo}"')

    # Action buttons
    youtube = variables.get("YOUTUBE_LINK", "")
    product_url = variables.get("PRODUCT_URL", PRODUCT_URL)
    btn_demo   = _btn(product_url,  "See it working &rarr;", "#4f46e5", "#ffffff", "#4f46e5")
    btn_book   = _btn(tracked_demo, "&#128197; Book a Demo",  "#ffffff", "#059669", "#6ee7b7")
    btn_call   = _btn(f"tel:{INBOUND_PHONE_RAW}", f"&#128222; {INBOUND_PHONE}", "#ffffff", "#7c3aed", "#c4b5fd")
    btn_yt     = (_btn(youtube, "&#9654; YouTube Introduction", "#ffffff", "#1e3a8a", "#93c5fd")
                  if youtube else "")

    # 2-column button grid (works in all email clients)
    col1 = f"{btn_demo}<br><br>{btn_book}"
    col2 = f"{btn_call}" + (f"<br><br>{btn_yt}" if btn_yt else "")

    buttons_block = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
  <td width="50%" style="padding:4px 8px 4px 0;vertical-align:top;">{col1}</td>
  <td width="50%" style="padding:4px 0 4px 8px;vertical-align:top;">{col2}</td>
</tr>
</table>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>PracticeDesk</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f1f5f9;">
<tr><td align="center" style="padding:24px 16px;">

<table width="580" cellpadding="0" cellspacing="0" border="0"
       style="max-width:580px;width:100%;background:#ffffff;border-radius:10px;
              overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.10);">

  <!-- ── HEADER ───────────────────────────────────────── -->
  <tr><td style="background:#312e81;padding:22px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td>
        <span style="font-size:22px;font-weight:900;color:#ffffff;letter-spacing:-0.5px;">
          Practice<span style="color:#a5b4fc;">Desk</span>
        </span>
        <div style="color:#c7d2fe;font-size:10px;letter-spacing:1.2px;
                    text-transform:uppercase;margin-top:3px;">
          AI Front Office &nbsp;&middot;&nbsp; 24 / 7
        </div>
      </td>
      <td align="right" style="font-size:11px;color:#a5b4fc;line-height:1.6;">
        Voice &nbsp;&bull;&nbsp; WhatsApp<br>Auto Bookings
      </td>
    </tr></table>
  </td></tr>

  <!-- ── FEATURE STRIP ────────────────────────────────── -->
  <tr><td style="background:#eef2ff;padding:10px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td align="center" style="font-size:11px;color:#4338ca;font-weight:600;
                                 padding:0 6px;border-right:1px solid #c7d2fe;">
        &#128222; 24/7 Voice Receptionist
      </td>
      <td align="center" style="font-size:11px;color:#4338ca;font-weight:600;
                                 padding:0 6px;border-right:1px solid #c7d2fe;">
        &#128172; WhatsApp Booking
      </td>
      <td align="center" style="font-size:11px;color:#4338ca;font-weight:600;
                                 padding:0 6px;">
        &#9989; One-Click Confirm
      </td>
    </tr></table>
  </td></tr>

  <!-- ── ACTION BUTTONS ───────────────────────────────── -->
  <tr><td style="padding:16px 32px 0;">
    {buttons_block}
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:14px 0 0;">
  </td></tr>

  <!-- ── BODY ─────────────────────────────────────────── -->
  <tr><td style="padding:24px 32px 20px;font-size:15px;line-height:1.75;color:#1e293b;">
    {body}
  </td></tr>

  <!-- ── FOOTER ───────────────────────────────────────── -->
  <tr><td style="padding:16px 32px 24px;border-top:1px solid #f1f5f9;
                  font-size:11px;line-height:1.8;color:#94a3b8;">
    {footer}
  </td></tr>

</table>
</td></tr>
</table>
{pixel}
</body>
</html>"""


def _build_footer(variables: dict, market: str) -> str:
    sender = variables.get("SENDER_NAME", "Henry")
    lead_id = variables.get("LEAD_ID", "")
    base = _tracking_base()
    unsubscribe = f"{base}/unsubscribe?id={lead_id}"
    demo = variables.get("DEMO_LINK", DEMO_LINK)
    product = variables.get("PRODUCT_URL", PRODUCT_URL)

    address = "1787 St Clair Ave W, Toronto, ON, Canada"
    compliance = {
        "AU": f"PracticeDesk · henry@practicedesk.live · {address}<br>Implied consent under AU Spam Act 2003 (B2B)",
        "CA": f"PracticeDesk · henry@practicedesk.live · {address}<br>Implied consent under CASL (publicly listed B2B email)",
        "US": f"PracticeDesk · henry@practicedesk.live · {address}<br>CAN-SPAM compliant",
    }.get(market, f"PracticeDesk · henry@practicedesk.live · {address}")

    return (
        f"{sender} · PracticeDesk · "
        f'<a href="{product}" style="color:#888888;">practicedesk.netlify.app</a><br>'
        f'<a href="{demo}" style="color:#4f46e5;">Book a demo</a> &nbsp;·&nbsp; '
        f'<a href="{product}" style="color:#4f46e5;">Start 14-day free trial</a> &nbsp;·&nbsp; '
        f'<a href="tel:{INBOUND_PHONE_RAW}" style="color:#4f46e5;">Call Henry: {INBOUND_PHONE}</a>'
        f'<span style="color:#aaaaaa;font-size:11px;"> (AI, answers 24/7)</span><br><br>'
        f'{compliance}<br>'
        f'<a href="{unsubscribe}" style="color:#aaaaaa;">Unsubscribe</a>'
    )


def generate_email(lead: dict, email_number: int = None) -> tuple[str, str, int, str]:
    """
    Returns (subject, html, email_number_used, subject_variant).
    email_number=None means auto-select based on routing logic.
    """
    market = detect_market(lead.get("phone", ""), lead.get("address", ""))

    if email_number is None:
        email_number = _first_email_number(market)

    name          = lead.get("name", "your practice")
    business_type = lead.get("business_type", "")
    city          = lead.get("city", "")
    address       = lead.get("address", "")
    state         = extract_state(address) or city

    variables = {
        "PRACTICE_NAME": name,
        "FIRST_NAME": "Doctor",
        "CITY": city,
        "STATE": state,
        "NEARBY_CITY": city,
        "MARKET": market,
        "PAIN_LINE": _pain_line(name, city, market),
        "REVIEW_LINE": _review_line(name, 0),
        "REVIEW_COUNT": "",
        "RATING": "",
        "DEMO_LINK": DEMO_LINK,
        "PRODUCT_URL": PRODUCT_URL,
        "YOUTUBE_LINK": YOUTUBE_INTRO,
        "SENDER_NAME": os.getenv("SENDER_NAME", "Henry"),
        "LEAD_ID": str(lead.get("id", "")),
        "UNSUBSCRIBE_LINK": f"{_tracking_base()}/unsubscribe?id={lead.get('id', '')}",
    }

    variant, subject_tpl = pick_subject(email_number)
    subject = subject_tpl
    for key, val in variables.items():
        subject = subject.replace("{" + key + "}", str(val))

    html = _render(email_number, variables)

    return subject, html, email_number, variant
