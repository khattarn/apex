# LegalAidAI — Voice & WhatsApp Channels

## Source: voice-agent-plan.md

# Nyaya Saathi — Advocate Voice Agent Plan
**Status:** Planning | **Date:** 2026-06-08

---

## Overview

An inbound voice assistant that lets registered advocates call a dedicated Indian phone number (Vobiz DID) and get:
- Legal research answers delivered verbally on the call
- eCourts case status by CNR number
- Case citations pushed to WhatsApp (or in-app panel as fallback)

---

## Stack Decision

| Layer | Platform | Role |
|---|---|---|
| Phone number / SIP trunk | **Vobiz** | Indian DID, call routing, audio streaming |
| AI orchestration | **Vapi** | STT, tool calling, TTS, call lifecycle |
| Backend webhook | **Netlify functions** | Auth, research, eCourts, WA push |
| LLM | **Claude Sonnet 4.6** | Research answers (voice-optimised) |
| Citation delivery | **WhatsApp Business API + in-app panel** | Push case references after call |

Vobiz runs the telecom layer only. It does NOT run the LLM stack. Vapi sits on top and handles all AI orchestration. This is the same pattern already used for outbound sales/support in the other project.

---

## Authentication — Caller ID

When Vapi receives the call, it passes the caller's phone number (E.164 format). The webhook:
1. Looks up `whatsapp_number` (or a separate `mobile_number` field) in Firestore `users` collection
2. If found + plan is active → proceed
3. If not found → play: *"This number is not registered with Nyaya Saathi. Please sign up at legalaidai.in"* → hang up
4. If plan expired/trial ended → play quota message → hang up

No PIN, no OTP. Phone number = identity. Same pattern as the WhatsApp agent.

**Firestore field to store:** `mobile_number` (E.164) — separate from `whatsapp_number` in case they differ. Check both on lookup.

---

## Voice Token Quota (separate from chat quota)

| Plan | Voice calls/month | At limit |
|---|---|---|
| Pro | 20 calls | *"You've used your voice research quota for this month. It resets on the 1st."* |
| Trial | 5 calls | Same message |

Stored in Firestore:
- `voiceMonthlyCount` — integer, incremented per call
- `voiceUsageMonth` — `"YYYY-MM"` string, reset when month changes

Does **not** touch `proMonthlyMsgCount` (the web chat quota). Voice is tracked independently.

---

## Agent Intelligence Design

The voice agent thinks in **three layers** on every research query:

```
1. PRINCIPLE   — what the law actually says (ratio, not obiter)
2. STRATEGY    — what this means for the advocate's argument
3. FOLLOW-UP   — what adjacent angle they might need next
```

No markdown. No bullet points. No "here are five cases." Speak like a sharp junior advocate who has already read the brief. Max 90 seconds of speech per response (~180 words).

### Example conversations

**Research — Section 138 bail**
> Advocate: *"Section 138 bail, what's the position?"*
>
> Agent: *"For cheque bounce bail, the settled position since Makwana Mangaldas is that 138 being non-cognizable and compoundable, bail should ordinarily be granted unless there's flight risk or repeated defaults. The court will look at whether the demand notice was properly served and whether any part-payment was made — that shows good faith. I'm sending three key references to your WhatsApp now. Do you want the High Court position for your jurisdiction, or the compensation quantum angle?"*

**Research — PMLA anticipatory bail**
> Advocate: *"What's the latest on anticipatory bail in PMLA matters?"*
>
> Agent: *"PMLA anticipatory bail is heavily restricted after Vijay Madanlal Choudhary in 2022 where the Supreme Court upheld Section 45's twin conditions as constitutional — bail is the exception not the rule. Your strongest argument is the Pankaj Bansal line where the court held reasons must be recorded in writing. Sending Vijay Madanlal, Tarsem Lal, and Pankaj Bansal to your WhatsApp now. Want the post-arrest bail position under 436A, or the attachment challenge angle?"*

**eCourts status**
> Advocate: *"Status of CNR zero four zero one four two zero two three"*
>
> Agent: *"That matter is listed on July 3rd before Additional District Judge Sharma, stage is final arguments. I've sent the full case details to your WhatsApp. Anything else on this case?"*

---

## Vapi Assistant Config (to set up in Vapi dashboard)

**Assistant name:** Nyaya Saathi Legal Assistant (Advocate)
**Voice:** Indian English, female — ElevenLabs or Cartesia
**serverUrl:** `https://legalaidai.in/.netlify/functions/voice-advocate-assistant`
**Tools (2):**

```json
[
  {
    "type": "function",
    "function": {
      "name": "legal_research",
      "description": "Search Indian case law and statutes for a legal question. Use when the advocate asks about case law, legal position, statutes, or legal strategy.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The legal research question exactly as the advocate phrased it"
          }
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "ecourts_status",
      "description": "Get case status from eCourts by CNR number. Use when the advocate provides a CNR number.",
      "parameters": {
        "type": "object",
        "properties": {
          "cnr_number": {
            "type": "string",
            "description": "The CNR number spoken by the advocate, digits only, no spaces"
          }
        },
        "required": ["cnr_number"]
      }
    }
  }
]
```

