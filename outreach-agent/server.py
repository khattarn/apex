import asyncio
import json
import logging
import os
import sys
import time as _time
from typing import Optional

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


def _track_active_call(
    run_id: str,
    lead_id: str,
    lead_name: str,
    phone: str,
    direction: str,
) -> None:
    """Register a just-triggered Dograh call in the live-call dashboard tracker."""
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

app = FastAPI(title="Apex Admin API", version="1.0.0")

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
    """Returns set of lead IDs that have received an outbound Aria call."""
    from database.client import get_client
    rows = get_client().table("lead_activities").select("lead_id").eq("type", "outbound_call").execute().data or []
    return {"ids": list({str(r["lead_id"]) for r in rows})}


@app.get("/api/active-calls")
async def get_active_calls(_=Depends(verify_token)):
    """Returns calls currently in progress (tracked in memory via Vapi call-started webhook)."""
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
        limit=limit,
        offset=offset,
    )


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
            log_activity, get_setting, EMAIL_SEQUENCE,
        )
        from agents.email_personalizer import generate_email, detect_market
        from agents.email_sender import send_email
        from utils.timezone import is_email_window, window_description

        leads = get_leads_due_for_email()
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
            city   = lead.get("city", "")
            market = detect_market(lead.get("phone", ""), lead.get("address", ""))

            if not is_email_window(city, market):
                win = window_description(city, market)
                yield {"data": json.dumps({"type": "log", "line": f"  ⏰ {name} — outside window ({win}), sending anyway (manual)"})}

            current_step = lead.get("email_sequence_step") or 0
            next_step    = current_step + 1
            if next_step > len(EMAIL_SEQUENCE):
                skipped += 1
                continue

            email_num, _ = EMAIL_SEQUENCE[next_step - 1]
            yield {"data": json.dumps({"type": "log", "line": f"  > {name} — Email {email_num} (step {next_step}/{len(EMAIL_SEQUENCE)})"})}

            try:
                subject, html, email_num_used, variant = await asyncio.to_thread(
                    generate_email, lead, email_number=email_num
                )
                send_result = await asyncio.to_thread(send_email, lead["email"], subject, html)
                resend_id   = (send_result or {}).get("id", "")
                if resend_id and run_id:
                    save_email_send(lead["id"], run_id, resend_id, email_num_used, next_step)
                advance_email_sequence(lead["id"], next_step)
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
    workflow_run_id = payload.get("workflow_run_id", "")
    initial_ctx     = payload.get("initial_context", {})
    gathered_ctx    = payload.get("gathered_context", {})
    recording_url   = payload.get("recording_url", "")
    transcript_url  = payload.get("transcript_url", "")
    cost_info       = payload.get("cost_info", {})

    lead_id      = str(initial_ctx.get("lead_id", ""))
    call_outcome = gathered_ctx.get("call_outcome", "unknown")

    # Clear from live-call dashboard tracker
    _active_calls.pop(workflow_run_id, None)

    # Inbound (Henry): Dograh doesn't inject lead_id — look up by caller phone
    if not lead_id:
        caller_phone = str(initial_ctx.get("phone_number", ""))
        lead = _find_lead_by_phone(caller_phone)
        lead_id = str(lead["id"]) if lead else ""

    if not lead_id:
        return {"ok": True}

    from database.client import update_lead, log_activity

    # ── Route by Sophie's extracted call_outcome ──────────────────────────────
    if call_outcome == "booked_demo":
        _handle_book_demo(
            lead_id=lead_id,
            preferred_time=gathered_ctx.get("demo_preferred_time", ""),
            attendee_email=gathered_ctx.get("attendee_email", ""),
            attendee_name=initial_ctx.get("contact_name", ""),
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
        day = gathered_ctx.get("callback_day", "")
        time = gathered_ctx.get("callback_time", "")
        try:
            callback_dt = parse_preferred_time(f"{day} {time}", tz)
            log_activity(lead_id, "callback_scheduled", {
                "callback_at": callback_dt.isoformat(),
                "preferred_day": day,
                "preferred_time": time,
            })
        except Exception as exc:
            log.warning("Could not parse callback time '%s %s': %s", day, time, exc)

    elif call_outcome == "callback_requested":
        update_lead(lead_id, {"callback_requested": True})
        log_activity(lead_id, "callback_requested", {
            "source": "dograh_outbound",
            "note": "Prospect requested human callback during Sophie call",
        })
        _notify_callback_requested(lead_id)

    elif call_outcome == "not_interested":
        update_lead(lead_id, {"status": "dead"})

    elif call_outcome == "booked_demo_manually":
        # Sophie confirmed sign-up / directed to practicedesk.live — just log it
        update_lead(lead_id, {"status": "converted"})

    # ── Always log completion ─────────────────────────────────────────────────
    log_activity(lead_id, "outbound_call_completed", {
        "dograh_run_id":  workflow_run_id,
        "call_outcome":   call_outcome,
        "recording_url":  recording_url,
        "transcript_url": transcript_url,
        "cost_info":      cost_info,
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


def _notify_callback_requested(lead_id: str) -> None:
    """Send Neeraj a WhatsApp alert when a prospect asks for a human callback."""
    try:
        from database.client import get_client
        db = get_client()
        lead = db.table("leads").select("name, phone, business_type, city").eq("id", lead_id).single().execute().data
        if not lead:
            return

        wa_token   = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        phone_id   = os.getenv("OUTREACH_WA_PHONE_NUMBER_ID", "")
        neeraj_no  = os.getenv("FOUNDER_WHATSAPP_NUMBER", "")  # e.g. +919XXXXXXXXX
        if not all([wa_token, phone_id, neeraj_no]):
            return

        msg = (
            f"📞 *Callback requested*\n"
            f"Lead: {lead['name']}\n"
            f"Phone: {lead['phone']}\n"
            f"Type: {lead.get('business_type', '')} · {lead.get('city', '')}\n"
            f"They want a human call — please follow up."
        )
        import requests as req
        req.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": neeraj_no,
                "type": "text",
                "text": {"body": msg},
            },
            headers={"Authorization": f"Bearer {wa_token}"},
            timeout=10,
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
        log_activity, save_campaign_run, EMAIL_SEQUENCE,
    )
    from agents.email_personalizer import generate_email, detect_market
    from agents.email_sender import send_email
    from utils.timezone import is_email_window, window_description

    from agents.email_sender import QuotaExceededError

    leads = get_leads_due_for_email(limit=180)
    sent = skipped = failed = 0

    for lead in leads:
        city   = lead.get("city", "")
        market = detect_market(lead.get("phone", ""), lead.get("address", ""))
        if not is_email_window(city, market):
            skipped += 1
            continue

        current_step = lead.get("email_sequence_step") or 0
        next_step    = current_step + 1
        if next_step > len(EMAIL_SEQUENCE):
            skipped += 1
            continue

        email_num, _ = EMAIL_SEQUENCE[next_step - 1]
        try:
            subject, html, email_num_used, variant = generate_email(lead, email_number=email_num)
            send_email(lead["email"], subject, html)
            advance_email_sequence(lead["id"], next_step)
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
    from agents.dograh_caller import place_outbound_call

    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("phone"):
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    try:
        result = place_outbound_call(
            phone=lead["phone"],
            business_type=lead.get("business_type", ""),
            business_name=lead.get("name", ""),
            lead_id=lead_id,
            city=lead.get("city", ""),
            trigger="cold",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    run_id = result.get("workflow_run_id", "")
    _track_active_call(run_id, lead_id, lead.get("name", ""), lead.get("phone", ""), "outbound")
    update_lead(lead_id, {"notes": f"Voice call placed — Dograh run ID: {run_id or 'unknown'}"})
    return {"ok": True, "workflow_run_id": run_id}


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
async def track_click(lead_id: str, url: str = "https://practicedesk.netlify.app"):
    from database.client import update_lead, log_activity, get_client
    from fastapi.responses import RedirectResponse
    from datetime import datetime, timezone
    try:
        lead = get_client().table("leads").select("email_opened, email_clicked").eq("id", lead_id).limit(1).execute()
        already_opened  = lead.data[0].get("email_opened")  if lead.data else False
        already_clicked = lead.data[0].get("email_clicked") if lead.data else False
        ts = datetime.now(timezone.utc).isoformat()
        patch = {"email_clicked": True, "email_opened": True, "email_clicked_at": ts}
        if not already_opened:
            patch["email_opened_at"] = ts
        update_lead(lead_id, patch)
        if not already_opened:
            log_activity(lead_id, "email_opened",  {"source": "pixel"})
        if not already_clicked:
            log_activity(lead_id, "email_clicked", {"source": "pixel"})
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


# ── Twilio browser dialer ─────────────────────────────────────────────────────

@app.get("/api/twilio/token")
async def twilio_token(_=Depends(verify_token)):
    from twilio.jwt.access_token import AccessToken
    from twilio.jwt.access_token.grants import VoiceGrant

    account_sid  = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token   = os.getenv("TWILIO_AUTH_TOKEN", "")
    twiml_app_sid = os.getenv("TWILIO_TWIML_APP_SID", "")
    caller_id    = os.getenv("TWILIO_CALLER_ID", "+13853633720")

    if not all([account_sid, auth_token, twiml_app_sid]):
        raise HTTPException(status_code=500, detail="Twilio env vars missing")

    token = AccessToken(account_sid, auth_token, twiml_app_sid, ttl=3600)
    grant = VoiceGrant(outgoing_application_sid=twiml_app_sid, incoming_allow=False)
    token.add_grant(grant)
    return {"token": token.to_jwt(), "caller_id": caller_id}


@app.post("/api/twilio/voice")
async def twilio_voice(To: str = "", _From: str = ""):
    from twilio.twiml.voice_response import VoiceResponse, Dial
    caller_id = os.getenv("TWILIO_CALLER_ID", "+13853633720")
    resp = VoiceResponse()
    if To:
        dial = Dial(caller_id=caller_id)
        dial.number(To)
        resp.append(dial)
    else:
        resp.say("No destination number provided.")
    return Response(content=str(resp), media_type="application/xml")


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
    cutoff_3d = (now_utc - timedelta(days=3)).isoformat()
    cutoff_5d = (now_utc - timedelta(days=5)).isoformat()

    wa_sent_ids    = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "wa_followup_sent").execute().data or [])}
    voice_sent_ids = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "voice_followup_placed").execute().data or [])}
    email_clicked_ids = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").eq("type", "email_clicked").execute().data or [])}
    called_ids     = {str(r["lead_id"]) for r in (db.table("lead_activities").select("lead_id").in_("type", ["outbound_call", "voice_followup_placed"]).execute().data or [])}

    wa_cands   = db.table("leads").select("id").eq("status", "contacted").eq("outreach_sent", True).lte("outreach_date", cutoff_3d).execute().data or []
    vox_cands  = db.table("leads").select("id").eq("status", "contacted").eq("outreach_sent", True).lte("outreach_date", cutoff_5d).execute().data or []

    wa_pending    = len([l for l in wa_cands  if str(l["id"]) not in wa_sent_ids])
    voice_pending = len([l for l in vox_cands if str(l["id"]) not in voice_sent_ids])
    click_pending_ids = email_clicked_ids - called_ids
    click_pending = len(click_pending_ids)

    click_leads: list[dict] = []
    if click_pending_ids:
        from utils.timezone import is_voice_window, CITY_TZ
        import pytz
        raw = db.table("leads").select("id, name, city, phone, business_type").in_("id", list(click_pending_ids)).execute().data or []
        _nanp_cities = {c for c, tz in CITY_TZ.items() if "America" in tz}
        for r in raw:
            city = r.get("city", "")
            tz_name = CITY_TZ.get(city, "")
            in_window = is_voice_window(city, "")
            if in_window:
                call_status = "ready"
            elif "Australia" in tz_name:
                # Show local time so it's clear when window opens
                local_t = now_utc.astimezone(pytz.timezone(tz_name))
                call_status = f"outside hours ({local_t.strftime('%H:%M')} {local_t.strftime('%Z')})"
            elif city in _nanp_cities:
                call_status = "blocked (Trust Hub)"
            else:
                call_status = "outside hours"
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
        for h in [13, 22]:
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
            "job": "WA Follow-up",
            "next_run": _next_daily(9, 0),
            "next_runs": [_next_daily(9, 0)],
            "queue": wa_pending,
            "frequency": "Daily 9:00 UTC",
            "last_ran": _last_of("wa_followup_sent"),
            "description": "Follow-up WA to leads contacted 3+ days ago with no reply",
        },
        {
            "job": "Voice Follow-up",
            "next_run": _next_daily(9, 0),
            "next_runs": [_next_daily(9, 0)],
            "queue": voice_pending,
            "frequency": "Daily 9:00 UTC",
            "last_ran": _last_of("voice_followup_placed"),
            "description": "Aria outbound call to leads silent 5+ days",
        },
        {
            "job": "Email Campaign",
            "next_run": _next_email_campaign(),
            "next_runs": [_next_email_campaign()],
            "queue": email_pending,
            "frequency": "13:00 & 22:00 UTC",
            "last_ran": _last_of("email_campaign_auto"),
            "description": "Next email in 6-step drip sequence (AU 8am / CA 9am EDT)",
        },
        {
            "job": "Aria Click Calls",
            "next_run": hourly_runs[0],
            "next_runs": hourly_runs,
            "queue": click_pending,
            "leads": click_leads,
            "frequency": "Hourly Mon–Fri",
            "last_ran": _last_of("outbound_call"),
            "description": "Calls leads who clicked an email link (10am–5pm local time)",
        },
        {
            "job": "Callbacks",
            "next_run": quarter_runs[0],
            "next_runs": quarter_runs,
            "queue": 0,
            "frequency": "Every 15 min Mon–Fri",
            "last_ran": None,
            "description": "Processes Aria-scheduled callbacks from previous calls",
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
    """Manually trigger a Signal weekly report."""
    from agents.signal import generate_weekly_report
    report = generate_weekly_report()
    return {
        "ok": True,
        "scores": report.get("scores", 0),
        "dead_ends": report.get("dead_ends", 0),
        "targets_behind": report.get("targets_behind", 0),
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_simple():
    return {"status": "ok"}


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

    # Anthropic
    try:
        import anthropic
        anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")).models.list()
        checks["anthropic"] = True
    except Exception:
        checks["anthropic"] = bool(os.getenv("ANTHROPIC_API_KEY"))

    # Google Maps
    checks["google_maps"] = bool(os.getenv("GOOGLE_MAPS_API_KEY"))

    # WhatsApp
    checks["whatsapp"] = bool(os.getenv("OUTREACH_WA_PHONE_NUMBER_ID") and os.getenv("WHATSAPP_ACCESS_TOKEN"))

    return checks


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


# ── Scheduled jobs (APScheduler — runs inside the server process) ─────────────

async def _job_wa_followup():
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
        except Exception as exc:
            log.error("WA followup failed for lead %s: %s", lead.get("id"), exc)
        await asyncio.sleep(2)


async def _job_voice_followup():
    from agents.dograh_caller import place_outbound_call
    from database.client import get_leads_for_voice_followup, log_activity
    leads = get_leads_for_voice_followup()
    for lead in leads:
        try:
            result = place_outbound_call(
                phone=lead["phone"],
                business_type=lead.get("business_type", ""),
                business_name=lead.get("name", ""),
                lead_id=str(lead["id"]),
                city=lead.get("city", ""),
                trigger="voice_followup",
            )
            run_id = result.get("workflow_run_id", "")
            _track_active_call(run_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
            log_activity(lead["id"], "voice_followup_placed", {
                "dograh_run_id": run_id,
                "phone": lead["phone"],
            })
        except Exception as exc:
            log.error("Voice followup failed for lead %s: %s", lead.get("id"), exc)
        await asyncio.sleep(3)


async def _job_observatory():
    from agents.observatory import send_observatory_digest
    from database.client import log_activity
    try:
        digest = send_observatory_digest()  # returns the digest text; builds it internally once
        if digest:
            log_activity(None, "observatory_sent", {"preview": digest[:200]})
    except Exception as exc:
        log.error("Observatory job failed: %s", exc)


async def _job_click_calls():
    try:
        from agents.click_caller import run_click_campaign
        await asyncio.to_thread(run_click_campaign)
    except Exception as exc:
        log.error("_job_click_calls failed: %s", exc)


async def _job_scheduled_callbacks():
    """Call back leads who asked Sophie to call them at a specific time."""
    try:
        from database.client import get_leads_due_callback, log_activity
        from agents.dograh_caller import place_outbound_call
        from utils.timezone import is_voice_window
        leads = get_leads_due_callback()
        for lead in leads:
            if not is_voice_window(lead.get("city", ""), lead.get("market", "")):
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
                    trigger="scheduled_callback",
                )
                run_id = result.get("workflow_run_id", "")
                _track_active_call(run_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
                log_activity(str(lead["id"]), "outbound_call", {
                    "dograh_run_id": run_id,
                    "trigger": "scheduled_callback",
                    "phone": lead["phone"],
                })
            except Exception as exc:
                log.error("Scheduled callback failed for lead %s: %s", lead.get("id"), exc)
    except Exception:
        pass


async def _job_email_campaign():
    """Auto-send up to 180 emails/day to leads due for their next sequence step."""
    try:
        from database.client import (
            get_leads_due_for_email, advance_email_sequence,
            log_activity, save_campaign_run, save_email_send, EMAIL_SEQUENCE,
        )
        from agents.email_personalizer import generate_email, detect_market
        from agents.email_sender import send_email, QuotaExceededError
        from utils.timezone import is_email_window

        leads = get_leads_due_for_email(limit=180)
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
            city   = lead.get("city", "")
            market = detect_market(lead.get("phone", ""), lead.get("address", ""))
            if not is_email_window(city, market):
                skipped += 1
                continue

            current_step = lead.get("email_sequence_step") or 0
            next_step    = current_step + 1
            if next_step > len(EMAIL_SEQUENCE):
                skipped += 1
                continue

            email_num, _ = EMAIL_SEQUENCE[next_step - 1]
            try:
                subject, html, email_num_used, variant = generate_email(lead, email_number=email_num)
                send_result = send_email(lead["email"], subject, html)
                resend_id   = (send_result or {}).get("id", "")
                if resend_id and run_id:
                    save_email_send(lead["id"], run_id, resend_id, email_num_used, next_step)
                advance_email_sequence(lead["id"], next_step)
                log_activity(lead["id"], "email_sent", {
                    "email_number": email_num_used,
                    "variant": variant,
                    "sequence_step": next_step,
                    "trigger": "scheduler",
                })
                sent += 1
            except QuotaExceededError:
                break  # daily Resend quota (180) reached — remaining retried next run
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
    except Exception as exc:
        log.error("_job_email_campaign failed: %s", exc)


async def _job_signal_weekly():
    """Signal weekly run — Monday 6am UTC. Scores templates, computes funnel,
    detects dead ends, generates projections, updates targets, writes brief."""
    try:
        from agents.signal import generate_weekly_report
        report = generate_weekly_report()
        log.info("Signal weekly report: %d scores, %d dead ends, %d targets behind",
                 report.get("scores_computed", 0),
                 report.get("dead_ends", 0),
                 report.get("targets_behind", 0))
    except Exception as exc:
        log.error("Signal weekly job failed: %s", exc)


@app.on_event("startup")
async def start_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(_job_wa_followup,      "cron", hour=9,        minute=0)      # 9am UTC daily
    scheduler.add_job(_job_voice_followup,   "cron", hour=9,        minute=0)      # 9am UTC daily
    scheduler.add_job(_job_observatory,      "cron", hour=1,        minute=30)     # 1:30am UTC = 7am IST
    scheduler.add_job(_job_email_campaign,   "cron", hour="22,13",  minute=0)      # 22:00 UTC = AU 8am | 13:00 UTC = CA 9am EDT
    scheduler.add_job(_job_click_calls,      "cron", hour="*",      minute=0,      # every hour Mon–Fri — timezone filter inside handles 10am–5pm local
                      day_of_week="mon-fri")
    scheduler.add_job(_job_scheduled_callbacks, "cron", minute="*/15",             # every 15 min — checks for due callbacks
                      day_of_week="mon-fri")
    scheduler.add_job(_job_signal_weekly,    "cron", day_of_week="mon", hour=6, minute=0)  # Monday 6am UTC
    scheduler.start()


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
    from database.client import get_lead_by_phone, update_lead, log_activity

    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}

    try:
        entry   = payload.get("entry", [{}])[0]
        change  = entry.get("changes", [{}])[0]
        value   = change.get("value", {})
        messages = value.get("messages", [])

        if not messages or messages[0].get("type") != "text":
            return {"ok": True}

        msg    = messages[0]
        sender = msg.get("from", "")          # digits-only from Meta
        text   = msg.get("text", {}).get("body", "").strip()
        if not sender or not text:
            return {"ok": True}

        phone = f"+{sender}" if not sender.startswith("+") else sender
        lead  = get_lead_by_phone(phone)
        if not lead:
            return {"ok": True}

        lead_id = lead["id"]
        name    = lead.get("name", "")
        btype   = lead.get("business_type", "practice")

        update_lead(lead_id, {"status": "replied"})
        log_activity(lead_id, "wa_reply_received", {"message": text, "sender": phone})

        intent = classify_intent(text)

        if intent == "interested":
            reply = get_demo_message(name)
            send_whatsapp_message(phone, reply)
            log_activity(lead_id, "demo_booking_sent", {"message": reply})

        elif intent == "question":
            reply = generate_reply(text, name, btype)
            send_whatsapp_message(phone, reply)
            log_activity(lead_id, "wa_reply_sent", {"message": reply})

        elif intent == "not_interested":
            update_lead(lead_id, {"status": "dead"})
            log_activity(lead_id, "marked_not_interested", {"message": text})

        # out_of_office: logged above, no reply sent

    except Exception:
        pass  # Always 200 — Meta will retry on non-200

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


# ── Cron: click-to-call campaign (email clickers, Mon–Fri 10 AM–5 PM local) ───

@app.post("/api/cron/click-calls")
async def cron_click_calls(request: Request):
    """
    Outbound voice campaign to leads who clicked an email link but have not yet
    been called. Respects 10 AM–5 PM in the lead's local timezone.
    Schedule on Railway: every hour, Mon–Fri.
    """
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.click_caller import run_click_campaign
    result = run_click_campaign()
    return {"ok": True, **result}


# ── Cron: voice follow-up (Agent 7 — 5-day silence) ──────────────────────────

@app.post("/api/cron/voice-followup")
async def cron_voice_followup(request: Request):
    """Place Dograh outbound call to leads silent for 5+ days."""
    import asyncio as _asyncio
    cron_secret = os.getenv("CRON_SECRET", "")
    if cron_secret:
        auth = request.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ").strip() != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from agents.dograh_caller import place_outbound_call
    from database.client import get_leads_for_voice_followup, log_activity

    leads = get_leads_for_voice_followup()
    placed = failed = 0

    for lead in leads:
        try:
            result = place_outbound_call(
                phone=lead["phone"],
                business_type=lead.get("business_type", ""),
                business_name=lead.get("name", ""),
                lead_id=str(lead["id"]),
                city=lead.get("city", ""),
                trigger="voice_followup",
            )
            run_id = result.get("workflow_run_id", "")
            _track_active_call(run_id, str(lead["id"]), lead.get("name", ""), lead["phone"], "outbound")
            log_activity(lead["id"], "voice_followup_placed", {
                "dograh_run_id": run_id,
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
    from database.client import log_activity

    digest = send_observatory_digest()  # builds once internally
    log_activity(None, "observatory_sent", {"preview": digest[:200]})
    return {"ok": True, "digest": digest}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
