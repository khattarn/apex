# Apex — Master Portfolio & Architecture Reference
**Owner:** Neeraj Khattar · khattarn3@yahoo.com
**Last updated:** May 2026
**Purpose:** Single source of truth for all products, infrastructure, services, and the Apex multi-agent platform.

---

## Portfolio Overview

| Product | URL | Market | Status | Revenue Model |
|---|---|---|---|---|
| Nyaya Saathi — Citizen | legalaidai.in/citizen | India (1.4B citizens) | Live (Beta 3) | Freemium — ₹499/mo premium |
| Nyaya Saathi — Advocate | legalaidai.in/advocate | India (1.7M advocates) | Live (Beta 3) | ₹2,500/mo · ₹5,000 renewal |
| Nyaya Saathi — Corporate | legalaidai.in/corporate | India (corporates) | Live (Beta 3) | ₹5,000+/mo |
| PracticeDesk | practicedesk.netlify.app | AU / USA / Global | Live (Beta) | $49 · $99 · $180/mo |
| **Apex** | TBD (internal) | All markets | **Building now** | Internal tool — drives all above |

---

## 1. Nyaya Saathi / LegalAidAI

**Brand name:** Nyaya Saathi (meaning "Legal Companion")
**Repo:** `D:\lawaid\LawAidN\Beta3`
**Deployed:** Netlify (static + serverless functions)

### What It Does

A two-sided AI legal platform for India:
- **Citizen panel** (`/citizen`) — free bilingual (English/Hindi) legal assistant. Know your rights, draft notices, manage cases, voice input/output.
- **Advocate panel** (`/advocate`) — professional AI research & drafting studio. Claude Sonnet + Indian Kanoon real case law, 12+ court templates, commercial courts module.
- **Corporate panel** (`/corporate`) — in-house counsel tools. Compliance, contracts, regulatory feeds.

### Tech Stack

| Layer | Technology |
|---|---|
| Hosting | Netlify (static site + serverless functions) |
| Frontend | Vanilla HTML/CSS/JS — no framework |
| Backend | Netlify Functions (Node.js 18) |
| Database | Firebase Firestore (auth + user data) |
| AI | Anthropic Claude Sonnet (research/drafting) + Claude Haiku (chat) |
| Case Law | Indian Kanoon API (real-time verified citations) |
| Payments | Razorpay (Indian cards, UPI, net banking) |
| Email | Resend |
| WhatsApp | Meta WhatsApp Cloud API |
| Voice | Vapi.ai + voice-outreach-trigger |
| OCR | Document upload + extraction |
| PWA | manifest.json + service worker |

### Key Frontend Files

| File | Purpose |
|---|---|
| `nyaya-saathi-v2.html` | Citizen panel (main app — auth + AI + templates) |
| `advocate.html` | Advocate panel (research + drafting studio) |
| `corporate.html` | Corporate panel |
| `admin-dashboard.html` | Admin console (users, analytics, plans) |
| `intake.html` | Client intake form |
| `feedback.html` | User feedback |
| `index.html` | Landing page |

### Key Netlify Functions

| Function | Purpose |
|---|---|
| `auth.js` | Signup, login, Firebase auth |
| `ai-chat.js` | Claude API — citizen chat |
| `enhance-document.js` | Claude Sonnet — document enhancement |
| `get-documents.js` | Document retrieval |
| `generate-pdf.js` | PDF generation |
| `generate-invoice.js` | Invoice generation |
| `send-invoice.js` | Email invoice via Resend |
| `ocr-document.js` | Document OCR |
| `upload-document.js` | Document storage |
| `razorpay-create-order.js` | Payment order creation |
| `razorpay-verify.js` | Payment verification |
| `razorpay-webhook.js` | Razorpay event handler |
| `whatsapp-outreach.js` | WA outreach sends |
| `whatsapp-service.js` | WA messaging service |
| `send-wa-batch-background.js` | Bulk WA morning batch |
| `send-wa-batch-afternoon-background.js` | Bulk WA afternoon batch |
| `wa-reengagement-cron.js` | Re-engagement cron |
| `voice-assistant-config.js` | Vapi voice config |
| `voice-outreach-trigger.js` | Outbound voice calls |
| `voice-webhook.js` | Vapi event handler |
| `outreach-apollo.js` | Apollo.io prospecting |
| `outreach-bulk-import.js` | Bulk lead import |
| `outreach-management.js` | Lead CRM management |
| `subscription-reminder.js` | Renewal reminders |
| `send-email.js` | Transactional email |
| `regulatory-feed-cron.js` | Daily regulatory updates |
| `regulatory-feed.js` | Regulatory content API |
| `ik-search.js` | Indian Kanoon search |
| `ik-verify.js` | IK citation verification |
| `ik-status.js` | IK service status |
| `corporate-chat.js` | Corporate AI chat |
| `self-register.js` | Self-service advocate signup |
| `admin.js` | Admin CRUD operations |
| `update-usage.js` | Usage tracking |
| `log-event.js` | Event logging |