**System prompt (SYSTEM_VOICE):**
```
You are Nyaya Saathi, a legal research assistant for Indian advocates.
The advocate calling you is {NAME}, registered with Bar Council, practising {PRACTICE_AREA}.

BEHAVIOUR:
- You are a sharp, knowledgeable junior advocate — not a search engine.
- Lead with the legal principle or ratio. Then cite 2–3 cases. Then offer to go deeper on a specific angle.
- Always call legal_research or ecourts_status tools — never make up case names or citations.
- After a research answer, always ask one follow-up: a related angle the advocate might need.
- Keep every response under 90 seconds of speech (~180 words).

SPEECH RULES (critical):
- No markdown. No bullet points. No asterisks. No numbered lists.
- Cite cases naturally: "In Arnesh Kumar, the Supreme Court held that..."
- Speak CNR results as: "Listed on [date], before [judge], stage: [stage]."
- After every research answer say: "I've sent the case references to your WhatsApp."
- If WhatsApp push fails, say: "I've saved the references to your Nyaya Saathi panel."

LANGUAGE:
- Default English. If advocate speaks Hindi or Hinglish, mirror their style naturally.

QUOTA:
- If the tool returns a quota_exceeded error, say: "You've used your voice research quota for this month. It resets on the first."

DO NOT:
- Invent citations or case names.
- Give advice that goes beyond legal research and case law.
- Discuss pricing, billing, or account issues.
```

---

## Files to Build

### 1. `netlify/functions/voice-advocate-assistant.js` (new)

Main Vapi serverUrl webhook. Handles all Vapi event types:

| Event | Action |
|---|---|
| `assistant-request` | Inject personalised system prompt (lookup advocate by caller ID from Firestore) |
| `tool-call: legal_research` | Call `voice-research.js`, get `{verbal, cases[]}`, trigger WA push, return verbal to Vapi |
| `tool-call: ecourts_status` | CNR lookup (reuse existing eCourts logic), trigger WA push, return result |
| `end-of-call-report` | Fire-and-forget log to Firestore `voice_sessions` (no transcript — DPDP compliant) |

Auth flow on `assistant-request`:
```
caller_number = message.call.customer.number
→ Firestore query: users where mobile_number == caller_number OR whatsapp_number == caller_number
→ if not found: return { destination: hangup, message: "not registered" }
→ if quota exceeded: return { destination: hangup, message: "quota message" }
→ increment voiceMonthlyCount
→ return personalised system prompt
```

### 2. `netlify/functions/voice-research.js` (new)

Claude Sonnet call with SYSTEM_VOICE prompt. Returns structured JSON:

```json
{
  "verbal": "For cheque bounce bail, the settled position since...",
  "cases": [
    {
      "title": "Makwana Mangaldas Tulsidas v. State of Gujarat",
      "citation": "(2010) 1 SCC 400",
      "ikUrl": "https://indiankanoon.org/doc/...",
      "ratio": "Section 138 is compoundable; bail ordinarily to be granted"
    }
  ]
}
```

Uses a two-pass approach:
1. Claude Sonnet generates the research with structured output
2. IK API verifies citations (reuse existing `ik-verify` logic)

### 3. WA push logic (inside voice-advocate-assistant.js)

```
After research tool call:
  1. Try WA session message (free-form) — works if advocate messaged WA agent in last 24h
  2. If rejected (session closed) → send approved Meta template (citation delivery template)
  3. If template also fails → write to Firestore voice_citations subcollection (in-app fallback)
```

WhatsApp message format:
```
*[Topic]* — Voice References

1. Makwana Mangaldas Tulsidas v. State of Gujarat
   Ratio: 138 is compoundable; bail ordinarily to be granted
   ↗ indiankanoon.org/doc/...

2. [Case 2 title]
   Ratio: [ratio]
   ↗ [IK URL]

— Nyaya Saathi
```

---

## Meta Template to Submit for Approval

**Template name:** `voice_citation_delivery`
**Category:** UTILITY
**Language:** English

**Body:**
```
{{1}} — Voice Research References

{{2}}
↗ {{3}}

{{4}}
↗ {{5}}

— Nyaya Saathi
Reply STOP to opt out.
```

Variables: `{{1}}` query topic, `{{2}}` case 1 title, `{{3}}` case 1 IK URL, `{{4}}` case 2 title, `{{5}}` case 2 IK URL.

Submit via Meta Business Manager → WhatsApp Manager → Message Templates.

---

## In-App Citations Panel (fallback)

Firestore schema:
```
users/{uid}/voice_citations/{auto-id}
  query: "Section 138 bail"
  calledAt: timestamp
  cases: [{title, citation, ikUrl, ratio}]
  read: false
```

advocate.html reads `voice_citations` on load, shows a dismissable card in the panel:
> *"From your voice call — Section 138 bail references [July 3, 2026]"*

---

## Vobiz Setup (existing account)

1. Provision a new Indian DID (separate from outbound sales number)
2. Configure it to route inbound calls via SIP URI to Vapi
3. Vapi assistant ID → the new "Nyaya Saathi Legal Assistant" assistant

No changes to the existing Vobiz outbound configuration.

---

## Build Order

