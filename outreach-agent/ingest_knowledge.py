"""
ingest_knowledge.py -- one-time (and re-runnable) ingestion script.

Reads source documentation from:
  - C:/Projects/Practice desk/docs/       (PracticeDesk)
  - D:/lawaid/LawAidN/Beta3/documentation/ (LegalAidAI)

Extracts text from .md and .html files, strips boilerplate, and writes
structured knowledge files to outreach-agent/knowledge/.

Run from outreach-agent/:
    python ingest_knowledge.py
"""

import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

PRACTICEDESK_DOCS  = Path(r"C:\Projects\Practice desk\docs")
LEGALAIDAI_DOCS    = Path(r"D:\lawaid\LawAidN\Beta3\documentation")
KNOWLEDGE_DIR      = Path(__file__).parent / "knowledge"


# ── HTML stripping ─────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, char in [
        ("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
        ("&#39;", "'"), ("&quot;", '"'), ("&mdash;", "—"), ("&ndash;", "–"),
        ("&bull;", "•"), ("&middot;", "·"),
    ]:
        text = text.replace(entity, char)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".html":
        return strip_html(raw)
    return raw


def write_knowledge(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    kb = KNOWLEDGE_DIR
    rel = path.relative_to(kb)
    print(f"  OK  {rel}  ({len(content):,} chars)")


# ── PracticeDesk ───────────────────────────────────────────────────────────────

PRACTICEDESK_SALON_FILES = [
    PRACTICEDESK_DOCS / "guides" / "salon-guide-detailed.html",
    PRACTICEDESK_DOCS / "guides" / "salon-guide-short.html",
    PRACTICEDESK_DOCS / "guides" / "salon-guide-detailed-india.html",
    PRACTICEDESK_DOCS / "guides" / "salon-guide-short-india.html",
]

PRACTICEDESK_MEDICAL_FILES = [
    PRACTICEDESK_DOCS / "guides" / "medical-guide-detailed.html",
    PRACTICEDESK_DOCS / "guides" / "medical-guide-short.html",
    PRACTICEDESK_DOCS / "guides" / "medical-guide-detailed-india.html",
    PRACTICEDESK_DOCS / "guides" / "medical-guide-short-india.html",
    PRACTICEDESK_DOCS / "guides" / "admin-setup-guide.html",
]

PRACTICEDESK_OVERVIEW_FILES = [
    PRACTICEDESK_DOCS / "guides" / "workflow-diagrams.html",
]


def ingest_practicedesk() -> None:
    print("\n-- PracticeDesk")

    def _combine(files: list[Path], label: str) -> str:
        parts = []
        for f in files:
            if f.exists():
                parts.append(f"## Source: {f.name}\n\n{read_file(f)}")
            else:
                print(f"  ⚠  not found: {f}")
        if not parts:
            return f"# {label}\n\n(no source files found)\n"
        header = f"# PracticeDesk — {label}\n\n"
        return header + "\n\n---\n\n".join(parts)

    write_knowledge(
        KNOWLEDGE_DIR / "practicedesk" / "salon.md",
        _combine(PRACTICEDESK_SALON_FILES, "Salon Vertical"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "practicedesk" / "medical.md",
        _combine(PRACTICEDESK_MEDICAL_FILES, "Medical / Dental / Physio Vertical"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "practicedesk" / "overview.md",
        _combine(PRACTICEDESK_OVERVIEW_FILES, "Platform Overview"),
    )


# ── LegalAidAI ─────────────────────────────────────────────────────────────────

D = LEGALAIDAI_DOCS


LEGALAIDAI_OVERVIEW_FILES = [
    D / "MASTER-PROJECT-REFERENCE.md",
    D / "MARKETING-PLAN.md",
    D / "beta3_project_overview.md",
    D / "PROMO-REFERENCE.md",
]

LEGALAIDAI_ADVOCATE_FILES = [
    D / "advocate_panel_features.md",
    D / "advocate_use_cases.md",
    D / "advocate_quick_reference_guide.md",
    D / "NOTEBOOKLM-ADVOCATE-SCRIPT.md",
    D / "OUTREACH-WORKFLOW.md",
]

LEGALAIDAI_CORPORATE_FILES = [
    D / "corporate-law-guide.md",
    D / "corporate-compliance-coverage.md",
    D / "notebooklm-corporate-demo-prompt.md",
    D / "corporate-inhouse-pending.md",
]

LEGALAIDAI_CITIZEN_FILES = [
    D / "CITIZEN-USER-GUIDE.md",
    D / "COMPLETE-FEATURE-GUIDE.md",
]

LEGALAIDAI_VOICE_WA_FILES = [
    D / "voice-agent-plan.md",
    D / "voice-hotline-plan.md",
    D / "WHATSAPP-BROADCAST-WORKFLOW.md",
    D / "WHATSAPP-CHATBOT-GUIDE.md",
    D / "voice-agent-setup.md",
]


def ingest_legalaidai() -> None:
    print("\n-- LegalAidAI / Nyaya Saathi")

    def _combine(files: list[Path], label: str) -> str:
        parts = []
        for f in files:
            if f.exists():
                content = read_file(f)
                parts.append(f"## Source: {f.name}\n\n{content}")
            else:
                print(f"  ⚠  not found: {f}")
        if not parts:
            return f"# {label}\n\n(no source files found)\n"
        header = f"# LegalAidAI — {label}\n\n"
        return header + "\n\n---\n\n".join(parts)

    write_knowledge(
        KNOWLEDGE_DIR / "legalaidai" / "overview.md",
        _combine(LEGALAIDAI_OVERVIEW_FILES, "Product Overview & Marketing"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "legalaidai" / "advocate.md",
        _combine(LEGALAIDAI_ADVOCATE_FILES, "Advocate Module"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "legalaidai" / "corporate.md",
        _combine(LEGALAIDAI_CORPORATE_FILES, "Corporate / In-house Module"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "legalaidai" / "citizen.md",
        _combine(LEGALAIDAI_CITIZEN_FILES, "Citizen Module"),
    )
    write_knowledge(
        KNOWLEDGE_DIR / "legalaidai" / "voice_wa.md",
        _combine(LEGALAIDAI_VOICE_WA_FILES, "Voice & WhatsApp Channels"),
    )


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ingesting knowledge base...")
    ingest_practicedesk()
    ingest_legalaidai()
    print("\nDone. Knowledge files written to:", KNOWLEDGE_DIR)