### Pending (from PENDING-FUNCTIONALITIES.md)

- Child custody petition, maintenance application, RCR notice templates
- E-Courts API integration (real-time case tracking)
- Bulk document generation (CSV upload)
- Vakalatnama generator
- Court fee calculator
- Regional language support (Marathi, Tamil, Bengali, Kannada)
- Native mobile apps (iOS/Android)
- White-labelling for law firms
- Multi-document comparison in Research Studio

### Capacity & Cost (from TECH-HEALTH.md)

| Scale | Monthly Cost | Revenue (est.) |
|---|---|---|
| 500 MAU / 7 premium | ~₹550 | ~₹4,500 |
| 2,000 MAU / 30 premium | ~₹2,300 | ~₹18,000 |
| 6,000 MAU / 90 premium | ~₹9,000 | ~₹55,000 |
| 20,000 MAU / 300 premium | ~₹26,500 | ~₹1,80,000 |

**Pending infra action:** Upgrade Firebase to Blaze plan before any marketing push.

---

## 2. PracticeDesk

**Repo:** `C:\Projects\Practice desk`
**Deployed:** practicedesk.netlify.app
**Outreach agent:** `practicedesk-agent/` (Python + FastAPI — runs locally, needs Railway)

### What It Does

AI-powered practice management for solo professionals (dentists, salons, accountants, physios). One subscription gives them: professional website, online booking, WhatsApp AI receptionist, voice agent that answers calls 24/7.

### Tech Stack

| Layer | Technology |
|---|---|
| Hosting | Netlify (static + serverless functions) |
| Frontend | Vanilla HTML/CSS/JS — no framework |
| Backend | Netlify Functions (Node.js) |
| Database | Supabase (PostgreSQL + RLS) |
| Auth | JWT (jsonwebtoken + bcryptjs, 7-day expiry) |
| AI | Anthropic Claude Sonnet (receptionist) + Haiku (outreach) |
| WhatsApp | Meta WhatsApp Cloud API |
| Voice | Vapi.ai + Twilio + Deepgram STT |
| TTS | Supertonic (Railway — not yet deployed) |
| Bookings | Cal.com API v2 |
| Billing | Stripe (stubbed — not wired) |
| Prospecting | Google Maps Places API |
| Outreach DB | Supabase (shared instance) |

### Key Files

| File | Purpose |
|---|---|
| `pro-dashboard.html` | Professional's main app (~2500 lines) |
| `admin.html` | Admin console |
| `booking.html` | Public booking page |
| `setup.html` | Professional signup wizard |
| `site/medical.html` | Public website — medical template |
| `site/salon.html` | Public website — salon template |
| `site/ca.html` | Public website — CA/accounting template |
| `netlify/functions/webhook.js` | Inbound WhatsApp + booking flow engine |
| `netlify/functions/ai-reply.js` | Claude AI module |
| `netlify/functions/voice-setup.js` | Creates Vapi assistant |
| `netlify/functions/voice-webhook.js` | Vapi tool calls |
| `netlify/functions/reminders.js` | Hourly appointment reminders |
| `netlify/functions/broadcast.js` | Bulk WhatsApp sends |
| `practicedesk-agent/pipeline.py` | 3-step outreach: prospect→personalise→send |
| `practicedesk-agent/agents/prospector.py` | Google Maps lead finder |
| `practicedesk-agent/agents/personalizer.py` | Claude Haiku message writer |
| `practicedesk-agent/agents/outreach.py` | WhatsApp sender |
| `admin-dashboard/` | React + Vite dashboard (5 views) |

### Supabase Tables