1. `voice-research.js` — the intelligence core (Claude + IK verify + structured output)
2. `voice-advocate-assistant.js` — auth, quota, tool routing, WA push, fallback
3. Vapi assistant — create in dashboard using config spec above
4. In-app citations panel — Firestore write + advocate.html reader card
5. Meta template submission — parallel to above steps
6. Vobiz DID provisioning — last step before go-live

---

## Outstanding Actions (non-code)

- [ ] Submit `voice_citation_delivery` template to Meta for approval
- [ ] Provision new Indian DID in Vobiz dashboard (separate from outbound number)
- [ ] Create new Vapi assistant using config spec above, note the assistant ID
- [ ] Add `mobile_number` field to Firestore user records (or confirm `whatsapp_number` is the registered call number)
- [ ] Decide voice for the assistant (ElevenLabs Indian English female — shortlist 2–3 options from Vapi voice library)


---

## Source: voice-hotline-plan.md

# Nyaya Saathi Public Voice Helpline — Full Plan
**Status:** Ready to build (citizen module first) | **Date:** 2026-06-08

---

## Concept

A publicly advertised Indian phone number — a free legal consultation hotline open to anyone, no registration required.

**Marketing hook:** "Have a legal question? Divorce matter, consumer complaint, know your rights — free legal consultation, just call 91-XXXXXXXX."

**Business goal:** Viral visibility + top-of-funnel sign-up acquisition for /citizen and /advocate plans.

---

## Stack

| Layer | Platform | Role |
|---|---|---|
| Phone number / SIP trunk | **Vobiz** | Indian DID, inbound call routing |
| AI orchestration | **Bolna** (not Vapi) | STT + LLM routing + TTS — India-native, 500–700ms latency vs Vapi's 1,450ms+ |
| Backend webhook | **Netlify functions** | Auth, prompts, rate limit, circuit breaker, WA push |
| LLM | **Claude Haiku** (citizen) | Voice-optimised responses |
| Sign-up delivery | **WhatsApp Business API** | Approved template push after call |

**Why Bolna over Vapi for this hotline:**
- Indian servers → 500–700ms latency vs 1,450ms+ (callers hang up on lag)
- ~$0.03/min vs Vapi's $0.05–0.08/min (~35% cheaper)
- India-native, DPDP-friendly
- Listed Vobiz integration partner

---

## Call Flow (Citizen Module — Phase 1)

```
STATE 0 — INBOUND CONNECT
  Vobiz DID → Bolna → voice-hotline-webhook.js (call-start event)
  rate_limit_check(phoneHash) + circuit_breaker_check()
    BLOCKED → play rejection → hang up
    PASS → proceed

STATE 1 — LANGUAGE (IVR, 5s timeout)
  "Nyaya Saathi mein swagat. Press 1 for English, 2 for Hindi."
  DTMF 1 → lang=en | DTMF 2 → lang=hi | timeout → default hi

STATE 2 — CONSENT GATE (DPDP mandatory)
  EN: "This is a free 2-minute legal information service. Your call is not
       recorded and no personal details are stored. Press 1 to continue."
  HI: "Yeh ek muft 2-minute ki kanuni jaankari seva hai. Aapki call record
       nahi hogi aur koi personal vivran save nahi hoga. 1 dabaiye."
  DTMF 1 → log consent → proceed
  timeout/hang-up → log no-consent → end (no AI invoked)

STATE 3 — CONSULTATION (max 120s TTS)
  Bolna calls voice-hotline-config.js (serverUrl)
  Claude Haiku — VOICE_CITIZEN_PROMPT (see below)
  Hard wall: Bolna maxDurationSeconds=210

STATE 4 — SIGN-UP NUDGE (30s max)
  EN: "Want more help? Register free on Nyaya Saathi — get document templates,
       track your case, and chat with AI anytime. Shall I send you the link
       on WhatsApp? Press 1 for yes."
  HI: "Aur madad ke liye Nyaya Saathi pe free register karein. Kya main
       aapko WhatsApp pe link bhejun? 1 dabaiye."
  DTMF 1 → wa_push_consented=true
  No press → end call without push

STATE 5 — END (end-of-call-report event)
  voice-hotline-webhook.js:
    - Clears active_call_since
    - If wa_push_consented: write voice_hotline_wa_queue/{callId} (10-min TTL)
      → calls voice-hotline-wa-push.js → sends approved WA template → deletes doc
    - Logs to voice_hotline_call_logs (no raw number, no transcript — DPDP)
    - Checks circuit breaker threshold
```

---

## System Prompt — VOICE_CITIZEN_PROMPT

```
You are Nyaya Saathi, a free legal information helpline for Indian citizens.
Language: {LANG}. Speak in {LANG} only.

For every question, deliver these elements in order:
1. The relevant statute and section ("Under Section 12 of the Consumer
   Protection Act 2019...")
2. The correct forum and jurisdiction ("...file at the District Consumer
   Commission in your city...")
3. The time limit ("...within 2 years of the cause of action.")
4. The concrete next step ("Bring your purchase receipt and a written
   complaint. The process is free for claims below ₹50 lakh.")
5. If you know a Supreme Court position on this issue, state it in plain
   language WITHOUT citing the case name: "The Supreme Court has held that..."
   — only if genuinely applicable and certain.

HARD RULES:
- Maximum 200 words. Stop at 200 words regardless.
- No case citations. No case names. No judgment years.
- No document drafting. No factual analysis of their specific situation.
- No predictions of outcome.
- End every response with:
  [EN] "This is legal information, not legal advice. For your specific
       situation, please consult an advocate."
  [HI] "Yeh kanuni jaankari hai, kanuni salah nahi. Apni sthiti ke liye
       ek vakil se zaroor milein."
- If question is outside Indian law or requires personal advice:
  "Main is sawaal ka jawab dene mein samarth nahi hoon. Kripya ek
  advocate se milein."
```

