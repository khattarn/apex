# Change #9 — Pain-Score & Dark-Spot Detection (Concrete Spec)

*Pre-call qualification for PracticeDesk prospects. Computes a `pain_score` (0–100) per
lead from legitimate, observable signals, ranks the outreach queue, and personalises
Sophie's opener with a TRUE finding. No fabricated findings — ever.*

---

## 0. Where the data comes from & the automated flow

**It is fully automatic.** It runs on the daily prospecting + enrichment crons (Change #7). The
only manual input is the founder setting target cities/verticals in the `settings` table — the
pipeline then finds, enriches, scores, ranks, and contacts on its own.

**Sources (note which are clean APIs vs scrapes):**
- **Google Maps — official Places API** (Text Search -> Place Details). The spine. Returns name,
  address, phone, website, rating, `user_ratings_total`, `opening_hours`, up to ~5 review texts,
  `business_status`. *This uses the API, not scraping Maps' pages — which keeps it ToS-safe.*
- **Each business's own website** — direct HTTP fetch (reuse `email_scraper`'s fetch) for the
  email and for booking-widget detection.
- **Telephony** (SignalWire / Twilio / Vapi) — the call result + Answering-Machine Detection for
  the after-hours outcome.
- **Jobs search** (Google Jobs / Indeed via a search API, e.g. SerpAPI) — the front-desk hiring
  signal. *This is the only signal needing a third-party API; it can be deferred to v2.*

**Signal -> source -> method:**

| Signal | Source | Method | Auto? | Note |
|---|---|---|---|---|
| `new_business` | Google Places | review count + earliest-review date | ✅ clean API | free within Places response |
| `review_reachability` | Google Places | ~5 review texts, regex (§3) | ✅ clean API | deeper reviews need paid API later |
| `no_online_booking` | business website | HTTP fetch + scan for booking widgets | ✅ scrape (own target) | some JS-rendered sites = best-effort |
| `after_hours_voicemail` | telephony | the outreach call + AMD | ✅ on call | post-attempt enrichment |
| `job_ad_frontdesk` | Google Jobs/Indeed | search API (SerpAPI) or skip | ⚠️ needs 3rd-party | defer to v2 if not ready |

**The flow (per daily cron run):**
1. Cron fires the prospect job (`_job_prospect_us` / `_ca`).
2. Places API: Text Search `"{vertical} in {city}"` -> Place Details per result -> dedupe by `place_id`.
3. Enrich each NEW lead: `new_business` + `review_reachability` from the Places data; `email` +
   `no_online_booking` from a website fetch; `job_ad_frontdesk` from the jobs API (if enabled).
