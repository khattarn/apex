# Job-Ad Outreach — "Applying for the role" (email + voice)

*For leads flagged `pain_signal = job_ad_frontdesk` (a practice actively hiring a receptionist).
This copy OVERRIDES the normal vertical email sequence for those leads, and gives Sophie a
hiring-specific voice opener. Works for dentist + doctor verticals.*

Placeholders: `{PRACTICE_NAME}` · `{VOICE_PRICE}` (US ~$180 / CA ~$200 — local currency) ·
`{DEMO_NUMBER}` (Claire's demo line) · `{DEMO_LINK}`.
Identity: written in the AI receptionist's voice, signed "Claire, via PracticeDesk" (honest — she's an AI).
Sequence cadence: Day 1 → Day 3 → Day 6. Canada = lighter CASL track; PHONE-first (Sophie) for these.

---

## EMAIL 1 — Day 1 · The application
**Subject A:** Applying for your front-desk role, {PRACTICE_NAME}
**Subject B:** You're hiring a receptionist — may I apply?
**Preheader:** I work 24/7, never call in sick, and I can start today.

I noticed {PRACTICE_NAME} is hiring for the front desk — so I'd like to apply.

I answer every call, WhatsApp and email, 24/7. I book appointments, keep your calendar tidy,
remind patients so they actually show up, and follow up the ones who don't. I don't need a salary,
benefits, training or holidays — and I can start in about fifteen minutes.

I'm Claire, an AI receptionist from PracticeDesk. Honestly, I'm at my best working *alongside* a
human receptionist — I make whoever you hire better by covering every call they can't: after hours,
lunch breaks, and the overflow that goes to voicemail today. Hire someone and add me, and between us
nothing gets missed.

Hear me for yourself — call {DEMO_NUMBER} and try me like a patient would. Or start a free 14-day trial.

*P.S. Keep hiring if you like — I'm happy to work alongside whoever you choose.*
— Claire, via PracticeDesk

---

## EMAIL 2 — Day 3 · The comparison
**Subject A:** $20 an hour, or about {VOICE_PRICE} a month?
**Subject B:** A quick comparison for the front-desk role
**Preheader:** Same job. Nights and weekends included. No benefits.

A front-desk hire at $19–25 an hour works out to roughly $40–50k a year — plus benefits, training,
and cover for sick days and holidays.

I'm about {VOICE_PRICE} a month, and I also work the nights, weekends and lunch breaks a human won't.

You don't have to choose. Most practices keep their receptionist for in-person care and add me for
everything after-hours and overflow — between us, nothing goes to voicemail.

Try me first: call {DEMO_NUMBER} and hear me take a live booking.
— Claire, via PracticeDesk

---

## EMAIL 3 — Day 6 · Withdraw the application
**Subject A:** Should I withdraw my application?
**Subject B:** Last note about your front desk, {PRACTICE_NAME}

I'll stop here so I'm not cluttering your inbox.

If you've filled the role — congratulations. And if you ever want me covering after-hours and
overflow alongside them, the 14-day trial is always open, and I'm live in about fifteen minutes.

Wishing {PRACTICE_NAME} a full schedule.
— Claire, via PracticeDesk
[Start the free trial anytime]({DEMO_LINK})

---

## VOICE — Sophie's follow-up opener (hiring clinics)

Sophie calls ~24h after the email. Honest, gentle, job-applicant framing:

> "Hi — I saw you're hiring for the front desk, so I thought I'd reach out. I'm Sophie, with
> PracticeDesk. We place an AI receptionist who works right alongside your team — she answers every
> call 24/7, books appointments, keeps the calendar, and reminds patients — for about {VOICE_PRICE}
> a month, no benefits, no sick days. She's not there to replace anyone; she covers the after-hours
> and overflow calls a front desk can't. Happy to answer any questions you have — or, if you'd like,
> I can point you to her line so you can hear her take a live booking."

Then: answer their questions plainly, route them to Claire's demo line ({DEMO_NUMBER}) to *experience*
it, or book the trial. Apply the six gentle-tone rules. Always frame the AI as an *addition* to a
human receptionist, not a replacement. If they've already filled the role, congratulate them and
offer the after-hours/overflow angle, then exit warmly.

---

## Wiring (for Claude Code — when you build it)
1. When a lead's `pain_signal == "job_ad_frontdesk"`, the email path uses THIS sequence instead of
   the vertical default (add a `job_ad` override set in `email_copy.yaml`, or a small lookup keyed on
   pain_signal).
2. Voice queue: these leads are high-intent → rank near the top; Sophie uses the hiring opener above.
3. Canada leads → lighter CASL email cadence; phone-first.
4. Keep claims to real PracticeDesk features; use the confirmed `{VOICE_PRICE}` per currency.