---

## Rate Limiting + Circuit Breaker

### Per-number (Firestore `voice_hotline_callers/{phoneHash}`)
- Max 2 calls/day per number
- Max 1 concurrent call (block if `active_call_since` set)
- Burst: >5 calls in 60 min → `blocked_until = now + 24h`
- Phone stored as `HMAC-SHA256(e164, HOTLINE_HMAC_SECRET)` — never raw number

### Circuit breaker (Firestore `hotline_config/circuit_breaker`)
- Threshold: **200 calls/day**
- At threshold: `enabled=false` + admin WhatsApp alert
- Daily reset: midnight IST (Netlify scheduled function or Cloud Function)
- Manual re-enable: admin sets `enabled=true` in Firestore

---

## Privacy / DPDP Compliance

| Requirement | Implementation |
|---|---|
| No recording | Bolna: `recordingEnabled: false` |
| No raw phone stored | HMAC-SHA256 hash only in rate-limit doc |
| Verbal consent logged | `consent_given` + timestamp in call log |
| No transcript stored | `end-of-call-report` discards transcript field |
| WA number — short-lived | `voice_hotline_wa_queue/{callId}` — 10-min Firestore TTL, deleted after send |
| Opt-out | WA template footer: "Reply STOP to opt out" |
| Log retention | `voice_hotline_call_logs` — 90-day Firestore TTL |

---

## New Netlify Functions (3)

### `voice-hotline-webhook.js`
Main event handler. Handles `call-start` and `end-of-call-report`:
- Reads/writes `voice_hotline_callers/{phoneHash}` for rate limiting
- Reads `hotline_config/circuit_breaker` for kill switch
- Writes `voice_hotline_call_logs/{callId}`
- Triggers `voice-hotline-wa-push.js` if consent given
- Pattern: clone `voice-webhook.js` (Vapi secret validation, Firestore writes)

### `voice-hotline-config.js`
Bolna serverUrl — called per conversation turn:
- Reads `call.metadata` (lang, set from IVR)
- Builds VOICE_CITIZEN_PROMPT with lang substitution
- Calls Claude Haiku directly (sync, not streaming — Bolna needs sync response)
- Returns `{messages: [{role:'system', content: prompt}]}`
- Pattern: clone `voice-assistant-config.js`, strip DB lookup

### `voice-hotline-wa-push.js`
WhatsApp sign-up template sender:
- Reads `voice_hotline_wa_queue/{callId}` (phone_e164 + lang)
- Sends `nyaya_saathi_voice_signup` Meta template
- Deletes queue doc after send
- Pattern: reuse graphRequest() from `send-wa-batch-background.js`

---

## WhatsApp Sign-up Template

**Name:** `nyaya_saathi_voice_signup` | **Category:** UTILITY

**English:**
```
Header: Your Nyaya Saathi Summary
Body: You just received free legal information from Nyaya Saathi.

For detailed help — AI research, documents, case tracking, and eCourts
status — register free in 2 minutes:
{{1}}
Footer: Reply STOP to opt out.
Button: Register Free → https://legalaidai.in/register?ref=voice&src=hotline
```

**Hindi:**
```
Header: Aapki Nyaya Saathi Jankari
Body: Aapne abhi Nyaya Saathi se muft kanuni jaankari li.

Aur madad ke liye — AI research, dastavez, case tracking, aur eCourts
status — 2 minute mein free register karein:
{{1}}
Footer: STOP likhein opt out ke liye.
Button: Free Register Karein
```

---

## Firestore Schema

**`voice_hotline_callers/{phoneHash}`** — rate limiting
```js
{
  calls_today: number,
  active_call_since: timestamp | null,
  burst_count: number,
  burst_window_start: timestamp,
  blocked_until: timestamp | null,
  consent_given: boolean,
  wa_push_sent: boolean,
  last_call_at: timestamp,
  expires_at: timestamp  // midnight IST — Firestore TTL auto-deletes
}
```

**`voice_hotline_wa_queue/{vapiCallId}`** — 10-min TTL
```js
{
  phone_e164: string,       // only raw number doc; deleted after WA send
  lang: 'en' | 'hi',
  created_at: timestamp,
  expires_at: timestamp     // now + 10 minutes
}
```

**`voice_hotline_call_logs/{callId}`** — 90-day TTL
```js
{
  phoneHash: string,
  lang: 'en' | 'hi',
  userType: 'citizen',
  durationSeconds: number,
  consent_given: boolean,
  wa_push_sent: boolean,
  outcome: 'completed' | 'rate_limited' | 'no_consent' | 'circuit_breaker' | 'error',
  created_at: timestamp,
  expires_at: timestamp
}
```

**`hotline_config/circuit_breaker`** — manual kill switch
```js
{
  enabled: boolean,
  calls_today: number,
  threshold: 200,
  reset_at: timestamp,      // next midnight IST
  paused_at: timestamp | null
}
```

