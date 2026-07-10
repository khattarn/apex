import asyncio
import json
import logging
import os
import sys
import time as _time
from contextlib import asynccontextmanager
from typing import Optional

import requests

log = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

sys.path.insert(0, os.path.dirname(__file__))

_running: dict = {}       # tracks which pipeline agents are currently executing
_active_calls: dict = {}  # workflow_run_id → {lead_name, phone, started_at, direction}
_JOB_REGISTRY: dict = {}  # job name → async fn; populated in start_scheduler for auto-recovery
_scheduler = None         # module-level ref prevents GC of the APScheduler instance


def _track_active_call(
    run_id: str,
    lead_id: str,
    lead_name: str,
    phone: str,
    direction: str,
) -> None:
    """Register a just-triggered Dograh call in the live-call dashboard tracker."""
    run_id = str(run_id)
    if not run_id:
        return
    from datetime import datetime, timezone
    _active_calls[run_id] = {
        "call_id":    run_id,
        "lead_name":  lead_name or phone,
        "phone":      phone,
        "direction":  direction,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "lead_id":    lead_id,
    }

@asynccontextmanager
async def lifespan(_app):
    # start_scheduler is defined later in this file — Python resolves the name at call time
    await start_scheduler()
    yield

app = FastAPI(title="Apex Admin API", version="1.0.0", lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _admin_password():
    return os.getenv("ADMIN_PASSWORD", "")

def _admin_email():
    return os.getenv("ADMIN_EMAIL", "")


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
async def login(body: LoginRequest):
    if body.email == _admin_email() and body.password == _admin_password():
        return {"token": _admin_password()}
    raise HTTPException(status_code=401, detail="Invalid credentials")


def verify_token(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ").strip()
    if token != _admin_password():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token


# ── Manual business ingest ────────────────────────────────────────────────────

class IngestBusinessRow(BaseModel):
    name: str
    city: str
    vertical: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@app.post("/api/ingest/new-businesses")
async def ingest_businesses(
    rows: list[IngestBusinessRow],
    _: str = Depends(verify_token),
):
    from agents.ingest import ingest_new_businesses
    payload = [r.model_dump() for r in rows]
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ingest_new_businesses, payload)
    return result


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    business_type: str
    city: str
    max_prospects: int = 5
    send_whatsapp: bool = False


@app.post("/api/pipeline/run")
async def run_pipeline(body: PipelineRequest, _=Depends(verify_token)):
    async def event_generator():
        from pipeline import run as pipeline_run
        from database.client import save_campaign_run

        log_lines: list[str] = []
        prospects_found = 0
        messages_sent = 0

        _running["pipeline"] = {"city": body.city, "type": body.business_type, "started": _time.time()}
        try:
            async for line in pipeline_run(
                business_type=body.business_type,
                city=body.city,
                max_prospects=body.max_prospects,
                send_whatsapp=body.send_whatsapp,
            ):
                log_lines.append(line)
                if "found" in line.lower() and "businesses" in line.lower():
                    try:
                        prospects_found += int(line.split("Found")[1].split("businesses")[0].strip())
                    except (IndexError, ValueError):
                        pass
                if line.strip().startswith("✓"):
                    messages_sent += 1
                yield {"data": json.dumps({"type": "log", "line": line})}
                await asyncio.sleep(0)

            new_leads = sum(1 for l in log_lines if l.strip().startswith("+"))
            try:
                save_campaign_run({
                    "business_type": body.business_type,
                    "city": body.city,
                    "max_prospects": body.max_prospects,
                    "mode": "live" if body.send_whatsapp else "dry_run",
                    "prospects_found": prospects_found,
                    "new_leads": new_leads,
                    "messages_sent": messages_sent,
                    "log": "\n".join(log_lines),
                })
            except Exception:
                pass

            _running.pop("pipeline", None)
            yield {
                "data": json.dumps({
                    "type": "done",
                    "prospects_found": prospects_found,
                    "new_leads": new_leads,
                    "messages_sent": messages_sent,
                })
            }

        except Exception as exc:
            _running.pop("pipeline", None)
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(event_generator(), headers={"X-Accel-Buffering": "no"}, ping=20)


# ── WA Blast — send WA to existing uncontacted leads ─────────────────────────

class WaBlastRequest(BaseModel):
    business_type: Optional[str] = None   # None = all types
    city: Optional[str] = None            # None = all cities; comma-separated ok
    limit: int = 50                       # max leads per run


@app.post("/api/leads/wa-blast", dependencies=[Depends(verify_token)])
async def wa_blast(body: WaBlastRequest):
    """Send WA messages to existing leads that haven't been contacted via WA yet.
    Streams SSE log lines identical to the pipeline endpoint."""

    async def event_generator():
        from datetime import datetime
        from agents.personalizer import generate_message
        from agents.outreach import send_whatsapp_message
        from database.client import get_client, mark_contacted, log_activity, save_campaign_run

        def _ts():
            return datetime.now().strftime("%H:%M:%S")

        db = get_client()

        # Build query for uncontacted leads with a phone number
        query = (
            db.table("leads")
            .select("*")
            .or_("outreach_sent.eq.false,outreach_sent.is.null")
            .not_.is_("phone", "null")
            .neq("phone", "")
            .neq("status", "dead")
        )
        if body.business_type:
            query = query.eq("business_type", body.business_type)
        if body.city:
            cities = [c.strip() for c in body.city.split(",") if c.strip()]
            if len(cities) == 1:
                query = query.ilike("city", f"%{cities[0]}%")
            else:
                query = query.in_("city", cities)

        rows = query.limit(body.limit).execute().data or []

        filters = []
        if body.business_type: filters.append(body.business_type)
        if body.city:           filters.append(body.city)
        filter_str = " · ".join(filters) if filters else "all types, all cities"

        yield {"data": json.dumps({"type": "log", "line": f"[{_ts()}] WA Blast — {len(rows)} uncontacted leads ({filter_str})"})}
        yield {"data": json.dumps({"type": "log", "line": f"[{_ts()}] Sending personalised WhatsApp messages..."})}
        yield {"data": json.dumps({"type": "log", "line": ""})}

        sent = skipped = failed = 0
        _running["wa_blast"] = {"started": _time.time(), "total": len(rows)}

        for lead in rows:
            name          = lead.get("name", "Business")
            business_type = lead.get("business_type", "practice")
            city          = lead.get("city", "")
            phone         = lead.get("phone", "")

            yield {"data": json.dumps({"type": "log", "line": f"  > {name} ({city})..."})}
            await asyncio.sleep(0)

            try:
                message = await asyncio.to_thread(generate_message, name, business_type, city)
            except Exception as exc:
                failed += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ✗ {name}: message failed — {exc}"})}
                continue

            try:
                await asyncio.to_thread(send_whatsapp_message, phone, message)
                await asyncio.to_thread(mark_contacted, lead["id"], message)
                await asyncio.to_thread(log_activity, lead["id"], "outreach_sent", {"trigger": "wa_blast", "message": message[:120]})
                sent += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ✓ Sent to {name}"})}
            except Exception as exc:
                failed += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ✗ {name}: send failed — {exc}"})}

            await asyncio.sleep(2)  # rate-limit guard

        _running.pop("wa_blast", None)

        try:
            save_campaign_run({
                "business_type": body.business_type or "all",
                "city":          body.city or "all",
                "max_prospects": body.limit,
                "mode":          "wa_blast",
                "prospects_found": len(rows),
                "new_leads":     0,
                "messages_sent": sent,
                "log":           f"WA Blast: Sent={sent} Skipped={skipped} Failed={failed}",
            })
        except Exception:
            pass

        yield {"data": json.dumps({
            "type":    "done",
            "sent":    sent,
            "skipped": skipped,
            "failed":  failed,
        })}

    return EventSourceResponse(event_generator(), headers={"X-Accel-Buffering": "no"}, ping=20)


# ── Leads ─────────────────────────────────────────────────────────────────────

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[str] = None


@app.get("/api/leads/called-ids")
async def get_called_ids(_=Depends(verify_token)):
    """Returns set of lead IDs that have received an outbound Sophie call."""
    from database.client import get_client
    rows = get_client().table("lead_activities").select("lead_id").in_("type", ["outbound_call", "voice_followup_placed"]).execute().data or []
    return {"ids": list({str(r["lead_id"]) for r in rows})}


@app.get("/api/active-calls")
async def get_active_calls(_=Depends(verify_token)):
    """Returns calls currently in progress (tracked in memory via Vapi call-started webhook)."""
    from datetime import datetime, timezone
    cutoff = datetime.now(timezone.utc).timestamp() - 900  # 15 min TTL
    stale = [k for k, v in _active_calls.items()
             if datetime.fromisoformat(v["started_at"]).timestamp() < cutoff]
    for k in stale:
        _active_calls.pop(k, None)
    return {"calls": list(_active_calls.values()), "count": len(_active_calls)}


@app.get("/api/leads")
async def list_leads(
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    city: Optional[str] = None,
    outreach_sent: Optional[bool] = None,
    email_engagement: Optional[str] = None,
    voice_called: Optional[bool] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_token),
):
    from database.client import get_leads
    return get_leads(
        business_type=business_type,
        status=status,
        city=city,
        outreach_sent=outreach_sent,
        email_engagement=email_engagement,
        voice_called=voice_called,
        search=search,
        source=source,
        limit=limit,
        offset=offset,
    )


@app.post("/api/leads")
async def create_lead(payload: dict, _=Depends(verify_token)):
    from database.client import save_lead, get_lead_by_place_id
    import uuid as _uuid

    name = (payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    if not name or not phone:
        raise HTTPException(status_code=400, detail="name and phone are required")

    # Normalise phone to E.164 for India if bare 10 digits
    if phone.isdigit() and len(phone) == 10:
        phone = f"+91{phone}"
    elif phone.startswith("0") and len(phone) == 11:
        phone = f"+91{phone[1:]}"

    place_id = payload.get("place_id") or f"manual-{_uuid.uuid4().hex[:12]}"

    existing = get_lead_by_place_id(place_id)
    if existing:
        raise HTTPException(status_code=409, detail="Lead with this place_id already exists")

    row = {
        "name": name,
        "phone": phone,
        "place_id": place_id,
        "business_type": payload.get("business_type") or "dentist",
        "city": (payload.get("city") or "").strip(),
        "status": "new",
        "address": (payload.get("address") or "").strip() or None,
        "website": (payload.get("website") or "").strip() or None,
        "email": (payload.get("email") or "").strip() or None,
        "notes": (payload.get("notes") or "").strip() or None,
    }
    result = save_lead(row)
    return result


@app.post("/api/leads/enrich-emails")
async def enrich_emails(_=Depends(verify_token)):
    async def generate():
        from database.client import get_leads_for_enrichment, mark_scrape_attempted
        from agents.email_scraper import scrape_email_debug

        candidates = get_leads_for_enrichment()
        total = len(candidates)
        yield {"data": json.dumps({"type": "log", "line": f"Found {total} leads to enrich"})}

        if total == 0:
            yield {"data": json.dumps({"type": "done", "enriched": 0, "total": 0, "queued": 0})}
            return

        _running["email_scraper"] = {"total": total, "started": _time.time()}

        async def _scrape_one(website: str) -> tuple[str | None, list[str]]:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(scrape_email_debug, website),
                    timeout=8,
                )
            except asyncio.TimeoutError:
                return None, [f"  timeout after 8s"]
            except Exception as exc:
                return None, [f"  error: {exc}"]

        BATCH = 5
        enriched = 0
        for batch_start in range(0, total, BATCH):
            batch = candidates[batch_start:batch_start + BATCH]
            results = await asyncio.gather(*[_scrape_one(l["website"]) for l in batch])

            for lead, (email, debug_lines) in zip(batch, results):
                name = lead["name"]
                yield {"data": json.dumps({"type": "log", "line": f"\n→ {name}"})}
                for line in debug_lines:
                    yield {"data": json.dumps({"type": "log", "line": line})}

                if email:
                    mark_scrape_attempted(lead["id"], email)
                    enriched += 1
                    yield {"data": json.dumps({"type": "log", "line": f"  ✓ {email} — queued for Email 1"})}
                else:
                    mark_scrape_attempted(lead["id"], None)
                    yield {"data": json.dumps({"type": "log", "line": f"  No email found"})}

            await asyncio.sleep(0)

        _running.pop("email_scraper", None)
        yield {"data": json.dumps({"type": "done", "enriched": enriched, "total": total, "queued": enriched})}

    return EventSourceResponse(generate(), ping=20)


@app.post("/api/leads/email-campaign")
async def email_campaign(_=Depends(verify_token)):
    async def generate():
        from database.client import (
            get_leads_due_for_email, advance_email_sequence,
            log_activity, get_setting, EMAIL_SEQUENCE, email_sequence_cap,
        )
        from agents.email_personalizer import generate_email, detect_market
        from agents.email_sender import send_email
        from utils.timezone import is_email_window, window_description

        candidates = get_leads_due_for_email()
        leads = _gate_casl_ca(candidates)
        if len(leads) < len(candidates):
            yield {"data": json.dumps({"type": "log", "line": f"CASL gate: {len(candidates) - len(leads)} CA lead(s) held back (daily cap or no scrape consent)"})}
        yield {"data": json.dumps({"type": "log", "line": f"Found {len(leads)} leads due for email"})}

        if not leads:
            _running.pop("email_campaign", None)
            yield {"data": json.dumps({"type": "done", "sent": 0, "skipped": 0, "failed": 0, "total": 0})}
            return

        _running["email_campaign"] = {"total": len(leads), "started": _time.time()}

        # Compute which cities/types are in this batch for attribution
        batch_cities = sorted({l.get("city", "") for l in leads if l.get("city")})
        batch_types  = sorted({l.get("business_type", "") for l in leads if l.get("business_type")})
        cities_str   = ", ".join(batch_cities) if batch_cities else "all"
        types_str    = ", ".join(batch_types)  if batch_types  else "all"
        yield {"data": json.dumps({"type": "log", "line": f"Cities in this run: {cities_str}"})}

        # Create campaign run now so we have an ID to link each email_send record
        from database.client import save_campaign_run, update_campaign_run, save_email_send
        run_record = save_campaign_run({
            "type": "email", "business_type": types_str, "city": cities_str,
            "max_prospects": len(leads), "mode": "live",
            "prospects_found": len(leads), "new_leads": 0,
            "messages_sent": 0, "emails_sent": 0, "log": "In progress…",
        })
        run_id = run_record["id"] if run_record else None

        test_recipient = get_setting("test_recipient_email") or ""
        test_copy_sent = False
        sent = skipped = failed = 0

        from agents.email_sender import QuotaExceededError
        quota_hit = False

        for i, lead in enumerate(leads):
            name   = lead["name"]
            if not (lead.get("business_type") or "").strip():
                skipped += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ⚠ {name} — skipped (no business_type)"})}
                continue
            city   = lead.get("city", "")
            market = detect_market(lead.get("phone", ""), lead.get("address", ""))

            if not is_email_window(city, market):
                win = window_description(city, market)
                yield {"data": json.dumps({"type": "log", "line": f"  ⏰ {name} — outside window ({win}), sending anyway (manual)"})}

            current_step = lead.get("email_sequence_step") or 0
            next_step    = current_step + 1
            seq_cap      = email_sequence_cap(lead)
            if next_step > seq_cap:
                skipped += 1
                continue

            email_num, _ = EMAIL_SEQUENCE[next_step - 1]
            yield {"data": json.dumps({"type": "log", "line": f"  > {name} — Email {email_num} (step {next_step}/{seq_cap})"})}

            try:
                subject, html, email_num_used, variant = await asyncio.to_thread(
                    generate_email, lead, email_number=email_num
                )
                send_result = await asyncio.to_thread(send_email, lead["email"], subject, html)
                resend_id   = (send_result or {}).get("id", "")
                if resend_id and run_id:
                    save_email_send(lead["id"], run_id, resend_id, email_num_used, next_step, market=market)
                advance_email_sequence(lead["id"], next_step, sequence_length=seq_cap)
                log_activity(lead["id"], "email_sent", {
                    "email_number": email_num_used, "subject": subject,
                    "variant": variant, "sequence_step": next_step,
                })
                sent += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ✓ {name} ({lead['email']}) — variant {variant}"})}

                if test_recipient and not test_copy_sent:
                    try:
                        await asyncio.to_thread(send_email, test_recipient, f"[TEST COPY] {subject}", html)
                        test_copy_sent = True
                        yield {"data": json.dumps({"type": "log", "line": f"  \U0001f4cb Test copy → {test_recipient}"})}
                    except Exception:
                        pass
            except QuotaExceededError:
                quota_hit = True
                remaining = len(leads) - i
                yield {"data": json.dumps({"type": "log", "line": f"  ⛔ Resend daily quota reached — {remaining} lead(s) deferred to next run"})}
                break
            except Exception as exc:
                failed += 1
                yield {"data": json.dumps({"type": "log", "line": f"  ✗ Failed {name}: {exc}"})}

            await asyncio.sleep(0.3)

        if run_id:
            try:
                update_campaign_run(run_id, {
                    "emails_sent": sent,
                    "log": f"Sent: {sent}, Skipped: {skipped}, Failed: {failed}",
                })
            except Exception:
                pass

        _running.pop("email_campaign", None)
        yield {"data": json.dumps({"type": "done", "sent": sent, "skipped": skipped, "failed": failed, "total": len(leads)})}
        await asyncio.sleep(0.1)

    return EventSourceResponse(generate(), headers={"X-Accel-Buffering": "no"}, ping=20)


# ── Resend webhook (open / click / bounce tracking) ───────────────────────────

