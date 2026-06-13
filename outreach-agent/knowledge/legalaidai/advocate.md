# LegalAidAI — Advocate Module

## Source: advocate_panel_features.md

# Nyaya Saathi — Advocate Panel: Features & Functionalities

> App: https://www.legalaidai.in/advocate  
> Tier: Pro (Licensed Advocates)  
> Last updated: 2026-04-19

---

## 1. Dashboard

- Active case counter, monthly draft stats, AI query usage tracker
- Quick action buttons: New Case, Research, Draft Document, Verify Citations
- Recent cases panel (last 5–10 cases)
- Pro Mode badge

---

## 2. Research Studio (AI Legal Research)

- AI chat powered by **Claude Sonnet** (research-grade model)
- Pre-loaded quick chips: Bail Application, Anticipatory Bail, Res Judicata, Stress-Test Draft
- **Document attachment** — upload PDF / TXT / DOC / DOCX for in-context research
- **Voice dictation** — microphone button for hands-free input
- **Reference Gallery** (right panel) — auto-extracts case citations with:
  - Case name, court, year, page number
  - Direct links to Indian Kanoon judgment pages
  - Copy-to-clipboard citation formatting
- **Indian Kanoon URL import** — paste a judgment URL to auto-fetch full text
- Streaming chat responses, conversation memory across queries
- Clear chat button, remaining query count display

---

## 3. Draft Documents

### Available Templates (7)

**Litigation Documents**

| # | Template | Governing Provision |
|---|----------|---------------------|
| 1 | Bail Application | S.437/439 CrPC / S.483 BNSS |
| 2 | Civil Plaint | Order VII Rule 1 CPC |
| 3 | Written Statement (Defense Reply) | Order VIII CPC |
| 4 | Interlocutory Application (Interim Relief) | Order XXXIX / S.151 CPC |
| 5 | Criminal Complaint | S.200 CrPC / S.223 BNSS |

**Professional Correspondence**

| # | Template | Governing Provision |
|---|----------|---------------------|
| 6 | Legal Opinion Letter | — |
| 7 | Vakalatnama (Power of Attorney) | Order III Rule 4 CPC / S.32 Advocates Act |

### Draft Generation Features

- AI-powered form-to-document generation (fill fields → complete court-ready draft)
- Indian Kanoon precedent search integrated while drafting
- Real-time document preview
- Copy to clipboard (one click)
- Print / PDF export
- Save generated draft to case file
- Template guide panel (right sidebar help text per template)

---

## 4. My Cases (Case Management)

### Case Creation

- Title, case type, court/forum, opposite party, initial notes
- Case types: Criminal Bail/Trial, Civil Suit/Execution, Writ, Consumer, Family Court, Arbitration, Other
- File upload on creation (PDF / TXT)

### Case Detail View

- Case header: title, type, court, status badge
- **Quick actions:** Add Note, Research (auto-populated), Generate Brief, Draft from Facts
- **Notes accordion** — timestamped timeline of hearing updates and case notes
- **Drafts accordion** — generated drafts specific to this case
- Case status dropdown (Active / Closed / Pending)

### Notes Features

- Voice-dictated notes (speech-to-text)
- File attachments (PDF / TXT) per note
- Chronological timeline view

### Cloud Sync

- Primary storage: browser localStorage (offline-capable)
- **Firestore cloud sync** — multi-device access
- Google Drive sync (UI ready)
- OneDrive sync (UI ready)
- Storage preference modal (choose local-only, Google Drive, or OneDrive)

---

## 5. Case Briefs (Judgment Summarization)

**Input methods:**
- Paste judgment text directly
- Upload PDF / TXT file
- Paste Indian Kanoon judgment URL

**AI-generated brief includes:**
- Case name and citation
- Brief facts
- Legal issues framed
- Arguments (both sides)
- Ratio Decidendi (reasoning / holding)
- Final decision / outcome

**Output options:**
- Read Aloud (text-to-speech playback)
- Save to case file
- Copy to clipboard

---

## 6. Verify Citations

- Paste any draft, document, or citation list
- AI scans all citations and marks each as:
  - **VERIFY** — specific case citations needing volume/page confirmation
  - **OK** — well-known statutes and sections
  - **WARNING** — incomplete or potentially incorrect citations
- Flags hallucinated or fabricated citations before filing
- Reminder to verify independently on SCC Online / Indian Kanoon

---

## 7. Calendar & Hearings

- Upcoming hearings count cards (today / this week)
- Create events with: title, date, time, related case (dropdown), description
- Events sorted chronologically, linked to specific cases

---

## 8. Settings & Profile

### Account

- Display name, plan tier (Pro), AI queries used, queries remaining

### Data Storage

- Local Device Only (browser, offline)
- Google Drive sync (own app folder)
- OneDrive sync (own folder)
- Storage status and sync confirmation

### Privacy

- Confidentiality notice: conversations processed and discarded, not stored on Nyaya Saathi servers

### Other

- Sign out button

---

## 9. Special & Cross-cutting Features

### AI Capabilities

- **Auto mode detection** — switches between:
  - Research Mode (legal analysis, precedent finding)
  - Strategy / Stress-Test Mode (opposing counsel analysis)
  - Drafting Mode (document generation)
- **BNS / BNSS mapping** — old CrPC/IPC sections mapped to new codes
- **4,000 token limit** per response (vs 800 for citizen tier)
- Citation tagging with `[REF:]` markers for post-generation verification

### Document Processing

- PDF text extraction — up to 30 pages / 25,000 characters (client-side)
- Supported formats: PDF, TXT, DOC, DOCX
- Attachments included in AI research context

### Voice & Accessibility

- Voice dictation (webkitSpeechRecognition) across Research, Cases, Briefs panels
- Text-to-speech playback for Case Briefs
- Interim results display during dictation

### PWA & Mobile

- Installable as Progressive Web App (desktop and mobile)
- Offline support via service worker caching
- Mobile responsive layout (sidebar collapses on small screens)
- Mobile back-button navigation in list/detail views
- Responsive grid breakpoints: 1200px, 900px

### Theme & Localisation

- Dark / Light theme toggle with persistence
- India date format (DD Mon YYYY, en-IN locale)

### Sidebar — External Resource Links

- eCourts Portal (ecourts.gov.in)
- Indian Kanoon (indiankanoon.org)
- Supreme Court Portal (sci.gov.in)

---

## 10. Authentication & Plan Management

### Authentication

- Firebase email/password login
- Pro plan gate — verifies plan before granting advocate access
- Bearer token authorization for all API calls

### Subscriptions (Razorpay)

| Plan | Price |
|------|-------|
| Monthly | ₹2,499 / month |
| Yearly | ₹24,999 / year |

### Usage Tracking

- AI query counter (increments per API call)
- Plan limit enforcement
- Fair-use ceiling: 500 queries / month
- Usage statistics visible on Settings page

---

## Summary

| Category | Count |
|----------|-------|
| Main panels | 8 |
| Document templates | 7 |
| AI features | 6 |
| Case management features | 5 |
| Voice / accessibility features | 3 |
| Cloud sync options | 3 |
| External integrations | 3 (Indian Kanoon, Firebase, Claude API) |
| Mobile / PWA features | 5 |
| **Total distinct features** | **40+** |


---

## Source: advocate_use_cases.md

# 📚 Nyaya Saathi Pro: Exhaustive Use Case Guide for Advocates

This guide provides a comprehensive list of scenarios where licensed advocates can leverage the **Nyaya Saathi Pro** (Advocate Studio) to enhance their practice, speed up drafting, and deepen legal research.

---

## 1. 🏛️ Civil Law Use Cases
Civil practice involves heavy documentation and procedural compliance under the CPC.

### 📝 Use Case: Money Recovery Suit
- **Goal:** Draft a plaint for unpaid dues or loan defaults.
- **Workflow:** Use the **Civil Plaint** template in the Drafts panel.
- **Instruction:** Fill in the plaintiff/defendant details and the "Facts of the Case." The AI generates a structured draft under Order VII Rule 1 CPC with valuation and prayer clauses.