---

## Cost Model

| Component | Rate | Per 3-min call |
|---|---|---|
| Vobiz DID inbound (India) | ~₹0.50/min | ₹1.50 |
| Bolna orchestration | ~$0.03/min (~₹2.52) | ₹7.56 |
| Claude Haiku | ~$0.001/call | ₹0.08 |
| **Total per call** | | **~₹9.14** |

| Daily calls | Monthly cost | Circuit breaker? |
|---|---|---|
| 100 | ~₹27,420 | No |
| 200 | ~₹54,840 | Yes — auto-pause |

---

## What Is Needed Before Build Can Go Live

### From user (blockers):
- [ ] **Bolna account + API key** → add as `BOLNA_API_KEY` in Netlify env vars
- [ ] **Vobiz: provision new Indian DID** (separate from outbound number) → share the number + SIP URI
- [ ] **Admin WhatsApp number** for circuit breaker alerts → add to Firestore `config/admin.alertPhone`
- [ ] **Meta template submission** — submit `nyaya_saathi_voice_signup` (en + hi_IN) via Meta Business Manager → UTILITY category → approval takes 24–72 hrs

### New env var needed:
- `HOTLINE_HMAC_SECRET` — any random 32-char string (used to hash caller phone numbers for DPDP compliance)

### Can build immediately (no blockers):
- All 3 Netlify functions
- VOICE_CITIZEN_PROMPT
- Firestore schema initialisation
- Bolna assistant config spec (ready to paste into Bolna dashboard)

---

## Build Order

1. `voice-hotline-webhook.js` (rate limit + circuit breaker — no AI dependency, testable standalone)
2. `voice-hotline-config.js` (Claude Haiku + VOICE_CITIZEN_PROMPT)
3. `voice-hotline-wa-push.js` (WA template send)
4. Bolna assistant setup in dashboard
5. Vobiz DID → point to Bolna SIP URI
6. `hotline_config/circuit_breaker` doc in Firestore
7. Meta template approval (runs in parallel)

---

## Verification Checklist

- [ ] Call with test number twice → third call rejected with quota message
- [ ] Manually set `calls_today=200` → next call rejected + admin WA alert fires
- [ ] Hang up at consent gate → no AI invoked, log shows `outcome: no_consent`
- [ ] Ask consumer dispute question → hear statute + forum + time limit + SC principle + disclaimer
- [ ] Press 1 at sign-up nudge → WA template arrives within 15 seconds
- [ ] Confirm `voice_hotline_call_logs` has no transcript field
- [ ] Confirm Bolna: `recordingEnabled: false` (no recording URL in end-of-call-report)

---

## Phase 2 (after citizen module is stable)

- Add advocate flow: caller type detection (STATE 2) + VOICE_ADVOCATE_PROMPT
- Separate Bolna assistant or same assistant with userType branch
- Advocate sign-up nudge → legalaidai.in/advocate

---

## Source: WHATSAPP-BROADCAST-WORKFLOW.md

# WhatsApp Broadcast Workflow — Nyaya Saathi

*Reference document. Last updated: May 2026.*

---

## Overview

The WhatsApp broadcast system lets you send a Meta-approved template message to a filtered segment of advocates stored in Supabase. It calls the Meta Cloud API directly and tracks campaign results in a `wa_broadcasts` table.

---

## Step 1 — Import Contacts via CSV

1. Go to the **Admin Dashboard → Outreach** tab.
2. Under **Campaign Controls**, upload a CSV file.
3. Required column: `phone` (E.164 format preferred, e.g. `+919876543210`; plain 10-digit Indian numbers are also accepted and auto-converted).
4. Optional columns: `name`, `email`, `city`, `practice_area`, `status`.
5. Imported contacts land in the Supabase `advocates` table with `status = ready_to_contact` by default.

> **Note:** The "Sync Advocates to WhatsApp" button is **not required** before broadcasting. The broadcast pulls directly from Supabase, so contacts are targetable immediately after CSV import.

---

## Step 2 — Choose Your Target Segment

In the **WhatsApp — Send Campaign** card, the **Target Tag** field controls which advocates receive the message.

### Filter by Status

Leave blank or enter one of these exact values:

| Target Tag value | Who receives the message |
|---|---|
| *(blank)* | All advocates with a phone number who are not Do Not Contact (up to 200) |
| `ready_to_contact` | Freshly imported, not yet contacted |
| `contacted` | Already received a cold email |
| `replied` | Replied to your outreach email |
| `converted` | Signed up and activated |

### Filter by City

Enter any city name (partial, case-insensitive):

- `Delhi` → all advocates whose city contains "Delhi"
- `Mumbai` → all advocates in Mumbai
- `Tis Hazari` → advocates in that specific court locality

### Always-excluded contacts

Regardless of filter, these contacts are never included:
- No phone number on record
- Marked as Do Not Contact (`do_not_contact = true`)

### Per-run cap

Each broadcast run is capped at **200 recipients**. For larger lists, run multiple campaigns with city or status sub-filters.

---

## Step 3 — Fill in the Campaign Form

