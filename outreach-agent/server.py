import asyncio
import json
import os
import sys
import time as _time
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

sys.path.insert(0, os.path.dirname(__file__))

_running: dict = {}  # tracks which agents are currently executing

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

    return EventSourceResponse(event_generator(), headers={"X-Accel-Buffering": "no"})


# ── Leads ─────────────────────────────────────────────────────────────────────

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[str] = None


@app.get("/api/leads")
async def list_leads(
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    city: Optional[str] = None,
    outreach_sent: Optional[bool] = None,
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

    return EventSourceResponse(generate())


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

        # Create campaign run now so we have an ID to link each email_send record
        from database.client import save_campaign_run, update_campaign_run, save_email_send
        run_record = save_campaign_run({
            "type": "email", "business_type": "all", "city": "all",
            "max_prospects": len(leads), "mode": "live",
            "prospects_found": len(leads), "new_leads": 0,
            "messages_sent": 0, "emails_sent": 0, "log": "In progress…",
        })
        run_id = run_record["id"] if run_record else None

        test_recipient = get_setting("test_recipient_email") or ""
        test_copy_sent = False
        sent = skipped = failed = 0

        for lead in leads:
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

    return EventSourceResponse(generate(), headers={"X-Accel-Buffering": "no"})


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

    leads = get_leads_due_for_email(limit=100)
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

    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("phone"):
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    result = place_outbound_call(lead["phone"], lead["business_type"], lead["name"])
    update_lead(lead_id, {"notes": f"Voice call placed — Vapi call ID: {result.get('id', 'unknown')}"})
    return {"ok": True, "call_id": result.get("id")}


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


# ── Resend webhook (open / click / bounce tracking) ──────────────────────────

@app.post("/api/webhooks/resend")
async def resend_webhook(request: Request):
    from database.client import get_client
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    event_type = body.get("type", "")
    data = body.get("data", {})
    to_list = data.get("to", [])
    if not to_list:
        return {"ok": True}

    recipient = to_list[0]
    update = {}
    if event_type == "email.opened":
        update["email_opened"] = True
    elif event_type == "email.clicked":
        update["email_clicked"] = True
    elif event_type in ("email.bounced", "email.complained"):
        update["email_bounced"] = True
        update["status"] = "dead"

    if update:
        try:
            get_client().table("leads").update(update).eq("email", recipient).execute()
        except Exception:
            pass

    return {"ok": True}


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
    from database.client import update_lead
    try:
        update_lead(lead_id, {"email_opened": True})
    except Exception:
        pass
    return Response(content=_PIXEL, media_type="image/gif",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@app.get("/track/click/{lead_id}")
async def track_click(lead_id: str, url: str = "https://practicedesk.netlify.app"):
    from database.client import update_lead
    from fastapi.responses import RedirectResponse
    try:
        update_lead(lead_id, {"email_clicked": True, "email_opened": True})
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
