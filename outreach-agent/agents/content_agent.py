"""
Content Agent — Agent 8.

Generates all outbound content for PracticeDesk and LegalAidAI:
  - WhatsApp broadcast templates (Meta-approved format)
  - Email subject + HTML body
  - Voice guidance (Aria opener, insight, pain question, objection handlers)
  - Social media posts (LinkedIn, Instagram)
  - Blog outlines (SEO-structured, keyword-targeted)
  - Blog posts (full long-form HTML articles, 1200–2000 words)

Usage:
    from agents.content_agent import generate_content, ContentRequest

    result = generate_content(ContentRequest(
        product="practicedesk",
        module="dentist",
        content_type="blog_outline",
        market="AU",
        seo_keyword="reduce dental no-shows",
    ))
    print(result.content)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
import anthropic

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Modules that belong to each product
PRODUCT_MODULES = {
    "practicedesk": ["dentist", "doctor", "salon", "physiotherapist", "accountant", "lawyer"],
    "legalaidai":   ["advocate", "corporate", "citizen", "cause_list"],
}

# Which knowledge files to load per product/module
_KNOWLEDGE_MAP: dict[str, list[str]] = {
    # PracticeDesk — medical verticals share one source file
    "practicedesk:dentist":        ["brand/practicedesk-brief.md", "practicedesk/overview.md", "practicedesk/medical.md"],
    "practicedesk:doctor":         ["brand/practicedesk-brief.md", "practicedesk/overview.md", "practicedesk/medical.md"],
    "practicedesk:physiotherapist":["brand/practicedesk-brief.md", "practicedesk/overview.md", "practicedesk/medical.md"],
    "practicedesk:salon":          ["brand/practicedesk-brief.md", "practicedesk/overview.md", "practicedesk/salon.md"],
    "practicedesk:accountant":     ["brand/practicedesk-brief.md", "practicedesk/overview.md"],
    "practicedesk:lawyer":         ["brand/practicedesk-brief.md", "practicedesk/overview.md"],
    # LegalAidAI
    "legalaidai:advocate":         ["brand/legalaidai-brief.md", "legalaidai/overview.md", "legalaidai/advocate.md", "legalaidai/voice_wa.md"],
    "legalaidai:corporate":        ["brand/legalaidai-brief.md", "legalaidai/overview.md", "legalaidai/corporate.md"],
    "legalaidai:citizen":          ["brand/legalaidai-brief.md", "legalaidai/overview.md", "legalaidai/citizen.md"],
    "legalaidai:cause_list":       ["brand/legalaidai-brief.md", "legalaidai/cause_list.md"],
}

_SYSTEM_PROMPT = """\
You are the Content Agent for Apex — an internal AI agent that generates outreach and marketing \
content for two SaaS products:

1. PracticeDesk — AI front-office assistant for practices (AU, US, CA, India)
2. LegalAidAI / Nyaya Saathi — AI legal platform for India (3 modules: Advocate, Corporate, Citizen)

Your output is used directly in production outbound campaigns. Quality rules:

ACCURACY
- Only use product features, statistics, and claims present in the knowledge base provided.
- Never invent case names, court citations, or pricing.
- Never hallucinate feature capabilities.

BRAND RULES (from brand brief — these override everything)
- Follow the approved positioning, rejected framings, and tone rules in the brand brief exactly.
- For PracticeDesk: NEVER describe it as a "WhatsApp AI assistant". It is an "AI office assistant \
across phone, WhatsApp, and email — 24/7".
- For LegalAidAI: NEVER describe it as "ChatGPT for lawyers". It is purpose-built for Indian law.