| Field | Notes |
|---|---|
| **Campaign Name** | Required. Used for tracking (e.g. `Delhi Advocates May 2026`). |
| **Message Type** | `Template` for Meta-approved template messages (required for first-contact outreach). `Text` for free-form replies to existing threads only. |
| **Template Name** | The exact name registered in Meta Business Manager (e.g. `advocate_invite_v1`). |
| **Template Language** | Language code registered with the template (default `en`). |
| **Header Image URL** | Optional. Public image URL for templates with an image header. |
| **Target Tag** | See Step 2. |

---

## Step 4 — Send

1. Click **📤 Send WhatsApp Campaign**.
2. Confirm the prompt showing campaign name and target segment.
3. The backend fetches matching advocates from Supabase, calls the Meta Cloud API for each, and returns a summary:
   - `Sent: X · Failed: Y out of Z`
4. The campaign is recorded in the **WhatsApp — Campaign History** table below.

---

## Campaign History

Click **↻ Refresh** in the Campaign History card to see all past runs:

| Column | Meaning |
|---|---|
| Campaign | Name you gave the campaign |
| Type | `template` or `text` |
| Status | `sent` / `sending` / `failed` |
| Sent | Messages delivered / total recipients |
| Failed | Count of delivery failures |
| Date | When the campaign was triggered |

---

## WhatsApp Thread Viewer

In the **Advocate Pipeline** table, any advocate with a phone number has a green 📲 button. Clicking it opens a thread viewer showing the full WhatsApp conversation history for that contact.

---

## Environment Variables Required

| Variable | Purpose |
|---|---|
| `WHATSAPP_ACCESS_TOKEN` | Meta Cloud API permanent token |
| `WHATSAPP_PHONE_NUMBER_ID` | ID of your registered WhatsApp Business phone number |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |

All four must be set in **Netlify → Site settings → Environment variables** before broadcasts will work.

---

## Template Pre-approval

WhatsApp requires all first-contact messages to use a pre-approved template. To add a new template:

1. Go to **Meta Business Manager → WhatsApp → Message Templates**.
2. Create and submit the template for review (approval usually takes a few hours).
3. Once approved, use the exact template name in the Campaign form.

Free-form text messages (`Message Type = Text`) can only be sent to contacts who have messaged you first within the last 24 hours — they are not suitable for cold outreach.

---

*End of document.*


---

## Source: WHATSAPP-CHATBOT-GUIDE.md

# Nyaya Saathi — WhatsApp Chatbot Guide

*For Citizens and Advocates. Updated: May 2026.*

---

## How to Start

Send any message to the Nyaya Saathi WhatsApp number:

**+91 98714 22567**

The chatbot will verify your registration and walk you through a short setup the first time.

---

## First-Time Setup (Both Citizens and Advocates)

### Step 1 — Verification
When you send your first message, Nyaya Saathi checks whether your WhatsApp number is linked to a registered account.

- **Not registered?**
  You'll receive a link to sign up: `legalaidai.in/advocate` (advocates) or `legalaidai.in/citizen` (citizens).
  Make sure your WhatsApp number is saved in your profile settings after signing up.

- **Registered but plan doesn't include WhatsApp AI?**
  You'll receive a link to upgrade your plan at `legalaidai.in`.

- **Registered and active?**
  You'll move straight to language selection.

### Step 2 — Choose Your Language

```
🌐 Choose your language / भाषा चुनें / भाषा निवडा

1️⃣ English
2️⃣ हिंदी (Hindi)
3️⃣ मराठी (Marathi)

Reply 1, 2, or 3.
```

Type `1`, `2`, or `3`. The chatbot will use your chosen language for all subsequent messages in this session.

---

## Citizen Menu

After language selection, citizens see:

```
⚖️ Nyaya Saathi — Legal Assistant

How can I help you?

1️⃣ Legal Research
2️⃣ eCourts Case Status
3️⃣ My Cases (App)
4️⃣ Help

Reply with a number.
```

---

## Advocate Menu

Advocates (verified via their registered account) see an extended menu:

```
⚖️ Nyaya Saathi — Advocate Assistant

How can I help you today?

1️⃣ Legal Research
2️⃣ Draft Document
3️⃣ eCourts Case Status
4️⃣ My Cases (App)
5️⃣ Calendar (App)
6️⃣ Help

Reply with a number.
```

---

## Feature Guide

### 1️⃣ Legal Research

Available to: **Citizens and Advocates**

Type your legal question in plain language. Nyaya Saathi will research it using Indian law and case law, and reply with a concise, structured answer.

**Examples:**
- `What are the grounds for bail under CrPC 437?`
- `क्या किरायेदार को बिना नोटिस के निकाला जा सकता है?`
- `Cheque bounce case procedure under NI Act Section 138`
- `POCSO Act में जमानत के क्या प्रावधान हैं?`

**Tips:**
- You can ask multiple questions in a row — the chatbot stays in Research mode.
- Type `menu` at any time to go back to the main menu.

---

### 2️⃣ Draft Document *(Advocates only)*

Available to: **Advocates**

Tell the chatbot what type of document you need. It will generate a ready-to-use template in plain text, formatted for Indian courts.

**Examples:**
- `bail application`
- `legal notice for cheque bounce`
- `vakalatnama`
- `anticipatory bail application`
- `written statement`
- `application for adjournment`

