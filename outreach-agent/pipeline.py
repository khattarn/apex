import asyncio
import sys
import os
from datetime import datetime

# Ensure package root is on the path when run directly
sys.path.insert(0, os.path.dirname(__file__))


def _ts():
    return datetime.now().strftime("%H:%M:%S")


async def run(business_type: str, city: str, max_prospects: int, send_whatsapp: bool):
    from agents.prospector import find_businesses
    from agents.personalizer import generate_message
    from agents.outreach import send_whatsapp_message
    from agents.email_scraper import scrape_email
    from database.client import get_lead_by_place_id, save_lead, update_lead, mark_contacted

    cities = [c.strip() for c in city.split(",") if c.strip()]
    multi = len(cities) > 1

    yield f"[{_ts()}] Pipeline started — {business_type} in {city} (max {max_prospects} per city)"
    yield f"[{_ts()}] Mode: {'LIVE (WhatsApp on)' if send_whatsapp else 'DRY RUN (no sends)'}"

    total_found = 0
    total_new_leads = 0
    total_messages_sent = 0

    for current_city in cities:
        if multi:
            yield f"\n[{_ts()}] ── {current_city} ──"

        # ── Step 1: Prospect ──────────────────────────────────────────────────
        yield f"[{_ts()}] Searching Google Maps for {business_type} businesses in {current_city}..."
        try:
            businesses = await asyncio.to_thread(find_businesses, business_type, current_city, max_prospects)
        except Exception as exc:
            yield f"[{_ts()}] ERROR during prospecting in {current_city}: {exc}"
            continue

        yield f"[{_ts()}] Found {len(businesses)} businesses"
        total_found += len(businesses)

        new_leads = 0
        messages_sent = 0

        for biz in businesses:
            name = biz.get("name", "Unknown")

            # ── Step 2: De-duplicate ──────────────────────────────────────────
            existing = await asyncio.to_thread(get_lead_by_place_id, biz["place_id"])
            if existing:
                yield f"  — {name}: already in database, skipping"
                continue

            lead_data = {
                **biz,
                "business_type": business_type,
                "city": current_city,
                "status": "new",
                "outreach_sent": False,
            }
            lead = await asyncio.to_thread(save_lead, lead_data)
            new_leads += 1

            # ── Step 2b: Scrape email ─────────────────────────────────────────
            if biz.get("website") and lead:
                try:
                    email = await asyncio.to_thread(scrape_email, biz["website"])
                    if email:
                        try:
                            await asyncio.to_thread(update_lead, lead["id"], {"email": email})
                            yield f"  + {name}: saved (email: {email})"
                        except Exception:
                            yield f"  + {name}: saved — email found but DB column missing (run migration)"
                    else:
                        yield f"  + {name}: saved as new lead"
                except Exception:
                    yield f"  + {name}: saved as new lead"
            else:
                yield f"  + {name}: saved as new lead"

            if not send_whatsapp:
                continue

            if not biz.get("phone"):
                yield f"  ! {name}: no phone number, skipping send"
                continue

            # ── Step 3: Personalise ───────────────────────────────────────────
            yield f"  > Generating message for {name}..."
            try:
                message = await asyncio.to_thread(generate_message, name, business_type, current_city)
            except Exception as exc:
                yield f"  ! {name}: message generation failed — {exc}"
                continue

            # ── Step 4: Send ──────────────────────────────────────────────────
            yield f"  > Sending WhatsApp to {name} ({biz['phone']})..."
            try:
                await asyncio.to_thread(send_whatsapp_message, biz["phone"], message)
                if lead:
                    await asyncio.to_thread(mark_contacted, lead["id"], message)
                messages_sent += 1
                yield f"  ✓ Message sent to {name}"
            except Exception as exc:
                yield f"  ✗ Failed to send to {name}: {exc}"

            # Rate-limit guard — 2 s between sends (do not remove)
            await asyncio.sleep(2)

        total_new_leads += new_leads
        total_messages_sent += messages_sent

    yield (
        f"\n[{_ts()}] DONE — "
        f"{total_found} found, {total_new_leads} new leads, {total_messages_sent} messages sent"
    )