### 🏠 Use Case: Property & Specific Performance
- **Goal:** Draft a suit for possession or specific performance of a contract.
- **Workflow:** Use the **Research Studio** to find latest SC precedents on SRA 1963, then use the **Civil Plaint** template.

### ⏸️ Use Case: Interim Relief (IAs)
- **Goal:** Obtain a stay order or temporary injunction.
- **Workflow:** Use the **Interlocutory Application** template.
- **Instruction:** Specify the grounds for "Irreparable Harm" and "Balance of Convenience." The AI drafts the application under Order XXXIX Rules 1 & 2 CPC.

### 🛡️ Use Case: Written Statement (Defense)
- **Goal:** Respond to a civil suit as a defendant.
- **Workflow:** Use the **Written Statement** template.
- **Instruction:** Paste the plaintiff's plaint into the AI Chat to generate a "Para-wise Reply" and preliminary objections (limitation, jurisdiction).

---

## 2. ⚖️ Criminal Law Use Cases
Criminal practice requires speed and precise grounding in the BNSS (formerly CrPC) and BNS (formerly IPC).

### 🔓 Use Case: Regular & Anticipatory Bail
- **Goal:** Secure release for a client.
- **Workflow:** Use the **Bail Application** template.
- **Instruction:** Input FIR details and sections charged. The AI drafts a petition under S.437/439 CrPC or S.482 BNSS with grounds like "no prior record" or "willingness to furnish surety."

### 💸 Use Case: Negotiable Instruments Act (S.138)
- **Goal:** File a case for cheque bounce.
- **Workflow:** Use the **Research Studio** for notice drafting.
- **Instruction:** Prompt: "Draft a legal notice for cheque bounce under S.138 NI Act based on these facts: [Bank Return Memo Details]."

### 🔬 Use Case: FIR Analysis & Quashing
- **Goal:** Challenge a false or meritless FIR.
- **Workflow:** Upload the FIR to the **Research Studio**.
- **Instruction:** Prompt: "Analyze this FIR. Are the ingredients of the alleged offences met? Draft a petition for quashing under S.482 CrPC/BNSS."

---

## 3. 💼 Corporate & Commercial Use Cases
Corporate lawyers use the app for risk assessment and high-level legal opinions.

### 📜 Use Case: Contract Review
- **Goal:** Identify risky clauses in a service agreement or NDA.
- **Workflow:** Upload the contract PDF to the **Research Studio**.
- **Instruction:** Prompt: "Identify the top 5 high-risk clauses in this contract for the service provider, specifically looking at indemnity and termination."

### 💼 Use Case: Professional Legal Opinions
- **Goal:** Provide a client with a formal assessment of a legal situation.
- **Workflow:** Use the **Legal Opinion Letter** template.
- **Instruction:** Input the "Facts" and "Question of Law." The AI generates a structured memo with ratio decidendi and recommended actions.

### 🏗️ Use Case: RERA & IBC Compliance
- **Goal:** Advising on real estate or insolvency matters.
- **Workflow:** Use **Research Studio** (Sonnet Engine).
- **Instruction:** Prompt: "Explain the effect of a Section 14 IBC moratorium on pending RERA execution proceedings with latest SC rulings."

---

## 4. 📑 General Practice & "Chamber" Tasks
Daily efficiency tools for every advocate.

### 📖 Use Case: Judgment Summarization
- **Goal:** Quickly digest a lengthy court ruling.
- **Workflow:** Use the **Case Briefs** panel.
- **Instruction:** Paste the judgment text or upload the PDF. The AI extracts facts, issues, arguments, and the ratio into a 1-page brief.

### 🔍 Use Case: Citation Verification
- **Goal:** Ensure no "hallucinations" in the final filing.
- **Workflow:** Use the **Verify Citations** panel.
- **Instruction:** Paste your finalized draft. The AI flags citations that need volume/page number confirmation on SCC Online/Manupatra.

### 🎙️ Use Case: Voice Case Management
- **Goal:** Record updates while traveling or in court.
- **Workflow:** Use the **My Cases** panel -> **Add Note** -> **Microphone**.
- **Instruction:** Dictate hearing outcomes. The AI saves the text to the cloud-synced case timeline.

---

## Summary of Practice Benefits
- **Speed:** Drafting time reduced from 3 hours to 10 minutes.
- **Depth:** Access to research-grade AI (Claude Sonnet) for complex legal queries.
- **Mobility:** Cloud-synced cases available on mobile in court and laptop in chambers.
- **Accuracy:** Dedicated tools for verifying citations and stress-testing arguments.

> [!IMPORTANT]
> **Verify All Citations:** While Nyaya Saathi Pro is an advanced legal assistant, all AI-generated content requires the professional review of a licensed advocate before filing.


---

## Source: advocate_quick_reference_guide.md

# 🏛️ Nyaya Saathi Pro: Advocate Quick Reference Guide

Welcome to **Nyaya Saathi Pro**, your AI-powered workspace calibrated specifically for licensed Indian Advocates. 

This guide outlines a highly efficient, sequential workflow designed to seamlessly integrate into your day-to-day practice—from your morning case reviews all the way to complex drafting and client communication.

---

## 🌅 Step 1: Morning Briefing & Case Triage
*Start your day by organizing your priorities and reviewing active litigation.*

1. **Access the Dashboard:** Log in to the Advocate Panel to view your centralized Case Dashboard.
2. **Review Active Matters:** Check your active cases, upcoming hearing dates, and pending deadlines.
3. **Prioritize & Plan:** Identify which cases require immediate drafting, deep research, or client updates today.

---

## 📂 Step 2: Client Intake & Document Analysis
*Use AI to quickly digest new client files and unstructured evidence.*

1. **Create a Case File:** Add a new matter to your dashboard, entering basic details (Client Name, Opposing Party, Court, Case Type).
2. **Upload Documents:** Upload raw client documents—FIRs, legal notices, contracts, or unstructured evidence.
3. **AI Fact Extraction:** 
   - Open the **AI Chat** and attach the newly uploaded document.
   - Ask the AI to *“Summarize the key facts, dates, and legal issues from this document.”*
   - Save the AI’s summary as a foundational "Fact Sheet" in your case file for quick review later.

---

## 🔍 Step 3: Deep Legal Research (Research Studio)
*Leverage our premium Research-Grade AI to build your courtroom strategy.*

1. **Enter the Research Studio:** Switch the AI Chat into **Research Mode**. This mode utilizes our most advanced reasoning model (Claude 3.5 Sonnet) specifically calibrated for Indian Advocates.
2. **Query for Precedents:** 
   - Prompt the AI with your specific legal scenario. 
   - *Example:* "What are the latest Supreme Court guidelines on anticipatory bail in economic offences under the BNSS?"
3. **Extract Citations & Statutes:** The AI will provide relevant citations (SC/HC decisions) and exact sections from applicable Acts (BNS, IPC, BNSS, CrPC, BSA, CPC, etc.).
4. **Save to Gallery:** Save critical arguments, case laws, and strategies generated by the AI to your **Reference Gallery** to use later while drafting.
   > ⚠️ **Critical Practice Standard:** Always verify AI-provided citations against official databases (SCC Online, Manupatra, Indian Kanoon) before citing them in court.

---

## 📝 Step 4: Drafting & Memo Generation
*Transition from research to actively building your legal submissions.*

1. **Drafting Prompts:** Use the AI Chat to generate structural drafts based on your saved research or fact sheets.
   - *Example:* "Draft a Legal Notice under Section 138 of the NI Act based on the fact sheet I provided earlier."
   - *Example:* "Draft the grounds for a Writ Petition challenging the arbitrary freezing of a bank account."
2. **Review & Refine:** Copy the AI-generated draft into your text editor. The AI provides a rigorous, legally-sound foundation, allowing you to focus purely on polishing the specific nuances and formatting required by your local court.
3. **Formatting Instructions:** Instruct the AI to structure the output using proper headers, numbered paragraphs, and prayer clauses for effortless copy-pasting.

