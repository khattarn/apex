"""
submit_v2_templates.py — One-time script to submit v2 WA templates to Meta.

v2 templates add:
  - IMAGE header (PracticeDesk AI logo)
  - YouTube intro video URL button
  - Home page URL button ("Start using for free")
  - Henry support phone button ("Call us with questions")

Run from outreach-agent/:
    python submit_v2_templates.py

Templates typically take minutes to a few hours to be approved.
Once approved, update VERTICAL_TEMPLATE in wa_broadcast.py to use v2 names.
"""
import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from agents.template_manager import (
    upload_image_for_template,
    submit_template,
    get_template_statuses,
    _V2_NAMES,
)

LOGO_PATH = Path(r"C:\Projects\Practice desk\images\PracticeDesk AI Logo.png")


def main():
    if not os.getenv("WHATSAPP_ACCESS_TOKEN"):
        print("ERROR: WHATSAPP_ACCESS_TOKEN not set")
        sys.exit(1)

    print("=== PracticeDesk v2 Template Submission ===\n")

    # Upload logo to Meta
    print(f"Uploading logo: {LOGO_PATH}")
    if not LOGO_PATH.exists():
        print(f"ERROR: Logo not found at {LOGO_PATH}")
        sys.exit(1)

    logo_handle = upload_image_for_template(str(LOGO_PATH))
    print(f"Logo handle: {logo_handle[:50]}...\n")

    # Submit all v2 templates
    results = []
    for name in sorted(_V2_NAMES):
        print(f"Submitting {name} ...", end=" ", flush=True)
        try:
            r = submit_template(name, logo_handle=logo_handle)
            print(r["status"])
            results.append(r)
        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({"name": name, "status": "ERROR", "error": str(exc)})

    print("\n=== Submission Results ===")
    print(json.dumps(results, indent=2))

    print("\n=== All Template Statuses ===")
    try:
        statuses = get_template_statuses()
        for s in statuses:
            print(f"  {s['name']:40s} {s['status']}")
    except Exception as exc:
        print(f"Could not fetch statuses: {exc}")


if __name__ == "__main__":
    main()
