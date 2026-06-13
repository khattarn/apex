"""
submit_v6_templates.py — Submit v6 WA outreach templates to Meta.

v6 = correct positioning (AI office assistant across phone/WA/email 24/7)
     + bullet capability list per vertical + logo header + all 4 buttons.

Run from outreach-agent/:
    python submit_v6_templates.py

After approval (~5 min), run:
    python test_send_v6.py
Then switch VERTICAL_TEMPLATE to _V6 in wa_broadcast.py.
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
    _V6_NAMES,
)

LOGO_PATH = Path(r"C:\Projects\Practice desk\images\PracticeDesk AI Logo.png")


def main():
    if not os.getenv("WHATSAPP_ACCESS_TOKEN"):
        print("ERROR: WHATSAPP_ACCESS_TOKEN not set")
        sys.exit(1)

    print("=== PracticeDesk v6 Template Submission ===\n")
    print(f"Uploading logo: {LOGO_PATH}")

    if not LOGO_PATH.exists():
        print(f"ERROR: Logo not found at {LOGO_PATH}")
        sys.exit(1)

    logo_handle = upload_image_for_template(str(LOGO_PATH))
    print(f"Logo handle: {logo_handle[:50]}...\n")

    results = []
    for name in sorted(_V6_NAMES):
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
            if "v6" in s["name"] or s["status"] not in ("NOT_SUBMITTED",):
                print(f"  {s['name']:45s} {s['status']}")
    except Exception as exc:
        print(f"Could not fetch statuses: {exc}")

    print("\nNext: wait ~5 minutes for approval, then run: python test_send_v6.py")


if __name__ == "__main__":
    main()