---

## 👥 Step 5: Client Communication
*Bridge the gap between complex legal jargon and client understanding.*

1. **Translate Strategy to Plain Language:** Legal strategy can be overwhelming for clients. Use the AI to convert your legal petition or case strategy into an easy-to-understand summary.
2. **Draft Client Updates:** 
   - Ask the AI: *"Draft a polite email/WhatsApp message to my client updating them on today's hearing where we filed for an injunction. Explain what it means for them in simple terms."*

---

## 🌙 Step 6: End-of-Day File Management
*Wrap up your day by securing your work.*

1. **Update Case Status:** Mark completed tasks and update the current status of your active cases on the dashboard.
2. **Export:** Export any finalized drafts to PDF or Word for subsequent physical printing, client signatures, or digital e-filing.
3. *[Coming Soon]* **Cloud Sync:** Sync your generated memos, fact sheets, and documents to Google Drive or Microsoft OneDrive for secure, long-term cloud backup.

---

### 💡 Pro-Tips for Maximizing the AI Chat
- **Context Carry-Over:** The AI remembers the context of your current conversation. You can ask follow-up questions like, *"Can you find a contrary judgment to the one you just cited?"* without re-explaining the whole case.
- **Be Jurisdiction Specific:** The more context you provide the AI regarding the specific High Court or tribunal, the better the localized research output.
- **File Attachments:** Always attach the specific document you are questioning rather than typing out long clauses manually to save time.


---

## Source: NOTEBOOKLM-ADVOCATE-SCRIPT.md

# Nyaya Saathi Pro — Advocate Studio: NotebookLM Audio Demo Script
**Format:** Two-speaker conversational podcast  
**Speakers:** Arjun (host — practising advocate, 8 years, district + sessions court) + Kavya (co-host — legal tech journalist)  
**Duration:** ~28–32 minutes at natural speaking pace  
**Audience:** Practising advocates, junior lawyers, law firm partners evaluating AI tools  
**URL:** legalaidai.in/advocate | Pro: ₹2,499/month  
**Version:** April 2026 — reflects all features including WhatsApp, 44 templates, OCR, eCourts, and auto-sync  

---

## OPENING

**Kavya:** Arjun, you've been practising for eight years — district court, sessions court, some High Court work. Let me ask you something direct. When does your actual working day end?

**Arjun:** Honest answer? Usually around midnight. Sometimes later. Not because of court work — because of drafting. A bail application, a written statement, an IA. Each one is two to three hours if you're doing it properly.

**Kavya:** And that's after a full day in court.

**Arjun:** Five hearings, travel, client calls — and then you come home and draft. Junior advocates work even longer because they don't have the templates built up yet. It's genuinely unsustainable, and almost nobody talks about it because it's just considered normal.

**Kavya:** Which is why we're here. Today we're doing a complete walkthrough of Nyaya Saathi Pro — the Advocate Studio at legalaidai.in/advocate. This is a purpose-built AI tool for Indian advocates. And I want to go deep — every panel, every feature, including some things that were added very recently, including the ability to access this entire system through WhatsApp.

**Arjun:** That last one changed how I use it in court. We'll get there. Let's start from login.

---

## SEGMENT 1 — LOGIN AND DASHBOARD

**Kavya:** You go to legalaidai.in/advocate. Firebase login — email and password. What's the first thing you see after logging in?

**Arjun:** The Dashboard. And the first thing you'll notice after logging in — if you've set up Google Drive or OneDrive sync — is that your cases automatically load. There's no manual sync button. On login, the app pulls your latest case data from the cloud and shows you a status banner at the top.

> **[SCREENSHOT: My Cases panel just after login — gold status banner reads "Syncing from Google Drive…" with a spinner; transitions to green "Synced — 14 cases loaded" which fades after 3 seconds]**

**Kavya:** So you never have to think about whether your phone and laptop are in sync.

**Arjun:** It just happens. And if there's a problem — say your Drive token has expired — you get a red banner with a Reconnect link. It doesn't silently fail. You always know the sync state.

**Kavya:** What else is on the Dashboard?

> **[SCREENSHOT: Advocate Studio Dashboard — dark navy, gold "Pro" badge top right, four stat cards: Active Cases, Drafts This Month, AI Queries Used, Queries Remaining; quick action row: New Case, Research, Draft Document, Verify Citations; Recent Cases list below showing last 5 matters]**

**Arjun:** Four stat cards — active case count, drafts generated this month, AI queries used, and queries remaining. The fair-use ceiling is five hundred queries a month, which is sixteen to seventeen a working day. More than enough. The quick action row — New Case, Research, Draft Document, Verify Citations — maps to the four core workflows. And Recent Cases below that gives you your last five open matters with one click each.

---

## SEGMENT 2 — THE RESEARCH STUDIO

**Kavya:** Let's go into the Research Studio. This is where I want to spend some time, because the architecture here is genuinely different from anything else in the market.

**Arjun:** Split screen — AI chat on the left, Reference Gallery on the right. The AI engine is Claude Sonnet by Anthropic — the same research-grade model that international legal departments use. Not a consumer chatbot.

> **[SCREENSHOT: Research Studio full view — left panel: chat interface with quick chip shortcuts along the top (Bail Application, Anticipatory Bail, Res Judicata, Stress-Test Draft, FIR Analysis); right panel: Reference Gallery with "IK Verified Cases" header; microphone icon and attachment icon in input area]**

**Kavya:** Those quick chips at the top —

**Arjun:** Shortcuts to the most common research starting points. "Bail Application" populates a structured query. "Stress-Test Draft" puts the AI in opposing counsel mode — I'll show that separately. "FIR Analysis" walks you through analysing whether the ingredients of the alleged offence are actually made out on the facts. These aren't just labels — they pre-load the right prompting structure.

---

## SEGMENT 3 — THE INDIAN KANOON RAG ARCHITECTURE

**Kavya:** Before we run a query — explain exactly how the Indian Kanoon integration works. Because this is the feature that separates this tool from every generic AI.

**Arjun:** Let me be precise, because this matters. When you submit a research query, the system does not immediately ask the AI to answer. First, it queries the Indian Kanoon database — India's largest free legal database — for real cases relevant to your specific query. Those cases are fetched. Their text is brought in as verified source material. Only then does the AI generate its response, grounded in those verified cases.

**Kavya:** So the AI cites cases that actually exist.

**Arjun:** That's the constraint. Cases fetched from Indian Kanoon get a green "IK Verified" badge in the Reference Gallery. Cases the AI draws from its own training knowledge — which may or may not be perfectly cited — get an amber "AI Suggested" badge. You see both. You know immediately what to trust and what to verify independently.

> **[SCREENSHOT: Reference Gallery with four cards — three green "✅ IK Verified" cards showing case name, court, year, one-line holding; one amber "⚠️ AI Suggested" card; "📖 Read on Kanoon" and "📜 Copy Citation" buttons on the expanded card]**

**Kavya:** What happens without this? What does a generic AI tool do wrong?

**Arjun:** A colleague of mine used a popular AI tool for a bail application. The AI cited three Supreme Court cases — names, years, citations, all sounding authoritative. He filed. Opposing counsel pointed out in court that one of those case names didn't exist. The AI had constructed a plausible-sounding citation. The judge adjourned. That's not a hypothetical — it happens. And in a bail matter, the client stays in custody while you sort it out.

**Kavya:** This architecture prevents that.

**Arjun:** At both ends. IK Verified on research, and there's a separate Verify Citations tool for your final draft before filing. We'll get to that.

---

## SEGMENT 4 — LIVE RESEARCH QUERY

**Kavya:** Let's run a real query.

**Arjun:** Realistic scenario. My client is arrested under BNS Section 64 — the new equivalent of IPC 376. Matrimonial dispute. No medical evidence of physical injury. I need to apply for regular bail under BNSS Section 483. I want to know what the Supreme Court has said about bail in these specific circumstances — and the distinction from anticipatory bail.

