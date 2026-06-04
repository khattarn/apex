# Apex — Claude Working Context

This file is read automatically by Claude Code at the start of every session.
It contains everything needed to continue work without losing context.

---

## Who You Are Working With

**Founder:** Neeraj Khattar · khattarn3@yahoo.com
**Portfolio:** 2 live SaaS products + 1 multi-agent platform (Apex) under construction

---

## The Portfolio (3 repos)

### 1. LegalAidAI / Nyaya Saathi
- **Repo:** `D:\lawaid\LawAidN\Beta3` (git — already on GitHub)
- **Live:** https://www.legalaidai.in
- **Products:** `/citizen` · `/advocate` · `/corporate`
- **Market:** India — 1.4B citizens, 1.7M advocates
- **Stack:** Netlify (static + Node.js functions) · Firebase Firestore · Anthropic Claude (Sonnet + Haiku) · Indian Kanoon API · Razorpay · Meta WhatsApp API · Vapi.ai voice
- **Pricing:** ₹2,500/mo first month · ₹5,000/mo renewal (advocate); freemium for citizens
- **Payments:** Razorpay — already wired
- **Firebase:** Already on Blaze plan ✅

### 2. PracticeDesk
- **Repo:** `C:\Projects\Practice desk` (separate git)
- **Live:** https://practicedesk.netlify.app
- **Market:** Australia · USA · Global
- **Verticals:** Dentists · Salons · Accountants · Physiotherapists
- **Stack:** Netlify (static + Node.js functions) · Supabase (PostgreSQL) · JWT auth · Anthropic Claude · Meta WhatsApp API · Vapi.ai + Twilio + Deepgram · Cal.com · Stripe (stubbed)
- **Pricing:** $49/month Starter · $99/month Growth · $180/month Pro · 14-day free trial
- **Pending:** Stripe billing not wired · Supertonic TTS not deployed · medical_migration.sql not run

### 3. Apex (THIS REPO)
- **Repo:** `C:\Projects\apex` (this repo — pushed to GitHub)
- **Purpose:** Internal multi-agent platform that promotes, sells, and operates LegalAidAI and PracticeDesk
- **Not customer-facing** — founder operations tool
- **Hosting:** Admin dashboard → Netlify · Python agents → Railway (~$5/mo)

---

## What Is Built in This Repo

### `outreach-agent/` — Python FastAPI (COMPLETE, runs locally)

The 3-step pipeline: **Prospect → Personalise → Send**

```
outreach-agent/
├── server.py              ← FastAPI app, all endpoints, SSE streaming
├── pipeline.py            ← async generator orchestrating all 3 steps
├── agents/
│   ├── prospector.py      ← Google Maps Places API — finds businesses by type + city
│   ├── personalizer.py    ← Claude Haiku — generates personalised WA message per business
│   └── outreach.py        ← Meta WhatsApp Cloud API — sends messages
├── database/
│   └── client.py          ← Supabase CRUD (leads, campaign_runs, settings tables)
├── requirements.txt
└── .env                   ← all keys filled in (never commit this)
```

**To run:**
```bash
cd outreach-agent
python server.py            # starts FastAPI on :8000
```

**Key env vars in `.env`:**
```
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_KEY
GOOGLE_MAPS_API_KEY
OUTREACH_WA_PHONE_NUMBER_ID=1122821020915109   ← dedicated outreach number
WHATSAPP_TOKEN
```