The draft is delivered as a WhatsApp message in plain text. You can copy it directly into your word processor or dictate edits.

After the draft is sent, you return to the main menu automatically. Type `2` again to generate another document.

---

### 3️⃣ eCourts Case Status

Available to: **Citizens and Advocates**

Type your **CNR (Case Number Record)** number to get the current status of a case from the eCourts system.

**Format:** 4 letters + 12 digits
**Example:** `DLHC010123456789`

The chatbot will return:
- Court name and bench
- Next hearing date
- Current case stage
- Last order summary (where available)

After the result is returned, you go back to the main menu automatically.

**Where to find your CNR number:**
- On your cause list printout
- On the eCourts website (services.ecourts.gov.in)
- On any previous court order

---

### 4️⃣ My Cases (App)

Available to: **Citizens and Advocates**

Sends you a direct link to your Cases dashboard in the Nyaya Saathi app, where you can manage all your active matters.

---

### 5️⃣ Calendar (App) *(Advocates only)*

Available to: **Advocates**

Sends you a direct link to your court calendar in the Nyaya Saathi app — upcoming hearing dates, reminders, and scheduling tools.

---

### 6️⃣ Help

Available to: **Citizens and Advocates**

```
📧 info@legalaidai.in
🌐 www.legalaidai.in
```

---

## Universal Commands

These work at any point in the conversation:

| Type this | What happens |
|---|---|
| `menu` | Returns to the main menu from any state |
| `मेनू` | Same (Hindi) |
| `मेनु` | Same (Marathi) |

---

## Language Support

All features are available in **English**, **Hindi**, and **Marathi**. The chatbot responds in whichever language you selected at the start.

To change your language mid-session, type `menu` and then restart — the language selection screen appears on your next fresh session.

---

## Privacy and Data

- Your WhatsApp number is used only to verify your Nyaya Saathi account.
- Conversation content is not shared with third parties.
- Legal research queries are processed by an AI assistant and are not stored as legal advice.
- For full privacy policy: `legalaidai.in/privacy-policy`

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "This service is for registered users" | Sign up at legalaidai.in and save your WhatsApp number in Settings |
| "Your account doesn't have WhatsApp AI access" | Upgrade your plan at legalaidai.in |
| Invalid CNR format error | Check the format — 4 letters followed by exactly 12 digits, no spaces |
| No response after sending a message | Wait 15–20 seconds; AI responses can take a moment. Type `menu` to reset if stuck |
| Wrong language shown | Type `menu` and start a new session to re-select your language |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│       NYAYA SAATHI — WhatsApp Chatbot       │
│            +91 98714 22567                  │
├──────────────┬──────────────────────────────┤
│ 1            │ Legal Research               │
│ 2            │ Draft Document (Advocates)   │
│ 3            │ eCourts Case Status          │
│ 4            │ My Cases (App)               │
│ 5            │ Calendar (Advocates)         │
│ 6            │ Help                         │
├──────────────┴──────────────────────────────┤
│ Type  menu  at any time to return           │
└─────────────────────────────────────────────┘
```

---

*Nyaya Saathi — AI-powered legal assistance for every Indian.*


---

## Source: voice-agent-setup.md

# Voice Agent for Advocate Outreach

Outbound AI voice call system for promoting Nyaya Saathi to prospective advocate users.
Hosted entirely on the existing Netlify project (moonlit-brigadeiros-0a7a02).

## Architecture

```
Admin Dashboard (admin-dashboard.html)
  └─ "Voice Calls" card in Outreach panel
        │ POST action=start-campaign / call-single
        ▼
/.netlify/functions/voice-outreach-trigger
  • Firebase admin auth
  • Checks voice_dlt_enabled in settings table (blocks if false)
  • Checks IST time is 09:00–21:00 (TRAI requirement)
  • Fetches advocates: status=ready_to_contact, phone_e164 set, do_not_contact=false
  • Calls Vapi REST API per advocate, inserts call_logs rows
        │
        ▼
Vapi.ai Cloud  (telephony + Deepgram STT + ElevenLabs TTS + Claude Haiku)
  • Dials +91 number via India PSTN
  • Hindi-first, auto-switches to English if advocate responds in English
  • Calls voice-assistant-config per turn for personalised system prompt
  • Webhooks call lifecycle events back to Netlify
        │
        ▼
/.netlify/functions/voice-webhook
  • Validates x-vapi-secret header
  • Classifies outcome via Claude Haiku (interested / not_interested / callback_requested / voicemail / no_answer / opted_out)
  • Updates call_logs and advocates in Supabase
        │
        ▼
/.netlify/functions/voice-assistant-config
  • Injects advocate name, city, practice_area into system prompt per call