> **[SCREENSHOT: Research query typed: "Bail application under BNSS Section 483 in matrimonial dispute — BNS Section 64 alleged, no medical evidence of physical injury. Key Supreme Court directions. Distinguish from anticipatory bail under BNSS Section 484."]**

**Kavya:** Submit. What happens?

**Arjun:** The Reference Gallery starts populating immediately — as the AI types each citation, the card appears on the right in real time. I can watch the research build.

> **[SCREENSHOT: Research Studio mid-response — AI response partially written, three paragraphs visible; Reference Gallery now has four cards: "Arnesh Kumar v. State of Bihar (2014) 8 SCC 273 ✅ IK Verified", "Sushila Aggarwal v. State NCT Delhi (2020) ✅ IK Verified", "Satender Kumar Antil v. CBI (2021) ✅ IK Verified", and one amber card]**

**Kavya:** Arnesh Kumar — that's the landmark case on arrest thresholds in 498A matters.

**Arjun:** The AI has identified the three most relevant precedents without me naming them. Arnesh Kumar on the threshold for arrest, Sushila Aggarwal on anticipatory bail duration, Satender Kumar Antil on the bail jurisprudence framework. All IK Verified — real cases, real citations. The amber card is an additional case from the AI's training data — I treat that as a lead to verify, not a citation to file.

> **[SCREENSHOT: Full research response — four sections: "Legal Framework", "Key Supreme Court Directions", "BNSS 483 vs BNSS 484 Distinction", "Grounds to Emphasise" — inline citations throughout in format "Arnesh Kumar v. State of Bihar (2014) 8 SCC 273"]**

**Kavya:** The response is structured like a research memo, not a chat reply.

**Arjun:** Sections, headings, inline citations. And that last section — "Grounds to Emphasise" — I can lift those directly into the bail application form. The research and drafting are connected.

---

## SEGMENT 5 — DOCUMENT ATTACHMENT AND OCR

**Kavya:** What if you have documents — an FIR, a charge sheet, a previous order — that you need the AI to read as part of the research?

**Arjun:** The attachment button in the chat input accepts PDF, TXT, DOC, DOCX, JPG, and PNG. And this is where a recent upgrade matters significantly — OCR.

**Kavya:** Explain what changed.

**Arjun:** Before, if you uploaded a scanned PDF — something photographed or printed and scanned — the system could only read it if the text was selectable. Most documents that come from courts in India are scanned images, not searchable PDFs. The upgrade adds OCR: if the system can't find selectable text in a PDF, it automatically switches to Claude Haiku vision processing — it reads the document visually, like a human would, up to ten pages.

> **[SCREENSHOT: Research input bar showing attachment chip "FIR_Scanned.pdf — 6 pages — OCR processed" alongside typed query "Analyse this FIR under BNS Section 64. Are the essential ingredients made out? Identify procedural defects."]**

**Kavya:** So a photographed FIR works.

**Arjun:** A photographed FIR, a handwritten order, a scanned vakalatnama. And image uploads — JPG and PNG — are OCR'd directly. Take a photo of a document on your phone, upload it, ask the AI to read it. This matters enormously in district courts where physical document handling is still the norm.

**Kavya:** What about Word documents? Advocates work in Word.

**Arjun:** .docx files now extract properly using mammoth.js — all the text, preserving structure. And this works across all the upload points in the app — Research Studio, Case Briefs, My Cases file attachments, even adding a note. Upload a .docx anywhere, the text is extracted and available to the AI.

**Kavya:** And if someone sends a .doc — the old format?

**Arjun:** The app tells you clearly to resave as .docx or PDF. It doesn't silently fail or give garbled output — it tells you what to do.

---

## SEGMENT 6 — INDIAN KANOON URL IMPORT

**Kavya:** You mentioned an Indian Kanoon URL import — when would you use that?

**Arjun:** When I've already found the specific judgment I want to work with on Indian Kanoon. Instead of copy-pasting text, I paste the URL directly into the chat — the system fetches the full judgment text automatically. Then I ask: "Summarise the ratio of this judgment" or "How does this apply if the accused has no prior record and the investigation is complete?"

> **[SCREENSHOT: Chat input with Indian Kanoon URL pasted: "https://indiankanoon.org/doc/..." and query "How does the ratio in this judgment apply to anticipatory bail where the applicant is a woman above 60 years and the alleged offence is non-cognisable?"]**

**Kavya:** So you can pull any judgment from Indian Kanoon directly into the conversation.

**Arjun:** Any public judgment. And the response is grounded in the actual text of that judgment — not the AI's approximate memory of it.

---

## SEGMENT 7 — STRESS-TEST MODE

**Kavya:** Stress-Test mode. You mentioned this changes how you prepare for hearings.

**Arjun:** After I've drafted my bail application or prepared my research, I paste it into the chat and use the Stress-Test chip — or type the equivalent. The AI reads my draft and argues against it, from the Public Prosecutor's perspective.

> **[SCREENSHOT: Chat input showing a pasted bail application draft and query: "Stress-test this bail application. You are the Public Prosecutor. Identify the three strongest arguments against bail on these facts and flag which grounds in my application are weakest."]**

**Kavya:** The AI argues against your own work.

**Arjun:** Specifically. Not generic pushback. It looks at my actual grounds and tells me where a competent prosecutor would push back, and why.

> **[SCREENSHOT: Stress-test response in three numbered sections — "1. Flight risk argument: The applicant's claim of 'roots in the community' is undermined by the three-month gap between FIR registration and surrender — prosecution will argue this demonstrates willingness to evade..."; "2. Investigation status: Ground 4 states investigation is complete but the supplementary charge sheet has not been filed — this is factually vulnerable..."; "3. Nature of allegation: The court in Arnesh Kumar explicitly noted that serious offences under 376 are not automatically bailable — your draft does not sufficiently distinguish the facts from the typical severity profile..."]**

**Kavya:** This is pre-hearing preparation that used to require a senior colleague.

**Arjun:** And a senior colleague who's honest enough to tell you where your application is weak — not everyone has that. At eleven at night before a nine AM hearing, this is invaluable. I've walked into court significantly better prepared because of this one feature.

---

## SEGMENT 8 — DRAFT DOCUMENTS: 44 TEMPLATES

**Kavya:** Draft Documents. You mentioned forty-four templates — let's be clear about what that means, because the number is significant.

**Arjun:** The Draft Documents panel now has forty-four professional court document templates across seven practice area categories. This covers the full scope of what most Indian advocates actually do day to day.

> **[SCREENSHOT: Draft Documents panel — seven collapsible category sections with coloured headers, each expanded to show template tiles:
> Criminal Law (9): Bail Application, Anticipatory Bail, Quashing Petition, Discharge Application, Section 156(3) Application, Revision Petition, S.138 NI Act Complaint, S.138 NI Act Reply, Criminal Complaint
> Civil Law CPC (10): Civil Plaint, Written Statement, Interlocutory Application, Rejoinder, Execution Petition, Contempt Application, First Appeal, Second Appeal S.100 CPC, Writ Petition, Partition Suit
> Commercial Court (4): Commercial Written Statement, Leave to Defend, Reply to Summary Suit, Section 12A Reply
> Family Law (7): Mutual Divorce Petition, Divorce MoU, Contested Divorce Petition, Maintenance Application, Custody Petition, DV Application, Conjugal Rights Petition
> Corporate/Securities/FEMA (8): NCLT Oppression Petition, NCLAT Appeal, IBC Section 7, IBC Section 9, SAT Appeal, SEBI SCN Reply, FEMA Compounding, ED SCN Reply
> Banking/DRT (2): SARFAESI Section 17, DRT Reply
> General (4): Legal Opinion Letter, Legal Notice, Reply to Legal Notice, Vakalatnama]**

**Kavya:** That's a complete practice library.

