import asyncio
import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

sys.path.insert(0, os.path.dirname(__file__))

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
                        prospects_found = int(line.split("Found")[1].split("businesses")[0].strip())
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

            yield {
                "data": json.dumps({
                    "type": "done",
                    "prospects_found": prospects_found,
                    "new_leads": new_leads,
                    "messages_sent": messages_sent,
                })
            }

        except Exception as exc:
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(event_generator())


# ── Leads ─────────────────────────────────────────────────────────────────────

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


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