Main: `professionals`, `bookings`, `contacts`, `conversations`, `messages`, `staff`, `broadcasts`, `knowledge_base`, `feedback`, `call_logs`, `admin_log`, `daily_stats`

Outreach: `leads`, `campaign_runs`, `settings`

### Pending (from HANDOVER.md)

1. Run `medical_migration.sql` in Supabase — rename dentist→medical
2. **Wire WA reply handler** for outreach number +91 120 427 9928
3. CRM + Birthday Greetings (DOB, anniversary, holiday WA)
4. Deploy Supertonic TTS to Railway
5. **Provision first voice agent** via admin panel
6. PWA icons
7. Wire Stripe billing

---

## 3. External Services — Full Register

| Service | Used By | Purpose | Cost Trigger |
|---|---|---|---|
| Anthropic (Claude) | Both | AI chat, drafting, outreach copywriting | Per token — monitor monthly |
| Firebase Firestore | LegalAidAI | User auth + data | Free to ~3K MAU; Blaze after |
| Supabase | PracticeDesk | PostgreSQL + RLS | Free to 500MB |
| Netlify | Both | Hosting + serverless functions | Free to 125K fn invocations/mo |
| Railway | PracticeDesk (planned) | FastAPI outreach server | ~$5/month |
| Meta WhatsApp API | Both | Customer + outreach messaging | Per message after 1K free/mo |
| Vapi.ai | Both | Voice agent orchestration | Per minute |
| Twilio | PracticeDesk | Phone number (+1 385 363-3720) | Per call/min |
| Deepgram | PracticeDesk | Speech-to-text | Per minute |
| Supertonic | PracticeDesk | TTS greeting audio | Railway hosting cost |
| Razorpay | LegalAidAI | Indian payments (UPI, cards) | 2% per transaction |
| Stripe | PracticeDesk | International payments | 2.9% + $0.30 (not wired yet) |
| Indian Kanoon | LegalAidAI | Legal case law API | Per query |
| Google Maps | PracticeDesk outreach | Business prospecting | Per request (free tier generous) |
| Cal.com | PracticeDesk | Appointment slots | Free / paid plans |
| Resend | LegalAidAI | Transactional email | Free to 3K/mo |
| Apollo.io | LegalAidAI | B2B lead prospecting | Subscription |
| ElevenLabs | PracticeDesk (optional) | TTS alternative | Per character |

---

## 4. Apex — The Multi-Agent Platform

**What it is:** An internal command platform that promotes, sells, and operates all products above. Not a customer-facing product — a founder operations tool.

**Repo name:** `apex`
**Recommended hosting:** Admin dashboard → Netlify · Python agents → Railway

### Apex Org Structure

```
Neeraj (Founder)
        │
   ─────┴──────────────────────────
   │              │                │
VP Marketing   GM Customer Care  Observatory Agent
(human apex)   (human apex)      (reports to founder)
   │                │
[AI agents]      [AI agents]
```

### Apex Agents

| # | Agent | Status | Function |
|---|---|---|---|
| 1 | Prospector | Live | Finds leads via Google Maps by city + profession |
| 2 | Personalizer | Live | Claude Haiku — writes tailored WA/email messages |
| 3 | Outreach | Live | Sends via Meta WA API (dedicated number) |
| 4 | Reply Handler | Planned | Catches WA replies, classifies intent, auto-responds |
| 5 | Demo Booking | Planned | Converts interested leads to booked demos |
| 6 | Follow-up | Planned | Re-engages leads silent after 3-4 days |
| 7 | Voice Follow-up | Planned | Vapi outbound call for unresponsive leads |
| 8 | Content | Planned | Weekly social posts for LinkedIn/Instagram |
| 9 | Re-engagement | Planned | Wins back churned/lapsed users |
| 10 | Observatory | Planned | Daily cost/usage digest — all services |
| 11 | Affiliate Tracker | Planned | Tracks referrals + ₹500/₹500 commission payouts |

### Apex Repo Structure

