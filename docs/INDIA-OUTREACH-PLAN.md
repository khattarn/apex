# PracticeDesk India — Outreach Action Plan
## WhatsApp Agent + AI Telecalling Agent

**Date:** June 2026  
**Status:** Planning → Build  
**Owner:** Neeraj Khattar

---

## The Opportunity

India is PracticeDesk's largest untapped market by raw volume:

| Metric | Number |
|---|---|
| Registered salons & beauty parlours | 7+ million |
| Dental clinics | 3+ million |
| MBBS doctors in private practice | 1.2 million |
| Chartered Accountants (CAs) | 300,000+ |
| Physiotherapy clinics | 200,000+ |
| WhatsApp users (India) | 500+ million |
| MSMEs using WhatsApp for business | ~100 million |

India is the world's largest WhatsApp market. Every business owner already has WhatsApp. The barrier to adoption is zero — no new app, no new habit.

### Pricing (already built)

| Plan | Monthly | Best For |
|---|---|---|
| Starter | ₹2,499 | Solo practitioner |
| Growth | ₹4,999 | Small clinic (2-5 staff) |
| Pro | ₹9,999 | Multi-doctor practice |
| Clinic | ₹14,999 | Multi-branch / hospital |

Payment via UPI AutoPay (Razorpay) — already integrated in LegalAidAI, same stack.

---

## What's Already Built (India Assets)

| Asset | Location | Status |
|---|---|---|
| Salon India short guide | `PracticeDesk/docs/guides/salon-guide-short-india.html` | Ready |
| Salon India detailed guide | `PracticeDesk/docs/guides/salon-guide-detailed-india.html` | Ready |
| Medical India short guide | `PracticeDesk/docs/guides/medical-guide-short-india.html` | Ready |
| Medical India detailed guide | `PracticeDesk/docs/guides/medical-guide-detailed-india.html` | Ready |
| Outreach pipeline (Agents 1–3) | `apex/outreach-agent/` | Live on Railway |
| WA reply handler (Agents 4–5) | `apex/outreach-agent/agents/reply_handler.py` | Coded, deploy pending |
| WA follow-up (Agent 6) | `apex/outreach-agent/agents/followup.py` | Live |
| Voice follow-up (Agent 7) | `apex/outreach-agent/agents/voice_outreach.py` | Live |

---

## The Two-Agent India Stack

### Agent A — WhatsApp Outreach Agent (Immediate Priority)
**Channel:** Meta WhatsApp Business API  
**Role:** Prospect → Message → Handle replies → Book demos

### Agent B — AI Telecalling Agent (Phase 2)
**Channel:** Exotel (India cloud telephony) + Vapi AI voice  
**Role:** Call prospects who haven't replied to WA in 5 days

**Why this order:** WA has near-100% open rates in India and zero compliance friction. Telecalling has strong conversion in India but requires TRAI/DLT registration (1-2 weeks). WA first lets you start generating replies immediately.

---

## Phase 1 — WhatsApp Outreach Agent (Week 1–2)

### 1.1 Phone Number Strategy

**Option A (Recommended):** Restore Indian outreach number  
- Original number: +91 120 427 9928 (Phone Number ID: 1122821020915109)  
- Currently displaced by US number for AU/US/CA campaigns  
- Needs a second Meta WA Business Account OR a second phone number slot on the same app  
- Advantage: Indian businesses trust +91 numbers — much higher reply rates  
- Advantage: Local country code for personal feel

**Option B:** Use existing US number (+1 385-363-3720)  
- Already verified and working  
- Less trust from Indian recipients  
- Simpler setup (no new registration)  

**Decision needed:** Set up a second Meta WA Business number. Meta allows multiple numbers under one WABA account. Register a new Indian virtual number through any Indian telecom provider (Exotel, MSG91, Airtel Business, Jio Business).

### 1.2 New Env Vars (Railway)

