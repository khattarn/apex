# Claude Code Handoff — Apex Route A (Email fix + guardrail + monitoring)

**Repo:** `C:\Projects\apex`  ·  **Backend:** `outreach-agent/` (FastAPI on Railway)  ·  **Frontend:** `admin-dashboard/` (Netlify)
**Read first:** `CLAUDE.md`, `docs/apex-rebuild/apex-rebuild-plan.html`

You are continuing a project that was reviewed and planned in Cowork. This document tells you **exactly what to change in code**, in priority order, with acceptance criteria. Do **not** re-architect. Connect what exists and add a guardrail + monitoring.

---

## What was produced for you in Cowork (already in the repo)

These are **assets**, in `docs/apex-rebuild/`. Your job is to wire them in — do not regenerate them.

| File | What it is | What you do with it |
|---|---|---|
| `email_copy.yaml` | Vertical-aware email sequences (dentist, physiotherapist, salon, accountant, lawyer + `defaults`). 4 emails each: 2 A/B subjects, `preheader`, `body` (HTML), per step. Placeholders match the existing renderer: `{PRACTICE_NAME} {CITY} {STATE} {DEMO_LINK} {PRODUCT_URL} {SENDER_NAME} {INBOUND_PHONE}`. | Move to `outreach-agent/assets/email_copy.yaml` and make `generate_email` consume it (Change #1). |
| `sample-emails.html` | Visual preview of all 20 emails (for human review only). | Reference; do not ship. |
| `apex-rebuild-plan.html` | Full context + plan. | Background. |
| `channel-strategy.html` | Per-market (US/CA/AU) channel strategy. | Background for Change #6. |
| `_master_prompt.py` | Shared master system prompt + `compose()` helper. | Add to `agents/` (Change #3). |
| `agent_prompts.py` | Per-agent specific prompts (`AGENT_PROMPTS`, `get_prompt`). | Add to `agents/` (Change #3). |

> The master prompt AND the per-agent prompt pack are both ready in `docs/apex-rebuild/` (`_master_prompt.py`, `agent_prompts.py`). **Do Changes #1–#2 first** (they stop the active damage); then #3; #4–#6 follow.

---

## Change #1 — Make email generation vertical-aware  🔴 TOP PRIORITY

**Problem:** `agents/email_personalizer.py → generate_email()` reads `business_type` (line ~247) and never uses it. `agents/email_templates.py` is 100% dental. The daily job `_job_email_campaign` therefore sends dental copy ("Dear Doctor… 73% of dental practices…") to salons, accountants and lawyers.

**Do this:**
1. Add a loader for `assets/email_copy.yaml` (cache like `personalizer._load_copy()` does for `copy.yaml`).
2. In `generate_email(lead, email_number=...)`:
   - Resolve `vertical = (lead.get("business_type") or "").lower().strip()`.
   - Select `seq = email_copy["verticals"].get(vertical)`. If missing, see Change #2 (do **not** fall back to dental).
   - Map the sequence step → entry. The existing `EMAIL_SEQUENCE` / `email_sequence_step` drives cadence; map step N to `seq["sequence"][N-1]` (clamp to last). Keep the existing day spacing.
   - Pick subject via A/B on `subject_a`/`subject_b` (reuse `pick_subject` logic / random A-B).
   - Set the body from the entry's `body`. Inject the `preheader` as a hidden preheader span at the top of the HTML shell (`<span style="display:none;max-height:0;overflow:hidden;">{preheader}</span>`) for inbox preview.
   - **Fix the salutation:** remove the hard-coded `"FIRST_NAME": "Doctor"`. Either drop the salutation (the new bodies open with the hook, no "Hi Doctor") or set a vertical-safe default. Do not address a salon as "Doctor".
3. Keep using the existing `_render()` shell, footer, tracking pixel, compliance-by-market, and CTA buttons — only the **body/subjects/preheader source** changes.
4. Leave `email_templates.py` in place for now but **stop referencing it** from `generate_email`. (Delete in a later cleanup once verified.)

**Acceptance:**
- `generate_email({"business_type":"salon","name":"Glow Studio","city":"Sydney",...})` returns salon copy with no "patient"/"dentist"/"Doctor"/"CDCP" anywhere.
- Same for accountant and lawyer.
- `dentist` output is unchanged in quality/positioning.
- A quick assertion test over all five verticals: subject + body contain `{PRACTICE_NAME}`-substituted name and **none** of `["dentist","patient","Doctor","CDCP"]` for non-dental verticals.

---

## Change #2 — Fail safe, never fail dental  🔴

**Problem:** unknown/missing `business_type` currently means dental copy.

**Do this:**
- If `vertical` has no entry in `email_copy["verticals"]`, use `email_copy["defaults"]` (generic, never wrong).
- In `_job_email_campaign` (and `/api/leads/email-campaign`), **skip** a lead whose `business_type` is empty/unknown rather than emailing it, and log a `skipped_unknown_vertical` count. Better a missed send than a wrong-vertical send.

**Acceptance:** a lead with `business_type=""` is skipped (counted), not sent dental copy. A lead with an unrecognised but non-empty type gets `defaults`.

---

## Change #3 — Master prompt + pre-send guardrail  🟠

**Problem:** no shared brand/vertical rule; nothing blocks wrong-vertical or off-brand sends.

**Do this:**
1. Copy both `docs/apex-rebuild/_master_prompt.py` and `docs/apex-rebuild/agent_prompts.py` into `outreach-agent/agents/`. Wire every Claude call as `system=compose(get_prompt("<agent>"))` — `compose()` prepends the master prompt and the per-agent brief sits beneath it. Specifics:
   - Agents with their own rich prompt (`content_agent`, `vp_marketing`) have a `None` entry in `AGENT_PROMPTS` — keep their existing `_SYSTEM_PROMPT` and wrap it: `system=compose(_SYSTEM_PROMPT)`.
   - Thin agents (`reply_handler`, `personalizer`, `followup`, `demo_booking`, `observatory`, `affiliate`, voice/Sophie, `signal`) use `system=compose(get_prompt("<agent>"))`.
   - The intent classifier (`reply_handler_intent`, a ~10-token call) uses `MASTER_PROMPT_LITE` directly — do NOT prepend the full master prompt there.
   - The `ceo` brief powers the daily growth-operator loop; wire it when that agent is built (Change #4/CEO work).
2. Add a lightweight **pre-send guardrail** used by the email + WA send paths: a function that asserts the rendered copy matches the lead's vertical (cheap string/heuristic check: non-dental lead must not contain dental-only tokens; product/brand line present; positioning not "WhatsApp chatbot"). On failure: do not send, log + raise to the monitoring layer (Change #4).

**Acceptance:** every agent's Claude call includes the master prompt; the guardrail blocks a deliberately mismatched test send and records it.

---

## Change #4 — Monitoring: catch silence, zero-output, and dead dependencies  🟠

**Problem:** `utils/alerter.py` only fires on a job **exception**. It misses: a job that stops firing, a job that runs but sends 0, and a dependency that dies. It also alerts over WhatsApp only — so a broken WA token blinds all alerting.

**Do this:**
1. **Heartbeat table** (Supabase migration): `agent_health(job text, last_success_at timestamptz, last_run_at timestamptz, last_result jsonb, updated_at)`. Each scheduler job upserts on success with counts (ran/sent/skipped/failed, duration).
2. **Watchdog job** (hourly): compare each job's `last_success_at` against its expected cadence; alert on overdue with a reason string (e.g. `"email_campaign last success 26h ago, expected every 12h — scheduler likely not restarted after deploy"`).
3. **Threshold alerts** inside jobs: `>30%` sends failed in a run; `0` new leads in 48h; `0` replies in 7d; Resend quota hit; Maps returned 0. Each carries a plain-English probable cause.
4. **Dependency probes** (daily + on-demand `/health/deep`): ping Anthropic, Supabase, Resend, Google Maps, Meta WA, Vapi/SignalWire; report up/down + reason. Extend the Settings "API health checks" to run on schedule.
5. **Dedup + severity:** alert once per incident (🔴 broken / 🟠 stalled / 🟡 degraded), send a "✅ resolved" when it clears. No hourly spam.

**Acceptance:** killing the scheduler (or simulating a stale `last_success_at`) produces one 🔴 overdue alert with a reason; a run that sends 0 produces a 🟠 alert; `/health/deep` returns per-dependency status.

---

## Change #5 — Dual-channel founder intimation (WhatsApp + email)  🟠

**Problem:** alerts/briefs go over WhatsApp only, and Meta blocks business-initiated WA outside the 24h window without an approved template.

**Do this:**
1. Generalise `alert_founder` (and the daily brief) into a `notify_founder(kind, payload)` that sends via **both** email (Resend, always works) **and** WhatsApp.
2. WhatsApp path uses two **UTILITY** templates you submit to Meta on the outreach number (Phone Number ID `1122821020915109`):
   - `apex_daily_brief` — 1 body variable (brief text)
   - `apex_system_alert` — variables: severity, component, reason
   Use the existing `submit_v6_templates.py` pattern to submit.
3. Until templates are approved, **email carries everything** (so you are never blind in the interim). Email is also the fail-safe if the WA token is the thing that broke.

**Acceptance:** a test alert arrives by email immediately; once templates are approved, the same alert also arrives on WhatsApp; a forced WA-token failure still delivers the alert by email.

---

## Change #6 — Channel re-ranking & a separate Canada track  🟠

**Why:** see `docs/apex-rebuild/channel-strategy.html`. WhatsApp is a minority channel in US/CA/AU (US ~23%, AU ~33%, CA lower); email is the B2B-preferred channel. The system currently treats WA broadcast as a primary cold push for these markets — effort on the wrong channel — and emails all markets at one volume, which is a CASL risk in Canada.

**Do this:**
1. **Re-rank channels for US/CA/AU** (do NOT touch India/LegalAidAI, where WA-first is correct):
   - **Email = primary engine** (Changes #1–#2 already make it vertical-correct).
   - **Sophie voice = engagement-triggered follow-up**, not cold-first. Trigger a voice-call task when a lead opens/clicks (use the existing tracking pixel/click events) rather than blasting `_job_wa_broadcast` / `_job_voice_followup` cold at scale.
   - **WhatsApp = post-opt-in only** in these markets. Demote cold WA broadcast for US/CA/AU leads; keep WA for leads who have replied/opted in (reply_handler, demo booking). Gate `_job_wa_broadcast` by market + opt-in status.
2. **Separate Canada (CASL) track** in `_job_email_campaign`:
   - Canada leads: lower daily cap, send only to scraped **published** business emails (already validated by `email_scraper`), respect implied-consent windows (EBR ~2 years / inquiry ~6 months), guarantee a working unsubscribe. Do not fold Canada into the same high-volume queue as AU/US.
   - Keep the existing CDCP ("Canada Dental Care Plan") timeline hook for Canadian dentists — it tested as the right angle.
3. **Send timing:** schedule sends for **Thursday + local evening** where practical (timezone-aware), the highest-reply window in the benchmarks.
4. **Hook A/B:** register a Signal experiment comparing timeline-style subject hooks vs. the current moment-based hooks in `email_copy.yaml`. Let Signal pick the winner; don't hardcode an assumption.

**Acceptance:**
- US/CA/AU cold WA broadcast no longer fires for non-opted-in leads; WA still works for replied/opted-in leads.
- Canada email runs on its own lower-volume, published-email-only path with unsubscribe enforced.
- A voice follow-up is triggered by email engagement, not by a blanket cold cron.
- Signal shows a hook A/B test running.

---

## Change #7 — Automate the lead pipeline (sprint: 7 trial signups/week, US+CA)  🟢

**Goal:** stop manual prospecting; feed ~300 qualified US/CA dentist leads/day and run email + voice to produce ~7 trial starts and 50+ engaged prospects in the week. Domain is warm (already sending up to 180/day), so email is the primary channel.

**Do this:**
1. **Add prospecting cron jobs** (`_job_prospect_us`, `_job_prospect_ca`):
   - Run daily; each prospects a **config-driven list** of `(business_type, city)` pairs stored in the `settings` table (key e.g. `prospect_targets`) so Neeraj can change cities/verticals without a redeploy.
   - Pipeline per lead: `find_businesses` → `scrape_email` → dedupe by `place_id` → `save_lead`. Target **~300 new leads/day total** (~150 US, ~150 CA).
   - Suggested times: `_job_prospect_us` at 12:00 UTC, `_job_prospect_ca` at 13:00 UTC (ahead of the email sends).
2. **Retune `_job_email_campaign`:** daily cap ~150 (ceiling 180), send in US + CA morning windows (13:00 UTC = CA 9am ET, 15:00 UTC = US 11am ET). Canada stays on its own lighter CASL track (Change #6).
3. **Voice as a priority queue (email first, voice 24h behind):** the call list is NOT cold-random and NOT "wait for a click". Email fires first; the voice job runs ~24h behind and dials in this priority order:
   `clicked  >  opened (no click)  >  emailed >24h ago (no open)  >  never-contacted`.
   Use the existing open/click tracking to rank. Sprint cap ~50–100 dials/day inside the 11am–5pm local window. (This resolves the apparent contradiction between `channel-strategy.html` "engagement-triggered" and the sprint's "fresh leads": it's a ranked queue, not either/or.)
4. **Engagement capture — required for the sprint to mean anything:**
   - Confirm WA inbound reply handling is live (it is).
   - **Add an email-reply path:** today only WhatsApp inbound is auto-handled. Either route inbound email replies to Henry (`reply_handler.generate_reply`) via an inbound-email webhook, or at minimum alert the founder on every email reply so it gets a fast human response. Do not let email replies sit unanswered.
5. **Daily founder read-out:** ensure the Observatory/CEO digest reports the sprint funnel each morning — prospected, emailed, replies, demos, trial starts — so rates can be recalibrated after ~3 days.

**Acceptance:** ~300 new deduped leads/day appear; ~150 emails/day send to US/CA dentists; ~50 Sophie calls/day place in-window; every email reply triggers a response or an alert; the morning digest shows the funnel.

---

## Change #8 — Fix the voice persona (Sophie everywhere) + naturalness  🟠

**Why:** the agent was named Sophie in the call plumbing (`place_sophie_call`, `VAPI_SOPHIE_ASSISTANT_ID`) but the spoken strings and all UI references have now been updated to match. Also reported as too robotic.

**Do this:**
1. ✅ Done: all spoken/persona strings, system prompts (`voice_sophie` key in `agent_prompts.py`), UI labels, docs, and knowledge-base files have been updated to Sophie. **Remaining:** update the Vapi assistant config in the Vapi dashboard (`VAPI_SOPHIE_ASSISTANT_ID`) — its greeting/system prompt is where the spoken name actually comes from on live calls (manual step in Vapi UI).
2. Load the new dental script from `docs/apex-rebuild/sophie-dental-call.md` into the voice config / `copy.yaml` for dentists.
3. Voice naturalness (Vapi dashboard): natural TTS voice, low latency, enable barge-in/interruption, 1–2 sentence turns. (Details in `sophie-dental-call.md`.)
4. Compliance flag: revisit the brand brief's "never reveal AI unless asked" rule against AI-voice disclosure law (FCC/TCPA in US, per-market). Sophie should not deny being AI if asked.

**Acceptance:** a live test call introduces as Sophie and uses the new script; no stale persona names remain in spoken strings or copy.yaml voice fields.

---

## Change #9 — "Dark-spot" qualification & pain score  🟢

**Why:** calling clinics that actually have the gap, with a true personalised opener, converts far better than generic dials. (Founder's idea — strong.)

**Do this:** add a qualification step (in the prospector or a new enrichment job) that computes a `pain_score` per lead from legitimate public signals:
1. **After-hours probe:** check/place a call outside the clinic's listed hours — voicemail / no answer / no IVR = high pain. (Legitimate: sampling a public-facing service.)
2. **Review mining:** scan Google reviews for phrases like "couldn't get through", "no answer", "left a message", "never called back", "hard to book" → pain signal. (Signal agent can do this.)
3. **Listing/website checks:** no online booking, no after-hours info, no chat widget.
Store `pain_signal` (type) + `pain_score` + `pain_finding` (the specific true detail) on the lead. Use it to (a) boost ranking in the voice priority queue (Change #7) and email targeting, and (b) personalise Sophie's opener honestly. Do NOT fabricate findings — only use real signals.

**Scope for v1:** build five high-yield signals — `job_ad_frontdesk`, `new_business` (low review count + recent earliest review from Google Places — buildable from data already fetched), `no_online_booking`, `review_reachability` (Places API ~5 reviews is enough; no paid reviews API yet), and `after_hours_voicemail`. `new_business` uses a **growth/congratulatory** opener, not a problem opener (see `sophie-dental-call.md` and §4b of the pain-score spec); phone is the better first touch for new practices.

**Pass the signal to Sophie:** `place_sophie_call` must pass `pain_signal` and `pain_finding` into the Vapi `initial_context` (`{{pain_signal}}`, `{{pain_finding}}`). Sophie's assistant prompt selects the matching **gentle** opener from the signal→opener table in `docs/apex-rebuild/sophie-dental-call.md` and must follow the six gentle-tone rules there (warmth first, normalise, point at the patient's experience not the clinic's failing, no numbers as a weapon, easy yes, back off if they bristle).

**Full spec (signals, weights, review-mining regex, probe logic, schema):** `docs/apex-rebuild/change9-painscore-spec.md`.

**Acceptance:** leads carry a `pain_score` + finding; high-pain leads rank first; Sophie's opener can cite the real finding.

---

## Change #10 — Automatic prospecting + enrichment (1 vertical × 3 cities/run, ~150/day)  🟢

**Goal:** fully automatic. Founder sets one focus vertical + a list of cities. Each run prospects
the **next 3 cities** (~50 leads each = ~150/day), using **multiple query synonyms per city**,
enriches every new lead with the pain signals, then rotates to the next 3 cities on the following
run. Builds directly on the dedup upgrade already in the repo. Enrichment module (written +
unit-tested): `docs/apex-rebuild/enrichment.py`.

**Already in the repo — build on these, do NOT recreate:**
- `database/client.get_existing_place_ids(business_type, city)` → saved `place_id`s for a city+type.
- `prospector.find_businesses(business_type, city, max_results, known_place_ids: set)` → skips
  known IDs *before* the paid Detail call and pages forward to collect `max_results` genuinely NEW
  businesses.
- `pipeline.py` already fetches known IDs and passes them through.

**Do this:**
1. **Add the module:** copy `docs/apex-rebuild/enrichment.py` into `outreach-agent/agents/`.
2. **Expand prospector fields:** request `enrichment.PLACES_DETAIL_FIELDS` in Place Details (adds
   `user_ratings_total`, `rating`, `reviews`, `opening_hours`, `business_status`) and return the
   full details dict per business so enrichment has its inputs.
3. **Add query synonyms:** change `BUSINESS_TYPE_QUERIES` values to LISTS, e.g.
   `"dentist": ["dental clinic", "dentist", "dental office"]`. Have `find_businesses` loop the
   synonyms for the city, **accumulating `known_place_ids` across synonyms** (and across the run)
   so the same place is never detailed twice. Synonyms + multi-city is what reliably yields the
   volume — a single query caps at ~60.
4. **Config in `settings`:**
   - `prospect_vertical` = e.g. `"dentist"`
   - `prospect_cities` = JSON list, e.g. `["Sydney NSW","Melbourne VIC","Brisbane QLD","Perth WA","Adelaide SA", …]`
   - `prospect_cursor` = `{"index":0}`
   - `cities_per_run` = `3`, `per_city_cap` = `50`
5. **Add cron `_job_prospect`:**
   - Load vertical, cities, cursor. Take the next `cities_per_run` cities from `cursor.index` (wrap).
   - For each city: `known = get_existing_place_ids(vertical, city)`; call
     `find_businesses(vertical, city, max_results=per_city_cap, known_place_ids=known)` (now loops
     synonyms). For each NEW business: `save_lead` → `fetch_website_html(website)` →
     `compute_pain(place_details, html)` → `update_lead` with `email` + `pain_score`,
     `pain_signal`, `pain_finding`, `pain_signals` (Change #9 schema).
   - Advance `cursor.index = (index + cities_per_run) % len(cities)` and save. Exhausted cities just
     return few/no new leads and the cursor keeps moving; re-visiting later naturally catches any
     newly-opened businesses.
   - Schedule e.g. `cron hour=12` (or split into 2 runs to spread API load).

**Acceptance:** each run yields ~150 new, deduped, **enriched** leads across 3 cities (≤50/city),
each with `pain_score`/`pain_signal`/`pain_finding`; no `place_id` is detailed twice (reuses
`known_place_ids`); the cursor rotates through the city list run over run; founder changes the
focus vertical/cities via `settings` only.

---

## Change #11 — Job-ad scout (SerpAPI Google Jobs → ingestion → job_ad_frontdesk)  🟢

**Why:** clinics actively hiring a receptionist are the warmest leads. Automate finding them daily
instead of screenshotting Indeed by hand. Indeed has no public API and scraping is fragile/ToS;
SerpAPI's Google Jobs engine returns clean JSON.

**Prereq:** SerpAPI account + `SERPAPI_KEY`. Free tier ~100–250 searches/mo; paid from ~$25/1,000.
All engines share one quota, so budget the daily search count.

**Do this:**
1. Add `SERPAPI_KEY` to Railway env + `.env`. Copy `docs/apex-rebuild/serpapi_client.py` into
   `outreach-agent/agents/` (or `utils/`). It's written + unit-tested and provides:
   `search_jobs(query, location, gl=...)`, `is_recent(posted_at, max_days)`,
   `to_ingest_rows(jobs, vertical, city)`, `JOBAD_QUERIES`, and `calls_made()` for quota logging.
2. **`_job_jobad_scout` cron (daily):** for each target city × `JOBAD_QUERIES[vertical]`, call
   `serpapi_client.search_jobs(query, city, gl="ca"/"us")`, filter with `is_recent(...)`, then
   `to_ingest_rows(...)` to get deduped `{name, city, vertical}` rows.
3. **Feed each row into the ingestion path** (reuse the name+city → Places Find Place → Details →
   dedupe by `place_id` → `save_lead` helper; build it if not present). Set
   `source="job_ad_serpapi"`, `pain_signal="job_ad_frontdesk"`,
   `pain_finding="actively hiring a front-desk receptionist"`. Scrape email as usual.
4. **Quota guard:** cap searches/day, log SerpAPI usage, and alert (via notify_founder) when nearing
   the monthly limit so you don't overrun the plan.
5. **Outreach for these leads** uses the job-ad override copy in `docs/apex-rebuild/job-ad-outreach.md`
   — the 3-email "application" sequence + Sophie's hiring voice opener. Phone-first; Canada on the
   lighter CASL email cadence.

**Narrative requirements (bake into the copy + Sophie's prompt):**
- Frame the AI as a **great addition to a human receptionist** — covers after-hours/overflow, makes
  the new hire better — NOT just "instead of hiring".
- Sophie opens in the **second person**: "I saw **you're** hiring…" (not the practice name).
- Sophie must **offer to answer any questions** they have, and offer to route them to Claire's demo
  line to hear it live.

**Acceptance:** the daily scout adds enriched `job_ad_frontdesk` leads from the target cities; no
`place_id` is detailed twice; SerpAPI usage is logged and under the cap; these leads receive the
application email sequence + Sophie's hiring opener (alongside-not-replacement framing, second-person,
offers to answer questions).

---

## Deliverability note (infra, do before scaling sends)  🟡

Cold email at 180/day from the main domain `practicedesk.live` — especially after past wrong-vertical sends — risks the whole domain's reputation. Before ramping volume: move cold outreach to a **subdomain** (e.g. `go.practicedesk.live`), set SPF/DKIM/DMARC, warm up, and ramp slowly. The `email_scraper` MX-validation already in place should gate the list. Flag this to Neeraj; do not just increase volume.

---

## Order of work
1. Change #1 + #2 (stops the active damage) → test → deploy.
2. Change #4 + #5 (so you can see failures and get told) .
3. Change #3 — master prompt is ready now (`docs/apex-rebuild/_master_prompt.py`).
4. Change #6 — channel re-ranking + Canada track.
5. Raise the deliverability item with Neeraj before increasing send volume.

Keep `pipeline.py` async (SSE, not WebSockets), dedupe leads by `place_id`, and never mix the outreach WA number with PracticeDesk's customer number — per `CLAUDE.md` conventions.