```
apex/
├── outreach-agent/              ← Python FastAPI (built — move from practicedesk-agent/)
│   ├── server.py
│   ├── pipeline.py
│   ├── agents/
│   │   ├── prospector.py
│   │   ├── personalizer.py
│   │   └── outreach.py
│   └── database/client.py
├── admin-dashboard/             ← React + Vite (built — move from admin-dashboard/)
│   └── src/views/
│       ├── Dashboard.jsx
│       ├── RunPipeline.jsx
│       ├── LeadsTable.jsx
│       ├── Campaigns.jsx
│       └── Settings.jsx
├── reply-handler/               ← Netlify function (Node.js) — to build
│   └── outreach-webhook.js
├── voice-agent/                 ← Vapi outbound config — to build
│   └── vapi-outbound.py
├── observatory/                 ← Daily cost monitor — to build
│   └── monitor.py
├── affiliate/                   ← Affiliate tracking — to build
│   ├── server.py
│   └── dashboard/
├── docs/
│   ├── ARCHITECTURE.md          ← This file
│   └── HANDOVER.md
├── railway.toml                 ← Railway deployment
└── README.md
```

### Affiliate Programme (LegalAidAI — confirmed)

- **Target:** Young Indian advocates who are Instagram influencers
- **Commission:** ₹500 on first paid subscription + ₹500 on first renewal
- **Structure:** Flat rate
- **Payout:** UPI (GPay / PhonePe / Paytm)
- **Tracking:** Unique referral codes → Supabase `affiliates` + `referrals` + `commissions` tables

### PracticeDesk Pricing (confirmed)

- **Pricing:** $49/month Starter · $99/month Growth · $180/month Pro · 14-day free trial
- **Market:** AU / USA / Global
- **Affiliate commission:** $15 on conversion + $15 on renewal (TBC)

---

## 5. Git Repos — Recommended Structure

| Repo | What | Where |
|---|---|---|
| `lawaid` (existing) | LegalAidAI (Nyaya Saathi) — all 3 verticals | `D:\lawaid\LawAidN\Beta3` — already has git |
| `practicedesk` (existing) | PracticeDesk main platform | `C:\Projects\Practice desk` |
| `apex` (create now) | Multi-agent marketing + ops platform | New — `C:\Projects\apex` |

### Create the Apex repo

```bash
cd C:\Projects
mkdir apex
cd apex
git init
git remote add origin https://github.com/YOUR_USERNAME/apex.git
```

Then move `practicedesk-agent/` and `admin-dashboard/` into `apex/` and commit.

---

## 6. Railway Setup (for Apex outreach server)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# From inside apex/outreach-agent/
railway init        # creates new project called "apex-outreach"
railway up          # deploys server.py

# Set env vars
railway variables set ANTHROPIC_API_KEY=...
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_KEY=...
railway variables set GOOGLE_MAPS_API_KEY=...
railway variables set OUTREACH_WA_PHONE_NUMBER_ID=1122821020915109
railway variables set WHATSAPP_TOKEN=...
```

After deploy, Railway gives you a URL like `https://apex-outreach.up.railway.app`.
Update `admin-dashboard/.env` → `VITE_API_URL=https://apex-outreach.up.railway.app`

---

## 7. What to Build Next (priority order)

1. **Create `apex` git repo** — move outreach agent + dashboard in
2. **Deploy outreach server to Railway** — makes admin dashboard live
3. **Wire WA reply handler** (Netlify function) — catches replies to +91 120 427 9928
4. **Provision LegalAidAI voice outreach** — `voice-outreach-trigger.js` already exists
5. **Observatory Agent** — daily cost digest to your WhatsApp
6. **Affiliate tracking system** — registration, unique links, Supabase commission tracking
7. **Upgrade Firebase to Blaze** — required before LegalAidAI marketing push
8. **Wire Stripe for PracticeDesk** — last blocker before paid signups

---

## 8. Key Credentials Reference (do not share this file publicly)

| Service | Key/ID | Notes |
|---|---|---|
| WA Outreach number | +91 120 427 9928 | Phone Number ID: 1122821020915109 · WABA: 2574949406008734 |
| Twilio number | +1 (385) 363-3720 | SID: PN6c06449e4ca56a281b07d3f889926185 |
| Vapi | `VAPI_API_KEY` + `VAPI_ACCOUNT_ID` | Set in Netlify env vars |
| Supabase | `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` | PracticeDesk only |
| Firebase | Project config in `firebase-config.js` | LegalAidAI only |
| Razorpay | `RAZORPAY_KEY_ID` + `RAZORPAY_KEY_SECRET` | LegalAidAI India payments |
| Anthropic | `ANTHROPIC_API_KEY` | Shared across all products |

---

*This document is auto-maintained. Update after every new service, feature, or architectural change.*