4. Compute `pain_score`, `pain_signal`, `pain_finding`; store on the lead.
5. Rank the queue by score; email + Sophie voice contact follow (Change #7). The after-hours call
   outcome writes `after_hours_voicemail` back as further enrichment.

No human in the loop except setting targets and approving — exactly as intended.

**Cost / fragility (honest):** Places API is per-request — budget for it at ~300 leads/day (Text
Search + Place Details each bill); a website fetch is free but JS-only sites may not reveal a
booking widget; job-ad detection needs a paid search API (SerpAPI) or gets deferred; reviews
beyond the Places ~5 need a paid reviews API later.

## 1. Data model — fields to add to `leads`

```
pain_score        int        # 0-100, computed
pain_signals      jsonb      # list of {signal, weight, detail} that fired
pain_finding      text       # the single best human-readable finding for the opener
                             # e.g. "after-hours call went to voicemail (tested 8:10pm)"
hours_json        jsonb      # opening hours from Google Places
has_online_booking bool
last_probe_outcome text      # human | voicemail | no_answer | busy | failed | null
last_probe_at     timestamptz
```

---

## 2. Signal catalog (weights are starting hypotheses — let Signal recalibrate)

| # | Signal | Source / how | Weight | Feeds opener? |
|---|---|---|---|---|
| 1 | **Active receptionist / front-desk job ad** | Indeed / Google Jobs search for the practice name + "receptionist/front desk" | **+30** | yes (strongest) |
| 1b | **Newly opened practice** | low review count (<~15) + earliest of the returned reviews within ~12 months (Google Places); optional later: new-business registries, "grand opening" social, GBP recently created | **+25** | yes (congratulatory framing) |
| 2 | **No online booking** | website scrape (no Calendly/Cal/NexHealth/Square/booking widget) + Google profile has no "Book online" action | **+20** | yes |
| 3 | **Reviews mention reachability problems** | review mining (§3) | **+20** (scaled by count×recency) | yes |
| 4 | **After-hours call → voicemail / no answer** | probe = the outreach call itself (§4) | **+25** | yes (best, specific) |
| 5 | **Reviews mention booking/scheduling problems** | review mining (§3) | **+15** | yes |
| 6 | **No website / phone-only** | Google Places `website` empty | **+10** | soft |
| 7 | **Solo practitioner / no admin staff** | website/listing heuristic ("Dr. X" only) | **+5** | soft |
| 8 | **Rating dip / recent negative velocity** | Places rating + recent review sentiment | **+5** | no (targeting only) |

`pain_score = min(100, sum of fired weights)`
Tiers: **0–30 low · 31–60 medium · 61–100 high.** High tier is dialed first (feeds the Change #7 priority queue) and gets the most specific opener.

---

## 3. Review-mining phrases

Fetch reviews, lowercase, and match the patterns below (case-insensitive regex). **API note:**
Google Places `place details` returns only ~5 reviews; for deeper mining use a reviews API
(SerpAPI / Outscraper) — respect each source's ToS. Score = (matches × recency factor),
capped per category.

**A. Reachability (weight: high) — the core PracticeDesk pain**
```
couldn'?t get through | can'?t get through | no ?one (answers|picks up) | nobody answers
| never answer the phone | phone (just )?rings (and rings)? | goes (straight )?to voicemail
| left (a|several|multiple) messages? | never (call|called) (me )?back | impossible to reach
| on hold (forever|for ages)
```

**B. Booking / scheduling friction (weight: medium)**
```
hard to (book|get an appointment) | took (weeks|forever) to get | can'?t get an appointment
| booking (is|was) a (nightmare|hassle|pain) | couldn'?t book | no availability
```

**C. Scheduling chaos / no-shows / records (weight: medium)**
```
no record of my appointment | lost my appointment | double[- ]?booked | forgot my appointment
| cancelled (on me|last minute) | overbooked | kept (me )?waiting | long wait time
```

**D. Front-desk / staffing (weight: low–medium, also hints at signal #1)**
```
front desk (was )?(rude|unhelpful|overwhelmed) | receptionist (was )?(rude|unhelpful|gone)
| disorgani[sz]ed | chaotic | under ?staffed | short[- ]staffed
```

For the opener, pick the single most recent/relevant matched quote as `pain_finding`
(e.g. *"a couple of your reviews mention trouble getting through on the phone"*).

---

## 4. After-hours probe logic (do it WITHOUT nuisance calls)

**Key design choice:** do **not** place separate silent/dead-air "probe" calls — that's a
nuisance and risks looking like a robocall. Instead, **the outreach call itself is the probe.**

1. Read `hours_json` (Google Places `opening_hours`). Pick a dial time **just after close**
   (or, for overflow signal, a busy mid-day window).
2. Place the normal Sophie outreach call via existing telephony (SignalWire / Twilio / Vapi),
   with **Answering-Machine Detection (AMD)** enabled.
3. Classify the call result → `last_probe_outcome`:
   | Outcome | Meaning | Action |
   |---|---|---|
   | `human` | someone answered after hours | great — Sophie pitches live; low after-hours pain |
   | `voicemail` (AMD = machine) | call hit voicemail | **+25 pain**; `pain_finding` = "after-hours call went to voicemail (tested {time})"; queue an email + next-day call citing it |
   | `no_answer` / rang out | no pickup, no VM | **+20 pain**; similar follow-up |
   | `busy` (during hours) | line engaged | overflow signal; +10 |
   | `failed` | bad number | flag lead for review |
4. **One probe attempt.** Store outcome + timestamp. Business numbers are DNC-exempt, but keep
   it to a single, normal-hours-aware attempt — no repeated dialing.

This way the probe costs nothing extra (it's the call you were making anyway), bothers no one
with dead air, and produces a true, specific finding for the follow-up touch.

---

## 4b. New-business detection & framing

**Detect (cheap, buildable now from data we already fetch):** flag `new_business` when the Google
Places `user_ratings_total` is low (< ~15) **and** the earliest of the returned reviews is recent
(within ~12 months) — or rating count is very low (<5). Optional later enrichment: new-business
registries (US Secretary of State / state dental boards; CA provincial registries; AU ABN/ASIC),
Chamber-of-Commerce new members, "grand opening" social posts.

**Caveat (be honest):** review-age is a *proxy*, not proof — a low-review listing could be an old
practice newly added to Maps, or simply a quiet one. Treat `new_business` as probabilistic: use it
to prioritise and tailor the opener, and have Sophie confirm gently ("Are you fairly new in the
area?") and pivot if not.

**Value framing flips for new businesses.** Do NOT use loss/"you're missing patients" language —
they have few patients yet. Emphasise **growth**: capture every first-time inquiry, look like an
established 24/7 operation from day one, no need to hire reception yet. New owners respond to
"help me grow / look professional", not "you have a problem". New practices also often stack
signals (new + hiring + no online booking) → high `pain_score` → call first. Email may be weaker
(generic/no scraped address yet), so **phone is the better first touch** for this segment.

## 5. How it plugs in

- **Ranking:** `pain_score` boosts position in the Change #7 voice queue and email targeting
  (high-pain dialed/emailed first).
- **Personalisation:** `pain_finding` fills Sophie's Opener A/B (`sophie-dental-call.md`) and can
  seed an email subject ("Noticed something about {PRACTICE_NAME}'s phone after hours").
- **Learning:** log which signals preceded a booked demo / trial; Signal recalibrates weights
  monthly. Drop signals that don't correlate with conversion.

**Hard rule:** every finding used in an opener must be real and logged. Never invent a finding.
