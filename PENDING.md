# Apex — Pending Items

Tracks work that's been discussed/scoped but deliberately not built yet.
Read alongside `CLAUDE.md`.

---

## Sophie — self-serve demo-line offer (job-ad calls)

**Status:** Pending — not started.
**Raised:** 2026-07-08, during Change #11 (job-ad scout) build.

**What's wanted:** `docs/apex-rebuild/job-ad-outreach.md`'s voice section says Sophie should
be able to offer prospects a phone number they can call *immediately* (mid-conversation,
self-serve — no scheduling) to hear Claire (the AI receptionist) answer a live call, e.g.:

> "Want to hear it for yourself? Call [number] right now and Claire will pick up like a
> real patient would."

**What exists today (confirmed 2026-07-08):**
- Sophie's script only has a *scheduled* demo flow — `book_demo` tool, asks for day/time
  + email, books via Cal.com. That's a human-scheduled callback, not a self-serve number.
- No demo phone number is threaded into Sophie's Vapi call variables anywhere
  (`agents/vapi_caller.py place_sophie_call` has no such field).
- No line in the system prompt (`scripts/update_vapi_sophie_prompt.py`) instructs her to
  offer one.
- This gap isn't job-ad-specific — no lead segment currently gets this offer from Sophie.

**To build later:**
1. Decide which number to offer (candidates already in the repo: `INBOUND_PHONE` =
   +1 (318) 770-6725 used in email copy's "call and try me like a patient would" CTA, or
   the Bright Smile Dental demo line +1 289-514-1951 used on Mehak's page — need a real,
   always-live demo number, not the seeded-data Bright Smile line).
2. Add a `demo_number` variableValue to `place_sophie_call()` (mirrors how
   `pricing_line`/`pain_signal` are already threaded through).
3. Add an offer line to the system prompt (Phase 4 Trial Offer or Phase 5 objection
   handling reads naturally) and push via `update_vapi_sophie_prompt.py`.

---

## Job-ad email — Claire demo-line offer scope check

Related to the above: confirm whether the *email* sequence's existing `{INBOUND_PHONE}`
CTA ("call {INBOUND_PHONE} and try me like a patient would") already satisfies the
email-side version of this requirement, or if it also needs updating once the voice
number is finalized (keep both channels pointing at the same number).