**Dedicated WA outreach number:** +91 120 427 9928 (separate from PracticeDesk's customer-facing number)

### `admin-dashboard/` — React + Vite (COMPLETE, runs locally)

Five views:

| View | File | Purpose |
|---|---|---|
| Dashboard | `Dashboard.jsx` | Stats cards + funnel charts + recent leads |
| Run Pipeline | `RunPipeline.jsx` | Form (type/city/count/mode) + live SSE log |
| Leads Table | `LeadsTable.jsx` | Paginated leads, filters, manual send, preview message |
| Campaigns | `Campaigns.jsx` | Pipeline run history |
| Settings | `Settings.jsx` | WA prompt template editor, API health checks, danger zone |

**To run:**
```bash
cd admin-dashboard
npm run dev                 # starts on :5173
```

**Talks to:** `http://localhost:8000` (the FastAPI server above)

**Update `admin-dashboard/.env` when Railway is deployed:**
```
VITE_API_URL=https://apex-outreach.up.railway.app
```

---

## Supabase Schema (shared with PracticeDesk)

```sql
leads           — id, name, address, place_id (unique), phone, website,
                  business_type, city, status, outreach_sent, outreach_message,
                  outreach_date, notes, created_at

campaign_runs   — id, business_type, city, max_prospects, mode, prospects_found,
                  new_leads, messages_sent, log, created_at

settings        — key (PK), value, updated_at
                  Seeded: key='whatsapp_prompt_template'
```

**Lead statuses:** `new → contacted → replied → converted → dead`

---

## The 11 Agents (build order)

| # | Agent | Status | Where it lives |
|---|---|---|---|
| 1 | Prospector | ✅ Live | `outreach-agent/agents/prospector.py` |
| 2 | Personalizer | ✅ Live | `outreach-agent/agents/personalizer.py` |
| 3 | Outreach | ✅ Live | `outreach-agent/agents/outreach.py` |
| 4 | Reply Handler | 🔨 Next | New Netlify function: `reply-handler/outreach-webhook.js` |
| 5 | Demo Booking | 📋 Planned | Handles interested replies → Cal.com demo link |
| 6 | Follow-up | 📋 Planned | 3-day silence → sends follow-up WA message |
| 7 | Voice Follow-up | 📋 Planned | 5-day silence → Vapi outbound call |
| 8 | Content | 📋 Planned | Weekly LinkedIn/Instagram posts |
| 9 | Re-engagement | 📋 Planned | Churned users win-back sequences |
| 10 | Observatory | 📋 Planned | Daily cost/usage digest → your WhatsApp |
| 11 | Affiliate Tracker | 📋 Planned | Referral links + ₹500/₹500 commissions |

---

## What to Build Next (priority order)

### Priority 1 — Deploy outreach server to Railway

Makes the admin dashboard live (not just local).

```bash
npm install -g @railway/cli
railway login
cd outreach-agent
railway init        # project name: apex-outreach
railway up
railway variables set ANTHROPIC_API_KEY=...
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_KEY=...
railway variables set GOOGLE_MAPS_API_KEY=...
railway variables set OUTREACH_WA_PHONE_NUMBER_ID=1122821020915109
railway variables set WHATSAPP_TOKEN=...
```

After deploy: update `admin-dashboard/.env` → `VITE_API_URL=https://apex-outreach.up.railway.app`
Then deploy admin-dashboard to Netlify (static site, `npm run build` → publish `dist/`).

**railway.toml** (create in `outreach-agent/`):
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python server.py"
healthcheckPath = "/health"
restartPolicyType = "always"
```

---

### Priority 2 — Wire WA Reply Handler (Netlify function)

When leads reply to +91 120 427 9928, nothing currently catches it.

Create `reply-handler/outreach-webhook.js` as a Netlify function on the **PracticeDesk Netlify site** (already deployed, Meta can reach it immediately):

URL will be: `https://practicedesk.netlify.app/.netlify/functions/outreach-webhook`

This function must:
1. Handle Meta webhook verification (GET with `hub.challenge`)
2. On POST: extract sender phone + message text
3. Look up sender in Supabase `leads` table by phone
4. If found: update `status → replied`, log message
5. Use Claude Haiku to classify intent: `interested | not_interested | question | out_of_office`
6. If `question`: Claude generates reply → send via WA
7. If `interested`: send demo booking message with Cal.com link
8. If `not_interested`: set status → `dead`

**Important:** Register this webhook URL in Meta Developer Console under the outreach WhatsApp number (Phone Number ID: 1122821020915109), separate from the main PracticeDesk webhook.

---

### Priority 3 — Observatory Agent

Daily cron (Railway, runs at 7am IST) that:
1. Queries Anthropic API for yesterday's token usage
2. Queries Supabase for lead counts, conversion rates
3. Queries Vapi for voice minutes used
4. Posts a WhatsApp digest to Neeraj's personal number

Message format:
```
📊 Apex Daily — [date]

Anthropic: $X.XX (↑/↓ vs yesterday)
WA messages sent: X
Leads added: X | Converted: X
Voice minutes: X

Pipeline last ran: [time] — [city] [type]
```

---

### Priority 4 — Affiliate Tracking (LegalAidAI)

New Supabase tables:
```sql
affiliates    — id, name, instagram_handle, bar_enrollment, upi_id,
                referral_code (unique), status, created_at
referrals     — id, affiliate_id, user_id, product, signup_date,
                converted_to_paid, conversion_date
commissions   — id, affiliate_id, referral_id, amount (500), type (conversion|renewal),
                status (pending|paid), paid_date
```

Commission structure:
- ₹500 on first paid subscription
- ₹500 on first renewal
- Flat rate, no tiers yet

Referral link format: `legalaidai.in/advocate?ref=RAHUL123`

---

## Org Structure for Apex

```
Neeraj (Founder)
        │
   ─────┴───────────────────────
   │               │             │
VP Marketing   GM Care      Observatory
(human apex)  (human apex)  (AI only → reports to Neeraj)

VP Marketing oversees agents 1-3, 6, 8, 9, 11
GM Care oversees agents 4, 5, 7
Observatory = agent 10
```

---

## External Services Used Across Portfolio

| Service | Products | Key env var |
|---|---|---|
| Anthropic Claude | All | `ANTHROPIC_API_KEY` |
| Supabase | PracticeDesk + Apex | `SUPABASE_URL`, `SUPABASE_KEY` |
| Firebase Firestore | LegalAidAI | Firebase config in `firebase-config.js` |
| Meta WhatsApp API | All | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |
| Meta WhatsApp (outreach) | Apex | `OUTREACH_WA_PHONE_NUMBER_ID=1122821020915109` |
| Vapi.ai | PracticeDesk + LegalAidAI | `VAPI_API_KEY`, `VAPI_ACCOUNT_ID` |
| Twilio | PracticeDesk | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` · number: +1 (385) 363-3720 |
| Deepgram | PracticeDesk | `DEEPGRAM_API_KEY` |
| Razorpay | LegalAidAI | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` |
| Stripe | PracticeDesk (not wired) | `STRIPE_SECRET_KEY` |
| Indian Kanoon | LegalAidAI | `IK_API_KEY` |
| Google Maps | Apex outreach | `GOOGLE_MAPS_API_KEY` |
| Cal.com | PracticeDesk | `CAL_API_KEY`, `CAL_USERNAME` |
| Resend | LegalAidAI | `RESEND_API_KEY` |
| Railway | Apex (planned) | Deployment platform for FastAPI |
| Netlify | All | Deployment + serverless functions |

---

## Critical Conventions

**Never break these:**

1. **Outreach WA number** (`OUTREACH_WA_PHONE_NUMBER_ID=1122821020915109`) is separate from PracticeDesk's customer WA number. Never mix them.

2. **Supabase is shared** between PracticeDesk main platform and Apex outreach agent. The `leads`, `campaign_runs`, `settings` tables belong to Apex. The `professionals`, `bookings`, `contacts` etc. belong to PracticeDesk. Don't query across them carelessly.

3. **FastAPI server** (`server.py`) uses SSE (Server-Sent Events) for pipeline streaming. The React dashboard consumes this with `EventSource`. Do not change this to WebSockets without updating both sides.

4. **Pipeline is async** — `pipeline.py` is an async generator. `server.py` iterates it and streams each log line. Do not make it synchronous.

5. **Lead deduplication** is by `place_id` (Google Maps unique ID). Never insert without checking for existing `place_id`.

6. **Business types** must match: `dentist | salon | accountant | physiotherapist | lawyer`. The personalizer has profession-specific pain point copy for each. Adding a new type requires updating `PROFESSION_CONTEXT` in `personalizer.py`.

---

## How to Run the Full Stack Locally

```bash
# Terminal 1 — Python backend
cd outreach-agent
python server.py
# → FastAPI running on http://localhost:8000

# Terminal 2 — React frontend
cd admin-dashboard
npm run dev
# → Dashboard at http://localhost:5173

# Login: khattarn3@yahoo.com
```

---

## Repo Structure (current state)

```
apex/
├── outreach-agent/          ← Python FastAPI (moved from practicedesk-agent/)
│   ├── server.py
│   ├── pipeline.py
│   ├── agents/
│   │   ├── prospector.py
│   │   ├── personalizer.py
│   │   └── outreach.py
│   ├── database/client.py
│   ├── requirements.txt
│   └── .env
├── admin-dashboard/         ← React + Vite (moved from admin-dashboard/)
│   ├── src/views/
│   │   ├── Dashboard.jsx
│   │   ├── RunPipeline.jsx
│   │   ├── LeadsTable.jsx
│   │   ├── Campaigns.jsx
│   │   └── Settings.jsx
│   └── package.json
├── docs/
│   └── ARCHITECTURE.md      ← full portfolio reference
├── CLAUDE.md                ← this file
└── README.md
```

---

## Reference Documents

| File | Location | Purpose |
|---|---|---|
| `CLAUDE.md` | `apex/` (this file) | VS Code / Claude Code working context |
| `ARCHITECTURE.md` | `apex/docs/` | Full portfolio + services + cost map |
| `HANDOVER.md` | `C:\Projects\Practice desk\` | PracticeDesk full technical handover |
| `FILE-STRUCTURE.md` | `D:\lawaid\LawAidN\Beta3\documentation\` | LegalAidAI file reference |
| `TECH-HEALTH.md` | `D:\lawaid\LawAidN\Beta3\documentation\` | LegalAidAI capacity + cost projections |
| `PENDING.md` | `D:\lawaid\LawAidN\Beta3\` | LegalAidAI pending features |
| `MASTER-PROJECT-REFERENCE.md` | `D:\lawaid\LawAidN\Beta3\documentation\` | LegalAidAI marketing reference |
