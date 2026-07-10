DEMO_LINK = "https://cal.com/neeraj-khattar-3zszap/practicedesk-demo"
PRODUCT_URL = "https://practicedesk.live"
INBOUND_PHONE = "+1 (318) 770-6725"
INBOUND_PHONE_RAW = "+13187706725"

# Job-ad sequence pricing line (docs/apex-rebuild/job-ad-outreach.md) — a single
# approximate monthly figure, not the full tier breakdown used elsewhere (click_caller.py).
VOICE_PRICE_USD = "$180/month"
VOICE_PRICE_CAD = "CA $200/month"
VOICE_PRICE_GBP = "£149/month"

# YouTube intro video — shown for all medical/professional verticals
YOUTUBE_INTRO = "https://youtu.be/zHVLE5ek7jY"

# Each template: subjects = list of (text, variant_letter), body = HTML string with {VAR} placeholders
TEMPLATES = {
    1: {
        "use_when": "No review pain found · Market AU or US · Day 1",
        "subjects": [
            ("{PRACTICE_NAME}'s after-hours calls", "A"),
            ("The patient who called {PRACTICE_NAME} at 6pm", "B"),
            ("A question about your front desk, {FIRST_NAME}", "C"),
            ("73% of dental practices in {STATE} have this problem", "D"),
            ("What happens when {PRACTICE_NAME}'s phone rings at 9pm?", "E"),
        ],
        "body": """\
<p>Hi {FIRST_NAME},</p>
<p>{PAIN_LINE}</p>
<p>Every call that reaches voicemail after hours is a patient who calls the next practice instead. Most dental practices in {CITY} lose 8–12 bookings a week this way — they just never see it happening.</p>
<p>PracticeDesk gives {PRACTICE_NAME} an AI receptionist that answers every call and WhatsApp message 24/7 — books the appointment, sends a confirmation, and puts it in your dashboard for you to review. You confirm in one click. No staff involved.</p>
<p>Practices using it report <strong>53% more bookings in the first 30 days.</strong></p>
<p>Worth a 10-minute look?</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">See it working →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. 14-day free trial — no setup fees, no IT help needed.</em></p>""",
    },

    2: {
        "use_when": "Review mining finds booking/communication pain · Day 1 (replaces Email 1)",
        "subjects": [
            ("Re: the review {PRACTICE_NAME} received recently", "A"),
            ("One of your patients couldn't get through, {FIRST_NAME}", "B"),
            ("{FIRST_NAME} — a patient left this about {PRACTICE_NAME}", "C"),
            ("What's costing {PRACTICE_NAME} patients every week", "D"),
        ],
        "body": """\
<p>Hi {FIRST_NAME},</p>
<p>{PAIN_LINE}</p>
<p>It happens to every practice — the phone rings during a consultation, nobody answers, the patient moves on.</p>
<p>PracticeDesk solves it completely. Your calls and WhatsApp messages get answered 24/7 by an AI that speaks in your practice's name, books appointments, and sends confirmations automatically.</p>
<p>You stay in control — every booking sits in your dashboard pending your one-click approval before it's confirmed. The AI never finalises a sensitive appointment without you.</p>
<p>Happy to show you a 5-minute demo of the actual booking flow.</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">Book a demo →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. {REVIEW_LINE}</em></p>""",
    },

    3: {
        "use_when": "No reply to Email 1 or 2 · Day 3",
        "subjects": [
            ("Try this right now, {FIRST_NAME}", "A"),
            ("Call {PRACTICE_NAME} from a different number tonight", "B"),
            ("A 30-second test for your practice", "C"),
            ("{FIRST_NAME} — honest question about your phone", "D"),
        ],
        "body": """\
<p>{FIRST_NAME} —</p>
<p>Try this: call {PRACTICE_NAME}'s main number tonight after 6pm from a different phone.</p>
<p>If it goes to voicemail — that's what your patients hear. <strong>67% of them won't leave a message.</strong> They'll call the next dentist instead.</p>
<p>PracticeDesk answers that call. Every time. Books the appointment. Sends the confirmation. From $49/month — and the $180 setup fee is waived until 29 July 2026. No staff. No upfront cost right now.</p>
<p>One recovered appointment pays for three months.</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">5-minute demo →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. Setup takes 20 minutes. The AI answered its first call the same evening for every practice we've set up so far.</em></p>""",
    },

    4: {
        "use_when": "No reply to Email 3 · Day 6",
        "subjects": [
            ("Dental practices in {NEARBY_CITY} using this", "A"),
            ("What changed for a {CITY} dental practice in 30 days", "B"),
            ("{FIRST_NAME} — results from practices like yours", "C"),
            ("53% more bookings. Here's how.", "D"),
        ],
        "body": """\
<p>{FIRST_NAME},</p>
<p>A dental practice similar to {PRACTICE_NAME} — solo practitioner, {STATE} — was missing an estimated 10 after-hours bookings per week.</p>
<p><strong>30 days after PracticeDesk:</strong></p>
<ul style="padding-left:20px;margin:8px 0;">
  <li>Missed calls: near zero</li>
  <li>After-hours bookings: up significantly</li>
  <li>Front desk time spent on admin: cut in half</li>
  <li>First month cost: $49 (Starter plan) — setup fee $180 waived until 29 Jul 2026</li>
</ul>
<p>The setup took 20 minutes. The AI answered the first call that same evening.</p>
<p>If missed calls are quietly costing {PRACTICE_NAME} patients, this is the fix.</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">See the full demo →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. 14-day free trial. Cancel any time. Plans from $49 · $99 · $180/month. Setup fee $180 waived until 29 Jul 2026.</em></p>""",
    },

    5: {
        "use_when": "No reply to Email 4 · Day 9",
        "subjects": [
            ("The objection I hear most from dentists, {FIRST_NAME}", "A"),
            ('"We already have a receptionist" — heard this before', "B"),
            ("Three reasons dentists say no (and why they change their mind)", "C"),
            ("{FIRST_NAME} — what's stopping {PRACTICE_NAME}?", "D"),
        ],
        "body": """\
<p>{FIRST_NAME},</p>
<p>Most dentists who hear about PracticeDesk say one of three things:</p>
<p><strong>"We already have a receptionist."</strong><br>
PracticeDesk works alongside your receptionist — not instead of them. It handles after-hours, overflow, and WhatsApp while your receptionist focuses on patients in the chair. Two of them together miss nothing.</p>
<p><strong>"We're too busy to set something like this up."</strong><br>
Setup takes 20 minutes. We've timed it. The AI is answering calls the same evening.</p>
<p><strong>"I don't want AI making clinical decisions."</strong><br>
It doesn't. The AI collects booking details and creates a pending request. You review it in your dashboard and confirm or decline with one click. The AI never confirms a sensitive appointment without you.</p>
<p>Still not sure if it fits {PRACTICE_NAME}? The demo takes 10 minutes and shows the exact flow — no sales pressure, just the product working.</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">Book a demo →</a></p>""",
    },

    6: {
        "use_when": "Market = CA · Day 1 (overrides Email 1 and 2 for all Canadian prospects)",
        "subjects": [
            ("9 million new dental patients in Canada — is {PRACTICE_NAME} ready?", "A"),
            ("The CDCP just sent {CITY} practices new patients, {FIRST_NAME}", "B"),
            ("Canada's Dental Care Plan created your biggest opportunity", "C"),
            ("{FIRST_NAME} — are you capturing the CDCP patients calling now?", "D"),
            ("New dental coverage. New patients calling. New problem.", "E"),
        ],
        "body": """\
<p>Hi {FIRST_NAME},</p>
<p>Canada's Dental Care Plan just extended coverage to 9 million previously uninsured Canadians.</p>
<p>That means more patients calling practices in {CITY} for the first time. The question is whether {PRACTICE_NAME} captures them — or whether they reach your voicemail and call someone else.</p>
<p>The practices that fill their books this year will be the ones that answer first. Every time. Including evenings, weekends, and the moments you're mid-treatment.</p>
<p>PracticeDesk gives {PRACTICE_NAME} an AI receptionist that answers every call and WhatsApp message 24/7, books appointments automatically, and puts every booking in your dashboard for one-click confirmation.</p>
<p><strong>Setup takes 20 minutes. Trial is 14 days free.</strong></p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">See a 10-minute demo →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. The CDCP rollout has already driven a measurable increase in first-time patient inquiries across Canadian dental practices. The window to position {PRACTICE_NAME} as the practice that always answers is right now.</em></p>""",
    },

    7: {
        "use_when": "No reply to any previous email · Day 12 · Final email",
        "subjects": [
            ("Closing {PRACTICE_NAME}'s file", "A"),
            ("Last email from me, {FIRST_NAME} — then I'll leave you alone", "B"),
            ("I'll stop here, {FIRST_NAME}", "C"),
            ("Final note about {PRACTICE_NAME}", "D"),
        ],
        "body": """\
<p>{FIRST_NAME},</p>
<p>I've reached out a few times — clearly the timing isn't right or PracticeDesk isn't a fit for {PRACTICE_NAME}, and that's completely fine.</p>
<p>I'm closing your file so I'm not cluttering your inbox.</p>
<p>If the front-office problem ever becomes something you want to solve — missed calls, after-hours bookings, WhatsApp follow-ups — the demo is always open and the 14-day trial is always free.</p>
<p>Wishing {PRACTICE_NAME} a full schedule.</p>
<p>{SENDER_NAME}<br><a href="{PRODUCT_URL}" style="color:#4f46e5;">practicedesk.live</a></p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">Start free trial anytime →</a></p>
<p style="font-size:13px;color:#999999;margin-top:24px;border-top:1px solid #eeeeee;padding-top:12px;">You won't hear from me again after this. To ensure that: <a href="{UNSUBSCRIBE_LINK}" style="color:#aaaaaa;">unsubscribe</a></p>""",
    },

    8: {
        "use_when": "Prospect opened at least one email but never replied · Day 30 after break-up",
        "subjects": [
            ("One thing changed since I last emailed, {FIRST_NAME}", "A"),
            ("New at PracticeDesk — relevant to {PRACTICE_NAME}", "B"),
            ("{FIRST_NAME} — something new that might change the picture", "C"),
        ],
        "body": """\
<p>{FIRST_NAME},</p>
<p>Quick update since I reached out last month —</p>
<p>PracticeDesk now includes a voice agent that answers {PRACTICE_NAME}'s phone calls in your name, books appointments by voice, and automatically follows up missed calls with a WhatsApp message to the patient.</p>
<p>So when a patient calls at 9pm on a Sunday:</p>
<ul style="padding-left:20px;margin:8px 0;">
  <li>Voice answers: "Hi, thanks for calling {PRACTICE_NAME}"</li>
  <li>Books the appointment in the conversation</li>
  <li>Sends a WhatsApp confirmation to the patient</li>
  <li>Puts the booking in your dashboard for one-click confirm</li>
</ul>
<p>Plans from $49 · $99 · $180/month. Setup fee $180 waived until 29 Jul 2026. Still 14 days free.</p>
<p>If anything's changed since we last connected — whether you're busier, growing, or just tired of missed calls — worth 10 minutes.</p>
<p><a href="{DEMO_LINK}" style="display:inline-block;background-color:#4f46e5;color:#ffffff;padding:11px 24px;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold;">Book a demo →</a></p>
<p style="font-size:13px;color:#666666;margin-top:24px;"><em>P.S. This is genuinely the last email I'll send. If the timing is ever right: <a href="{PRODUCT_URL}" style="color:#4f46e5;">practicedesk.live</a></em></p>""",
    },
}
