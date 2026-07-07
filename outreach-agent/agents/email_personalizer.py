import os
import re
import random
import yaml
from functools import lru_cache
from agents.email_templates import (
    DEMO_LINK, PRODUCT_URL, INBOUND_PHONE, INBOUND_PHONE_RAW, YOUTUBE_INTRO,
    VOICE_PRICE_USD, VOICE_PRICE_CAD,
)

# Canadian provinces — used to distinguish +1 CA from +1 US
_CA_TOKENS = {
    "ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "NT", "YT", "NU",
    "ONTARIO", "QUEBEC", "ALBERTA", "MANITOBA", "SASKATCHEWAN",
    "BRITISH COLUMBIA", "NOVA SCOTIA", "NEW BRUNSWICK", "NEWFOUNDLAND",
    "PRINCE EDWARD ISLAND", "CANADA",
}

# Australian state abbreviations
_AU_STATES = {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT", "AUSTRALIA"}

# Tokens that must never appear in non-dental email copy
_DENTAL_TOKENS = {"dentist", "dental", "patient", "doctor", "cdcp", "cdbs"}


@lru_cache(maxsize=1)
def _load_email_copy() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "email_copy.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def _first_email_number(market: str) -> int:
    if market == "CA":
        return 6
    return 1


def pick_subject(subject_a: str, subject_b: str) -> tuple[str, str]:
    """Returns (variant_letter, subject_string). Random A/B split."""
    pair = random.choice([("a", subject_a), ("b", subject_b)])
    return pair[0], pair[1]


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


def _render(body: str, preheader: str, variables: dict) -> str:
    # Preheader: hidden span for inbox preview line
    preheader_html = ""
    if preheader:
        ph = preheader
        for key, val in variables.items():
            ph = ph.replace("{" + key + "}", str(val))
        preheader_html = (
            f'<span style="display:none;max-height:0;overflow:hidden;mso-hide:all;">'
            f'{ph}</span>'
        )

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
{preheader_html}
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
        f'<a href="{product}" style="color:#888888;">practicedesk.live</a><br>'
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
    Selects vertical-correct copy from email_copy.yaml by lead.business_type.
    Falls back to defaults block for unrecognised verticals; callers must skip
    leads with empty business_type before calling (Change #2).
    """
    market = detect_market(lead.get("phone", ""), lead.get("address", ""))

    if email_number is None:
        email_number = _first_email_number(market)

    name    = lead.get("name", "your practice")
    city    = lead.get("city", "")
    address = lead.get("address", "")
    state   = extract_state(address) or city

    # ── Vertical lookup — job-ad leads override the vertical sequence ─────────
    ec = _load_email_copy()
    if lead.get("pain_signal") == "job_ad_frontdesk" and "job_ad" in ec:
        seq_data = ec["job_ad"]
    else:
        vertical = (lead.get("business_type") or "").lower().strip()
        seq_data = ec["verticals"].get(vertical) or ec["defaults"]
    sequence = seq_data["sequence"]
    idx = min(max(email_number - 1, 0), len(sequence) - 1)
    entry = sequence[idx]

    variables = {
        "PRACTICE_NAME": name,
        "CITY": city,
        "STATE": state,
        "NEARBY_CITY": city,
        "MARKET": market,
        "DEMO_LINK": DEMO_LINK,
        "PRODUCT_URL": PRODUCT_URL,
        "YOUTUBE_LINK": YOUTUBE_INTRO,
        "SENDER_NAME": os.getenv("SENDER_NAME", "Henry"),
        "LEAD_ID": str(lead.get("id", "")),
        "UNSUBSCRIBE_LINK": f"{_tracking_base()}/unsubscribe?id={lead.get('id', '')}",
        "VOICE_PRICE": VOICE_PRICE_CAD if market == "CA" else VOICE_PRICE_USD,
    }

    variant, subject_tpl = pick_subject(entry["subject_a"], entry["subject_b"])
    subject = subject_tpl
    for key, val in variables.items():
        subject = subject.replace("{" + key + "}", str(val))

    html = _render(entry["body"], entry.get("preheader", ""), variables)

    return subject, html, email_number, variant


# ── Vertical leak test (run: python -m agents.email_personalizer) ─────────────
if __name__ == "__main__":
    import sys

    BASE_LEAD = {
        "id": "test-000",
        "name": "Test Business",
        "city": "Sydney",
        "address": "123 Main St, Sydney NSW 2000",
        "phone": "+61 2 9000 0000",
        "email": "test@example.com",
    }

    verticals_under_test = ["dentist", "physiotherapist", "salon", "accountant", "lawyer"]
    # Tokens that are exclusive to dental — must never appear in any other vertical.
    # "patient" is valid for physiotherapist so it's excluded from this set.
    # (The real guard against wrong-vertical sends is the yaml itself.)
    dental_only_tokens = {"dentist", "dental", "cdcp", "cdbs"}
    # Additional tokens invalid for non-clinical verticals (salon / accountant / lawyer)
    non_clinical_extra = {"patient"}
    clinical_verticals = {"dentist", "physiotherapist"}

    errors = []
    for v in verticals_under_test:
        lead = {**BASE_LEAD, "business_type": v}
        for step in [1, 2, 3, 4]:
            subj, html, _, variant = generate_email(lead, email_number=step)
            combined = (subj + html).lower()
            if v != "dentist":
                forbidden = dental_only_tokens.copy()
                if v not in clinical_verticals:
                    forbidden |= non_clinical_extra
                leaked = [tok for tok in forbidden if tok in combined]
                if leaked:
                    errors.append(f"FAIL  vertical={v} step={step}  leaked tokens: {leaked}")
                else:
                    print(f"OK    vertical={v} step={step} variant={variant}  subject: {subj[:60]}")
            else:
                print(f"OK    vertical={v} step={step} variant={variant}  subject: {subj[:60]}")

    if errors:
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("\nAll verticals clean — no dental language leaks to non-dental.")