@app.post("/api/webhooks/resend")
async def resend_webhook(request: Request):
    import hmac as _hmac, hashlib as _hashlib, base64 as _base64
    body   = await request.body()
    secret = os.getenv("RESEND_WEBHOOK_SECRET", "")

    if secret:
        svix_id        = request.headers.get("svix-id", "")
        svix_timestamp = request.headers.get("svix-timestamp", "")
        svix_signature = request.headers.get("svix-signature", "")
        to_sign        = f"{svix_id}.{svix_timestamp}.{body.decode()}"
        raw_secret     = secret.removeprefix("whsec_")
        decoded_secret = _base64.b64decode(raw_secret)
        computed       = "v1," + _base64.b64encode(
            _hmac.new(decoded_secret, to_sign.encode(), _hashlib.sha256).digest()
        ).decode()
        if computed not in svix_signature.split(" "):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload    = json.loads(body)
    event_type = payload.get("type", "")
    data       = payload.get("data", {})
    resend_id  = data.get("email_id", "")

    if not resend_id:
        return {"ok": True}

    from database.client import (
        get_email_send_by_resend_id, record_email_opened,
        record_email_clicked, update_lead,
    )
    send_record = get_email_send_by_resend_id(resend_id)
    lead_id     = send_record["lead_id"]     if send_record else None
    campaign_id = send_record["campaign_run_id"] if send_record else None

    if event_type == "email.opened" and lead_id:
        record_email_opened(lead_id, campaign_id, data.get("created_at"))
    elif event_type == "email.clicked" and lead_id:
        link = data.get("click", {}).get("link", "")
        record_email_clicked(lead_id, campaign_id, link, data.get("created_at"))
    elif event_type in ("email.bounced", "email.delivery_delayed") and lead_id:
        update_lead(lead_id, {"email_bounced": True})

    return {"ok": True}