**Arjun:** Criminal — bail, anticipatory bail, quashing, discharge, Section 156(3), revision, Section 138 both complaint and reply, criminal complaint. Civil — plaint, written statement, IA, rejoinder, execution, contempt, first appeal, second appeal, writ petition, partition suit. Commercial Court — commercial written statement, leave to defend, summary suit reply, Section 12A reply. Family — seven templates covering the full range of matrimonial and domestic matters. Corporate and securities — NCLT, NCLAT, IBC, SAT, SEBI, FEMA, ED. Banking — SARFAESI and DRT. General — legal opinion, legal notice, reply to notice, vakalatnama.

**Kavya:** For a district court practitioner who does a mix of criminal and civil —

**Arjun:** Everything you need is there. For a corporate lawyer at the NCLT — everything you need is there. For a family court advocate — everything you need is there. Forty-four templates is not a number I'm citing for effect. It genuinely covers the core documents across Indian litigation practice.

---

## SEGMENT 9 — DRAFTING WALKTHROUGH: BAIL APPLICATION

**Kavya:** Walk me through an actual draft.

**Arjun:** Bail Application. I click the tile. The right side shows a template guide — what information I need to have ready. Court name, accused name, FIR details, offence sections, facts, grounds, surety.

> **[SCREENSHOT: Bail Application form — Court Name: "Sessions Court, Lucknow", Accused: "Ramesh Kumar Singh S/o Shyam Narain Singh, aged 34 years", FIR No: "42/2026 dated 15.03.2026", Police Station: "Hazratganj", Sections: "Section 64 BNS / Section 376 IPC — Section 483 BNSS / Section 439 CrPC", Facts field, three Grounds fields, Prayer]**

**Kavya:** The offence sections — BNS and old IPC, BNSS and old CrPC, all filled simultaneously.

**Arjun:** The system knows the mapping. I type the new BNS section and it fills the old IPC equivalent automatically, and vice versa. Dual citation — built in. I fill the facts and grounds from my brief, and click Generate.

> **[SCREENSHOT: Generated bail application — proper court heading "IN THE COURT OF SESSIONS JUDGE, LUCKNOW", parties, FIR details, numbered paragraphs, grounds with inline citations "Arnesh Kumar v. State of Bihar (2014) 8 SCC 273" and "Satender Kumar Antil v. CBI (2021) 10 SCC 51", prayer clause, verification]**

**Kavya:** Eight pages. Properly formatted for that court.

**Arjun:** Forty-five seconds. Compare to forty-five minutes from a blank page. And the citations in the draft are drawn from the Research Studio session — the IK Verified cases I already found are woven into the draft automatically.

**Kavya:** So research and drafting are linked.

**Arjun:** You don't re-enter the case law. Research it once, draft with it. That connection between the two panels is what makes the workflow efficient rather than just fast.

---

## SEGMENT 10 — MY CASES AND ECOURTS INTEGRATION

**Kavya:** My Cases. This has had significant upgrades — let's go through the full picture.

**Arjun:** Creating a case: title, case type — now expanded to the full range of matter types across all practice areas — court or forum, opposite party, initial facts. And there's now a CNR field.

**Kavya:** CNR — the eCourts case number.

**Arjun:** The Case Number Register. The unique identifier every case listed in the eCourts system has. When I enter it on a new case — or add it later from the case detail view — the app fetches the current case status directly from the eCourts Services API.

> **[SCREENSHOT: Case detail for "Ramesh Kumar Singh — Bail" — below the case header, an "eCourts Status" accordion is expanded showing: Next Hearing Date in gold "15 May 2026", Stage: "Arguments", Coram: "Shri A.K. Sharma, Sessions Judge", Case No: "Bail No. 142/2026", Last Order: "Bail application filed. Adjourned for prosecution reply. [12 Apr 2026]"; below that: gold "Add to Calendar" button]**

**Kavya:** Next hearing date, the stage of the matter, which judge is on the bench, and the last order. All pulled live.

**Arjun:** Without logging into eCourts separately. And I can add that hearing date to my calendar with one button — it goes directly into the Calendar panel linked to this case. No manual entry.

**Kavya:** What if eCourts is down? That happens.

**Arjun:** The system handles it gracefully — it shows the last successfully fetched data with a timestamp, and displays a note that eCourts couldn't be reached. It doesn't crash or show an error page. Cached data is available even when eCourts is unavailable.

**Kavya:** And this eCourts data — does it affect the AI?

**Arjun:** This is the part I find most useful. When I open Research from within a case that has eCourts data fetched, that data is automatically injected into the AI's context. The AI knows the next hearing date, the current stage, and the bench when it generates research or a draft. So if I ask for a bail application and the eCourts data says the case is at the "Arguments" stage before Sessions Judge Sharma — the AI drafts for that specific context. Not a generic application.

> **[SCREENSHOT: Research Studio with a case pre-loaded — input shows auto-populated context: "Case: Ramesh Kumar Singh — Bail | Court: Sessions Court, Lucknow | Next Hearing: 15 May 2026 | Stage: Arguments | Coram: Shri A.K. Sharma, Sessions Judge | CNR: UPLK010123456" and the research query appended below]**

**Kavya:** The AI is drafting with real, current case information.

**Arjun:** Not hypothetical facts I've typed from memory. Live court data. That's a meaningful difference in the quality of the draft.

---

## SEGMENT 11 — VOICE NOTES AND CASE TIMELINE

**Kavya:** The notes and timeline inside a case.

**Arjun:** Every note is timestamped. They stack chronologically — so the case file reads like a log of the matter from start to finish. And I can add notes by voice. In court, after the hearing wraps up, before I've left the courtroom, I dictate: "Bail rejected. Prosecution argued flight risk — three months between FIR and surrender. Judge noted no surety available. Matter to be filed before HC. Next steps: prepare HC bail application, address flight risk ground."

> **[SCREENSHOT: Case Notes tab — chronological timeline: "15 Mar 2026 — Briefed by client's family. FIR details confirmed. Arrest on 16 Mar."; "17 Mar 2026 — Research complete. Bail application drafted and reviewed."; "18 Mar 2026 — Bail application filed. Listed before Sessions Judge."; "12 Apr 2026 — [microphone icon] DICTATED: Bail rejected. Prosecution argued flight risk..."]**

**Kavya:** The microphone label shows it was dictated.

**Arjun:** So I know which notes were captured in the moment and which were typed later. The voice capture happens immediately — I haven't forgotten anything by the time I get back to my desk, and it's in the right case file. Not a voice memo I have to transcribe later.

---

## SEGMENT 12 — CASE BRIEFS AND JUDGMENT SUMMARISATION

**Kavya:** Case Briefs — summarising judgments. Walk me through what this produces.

**Arjun:** I paste a judgment text, upload a PDF — including scanned PDFs now with OCR — or paste an Indian Kanoon URL. The AI produces a structured one-page brief in six sections.

> **[SCREENSHOT: Completed Case Brief for "Satender Kumar Antil v. CBI (2021) 10 SCC 51" — six labelled sections: Case Name & Citation | Brief Facts | Legal Issues Framed | Arguments (Petitioner & Respondent) | Ratio Decidendi | Final Decision — text-to-speech play button top right, Save to Case and Copy buttons at bottom]**

**Kavya:** Six sections — and "Arguments of Both Sides" stands out. You get the prosecution reasoning, not just the outcome.

**Arjun:** When I'm preparing to argue against a specific judgment that opposing counsel will cite, knowing the strongest arguments in its favour helps me understand where to push back. And the ratio decidendi section is what I quote — the actual legal principle, not a summary of facts.

**Kavya:** The text-to-speech button.

**Arjun:** Listen to the brief on the drive between courts. District court advocates in India often cover multiple courts in a day. That commute time, previously wasted, becomes preparation time.

---

## SEGMENT 13 — VERIFY CITATIONS

**Kavya:** Verify Citations — the quality control step.

**Arjun:** Before any document goes out, I paste the final draft here. The AI scans every citation and returns a verdict on each one.