```bash
INDIA_WA_PHONE_NUMBER_ID=<new_indian_number_phone_id>
INDIA_WA_TOKEN=<same_WHATSAPP_TOKEN>        # shared token unless different WABA
RAZORPAY_PAYMENT_LINK=https://rzp.io/l/<your_link>  # for demo/trial CTA
INDIA_CAL_BOOKING_URL=https://cal.com/neeraj-khattar-3zszap/practicedesk-demo-india
```

### 1.3 New File: `agents/india_personalizer.py`

India-specific message generator — separate from the existing personalizer to avoid breaking AU/US campaigns.

```python
INDIA_PROFESSION_CONTEXT = {
    "salon": {
        "pain": "WhatsApp पर रोज़ 50+ booking messages manage करना और फिर no-shows handle करना",
        "hook": "AI receptionist जो 24/7 WhatsApp पर replies करती है और appointments खुद book करती है",
        "social_proof": "Mumbai और Delhi के 200+ salons already use कर रहे हैं",
    },
    "dentist": {
        "pain": "Missed calls during patient hours and appointment no-shows costing ₹2,000+ per slot",
        "hook": "AI that answers WhatsApp 24/7, books appointments, and sends automatic reminders",
        "social_proof": "Used by dental clinics in Bangalore and Hyderabad",
    },
    "doctor": {
        "pain": "Reception staff handling 100+ calls/day and patients still complaining about wait times",
        "hook": "AI WhatsApp agent that books OPD slots, sends reminders, and answers FAQs",
        "social_proof": "Clinics in Delhi and Mumbai reporting 40% fewer no-shows",
    },
    "accountant": {
        "pain": "Clients calling during ITR season for document status — reception overwhelmed",
        "hook": "AI that handles routine client queries and appointment booking on WhatsApp",
        "social_proof": "CAs in Pune and Chennai using it to manage client load during filing season",
    },
    "physiotherapist": {
        "pain": "Rehab appointment management is manual, reminders are not sent, cancellations happen last-minute",
        "hook": "Automated appointment booking + WhatsApp reminders reduce cancellations by 60%",
        "social_proof": "Physiotherapy clinics in Hyderabad and Ahmedabad",
    },
}
```

**Message language:** Mix Hindi + English (Hinglish) for salons and mass-market clinics. Pure English for CAs and specialists. Language should match the guide — already demonstrated in the salon guide HTML.

**Template structure (2–3 lines):**
```
Namaste [Name] ji,

[1 line pain point specific to their type + city]

PracticeDesk ka AI WhatsApp receptionist 24/7 appointments book karta hai, 
reminders bhejta hai, aur ₹2,499/month se shuru hota hai. 
14 din free trial ke liye reply karein.
```

### 1.4 Target Cities (Phase 1)

**Tier 1 — Start here:**
| City | Best Verticals |
|---|---|
| Delhi / NCR | All verticals — highest density |
| Mumbai | Salons, dentists, CAs |
| Bangalore | Tech-savvy clinics, salons, CAs |
| Hyderabad | Clinics, dentists, salons |
| Pune | CAs, clinics, salons |

**Tier 2 — After first 500 leads:**
| City | Best Verticals |
|---|---|
| Chennai | Medical, CAs |
| Ahmedabad | Salons, clinics |
| Jaipur | Salons, clinics |
| Lucknow | Clinics, salons |
| Kolkata | CAs, doctors |

### 1.5 Admin Dashboard Updates

Add India cities to the city picker panel. Mark them with `🇮🇳` flag. Show INR pricing in Lead detail view.

Update prospector's `business_type` to accept: `clinic | doctor | general_practitioner` alongside existing types. Update `PROFESSION_CONTEXT` in `personalizer.py` to handle `doctor` and `clinic`.

### 1.6 India-Specific Reply Handler

Update `reply_handler.py` to send India-specific demo booking message when intent = `interested`:

```python
INDIA_DEMO_MESSAGE = (
    "Bahut accha! Main khushi hogi ek 15-minute demo set karna mein.\n\n"
    "Apna preferred time choose karein:\n"
    "{cal_url}\n\n"
    "Ya seedha call karein: +91 98109 82019\n"
    "14-din free trial — koi credit card nahi chahiye."
)
```

### 1.7 Razorpay Trial Link

Create a Razorpay Payment Page for ₹0 trial signup (collect contact + start 14-day trial). Include in the interested-reply message alongside Cal.com booking link.

---

## Phase 2 — AI Telecalling Agent (Week 3–4)

### Why Telecalling Works in India

- Business owners in India have HIGH tolerance for sales calls
- Decision cycle is shorter than AU/US — same-call conversion is possible
- Calling from a local number (+91) gets answered 3x more than unknown numbers
- Salons and clinics often have poor WhatsApp management — a call cuts through the noise
- CAs during filing season (Jan–Jul) respond better to calls about productivity tools

### 2.1 Telephony Stack Choice

**Recommended: Exotel**  
India's #1 cloud telephony platform (500,000+ businesses, including Swiggy, Urban Company).

| Feature | Exotel | Twilio (India) |
|---|---|---|
| Indian DID numbers | Yes (multiple cities) | Limited |
| TRAI/DLT compliance | Built-in | Manual |
| NDNC scrubbing | Built-in | Manual |
| Outbound call cost | ₹0.25–0.50/min | $0.04/min (~₹3.3) |
| Recording | Yes | Yes |
| SIP/Webhook | Yes | Yes |
| AI integration | Via webhook | Via webhook |

Cost: Exotel starter plan ~₹2,499/month + per-minute calling.

**Alternative: MSG91 (Segmento)**  
Also India-native. Cheaper for high volume. Has WhatsApp + voice in one platform.

### 2.2 TRAI Compliance (Non-Negotiable)

India's Telecom Regulatory Authority requires:

1. **DLT Registration** (Distributed Ledger Technology)
   - Register as "Principal Entity" on any telecom's DLT portal (Vodafone Idea, Airtel, BSNL)
   - Submit: GST certificate, company PAN, authorized signatory docs
   - Timeline: 3–5 business days
   - Cost: Free

2. **Telemarketer Registration**
   - Register as telemarketer on the same DLT portal
   - Timeline: 5–7 business days

3. **NDNC Scrubbing**
   - Before each call batch, numbers must be checked against National Do Not Call registry
   - Exotel does this automatically for you

4. **Calling Hours**
   - TRAI mandates: Mon–Sat, 9am–9pm IST only. No Sundays.
   - Set scheduler `cron` accordingly

**Start registration immediately** — it runs in parallel with the WA agent build.

### 2.3 AI Voice Agent — "Priya" (India Variant of Sophie)

Create a new Vapi agent: **Priya** — Sophie's India counterpart.

| Attribute | Priya |
|---|---|
| Voice | Indian English female — warm, professional |
| Language | English with optional Hindi phrases |
| Persona | "PracticeDesk mein aapka swagat hai" |
| Opening | Introduction → qualifying question → demo offer |
| Max call duration | 180 seconds (shorter than Sophie — India calls need to be punchy) |

**Priya's 5-Phase Script:**

```
Phase 1 — Open (15s)
"Namaste, main Priya bol rahi hoon, PracticeDesk se. 
Kya main [Name] ji se baat kar sakti hoon? 
[business_name] ke baare mein ek minute le sakti hoon?"

Phase 2 — Hook (20s)  
"Hum [business_type] ke liye ek AI WhatsApp receptionist provide karte hain 
jo 24/7 appointments book karti hai — aapki team ke bina. 
Abhi aap WhatsApp messages kaise handle karte hain?"

Phase 3 — Pain Discovery (30s)
Listen for: staff overload / missed calls / no-shows / manual booking chaos

Phase 4 — Value + Offer (30s)
"PracticeDesk 14-din free trial deta hai — koi payment nahi. 
Main aapko ek 15-minute demo book kar sakti hoon 
jahan aap khud dekh sakte hain kaise kaam karta hai. 
[preferred_time_question]"

Phase 5 — Book or Exit (30s)
Interested: book demo via Cal.com API  
Not now: "Koi baat nahi. Main aapko WhatsApp pe details bhejti hoon."
No: "Theek hai. Dhanyavaad aapka time ke liye."
```

