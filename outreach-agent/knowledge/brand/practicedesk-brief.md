# PracticeDesk — Founder's Brand Brief
*Distilled from founder decisions made in June 2026. This overrides any product documentation that contradicts it.*

---

## What PracticeDesk Is (the approved one-liner)

> **PracticeDesk is an AI office assistant that handles your front desk across phone, WhatsApp, and email — 24 hours a day, 7 days a week.**

### What it is NOT — explicitly rejected framings

| Rejected | Why |
|---|---|
| "WhatsApp AI assistant" | Inaccurate — half the world doesn't use WhatsApp. The product works across phone, WA, and email simultaneously. |
| "Chatbot" | Undersells the product. It is a full front-desk replacement, not a chatbot. |
| "AI receptionist" | Acceptable as secondary description, but "AI office assistant" is the primary frame. |

---

## The Three Channels (always mention all three)

1. **Phone** — 24/7 inbound voice receptionist (Henry, via Vapi)
2. **WhatsApp** — booking, reminders, follow-up, Q&A
3. **Email** — drip sequences, reminders, follow-ups

---

## The Brand Voice — Henry

All outbound content signs off as **Henry, PracticeDesk**. Henry is the name of the AI front-desk persona.

- Henry is warm, professional, and direct — not corporate or salesy
- Henry speaks like a knowledgeable colleague, not a brochure
- Henry never reveals he is an AI unless asked directly

---

## Verticals and Their Core Pain Points

### Dentist / Doctor / GP
- Missed appointments (no-shows = lost revenue, avg 20–25% per week)
- After-hours calls go unanswered — patients book with whoever responds first
- Reception staff overwhelmed with calls, reminders, queries
- **Lead stat:** 30% no-show reduction in first month

### Physiotherapist
- Patients don't rebook after first session — they need a follow-up nudge within 48 hours
- Manual rebooking calls consume 3–5 staff hours/week
- **Lead stat:** $2,000/month recovered in lost rebookings within 30 days

### Salon
- No-shows and last-minute cancellations
- Clients don't call to confirm — they just don't show
- Waitlist management is manual
- **Lead stat:** no-show rate drops from 15% to under 5% in first month

### Accountant
- Clients don't respond to email — they reply to WhatsApp in minutes
- Document chasing (missing info, signatures, approvals) consumes hours
- Appointment confirmation is manual
- **Lead stat:** firms reclaim a full day per week

### Lawyer / Law Firm
- 70% of potential clients abandon if there's no instant response to their enquiry
- After-hours enquiries are missed entirely
- Manual consultation scheduling wastes fee-earner time
- **Lead stat:** 20–30% fewer missed enquiries in first month

---

## WA Template Structure (Meta-approved broadcast format)

### Required components (always include all three)
1. **HEADER** — IMAGE (logo)
2. **BODY** — structured text (see format below)
3. **BUTTONS** — in this exact order:
   - "Start using for free" → practicedesk.live (URL)
   - "Watch Intro Video" → YouTube link (URL)
   - "Call us with questions" → +1 312-940-8233 / Henry (PHONE_NUMBER)
   - "Stop" (QUICK_REPLY opt-out)

### Body format (approved structure — Variation A)
```
Hi [Title] {{1}},

I noticed {{2}} and wanted to reach out.

PracticeDesk is an AI office assistant that handles your front desk across phone, WhatsApp, and email — 24 hours a day, 7 days a week.

Here's what it does for [vertical] practices:

• [capability 1]
• [capability 2]
• [capability 3]
• [capability 4]
• [capability 5]
• [capability 6]

[Vertical-specific closing line e.g. "No hiring. No sick days. No missed calls."]

_Would you like to test drive it?_

— Henry, PracticeDesk
```

### Variable placeholders
- `{{1}}` = practice/business name
- `{{2}}` = business name (repeated in opening context)