> **[SCREENSHOT: Verify Citations results table — four citations listed:
> "Arnesh Kumar v. State of Bihar (2014) 8 SCC 273 — ✅ OK — Well-known Supreme Court judgment, citation complete"
> "State of Rajasthan v. Balchand (1977) 4 SCC 308 — ✅ OK — Volume and page confirmed"
> "Ranjit Singh v. State of Punjab (2021) HC — ⚠️ VERIFY — High Court not specified; confirm court and citation on SCC Online before filing"
> "Mohan Lal v. State 2023 — ❌ WARNING — Year only; no court, volume, or page number. Locate full citation before filing"]**

**Kavya:** Three outcomes — OK, VERIFY, WARNING.

**Arjun:** OK means complete and recognisable. VERIFY means something is missing — usually a volume or page number — check on SCC Online or Indian Kanoon. WARNING means the citation is incomplete or potentially incorrect — do not file without locating the full reference. Combined with the IK Verified badges in Research, this is two layers of citation checking. Mistakes get caught before the filing, not after.

---

## SEGMENT 14 — CALENDAR

**Kavya:** Calendar panel — how does this work in practice?

> **[SCREENSHOT: Calendar panel — month grid view with five hearing dates marked in gold; below: chronological hearing list showing matter title, court, time, linked case name; "Today: 2 hearings" and "This Week: 8 hearings" stat cards at top; "Add Hearing" button]**

**Arjun:** Hearing dates from eCourts sync here automatically when I use the Add to Calendar button from a case. I can also add manually. Each event is linked to the specific case — click it and I'm directly in the case file. So my morning routine is: open Calendar, see what's listed, click each matter, review my research and the last order, and go.

**Kavya:** One workflow from schedule to preparation.

**Arjun:** No hunting through files. No checking eCourts separately. Everything I need for today's hearings is accessible from the Calendar panel in under a minute.

---

## SEGMENT 15 — WHATSAPP ACCESS

**Kavya:** Let's talk about something that's genuinely new — WhatsApp access. What does it mean to use Nyaya Saathi Pro on WhatsApp?

**Arjun:** This is the feature I didn't expect to use and now use every day in court. Your Nyaya Saathi Pro subscription includes WhatsApp access — you register your phone number in your account, and from that point you can message the Nyaya Saathi WhatsApp number directly.

**Kavya:** And the AI responds?

**Arjun:** The AI responds. Same engine — Claude Sonnet, same legal intelligence. Optimised for WhatsApp — responses are under three hundred words, plain text, no markdown. Readable on a phone screen in a courtroom corridor.

> **[SCREENSHOT: WhatsApp conversation — user message: "What are the grounds for default bail under BNSS Section 479 if the charge sheet is not filed within 60 days?" — Nyaya Saathi response in plain text: "Under BNSS Section 479 (formerly CrPC Section 167(2)), if the police fail to file a charge sheet within: 60 days (for offences punishable with less than 10 years imprisonment) or 90 days (for offences punishable with death, life imprisonment, or 10 years or more) — the accused becomes entitled to default bail as a matter of right. Key points: (1) The right arises automatically on the expiry of the prescribed period. (2) The accused must make an application and be ready to furnish bail. (3) The right lapses if not exercised before the charge sheet is filed. Key case: Rakesh Kumar Paul v. State of Assam (2017) 15 SCC 67. Verify dates on eCourts before arguing."]**

**Kavya:** That response is usable immediately. In court. Without opening the app.

**Arjun:** That's exactly how I use it. I'm standing outside the courtroom, I have a question on a procedural point, I WhatsApp Nyaya Saathi, I have the answer in thirty seconds. No login, no loading, no switching apps.

**Kavya:** Does it work in Hindi?

**Arjun:** English, Hindi, and Marathi. The system detects your language preference — you can also set it explicitly by messaging "language: Hindi" — and all subsequent responses come in that language. Devanagari script for both Hindi and Marathi.

> **[SCREENSHOT: WhatsApp conversation in Hindi — user message in Hindi: "अग्रिम जमानत के लिए BNSS की कौन सी धारा लागू होती है?" — Nyaya Saathi response in Hindi Devanagari with legal content about BNSS Section 484]**

**Kavya:** For advocates who practice in district courts where Hindi is the working language —

**Arjun:** This removes the language barrier entirely. You ask in Hindi, you get an answer in Hindi, you can quote it directly in an argument.

**Kavya:** What else can you do from WhatsApp?

**Arjun:** eCourts case status lookup. Send a message with a CNR number — "Status: UPLK010123456" — and the system fetches the current case status, next hearing date, and last order from eCourts. Without opening the app, without going to the eCourts website.

> **[SCREENSHOT: WhatsApp conversation — user message: "Status: UPLK010123456" — Nyaya Saathi response: "eCourts Status — Case: Criminal Bail No. 142/2026, Ramesh Kumar Singh v. State of UP | Court: Sessions Court, Lucknow | Next Date: 15 May 2026 | Stage: Arguments | Last Order: Bail application filed. Adjourned for prosecution reply. [12 Apr 2026]"]**

**Kavya:** That's genuinely useful when you're in court and need to confirm a date quickly.

**Arjun:** Every advocate has had the moment of standing in a courtroom not knowing whether the next date on another matter is today or tomorrow. This solves that in one message.

**Kavya:** Is WhatsApp access on all plans?

**Arjun:** WhatsApp access is included in the Pro plan. It verifies that your registered phone number is on an active Pro subscription before responding. If your subscription lapses, WhatsApp access lapses with it.

---

## SEGMENT 16 — HELP CHATBOT

**Kavya:** There's a help chatbot in the app itself?

**Arjun:** A small chat widget accessible from any panel — gold themed, sits in the corner. It's an advocate-specific FAQ chatbot. If I'm in the middle of drafting and I can't remember which template to use for an IBC Section 7 matter, or I want to know how to add a CNR to an existing case, I ask the chatbot. It knows the app.

> **[SCREENSHOT: Help chatbot widget open in bottom-right corner — user has typed "How do I add a CNR number to a case I already created?", chatbot response: "Open the case from My Cases. In the case detail view, look for the 'eCourts Status' section. Click 'Add CNR' — enter your CNR number and click Fetch. The status will load and you can add the hearing date to your Calendar from there."]**

**Kavya:** It knows the UI, not just the law.

**Arjun:** Exactly. It's not a general legal AI — it's a how-do-I-use-this-feature assistant. Faster than looking for documentation, faster than a tutorial video.

---

## SEGMENT 17 — CLOUD SYNC AND PRIVACY

**Kavya:** Let's talk about where your data lives. Advocates are handling client privileged information — this is sensitive.

**Arjun:** The AI conversations — your research queries, the facts you share — are processed to generate the response and then discarded. There are no chat logs on Nyaya Saathi's servers. What you described about your client's case is gone from their infrastructure as soon as the response is returned.

**Kavya:** Case files?

**Arjun:** Three options in Settings. Local device only — stays in your browser, never leaves your machine. Google Drive — syncs to your own Google Drive account, your folder, your data. OneDrive — same. The company has no access to Drive or OneDrive data. You own it.

> **[SCREENSHOT: Settings > Data Storage panel — three radio button options with descriptions: "📱 Local Device Only — Private. Offline capable." (selected), "☁️ Google Drive — Sync to your own account. Access from any device.", "💼 OneDrive — Sync to your Microsoft account." — below: sync status and last sync timestamp]**

**Kavya:** And the auto-sync on login we mentioned at the start —

**Arjun:** That runs against your own Drive or OneDrive — not a central server. The sync is between your devices and your cloud storage account. Nyaya Saathi is the messenger, not the storage.

**Kavya:** For a client matter with highly sensitive facts.

**Arjun:** Keep it local only. The research query goes to the AI and comes back — that exchange is not stored. Your notes and drafts sit on your device. That's as private as any offline document.

---

## SEGMENT 18 — DARK MODE, MOBILE, AND PWA

**Kavya:** Practically — how does this work on a phone in court?

