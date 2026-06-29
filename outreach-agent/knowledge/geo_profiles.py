"""
Geo Profiles — Signal Agent seed intelligence
Country-level communication preferences, channel rankings, regulatory constraints.

Sources:
  - Hofstede Insights (hofstede-insights.com) — cultural dimension scores
  - Twilio State of Customer Engagement (2024)
  - Meta WhatsApp Business Global Report (2024)
  - HubSpot State of Marketing (2025)
  - Edelman Trust Barometer (2025)
  - ACMA, CRTC, FTC regulatory publications

Scope: PracticeDesk markets — AU, CA, US
       IN included as planned expansion (Vobiz wired, campaign not yet live)

Update cadence: Signal web research job refreshes these monthly.
Last seeded: June 2026 by Claude.
"""

GEO_PROFILES = {

    # ── AUSTRALIA ─────────────────────────────────────────────────────────────
    "AU": {
        "country": "Australia",
        "currency": "AUD",
        "language": "English",

        # Hofstede dimensions (0-100)
        "hofstede": {
            "individualism": 90,       # Very high — appeal to personal gain, not community
            "power_distance": 36,      # Low — no titles needed, first names immediately
            "uncertainty_avoidance": 51, # Medium — open to new things but want proof
            "indulgence": 71,          # High — aspirational language works well
        },

        # Channel preference (1 = most preferred for cold B2B outreach)
        "channel_rank": {
            "voice": 1,     # Cold calls accepted and effective in AU B2B
            "email": 2,     # Strong for professional services
            "wa": 3,        # ~79% smartphone adoption, growing for B2B
            "sms": 4,       # Still used but declining vs WA
        },

        "cold_call_receptivity": "high",
        # Australians are notably more receptive to cold B2B calls than US/CA.
        # Direct, no-nonsense opener. Don't apologise for calling.

        "tone": {
            "style": "direct, casual, egalitarian",
            "opener": "first name immediately — never Mr/Ms unless they use it first",
            "jargon": "none — plain English always",
            "length": "short — get to the point within 2 sentences",
            "avoid": [
                "overly formal language",
                "American spelling (use 'organisation' not 'organization')",
                "overselling or superlatives ('amazing', 'revolutionary')",
                "corporate buzzwords",
                "tall poppy triggers — don't imply they're behind competitors",
            ],
        },

        "trust_signals": [
            "local suburb or city references ('dentists in Melbourne', 'clinics in Bondi')",
            "specific dollar amounts rather than percentages",
            "named Australian client references if available",
            "practical outcome statements ('saves 3 hours a week') not feature lists",
        ],

        "optimal_contact_windows": {
            "email": "Tue–Thu 8:30am–10:30am AEST",
            "voice": "Tue–Thu 9:00am–11:30am AEST, or 1:30pm–3:30pm AEST",
            "wa": "same as email",
            "avoid": "Monday mornings, Friday afternoons, school holiday periods",
        },

        "regulatory": {
            "email": {
                "law": "Australian Spam Act 2003",
                "consent": "implied consent acceptable for business emails (published address or business context)",
                "unsubscribe": "functional unsubscribe mechanism required, honoured within 5 business days",
                "penalty": "up to AUD $2.2M per violation",
            },
            "voice": {
                "law": "Do Not Call Register Act 2006",
                "register": "DNCR — check before dialling consumer numbers. B2B numbers not registered.",
                "hours": "8am–9pm weekdays, 9am–5pm Saturdays. No Sundays.",
                "penalty": "up to AUD $250,000 per violation",
            },
            "wa": {
                "law": "Spam Act applies — treat as marketing message",
                "consent": "implied consent acceptable for business context",
            },
            "privacy": "Privacy Act 1988 — Australian Privacy Principles govern data handling",
        },

        "business_calendar": {
            "tax_year": "1 July – 30 June",
            "busy_periods": {
                "accountants": "Jul–Oct (tax returns), Feb–Mar (BAS)",
                "dentists": "Jan (back to school) and school term starts",
                "salons": "pre-Christmas (Nov–Dec), pre-school year",
                "physiotherapists": "Jan–Feb (sports season start)",
            },
            "quiet_periods": "late December – mid January (summer holidays, many businesses close)",
            "public_holidays": "Note state-based holidays vary (Melbourne Cup in VIC, etc.)",
        },

        "time_zones": {
            "AEST": "UTC+10 (NSW, VIC, QLD, ACT, TAS)",
            "AEDT": "UTC+11 (NSW, VIC, ACT, TAS — daylight saving Oct–Apr)",
            "ACST": "UTC+9:30 (SA, NT)",
            "AWST": "UTC+8 (WA — no daylight saving)",
            "note": "Perth is 2–3 hours behind Sydney. Always resolve to local time before scheduling Sophie calls.",
        },

        "competitor_awareness": "low-medium",
        "market_maturity": "early adopter phase for AI practice tools — first-mover framing works",
        "signal_notes": "AU is the strongest market for WA outreach. Voice calls have highest connect rate. Australians respond to brevity and directness. Avoid anything that sounds like a US sales script.",
    },


    # ── CANADA ────────────────────────────────────────────────────────────────
    "CA": {
        "country": "Canada",
        "currency": "CAD",
        "language": "English (French in Quebec — treat as separate sub-profile)",

        "hofstede": {
            "individualism": 80,
            "power_distance": 39,
            "uncertainty_avoidance": 48,
            "indulgence": 36,          # Low — restrained, less aspirational language. ROI over aspiration.
        },

        "channel_rank": {
            "email": 1,     # Dominant B2B channel in Canada
            "voice": 2,     # Accepted but lower receptivity than AU — formal tone required
            "sms": 3,       # Used but declining
            "wa": 4,        # Very low B2B adoption — ~28% have WA, most don't use for business
        },

        # CRITICAL: Do not use WA as primary channel for CA cold outreach.
        # Many Canadian business owners do not have WA installed on their work phone.
        "wa_warning": "WA adoption in Canadian B2B is very low. Use email first, voice second. WA only after prospect has engaged.",

        "cold_call_receptivity": "medium",
        # Canadians are polite but more reserved than Australians.
        # Give them an easy out early — reduces resistance and paradoxically improves conversion.
        # Formal opener, then warm quickly.

        "tone": {
            "style": "professional but approachable, low-pressure",
            "opener": "acknowledge it's a cold call and give an easy out within first 10 seconds",
            "jargon": "minimal — plain English",
            "length": "medium — slightly more context than AU before the ask",
            "avoid": [
                "aggressive follow-up cadence",
                "American cultural references",
                "price-first pitches",
                "high-pressure close language",
                "ignoring Quebec French speakers in any Quebec campaign",
            ],
        },

        "trust_signals": [
            "Canadian client references ('a physio clinic in Mississauga')",
            "professional credentials and certifications",
            "data privacy reassurance (Canadians are privacy-conscious post-CASL)",
            "clear unsubscribe option visible — signals you're legitimate",
            "bilingual capability flag for any Quebec outreach",
        ],

        "optimal_contact_windows": {
            "email": "Tue–Thu 9:00am–11:00am local time",
            "voice": "Tue–Thu 10:00am–12:00pm local time",
            "wa": "do not use for cold outreach",
            "avoid": "Mondays, Fridays, stat holidays (very numerous in Canada)",
        },

        "regulatory": {
            "email": {
                "law": "CASL — Canada's Anti-Spam Legislation",
                "consent_types": {
                    "express": "explicit opt-in — safest",
                    "implied": "business card given, email published on website, prior business relationship within 2 years, membership in same professional organisation",
                },
                "required_elements": [
                    "sender identification (legal name, mailing address)",
                    "functional unsubscribe mechanism",
                    "unsubscribe honoured within 10 business days",
                ],
                "penalty": "up to CAD $10M per violation — one of the strictest laws globally",
                "signal_rule": "Always log consent basis before sending. For cold email to Canadian addresses, use 'published business email' as implied consent basis. Never email personal addresses.",
            },
            "voice": {
                "law": "National Do Not Call List (DNCL) — CRTC",
                "exemptions": "B2B calls to registered business numbers are generally exempt",
                "hours": "8am–9:30pm local time weekdays, 9am–6pm weekends",
            },
            "wa": {
                "law": "CASL applies to electronic messages including WA",
                "note": "Same consent rules apply. Low adoption makes this a moot point for cold outreach.",
            },
            "privacy": "PIPEDA — Personal Information Protection and Electronic Documents Act",
        },

        "business_calendar": {
            "tax_year": "calendar year (Jan–Dec)",
            "busy_periods": {
                "accountants": "Feb–Apr (T1 personal tax), varies for corporate",
                "dentists": "Sep–Nov (back to school dental checks)",
                "salons": "Dec, May–Jun (weddings)",
                "physiotherapists": "Jan–Feb (new year resolutions, winter sports injuries)",
            },
            "quiet_periods": "late Jul–Aug (summer holidays), between Christmas and New Year",
            "stat_holidays": "More than AU — check provincial holidays (Quebec has distinct set)",
        },

        "time_zones": {
            "EST": "UTC-5 (Ontario, Quebec, most of eastern Canada)",
            "EDT": "UTC-4 (daylight saving Mar–Nov)",
            "CST": "UTC-6 (Manitoba, Saskatchewan)",
            "MST": "UTC-7 (Alberta)",
            "PST": "UTC-8 (BC)",
            "note": "Canada spans 6 time zones. Always resolve city to zone before scheduling.",
        },

        "competitor_awareness": "low-medium",
        "market_maturity": "early adopter — less saturated than US, more conservative than AU",
        "signal_notes": "Canada is email-first, voice-second. Never lead with WA. CASL compliance is non-negotiable — Signal must flag any Canadian campaign that lacks documented consent basis. Quebec requires French — do not send English-only copy to Quebec postal codes.",
    },


    # ── UNITED STATES ─────────────────────────────────────────────────────────
    "US": {
        "country": "United States",
        "currency": "USD",
        "language": "English",

        "hofstede": {
            "individualism": 91,       # Highest globally — personal ROI message above all
            "power_distance": 40,
            "uncertainty_avoidance": 46, # Low — Americans try new things quickly
            "indulgence": 68,          # High — aspirational language works
        },

        "channel_rank": {
            "email": 1,     # Dominant B2B channel
            "voice": 2,     # Cold calling culture very strong in US B2B
            "sms": 3,       # SMS preferred over WA for B2B
            "wa": 4,        # Very low adoption (~25%) — treated as personal app, not business
        },

        "wa_warning": "WA adoption in US B2B is very low. Americans use SMS for informal business comms. WA is perceived as a foreign/personal app. Do not use for cold outreach.",

        "cold_call_receptivity": "high",
        # US has the most mature cold calling culture. Decision makers are used to it.
        # Get to value proposition in 15 seconds or they hang up.
        # ROI-first, no relationship preamble.

        "tone": {
            "style": "direct, confident, ROI-first, transactional",
            "opener": "value proposition in first sentence — no small talk",
            "jargon": "some tech/business jargon acceptable ('streamline', 'automate', 'scale')",
            "length": "very short — Americans respect brevity. One clear ask.",
            "avoid": [
                "lengthy relationship-building preamble",
                "anything that sounds apologetic",
                "pricing without ROI context",
                "passive voice",
                "British/Australian spelling variants",
            ],
        },

        "trust_signals": [
            "specific dollar ROI figures ('practices using this recover $3,200/month in missed bookings')",
            "named recognisable clients if possible",
            "social proof numbers ('400+ practices')",
            "testimonial quotes with first name and city",
            "BBB accreditation or professional association membership",
        ],

        "optimal_contact_windows": {
            "email": "Tue–Thu 9:00am–11:00am local time",
            "voice": "Tue–Thu 10:00am–12:00pm or 2:00pm–4:00pm local time",
            "wa": "do not use for cold outreach",
            "avoid": "Monday mornings, Friday afternoons, US federal holidays",
        },

        "regulatory": {
            "email": {
                "law": "CAN-SPAM Act",
                "consent": "opt-out based — no prior consent required for commercial email",
                "required_elements": [
                    "accurate From and Reply-To",
                    "honest subject line",
                    "physical postal address of sender",
                    "functional unsubscribe honoured within 10 business days",
                ],
                "penalty": "up to $51,744 per email in violation",
                "state_laws": "California CCPA — if prospect is in CA, additional data rights apply. Do not ignore.",
            },
            "voice": {
                "law": "TCPA — Telephone Consumer Protection Act",
                "critical": "TCPA is extremely strict for auto-dialled calls. Sophie must not use predictive/auto-dialler mode for US consumer numbers. Manual dial or single-line auto-dial to business numbers is safer.",
                "hours": "8am–9pm local time",
                "do_not_call": "National DNC list — check before dialling consumer numbers. B2B is largely exempt.",
            },
            "sms": {
                "law": "TCPA also covers SMS — express consent required for marketing SMS",
                "note": "Do not send marketing SMS to US numbers without prior opt-in",
            },
            "wa": "CAN-SPAM interpretation extends to commercial WA messages. Low adoption makes this low risk.",
            "privacy": "No federal privacy law. CCPA (California) is most significant state law.",
        },

        "business_calendar": {
            "tax_year": "calendar year (Jan–Dec). Fiscal year varies by company.",
            "busy_periods": {
                "accountants": "Jan–Apr 15 (tax season — do not reach out)",
                "dentists": "Sep–Nov (back to school, insurance year-end pushes)",
                "salons": "Nov–Dec (holidays), May–Jun (wedding season)",
                "physiotherapists": "Jan–Mar (new year resolutions, winter sports)",
            },
            "quiet_periods": "Thanksgiving week (late Nov), Christmas–New Year",
            "federal_holidays": "11 per year — check before scheduling campaigns",
        },

        "time_zones": {
            "EST": "UTC-5 (NY, FL, most of east coast)",
            "EDT": "UTC-4 (daylight saving Mar–Nov)",
            "CST": "UTC-6 (TX, IL, most of midwest)",
            "MST": "UTC-7 (CO, AZ — Arizona does not observe daylight saving)",
            "PST": "UTC-8 (CA, WA, OR)",
            "note": "US spans 4 primary zones. Always resolve city before scheduling Sophie calls. California is PST — 3 hours behind New York.",
        },

        "competitor_awareness": "very high",
        "market_maturity": "saturated — practice management and AI tools well established. Pitch must differentiate sharply.",
        "signal_notes": "US is the most competitive market. Dentists and physios already have multiple AI tools pitched to them monthly. Generic outreach fails. Signal must ensure US campaigns lead with sharp differentiation, specific ROI numbers, and reference the prospect's likely existing software. Email is primary — voice is secondary but effective if short and ROI-first.",
    },


    # ── INDIA (planned expansion — Vobiz wired) ───────────────────────────────
    "IN": {
        "country": "India",
        "currency": "INR",
        "language": "English (Hindi and regional languages for tier-2 cities)",
        "status": "planned — Vobiz wired, campaign not yet live for PracticeDesk",

        "hofstede": {
            "individualism": 48,
            "power_distance": 77,      # High — use professional titles, respect hierarchy
            "uncertainty_avoidance": 40,
            "indulgence": 26,          # Very low — pragmatic, not aspirational. Practical value over aspiration.
        },

        "channel_rank": {
            "wa": 1,        # WhatsApp IS the business channel in India. 487M users.
            "voice": 2,     # Cold calling accepted and high volume
            "email": 3,     # Used but WA gets faster response
            "sms": 4,
        },

        "cold_call_receptivity": "high",
        "tone": {
            "style": "respectful, relationship-oriented, formal opener then warm",
            "opener": "use professional titles (Dr., CA, Sir/Ma'am) in first contact",
            "jargon": "minimal — clear practical language",
            "length": "medium — relationship preamble before the pitch is expected",
            "avoid": [
                "skipping the relationship-building phase",
                "aggressive pricing as opener",
                "ignoring titles and hierarchy",
                "purely transactional tone on first contact",
            ],
        },

        "regulatory": {
            "voice": {
                "law": "TRAI DND — Telecom Regulatory Authority of India",
                "hours": "9am–9pm only. No calls outside this window.",
                "dnd_check": "Commercial calls to DND numbers prohibited. B2B numbers generally exempt but verify.",
            },
            "wa": "No specific WA regulation. Follow TRAI guidelines for commercial messaging.",
            "email": "No equivalent to CASL/CAN-SPAM. Professional norms apply.",
            "privacy": "Digital Personal Data Protection Act 2023 — coming into effect. Monitor.",
        },

        "signal_notes": "India campaign not yet active for PracticeDesk. When launched: WA is primary, voice is secondary. Relationship-first copy. Price sensitivity is high — price point must be adjusted for Indian market.",
    },
}