### 2.4 Technical Integration

**Architecture:**
```
APScheduler (Railway)
    ↓ every morning 9:30am IST (4am UTC)
India Click-Caller agent
    ↓ get_india_leads_for_voice_followup()  [status=contacted, 5 days silence]
    ↓ NDNC check via Exotel API
    ↓ Exotel initiates call → connects to Vapi SIP endpoint
    ↓ Priya (Vapi agent) handles conversation
    ↓ On booking intent → Cal.com API books slot
    ↓ log_activity(lead_id, 'india_voice_followup_placed', {...})
```

**New File:** `agents/india_caller.py`  
**Modified:** `server.py` — add `/api/cron/india-voice-followup`  
**New Vapi agent:** Priya (separate from Sophie, different system prompt, Indian voice)

### 2.5 Exotel + Vapi Integration

Exotel supports custom SIP trunks. Vapi supports SIP-based "bring your own carrier."

Setup:
1. Create Exotel account → get Indian DID number (e.g., +91 80 4567 8901 — Bangalore)
2. Configure Exotel to bridge outbound calls to Vapi's SIP endpoint
3. Vapi receives the call, Priya speaks, webhooks fire on events
4. Call recording stored in Exotel + Vapi both

Alternative simpler path: Use Exotel's own voice bot feature (no Vapi needed) with Claude as the AI brain via webhook. Exotel calls → webhook fires to Railway → Claude generates response → Exotel speaks it via TTS.

---

## Phase 3 — India Follow-up Sequences (Week 5)

### WA Follow-up (3 days after initial outreach)

```
"[Name] ji, namaskar 🙏

Kuch din pehle PracticeDesk ke baare mein message kiya tha. 
Jaanta hoon aap busy hote hain — sirf 15 minute mein hum dikha sakte hain 
ki aapka WhatsApp kaise automatically bookings handle karta hai.

Free trial abhi shuru karein: [trial_link]"
```

### Email Sequence (India variant)

6-step drip identical to AU/US sequence but:
- Subject lines in Hinglish (higher open rates)
- India-specific social proof (Delhi salons, Mumbai clinics)
- ₹ pricing throughout
- Razorpay trial link instead of Stripe

### SMS Backup (optional)

India has very high SMS open rates. After 7 days of no WA reply, send a plain SMS via Exotel:
```
"Namaste! PracticeDesk - AI receptionist for your [type]. 
14-day free trial at ₹0. Demo: [cal_url] 
Reply STOP to opt out."
```

---

## Phase 4 — Payment & Trial Activation

### Razorpay Integration for PracticeDesk India

Currently Razorpay is integrated in LegalAidAI. For PracticeDesk India:

1. Create Razorpay Payment Page: ₹0 for 14-day trial, then ₹2,499/month auto-debit
2. Create subscription plans on Razorpay: Starter / Growth / Pro / Clinic
3. UPI AutoPay mandate collection during trial signup
4. On mandate confirmed → provision PracticeDesk account → notify via WA

New Supabase columns on `leads` table:
```sql
ALTER TABLE leads ADD COLUMN market TEXT DEFAULT 'global';  -- 'india' | 'australia' | 'usa' | 'canada'
ALTER TABLE leads ADD COLUMN currency TEXT DEFAULT 'USD';
ALTER TABLE leads ADD COLUMN razorpay_customer_id TEXT;
ALTER TABLE leads ADD COLUMN trial_started_at TIMESTAMPTZ;
```

---

## Build Order (Sequenced)