**Arjun:** The app installs as a Progressive Web App. On Android or iOS, open the site in your browser, hit "Add to Home Screen," and it's on your home screen like a native app. No Play Store, no App Store. The layout responds to screen size — on a phone, the sidebar collapses and you navigate by panel.

> **[SCREENSHOT: Mobile view — Research Studio on a smartphone, full-width chat panel, hamburger menu top left, microphone and attachment icons in input bar]**

**Kavya:** And offline capability?

**Arjun:** Case files, notes, calendar, saved drafts — all accessible offline. The AI research and drafting need internet. But reviewing your preparation, checking hearing dates, reading a draft you saved yesterday — that works without a signal. Courthouse basements, rural court complexes — this matters.

**Kavya:** Dark mode is the default?

**Arjun:** Navy background, gold accents, white text. Designed for low-light environments. Light mode available in Settings for those who prefer it. Both are clean — the UI is built to not be distracting. You're here to work.

---

## SEGMENT 19 — PRICING AND WHO THIS IS FOR

**Kavya:** Pricing. Who is this built for and what does it cost?

**Arjun:** Two thousand four hundred and ninety-nine rupees a month for Pro. Twenty-four thousand nine hundred and ninety-nine for a year — saves about five thousand. Promo code LAI50 gives fifty percent off.

**Kavya:** Put that in context against alternatives.

**Arjun:** SCC Online — just the case law database, no AI, no drafting — runs thirty to fifty thousand a year for meaningful coverage. Manupatra is similar. Neither of them drafts your bail application, runs a stress-test against your arguments, summarises judgments, manages your cases, or sends you eCourts updates on WhatsApp. The comparison isn't perfectly like-for-like, but for a district court advocate doing five to ten drafts a week — the time saving at eighty-three rupees a day makes the calculation obvious.

**Kavya:** Who gets the most value?

**Arjun:** Four profiles. Solo practitioners at district courts — high volume, need maximum efficiency. Junior advocates building their practice — no drafting templates, no SCC subscription, this gives them both. Criminal lawyers doing heavy bail work under the new BNSS codes. And civil litigators writing plaints, written statements, and IAs at scale. For corporate and NCLT work — the eight templates in that category cover what smaller firms need without a large firm's research infrastructure.

**Kavya:** And there's a beta trial?

**Arjun:** Forty-eight-hour full Pro access with no payment required. Apply on the website. Use it on a real matter. If it saves you time on one bail application in those forty-eight hours — which it will — the value proposition is answered.

---

## SEGMENT 20 — WHAT IT DOESN'T DO

**Kavya:** Last segment — limitations. What does this not do?

**Arjun:** The draft is a first draft. Not a filed document. Every output requires professional review. The AI doesn't know your specific judge's preferences. It doesn't know the tone of your relationship with opposing counsel. It doesn't know what the Presiding Officer said off the record last week. That context lives with you — and it changes the strategy.

**Kavya:** Citation accuracy?

**Arjun:** The IK Verified system significantly reduces hallucinated citations — it doesn't eliminate the need to verify before filing. Green-badged cases should still be spot-checked on Indian Kanoon before you quote paragraph numbers in a submission. The Verify Citations tool adds another layer, but the advocate's eye is the final check.

**Kavya:** And the legal judgment?

**Arjun:** Always yours. The AI can tell you what the Supreme Court said about anticipatory bail in matrimonial disputes. It cannot tell you whether applying for bail is the right strategy for your specific client at this moment. Whether to apply at the Sessions Court first or go directly to the High Court. Whether this judge is likely to grant on these facts. Those calls are made by you, for your client, based on everything you know. That's what the practice of law is. This tool gives you more time and better information to make those calls — it doesn't make them for you.

**Kavya:** Co-pilot not autopilot.

**Arjun:** Exactly. The advocate's expertise is the irreplaceable part. This handles the structured, repetitive, format-dependent work so that expertise has more time to do what it's actually for.

---

## CLOSING

**Kavya:** Nyaya Saathi Pro. Advocate Studio at legalaidai.in/advocate. Two thousand four hundred and ninety-nine rupees a month — use LAI50 for fifty percent off. Forty-four professional templates across seven practice areas. WhatsApp access included. Forty-eight-hour beta trial with no payment required.

**Arjun:** And for anyone sceptical — I was too. I tested it on a real anticipatory bail matter. The research took eight minutes instead of ninety. The draft was ready in under a minute. I still reviewed it, corrected two things specific to the local court, filed it. The client was at home that evening.

**Kavya:** That's the outcome that matters.

**Arjun:** The outcome is always what matters. The tool exists to serve that.

---

## END OF SCRIPT

---

## NOTEBOOKLM UPLOAD INSTRUCTIONS

**How to use this script in NotebookLM:**