# ── Cal.com webhook — captures self-serve demo bookings ─────────────────────
# Catches bookings made by a lead clicking the demo link directly (email/dashboard),
# never talking to Sophie. Without this, leads.demo_booked only ever got set via
# _handle_book_demo() (the in-call auto-booking path) — self-serve bookings were
# completely invisible to this system, only visible by checking the Cal.com
# calendar directly.
#
# Configure in Cal.com: Settings -> Developer -> Webhooks -> Add -> Subscriber URL
# = https://<railway-domain>/api/webhooks/cal, Event trigger = "Booking Created",
# copy the generated secret into Railway as CAL_WEBHOOK_SECRET.
@app.post("/api/webhooks/cal")
async def cal_webhook(request: Request):
    import hmac as _hmac, hashlib as _hashlib
    body   = await request.body()
    secret = os.getenv("CAL_WEBHOOK_SECRET", "")

    if secret:
        signature = request.headers.get("X-Cal-Signature-256", "")
        computed  = _hmac.new(secret.encode(), body, _hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(computed, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    if payload.get("triggerEvent") != "BOOKING_CREATED":
        return {"ok": True}

    data      = payload.get("payload", {})
    attendees = data.get("attendees") or []
    email     = (attendees[0].get("email", "") if attendees else "").strip().lower()
    start_time  = data.get("startTime", "")
    booking_uid = data.get("uid", "")

    if not email:
        return {"ok": True}

    from database.client import get_client, update_lead, log_activity
    db   = get_client()
    rows = db.table("leads").select("id, name").ilike("email", email).limit(1).execute().data or []
    if not rows:
        log.info("Cal.com webhook: booking from %s — no matching lead", email)
        return {"ok": True}

    lead    = rows[0]
    lead_id = str(lead["id"])

    update_lead(lead_id, {
        "demo_booked":    True,
        "demo_booked_at": start_time or None,
        "status":         "converted",
    })
    log_activity(lead_id, "booked_demo", {
        "start_time":     start_time,
        "booking_uid":    booking_uid,
        "attendee_email": email,
        "source":         "email_self_serve",
    })

    try:
        from utils.notifier import notify_founder
        notify_founder(
            kind="call_outcome",
            label="🎉 Demo booked (self-serve, no call)",
            lead_line=f"{lead.get('name', '')} — {email}",
            detail=f"Booked for {start_time}" if start_time else "",
        )
    except Exception:
        pass

    return {"ok": True}


# ── Vapi webhook — Henry inbound only (number printed on outgoing emails) ───
# Henry stays on Vapi until the printed number is retired. When a new inbound
# number is set up in Dograh, update INBOUND_PHONE* in email_templates.py and
# remove this endpoint.

@app.post("/api/webhooks/vapi")
async def vapi_webhook(request: Request):
    payload    = await request.json()
    event_type = payload.get("type", "")

    if event_type != "end-of-call-report":
        return {"ok": True}

    # Debug: persist raw payload so the structuredData field location can be
    # confirmed/corrected against a real call without needing another live test.
    try:
        from database.client import get_client as _gc
        from datetime import datetime, timezone as _tz
        _gc().table("settings").upsert({
            "key": "vapi_last_webhook_payload",
            "value": json.dumps(payload),
            "updated_at": datetime.now(_tz.utc).isoformat(),
        }).execute()
    except Exception:
        pass

    call          = payload.get("call", {})
    artifact      = payload.get("artifact", {})
    # Field location isn't verified against a live payload yet — Vapi's docs were
    # inconsistent on this. Check all three plausible spots defensively.
    analysis      = call.get("analysis") or artifact.get("analysis") or payload.get("analysis") or {}
    structured    = analysis.get("structuredData") or {}
    ended_reason  = call.get("endedReason", "")
    recording_url = artifact.get("recordingUrl", "")
    summary       = (artifact.get("summary") or "")[:500]
    transcript    = (artifact.get("transcript") or "")[:1000]
    call_type     = call.get("type", "")  # "outboundPhoneCall" | "inboundPhoneCall"
    customer_phone = call.get("customer", {}).get("number", "")
    # Same defensive-location pattern as `analysis` above — Vapi's documented
    # field is call.cost (USD), but check message/top-level too since that
    # doc has been unreliable before.
    call_cost = call.get("cost") or payload.get("cost") or 0

    call_outcome        = structured.get("call_outcome", "") or "unknown"
    demo_preferred_time = structured.get("demo_preferred_time", "")
    attendee_email      = structured.get("attendee_email", "")
    contact_name        = structured.get("contact_name", "")
    callback_day        = structured.get("callback_day", "")
    callback_time_str   = structured.get("callback_time", "")

    from database.client import update_lead, log_activity

    # ── Outbound Sophie call ──────────────────────────────────────────────────
    if call_type == "outboundPhoneCall":
        lead_id = (call.get("metadata") or {}).get("lead_id", "")
        if not lead_id:
            lead = _find_lead_by_phone(customer_phone)
            lead_id = str(lead["id"]) if lead else ""
        if not lead_id:
            return {"ok": True}
        update_lead(lead_id, {
            "status": "replied",
            "notes": f"Sophie call completed. Ended: {ended_reason}. Recording: {recording_url}",
        })
        log_activity(lead_id, "outbound_call_completed", {
            "ended_reason":  ended_reason,
            "recording_url": recording_url,
            "summary":       summary,
            "transcript":    transcript,
            "call_outcome":  call_outcome,
            "cost_info":     {"total_cost": call_cost},
        })

        # ── CA trunk fallback: retry once via Ontario if Aria hit a SIP/provider
        # fault (never a real "prospect didn't answer" outcome — the call never
        # connected). One retry only, guarded by a lead_activities marker so a
        # second Ontario failure doesn't loop.
        phone_number_id_used = call.get("phoneNumberId", "")
        aria_ca_id    = os.getenv("VAPI_CA_PHONE_NUMBER_ID", "a513803a-5229-4ac1-881d-6c89ae708738")
        ontario_ca_id = os.getenv("VAPI_CA_ONTARIO_PHONE_NUMBER_ID", "94e7fccf-03c2-4442-a99b-d992b01b3a2f")
        is_provider_fault = ended_reason.startswith("call.in-progress.error-providerfault") or \
                             ended_reason.startswith("call.start.error")
        if is_provider_fault and phone_number_id_used == aria_ca_id:
            from database.client import get_client as _gc2
            existing = _gc2().table("lead_activities").select("id").eq("lead_id", lead_id).eq("type", "ca_fallback_retry").limit(1).execute()
            if not existing.data:
                try:
                    from agents.vapi_caller import place_sophie_call
                    from agents.voice_outreach import _get_script, _pricing_line
                    from agents.email_personalizer import detect_market
                    from database.client import get_lead_by_id
                    lead_rec = get_lead_by_id(lead_id)
                    if lead_rec and lead_rec.get("phone"):
                        script = _get_script(lead_rec.get("business_type", "").lower(), lead_rec.get("pain_signal", ""))
                        mkt = detect_market(lead_rec.get("phone", ""), lead_rec.get("address", "") or "")
                        retry_result = place_sophie_call(
                            phone=lead_rec["phone"],
                            business_name=lead_rec.get("name", ""),
                            business_type=lead_rec.get("business_type", ""),
                            city=lead_rec.get("city", ""),
                            opener=script.get("firstMessage", ""),
                            insight=script.get("insight", ""),
                            pain_question=script.get("pain_question", ""),
                            lead_id=lead_id,
                            phone_number_id=ontario_ca_id,
                            pain_signal=lead_rec.get("pain_signal", "") or "",
                            pain_finding=lead_rec.get("pain_finding", "") or "",
                            pricing_line=_pricing_line(mkt),
                            address=lead_rec.get("address", ""),
                        )
                        log_activity(lead_id, "ca_fallback_retry", {
                            "reason": ended_reason,
                            "retry_vapi_call_id": retry_result.get("id", ""),
                            "retry_number_id": ontario_ca_id,
                        })
                        log.info("CA fallback: retried lead %s via Ontario after Aria %s", lead_id, ended_reason)
                except Exception as exc:
                    log.warning("CA fallback retry failed for lead %s: %s", lead_id, exc)

        # ── Route by extracted call_outcome (mirrors dograh_webhook) ───────────
        if call_outcome == "booked_demo":
            booking_result = _handle_book_demo(
                lead_id=lead_id,
                preferred_time=demo_preferred_time,
                attendee_email=attendee_email,
                attendee_name=contact_name,
            )
            _notify_call_outcome(
                lead_id, "booked_demo", recording_url, summary,
                extra_line=booking_result,
            )

        elif call_outcome == "callback_scheduled":
            from agents.cal_booking import parse_preferred_time
            from utils.timezone import get_tz_name
            from database.client import get_lead_by_id
            lead_rec = get_lead_by_id(lead_id)
            tz = get_tz_name(
                lead_rec.get("city", "") if lead_rec else "",
                lead_rec.get("market", "") if lead_rec else "",
            )
            try:
                callback_dt = parse_preferred_time(f"{callback_day} {callback_time_str}", tz)
                log_activity(lead_id, "callback_scheduled", {
                    "callback_at":    callback_dt.isoformat(),
                    "preferred_day":  callback_day,
                    "preferred_time": callback_time_str,
                })
                _notify_call_outcome(
                    lead_id, "callback_scheduled", recording_url, summary,
                    extra_line=f"Call back: {callback_day} {callback_time_str}",
                )
            except Exception as exc:
                log.warning("Could not parse callback time '%s %s': %s", callback_day, callback_time_str, exc)
                _notify_call_outcome(
                    lead_id, "callback_scheduled", recording_url, summary,
                    extra_line=f"Call back: {callback_day} {callback_time_str} (unparsed)",
                )

        elif call_outcome == "callback_requested":
            update_lead(lead_id, {"callback_requested": True})
            log_activity(lead_id, "callback_requested", {
                "source": "vapi_outbound",
                "note": "Prospect requested human callback during Sophie call",
            })
            _notify_call_outcome(
                lead_id, "callback_requested", recording_url, summary,
                extra_line="They want a human call — please follow up.",
            )

        elif call_outcome == "not_interested":
            update_lead(lead_id, {"status": "dead"})
            _notify_call_outcome(lead_id, "not_interested", recording_url, summary)

        elif call_outcome == "booked_demo_manually":
            update_lead(lead_id, {"status": "converted"})
            log_activity(lead_id, "booked_demo_manually", {
                "source": "vapi_outbound",
                "note": "Sophie booked the demo manually mid-call",
            })
            _notify_call_outcome(lead_id, "booked_demo_manually", recording_url, summary)

        return {"ok": True}

    # ── Inbound Henry call ────────────────────────────────────────────────────
    lead = _find_lead_by_phone(customer_phone)
    if not lead:
        return {"ok": True}
    lead_id = str(lead["id"])
    update_lead(lead_id, {
        "status": "replied",
        "notes": f"Inbound call via Henry. Ended: {ended_reason}. Recording: {recording_url}",
    })
    log_activity(lead_id, "inbound_call", {
        "caller":        customer_phone,
        "ended_reason":  ended_reason,
        "recording_url": recording_url,
        "summary":       summary,
        "transcript":    transcript,
    })
    return {"ok": True}


# ── Dograh webhook (end-of-call for both outbound Sophie and inbound Henry) ────

def _find_lead_by_phone(phone: str) -> dict | None:
    """Fuzzy-match a phone number against the leads table. Returns the lead row or None."""
    if not phone:
        return None
    from database.client import get_client
    db = get_client()
    digits = "".join(c for c in phone if c.isdigit())
    result = db.table("leads").select("id, name, status, phone, city, market").or_(
        f"phone.eq.{phone},phone.ilike.%{digits[-9:]}%"
    ).limit(1).execute()
    return result.data[0] if result.data else None


@app.post("/api/webhooks/dograh")
async def dograh_webhook(request: Request):
    payload         = await request.json()

    # Debug: persist raw payload so we can inspect what Dograh actually sends
    try:
        from database.client import get_client as _gc
        from datetime import datetime, timezone as _tz
        _gc().table("settings").upsert({
            "key": "dograh_last_webhook_payload",
            "value": json.dumps(payload),
            "updated_at": datetime.now(_tz.utc).isoformat(),
        }).execute()
    except Exception:
        pass

    # Dograh sends a FLAT payload — initial_context and gathered_context fields
    # are merged into the top level, not nested.
    workflow_run_id = str(payload.get("workflow_run_id", ""))
    recording_url   = payload.get("recording_url", "")
    transcript_url  = payload.get("transcript_url", "")

    # Fields we put in initial_context come back at top level
    lead_id      = str(payload.get("lead_id", ""))
    caller_phone = str(payload.get("phone_number", "") or payload.get("caller_number", "") or "")

    # Fields from gathered_context also come back at top level
    call_outcome       = payload.get("call_outcome", "") or "unknown"
    demo_preferred_time = payload.get("demo_preferred_time", "")
    attendee_email      = payload.get("attendee_email", "")
    contact_name        = payload.get("contact_name", "")
    callback_day        = payload.get("callback_day", "")
    callback_time_str   = payload.get("callback_time", "")
    summary             = str(payload.get("summary", ""))[:500]

    # Clear from live-call dashboard tracker
    _active_calls.pop(workflow_run_id, None)

    is_inbound = not lead_id

    # Henry/Priya inbound: look up lead by caller phone number
    if is_inbound:
        lead = _find_lead_by_phone(caller_phone) if caller_phone else None
        lead_id = str(lead["id"]) if lead else ""

    if not lead_id:
        return {"ok": True}

    from database.client import update_lead, log_activity

    # ── Henry/Priya inbound — set replied, log call, done ────────────────────
    if is_inbound:
        update_lead(lead_id, {"status": "replied"})
        log_activity(lead_id, "inbound_call", {
            "dograh_run_id":  workflow_run_id,
            "caller_number":  caller_phone,
            "recording_url":  recording_url,
            "transcript_url": transcript_url,
            "summary":        summary,
        })
        return {"ok": True}

    # ── Sophie outbound — route by extracted call_outcome ────────────────────
    if call_outcome == "booked_demo":
        booking_result = _handle_book_demo(
            lead_id=lead_id,
            preferred_time=demo_preferred_time,
            attendee_email=attendee_email,
            attendee_name=contact_name,
        )
        _notify_call_outcome(
            lead_id, "booked_demo", recording_url, summary,
            extra_line=booking_result,
        )

    elif call_outcome == "callback_scheduled":
        from agents.cal_booking import parse_preferred_time
        from utils.timezone import get_tz_name
        from database.client import get_lead_by_id
        lead_rec = get_lead_by_id(lead_id)
        tz = get_tz_name(
            lead_rec.get("city", "") if lead_rec else "",
            lead_rec.get("market", "") if lead_rec else "",
        )
        try:
            callback_dt = parse_preferred_time(f"{callback_day} {callback_time_str}", tz)
            log_activity(lead_id, "callback_scheduled", {
                "callback_at":    callback_dt.isoformat(),
                "preferred_day":  callback_day,
                "preferred_time": callback_time_str,
            })
            _notify_call_outcome(
                lead_id, "callback_scheduled", recording_url, summary,
                extra_line=f"Call back: {callback_day} {callback_time_str}",
            )
        except Exception as exc:
            log.warning("Could not parse callback time '%s %s': %s", callback_day, callback_time_str, exc)
            _notify_call_outcome(
                lead_id, "callback_scheduled", recording_url, summary,
                extra_line=f"Call back: {callback_day} {callback_time_str} (unparsed)",
            )

    elif call_outcome == "callback_requested":
        update_lead(lead_id, {"callback_requested": True})
        log_activity(lead_id, "callback_requested", {
            "source": "dograh_outbound",
            "note": "Prospect requested human callback during Sophie call",
        })
        _notify_call_outcome(
            lead_id, "callback_requested", recording_url, summary,
            extra_line="They want a human call — please follow up.",
        )

    elif call_outcome == "not_interested":
        update_lead(lead_id, {"status": "dead"})
        _notify_call_outcome(lead_id, "not_interested", recording_url, summary)

    elif call_outcome == "booked_demo_manually":
        update_lead(lead_id, {"status": "converted"})
        log_activity(lead_id, "booked_demo_manually", {
            "source": "dograh_outbound",
            "note": "Sophie booked the demo manually mid-call",
        })
        _notify_call_outcome(lead_id, "booked_demo_manually", recording_url, summary)

    # ── Always log Sophie completion ──────────────────────────────────────────
    log_activity(lead_id, "outbound_call_completed", {
        "dograh_run_id":  workflow_run_id,
        "call_outcome":   call_outcome,
        "recording_url":  recording_url,
        "transcript_url": transcript_url,
        "summary":        summary,
    })

    return {"ok": True}


def _handle_book_demo(
    lead_id: str,
    preferred_time: str = "",
    attendee_email: str = "",
    attendee_name: str = "",
) -> str:
    """Book a Cal.com demo slot and send WhatsApp confirmation. Called post-call from Dograh webhook."""
    try:
        from agents.cal_booking import book_demo, send_booking_whatsapp
        from database.client import get_lead_by_id, log_activity

        lead = get_lead_by_id(lead_id) if lead_id else None
        name  = attendee_name or (lead.get("name", "") if lead else "")
        email = attendee_email or (lead.get("email", "") if lead else "")
        phone = lead.get("phone", "") if lead else ""

        from utils.timezone import get_tz_name
        tz = get_tz_name(
            lead.get("city", "") if lead else "",
            lead.get("market", "") if lead else "",
        )

        if not email:
            return "No email — could not auto-book. Prospect should visit cal.com/practicedesk."

        result = book_demo(
            attendee_name=name,
            attendee_email=email,
            preferred_time=preferred_time,
            attendee_phone=phone,
            attendee_tz=tz,
        )

        if result["ok"]:
            from datetime import datetime
            start_iso = result["start_time"]
            try:
                dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
                import pytz as _pytz
                dt_local = dt.astimezone(_pytz.timezone(tz))
                friendly = dt_local.strftime("%A, %d %b at %-I:%M %p %Z")
            except Exception:
                friendly = start_iso

            send_booking_whatsapp(phone, name, friendly)

            if lead_id:
                from database.client import update_lead as _update_lead
                _update_lead(lead_id, {
                    "demo_booked":    True,
                    "demo_booked_at": start_iso,
                    "status":         "converted",
                })
                log_activity(lead_id, "demo_booked", {
                    "start_time":    start_iso,
                    "booking_uid":   result.get("booking_uid"),
                    "attendee_email": email,
                })

            return (
                f"Booking confirmed for {friendly}. "
                f"Meeting link: {result.get('meeting_url', 'cal.com/practicedesk')}."
            )
        else:
            return (
                f"Auto-booking failed ({result.get('error', 'unknown error')}). "
                f"Prospect should visit cal.com/practicedesk."
            )
    except Exception as exc:
        return f"Booking failed: {exc}."


_CALL_OUTCOME_LABELS = {
    "booked_demo":          "🎉 Demo booked",
    "callback_scheduled":   "📞 Callback scheduled",
    "callback_requested":   "📞 Callback requested",
    "not_interested":       "❌ Not interested",
    "booked_demo_manually": "🎉 Demo booked (manual)",
}


def _notify_call_outcome(
    lead_id: str,
    outcome: str,
    recording_url: str = "",
    summary: str = "",
    extra_line: str = "",
) -> None:
    """Notify Neeraj (email always-on + WA approved template) for any actionable Sophie call outcome."""
    try:
        from database.client import get_client
        from utils.notifier import notify_founder
        db = get_client()
        lead = db.table("leads").select("name, phone, business_type, city").eq("id", lead_id).single().execute().data
        if not lead:
            return

        label = _CALL_OUTCOME_LABELS.get(outcome, outcome)
        lead_line = f"{lead['name']} · {lead['phone']} · {lead.get('business_type', '')} · {lead.get('city', '')}"
        notify_founder(
            kind="call_outcome",
            label=label,
            lead_line=lead_line,
            detail=extra_line,
            summary=summary,
            recording_url=recording_url,
        )
    except Exception:
        pass  # notification is best-effort


# ── Cron: email sequence (called by Railway scheduled job) ────────────────────

@app.post("/api/cron/email-sequence")
async def cron_email_sequence(request: Request):
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")
    # Delegate to the same logic as the manual campaign
    from database.client import (
        get_leads_due_for_email, advance_email_sequence,
        log_activity, save_campaign_run, save_email_send, EMAIL_SEQUENCE, email_sequence_cap,
    )
    from agents.email_personalizer import generate_email, detect_market
    from agents.email_sender import send_email
    from utils.timezone import is_email_window, window_description

    from agents.email_sender import QuotaExceededError

    candidates = get_leads_due_for_email(limit=150)
    leads = _gate_casl_ca(candidates)
    sent = skipped = failed = 0

    run_record = save_campaign_run({
        "type": "email", "business_type": "all", "city": "all",
        "max_prospects": len(leads), "mode": "cron",
        "prospects_found": len(leads), "new_leads": 0,
        "messages_sent": 0, "emails_sent": 0, "log": "Cron in progress…",
    })
    run_id = run_record["id"] if run_record else None

    for lead in leads:
        if not (lead.get("business_type") or "").strip():
            skipped += 1
            log.info("email: skipped %s — no business_type", lead.get("name", lead.get("id")))
            continue
        city   = lead.get("city", "")
        market = detect_market(lead.get("phone", ""), lead.get("address", ""))
        if not is_email_window(city, market):
            skipped += 1
            continue

        current_step = lead.get("email_sequence_step") or 0
        next_step    = current_step + 1
        seq_cap      = email_sequence_cap(lead)
        if next_step > seq_cap:
            skipped += 1
            continue

        email_num, _ = EMAIL_SEQUENCE[next_step - 1]
        try:
            subject, html, email_num_used, variant = generate_email(lead, email_number=email_num)
            send_result = send_email(lead["email"], subject, html)
            resend_id   = (send_result or {}).get("id", "")
            if resend_id and run_id:
                save_email_send(lead["id"], run_id, resend_id, email_num_used, next_step, market=market)
            advance_email_sequence(lead["id"], next_step, sequence_length=seq_cap)
            log_activity(lead["id"], "email_sent", {
                "email_number": email_num_used,
                "variant": variant,
                "sequence_step": next_step,
                "trigger": "cron",
            })
            sent += 1
        except QuotaExceededError:
            break  # remaining leads will be retried next cron run
        except Exception:
            failed += 1

    try:
        save_campaign_run({
            "type": "email",
            "business_type": "all",
            "city": "all",
            "max_prospects": len(leads),
            "mode": "cron",
            "prospects_found": len(leads),
            "new_leads": 0,
            "messages_sent": 0,
            "emails_sent": sent,
            "log": f"Cron: Sent={sent} Skipped={skipped} Failed={failed}",
        })
    except Exception:
        pass

    return {"sent": sent, "skipped": skipped, "failed": failed, "total": len(leads)}


@app.patch("/api/leads/{lead_id}")
async def patch_lead(lead_id: str, body: LeadUpdate, _=Depends(verify_token)):
    from database.client import update_lead
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = update_lead(lead_id, changes)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result


@app.delete("/api/leads/{lead_id}")
async def remove_lead(lead_id: str, _=Depends(verify_token)):
    from database.client import delete_lead
    delete_lead(lead_id)
    return {"ok": True}


@app.get("/api/leads/{lead_id}/activities")
async def get_lead_activities(lead_id: str, _=Depends(verify_token)):
    from database.client import get_client
    result = (
        get_client()
        .table("lead_activities")
        .select("id, type, detail, created_at")
        .eq("lead_id", lead_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"data": result.data or []}


@app.get("/api/ceo-report")
async def get_ceo_report(_=Depends(verify_token)):
    """
    Every genuinely actionable outbound-call outcome (a live person engaged, not just a
    dial/voicemail), with the full transcript, summary and recording matched in, plus
    whether a scheduled callback has actually been followed up on yet.
    """
    from datetime import datetime, timezone
    from collections import defaultdict
    from database.client import get_client
    db = get_client()

    def _parse(ts: str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    outcome_types = ["callback_scheduled", "callback_requested", "booked_demo", "booked_demo_manually"]
    outcomes = (
        db.table("lead_activities")
        .select("id, lead_id, type, detail, created_at")
        .in_("type", outcome_types)
        .order("created_at", desc=True)
        .execute().data or []
    )
    if not outcomes:
        return {"data": []}

    lead_ids = list({str(o["lead_id"]) for o in outcomes})

    leads_rows = (
        db.table("leads")
        .select("id, name, phone, email, city, business_type, status")
        .in_("id", lead_ids)
        .execute().data or []
    )
    lead_map = {str(r["id"]): r for r in leads_rows}

    completed_rows = (
        db.table("lead_activities")
        .select("id, lead_id, detail, created_at")
        .eq("type", "outbound_call_completed")
        .in_("lead_id", lead_ids)
        .order("created_at")
        .execute().data or []
    )
    completed_by_lead = defaultdict(list)
    for c in completed_rows:
        completed_by_lead[str(c["lead_id"])].append(c)

    call_rows = (
        db.table("lead_activities")
        .select("lead_id, created_at")
        .eq("type", "outbound_call")
        .in_("lead_id", lead_ids)
        .order("created_at")
        .execute().data or []
    )
    calls_by_lead = defaultdict(list)
    for c in call_rows:
        calls_by_lead[str(c["lead_id"])].append(_parse(c["created_at"]))

    rows = []
    for o in outcomes:
        lid = str(o["lead_id"])
        lead = lead_map.get(lid, {})
        detail = o.get("detail") or {}
        o_time = _parse(o["created_at"])

        # The completed-call row (with transcript/summary/recording) lands a few
        # seconds after the outcome row for the same Dograh call — match by proximity.
        matched = {}
        for c in completed_by_lead.get(lid, []):
            c_time = _parse(c["created_at"])
            if 0 <= (c_time - o_time).total_seconds() <= 120:
                matched = c.get("detail") or {}
                break

        callback_at = detail.get("callback_at", "")
        followed_up = False
        if callback_at:
            try:
                cb_dt = _parse(callback_at)
                followed_up = any(t > cb_dt for t in calls_by_lead.get(lid, []))
            except Exception:
                pass

        rows.append({
            "activity_id":     o["id"],
            "lead_id":         lid,
            "lead_name":       lead.get("name", "Unknown"),
            "phone":           lead.get("phone", ""),
            "email":           lead.get("email", ""),
            "city":            lead.get("city", ""),
            "business_type":   lead.get("business_type", ""),
            "lead_status":     lead.get("status", ""),
            "outcome":         o["type"],
            "callback_at":     callback_at,
            "preferred_day":   detail.get("preferred_day", ""),
            "preferred_time":  detail.get("preferred_time", ""),
            "summary":         matched.get("summary", ""),
            "transcript":      matched.get("transcript", ""),
            "recording_url":   matched.get("recording_url", ""),
            "ended_reason":    matched.get("ended_reason", ""),
            "followed_up":     followed_up,
            "occurred_at":     o["created_at"],
        })

    return {"data": rows}


@app.get("/api/call-sessions")
async def get_call_sessions(
    limit: int = 100,
    offset: int = 0,
    _=Depends(verify_token),
):
    """Return all call events joined with lead details, newest first."""
    from database.client import get_client
    db = get_client()

    call_types = ["voice_followup_placed", "outbound_call", "inbound_call", "voice_followup_outcome"]

    acts = (
        db.table("lead_activities")
        .select("id, lead_id, type, detail, created_at")
        .in_("type", call_types)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
        .data or []
    )

    if not acts:
        return {"data": [], "total": 0}

    lead_ids = list({str(a["lead_id"]) for a in acts})
    leads_rows = (
        db.table("leads")
        .select("id, name, phone, city, business_type, status")
        .in_("id", lead_ids)
        .execute()
        .data or []
    )
    lead_map = {str(r["id"]): r for r in leads_rows}

    rows = []
    for a in acts:
        lead = lead_map.get(str(a["lead_id"]), {})
        detail = a.get("detail") or {}
        rows.append({
            "activity_id":   a["id"],
            "lead_id":       str(a["lead_id"]),
            "lead_name":     lead.get("name", "Unknown"),
            "phone":         lead.get("phone", detail.get("phone", "")),
            "city":          lead.get("city", ""),
            "business_type": lead.get("business_type", ""),
            "lead_status":   lead.get("status", ""),
            "call_type":     a["type"],
            "outcome":       detail.get("call_outcome") or detail.get("outcome") or "",
            "summary":       detail.get("summary", ""),
            "recording_url": detail.get("recording_url", ""),
            "dograh_run_id": detail.get("dograh_run_id", ""),
            "called_at":     a["created_at"],
        })

    total = (
        db.table("lead_activities")
        .select("id", count="exact")
        .in_("type", call_types)
        .execute()
        .count or 0
    )
    return {"data": rows, "total": total}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def stats(_=Depends(verify_token)):
    from database.client import get_stats
    return get_stats()


# ── Message preview & send ────────────────────────────────────────────────────

class PreviewRequest(BaseModel):
    lead_id: str


@app.post("/api/message/preview")
async def preview_message(body: PreviewRequest, _=Depends(verify_token)):
    from database.client import get_lead_by_id
    from agents.personalizer import generate_message

    lead = get_lead_by_id(body.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    message = generate_message(lead["name"], lead["business_type"], lead["city"])
    return {"message": message}


@app.post("/api/leads/{lead_id}/call")
async def call_lead(lead_id: str, _=Depends(verify_token)):
    from database.client import get_lead_by_id, update_lead
    from agents.voice_outreach import place_outbound_call
    from agents.email_personalizer import detect_market

    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("phone"):
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    market = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
    try:
        result = place_outbound_call(
            phone=lead["phone"],
            business_type=lead.get("business_type", ""),
            business_name=lead.get("name", ""),
            lead_id=lead_id,
            city=lead.get("city", ""),
            market=market,
            pain_signal=lead.get("pain_signal", "") or "",
            pain_finding=lead.get("pain_finding", "") or "",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    call_id = result.get("id", "")
    _track_active_call(call_id, lead_id, lead.get("name", ""), lead.get("phone", ""), "outbound")
    update_lead(lead_id, {"notes": f"Voice call placed — Vapi call ID: {call_id or 'unknown'}"})
    from database.client import log_activity
    log_activity(lead_id, "outbound_call", {
        "vapi_call_id": call_id,
        "trigger": "manual",
        "phone": lead.get("phone", ""),
    })
    return {"ok": True, "call_id": call_id}


@app.post("/api/dial")
async def dial_direct(payload: dict, _=Depends(verify_token)):
    """Place an outbound call to any phone number without requiring a Supabase lead.
    Used by LegalAidAI admin dashboard to call registered users directly.
    Body: { phone, name, business_type?, city? }
    """
    from agents.vapi_caller import place_sophie_call

    phone = (payload.get("phone") or "").strip()
    name  = (payload.get("name")  or "").strip()
    if not phone or not name:
        raise HTTPException(status_code=400, detail="phone and name are required")

    try:
        result = place_sophie_call(
            phone=phone,
            business_name=name,
            business_type=payload.get("business_type") or "lawyer",
            city=payload.get("city") or "",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    call_id = result.get("id", "")
    return {"ok": True, "call_id": call_id, "phone": phone, "name": name}


@app.post("/api/leads/{lead_id}/send")
async def send_to_lead(lead_id: str, _=Depends(verify_token)):
    from database.client import get_lead_by_id, mark_contacted
    from agents.personalizer import generate_message
    from agents.outreach import send_whatsapp_message

    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("phone"):
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    message = generate_message(lead["name"], lead["business_type"], lead["city"])
    send_whatsapp_message(lead["phone"], message)
    mark_contacted(lead_id, message)
    return {"ok": True, "message": message}


@app.post("/api/leads/{lead_id}/email")
async def email_lead(lead_id: str, _=Depends(verify_token)):
    from database.client import get_lead_by_id
    from agents.email_personalizer import generate_email
    from agents.email_sender import send_email

    from database.client import mark_emailed
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("email"):
        raise HTTPException(status_code=400, detail="Lead has no email address")

    subject, html, email_num, variant = generate_email(lead)
    send_email(lead["email"], subject, html)
    mark_emailed(lead_id)
    return {"ok": True, "subject": subject, "email_number": email_num, "variant": variant}


# ── Campaigns ─────────────────────────────────────────────────────────────────

@app.get("/api/campaigns")
async def list_campaigns(_=Depends(verify_token)):
    from database.client import get_campaigns
    return get_campaigns()


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    value: str


@app.get("/api/settings/{key}")
async def get_setting_endpoint(key: str, _=Depends(verify_token)):
    from database.client import get_setting
    value = get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": value}


@app.put("/api/settings/{key}")
async def put_setting(key: str, body: SettingUpdate, _=Depends(verify_token)):
    from database.client import save_setting
    save_setting(key, body.value)
    return {"key": key, "value": body.value}


# ── Templates ─────────────────────────────────────────────────────────────────

class TemplateSubmitRequest(BaseModel):
    name: str  # template name or "all"


@app.get("/api/templates")
async def list_template_statuses(_=Depends(verify_token)):
    from agents.template_manager import get_template_statuses
    return get_template_statuses()


@app.post("/api/templates/submit")
async def submit_templates(body: TemplateSubmitRequest, _=Depends(verify_token)):
    from agents.template_manager import submit_template, submit_all_templates
    if body.name == "all":
        return submit_all_templates()
    return [submit_template(body.name)]


# ── Email tracking ────────────────────────────────────────────────────────────

# 1x1 transparent GIF
_PIXEL = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
    b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00"
    b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
    b"\x44\x01\x00\x3b"
)


@app.get("/track/open/{lead_id}")
async def track_open(lead_id: str):
    from database.client import update_lead, log_activity, get_client
    from datetime import datetime, timezone
    try:
        lead = get_client().table("leads").select("email_opened").eq("id", lead_id).limit(1).execute()
        already = lead.data[0].get("email_opened") if lead.data else False
        ts = datetime.now(timezone.utc).isoformat()
        update_lead(lead_id, {"email_opened": True, "email_opened_at": ts})
        if not already:
            log_activity(lead_id, "email_opened", {"source": "pixel"})
    except Exception:
        pass
    return Response(content=_PIXEL, media_type="image/gif",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@app.get("/track/click/{lead_id}")
async def track_click(lead_id: str, url: str = "https://practicedesk.live"):
    from database.client import update_lead, log_activity, get_client
    from fastapi.responses import RedirectResponse
    from datetime import datetime, timezone
    try:
        lead = get_client().table("leads").select("email_opened, email_clicked").eq("id", lead_id).limit(1).execute()
        already_opened  = lead.data[0].get("email_opened")  if lead.data else False
        already_clicked = lead.data[0].get("email_clicked") if lead.data else False
        ts = datetime.now(timezone.utc).isoformat()
        patch = {
            "email_clicked": True, "email_opened": True,
            "email_clicked_at": ts, "email_opened_at": ts,
            "email_clicked_link": url,
        }
        update_lead(lead_id, patch)
        if not already_opened:
            log_activity(lead_id, "email_opened",  {"source": "pixel"})
        if not already_clicked:
            log_activity(lead_id, "email_clicked", {"source": "pixel", "url": url})
    except Exception:
        pass
    return RedirectResponse(url=url, status_code=302)


# ── Email template preview ───────────────────────────────────────────────────

@app.get("/api/preview/email")
async def preview_email(
    email_num: int = Query(1, ge=1, le=8),
    business_type: str = Query("dentist"),
    market: str = Query("US"),
    _=Depends(verify_token),
):
    from agents.email_personalizer import generate_email

    city_map = {"US": "Seattle", "CA": "Toronto", "AU": "Sydney"}
    city = city_map.get(market, "Toronto")
    phone_map = {"US": "+1 (206) 555-0123", "CA": "+1 (416) 555-0123", "AU": "+61 2 9555 0123"}

    sample_lead = {
        "id": "preview-000",
        "name": "Sunrise Dental",
        "business_type": business_type,
        "city": city,
        "address": f"123 Main St, {city}, {'ON M5V 2T6' if market == 'CA' else 'NSW 2000' if market == 'AU' else 'WA 98101'}",
        "phone": phone_map.get(market, "+1 (416) 555-0123"),
        "email": "info@sunrisedental.com",
        "website": "https://sunrisedental.com",
    }

    subject, html, email_number, variant = generate_email(sample_lead, email_number=email_num)
    return {"subject": subject, "html": html, "email_number": email_number, "variant": variant}


# ── Reporting ────────────────────────────────────────────────────────────────

@app.get("/api/agents/stats")
async def agents_stats(_=Depends(verify_token)):
    from database.client import get_client, get_stats

    db = get_client()
    all_runs = db.table("campaign_runs").select("*").order("created_at", desc=True).execute().data or []
    wa_runs = [r for r in all_runs if r.get("type") != "email"]
    em_runs = [r for r in all_runs if r.get("type") == "email"]

    lead_stats = get_stats()

    return {
        "running": _running,
        "pipeline": {
            "runs": len(wa_runs),
            "prospects_found": sum((r.get("prospects_found") or 0) for r in wa_runs),
            "new_leads": sum((r.get("new_leads") or 0) for r in wa_runs),
            "messages_sent": sum((r.get("messages_sent") or 0) for r in wa_runs),
            "last_run": wa_runs[0]["created_at"] if wa_runs else None,
            "recent_runs": wa_runs[:10],
        },
        "email_enrichment": {
            "total_leads": lead_stats["total_leads"],
            "with_email": sum(
                1 for r in (db.table("leads").select("email").execute().data or [])
                if r.get("email")
            ),
        },
        "email_campaign": {
            "runs": len(em_runs),
            "emails_sent": sum((r.get("emails_sent") or 0) for r in em_runs),
            "email_opened": lead_stats["email_opened"],
            "email_clicked": lead_stats["email_clicked"],
            "last_run": em_runs[0]["created_at"] if em_runs else None,
            "recent_runs": em_runs[:10],
        },
    }


@app.get("/api/products/stats")
async def products_stats(_=Depends(verify_token)):
    from database.client import get_stats
    stats = get_stats()
    return {
        "practicedesk": {
            "total_leads": stats["total_leads"],
            "emailed": stats["emailed"],
            "wa_sent": stats["wa_sent"],
            "opened": stats["email_opened"],
            "clicked": stats["email_clicked"],
            "replied": stats["replied"],
            "converted": stats["converted"],
            "by_vertical": stats["by_business_type"],
            "by_city": stats["by_city"],
        }
    }


# ── SignalWire browser dialer ─────────────────────────────────────────────────

@app.get("/api/signalwire/token")
async def signalwire_token(_=Depends(verify_token)):
    space      = os.getenv("SIGNALWIRE_SPACE", "")
    project_id = os.getenv("SIGNALWIRE_PROJECT_ID", "")
    sw_token   = os.getenv("SIGNALWIRE_TOKEN", "")
    caller_id  = os.getenv("SIGNALWIRE_CALLER_ID", "+12086884760")
    if not all([space, project_id, sw_token]):
        raise HTTPException(status_code=500, detail="SIGNALWIRE_PROJECT_ID / SIGNALWIRE_TOKEN / SIGNALWIRE_SPACE not set")
    resp = requests.post(
        f"https://{space}/api/fabric/subscribers/tokens",
        auth=(project_id, sw_token),
        json={"reference": "practicedesk-dialpad@practicedesk.live", "expires_in": 3600},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(status_code=500, detail=f"SAT generation failed: {resp.text}")
    return {"token": resp.json()["token"], "space": space, "caller_id": caller_id}


# Module-level store for the pending dialpad call destination (single-user tool)
import time as _time_mod
_pending_dialpad: dict = {"to": "", "ts": 0.0}


class DialpadPrepareRequest(BaseModel):
    to: str

@app.post("/api/signalwire/prepare")
async def signalwire_prepare(req: DialpadPrepareRequest, _=Depends(verify_token)):
    """Store the PSTN destination so the /dialpad-swml webhook can retrieve it when
    SignalWire invokes it after the browser dials /public/practicedesk-dialpad."""
    global _pending_dialpad
    to_number = req.to if req.to.startswith('+') else f"+{req.to.lstrip('0')}"
    _pending_dialpad = {"to": to_number, "ts": _time_mod.time()}
    log.info("Dialpad prepare: dest=%s", to_number)
    return {"ok": True, "to": to_number}


@app.get("/api/signalwire/dialpad-swml")
@app.post("/api/signalwire/dialpad-swml")
async def signalwire_dialpad_swml(request: Request):
    """SWML webhook — SignalWire calls this when the browser dials /public/practicedesk-dialpad.
    Returns SWML that connects the incoming browser call to the pending PSTN destination.
    Every outbound sales call is recorded (record_call) so the audio can be reviewed later."""
    import json as _json
    from urllib.parse import quote as _quote
    caller_id = os.getenv("SIGNALWIRE_CALLER_ID", "+12086884760")
    base_url  = os.getenv("PUBLIC_BASE_URL", "https://serene-passion-production-cd82.up.railway.app")
    dest = _pending_dialpad.get("to", "")
    age  = _time_mod.time() - _pending_dialpad.get("ts", 0.0)
    log.info("dialpad-swml called: dest=%s age=%.1fs", dest, age)

    if not dest or age > 120:
        swml = {
            "version": "1.0.0",
            "sections": {"main": [{"play": {"url": "silence:1"}}, {"hangup": {}}]}
        }
    else:
        status_url = f"{base_url}/api/signalwire/recording-callback?to={_quote(dest)}"
        swml = {
            "version": "1.0.0",
            "sections": {
                "main": [
                    {
                        "record_call": {
                            "format": "mp3",
                            "stereo": True,
                            "status_url": status_url,
                        }
                    },
                    {
                        "connect": {
                            "from": caller_id,
                            "to":   dest,
                            "timeout": 60,
                        }
                    }
                ]
            }
        }
    return Response(content=_json.dumps(swml), media_type="application/json")


@app.get("/api/signalwire/recording-callback")
@app.post("/api/signalwire/recording-callback")
async def signalwire_recording_callback(request: Request, to: str = Query(default="")):
    """Best-effort capture of the record_call status callback for International-dialpad calls.
    SignalWire's exact payload shape isn't confirmed for record_call yet, so this parses both
    JSON and form bodies and checks several likely field-name variants. The raw payload is always
    logged so field mapping can be corrected after the first live call without guessing blind.
    The recording itself always lands in the SignalWire Space (Storage > Recordings) regardless
    of whether this callback fires or the fields below are recognised."""
    raw: dict = {}
    try:
        raw = await request.json()
    except Exception:
        try:
            form = await request.form()
            raw = dict(form)
        except Exception:
            raw = {}

    log.info("signalwire recording-callback: to=%s raw=%s", to, raw)

    def _first(*keys):
        for k in keys:
            v = raw.get(k)
            if v:
                return v
        return ""

    recording_url = _first("recording_url", "RecordingUrl", "url", "public_url", "media_url")
    duration       = _first("duration", "RecordingDuration", "call_duration")
    call_id        = _first("call_id", "CallSid", "id")

    if to:
        try:
            from database.client import get_lead_by_phone, log_activity
            lead = get_lead_by_phone(to)
            if lead:
                log_activity(lead["id"], "outbound_call", {
                    "channel":       "international_dialpad",
                    "dialed_number": to,
                    "recording_url": recording_url,
                    "duration":      duration,
                    "call_id":       call_id,
                    "raw":           raw,
                })
        except Exception:
            log.exception("signalwire recording-callback: failed to log activity")

    return {"ok": True}


class StartRecordingRequest(BaseModel):
    call_id: str
    to: str = ""


@app.post("/api/signalwire/start-recording")
async def signalwire_start_recording(req: StartRecordingRequest, _=Depends(verify_token)):
    """Starts recording on an already-connected International-dialpad call via the
    Compatibility REST API. Works regardless of how the call was dialed (direct PSTN
    dial via the Fabric SDK, not just calls routed through the dialpad-swml resource) —
    confirmed by probing a past Fabric-dialed call's id against this same endpoint and
    getting error 21220 (call not in-progress) rather than a not-found error."""
    from urllib.parse import quote as _quote
    space      = os.getenv("SIGNALWIRE_SPACE", "")
    project_id = os.getenv("SIGNALWIRE_PROJECT_ID", "")
    sw_token   = os.getenv("SIGNALWIRE_TOKEN", "")
    base_url   = os.getenv("PUBLIC_BASE_URL", "https://serene-passion-production-cd82.up.railway.app")
    if not all([space, project_id, sw_token]):
        raise HTTPException(status_code=500, detail="SIGNALWIRE_PROJECT_ID / SIGNALWIRE_TOKEN / SIGNALWIRE_SPACE not set")

    status_url = f"{base_url}/api/signalwire/recording-callback?to={_quote(req.to)}"
    resp = requests.post(
        f"https://{space}/api/laml/2010-04-01/Accounts/{project_id}/Calls/{req.call_id}/Recordings.json",
        auth=(project_id, sw_token),
        data={
            "RecordingChannels": "dual",
            "RecordingStatusCallback": status_url,
            "RecordingStatusCallbackEvent": "completed",
        },
        timeout=10,
    )
    log.info("start-recording: call_id=%s status=%s body=%s", req.call_id, resp.status_code, resp.text[:300])
    if not resp.ok:
        return {"ok": False, "status_code": resp.status_code, "error": resp.text}
    return {"ok": True, "recording": resp.json()}


@app.get("/api/signalwire/henry-inbound-swml")
@app.post("/api/signalwire/henry-inbound-swml")
async def henry_inbound_swml(request: Request):
    """TwiML endpoint: routes +12895141951 inbound calls to Vapi Claire via SIP Dial."""
    inbound_cred_id = os.getenv("VAPI_INBOUND_CREDENTIAL_ID", "bfbf497d-25ef-4670-a10f-cbd3d25ce0f5")
    dental_number   = os.getenv("VAPI_DENTAL_PHONE_NUMBER", "+12895141951")
    sip_uri = f"sip:{dental_number}@{inbound_cred_id}.sip.vapi.ai"
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Dial><Sip>{sip_uri}</Sip></Dial></Response>'
    return Response(content=twiml, media_type="application/xml")


@app.get("/api/signalwire/vapi-ca-outbound-swml")
@app.post("/api/signalwire/vapi-ca-outbound-swml")
async def vapi_ca_outbound_swml(request: Request):
    """
    SWML webhook for the CA (Alberta) SignalWire Domain Application. Mirrors the
    working Bright Smile Dental outbound script (resource 79839a02-6f5f-471e-8ed6-a7dd28524600):
    Vapi's byo-sip-trunk sends an authenticated INVITE to this Domain Application's
    SIP address; this SWML connects it out to the PSTN destination embedded in the
    original "to" URI, with +15872090343 forced as the caller ID.
    """
    import json as _json
    ca_number = os.getenv("VAPI_CA_PHONE_NUMBER", "+15872090343")
    swml = {
        "version": "1.0.0",
        "sections": {
            "main": [
                {
                    "connect": {
                        "answer_on_bridge": True,
                        "from": ca_number,
                        "to": '%{call.to.replace(/^sip:/i, "").replace(/@.*/, "")}',
                    }
                }
            ]
        },
    }
    return Response(content=_json.dumps(swml), media_type="application/json")


# Keep legacy Twilio endpoints as aliases during transition
@app.get("/api/twilio/token")
async def twilio_token(_=Depends(verify_token)):
    return await signalwire_token(_)



# ── Unsubscribe (public — no auth) ───────────────────────────────────────────

_UNSUB_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Unsubscribed — PracticeDesk</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, Helvetica, sans-serif; background: #f4f4f5;
           display: flex; align-items: center; justify-content: center;
           min-height: 100vh; padding: 24px; }
    .card { background: #fff; border-radius: 8px; padding: 48px 40px;
            max-width: 480px; width: 100%; text-align: center;
            box-shadow: 0 1px 6px rgba(0,0,0,0.08); }
    .icon { font-size: 40px; margin-bottom: 20px; }
    h1 { font-size: 20px; color: #111; margin-bottom: 10px; }
    p  { font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 8px; }
    a  { color: #4f46e5; text-decoration: none; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <h1>You've been unsubscribed</h1>
    <p>You won't receive any more emails from PracticeDesk at this address.</p>
    <p style="margin-top:20px;">Changed your mind?
      <a href="https://cal.com/neeraj-khattar-3zszap/practicedesk-demo">Book a demo anytime</a>
    </p>
  </div>
</body>
</html>"""


@app.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(id: str = Query(default="")):
    if id:
        try:
            from database.client import update_lead
            update_lead(id, {"status": "dead"})
        except Exception:
            pass
    return HTMLResponse(content=_UNSUB_PAGE, status_code=200)


# ── Resend backfill — sync open/click events from Resend API into DB ──────────

@app.post("/api/admin/resend-backfill", dependencies=[Depends(verify_token)])
async def resend_backfill(days_back: int = 3):
    """Pull open/click events from Resend for the last N days and update leads.
    Uses recipient email address as the join key (no email_sends lookup needed)."""
    import requests as _requests
    from datetime import datetime, timezone, timedelta
    from database.client import get_client, log_activity

    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not set")

    db = get_client()
    cutoff_str = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    opened_leads: list[str] = []
    clicked_leads: list[str] = []
    total_fetched = 0
    stop = False
    cursor: str | None = None

    def _fetch_page(after: str | None) -> dict:
        url = "https://api.resend.com/emails?limit=100"
        if after:
            url += f"&after={after}"
        r = _requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        r.raise_for_status()
        return r.json()

    while not stop:
        data   = await asyncio.to_thread(_fetch_page, cursor)
        emails = data.get("data", [])
        if not emails:
            break

        for em in emails:
            created = em.get("created_at", "")
            if created and created[:10] < cutoff_str:
                stop = True
                break

            event   = em.get("last_event", "")
            to_list = em.get("to", [])
            total_fetched += 1

            if event not in ("opened", "clicked") or not to_list:
                continue

            to_email = to_list[0].lower().strip()
            row = db.table("leads").select("id, email_opened, email_clicked").ilike("email", to_email).limit(1).execute()
            if not row.data:
                continue

            lead    = row.data[0]
            lead_id = str(lead["id"])
            updates: dict = {}

            if not lead.get("email_opened"):
                updates["email_opened"] = True
                opened_leads.append(lead_id)

            if event == "clicked" and not lead.get("email_clicked"):
                updates["email_clicked"] = True
                clicked_leads.append(lead_id)

            if updates:
                db.table("leads").update(updates).eq("id", lead_id).execute()
                activity_type = "email_clicked" if event == "clicked" else "email_opened"
                log_activity(lead_id, activity_type, {"source": "resend_backfill"})

        cursor = emails[-1]["id"] if emails else None
        if not data.get("has_more"):
            break

    return {
        "ok":             True,
        "total_fetched":  total_fetched,
        "opened_updated": len(opened_leads),
        "clicked_updated": len(clicked_leads),
    }


# ── Live Activity Monitor ─────────────────────────────────────────────────────

@app.get("/api/activity/live", dependencies=[Depends(verify_token)])
async def activity_live():
    """Real-time feed: recent activities, pending queues, next scheduled jobs."""
    from datetime import datetime, timezone, timedelta
    from database.client import get_client

    db      = get_client()
    now_utc = datetime.now(timezone.utc)

    # ── Recent activities (last 60 entries) ──────────────────────────────────
    acts_raw = (
        db.table("lead_activities")
        .select("id, lead_id, type, detail, created_at")
        .order("created_at", desc=True)
        .limit(60)
        .execute()
    ).data or []

    lead_ids = list({str(a["lead_id"]) for a in acts_raw if a.get("lead_id")})
    leads_map: dict = {}
    if lead_ids:
        rows = db.table("leads").select("id, name, business_type, city").in_("id", lead_ids[:50]).execute().data or []
        leads_map = {str(r["id"]): r for r in rows}

    activities = []
    for a in acts_raw:
        lead = leads_map.get(str(a["lead_id"])) if a.get("lead_id") else None
        activities.append({
            "id":            a["id"],
            "type":          a["type"],
            "detail":        a.get("detail"),
            "created_at":    a["created_at"],
            "lead_name":     lead["name"]          if lead else None,
            "business_type": lead["business_type"] if lead else None,
            "city":          lead["city"]           if lead else None,
        })

    # ── Pending queues ────────────────────────────────────────────────────────
    from collections import defaultdict
    from utils.timezone import is_voice_window, is_wa_window, CITY_TZ
    import pytz
    cutoff_3d = (now_utc - timedelta(days=3)).isoformat()
    cutoff_5d = (now_utc - timedelta(days=5)).isoformat()

    wa_sent_ids    = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "wa_followup_sent").execute().data or [])}
    voice_sent_ids = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "voice_followup_placed").execute().data or [])}
    email_clicked_ids = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "email_clicked").execute().data or [])}
    called_ids     = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").in_("type", ["outbound_call", "voice_followup_placed"]).execute().data or [])}

    wa_cands   = db.table("leads").select("id, city").eq("status", "contacted").eq("outreach_sent", True).lte("outreach_date", cutoff_3d).execute().data or []
    vox_cands  = db.table("leads").select("id").eq("status", "contacted").eq("outreach_sent", True).lte("outreach_date", cutoff_5d).execute().data or []

    voice_pending = len([l for l in vox_cands if str(l["id"]) not in voice_sent_ids])

    # WA follow-up — city breakdown
    wa_followup_by_city: dict[str, int] = defaultdict(int)
    for l in wa_cands:
        if str(l["id"]) not in wa_sent_ids:
            wa_followup_by_city[l.get("city", "unknown")] += 1
    wa_pending = sum(wa_followup_by_city.values())

    # WA broadcast — city breakdown (new uncontacted leads)
    from agents.wa_broadcast import pending_by_city as _broadcast_by_city
    wa_broadcast_by_city = _broadcast_by_city()
    wa_broadcast_total = sum(wa_broadcast_by_city.values())

    # Click calls — per-lead status
    click_pending_ids = email_clicked_ids - called_ids
    click_pending = len(click_pending_ids)
    click_leads: list[dict] = []
    if click_pending_ids:
        raw = db.table("leads").select("id, name, city, phone, business_type").in_("id", list(click_pending_ids)).not_.is_("phone", "null").neq("phone", "").execute().data or []
        for r in raw:
            city = r.get("city", "")
            tz_name = CITY_TZ.get(city, "")
            in_window = is_voice_window(city, "")
            if not in_window:
                if tz_name:
                    local_t = now_utc.astimezone(pytz.timezone(tz_name))
                    call_status = f"outside hours ({local_t.strftime('%H:%M')} {local_t.strftime('%Z')})"
                else:
                    call_status = "outside hours"
            else:
                call_status = "ready"
            click_leads.append({"id": str(r["id"]), "name": r.get("name",""), "city": city, "business_type": r.get("business_type",""), "call_status": call_status})

    email_due = db.table("leads").select("id", count="exact").not_.is_("email", "null").neq("email", "").not_.is_("email_sequence_step", "null").eq("status", "contacted").execute()
    email_pending = email_due.count or 0

    # ── Next scheduled fire times ─────────────────────────────────────────────
    def _next_daily(hour: int, minute: int) -> str:
        t = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if t <= now_utc:
            t += timedelta(days=1)
        return t.isoformat()

    def _next_hourly_runs(count: int = 6) -> list[str]:
        """Next N hourly fire times, Mon–Fri only."""
        runs, t = [], now_utc.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        while len(runs) < count:
            if t.weekday() < 5:
                runs.append(t.isoformat())
            t += timedelta(hours=1)
        return runs

    def _next_15min_runs(count: int = 4) -> list[str]:
        mins_to_add = 15 - (now_utc.minute % 15) or 15
        base = now_utc.replace(second=0, microsecond=0) + timedelta(minutes=mins_to_add)
        return [(base + timedelta(minutes=15 * i)).isoformat() for i in range(count)]

    def _next_email_campaign() -> str:
        candidates = []
        for h in [13, 15, 22]:
            t = now_utc.replace(hour=h, minute=0, second=0, microsecond=0)
            if t <= now_utc:
                t += timedelta(days=1)
            candidates.append(t)
        return min(candidates).isoformat()

    def _next_monday_6am() -> str:
        days_ahead = (7 - now_utc.weekday()) % 7
        t = now_utc.replace(hour=6, minute=0, second=0, microsecond=0)
        if days_ahead == 0 and t <= now_utc:
            days_ahead = 7
        return (t + timedelta(days=days_ahead)).isoformat()

    def _last_of(activity_type: str) -> str | None:
        row = (db.table("lead_activities")
               .select("created_at").eq("type", activity_type)
               .order("created_at", desc=True).limit(1).execute())
        return row.data[0]["created_at"] if row.data else None

    hourly_runs  = _next_hourly_runs(6)
    quarter_runs = _next_15min_runs(4)

    schedule = [
        {
            "job": "WA Outreach",
            "next_run": hourly_runs[0],
            "next_runs": hourly_runs,
            "queue": wa_broadcast_total + wa_pending,
            "broadcast_total": wa_broadcast_total,
            "broadcast_by_city": dict(sorted(wa_broadcast_by_city.items(), key=lambda x: -x[1])[:15]),
            "followup_total": wa_pending,
            "followup_by_city": dict(sorted(wa_followup_by_city.items(), key=lambda x: -x[1])[:15]),
            "frequency": "Hourly Mon–Fri",
            "last_ran": _last_of("wa_outreach_sent") or _last_of("wa_followup_sent"),
            "description": "Initial WA to new leads + follow-up to silent contacts (8:30am–7pm local)",
        },
        {
            "job": "Voice Follow-up",
            "next_run": _next_daily(9, 0),
            "next_runs": [_next_daily(9, 0)],
            "queue": voice_pending,
            "frequency": "Daily 9:00 UTC",
            "last_ran": _last_of("voice_followup_placed"),
            "description": "Sophie outbound call to leads silent 5+ days",
        },
        {
            "job": "Email Campaign",
            "next_run": _next_email_campaign(),
            "next_runs": [_next_email_campaign()],
            "queue": email_pending,
            "frequency": "13:00, 15:00 & 22:00 UTC",
            "last_ran": _last_of("email_campaign_auto"),
            "description": "Next email in 6-step drip sequence (CA 9am ET / US 11am ET / AU 8am AEST)",
        },
        {
            "job": "Sophie Click Calls",
            "next_run": hourly_runs[0],
            "next_runs": hourly_runs,
            "queue": click_pending,
            "leads": click_leads,
            "frequency": "Hourly Mon–Fri",
            "last_ran": _last_of("outbound_call"),
            "description": "Calls leads who clicked an email link (11am–5pm local time)",
        },
        {
            "job": "Callbacks",
            "next_run": quarter_runs[0],
            "next_runs": quarter_runs,
            "queue": 0,
            "frequency": "Every 15 min Mon–Fri",
            "last_ran": None,
            "description": "Processes Sophie-scheduled callbacks from previous calls",
        },
        {
            "job": "Observatory",
            "next_run": _next_daily(1, 30),
            "next_runs": [_next_daily(1, 30)],
            "queue": 0,
            "frequency": "Daily 1:30 UTC (7am IST)",
            "last_ran": _last_of("observatory_sent"),
            "description": "Daily cost + funnel digest → founder WhatsApp",
        },
        {
            "job": "Signal Weekly",
            "next_run": _next_monday_6am(),
            "next_runs": [_next_monday_6am()],
            "queue": 0,
            "frequency": "Monday 6:00 UTC",
            "last_ran": _last_of("signal_weekly_report"),
            "description": "Marketing Head: template scores, projections, A/B results",
        },
    ]

    return {
        "ok":          True,
        "server_time": now_utc.isoformat(),
        "recent":      activities,
        "queue": {
            "wa_followup":    wa_pending,
            "voice_followup": voice_pending,
            "email":          email_pending,
            "click_calls":    click_pending,
        },
        "schedule": schedule,
    }


# ── Signal Agent endpoints ────────────────────────────────────────────────────

@app.post("/api/signal/score", dependencies=[Depends(verify_token)])
async def signal_score():
    """Trigger manual template scoring run."""
    from agents.signal import score_templates
    scores = score_templates()
    return {"ok": True, "scored": len(scores)}

@app.post("/api/signal/project", dependencies=[Depends(verify_token)])
async def signal_project(prospects_per_month: int = 50):
    """Recompute projections and persist them."""
    from agents.signal import generate_projections
    projs = generate_projections(prospects_per_month)
    return {"ok": True, "projections": len(projs)}

@app.get("/api/signal/funnel", dependencies=[Depends(verify_token)])
async def signal_funnel():
    """Return latest funnel metrics per vertical x country."""
    from database.client import get_client
    res = get_client().table("funnel_metrics").select("*").order("computed_at", desc=True).execute()
    return {"ok": True, "data": res.data or []}

@app.get("/api/signal/projections", dependencies=[Depends(verify_token)])
async def signal_projections():
    """Return latest projections per vertical x country x scenario."""
    from database.client import get_client
    res = get_client().table("projections").select("*").order("generated_at", desc=True).execute()
    return {"ok": True, "data": res.data or []}

@app.get("/api/signal/targets", dependencies=[Depends(verify_token)])
async def signal_targets():
    """Return all active targets with on_track / behind / missed status."""
    from database.client import get_client
    res = get_client().table("targets").select("*").order("updated_at", desc=True).execute()
    return {"ok": True, "data": res.data or []}

@app.get("/api/signal/dead-ends", dependencies=[Depends(verify_token)])
async def signal_dead_ends():
    """Return dead-end proposals Signal has raised."""
    from database.client import get_client
    res = (
        get_client().table("system_journal")
        .select("*")
        .eq("entry_type", "signal_dead_end_detected")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"ok": True, "data": res.data or []}

@app.get("/api/signal/report", dependencies=[Depends(verify_token)])
async def signal_report():
    """Return the latest Signal weekly report from the journal."""
    from database.client import get_client
    res = (
        get_client().table("system_journal")
        .select("*")
        .eq("entry_type", "signal_weekly_report")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = res.data[0] if res.data else None
    return {"ok": True, "data": data}

@app.post("/api/signal/report/generate", dependencies=[Depends(verify_token)])
async def signal_report_generate():
    """Manually trigger a Signal weekly report and email it."""
    import traceback
    try:
        from agents.signal import generate_weekly_report, send_signal_email
        report = generate_weekly_report()
        email_ok = send_signal_email(report)
        return {
            "ok": True,
            "scores_computed": report.get("scores_computed", 0),
            "dead_ends": report.get("dead_ends", 0),
            "targets_behind": report.get("targets_behind", 0),
            "email_sent": email_ok,
            "brief": report.get("brief", ""),
        }
    except Exception as exc:
        tb = traceback.format_exc()
        log.error("Signal generate failed: %s\n%s", exc, tb)
        raise HTTPException(status_code=500, detail={"error": str(exc), "traceback": tb})


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_simple():
    return {"status": "ok", "v": "emma-1"}


@app.get("/my-ip")
async def my_ip(request: Request):
    """Returns Railway's outbound public IP by probing Vobiz SIP (for IP ACL setup)."""
    import re
    from agents.sip_bridge import _SIPClient
    import uuid

    try:
        client = _SIPClient()
        client.connect()
        msg, _ = client._invite_msg("+910000000001", uuid.uuid4().hex, uuid.uuid4().hex[:8])
        client._send(msg)
        resp = client._recv(8)
        client.close()
        # Vobiz echoes our public IP in "received=" on the Via header
        m = re.search(r"received=([^\s;>\r\n]+)", resp)
        ip = m.group(1) if m else "not found in SIP response"
        return {"railway_outbound_ip": ip, "add_this_to_vobiz_acl": True}
    except Exception as e:
        return {"error": str(e)}


# ── API health ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    checks: dict[str, bool] = {}

    # Supabase
    try:
        from database.client import get_client
        get_client().table("leads").select("id").limit(1).execute()
        checks["supabase"] = True
    except Exception:
        checks["supabase"] = False

    # Anthropic — raw HTTP, not the SDK (SDK version skew has previously caused
    # false "down" alerts; see utils/monitoring.py's probe_dependencies for the
    # same fix). 200/401 both mean the API is actually reachable.
    try:
        r = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key":         os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
            },
            timeout=8,
        )
        checks["anthropic"] = r.status_code in (200, 401)
    except Exception:
        checks["anthropic"] = False

    # Google Maps
    checks["google_maps"] = bool(os.getenv("GOOGLE_MAPS_API_KEY"))

    # WhatsApp
    checks["whatsapp"] = bool(os.getenv("OUTREACH_WA_PHONE_NUMBER_ID") and os.getenv("WHATSAPP_ACCESS_TOKEN"))

    return checks


@app.get("/health/deep")
async def health_deep():
    """
    Deep dependency probe + cadence check. No auth — safe for external monitors.
    Returns per-service status and list of overdue scheduler jobs.
    """
    from utils.monitoring import probe_dependencies, check_cadences
    deps    = await asyncio.to_thread(probe_dependencies)
    overdue = check_cadences()
    all_ok  = all(s["ok"] for s in deps.values()) and not overdue
    return {
        "status":       "ok" if all_ok else "degraded",
        "dependencies": deps,
        "overdue_jobs": overdue,
    }


# ── Anthropic spend (current month) ──────────────────────────────────────────

@app.get("/api/anthropic/spend")
async def anthropic_spend(_=Depends(verify_token)):
    """Return estimated Anthropic spend for the current calendar month via the usage API."""
    import asyncio
    import requests as req
    from datetime import date

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "total_usd": None}

    today = date.today()
    start = today.replace(day=1).isoformat()

    def _fetch():
        return req.get(
            "https://api.anthropic.com/v1/usage",
            params={"start_date": start, "end_date": today.isoformat()},
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=8,
        )

    try:
        r = await asyncio.to_thread(_fetch)
        if r.status_code == 200:
            data = r.json()
            total = sum(
                item.get("input_tokens", 0) * item.get("input_cost_per_token", 0)
                + item.get("output_tokens", 0) * item.get("output_cost_per_token", 0)
                for item in (data.get("data") or [])
            )
            return {"total_usd": round(total, 4), "source": "anthropic_usage_api"}
        return {"error": f"Usage API returned {r.status_code}", "total_usd": None}
    except Exception as exc:
        return {"error": str(exc), "total_usd": None}


# ── Danger zone ───────────────────────────────────────────────────────────────

@app.delete("/api/admin/leads")
async def danger_clear_leads(_=Depends(verify_token)):
    from database.client import clear_all_leads
    clear_all_leads()
    return {"ok": True}


@app.post("/api/admin/reset-outreach")
async def danger_reset_outreach(_=Depends(verify_token)):
    from database.client import reset_outreach_flags
    reset_outreach_flags()
    return {"ok": True}


@app.post("/api/admin/backfill-contacted")
async def backfill_contacted(_=Depends(verify_token)):
    """One-off: set status=contacted for any lead that has email_sent=true but status=new."""
    from database.client import get_client
    result = (
        get_client()
        .table("leads")
        .update({"status": "contacted"})
        .eq("status", "new")
        .eq("email_sent", True)
        .execute()
    )
    updated = len(result.data) if result.data else 0
    return {"ok": True, "updated": updated}


# ── Agent 11: Affiliate Tracker ───────────────────────────────────────────────

_AFFILIATE_INVITE_MSG = (
    "Hi {name}! I came across your Instagram (@{handle}) — great content for the legal community.\n\n"
    "We've built *Nyaya Saathi* — AI-powered legal research for Indian advocates. "
    "Fast, accurate case law search at ₹2,500/month (vs ₹25,000+ for SCC Online).\n\n"
    "We have an affiliate programme:\n"
    "• Share your referral link with fellow advocates\n"
    "• Earn *₹500 for every subscriber* you refer\n"
    "• Paid directly to your UPI every month, no cap\n\n"
    "Interested? Reply here and I'll set you up with a personalised referral link.\n\n"
    "— Neeraj, LegalAidAI"
)


@app.post("/api/affiliates/scrape", dependencies=[Depends(verify_token)])
async def affiliate_scrape(
    max_per_hashtag: int = Query(30, ge=5, le=100),
    min_followers:   int = Query(2000, ge=100),
    max_followers:   int = Query(500000, ge=1000),
):
    """SSE: scrape Instagram for legal influencer prospects. Streams lines in real time."""
    async def generate():
        import threading
        from agents.insta_scraper import scrape

        loop = asyncio.get_event_loop()
        q: asyncio.Queue = asyncio.Queue()
        _running["affiliate_scrape"] = {"started": _time.time()}

        def _run():
            try:
                for line in scrape(
                    max_per_query=max_per_hashtag,
                    min_followers=min_followers,
                    max_followers=max_followers,
                ):
                    loop.call_soon_threadsafe(q.put_nowait, ("log", line))
            except Exception as exc:
                loop.call_soon_threadsafe(q.put_nowait, ("error", str(exc)))
            finally:
                loop.call_soon_threadsafe(q.put_nowait, ("done", None))

        threading.Thread(target=_run, daemon=True).start()

        try:
            while True:
                kind, payload = await q.get()
                if kind == "log":
                    yield {"data": json.dumps({"type": "log", "line": payload})}
                elif kind == "error":
                    yield {"data": json.dumps({"type": "error", "message": payload})}
                    break
                elif kind == "done":
                    break
        finally:
            _running.pop("affiliate_scrape", None)

        yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(generate(), headers={"X-Accel-Buffering": "no"}, ping=20)


class AffiliateCreate(BaseModel):
    instagram_handle: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    follower_count: Optional[int] = None
    bio: Optional[str] = None
    upi_id: Optional[str] = None
    bar_enrollment: Optional[str] = None
    notes: Optional[str] = None


class AffiliateUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    upi_id: Optional[str] = None
    bar_enrollment: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OnboardRequest(BaseModel):
    upi_id: str
    bar_enrollment: Optional[str] = ""


class CommissionPaidRequest(BaseModel):
    notes: Optional[str] = ""


@app.get("/api/affiliates", dependencies=[Depends(verify_token)])
async def list_affiliates(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    from database.affiliate_client import get_affiliates
    return get_affiliates(status=status, limit=limit, offset=offset)


@app.post("/api/affiliates", dependencies=[Depends(verify_token)])
async def create_affiliate(body: AffiliateCreate):
    from database.affiliate_client import save_affiliate
    data = body.model_dump(exclude_none=True)
    data["source"] = "manual"
    result = save_affiliate(data)
    if not result:
        raise HTTPException(status_code=409, detail="Handle already exists")
    return result


@app.patch("/api/affiliates/{affiliate_id}", dependencies=[Depends(verify_token)])
async def patch_affiliate(affiliate_id: str, body: AffiliateUpdate):
    from database.affiliate_client import update_affiliate
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = update_affiliate(affiliate_id, changes)
    if not result:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    return result


@app.post("/api/affiliates/{affiliate_id}/invite", dependencies=[Depends(verify_token)])
async def invite_affiliate(affiliate_id: str):
    """Send a WA invite to a prospect. Marks status as 'invited'."""
    from database.affiliate_client import get_affiliate_by_id, update_affiliate
    from agents.outreach import send_whatsapp_message

    aff = get_affiliate_by_id(affiliate_id)
    if not aff:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    phone = aff.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="No phone number — cannot send WA")

    msg = _AFFILIATE_INVITE_MSG.format(
        name=aff.get("name") or aff.get("instagram_handle", ""),
        handle=aff.get("instagram_handle", ""),
    )

    # Send via India WA number (outreach to IN numbers)
    india_phone_id = os.getenv("INDIA_WA_PHONE_NUMBER_ID", os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", ""))
    import requests as _req
    wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    resp = _req.post(
        f"https://graph.facebook.com/v19.0/{india_phone_id}/messages",
        json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": msg},
        },
        headers={"Authorization": f"Bearer {wa_token}"},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"WA send failed: {resp.text}")

    from datetime import datetime, timezone
    update_affiliate(affiliate_id, {
        "status": "invited",
        "invited_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "message": msg}


@app.post("/api/affiliates/{affiliate_id}/onboard", dependencies=[Depends(verify_token)])
async def onboard_affiliate_endpoint(affiliate_id: str, body: OnboardRequest):
    """Promote prospect → active affiliate. Generates referral code."""
    from database.affiliate_client import onboard_affiliate
    result = onboard_affiliate(affiliate_id, body.upi_id, body.bar_enrollment or "")
    if not result:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    return result


@app.get("/api/affiliates/stats", dependencies=[Depends(verify_token)])
async def affiliate_stats():
    from database.affiliate_client import get_affiliate_stats
    return get_affiliate_stats()


@app.get("/api/affiliates/commissions", dependencies=[Depends(verify_token)])
async def list_commissions(status: Optional[str] = None):
    from database.affiliate_client import get_commissions
    return {"data": get_commissions(status=status)}


@app.post("/api/affiliates/commissions/{commission_id}/pay", dependencies=[Depends(verify_token)])
async def pay_commission(commission_id: str, body: CommissionPaidRequest):
    from database.affiliate_client import mark_commission_paid
    result = mark_commission_paid(commission_id, body.notes or "")
    if not result:
        raise HTTPException(status_code=404, detail="Commission not found")
    return result


# ── Scheduled jobs (APScheduler — runs inside the server process) ─────────────

async def _job_wa_followup():
    sent = failed = 0
    try:
        from agents.followup import generate_followup_message
        from agents.outreach import send_whatsapp_message
        from database.client import get_leads_for_followup, log_activity
        leads = get_leads_for_followup()
        for lead in leads:
            try:
                msg = generate_followup_message(
                    lead.get("name", ""), lead.get("business_type", "practice"), lead.get("city", "")
                )
                send_whatsapp_message(lead["phone"], msg)
                log_activity(lead["id"], "wa_followup_sent", {"message": msg})
                sent += 1
            except Exception as exc:
                log.error("WA followup failed for lead %s: %s", lead.get("id"), exc)
                failed += 1
            await asyncio.sleep(2)
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("wa_followup", {"sent": sent, "failed": failed})
    except Exception as exc:
        log.error("_job_wa_followup failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("wa_followup", exc)


async def _job_voice_followup():
    try:
        from agents.voice_outreach import place_outbound_call
        from agents.email_personalizer import detect_market
        from database.client import get_leads_for_voice_followup, log_activity
        leads = get_leads_for_voice_followup()
        placed = failed = 0

        # US/CA: _job_click_calls owns all voice for these markets (engagement-triggered).
        # Never double-call via this cold-followup path — skip US/CA entirely here.
        # (get_clicked_uncalled_leads deduplicates outbound_call+voice_followup_placed,
        #  but get_leads_for_voice_followup only excludes voice_followup_placed, so
        #  passing clicked US/CA leads through here would create duplicate calls.)
        for lead in leads:
            _mkt = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
            if _mkt in ("US", "CA"):
                log.info(
                    "voice_followup: skip %s — %s market (click_caller handles voice here)",
                    lead.get("name"), _mkt,
                )
                continue
            try:
                result = place_outbound_call(
                    phone=lead["phone"],
                    business_type=lead.get("business_type", ""),
                    business_name=lead.get("name", ""),
                    lead_id=str(lead["id"]),
                    city=lead.get("city", ""),
                    market=_mkt,
                    pain_signal=lead.get("pain_signal", "") or "",
                    pain_finding=lead.get("pain_finding", "") or "",
                )
                call_id = result.get("id", "")
                _track_active_call(call_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
                log_activity(lead["id"], "voice_followup_placed", {
                    "vapi_call_id": call_id,
                    "phone": lead["phone"],
                })
                placed += 1
            except Exception as exc:
                log.error("Voice followup failed for lead %s: %s", lead.get("id"), exc)
                failed += 1
            await asyncio.sleep(3)
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("voice_followup", {"placed": placed, "failed": failed})
    except Exception as exc:
        log.error("_job_voice_followup failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("voice_followup", exc)


async def _job_observatory():
    from agents.observatory import send_observatory_digest
    try:
        send_observatory_digest()  # stores to settings table + sends WA/email internally
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("observatory", {"digest_sent": True})
    except Exception as exc:
        log.error("Observatory job failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("observatory", exc)


async def _job_wa_broadcast():
    try:
        from agents.wa_broadcast import run_wa_broadcast
        result = await asyncio.to_thread(run_wa_broadcast)
        if result["sent"] > 0:
            from database.client import log_activity
            log_activity(None, "wa_outreach_sent", {
                "trigger": "broadcast_cron",
                "sent": result["sent"],
                "skipped": result["skipped_outside_hours"],
                "errors": result["errors"],
            })
        log.info("WA broadcast: %s", result)
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("wa_broadcast", {
            "sent": result.get("sent", 0),
            "skipped": result.get("skipped_outside_hours", 0),
            "errors": result.get("errors", 0),
        })
    except Exception as exc:
        log.error("_job_wa_broadcast failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("wa_broadcast", exc)


async def _job_click_calls():
    try:
        from agents.click_caller import run_click_campaign
        await asyncio.to_thread(run_click_campaign)
    except Exception as exc:
        log.error("_job_click_calls failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("click_calls", exc)


async def _job_scheduled_callbacks():
    """Call back leads who asked Sophie to call them at a specific time."""
    called = errors = 0
    try:
        from database.client import get_leads_due_callback, log_activity
        from agents.voice_outreach import place_outbound_call
        from agents.email_personalizer import detect_market
        from utils.timezone import is_voice_window
        leads = get_leads_due_callback()
        for lead in leads:
            # leads.market (DB column) is unpopulated for almost all leads —
            # compute fresh from phone+address instead of trusting it.
            _mkt = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
            if not is_voice_window(lead.get("city", ""), _mkt):
                continue
            if not lead.get("phone"):
                continue
            try:
                result = place_outbound_call(
                    phone=lead["phone"],
                    business_type=lead.get("business_type", ""),
                    business_name=lead.get("name", ""),
                    lead_id=str(lead["id"]),
                    city=lead.get("city", ""),
                    market=_mkt,
                    pain_signal=lead.get("pain_signal", "") or "",
                    pain_finding=lead.get("pain_finding", "") or "",
                )
                call_id = result.get("id", "")
                _track_active_call(call_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
                log_activity(str(lead["id"]), "outbound_call", {
                    "vapi_call_id": call_id,
                    "trigger": "scheduled_callback",
                    "phone": lead["phone"],
                })
                called += 1
            except Exception as exc:
                log.error("Scheduled callback failed for lead %s: %s", lead.get("id"), exc)
                errors += 1
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("scheduled_callbacks", {"called": called, "errors": errors})
    except Exception as exc:
        log.error("_job_scheduled_callbacks failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("scheduled_callbacks", exc)


_CASL_CA_DAILY_CAP = 30


def _gate_casl_ca(leads: list[dict]) -> list[dict]:
    """CASL requires Canada leads on a separate, lower-volume, consent-gated path:
    only publicly-scraped addresses (scrape_attempted=True, satisfying implied-consent
    under CASL s.10(9)(b)), capped at _CASL_CA_DAILY_CAP per UTC calendar day — counted
    against ALL email_sends today, not just this run, since this gate must be applied by
    every send path (manual, cron endpoint, and the scheduler) to hold as a real daily cap.
    """
    from database.client import get_emails_sent_today
    from agents.email_personalizer import detect_market

    already_sent_ca = get_emails_sent_today(market="CA")
    remaining_ca = max(0, _CASL_CA_DAILY_CAP - already_sent_ca)

    ca_leads, non_ca_leads = [], []
    for lead in leads:
        mkt = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
        if mkt == "CA":
            if lead.get("scrape_attempted"):
                ca_leads.append(lead)
        else:
            non_ca_leads.append(lead)
    return non_ca_leads + ca_leads[:remaining_ca]


async def _job_email_campaign():
    """Auto-send to leads due for their next sequence step. Resend's actual account
    quota is 150 emails/day (not enforced here — send_email() raises QuotaExceededError
    on Resend's own 429, which is what actually stops sending once the real cap hits)."""
    try:
        from database.client import (
            get_leads_due_for_email, advance_email_sequence,
            log_activity, save_campaign_run, save_email_send, EMAIL_SEQUENCE, email_sequence_cap,
        )
        from agents.email_personalizer import generate_email, detect_market
        from agents.email_sender import send_email, QuotaExceededError
        from utils.timezone import is_email_window

        all_candidates = get_leads_due_for_email(limit=250)
        leads = _gate_casl_ca(all_candidates)
        sent = skipped = failed = 0

        # Create a campaign run so email_sends records have a parent
        run_record = save_campaign_run({
            "type": "email", "business_type": "all", "city": "all",
            "max_prospects": len(leads), "mode": "scheduler",
            "prospects_found": len(leads), "new_leads": 0,
            "messages_sent": 0, "emails_sent": 0, "log": "Scheduler in progress…",
        })
        run_id = run_record["id"] if run_record else None

        for lead in leads:
            if not (lead.get("business_type") or "").strip():
                skipped += 1
                log.info("email: skipped %s — no business_type", lead.get("name", lead.get("id")))
                continue
            city   = lead.get("city", "")
            market = detect_market(lead.get("phone", ""), lead.get("address", ""))
            if not is_email_window(city, market):
                skipped += 1
                continue

            current_step = lead.get("email_sequence_step") or 0
            next_step    = current_step + 1
            seq_cap      = email_sequence_cap(lead)
            if next_step > seq_cap:
                skipped += 1
                continue

            email_num, _ = EMAIL_SEQUENCE[next_step - 1]
            try:
                subject, html, email_num_used, variant = generate_email(lead, email_number=email_num)
                send_result = send_email(lead["email"], subject, html)
                resend_id   = (send_result or {}).get("id", "")
                if resend_id and run_id:
                    save_email_send(lead["id"], run_id, resend_id, email_num_used, next_step, market=market)
                advance_email_sequence(lead["id"], next_step, sequence_length=seq_cap)
                log_activity(lead["id"], "email_sent", {
                    "email_number": email_num_used,
                    "variant": variant,
                    "sequence_step": next_step,
                    "trigger": "scheduler",
                })
                sent += 1
            except QuotaExceededError:
                break  # daily Resend quota (150) reached — remaining retried next run
            except Exception:
                failed += 1

        if sent or failed:
            save_campaign_run({
                "type": "email",
                "business_type": "all",
                "city": "all",
                "max_prospects": len(leads),
                "mode": "scheduler",
                "prospects_found": len(leads),
                "new_leads": 0,
                "messages_sent": 0,
                "emails_sent": sent,
                "log": f"Scheduler: Sent={sent} Skipped={skipped} Failed={failed}",
            })
        log_activity(None, "email_campaign_auto", {"sent": sent, "skipped": skipped, "failed": failed})  # lead_id=None is intentional system-level event

        # Threshold alert: >30% failure rate with meaningful sample
        total = sent + failed
        if total > 5 and failed / total > 0.30:
            try:
                from utils.notifier import notify_founder
                notify_founder(
                    kind="system_alert", severity="warning",
                    component="email_campaign",
                    reason=f"🟠 {failed}/{total} emails failed ({int(failed/total*100)}%) — check Resend quota or SMTP auth.",
                )
            except Exception:
                pass

        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("email_campaign", {"sent": sent, "skipped": skipped, "failed": failed})
    except Exception as exc:
        log.error("_job_email_campaign failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("email_campaign", exc)


async def _job_enrich_emails():
    """
    Auto-run email enrichment so new leads from prospecting get a real email
    address without anyone having to click "Run Pipeline" manually. Without this,
    leads pile up with scrape_attempted=False forever and are never eligible for
    the email campaign (get_leads_due_for_email requires a non-empty email).
    Mirrors the logic in POST /api/leads/enrich-emails, minus the SSE streaming.
    """
    try:
        from database.client import get_leads_for_enrichment, mark_scrape_attempted
        from agents.email_scraper import scrape_email_debug

        candidates = get_leads_for_enrichment()
        total = len(candidates)
        if total == 0:
            from utils.monitoring import upsert_heartbeat
            upsert_heartbeat("enrich_emails", {"enriched": 0, "total": 0})
            return

        async def _scrape_one(website: str) -> tuple[str | None, list[str]]:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(scrape_email_debug, website),
                    timeout=8,
                )
            except asyncio.TimeoutError:
                return None, ["timeout after 8s"]
            except Exception as exc:
                return None, [f"error: {exc}"]

        BATCH = 5
        enriched = 0
        for batch_start in range(0, total, BATCH):
            batch = candidates[batch_start:batch_start + BATCH]
            results = await asyncio.gather(*[_scrape_one(l["website"]) for l in batch])
            for lead, (email, _debug) in zip(batch, results):
                if email:
                    mark_scrape_attempted(lead["id"], email)
                    enriched += 1
                else:
                    mark_scrape_attempted(lead["id"], None)
            await asyncio.sleep(0)

        log.info("_job_enrich_emails: enriched %d/%d", enriched, total)
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("enrich_emails", {"enriched": enriched, "total": total})
    except Exception as exc:
        log.error("_job_enrich_emails failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("enrich_emails", exc)


async def _job_signal_weekly():
    """Signal weekly run — Monday 6am UTC. Scores templates, computes funnel,
    detects dead ends, generates projections, updates targets, writes brief, emails founder."""
    try:
        from agents.signal import generate_weekly_report, send_signal_email
        report = generate_weekly_report()
        log.info("Signal weekly report: %d scores, %d dead ends, %d targets behind",
                 report.get("scores_computed", 0),
                 report.get("dead_ends", 0),
                 report.get("targets_behind", 0))
        email_ok = send_signal_email(report)
        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("signal_weekly", {
            "scores_computed": report.get("scores_computed", 0),
            "dead_ends":       report.get("dead_ends", 0),
            "email_sent":      email_ok,
        })
    except Exception as exc:
        log.error("Signal weekly job failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("signal_weekly", exc)


async def _job_watchdog():
    """Hourly watchdog — cadence check + dependency probes + tiered alerts + auto-recovery."""
    try:
        from utils.monitoring import run_watchdog
        overdue = await asyncio.to_thread(run_watchdog)
        for job_name in (overdue or []):
            fn = _JOB_REGISTRY.get(job_name)
            if fn:
                log.warning("Watchdog: auto-recovering overdue job '%s'", job_name)
                asyncio.ensure_future(fn())
    except Exception as exc:
        log.error("_job_watchdog failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("watchdog", exc)


async def _job_prospect():
    """Daily 12:00 UTC prospecting cron — discovers new leads for configured types/cities.

    Reads config from Supabase settings table (keys seeded at deploy time):
      cron_prospect_enabled       — "true" / "false"  (default true if missing)
      cron_prospect_types         — comma-separated list e.g. "dentist,salon"
      cron_prospect_cities        — comma-separated list e.g. "Sydney,Toronto"
      cron_prospect_max           — max leads per type/city pass (default 10)
      cron_prospect_pairs_per_run — how many (type, city) pairs to process per run (default 1)
      cron_prospect_cursor        — JSON {"idx": ...} — rotates through pairs across runs
    """
    try:
        from database.client import get_setting, save_setting, save_lead, get_existing_place_ids
        from agents.prospector import find_businesses

        enabled = (get_setting("cron_prospect_enabled") or "true").lower()
        if enabled == "false":
            log.info("_job_prospect: disabled via settings")
            return

        types_raw     = get_setting("cron_prospect_types")         or "dentist"
        cities_raw    = get_setting("cron_prospect_cities")        or "Sydney"
        max_raw       = get_setting("cron_prospect_max")           or "10"
        per_run_raw   = get_setting("cron_prospect_pairs_per_run") or "1"
        cursor_raw    = get_setting("cron_prospect_cursor")

        types  = [t.strip() for t in types_raw.split(",") if t.strip()]
        cities = [c.strip() for c in cities_raw.split(",") if c.strip()]
        max_results  = int(max_raw)     if str(max_raw).isdigit()     else 10
        pairs_per_run = int(per_run_raw) if str(per_run_raw).isdigit() else 1

        # Parse cursor — tells us which (type, city) pair to start from this cycle
        try:
            cursor = json.loads(cursor_raw) if isinstance(cursor_raw, str) else (cursor_raw or {})
        except Exception:
            cursor = {}
        idx = int(cursor.get("idx", 0))

        # All (type, city) pairs — rotate through pairs_per_run of them per run
        pairs = [(t, c) for t in types for c in cities]
        if not pairs:
            return
        pairs_per_run = max(1, min(pairs_per_run, len(pairs)))

        total_new_leads = 0
        run_summary = []

        for step in range(pairs_per_run):
            pair_idx = (idx + step) % len(pairs)
            btype, city = pairs[pair_idx]

            log.info("_job_prospect: running %s in %s (pair %d/%d)", btype, city, pair_idx + 1, len(pairs))

            known_ids = await asyncio.to_thread(get_existing_place_ids, btype, city)
            businesses = await asyncio.to_thread(find_businesses, btype, city, max_results, known_ids)

            new_leads = 0
            for biz in businesses:
                lead_data = {
                    "name":               biz.get("name"),
                    "address":            biz.get("address"),
                    "place_id":           biz.get("place_id"),
                    "phone":              biz.get("phone"),
                    "website":            biz.get("website"),
                    "business_type":      btype,
                    "city":               city,
                    "status":             "new",
                    "outreach_sent":      False,
                    "pain_score":         biz.get("pain_score"),
                    "pain_signal":        biz.get("pain_signal"),
                    "pain_finding":       biz.get("pain_finding"),
                    "has_online_booking": biz.get("has_online_booking"),
                    "hours_json":         biz.get("hours_json"),
                }
                try:
                    result = await asyncio.to_thread(save_lead, lead_data)
                    if result:
                        new_leads += 1
                except Exception as exc:
                    log.warning("_job_prospect: save_lead failed for %s: %s", biz.get("name"), exc)

            log.info("_job_prospect: %s new leads for %s in %s", new_leads, btype, city)
            total_new_leads += new_leads
            run_summary.append({"type": btype, "city": city, "new_leads": new_leads})

        # Advance cursor past all pairs processed this run
        next_cursor = json.dumps({"idx": (idx + pairs_per_run) % len(pairs)})
        await asyncio.to_thread(save_setting, "cron_prospect_cursor", next_cursor)

        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("prospect_cron", {"new_leads": total_new_leads, "pairs": run_summary})
    except Exception as exc:
        log.error("_job_prospect failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("prospect_cron", exc)


async def _job_jobad_scout():
    """Daily job-ad scout — SerpAPI Google Jobs -> Places resolve -> pain_signal=job_ad_frontdesk (Change #11).

    Reads config from Supabase settings table:
      jobad_scout_enabled   — "true" / "false"  (default true if missing)
      jobad_cities          — comma-separated list (falls back to cron_prospect_cities — the CA list)
      jobad_cities_per_run  — how many cities to scout per run (default 1)
      jobad_cursor          — JSON {"idx": ...} — rotates through cities across runs
      jobad_gl              — SerpAPI country code for these cities (default "ca")
      jobad_max_days_recent — recency cutoff passed to is_recent() (default 30)
      jobad_monthly_limit   — SerpAPI searches/month budget for the alert threshold (default 250)
      jobad_calls_month     — "YYYY-MM" — auto-managed, resets jobad_calls_count on month rollover
      jobad_calls_count     — auto-managed running total of searches this month
    """
    try:
        from database.client import get_setting, save_setting
        from agents.ingest import ingest_job_ad_leads
        from agents import serpapi_client
        from datetime import datetime, timezone

        enabled = (get_setting("jobad_scout_enabled") or "true").lower()
        if enabled == "false":
            log.info("_job_jobad_scout: disabled via settings")
            return

        cities_raw    = get_setting("jobad_cities") or get_setting("cron_prospect_cities") or "Toronto"
        per_run_raw   = get_setting("jobad_cities_per_run") or "1"
        cursor_raw    = get_setting("jobad_cursor")
        gl            = get_setting("jobad_gl") or "ca"
        max_days      = int(get_setting("jobad_max_days_recent") or "30")
        monthly_limit = int(get_setting("jobad_monthly_limit") or "250")

        cities = [c.strip() for c in cities_raw.split(",") if c.strip()]
        if not cities:
            return
        cities_per_run = max(1, min(int(per_run_raw) if str(per_run_raw).isdigit() else 1, len(cities)))

        try:
            cursor = json.loads(cursor_raw) if isinstance(cursor_raw, str) else (cursor_raw or {})
        except Exception:
            cursor = {}
        idx = int(cursor.get("idx", 0))

        # Monthly quota bookkeeping — reset on month rollover
        month_key    = datetime.now(timezone.utc).strftime("%Y-%m")
        stored_month = get_setting("jobad_calls_month")
        stored_count = int(get_setting("jobad_calls_count") or "0")
        if stored_month != month_key:
            stored_month, stored_count = month_key, 0

        if stored_count >= monthly_limit:
            log.warning("_job_jobad_scout: monthly SerpAPI quota reached (%d/%d) — skipping", stored_count, monthly_limit)
            from utils.notifier import notify_founder
            notify_founder(kind="system_alert", severity="warning", component="jobad_scout",
                            reason=f"SerpAPI monthly quota reached ({stored_count}/{monthly_limit}) — scout paused until next month or raise jobad_monthly_limit.")
            await asyncio.to_thread(save_setting, "jobad_calls_month", stored_month)
            return

        calls_before = serpapi_client.calls_made()
        total_saved = total_skipped = total_unresolved = 0
        run_summary = []

        for step in range(cities_per_run):
            city = cities[(idx + step) % len(cities)]
            city_rows = []
            for vertical, queries in serpapi_client.JOBAD_QUERIES.items():
                for query in queries:
                    run_calls_so_far = serpapi_client.calls_made() - calls_before
                    if stored_count + run_calls_so_far >= monthly_limit:
                        break
                    jobs = await asyncio.to_thread(serpapi_client.search_jobs, query, city, gl=gl)
                    recent = [j for j in jobs if serpapi_client.is_recent(j.get("posted_at", ""), max_days)]
                    city_rows.extend(serpapi_client.to_ingest_rows(recent, vertical, city))

            result = {"saved": [], "skipped": [], "unresolved": []}
            if city_rows:
                result = await asyncio.to_thread(
                    ingest_job_ad_leads, city_rows,
                    dry_run=False, source="job_ad_serpapi",
                    pain_finding="actively hiring a front-desk receptionist",
                )
            total_saved      += len(result["saved"])
            total_skipped    += len(result["skipped"])
            total_unresolved += len(result["unresolved"])
            run_summary.append({"city": city, **{k: len(v) for k, v in result.items()}})

        await asyncio.to_thread(save_setting, "jobad_cursor", json.dumps({"idx": (idx + cities_per_run) % len(cities)}))

        run_calls = serpapi_client.calls_made() - calls_before
        new_count = stored_count + run_calls
        await asyncio.to_thread(save_setting, "jobad_calls_month", month_key)
        await asyncio.to_thread(save_setting, "jobad_calls_count", str(new_count))

        log.info("_job_jobad_scout: %d saved, %d skipped, %d unresolved — %d SerpAPI calls (%d/%d this month)",
                  total_saved, total_skipped, total_unresolved, run_calls, new_count, monthly_limit)

        # Quota guard — warn once when crossing 80%
        if new_count >= 0.8 * monthly_limit > stored_count:
            from utils.notifier import notify_founder
            notify_founder(kind="system_alert", severity="warning", component="jobad_scout",
                            reason=f"SerpAPI usage at {new_count}/{monthly_limit} searches this month (~{int(100*new_count/monthly_limit)}%) — nearing plan limit.")

        from utils.monitoring import upsert_heartbeat
        upsert_heartbeat("jobad_scout", {"saved": total_saved, "skipped": total_skipped,
                                          "unresolved": total_unresolved, "calls_this_run": run_calls,
                                          "calls_this_month": new_count, "cities": run_summary})
    except Exception as exc:
        log.error("_job_jobad_scout failed: %s", exc)
        from utils.alerter import alert_founder
        alert_founder("jobad_scout", exc)


async def _job_email_poller():
    """Poll info@practicedesk.live via IMAP every 15 min — process replies from known leads."""
    try:
        from agents.email_poller import poll_email_replies
        from utils.monitoring import upsert_heartbeat
        result = await asyncio.to_thread(poll_email_replies)
        upsert_heartbeat("email_poller", result)
        if result["processed"] > 0:
            log.info("email_poller: %s reply(s) processed", result["processed"])
    except Exception as exc:
        log.error("_job_email_poller failed: %s", exc)


async def start_scheduler():
    global _scheduler
    try:
        from agents.signal import register_hook_ab_test
        register_hook_ab_test()
    except Exception:
        pass  # non-fatal — Signal tables may not be migrated yet in fresh deploys

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    # misfire_grace_time: max seconds past due-time a job can still fire after a restart.
    # Default is 1s — any Railway restart ≥ 1s from a job's scheduled time silently skips it.
    # 900s (15 min) means jobs fire on the next startup even if the server was down ≤ 15 min.
    _MGT_SHORT = 300     # 5 min  — for high-frequency jobs (every 15 min / hourly)
    _MGT_LONG  = 82800  # 23 h   — for daily jobs; fires on restart even if server was down all day

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(_job_wa_followup,         "cron", hour=9,        minute=0,   misfire_grace_time=_MGT_LONG)   # 9am UTC daily
    _scheduler.add_job(_job_voice_followup,       "cron", hour="*",      minute=0,   misfire_grace_time=_MGT_SHORT,  # every hour Mon–Fri
                       day_of_week="mon-fri")
    _scheduler.add_job(_job_observatory,          "cron", hour=1,        minute=30,  misfire_grace_time=_MGT_LONG)   # 1:30am UTC = 7am IST
    _scheduler.add_job(_job_email_campaign,       "cron", hour="13,15,22", minute=0, misfire_grace_time=_MGT_LONG)   # 13:00=CA 9am ET | 15:00=US 11am ET | 22:00=AU 8am AEST
    _scheduler.add_job(_job_wa_broadcast,         "cron", hour="*",      minute=15,  misfire_grace_time=_MGT_SHORT,  # every hour Mon–Fri
                       day_of_week="mon-fri")
    _scheduler.add_job(_job_click_calls,          "cron", hour="*",      minute=0,   misfire_grace_time=_MGT_SHORT,  # every hour Mon–Fri
                       day_of_week="mon-fri")
    _scheduler.add_job(_job_scheduled_callbacks,  "cron", minute="*/15",             misfire_grace_time=_MGT_SHORT,  # every 15 min
                       day_of_week="mon-fri")
    _scheduler.add_job(_job_signal_weekly,        "cron", day_of_week="mon", hour=6, minute=0, misfire_grace_time=_MGT_LONG)  # Monday 6am UTC
    _scheduler.add_job(_job_watchdog,             "cron", hour="*",      minute=45,  misfire_grace_time=_MGT_SHORT)           # :45 every hour
    _scheduler.add_job(_job_prospect,             "cron", hour=12,       minute=0,   misfire_grace_time=_MGT_LONG)            # 12:00 UTC daily
    _scheduler.add_job(_job_jobad_scout,          "cron", hour=14,       minute=0,
                       misfire_grace_time=3600,   coalesce=True)  # 14:00 UTC daily, 1h grace, collapse missed runs
    _scheduler.add_job(_job_email_poller,         "cron", minute="*/15",             misfire_grace_time=_MGT_SHORT)           # every 15 min, 7 days
    _scheduler.add_job(_job_enrich_emails,        "cron", hour="*",      minute=30,  misfire_grace_time=_MGT_SHORT)           # every hour, all days — keeps up with daily prospecting
    _scheduler.start()

    # Populate job registry — used by _job_watchdog for auto-recovery
    _JOB_REGISTRY.update({
        "prospect_cron":        _job_prospect,
        "jobad_scout":          _job_jobad_scout,
        "email_campaign":       _job_email_campaign,
        "wa_broadcast":         _job_wa_broadcast,
        "wa_followup":          _job_wa_followup,
        "voice_followup":       _job_voice_followup,
        "observatory":          _job_observatory,
        "email_poller":         _job_email_poller,
        "enrich_emails":        _job_enrich_emails,
        "click_calls":          _job_click_calls,
        "scheduled_callbacks":  _job_scheduled_callbacks,
        "signal_weekly":        _job_signal_weekly,
    })

    # Startup catch-up: re-fire any overdue jobs immediately on boot.
    # Handles deploys that land after a job's scheduled window + grace time.
    try:
        from utils.monitoring import check_cadences
        overdue = await asyncio.to_thread(check_cadences)
        for alert in overdue:
            fn = _JOB_REGISTRY.get(alert["job"])
            if fn:
                log.info("start_scheduler: catch-up firing '%s' (overdue by %s)", alert["job"], alert["message"])
                asyncio.ensure_future(fn())
    except Exception as _e:
        log.warning("start_scheduler: catch-up check failed: %s", _e)


# ── Vobiz call-event webhook (Ring / StartApp / Hangup / recording.completed) ──

@app.post("/api/webhooks/vobiz")
async def vobiz_webhook(request: Request):
    """Receive Vobiz call lifecycle events. Logs to lead_activities when lead matched."""
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}

    event     = payload.get("Event", "")
    call_uuid = payload.get("CallUUID", "")
    from_no   = payload.get("From", "")
    to_no     = payload.get("To", "")
    direction = payload.get("Direction", "")
    duration  = payload.get("Duration", "")
    rec_url   = payload.get("RecordingUrl", "")

    if event in ("Hangup", "recording.completed") and from_no:
        try:
            from database.client import get_lead_by_phone, log_activity
            phone = f"+{from_no}" if not from_no.startswith("+") else from_no
            lead  = get_lead_by_phone(phone)
            if lead:
                log_activity(lead["id"], f"vobiz_{event.lower()}", {
                    "call_uuid": call_uuid,
                    "direction": direction,
                    "duration":  duration,
                    "recording_url": rec_url,
                })
        except Exception:
            pass

    return {"ok": True}


# ── WA Outreach Inbound Webhook (Agents 4 + 5: Reply Handler + Demo Booking) ──

@app.get("/api/webhooks/wa-outreach")
async def wa_outreach_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
):
    """Meta webhook verification handshake."""
    verify_token = os.getenv("WA_WEBHOOK_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/api/webhooks/wa-outreach")
async def wa_outreach_webhook(request: Request):
    """Receive inbound WhatsApp messages, classify intent, and respond."""
    from agents.reply_handler import classify_intent, generate_reply, get_demo_message
    from agents.outreach import send_whatsapp_message
    from database.client import (
        get_lead_by_phone, update_lead, log_activity,
        save_wa_inbox, update_wa_inbox, PHONE_NUMBER_LABELS,
    )
    from datetime import datetime, timezone

    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}

    try:
        entry    = payload.get("entry", [{}])[0]
        change   = entry.get("changes", [{}])[0]
        value    = change.get("value", {})
        messages = value.get("messages", [])

        if not messages or messages[0].get("type") != "text":
            return {"ok": True}

        msg    = messages[0]
        sender = msg.get("from", "")
        text   = msg.get("text", {}).get("body", "").strip()
        if not sender or not text:
            return {"ok": True}

        phone          = f"+{sender}" if not sender.startswith("+") else sender
        number_id      = value.get("metadata", {}).get("phone_number_id", "")
        to_number      = PHONE_NUMBER_LABELS.get(number_id, "US")
        received_at    = datetime.now(timezone.utc).isoformat()

        # Save to inbox immediately — before lead lookup so unknowns are captured too
        lead       = get_lead_by_phone(phone)
        lead_id    = str(lead["id"]) if lead else None
        lead_name  = lead.get("name") if lead else None

        inbox_row = save_wa_inbox({
            "from_phone":   phone,
            "to_number":    to_number,
            "to_number_id": number_id,
            "message":      text,
            "lead_id":      lead_id,
            "lead_name":    lead_name,
            "status":       "new",
            "received_at":  received_at,
        })
        inbox_id = inbox_row["id"] if inbox_row else None

        if not lead:
            return {"ok": True}  # unknown sender stored, nothing more to do

        btype = lead.get("business_type", "practice")
        update_lead(lead_id, {"status": "replied"})
        log_activity(lead_id, "wa_reply_received", {"message": text, "sender": phone})

        intent = classify_intent(text)
        reply  = None

        if intent == "interested":
            reply = get_demo_message(lead_name)
            send_whatsapp_message(phone, reply)
            log_activity(lead_id, "demo_booking_sent", {"message": reply})

        elif intent == "question":
            reply = generate_reply(text, lead_name, btype)
            send_whatsapp_message(phone, reply)
            log_activity(lead_id, "wa_reply_sent", {"message": reply})

        elif intent == "not_interested":
            update_lead(lead_id, {"status": "dead"})
            log_activity(lead_id, "marked_not_interested", {"message": text})

        if inbox_id:
            update_wa_inbox(inbox_id, {
                "intent":     intent,
                "status":     "replied" if reply else "read",
                "reply_sent": reply,
                "replied_at": datetime.now(timezone.utc).isoformat() if reply else None,
            })

    except Exception:
        pass  # Always 200 — Meta will retry on non-200

    return {"ok": True}


@app.get("/api/inbox/wa")
async def get_wa_inbox_api(_=Depends(verify_token)):
    from database.client import get_wa_inbox, get_wa_inbox_unread_count
    messages = get_wa_inbox(limit=200)
    unread   = get_wa_inbox_unread_count()
    return {"messages": messages, "unread": unread}


@app.post("/api/inbox/wa/{inbox_id}/reply")
async def reply_wa_inbox(inbox_id: str, body: dict, _=Depends(verify_token)):
    from database.client import get_client, update_wa_inbox
    from agents.outreach import send_whatsapp_message

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        db     = get_client()
        result = db.table("wa_inbox").select("*").eq("id", inbox_id).limit(1).execute()
        row    = result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB lookup failed: {e}")

    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    # Reply from the exact number that received the message (not auto-routed)
    phone_number_id = row.get("to_number_id") or None
    send_whatsapp_message(row["from_phone"], text, phone_number_id=phone_number_id)

    try:
        update_wa_inbox(inbox_id, {"status": "replied", "reply_sent": text})
    except Exception:
        pass  # DB update failure must not block a successfully sent message

    return {"ok": True}


@app.post("/api/inbox/wa/{inbox_id}/read")
async def mark_wa_inbox_read(inbox_id: str, _=Depends(verify_token)):
    """Mark a WA inbox message read without sending a reply (drives the unread badge)."""
    from database.client import get_client

    # Only flip status if it's still "new" — never clobber a "replied" status.
    get_client().table("wa_inbox").update({"status": "read"}).eq("id", inbox_id).eq("status", "new").execute()
    return {"ok": True}


# ── Email reply capture ──────────────────────────────────────────────────────
# Route: POST /api/webhooks/email-inbound
#
# Handles Resend inbound webhook (email.received) for replies to outgoing emails.
# Resend fires this when a lead replies to info@replies.practicedesk.live.
#
# Resend webhook payload: { "type": "email.received", "data": { "email_id", "from", "subject", ... } }
# Body is NOT included in the webhook — a second Resend API call fetches it.
#
# Setup (one-time, dashboard only):
#   1. Resend dashboard → Receiving → add domain "replies.practicedesk.live"
#      → copy the MX record values shown
#   2. GoDaddy DNS → add MX record for "replies.practicedesk.live" using Resend's values
#   3. Resend dashboard → Webhooks → add webhook:
#      URL: https://serene-passion-production-cd82.up.railway.app/api/webhooks/email-inbound
#      Event: email.received
#   4. Railway env var OUTREACH_REPLY_TO = info@replies.practicedesk.live  ← already set

@app.post("/api/webhooks/email-inbound")
async def email_inbound_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}

    # ── Parse: Resend inbound format vs legacy simple format ──────────────────
    if payload.get("type") == "email.received":
        data       = payload.get("data") or {}
        from_email = (data.get("from")    or "").strip().lower()
        subject    = (data.get("subject") or "").strip()
        email_id   = data.get("email_id", "")

        # Fetch body via Resend received-email API (body is not in the webhook)
        body_text = ""
        if email_id:
            try:
                import requests as _req
                _rkey = os.getenv("RESEND_API_KEY", "")
                _r = _req.get(
                    f"https://api.resend.com/emails/received/{email_id}",
                    headers={"Authorization": f"Bearer {_rkey}"},
                    timeout=10,
                )
                if _r.ok:
                    body_text = (_r.json().get("text") or "")[:2000]
            except Exception:
                pass
    else:
        # Legacy / manual format: { from_email, subject, body_text }
        from_email = (payload.get("from_email") or "").strip().lower()
        subject    = (payload.get("subject")    or "").strip()
        body_text  = (payload.get("body_text")  or "")[:2000]

    if not from_email:
        return {"ok": True}

    from database.client import get_client, update_lead, log_activity
    db = get_client()

    row = db.table("leads").select("id, name, business_type, status").ilike("email", from_email).limit(1).execute()

    if not row.data:
        try:
            from utils.notifier import notify_founder
            notify_founder(
                kind="system_alert", severity="info",
                component="email_reply",
                reason=f"Email reply from unknown sender: {from_email}\nSubject: {subject}\n\n{body_text[:400]}",
            )
        except Exception:
            pass
        return {"ok": True}

    lead    = row.data[0]
    lead_id = str(lead["id"])
    name    = lead.get("name", "")
    btype   = lead.get("business_type", "practice")

    if lead.get("status") not in ("replied", "converted", "dead"):
        update_lead(lead_id, {"status": "replied"})

    log_activity(lead_id, "email_reply_received", {
        "from_email": from_email,
        "subject":    subject,
        "body":       body_text[:500],
    })

    try:
        from utils.notifier import notify_founder
        notify_founder(
            kind="system_alert", severity="info",
            component="email_reply",
            reason=(
                f"Email reply from {name} ({btype})\n"
                f"From: {from_email}\nSubject: {subject}\n\n{body_text[:500]}"
            ),
        )
    except Exception:
        pass

    return {"ok": True}


# ── Cron: WA follow-up (Agent 6 — 3-day silence) ─────────────────────────────

@app.post("/api/cron/wa-followup")
async def cron_wa_followup(request: Request):
    """Send follow-up WA message to leads silent for 3+ days."""
    import asyncio as _asyncio
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.followup import generate_followup_message
    from agents.outreach import send_whatsapp_message
    from database.client import get_leads_for_followup, log_activity

    leads = get_leads_for_followup()
    sent = failed = 0

    for lead in leads:
        try:
            msg = generate_followup_message(
                lead.get("name", ""),
                lead.get("business_type", "practice"),
                lead.get("city", ""),
            )
            send_whatsapp_message(lead["phone"], msg)
            log_activity(lead["id"], "wa_followup_sent", {"message": msg})
            sent += 1
        except Exception:
            failed += 1
        await _asyncio.sleep(2)

    return {"sent": sent, "failed": failed, "total": len(leads)}


# ── Cron: WA broadcast (new leads, Mon–Fri 8:30 AM–7 PM local) ──────────────

@app.post("/api/cron/wa-broadcast")
async def cron_wa_broadcast(request: Request):
    """Send initial WA to pending (uncontacted) leads within their local hours."""
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.wa_broadcast import run_wa_broadcast
    result = await asyncio.to_thread(run_wa_broadcast)
    return {"ok": True, **result}


# ── Cron: click-to-call campaign (email clickers, Mon–Fri 11 AM–5 PM local) ───

@app.post("/api/cron/click-calls")
async def cron_click_calls(request: Request):
    """
    Outbound voice campaign to leads who clicked an email link but have not yet
    been called. Respects 11 AM–5 PM in the lead's local timezone.
    Schedule on Railway: every hour, Mon–Fri.
    Accepts either CRON_SECRET or admin JWT.
    """
    cron_secret = os.getenv("CRON_SECRET", "")
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if cron_secret and token != cron_secret:
        # Fall back to admin JWT check
        try:
            verify_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.click_caller import run_click_campaign
    result = run_click_campaign()
    return {"ok": True, **result}


# ── Cron: voice follow-up (Agent 7 — 5-day silence) ──────────────────────────

@app.post("/api/cron/voice-followup")
async def cron_voice_followup(request: Request):
    """Place outbound follow-up call to leads silent for 5+ days."""
    import asyncio as _asyncio
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Delegate to voice_outreach.place_outbound_call() rather than calling Vapi
    # directly — that function already has the correct India/CA/AU/US routing
    # (this endpoint used to always default to the US Platform number, which
    # is what caused the Edmonton CA lead's 24 repeated wrong-number failures).
    from agents.voice_outreach import place_outbound_call
    from agents.email_personalizer import detect_market
    from database.client import get_leads_for_voice_followup, log_activity

    leads = get_leads_for_voice_followup()
    placed = failed = 0

    for lead in leads:
        try:
            mkt = detect_market(lead.get("phone", ""), lead.get("address", "") or "")
            result = place_outbound_call(
                phone=lead["phone"],
                business_type=lead.get("business_type", ""),
                business_name=lead.get("name", ""),
                lead_id=str(lead["id"]),
                city=lead.get("city", ""),
                market=mkt,
                pain_signal=lead.get("pain_signal", "") or "",
                pain_finding=lead.get("pain_finding", "") or "",
            )
            call_id = result.get("id", "")
            _track_active_call(call_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
            log_activity(lead["id"], "voice_followup_placed", {
                "vapi_call_id": call_id,
                "phone": lead["phone"],
            })
            placed += 1
        except Exception:
            failed += 1
        await _asyncio.sleep(3)

    return {"placed": placed, "failed": failed, "total": len(leads)}


# ── Cron: Observatory (Agent 10 — daily digest) ───────────────────────────────

@app.post("/api/cron/observatory")
async def cron_observatory(request: Request):
    """Build and send the daily Apex digest to the founder's WhatsApp."""
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.observatory import send_observatory_digest
    digest = send_observatory_digest()
    return {"ok": True, "digest": digest}


@app.post("/api/cron/prospect")
async def cron_prospect(_: str = Depends(verify_token)):
    """Manually trigger one prospecting run (same as the 12:00 UTC daily cron)."""
    await _job_prospect()
    return {"ok": True}


@app.post("/api/cron/jobad-scout")
async def cron_jobad_scout(request: Request):
    """
    Manually/externally trigger one job-ad scout run (same as the 14:00 UTC daily cron).
    Auth: CRON_SECRET bearer token — lets an external scheduler trigger it if the
    in-process APScheduler instance is down (Change #11 reliability requirement).
    """
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")
    await _job_jobad_scout()
    return {"ok": True}


@app.post("/api/cron/email-campaign")
async def cron_email_campaign(_: str = Depends(verify_token)):
    """Manually trigger the email campaign job (same as the 13/15/22 UTC scheduler)."""
    await _job_email_campaign()
    return {"ok": True}


@app.get("/api/webhooks/dograh/debug")
async def dograh_webhook_debug(_=Depends(verify_token)):
    """Return the last raw payload received from Dograh (for debugging)."""
    from database.client import get_client
    result = get_client().table("settings").select("value, updated_at").eq("key", "dograh_last_webhook_payload").execute()
    if not result.data:
        return {"payload": None, "updated_at": None, "note": "No Dograh webhook received yet"}
    row = result.data[0]
    return {"payload": json.loads(row["value"]), "updated_at": row["updated_at"]}


@app.post("/api/observatory/run")
async def observatory_run(_=Depends(verify_token)):
    """Manually trigger the Observatory digest (admin auth)."""
    from agents.observatory import send_observatory_digest
    digest = send_observatory_digest()
    return {"ok": True, "digest": digest}


@app.get("/api/observatory/latest")
async def observatory_latest(_=Depends(verify_token)):
    """Return the most recently stored Observatory digest."""
    from database.client import get_client
    result = (
        get_client()
        .table("settings")
        .select("value, updated_at")
        .eq("key", "last_observatory_digest")
        .execute()
    )
    if not result.data:
        return {"digest": None, "updated_at": None}
    row = result.data[0]
    return {"digest": row["value"], "updated_at": row["updated_at"]}


# ── Content Agent (Agent 8) ────────────────────────────────────────────────────

class ContentGenerateRequest(BaseModel):
    product: str
    module: str
    content_type: str
    tone: str = "structured"
    market: str = "AU"
    language: str = "en"
    platform: str = ""
    brief: str = ""
    signal_feedback: str = ""   # optional: Signal performance context from VP Marketing


@app.post("/api/content/generate")
async def content_generate(body: ContentGenerateRequest):
    """Content Agent — generates WA templates, email copy, voice guidance, or social posts."""
    from agents.content_agent import generate_content, ContentRequest

    req = ContentRequest(
        product=body.product,
        module=body.module,
        content_type=body.content_type,
        tone=body.tone,
        market=body.market,
        language=body.language,
        platform=body.platform,
        brief=body.brief,
        signal_feedback=body.signal_feedback,
    )
    result = generate_content(req)
    return {
        "content": result.content,
        "product": result.product,
        "module": result.module,
        "content_type": result.content_type,
        "tone": result.tone,
        "market": result.market,
        "language": result.language,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }


@app.get("/api/content/modules")
async def content_modules():
    """List available products and their modules."""
    from agents.content_agent import PRODUCT_MODULES
    return {
        "products": PRODUCT_MODULES,
        "content_types": ["wa_template", "email", "voice_guidance", "social_post", "affiliate_dm"],
        "tones": ["structured", "pain_first", "outcome_first", "conversational"],
        "markets": ["AU", "US", "CA", "IN"],
        "languages": ["en", "hi"],
    }


# ── Content Approvals ─────────────────────────────────────────────────────────

class ContentApprovalCreate(BaseModel):
    content_type: str
    product: str
    module: str
    market: str = "AU"
    tone: str = "structured"
    language: str = "en"
    content: str
    subject: str = ""
    source: str = "content_screen"


class ContentApprovalUpdate(BaseModel):
    status: str | None = None
    content: str | None = None
    notes: str | None = None


@app.post("/api/content/approvals", dependencies=[Depends(verify_token)])
async def create_approval(body: ContentApprovalCreate):
    from database.client import save_approval
    row = save_approval({
        "content_type": body.content_type,
        "product": body.product,
        "module": body.module,
        "market": body.market,
        "tone": body.tone,
        "language": body.language,
        "content": body.content,
        "subject": body.subject or None,
        "source": body.source,
        "status": "pending",
    })
    return row


@app.get("/api/content/approvals", dependencies=[Depends(verify_token)])
async def list_approvals(status: str | None = None, limit: int = 100):
    from database.client import get_approvals
    return get_approvals(status=status, limit=limit)


@app.patch("/api/content/approvals/{approval_id}", dependencies=[Depends(verify_token)])
async def patch_approval(approval_id: str, body: ContentApprovalUpdate):
    from database.client import update_approval
    data = {k: v for k, v in body.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="Nothing to update")
    return update_approval(approval_id, data)


# ── Signal — Performance Feedback (Agent 1 → VP Marketing → Content Agent) ───

@app.get("/api/signal/feedback")
async def signal_feedback(_: str = Depends(verify_token)):
    """
    Signal compiles a performance feedback brief.
    VP Marketing reads this to decide what content to commission.
    Content Agent uses it to improve underperforming templates.
    """
    from agents.signal import get_performance_feedback_brief
    return get_performance_feedback_brief()


# ── VP Marketing Agent (Agent 12) ─────────────────────────────────────────────

class VPMarketingPlanRequest(BaseModel):
    additional_brief: str = ""
    include_signal: bool = True   # whether to pull live Signal data before planning


class VPMarketingCommissionRequest(BaseModel):
    commission: dict              # one item from the content_queue
    signal_context: str = ""     # Signal context string to pass to Content Agent


@app.post("/api/vp-marketing/plan")
async def vp_marketing_plan(body: VPMarketingPlanRequest, _: str = Depends(verify_token)):
    """
    VP Marketing generates a comprehensive campaign plan for all verticals.
    Optionally pulls Signal performance data first to prioritise refreshes.
    Returns strategic brief + ordered content queue for Agent 8.
    """
    from agents.vp_marketing import generate_campaign_plan

    signal_feedback = None
    if body.include_signal:
        try:
            from agents.signal import get_performance_feedback_brief
            signal_feedback = get_performance_feedback_brief()
        except Exception as exc:
            log.warning("Signal feedback unavailable: %s", exc)

    plan = generate_campaign_plan(
        signal_feedback=signal_feedback,
        additional_brief=body.additional_brief,
    )
    return {
        "generated_at":    plan.generated_at,
        "strategic_brief": plan.strategic_brief,
        "content_queue":   plan.content_queue,
        "signal_context":  plan.signal_context,
        "queue_length":    len(plan.content_queue),
        "usage": {
            "input_tokens":  plan.input_tokens,
            "output_tokens": plan.output_tokens,
        },
    }


@app.post("/api/vp-marketing/commission")
async def vp_marketing_commission(body: VPMarketingCommissionRequest, _: str = Depends(verify_token)):
    """
    VP Marketing executes one content commission → calls Content Agent.
    Result is returned for review; not auto-deployed.
    """
    from agents.vp_marketing import execute_commission

    result = execute_commission(body.commission, signal_context=body.signal_context)
    return {
        "content":      result.content,
        "commission":   result.commission,
        "usage": {
            "input_tokens":  result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }


class EmmaCallRequest(BaseModel):
    phone: str
    call_type: str
    patient_name: str
    appointment_time: str = ""
    city: str = ""


@app.get("/api/ping-emma")
async def ping_emma():
    return {"pong": "emma"}


@app.post("/api/emma/call")
async def emma_call(req: EmmaCallRequest, _=Depends(verify_token)):
    from agents.vapi_caller import place_emma_call as place_emma_call_vapi
    valid_types = {"appointment_reminder", "six_month_recall", "post_treatment_checkin", "no_show_followup"}
    if req.call_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"call_type must be one of: {', '.join(sorted(valid_types))}")
    try:
        result = place_emma_call_vapi(
            phone=req.phone,
            call_type=req.call_type,
            patient_name=req.patient_name,
            appointment_time=req.appointment_time,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"ok": True, "call_id": result.get("id", ""), "call_type": req.call_type}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