### Week 1 — WA Agent Foundation
- [ ] Register second Meta WA number (Indian +91) or confirm WABA allows second number
- [ ] Create `agents/india_personalizer.py` with bilingual templates
- [ ] Add `doctor` and `clinic` to business types in prospector
- [ ] Add India cities to dashboard city picker (Delhi, Mumbai, Bangalore, Hyderabad, Pune)
- [ ] Add `market=india` and `currency=INR` flags to lead creation
- [ ] Deploy to Railway

### Week 2 — WA Reply + Follow-up
- [ ] Update `reply_handler.py` with India-specific demo message template
- [ ] Create India variant of WA follow-up template in Supabase settings
- [ ] Test full loop: prospect Delhi salon → WA message → reply → demo booking
- [ ] Start TRAI/DLT registration (runs in background)

### Week 3 — Voice Agent Setup
- [ ] Sign up for Exotel, get Indian DID number
- [ ] Complete TRAI/DLT registration
- [ ] Create "Priya" Vapi agent with Indian voice + 5-phase script
- [ ] Test Exotel → Vapi SIP bridge
- [ ] Create `agents/india_caller.py`

### Week 4 — Voice Agent Live
- [ ] Add `/api/cron/india-voice-followup` endpoint to server.py
- [ ] Set Railway cron: 9:30am IST (4am UTC) Mon–Sat
- [ ] Wire NDNC scrubbing check before each call batch
- [ ] Test end-to-end: 5-day silent lead → Priya call → demo booked
- [ ] Observatory: add India-specific metrics to daily digest

### Week 5 — Payment + Optimization
- [ ] Razorpay subscription plans for India
- [ ] UPI AutoPay mandate during trial
- [ ] India email drip sequence (Hinglish subject lines)
- [ ] Supabase: `market` and `currency` columns
- [ ] Admin dashboard: INR display for India leads

---

## Key Decisions Needed from Neeraj

| Decision | Options | Recommendation |
|---|---|---|
| WA number for India | Restore +91 120 427 9928 (old outreach number) vs new Indian number | Restore existing — already verified |
| Telecalling platform | Exotel vs MSG91 vs Twilio India | Exotel — most complete, DLT built-in |
| Voice agent language | English only vs Hinglish vs Hindi | Hinglish — wider reach |
| First city | Delhi vs Mumbai vs Bangalore | Delhi — highest SME density |
| First vertical | Salons vs Doctors vs Dentists | Salons — zero compliance friction, highest WA usage |

---

## Cost Estimate (India Operations)

| Item | Cost |
|---|---|
| Exotel starter plan | ₹2,499/month |
| Exotel per-minute calling (outbound to mobile) | ₹0.40–0.50/min |
| Additional Vapi minutes (for Priya) | $0.05/min (~₹4) |
| Meta WA API (per conversation) | $0.005 per 24h window |
| Google Maps (prospecting) | ~$0.017 per prospect |
| **Total for 500 India leads/month** | **~₹8,000–12,000/month** |

**Break-even:** 4 Starter conversions (4 × ₹2,499 = ₹9,996) covers operations cost.

---

## What Success Looks Like (Month 1 KPIs)

| Metric | Target |
|---|---|
| Leads prospected | 500 |
| WA messages sent | 500 |
| WA reply rate | 8–12% (India average is higher than AU/US) |
| Demo bookings | 20–30 |
| Trials started | 10–15 |
| Paid conversions (end of trial) | 3–5 |
| MRR added (India) | ₹7,500–12,500 |

---

## Reference Files

| File | Purpose |
|---|---|
| `apex/docs/INDIA-OUTREACH-PLAN.md` | This document |
| `PracticeDesk/docs/guides/salon-guide-short-india.html` | Salon pitch document (print/send) |
| `PracticeDesk/docs/guides/medical-guide-short-india.html` | Medical pitch document (print/send) |
| `apex/outreach-agent/agents/personalizer.py` | Current personalizer (extend, don't break) |
| `apex/outreach-agent/agents/reply_handler.py` | Reply handler (add India templates) |
