"""
setup_vobiz_vapi.py
───────────────────
One-shot script to wire Vobiz + Vapi for the India voice agent (Priya).

Fill in the three values below, then run:
    python setup_vobiz_vapi.py

What it does:
  1. Creates SIP credentials on the Vobiz trunk
  2. Adds webhook URL to the trunk
  3. Registers Vobiz as a BYOT SIP trunk in Vapi
  4. Registers the India +91 number in Vapi
  5. Prints the INDIA_VAPI_PHONE_NUMBER_ID to add to Railway
"""

import secrets
import string
import requests

# ── Fill these in ─────────────────────────────────────────────────────────────

VOBIZ_AUTH_ID    = ""   # Your Vobiz ID  (from Vobiz console → profile)
VOBIZ_AUTH_TOKEN = ""   # Your Vobiz Auth Token
VAPI_API_KEY     = ""   # From Railway env VAPI_API_KEY

# ── Fixed values (already known) ──────────────────────────────────────────────

VOBIZ_TRUNK_ID   = "edcf4901-9062-44ac-8872-b3d3d36969c8"
VOBIZ_SIP_DOMAIN = "edcf4901.sip.vobiz.ai"
INDIA_NUMBER     = "+919262171423"
WEBHOOK_URL      = "https://serene-passion-production-cd82.up.railway.app/api/webhooks/vobiz"

VOBIZ_BASE = "https://api.vobiz.ai/api/v1"
VAPI_BASE  = "https://api.vapi.ai"

# ─────────────────────────────────────────────────────────────────────────────

def vobiz_headers():
    return {
        "X-Auth-ID":    VOBIZ_AUTH_ID,
        "X-Auth-Token": VOBIZ_AUTH_TOKEN,
        "Content-Type": "application/json",
    }

def vapi_headers():
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type":  "application/json",
    }

def _check(resp, label):
    if not resp.ok:
        print(f"\n✗ {label} failed [{resp.status_code}]: {resp.text}")
        raise SystemExit(1)
    return resp.json()

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(chars) for _ in range(length))


def step1_create_sip_credentials():
    print("\n-- Step 1: Create SIP credentials on Vobiz trunk --")
    username = "practicedesk-priya"
    password = generate_password()

    resp = requests.post(
        f"{VOBIZ_BASE}/Account/{VOBIZ_AUTH_ID}/credentials",
        headers=vobiz_headers(),
        json={
            "username":    username,
            "password":    password,
            "enabled":     True,
            "description": "Priya — India outbound voice agent",
        },
        timeout=15,
    )
    data = _check(resp, "Create SIP credentials")
    print(f"  ✓ Credential ID : {data.get('id')}")
    print(f"  ✓ Username      : {username}")
    print(f"  ✓ Password      : {password}  ← save this, shown once")
    return username, password


def step2_add_webhook():
    print("\n── Step 2: Add webhook to Vobiz trunk ──")
    resp = requests.put(
        f"{VOBIZ_BASE}/Account/{VOBIZ_AUTH_ID}/trunks/{VOBIZ_TRUNK_ID}",
        headers=vobiz_headers(),
        json={
            "status_callback":        WEBHOOK_URL,
            "status_callback_method": "POST",
            "status_callback_events": ["Ring", "StartApp", "Hangup", "recording.completed"],
        },
        timeout=15,
    )
    _check(resp, "Add webhook")
    print(f"  ✓ Webhook set → {WEBHOOK_URL}")


def step3_register_vobiz_in_vapi(sip_username, sip_password):
    print("\n-- Step 3: Register Vobiz SIP trunk in Vapi (BYOT) --")
    resp = requests.post(
        f"{VAPI_BASE}/credential",
        headers=vapi_headers(),
        json={
            "provider": "byo-sip-trunk",
            "name": "Vobiz India",
            "gateways": [{"ip": VOBIZ_SIP_DOMAIN}],
        },
        timeout=15,
    )
    data = _check(resp, "Register Vobiz in Vapi")
    cred_id = data.get("id")
    print(f"  ✓ Vapi credential ID: {cred_id}")
    return cred_id


def step4_register_india_number(vapi_credential_id):
    print("\n── Step 4: Register India number in Vapi ──")
    resp = requests.post(
        f"{VAPI_BASE}/phone-number",
        headers=vapi_headers(),
        json={
            "provider":     "byo-sip-trunk",
            "number":       INDIA_NUMBER,
            "credentialId": vapi_credential_id,
        },
        timeout=15,
    )
    data = _check(resp, "Register India number in Vapi")
    phone_id = data.get("id")
    print(f"  ✓ India Vapi phone number ID: {phone_id}")
    return phone_id


def main():
    # Validate inputs
    missing = []
    if not VOBIZ_AUTH_ID:    missing.append("VOBIZ_AUTH_ID")
    if not VOBIZ_AUTH_TOKEN: missing.append("VOBIZ_AUTH_TOKEN")
    if not VAPI_API_KEY:     missing.append("VAPI_API_KEY")
    if missing:
        print(f"✗ Fill in these values at the top of the script: {', '.join(missing)}")
        raise SystemExit(1)

    print("Wiring Vobiz + Vapi for India voice agent...")

    sip_user, sip_pass  = step1_create_sip_credentials()
    step2_add_webhook()
    cred_id             = step3_register_vobiz_in_vapi(sip_user, sip_pass)
    phone_id            = step4_register_india_number(cred_id)

    print("\n" + "═" * 60)
    print("✅  DONE — add this to Railway env vars:")
    print("═" * 60)
    print(f"\n  INDIA_VAPI_PHONE_NUMBER_ID={phone_id}\n")
    print("That's the only Railway change needed.")
    print("Priya can now place outbound calls via Vobiz +919262171423.")


if __name__ == "__main__":
    main()