FORMAT RULES BY CONTENT TYPE
- wa_template: Return the full Meta template body text using {{1}} and {{2}} variable syntax, \
WhatsApp markdown (*bold*, _italic_, bullet •). Include all 3 components: \
HEADER note, BODY text, BUTTONS list. Do NOT include emoji unless brief explicitly requests it.
- email: Return a JSON object with keys: "subject_a", "subject_b", "html_body". \
HTML body uses inline styles only (no <style> blocks).
- voice_guidance: Return sections: opener (1–2 sentences), insight (2–3 sentences), \
pain_question (1 sentence), objection_handlers (3–5 common objections with responses).
- social_post: Return the post text ready to copy-paste. For LinkedIn include a hook line. \
For Instagram include suggested hashtags.
- affiliate_dm: Return exactly 3 Instagram DM variations labelled A, B, C. Each is 60–80 words max. \
Tone guide — A: curiosity hook (no product name in opening line, ends with a question); \
B: peer-to-peer honest (acknowledge it's a programme outreach, keep it direct and respectful); \
C: audience-led (open with the value of their audience, why the programme suits an influencer). \
Include legalaidai.in/affiliates in each DM. Commission: ₹500 on subscription + ₹500 on renewal. \
Mark personalisation slots as [Name] and [specific detail from their account]. \
Never use: "revolutionary", "game-changing", emojis, corporate buzzwords. \
Use specific product features from the knowledge base — do not be generic.
- blog_outline: Return a structured SEO plan using this exact format:
  TITLE: [60 chars max, keyword-first, benefit-led]
  META_DESCRIPTION: [150–160 chars, includes primary keyword and a clear reason to click]
  PRIMARY_KEYWORD: [the single term this article targets — think what a {module} owner Googles]
  SECONDARY_KEYWORDS: [3–5 related terms, comma-separated]
  TARGET_READER: [one sentence — who this is for and what stage of awareness]
  FUNNEL_STAGE: [top / mid / bottom]
  RECOMMENDED_WORD_COUNT: [800–1200 for listicle, 1500–2500 for guide, 2000–3000 for comparison]
  INTERNAL_CTA: [URL and CTA copy to link to at the end — e.g. practicedesk.live free trial]
  OUTLINE:
  H1: [exact H1 — same as TITLE or slight variation]
  INTRO: [2 sentences describing the hook and what the reader will learn]
  H2: [section heading]
    H3: [subsection if needed] — [one line on what this covers]
  H2: [next section]
    ...
  CONCLUSION: [what the article wraps up with and the CTA placement]
- blog_post: Return a complete, publication-ready blog article in clean HTML. Rules:
  Use semantic tags: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <strong>, <em>.
  Inline styles only (no <style> blocks — email-client safe).
  Include <!-- PRIMARY_KEYWORD: ... --> and <!-- META_DESCRIPTION: ... --> comments at the top.
  Word count: 1200–2000 words for standard articles, 2000–3000 for pillar guides.
  Use the seo_keyword naturally in H1, first paragraph, one H2, and conclusion.
  Include 2–3 internal links to the product site (use the URL from the knowledge base).
  End with a CTA section: free trial or demo link, no hard-sell language.
  Do NOT use the word "revolutionary", "game-changing", "seamless", or "leverage" anywhere.
  Statistics and claims must come only from the knowledge base — never invent numbers.

HINDI CONTENT
- Use natural Hinglish for WhatsApp (mix of Hindi Devanagari + English terms is correct and preferred).
- Legal terms in English are acceptable within Hindi sentences.
- Formal Hindi is wrong — use conversational register.

OUTPUT
- Return only the content itself, cleanly formatted.
- Do not add preamble like "Here is your template:" or closing remarks.
- Do not add implementation notes unless brief explicitly asks for them.
"""


@dataclass
class ContentRequest:
    product: str        # "practicedesk" | "legalaidai"
    module: str         # e.g. "dentist", "salon", "advocate", "corporate", "citizen"
    content_type: str   # "wa_template" | "email" | "voice_guidance" | "social_post" | "blog_outline" | "blog_post"
    tone: str = "structured"   # "structured" | "pain_first" | "outcome_first" | "conversational"
    market: str = "AU"         # "AU" | "US" | "CA" | "IN"
    language: str = "en"       # "en" | "hi"
    platform: str = ""         # for social_post: "linkedin" | "instagram"
    brief: str = ""            # any additional founder instructions
    signal_feedback: str = ""  # performance context piped in from Signal via VP Marketing
    seo_keyword: str = ""      # primary SEO keyword for blog_outline / blog_post


@dataclass
class ContentResult:
    content: str
    product: str
    module: str
    content_type: str
    tone: str
    market: str
    language: str
    input_tokens: int = 0
    output_tokens: int = 0


def _load_knowledge(product: str, module: str) -> str:
    key = f"{product}:{module}"
    files = _KNOWLEDGE_MAP.get(key, [f"brand/{product}-brief.md"])
    parts = []
    for fname in files:
        fpath = KNOWLEDGE_DIR / fname
        if fpath.exists():
            parts.append(f"=== {fname} ===\n\n{fpath.read_text(encoding='utf-8')}")
        else:
            parts.append(f"=== {fname} === [FILE NOT FOUND — run ingest_knowledge.py]")
    return "\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(parts)


def _build_prompt(req: ContentRequest) -> str:
    knowledge = _load_knowledge(req.product, req.module)

    platform_note    = f"\nPlatform: {req.platform}" if req.platform else ""
    seo_note         = f"\nSEO Keyword: {req.seo_keyword}" if req.seo_keyword else ""
    brief_section    = f"\n\n## Additional Brief\n{req.brief}" if req.brief else ""
    signal_section   = f"\n\n## Signal Performance Context (from VP Marketing)\n{req.signal_feedback}" if req.signal_feedback else ""

    return f"""\
# Content Request

Product:      {req.product}
Module:       {req.module}
Content type: {req.content_type}{platform_note}{seo_note}
Tone:         {req.tone}
Market:       {req.market}
Language:     {req.language}{brief_section}{signal_section}

## Knowledge Base
{knowledge}

---

Generate the {req.content_type} now for the {req.module} vertical ({req.product}), \
{req.tone} tone, {req.market} market, {req.language} language.
Follow all brand rules from the brief above. If Signal performance context is provided, \
use it to improve on what has underperformed — address the identified weakness in tone, \
hook, or pain-point framing. Output the content only.\
"""


def generate_content(req: ContentRequest) -> ContentResult:
    """Call Claude to generate content for the given request."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(req)}],
    )

    return ContentResult(
        content=message.content[0].text.strip(),
        product=req.product,
        module=req.module,
        content_type=req.content_type,
        tone=req.tone,
        market=req.market,
        language=req.language,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )


def generate_full_vertical(product: str, module: str) -> dict[str, ContentResult]:
    """
    Generate the full content suite for one vertical in one call-per-type.
    Returns a dict keyed by content_type.
    """
    base = ContentRequest(product=product, module=module)
    results = {}

    for ct in ["wa_template", "email", "voice_guidance"]:
        req = ContentRequest(
            product=product,
            module=module,
            content_type=ct,
            tone="structured",
            market="AU" if product == "practicedesk" else "IN",
            language="en",
        )
        results[ct] = generate_content(req)

    return results