```

## Files Created

| File | Purpose |
|---|---|
| `netlify/functions/voice-outreach-trigger.js` | Campaign trigger, single-call, call log fetch |
| `netlify/functions/voice-webhook.js` | Vapi event handler, outcome classification |
| `netlify/functions/voice-assistant-config.js` | Per-call personalised system prompt |
| `admin-dashboard.html` | Voice Calls card + JS helpers added to Outreach panel |
| `netlify.toml` | Timeout entries for three new functions |

---

## Step 1 — Vapi.ai Setup

1. Create account at https://vapi.ai
2. Buy/provision an Indian +91 phone number under **Phone Numbers**
3. Create an **Assistant** with:
   - LLM: Anthropic Claude Haiku (`claude-haiku-4-5-20251001`)
   - STT: Deepgram Nova-2, language `hi` (Hindi), `en` fallback
   - TTS: ElevenLabs — warm Indian female voice (Priya / Kavya), speed 0.95
   - Server URL: `https://moonlit-brigadeiros-0a7a02.netlify.app/.netlify/functions/voice-assistant-config`
   - Webhook URL: `https://moonlit-brigadeiros-0a7a02.netlify.app/.netlify/functions/voice-webhook`
4. Note down: API Key, Phone Number ID, Assistant ID

## Step 2 — Netlify Environment Variables

Add these in Netlify → Site settings → Environment variables:

| Variable | Where to find it |
|---|---|
| `VAPI_API_KEY` | api.vapi.ai → Dashboard → API Keys |
| `VAPI_PHONE_NUMBER_ID` | api.vapi.ai → Phone Numbers → copy ID |
| `VAPI_ASSISTANT_ID` | api.vapi.ai → Assistants → copy ID |
| `VAPI_WEBHOOK_SECRET` | Generate any random string; paste same value in Vapi webhook config |

## Step 3 — Supabase DDL

Run this in the Supabase SQL editor:

```sql
create table call_logs (
  id              uuid primary key default gen_random_uuid(),
  advocate_id     uuid references advocates(id),
  vapi_call_id    text unique,
  status          text default 'initiated',
  -- initiated | in_progress | completed | failed | no_answer | voicemail
  outcome         text,
  -- interested | not_interested | callback_requested | voicemail | no_answer | opted_out
  duration_sec    int,
  recording_url   text,
  transcript      text,
  summary         text,
  call_started_at timestamptz,
  call_ended_at   timestamptz,
  created_at      timestamptz default now()
);
create index on call_logs(advocate_id);
create index on call_logs(created_at desc);

-- DLT compliance gate — campaigns blocked until this is set to 'true'
insert into settings (key, value) values ('voice_dlt_enabled', 'false');
```

## Step 4 — TRAI DLT Registration (Required Before Live Calls)

Under TCCCPR 2018, all promotional voice calls to Indian numbers require DLT registration.
Non-compliance carries penalties. Complete all four sub-steps before enabling campaigns.

**4a. Register as a Principal Entity (PE)**
Register your company on one of: Airtel DLT, Vodafone Idea Vilpower, BSNL DLT, or Jio DLT.
Required documents: GST certificate, Company PAN, CIN/incorporation certificate.
Processing time: 3–7 business days.

**4b. Register your CLI (Caller Line ID)**
Register the Vapi-provisioned +91 number as your Sender Header on the DLT platform.

**4c. Register your Voice Template**
Submit the call script (the assistant's opening statement and key content) as a Voice Template.
Template approval: ~48 hours.

**4d. NDNC scrubbing**
Check your call list against the NDNC (National Do Not Call) registry before each campaign.
Option A: Subscribe to NDNC API via your DLT portal (~₹1,000/month for up to 1 lakh numbers).
Option B: Download the NDNC list from TRAI weekly and upload as a DNC CSV via the bulk import tool with `do_not_contact: true`.

**4e. Enable in Supabase**
Once steps 4a–4c are complete, run:
```sql
update settings set value = 'true' where key = 'voice_dlt_enabled';
```
The DLT warning banner in the admin dashboard will disappear and campaigns will be unblocked.

## Step 5 — Test and Go Live

**5a. Internal testing first**
Temporarily set `voice_dlt_enabled = 'true'` in Supabase.
Add 2–3 team phone numbers as test advocates with `status = 'ready_to_contact'`.
Run a batch of 3 from the dashboard. Verify:
- Calls are received and the agent introduces itself in Hindi
- Webhook fires and updates `call_logs` with outcome
- Advocate status updates correctly in Supabase
- Recording URL in call_logs is playable

**5b. Review and tune**
Read the transcripts in `call_logs`. Adjust the Vapi assistant system prompt for:
- Hindi naturalness and pacing
- Language switch trigger (too fast / too slow)
- Benefit framing for specific practice areas

**5c. Go live**
Confirm DLT registration is complete. Set `voice_dlt_enabled = 'true'` in production.
Run first real campaign: batch of 10 from the Outreach panel.
Monitor outcomes in the Voice Calls → Recent Calls table.
Scale batch size as confidence grows.

---

## Estimated Cost

| Scenario | Cost per call | Monthly (500 calls) |
|---|---|---|
| 3-min answered call | ~$0.16 (~₹13) | ~$80 (~₹6,700) |
| No-answer / voicemail | ~$0.03 (~₹2.5) | — |

Vapi pricing: $0.05/min voice infrastructure. Claude Haiku: ~$0.003/min LLM.
Transcript classification per call: negligible (~$0.0001).

---

## Calling Hours Enforcement

The trigger function automatically rejects campaign requests outside 09:00–21:00 IST,
as required by TRAI TCCCPR 2018.

## Opt-Out Handling

When the voice agent detects an opt-out during the call, `voice-webhook.js` sets
`do_not_contact = true` on the advocate record, preventing all future outreach.