1. Go to [notebooklm.google.com](https://notebooklm.google.com) → Create a new Notebook: "Nyaya Saathi Pro — Advocate Studio"
2. **Add Source → Upload** this file as `.md` or `.txt`
3. Optionally add supporting sources:
   - `advocate_panel_features.md` — full technical feature reference
   - `advocate_use_cases.md` — practice area use cases
   - `PROMO-REFERENCE.md` — pricing and competitive context
4. Click **Generate** under **Audio Overview** — produces a 20–28 minute podcast
5. NotebookLM will paraphrase, not read verbatim — this is expected and produces a more natural result

---

## SCREENSHOT CUE REFERENCE

Prepare these screen captures for recorded walkthroughs (each `[SCREENSHOT: …]` is a cut point):

| # | Panel / Screen | Key element to show |
|---|---|---|
| 1 | Login → My Cases | Auto-sync banner (gold spinner → green confirmation) |
| 2 | Dashboard | Stat cards, Quick Actions, Recent Cases |
| 3 | Research Studio | Split screen — chat left, Reference Gallery right, quick chips |
| 4 | Reference Gallery | IK Verified (green) vs AI Suggested (amber) cards |
| 5 | Live query | Response building + Gallery populating in real time |
| 6 | Document upload | Attachment chip showing "OCR processed" label |
| 7 | Stress-test response | Three numbered prosecution arguments |
| 8 | Draft Documents panel | All 7 category sections expanded showing 44 template tiles |
| 9 | Bail Application form | Dual BNS/IPC and BNSS/CrPC section fields |
| 10 | Generated bail application | Full court heading, numbered paragraphs, citations |
| 11 | Case detail + eCourts accordion | Next date in gold, stage, coram, last order, Add to Calendar |
| 12 | Research Studio with eCourts context | Auto-populated case and hearing data in research input |
| 13 | Case Notes tab | Chronological timeline with dictated note label |
| 14 | Case Briefs completed | Six sections, text-to-speech button |
| 15 | Verify Citations results | OK / VERIFY / WARNING table |
| 16 | Calendar panel | Stat cards, hearing list, linked cases |
| 17 | WhatsApp conversation | Research query + plain-text AI response |
| 18 | WhatsApp in Hindi | Same conversation in Devanagari |
| 19 | WhatsApp eCourts lookup | CNR status response in WhatsApp |
| 20 | Help chatbot widget | FAQ response about CNR setup |
| 21 | Settings > Data Storage | Three sync options, auto-sync status |
| 22 | Mobile PWA view | Research Studio on smartphone screen |

**Separate citizen script:** See `NOTEBOOKLM-CITIZEN-SCRIPT.md`  
**Combined script (older version):** See `NOTEBOOKLM-DEMO-SCRIPT.md`





---

*Script version: April 2026 — all features current | Nyaya Saathi Pro | legalaidai.in/advocate*


---

## Source: OUTREACH-WORKFLOW.md

# Nyaya Saathi — Advocate Outreach Workflow

*Reference document. Last updated: May 2026.*

---

## Overview

The outreach system finds Indian advocates, sends them a personalized cold email with a one-time beta activation link, and tracks their journey from first contact to paid subscription. It has two independent components:

1. **Admin Dashboard (Outreach Panel)** — manages the contact database, imports contacts, reviews reply drafts
2. **Outreach Agent** — the sending engine (Node.js CLI / scheduled job) that personalizes and delivers emails

---

## The Two Email Paths

### Path 1 — Admin Manual Invite (Beta Panel in Dashboard)

**When to use:** Warm contacts, known advocates, someone who expressed interest directly.

**Trigger:** Admin clicks "Send Invite" in the admin dashboard → Beta tab.

**What happens:**
1. `beta-invite.js` Netlify function generates a signed HMAC token
2. Stores an audit record in Firestore → `beta_invites` collection
3. Sends a formal branded HTML email via Resend

**Email format:** Formal corporate HTML
```
Dear [Name],

You have been selected to join the private beta of Nyaya Saathi Pro —
the advanced AI engine designed specifically for the Indian legal profession.

Included in this Beta:
  • AI Research Studio: High-speed legal research with automatic citation extraction
  • Drafting Engine: Generate bail applications, complaints, and opinions in seconds
  • Case Management: Securely store your notes and case timelines
  • Reference Gallery: Interactive cards for Supreme Court & High Court cases

Your invitation grants 48 hours of full access to all premium features.

[🚀 Launch Research Studio button]
```

**Link format:** `https://www.legalaidai.in/advocate?beta=<base64payload>.<HMAC-signature>`

---

### Path 2 — Outreach Agent Cold Email (Outreach Panel in Dashboard)

**When to use:** Cold contacts imported via CSV or Apollo.io — advocates who haven't heard of Nyaya Saathi yet.

**Trigger:** "Send Next Batch (20)" button in the Outreach panel → OR `npm run send` locally → OR automated cron schedule (see Automation section below).

**What happens:**
1. Outreach agent pulls up to 20 advocates with `status = ready_to_contact` from Supabase
2. For each advocate, calls `beta-invite.js` API with `action: generate-code`
3. Gets back a unique `NSP-XXXX-XXXX` activation code (stored in Firestore → `beta_codes`)
4. Passes the code link + advocate details (name, city, practice area) to Claude
5. Claude writes a personalized 90–130 word peer-to-peer cold email
6. Email is sent via Resend
7. Supabase `advocates.status` updated to `contacted`, message logged to `messages` table

**Email format:** Plain text, Claude-personalized. Rules:
- 90–130 words, short sentences, Indian English
- Hook: names specific pain using practice area / city (e.g., *"Drafting bail applications in Tis Hazari at 11pm is brutal."*)
- One concrete benefit (time saved, verified citations, BNSS coverage)
- Offer: 48-hour free beta, no card required, promo code **LAI50** = 50% off first month
- CTA: the personal one-time activation link
- Sign-off: human first name only (e.g., *— Nidhi*)
- PS line mentioning LAI50 and the personal link
- Never uses: "revolutionary", "game-changing", "synergy", emojis

**Example (illustrative):**
```
Hi Priya,

Drafting bail applications in Tis Hazari at 11pm is brutal. I know 
because I've heard it from a dozen advocates this month.

We built Nyaya Saathi Pro for exactly this — AI legal research and 
drafting that actually cites real Indian judgements, not hallucinated 
ones. Bail drafts in under 2 minutes. BNSS and IPC covered.

48 hours completely free, no card required. Your personal access link:
https://www.legalaidai.in/advocate?activate=NSP-A7B2-X9K4

Try it tonight — Nidhi

PS: Use code LAI50 at checkout for 50% off your first month.
```

**Activation link format:** `https://www.legalaidai.in/advocate?activate=NSP-XXXX-XXXX`

---

## How the Invitee Accesses the Site

**Step-by-step for the advocate:**

1. Receives email → clicks the personal activation link
2. Browser opens `https://www.legalaidai.in/advocate?activate=NSP-XXXX-XXXX`
   (or `?beta=<token>` for Path 1)
3. Frontend detects the URL parameter → calls `beta-access` Netlify function to validate
4. If valid and not expired → **registration modal appears** pre-filled where possible
5. Advocate fills in: Full name, Email, Password, Category of law, Bar enrollment no., Years of practice, State
6. Clicks **"Activate & Create Account"**
7. `beta-register` Netlify function creates their Firebase account and marks the code as used
8. **48 hours of full Pro access begins immediately** from first login
9. After 48 hours → they see: *"Your beta access has ended. Use code LAI50 for 50% off."*

**Important:** The activation code is one-time use and expires after 48 hours from generation (not from first login). If they don't click within 48h, the link is dead.

---

## Automation Options for the Send Step

The email sending (Path 2) requires the outreach agent to run. Three options:

### Option A — Manual Local Run (Current State)
Run on your laptop whenever you want to send a batch:
```
cd outreach-agent
npm run send
```
No setup needed. You control timing completely.

### Option B — Button-Triggered via Build Hook (Semi-automated)
The "Send Next Batch" button in the admin dashboard is wired to `OUTREACH_AGENT_BUILD_HOOK`.

Setup required:
1. Deploy the outreach agent as a **separate Netlify site**
2. In that Netlify site → Site Settings → Build Hooks → create a hook
3. Copy the hook URL → add to Beta3 Netlify env vars as `OUTREACH_AGENT_BUILD_HOOK`
4. Set the outreach agent site's build command to `npm run send`

Now the dashboard button triggers a remote send job without touching your laptop.

### Option C — Fully Automated Daily/Weekly Send (Scheduled)
Same as Option B, plus add a cron schedule in the outreach agent's `netlify.toml`:
```toml
[functions.'send-cron']
  schedule = '0 3 * * 1'   # Every Monday at 3:30am IST (UTC+5:30)
```
Sends automatically on a schedule. No button press needed.

---

## Contact Pipeline — Status Flow

```
[CSV/Apollo Import]
        ↓
  ready_to_contact   ← Starting state for all new imports
        ↓
    contacted        ← After cold email is sent
        ↓
      replied        ← After advocate replies to the email
        ↓
    converted        ← After they sign up and activate
        ↓
  opted_out / bounced  ← If they unsubscribe or email bounces
```

The outreach agent's reply handler (auto-reply mode) reads inbound replies, classifies intent (question / interested / objection / opt_out / out_of_office), and either:
- Drafts a reply automatically (for questions and interested)
- Flags it for human review in the admin dashboard (for objections)
- Does nothing + marks opted_out (for unsubscribe requests)

---

## Admin Dashboard — Outreach Panel

The Outreach tab in `admin-dashboard.html` provides:

| Section | What it does |
|---|---|
| **Stats row** | Live counts: Ready / Contacted / Replied / Converted / Opted Out / Bounced |
| **Campaign Controls** | "Send Next Batch" button + CSV file upload |
| **Apollo.io Search** | Live API search → import contacts directly into Supabase |
| **WhatsApp Sync** | Push phone-verified advocates into the WhatsApp agent as contacts |
| **WhatsApp Broadcast** | Send a WhatsApp campaign message to a tagged segment |
| **Drafts Pending Review** | Reply drafts that need human approval before sending |
| **Advocate Pipeline** | Full table with search + status filter, thread viewer, Do Not Contact button |

---

## Environment Variables Required (Beta3 Netlify Site)

| Variable | Required for | Status |
|---|---|---|
| `SUPABASE_URL` | All outreach functions | ✅ Configured |
| `SUPABASE_SERVICE_KEY` | All outreach functions | ✅ Configured |
| `RESEND_API_KEY` | Draft approval, sending | ✅ Already present |
| `RESEND_FROM_EMAIL` | From address (defaults to `Nyaya Saathi <hello@mail.legalaidai.in>`) | Optional |
| `APOLLO_API_KEY` | Apollo.io live search | ⬜ Add in Netlify UI |
| `OUTREACH_AGENT_BUILD_HOOK` | "Send Next Batch" button | ⬜ Add after deploying outreach agent site |

---

## Promo Code Reference

| Code | Discount | Where mentioned |
|---|---|---|
| **LAI50** | 50% off first month | Cold email PS line, reply emails |

---

*End of document.*