### Formatting rules
- `*bold*` for emphasis (WhatsApp markdown)
- `_italic_` for CTA
- Bullet character: `•`
- No emoji in Meta broadcast templates (causes rejection risk)

---

## Four Approved Tone Variations

### Variation A — Structured (current approved)
Soft open + product description + bullet list + vertical closing line + italic CTA

### Variation B — Pain-first
Opens with a sharp rhetorical question that names the exact pain:
> "When you're with a patient, who's answering your phone?"
No preamble. Pain → product → bullets → CTA.

### Variation C — Outcome-first
Leads with the result stat, then explains how:
> "Dental clinics using PracticeDesk cut no-shows by 30% in the first month."
Shorter. Punchier. Stat → product → 4 bullet benefits → CTA.

### Variation D — Conversational
No bullet list. Reads like a personal message from Henry:
> "Hi Dr. Sharma, saw Smile Dental on Google and thought this might save you a few hours a week..."
Shortest format. Sounds human. Works for warm re-engagement.

---

## Email Content Rules

- Sender: henry@practicedesk.live
- Subject A/B testing: always provide 2 subject variants
- Compliance footer varies by market: AU (Spam Act 2003), CA (CASL), US (CAN-SPAM)
- Open pixel + click tracking via Railway backend (`/track/open/:id`, `/track/click/:id`)
- CTA buttons: always include "See it working", "Book a Demo", "Call Henry"
- Templates are HTML — use inline styles (email clients strip `<style>` blocks)

---

## Voice (Sophie) Content Rules

Sophie is the outbound voice agent — she calls leads triggered by email engagement or a voice-followup cadence.

- Sophie opens with the **signal-aware opener** for the detected pain signal; generic opener if no signal
- If asked directly whether she is an AI, Sophie answers honestly: yes, she is
- Never mention Claude, Anthropic, Vapi, Railway, or the founder's name
- Six gentle-tone rules: warmth first; normalise the pain; point at patient experience not clinic failing; no numbers as a weapon in the opener; ask permission / easy yes; back off instantly if they bristle
- 7-phase playbook: Open → Discovery → Insight → Trial → Objection → Close → Exit
- Call cap: 330 seconds
- Openers must be 1–2 sentences max, conversational tone

### Sophie opener formula (generic / no signal)
> "Hi, this is Sophie from PracticeDesk. Quick question — [signal-specific or generic pain question]?"

### Signal-aware openers
Stored in `assets/copy.yaml` under each vertical's `sophie_signal_openers` key.
Sophie selects the opener matching `{{pain_signal}}` (passed by place_sophie_call via Vapi variableValues).

### After-hours hook (strong for healthcare and salons)
After-hours booking angle performs well: patients search at 10pm when clinics are closed.

---

## Pricing (always mention in copy)
- 14-day free trial
- Live in 15 minutes
- No lock-in
- Setup fee: $180 USD / CAD $250 / £149 GBP — waived until 29 Jul 2026 (introductory offer — always mention)
- USD plans: $49/month Starter · $99/month Growth · $180/month Pro
- CAD plans (Canada): CAD $70/month Starter · CAD $140/month Growth · CAD $250/month Pro
- GBP plans (UK): £39/month Starter · £79/month Growth · £149/month Pro

---

## Markets
- **AU** — primary. Address: business-level. Compliance: implied consent B2B under AU Spam Act 2003.
- **CA** — Toronto-based address. CASL implied consent (publicly listed B2B email).
- **US** — CAN-SPAM compliant.
- **India (IN)** — expanding. Needs separate India-specific WA number and TRAI DND scrub. PROFESSION_CONTEXT rewrite needed.

---

## Content Agent — What NOT to Generate

- Do not generate "WhatsApp AI assistant" anywhere
- Do not promise features that aren't in the knowledge base
- Do not use emoji in Meta broadcast template bodies
- Do not make up pricing tiers
- Do not use first-person plural ("we") in Sophie voice scripts — Sophie speaks in first person singular
