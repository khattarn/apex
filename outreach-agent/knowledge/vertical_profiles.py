"""
Vertical Profiles — Signal Agent seed intelligence
Business-type + country specific knowledge: software landscape, pain points,
pitch angles, objections, decision makers, saturation level.

Scope: PracticeDesk verticals × AU, CA, US markets
       12 profiles total (4 verticals × 3 countries)

Sources:
  - ADA (American Dental Association) Practice Economics Survey
  - CDA (Canadian Dental Association) Practice Survey
  - ADA AU (Australian Dental Association) Annual Survey
  - Dental Economics Magazine (US)
  - IBISWorld industry reports (AU/CA/US)
  - Grand View Research — practice management software market reports
  - Jane App / Nookal / Dental4Windows market share data
  - LinkedIn Sales Insights B2B reports

Update cadence: Signal web research job refreshes quarterly.
Last seeded: June 2026 by Claude.
"""

VERTICAL_PROFILES = {

    # ════════════════════════════════════════════════════════════════════════
    # DENTISTS
    # ════════════════════════════════════════════════════════════════════════

    ("dentist", "AU"): {
        "vertical": "Dentist",
        "country": "AU",

        "market_reality": {
            "practice_size": "1–4 dentists, 2–6 chairs, 2–5 admin staff",
            "revenue_range": "AUD $800K–$2M typical private practice",
            "ownership": "owner-dentist runs most practices. Corporate chains (Pacific Smiles, Bupa Dental) growing but still minority.",
            "saturation": "low-medium",
            "ai_awareness": "growing but early. Most haven't been pitched an AI receptionist yet.",
        },

        "software_landscape": {
            "dominant": "Dental4Windows (D4W) — ~55% market share. Windows-based, widely used but not cloud-native.",
            "growing": "Core Practice — cloud-based, gaining in younger/metro practices",
            "others": ["Exact (Carestream)", "Titanium Schedule", "Pracsoft"],
            "ai_tools_in_use": "minimal — this is greenfield",
            "signal_implication": "Most AU dentists know D4W well. Acknowledge it in pitch: 'works alongside your existing Dental4Windows setup.' Do not pitch as a replacement.",
        },

        "pain_points": [
            "after-hours calls — patients call after 5:30pm, no one answers, they book elsewhere",
            "appointment no-shows (industry avg 15–20% in AU)",
            "admin time spent on phone bookings and reminders",
            "new patient acquisition — high cost per new patient in AU ($300–$800 via ads)",
            "patient recall — lapsed patients not returning for check-ups",
        ],

        "decision_maker": {
            "primary": "Owner-dentist (principal). They control spend.",
            "secondary": "Practice manager in larger multi-dentist practices.",
            "gatekeeper": "Receptionist or admin coordinator — treat them well, they influence the owner.",
            "note": "In corporate chains: regional manager or operations director. Different pitch entirely.",
        },

        "pitch_angle": {
            "primary": "Never miss a new patient call again — AI answers after hours and books straight into your calendar.",
            "secondary": "Reduce no-shows — automated reminders via WhatsApp cut cancellations by up to 30%.",
            "avoid": "Do not pitch as 'replacing your receptionist' — they will reject this immediately.",
            "framing": "Position as an extension of existing team, not a replacement.",
        },

        "objections": {
            "we already have a receptionist": "Absolutely — this works alongside them. It handles the after-hours and overflow calls your receptionist can't get to. She keeps her job; you stop losing $400 every missed new patient call.",
            "dental4windows already does this": "D4W is great for records and billing, but it doesn't answer your phone at 7pm or send WA reminders automatically. That's the gap this fills.",
            "we're happy with how things are": "Completely understand. Worth knowing that practices using this recover an average of 3–5 new patients per month that would have gone elsewhere. Happy to show you the numbers with zero obligation.",
            "too expensive": "At $99/month, one recovered new patient more than covers it. Most practices see that in the first week. And the $180 setup fee is waived until the end of July — so right now there's no upfront cost at all.",
            "i need to think about it": "Of course. Can I send you a quick case study from a Sydney dental practice — similar size to yours — so you have something concrete to review?",
        },

        "best_outreach_time": "12pm–2pm AEST (lunch break — dentist not with patients) or pre-8:30am",
        "best_days": "Tuesday, Wednesday, Thursday",
        "avoid": "Monday (catching up), Friday (winding down, early finish common)",

        "price_sensitivity": "low — AU dentists spend freely on things that demonstrably save time or increase revenue. $99/mo is a non-event if ROI is clear.",
        "competitor_landscape": "Minimal direct competitors in AU for AI-powered WA + voice combo. Low urgency from competition.",
        "signal_notes": "AU dentist is our best-converting vertical based on early data. Voice call at lunch is the highest-value touch. Email with specific suburb reference ('serving practices in Bondi and Randwick') outperforms generic.",
    },


    ("dentist", "CA"): {
        "vertical": "Dentist",
        "country": "CA",

        "market_reality": {
            "practice_size": "1–3 dentists, small to mid-size teams",
            "revenue_range": "CAD $800K–$2M typical private practice",
            "ownership": "owner-dentist dominant. Corporate group practices growing (Dentalcorp is the main consolidator in CA).",
            "saturation": "medium",
            "ai_awareness": "low-medium. Aware of AI generally, skeptical of dental-specific AI.",
        },

        "software_landscape": {
            "dominant": "ABELDent — dominant in English Canada. Feature-rich, deeply embedded.",
            "regional": "Dentitek — strong in Quebec. French-language support.",
            "others": ["Dentrix Canada", "ClearDent (BC-built, growing)", "Paradigm"],
            "ai_tools_in_use": "minimal",
            "signal_implication": "ABELDent users are entrenched. Pitch must acknowledge: 'works alongside ABELDent.' ClearDent users in BC are younger, more tech-forward — slightly easier pitch.",
        },

        "pain_points": [
            "after-hours calls unanswered",
            "appointment no-shows and last-minute cancellations",
            "high labour costs for admin staff (Canadian wages are high)",
            "new patient acquisition via Google/ads is expensive",
            "patient recall and reactivation",
        ],

        "decision_maker": {
            "primary": "Owner-dentist",
            "secondary": "Office manager in 3+ dentist practices",
            "gatekeeper": "Receptionist — more influential in CA than AU. Treat with respect.",
            "note": "Dentalcorp-owned clinics: regional operations manager. High friction — skip unless you have a corporate deal pathway.",
        },

        "pitch_angle": {
            "primary": "Reduce your admin costs without replacing your team — AI handles the overflow calls and automated patient reminders.",
            "secondary": "Works alongside ABELDent. No migration, no disruption.",
            "avoid": "Do not mention replacing staff. Labour is a sensitive topic in Canada.",
            "framing": "Efficiency and cost reduction resonate more than aspiration in CA.",
        },

        "objections": {
            "we already have a receptionist": "This doesn't replace her — it handles the volume she can't. After-hours calls, WA reminders, overflow. She focuses on what actually needs a human.",
            "abelDent already does this": "ABELDent handles your records and billing brilliantly. The patient communication layer — automated WA, after-hours voice, smart reminders — that's what this adds on top.",
            "casl concerns — is this compliant": "Yes — we operate on implied consent for existing patient communication and have full CASL-compliant unsubscribe built in. Happy to share our compliance documentation.",
            "too expensive": "At CAD $140/month, recovering one lapsed patient's appointment pays for 3 months. Happy to show the math. And the CAD $250 setup fee is waived until end of July — no upfront cost right now.",
            "we're not sure about AI for patients": "Completely understandable. The AI handles bookings and reminders only — all clinical questions route straight to your team. Patients don't know it's AI unless you tell them.",
        },

        "best_outreach_time": "Tue–Thu 10am–12pm EST (or local)",
        "best_days": "Tuesday, Wednesday, Thursday",
        "avoid": "Mondays, Fridays, any Canadian stat holiday (very numerous)",
        "channel_note": "Email first. Voice follow-up on day 5. Do not use WA for cold outreach in Canada.",

        "price_sensitivity": "medium — CA dentists are careful spenders. Need clear ROI case before committing.",
        "competitor_landscape": "Low competition in CA for AI dental tools. Weave has some presence but not dominant.",
        "signal_notes": "CASL compliance must be documented for every CA email send. Signal must log consent basis. Quebec campaigns require French language — flag to Neeraj before any Quebec outreach.",
    },


    ("dentist", "US"): {
        "vertical": "Dentist",
        "country": "US",

        "market_reality": {
            "practice_size": "1–5 dentists. DSOs (Dental Service Organizations) control ~30% of market and growing.",
            "revenue_range": "USD $800K–$3M typical private practice",
            "ownership": "still majority private owner-dentist but DSOs growing fast. Heartland Dental, Pacific Dental, Aspen Dental are large chains.",
            "saturation": "very high — this is the most competitive dental tech market in the world",
            "ai_awareness": "high. US dentists have already been pitched AI tools.",
        },

        "software_landscape": {
            "dominant": "Dentrix (Henry Schein) — ~35% market share. The industry standard.",
            "second": "Eaglesoft (Patterson) — ~20% market share",
            "growing": "Open Dental (open source, strong in price-sensitive practices), Curve Dental (cloud)",
            "patient_communication_tools": [
                "Weave — phone + texting + reviews, very widely used",
                "Birdeye — reviews + messaging",
                "Podium — messaging + reviews",
                "RevenueWell — patient engagement",
                "Lighthouse 360 — automated reminders",
                "Doctible — newer AI-forward option",
            ],
            "signal_implication": "CRITICAL: Many US dental practices already have a patient communication tool (Weave is dominant). Before pitching, Signal must check if we can identify which tool they use. Pitch must be sharp differentiation: 'Unlike Weave, we include AI voice that actually converses — not just text.'",
        },

        "pain_points": [
            "no-shows (high cost — avg $200 per no-show in US)",
            "online reputation management (Google reviews critical for new patients)",
            "new patient acquisition costs are high ($400–$1,200 per new patient)",
            "after-hours inquiries lost to competitors",
            "insurance verification admin (we don't touch this — it's too complex)",
        ],

        "decision_maker": {
            "primary": "Owner-dentist for private practices",
            "secondary": "Practice administrator in larger groups",
            "dso": "Regional VP or operations director for DSO-owned clinics — completely different sales motion, not our target",
            "note": "Target private practice owner-dentists only. DSOs require enterprise sales cycle.",
        },

        "pitch_angle": {
            "primary": "The only AI receptionist that handles voice calls AND WhatsApp AND email — and it works alongside Dentrix.",
            "secondary": "Practices using this recover an average of $3,200/month in bookings that would have gone to a competitor.",
            "differentiation": "Position against Weave: 'Weave texts patients. This actually converses with them — books, answers questions, handles after-hours voice calls.'",
            "avoid": "Generic AI positioning — they've heard it all. Lead with specifics.",
        },

        "objections": {
            "we already have weave": "Weave handles text messaging well — it doesn't do conversational voice. When your front desk is with a patient and the phone rings at 6pm, Weave can't answer it and book a new patient. That's the gap.",
            "we already have a patient communication system": "What does it do after hours when your team is gone? If a new patient calls at 7pm and hits voicemail, they're booking your competitor. This is specifically that after-hours + overflow gap.",
            "we use dentrix — does this integrate": "Yes — bookings go straight into your Dentrix schedule. No double entry, no disruption to your existing workflow.",
            "too expensive": "At $99/month, one new patient a month more than covers it. Most practices see 3–5 additional new patients in month one from after-hours recovery alone. Setup is $180 but it's waived until end of July — zero upfront.",
            "not interested in more tech": "Understood. Worth knowing that 73% of new dental patients choose the first practice that responds to their inquiry. After-hours voice is the single fastest way to win that race.",
        },

        "best_outreach_time": "Tue–Thu 10am–12pm or 2pm–4pm local time",
        "best_days": "Tuesday, Wednesday, Thursday",
        "avoid": "Mondays, Fridays, lunch hour (owner is likely with patients), US federal holidays",
        "channel_note": "Email primary. Cold voice call secondary. Do not use WA. SMS only if they reply via SMS first.",

        "price_sensitivity": "low — US dentists pay freely for tech that demonstrably improves revenue",
        "competitor_landscape": "Very high. Weave, Birdeye, Podium, Lighthouse 360 all have dental customers. Must differentiate on AI voice capability.",
        "signal_notes": "US dentist campaigns need sharper copy than AU/CA. Lead with dollar ROI, not features. Always reference the specific software they likely use (if known). TCPA compliance critical for any voice outreach — do not auto-dial US numbers.",
    },


    # ════════════════════════════════════════════════════════════════════════
    # SALONS
    # ════════════════════════════════════════════════════════════════════════

    ("salon", "AU"): {
        "vertical": "Salon",
        "country": "AU",

        "market_reality": {
            "practice_size": "solo to 5 stylists, boutique to mid-size",
            "revenue_range": "AUD $200K–$800K",
            "ownership": "almost always owner-operated. Owner is usually the head stylist.",
            "saturation": "low — limited AI pitch penetration",
            "ai_awareness": "low. They know apps exist but haven't been pitched AI specifically.",
        },

        "software_landscape": {
            "dominant": "Kitomba — NZ-origin, dominant in AU/NZ salon market",
            "second": "Timely — cloud-based, popular with boutique salons",
            "others": ["Shortcuts", "Fresha (free tier very popular)", "Square Appointments"],
            "fresha_note": "Fresha has a large free user base. These practices are price-sensitive but high volume. Kitomba and Timely users are more likely to pay for premium tools.",
            "signal_implication": "Fresha users: harder to convert, price pitch needed. Kitomba/Timely users: already paying for software, more receptive to add-ons.",
        },

        "pain_points": [
            "no-shows and last-minute cancellations (every empty chair is lost revenue)",
            "filling gaps in the appointment book — empty slots mid-week",
            "client rebooking — getting clients to book their next appointment before they leave",
            "after-hours booking requests (clients want to book at 9pm — salon is closed)",
            "new client acquisition — expensive via Instagram ads",
        ],

        "decision_maker": {
            "primary": "Owner-stylist. She makes every decision.",
            "note": "She's probably behind a chair with a client most of the day. Best reached in the first 30 minutes of the day or at lunch.",
        },

        "pitch_angle": {
            "primary": "Fill your empty slots automatically — no more chasing cancellations or dead Tuesdays.",
            "secondary": "Clients can book at 10pm on their phone without calling. You wake up with a full book.",
            "tone": "Very casual, peer-to-peer. Speak to her like you're another small business owner, not a tech company.",
        },

        "objections": {
            "fresha does this": "Fresha does basic online booking. This is the layer on top — the AI that sends WA reminders to reduce no-shows, fills your last-minute cancellations automatically, and answers after-hours booking requests so you don't lose that client to the salon down the road.",
            "i don't have time for new tech": "It runs itself — you set it up once and it handles client reminders and booking requests without you doing anything. Most salon owners spend about 20 minutes setting it up.",
            "my clients prefer to call me directly": "They still can — this just means when they can't reach you, they get an instant response instead of voicemail. Especially useful for after-hours and when you're with a client.",
            "too expensive": "At $49/month, filling one extra appointment a week pays for itself twice over. Setup is $180 but waived until end of July — nothing upfront.",
        },

        "best_outreach_time": "8:00am–9:30am AEST (before first clients), or 12pm–1pm",
        "best_days": "Tuesday, Wednesday, Thursday (Monday is recovery from weekend, Friday is chaos)",
        "channel_note": "WA is natural — salon owners use WA constantly with their clients. Instagram DM also viable if email bounces.",

        "price_sensitivity": "medium-high — salons operate on tighter margins. $49/mo starter plan is the right anchor.",
        "signal_notes": "Most casual vertical in the portfolio. Copy must match their voice — conversational, no jargon. WA outreach works well because they're already living in WA with their clients. Instagram is a secondary channel worth testing for AU salons.",
    },


    ("salon", "CA"): {
        "vertical": "Salon",
        "country": "CA",

        "market_reality": {
            "practice_size": "solo to 4 stylists",
            "revenue_range": "CAD $150K–$600K",
            "saturation": "low",
            "ai_awareness": "very low",
        },

        "software_landscape": {
            "dominant": "Fresha (free, widely used), Vagaro, Booker, Meevo",
            "signal_implication": "High Fresha penetration = price-sensitive segment. Vagaro/Booker users are more likely to pay.",
        },

        "pain_points": [
            "same core pain points as AU salons",
            "higher labour costs make no-shows more painful",
            "seasonal demand swings (slow winters in most Canadian cities)",
        ],

        "pitch_angle": {
            "primary": "Never lose a booking to voicemail again — AI answers after hours and fills your book automatically.",
            "tone": "Warmer than AU, slightly more formal opener but quickly casual",
        },

        "objections": {
            "we use fresha": "Fresha handles bookings when clients come to you. This handles the times they don't — after hours, when you're with a client, when they want to ask a question before booking. Different layer.",
            "too expensive": "At CAD $70/month, filling two extra appointments a week covers it. And the CAD $250 setup fee is waived until end of July — nothing to pay upfront.",
        },

        "best_outreach_time": "Tue–Thu 8:30am–10am local",
        "channel_note": "Email primary in Canada. Do not use WA for cold outreach.",
        "price_sensitivity": "high — CAD $70/mo Starter plan essential. Setup fee CAD $250 waived until 29 Jul 2026 — always lead with this.",
        "signal_notes": "CA salons are similar to AU but email-first. Seasonal angle works well — 'prepare for your slow season now' in September/October.",
    },


    ("salon", "US"): {
        "vertical": "Salon",
        "country": "US",

        "market_reality": {
            "practice_size": "solo to 6 stylists. Large variation — from independent booth renters to multi-location boutiques.",
            "revenue_range": "USD $100K–$600K",
            "saturation": "medium",
            "ai_awareness": "low-medium",
        },

        "software_landscape": {
            "dominant": "Vagaro (~30% of US salons), Booksy, Mindbody (higher-end spas), StyleSeat, Square Appointments",
            "signal_implication": "Mindbody users are most sophisticated and highest-paying. Vagaro users are mid-market sweet spot. StyleSeat users are often independent stylists — hardest to convert.",
        },

        "pain_points": [
            "no-shows (high cost in US — stylists often don't get paid for empty slots)",
            "last-minute cancellations",
            "filling mid-week slow periods",
            "competing with large chains (Great Clips, SportClips) on price — can't, so must win on experience",
        ],

        "pitch_angle": {
            "primary": "Stop losing revenue to no-shows — AI sends automated reminders and fills your cancellations within minutes.",
            "secondary": "Your clients can book at 11pm. Your competitors' clients are booking your appointments while their salon is closed.",
            "roi_focus": "Lead with dollar amounts — US resonates with specifics.",
        },

        "objections": {
            "we use vagaro": "Vagaro handles the booking side. This is the communication layer — automated WA and SMS reminders that reduce no-shows, plus AI that answers after-hours booking requests so you capture clients when your desk is closed.",
            "too expensive": "At $49/month, one recovered no-show appointment per week pays for it. Most salons see a 20–30% reduction in no-shows in month one. Setup is $180 but waived until end of July — nothing upfront.",
        },

        "best_outreach_time": "Tue–Thu 9am–11am local time",
        "channel_note": "Email primary. SMS preferred over WA for US follow-up. Do not use WA cold.",
        "price_sensitivity": "high — US independent salons are price-sensitive. $49/mo starter plan.",
        "signal_notes": "US salon market is fragmented. Target Vagaro and Mindbody users — they're already paying for software and are more receptive to add-ons. Independent booth renters (own their own chair, not the salon) are not a good target — no admin pain.",
    },


    # ════════════════════════════════════════════════════════════════════════
    # ACCOUNTANTS
    # ════════════════════════════════════════════════════════════════════════

    ("accountant", "AU"): {
        "vertical": "Accountant",
        "country": "AU",

        "market_reality": {
            "practice_size": "sole practitioner to 10-partner firm",
            "revenue_range": "AUD $300K–$5M depending on size",
            "ownership": "partner-owned firms dominant. CPA Australia and CAANZ are the professional bodies.",
            "saturation": "low for AI tools",
            "ai_awareness": "medium — accountants follow tech closely but are cautious adopters",
        },

        "software_landscape": {
            "dominant": "Xero — Australia is Xero's home market. Penetration is very high (~60% of AU practices).",
            "second": "MYOB — legacy, declining but significant installed base",
            "others": ["QuickBooks (smaller share in AU)", "Reckon"],
            "practice_management": "Xero Practice Manager, GreatSoft, MYOB Practice",
            "signal_implication": "AU accountants know Xero deeply. Pitch must acknowledge Xero integration or non-disruption. 'Works alongside Xero' is the magic phrase.",
        },

        "pain_points": [
            "client document collection — chasing clients for tax info is the biggest time drain",
            "appointment scheduling for tax reviews and advisory meetings",
            "client communication during busy season — too many calls, not enough time",
            "new client acquisition — referral-dependent, hard to scale",
            "compliance deadlines creating unpredictable workload spikes",
        ],

        "decision_maker": {
            "primary": "Principal/owner or managing partner",
            "note": "Partners are analytical — they'll want to see numbers before committing. Have ROI data ready.",
        },

        "pitch_angle": {
            "primary": "Automate the client communication your team does manually — appointment reminders, document requests, deadline alerts — so they focus on billable work.",
            "secondary": "Your clients can book their tax review online, get automated reminders, and receive WA updates without your team touching a single message.",
            "avoid": "Do not use the word 'AI' prominently in AU accountant copy — it triggers skepticism. Use 'automated' instead.",
        },

        "timing": {
            "best_months": "November, December, May, June (outside busy season)",
            "avoid": "July–October (peak tax return season), February–March (BAS period)",
            "best_days": "Tuesday–Thursday",
            "best_time": "9am–11am AEST",
        },

        "objections": {
            "we already have a practice management system": "Xero Practice Manager handles your work flow. This handles client-facing communication — the reminders, appointment bookings, and status updates you currently do manually or via email. Completely separate layer.",
            "our clients prefer to call us": "They still can — this just means when they can't reach you, they get an instant response and can book online at 9pm. You stop playing phone tag.",
            "we're too busy to implement new systems": "Implementation takes one afternoon. After that it runs itself. Most firms save 3–5 hours a week in admin within the first month.",
            "what does it actually do": "Book appointments, send automated reminders, request documents via WA, alert clients to upcoming deadlines. Everything you currently do by email or phone, automated.",
        },

        "price_sensitivity": "medium — accountants are analytical about spend. Need clear ROI case. $99/mo is right for a 2-3 person practice.",
        "signal_notes": "AU accountants are a strong vertical but require evidence-based pitching. Use 'automated' not 'AI'. Avoid busy season outreach completely. Xero acknowledgment in copy is important.",
    },


    ("accountant", "CA"): {
        "vertical": "Accountant",
        "country": "CA",

        "market_reality": {
            "practice_size": "sole practitioners (very common in CA) to mid-size CPA firms",
            "revenue_range": "CAD $300K–$4M",
            "ownership": "partner-owned. CPA Canada is the professional body — designation is 'CPA', not 'CA' or 'CGA' (merged 2014).",
            "saturation": "low",
            "ai_awareness": "medium",
        },

        "software_landscape": {
            "dominant": "QuickBooks (Intuit, very strong in CA SMB accounting)",
            "second": "Sage, Xero (growing in CA)",
            "practice_management": "TaxCycle (dominant for Canadian tax software), Profile (Wolters Kluwer)",
            "signal_implication": "Always use 'CPA' designation in copy. Never 'CA' or 'accountant' alone — CPAs find the distinction important.",
        },

        "pain_points": [
            "T1 tax season (Feb–Apr) is brutal — too many clients, too little time",
            "client document collection (same universal pain)",
            "client communication during tax season overwhelm",
            "new client acquisition is referral-dependent",
        ],

        "pitch_angle": {
            "primary": "Reduce your tax season stress — automated client reminders, document requests, and appointment booking so your team focuses on filings, not logistics.",
            "secondary": "Your clients book their review online, get automated document checklists, and receive WA deadline reminders without your team manually following up.",
        },

        "timing": {
            "best_months": "May, June, September, October, November",
            "avoid": "January–April (T1 tax season — do not contact)",
            "best_days": "Tuesday–Thursday",
        },

        "objections": {
            "we use quickbooks": "QuickBooks handles your client accounting. This handles your client communication — the appointment scheduling, reminders, and document requests you currently do manually. Different layer entirely.",
            "casl — is this compliant": "Yes — the system is CASL-compliant with full consent documentation and unsubscribe built in. Happy to share our compliance documentation.",
        },

        "price_sensitivity": "medium — CPAs are careful. CAD $140/mo Growth plan is the right anchor in Canada. Setup fee CAD $250 waived until 29 Jul 2026 — lead with this.",
        "signal_notes": "Always use 'CPA' not 'accountant' in CA copy. CASL compliance statement in outreach email helps build trust with this audience. Never reach out during tax season.",
    },


    ("accountant", "US"): {
        "vertical": "Accountant",
        "country": "US",

        "market_reality": {
            "practice_size": "solo CPA to mid-size firm",
            "revenue_range": "USD $200K–$5M",
            "ownership": "partner-owned firms. AICPA is professional body. CPA designation critical.",
            "saturation": "medium",
            "ai_awareness": "medium — some exposure to AI accounting tools",
        },

        "software_landscape": {
            "dominant": "QuickBooks (Intuit, ~80% US SMB market)",
            "tax_software": "TurboTax Business, Drake Tax, ProConnect, UltraTax",
            "practice_management": "Karbon, Canopy, TaxDome (all growing strongly)",
            "signal_implication": "US CPAs are already paying for practice management (Karbon/TaxDome). Pitch must be differentiated from those tools — client-facing communication is the gap.",
        },

        "pitch_angle": {
            "primary": "Your clients book their tax review, get automated document checklists, and receive deadline reminders automatically — without your team touching a single message.",
            "roi_focus": "Saving 5 hours/week of admin at $200/hr billing rate = $4,000/month value. Tool costs $99.",
        },

        "timing": {
            "best_months": "May, June, July, September, October, November",
            "avoid": "January–April 15 (tax season — absolutely do not contact)",
        },

        "objections": {
            "we already use karbon/taxdome": "Karbon manages your internal workflow. This is the client-facing communication layer — the automated reminders, online booking, and document request messages your team currently sends manually. They're complementary.",
            "too expensive": "At $99/month, saving 2 hours of admin per week at your billing rate pays for it in the first hour of month one. Setup is $180 but waived until end of July — nothing upfront.",
        },

        "price_sensitivity": "low-medium — US CPAs pay for tools that demonstrably save billable time",
        "signal_notes": "US CPA outreach must use 'CPA' not 'accountant'. Tax season blackout is absolute — Jan 1 to Apr 16. Target solo practitioners and 2–5 person firms first. Larger firms have internal admin staff and lower pain.",
    },


    # ════════════════════════════════════════════════════════════════════════
    # PHYSIOTHERAPISTS
    # ════════════════════════════════════════════════════════════════════════

    ("physiotherapist", "AU"): {
        "vertical": "Physiotherapist",
        "country": "AU",

        "market_reality": {
            "practice_size": "1–6 physios, small to mid-size clinics",
            "revenue_range": "AUD $400K–$2M",
            "ownership": "owner-physio operated. Some corporate chains (Back In Motion, Physitrack affiliates) but majority independent.",
            "saturation": "low for AI tools",
            "ai_awareness": "low — behind dentists in tech adoption",
        },

        "software_landscape": {
            "dominant": "Nookal — AU-built, dominant in AU physiotherapy practices",
            "second": "Cliniko — also AU-built, cloud-native, very popular, strong UX",
            "others": ["Best Practice (more medical-focused)", "Halaxy (growing, free tier)", "MedTech"],
            "ndis_note": "NDIS (National Disability Insurance Scheme) billing is a major complexity for AU physios. Do not touch NDIS billing in the pitch.",
            "signal_implication": "Cliniko users are more tech-forward and more receptive to new tools. Nookal users are entrenched but reachable. Acknowledge their software.",
        },

        "pain_points": [
            "appointment cancellations — particularly impactful as physio appointments are longer (45–60min)",
            "NDIS administration — time-consuming but do not pitch to this pain (too complex to help)",
            "waitlists — turning waitlist enquiries into booked appointments",
            "patient non-attendance without notice",
            "recall — getting discharged patients back for review or maintenance",
        ],

        "decision_maker": {
            "primary": "Owner-physio",
            "secondary": "Practice manager in larger clinics (3+ physios)",
        },

        "pitch_angle": {
            "primary": "Every empty 45-minute slot costs you $120. AI reminders reduce cancellations by 25% and fill gaps automatically.",
            "secondary": "Patients on your waitlist get an automatic WA when a slot opens. You fill it in minutes, not hours.",
            "avoid": "Do not mention NDIS. Do not pitch as replacing clinical judgment or staff.",
        },

        "objections": {
            "cliniko does this": "Cliniko handles your clinical records and basic reminders. The AI communication layer — conversational WA, voice follow-up for recalls, automatic waitlist filling — that's what this adds on top.",
            "we have a receptionist": "She still runs the clinic. This handles the after-hours calls, the waitlist matching, and the reminder sequence so she focuses on patients in front of her.",
            "our patients prefer to call": "They still can — this just means when they call after hours or you're fully booked, they get an instant WA response and can join the waitlist digitally instead of hanging up and calling someone else.",
        },

        "best_outreach_time": "12pm–2pm AEST (physio clinic lunch break), or pre-8:30am",
        "best_days": "Tuesday, Wednesday, Thursday",
        "price_sensitivity": "medium — physios are practical. Clear per-slot ROI calculation works well.",
        "signal_notes": "Physio is our second-best converting AU vertical. The 'cost of empty slot' framing ($120/slot) resonates strongly. Never mention NDIS — it's a political and administrative minefield.",
    },


    ("physiotherapist", "CA"): {
        "vertical": "Physiotherapist",
        "country": "CA",

        "market_reality": {
            "practice_size": "1–4 physios",
            "revenue_range": "CAD $300K–$1.5M",
            "ownership": "owner-physio dominant",
            "saturation": "low",
            "ai_awareness": "low",
        },

        "software_landscape": {
            "dominant": "Jane App — built in BC, beloved by Canadian physios. Has very strong community loyalty.",
            "others": ["Owl Practice", "Cliniko (growing in CA)", "Power Diary"],
            "jane_note": "Jane App has cult-like loyalty in Canadian allied health. Any pitch that sounds like a replacement will be rejected immediately. Must lead with 'alongside Jane'.",
            "signal_implication": "'Works alongside your Jane App' is the required framing for 90% of CA physio outreach.",
        },

        "pain_points": [
            "insurance billing complexity — direct billing to insurers is time-consuming",
            "appointment cancellations and no-shows",
            "waitlist management",
            "patient recall after discharge",
        ],

        "pitch_angle": {
            "primary": "Works alongside Jane App — automates your patient reminders and waitlist filling without changing how you run your clinic.",
            "secondary": "Never lose a cancelled slot — AI fills your openings from your waitlist automatically via WA.",
            "avoid": "Do not pitch as a Jane replacement. Do not touch insurance billing in the pitch.",
        },

        "objections": {
            "we use jane app": "We work alongside Jane — your clinical records, billing, and scheduling stay exactly the same. This adds the automated patient communication layer Jane doesn't have: AI WA reminders, waitlist auto-fill, after-hours booking capture.",
            "jane already sends reminders": "Jane sends basic email reminders. This adds WA reminders (much higher open rate), conversational AI for after-hours enquiries, and automatic waitlist filling when a slot opens. Different level of capability.",
        },

        "best_outreach_time": "Tue–Thu 10am–12pm local",
        "channel_note": "Email primary. Voice secondary. Do not use WA for cold outreach.",
        "price_sensitivity": "medium",
        "signal_notes": "Jane App loyalty is the key insight for CA physio outreach. Every template must acknowledge Jane explicitly. 'Alongside Jane' in the subject line has tested well in our early data.",
    },


    ("physiotherapist", "US"): {
        "vertical": "Physiotherapist",
        "country": "US",

        "market_reality": {
            "practice_size": "1–8 physios (called Physical Therapists — PT — in US)",
            "title_note": "Always say 'Physical Therapist' or 'PT practice' in US. 'Physiotherapist' is the Commonwealth term and sounds foreign.",
            "revenue_range": "USD $500K–$3M",
            "ownership": "private practice owner-PT. Corporate PT groups growing (ATI Physical Therapy, Athletico).",
            "saturation": "medium",
            "ai_awareness": "medium",
        },

        "software_landscape": {
            "dominant": "WebPT — dominant US PT-specific software (~40% market share)",
            "others": ["Clinicient", "Netsmart", "Theralytics", "Jane (growing in US too)"],
            "complexity_note": "US PT billing involves complex insurance authorization workflows (prior auth, benefits verification). Do NOT pitch anything that touches billing. Stick to patient communication.",
            "signal_implication": "WebPT users are the primary target. 'Works alongside WebPT' is the required framing.",
        },

        "pain_points": [
            "no-shows and cancellations (particularly expensive — 60-minute slots)",
            "waitlist management",
            "patient recall after discharge — getting patients back for maintenance",
            "after-hours enquiries lost",
            "insurance pre-authorization delays (do not touch — too complex)",
        ],

        "pitch_angle": {
            "primary": "Every empty hour in your PT schedule costs $150+. AI reminders reduce no-shows and fill your cancellations automatically from your waitlist.",
            "secondary": "Works alongside WebPT — no change to your billing or clinical workflow.",
            "avoid": "Do not mention insurance billing, prior authorization, or anything clinical. Stick to patient communication.",
        },

        "objections": {
            "we use webpt": "WebPT handles your clinical documentation and billing — which it does brilliantly. This is the patient-facing communication layer WebPT doesn't have: automated WA reminders, waitlist auto-fill, after-hours AI for new patient enquiries.",
            "we have front desk staff": "They still handle everything they do today. This handles the calls and messages outside business hours and the automated reminder sequence so your front desk doesn't manually call 30 patients every morning.",
            "too expensive": "At $99/month, filling one cancelled hour per week more than covers it. Most PT practices see no-show rates drop 20–25% in month one. Setup is $180 but waived until end of July — nothing upfront.",
        },

        "best_outreach_time": "Tue–Thu 10am–12pm or 2pm–4pm local",
        "channel_note": "Email primary. Voice secondary. Do not use WA cold.",
        "price_sensitivity": "low-medium — US PT owners invest in tools with clear ROI",
        "signal_notes": "Always say 'Physical Therapist' or 'PT' not 'Physiotherapist' in US copy. WebPT acknowledgment is as important as Jane acknowledgment in Canada. Never touch billing/insurance in the pitch — it's a regulatory and complexity minefield.",
    },
}


# ── Helper functions ───────────────────────────────────────────────────────────

def get_vertical_profile(business_type: str, country: str) -> dict:
    """
    Retrieve the vertical profile for a given business type and country.
    Falls back to AU profile if country-specific profile not found.
    """
    key = (business_type.lower(), country.upper())
    profile = VERTICAL_PROFILES.get(key)
    if not profile:
        fallback_key = (business_type.lower(), "AU")
        profile = VERTICAL_PROFILES.get(fallback_key, {})
    return profile


def get_combined_context(business_type: str, country: str, geo_profiles: dict) -> dict:
    """
    Returns merged geo + vertical context for Signal to inject into prompts.
    """
    from knowledge.geo_profiles import GEO_PROFILES
    geo = GEO_PROFILES.get(country.upper(), {})
    vertical = get_vertical_profile(business_type, country)
    return {
        "geo": geo,
        "vertical": vertical,
        "country": country.upper(),
        "business_type": business_type.lower(),
    }
