# LegalAidAI — Corporate / In-house Module

## Source: corporate-law-guide.md

# Nyaya Saathi Pro — Corporate Law Features Guide

A reference for corporate advocates on what the app covers, how to use it effectively, and ready-to-use prompts for key corporate law scenarios.

---

## Coverage at a Glance

| Area | Research Studio | Drafting |
|---|---|---|
| NCLT — Oppression & Mismanagement (Sections 241-242 CA 2013) | ✓ | ✓ Company Petition |
| NCLT — Class Action (Section 245 CA 2013) | ✓ | — |
| NCLT — Winding Up (Sections 271-272 CA 2013) | ✓ | — |
| IBC 2016 — Financial Creditor (Section 7) | ✓ | ✓ Section 7 Application |
| IBC 2016 — Operational Creditor (Section 9) | ✓ | ✓ Section 9 Application |
| IBC 2016 — Pre-Pack Insolvency (Section 54A, MSMEs) | ✓ | — |
| Commercial Courts Act 2015 — full suite | ✓ | ✓ Multiple types |
| SEBI Act / Insider Trading (PIT Regs) / Takeover Code | ✓ | ✓ SCN Reply + SAT Appeal |
| FEMA 1999 / FDI / ECB / Compounding | ✓ | ✓ Compounding App + ED SCN Reply |
| Legal Opinion Letters | ✓ | ✓ |
| Contract Review & Risk Audit | ✓ | — |

**Not covered:** RBI banking supervision · IRDAI · Competition Act / CCI · PMLA as standalone practice · Direct/indirect tax matters.

---

## Research Studio — How Corporate Law Works

The Research Studio uses Claude Sonnet with dedicated specialist blocks for each area. Responses include:
- Precise statutory provisions with correct section numbers
- Key case citations tagged `[REF: CASE]` (certain) or `[UNCERTAIN:]` (verify before filing)
- Procedural guidance — NCLT Rules 2016, IBC timelines, SEBI adjudication process
- Strategic advice oriented toward the specific side you are advising

### Tips by Area

**NCLT matters:** Provide the petitioner's shareholding percentage, the total number of shareholders, and specific acts of oppression with dates. The AI structures grounds under Sections 241/242 and advises on Section 244 locus.

**IBC matters:** Specify financial creditor or operational creditor upfront. For Section 9, always mention whether a demand notice was sent, the date, mode of service, and the corporate debtor's exact reply — the Mobilox test analysis depends on this.

**SEBI matters:** Provide the SCN reference number, the specific Regulation alleged to have been violated (PIT / SAST / LODR), and the nature of the allegation. The AI identifies applicable provisions, limitation arguments, and penalty mitigation factors.

**FEMA matters:** Specify the type of transaction (FDI allotment, ECB drawdown, share transfer), the specific contravention (late FCGPR filing, end-use violation, approval-route non-compliance), and whether it is an RBI compounding matter or an ED adjudication matter — this distinction is critical and the AI explains it precisely.

---

## Drafting — Corporate Documents Supported

Access via the **✍ Draft button** in Research Studio (research-led drafting, up to 8,000 tokens) or via **My Cases → Draft accordion** (case-file-linked drafts).

### 1. NCLT Company Petition — Oppression & Mismanagement (Sections 241-242 CA 2013)

**What the AI generates:**
- Locus averment (Section 244 threshold — 10% equity or 100 members)
- Incorporation, CIN, authorised/paid-up capital, shareholding structure
- Part-wise narrative of oppressive acts and prejudicial conduct
- Section 242 relief menu: share purchase at fair value, director removal, injunction, winding up in the alternative
- Verification by petitioner(s)

**Sample prompt for My Cases drafting:**
> "Draft an NCLT Company Petition under Sections 241 and 242 CA 2013. Petitioner: [Name], holding [X]% equity in [Company Name] (CIN: [X]). Respondents: (1) the company; (2) [Majority Director Name]. Acts of oppression: [describe specifically — date, act, impact]. Relief sought: purchase of petitioner's shares at fair value determined by independent valuer and removal of Respondent No. 2 as Director."

---

### 2. IBC Section 7 Application — Financial Creditor

**What the AI generates:**
- CP (IB) case heading with correct bench citation format
- All four Parts of Form 1 structure (financial debt → default → proposed IRP → documents)
- NPA/default date averments
- Moratorium prayer under Section 14 and IRP appointment prayer

**Sample prompt:**
> "Draft a Section 7 IBC application. Financial creditor: [Bank name]. Corporate debtor: [Company name, CIN]. Nature of debt: term loan of ₹[X] crore disbursed on [date] under Loan Agreement dated [date]. Date of first default: [date]. Total outstanding: ₹[X] crore (principal + interest). Proposed IRP: [Full name, IBBI Reg. No. IBBI/IPA-001/IP-P-XXXX]."

---

### 3. IBC Section 9 Application — Operational Creditor

**What the AI generates:**
- All five Parts of Form 5 structure
- Full jurisdictional pre-condition chain: demand notice → 10-day period → no payment → no genuine dispute
- Mobilox test averment (dispute not spurious/illusory)
- Correct prayer sequence (admission → moratorium → IRP → public announcement)

**Sample prompt:**
> "Draft a Section 9 IBC application. Operational creditor: [Supplier name]. Corporate debtor: [Company name, CIN]. Operational debt: unpaid invoices for [goods/services] totalling ₹[X] lakh. Demand notice sent on [date] by registered post, delivered on [date]. No reply received within 10 days. No payment made. Proposed IRP: [Name, IBBI Reg. No.]."

---

### 4. SAT Appeal — Section 15T SEBI Act

**What the AI generates:**
- Correct SAT case heading (Appeal No. / year)
- Full particulars of impugned AO/Board order (order number, date, operative directions, penalty)
- Numbered grounds covering: AO error of law, natural justice violation, disproportionate penalty, perversity of fact-finding, limitation
- Stay application paragraph
- Prayer with all standard SAT reliefs

**Sample prompt:**
> "Draft a SAT Appeal under Section 15T SEBI Act. Appellant: [Name]. Impugned order: Adjudication Order No. [X] dated [date] by AO [Name]. Penalty: ₹[X] for alleged violation of Regulation [X] PIT Regulations 2015. Grounds: (1) no UPSI existed at the time of trade — information was public; (2) personal hearing was denied despite specific request; (3) penalty disproportionate to the quantity and value of trades."

---

### 5. Reply to SEBI Show Cause Notice

**What the AI generates:**
- Para-wise reply structure to every allegation in the SCN
- Substantive defences tailored to the specific violation type: insider trading (no UPSI / legitimate purpose / not connected person), open offer (below trigger threshold / Regulation 10 exemption), LODR (technical default without investor prejudice)
- Limitation argument if the SCN is issued beyond 3 years
- Mandatory personal hearing request
- Verification

---

### 6. FEMA Compounding Application — Section 15 FEMA 1999

**What the AI generates:**
- All four Parts expected by the RBI Compounding Authority
- Specific FEMA Regulation and Notification citation
- Factual narrative of how the contravention arose and steps taken to regularise
- Mandatory undertaking clause
- Correct addressee (RBI Regional Office vs ED — clarified in the research phase)

---

### 7. Reply to ED Show Cause Notice — FEMA

**What the AI generates:**
- Preliminary objections: vagueness of SCN, limitation under Section 16(4) FEMA (2-year bar)
- Para-wise reply to each allegation
- Substantive defences: permissible transaction, AD bank compliance, RBI Master Direction permits, compounding already done (closure defence)
- PMLA separation argument where relevant
- Verification

---

## Key Workflows

### Workflow A: Minority Shareholder Dispute — NCLT Petition

1. **Research Studio:** "Does my client holding [X]% equity in [Company] meet the Section 244 CA 2013 locus threshold to file an oppression petition?"
2. **Research Studio:** "These acts of oppression occurred: [describe]. Are they sufficient for Section 241(1)(a) — oppressive to members — or Section 241(1)(b) — prejudicial to company's interests?"
3. **My Cases → Draft:** NCLT Company Petition (Sections 241-242)
4. **Research Studio:** "What interim relief can the NCLT grant before the petition is heard? Can it restrain the majority from further share allotments or asset alienation?"

---

### Workflow B: Operational Creditor Filing Section 9

1. **Check threshold:** ₹1 crore minimum (Section 4 IBC — 2020 notification).
2. **Research Studio:** "I sent a demand notice under Section 8 IBC on [date]. The CD replied on [date] saying [describe reply]. Does this constitute a pre-existing dispute that defeats my Section 9 application under the Mobilox test?"
3. **My Cases → Draft:** IBC Section 9 Application — Operational Creditor
4. **Research Studio:** "What is the NCLT Bench jurisdiction for a company whose registered office is in [city]?"
5. **File at the correct NCLT Bench** with Form 5 and all annexures.

---

### Workflow C: Defending a SEBI SCN (Insider Trading)

1. **Research Studio:** "SEBI SCN No. [X] dated [date] alleges insider trading under Regulation 4(1) PIT Regulations 2015. The alleged trade was [X] shares of [Company] on [date]. Was the quarterly result announcement (made on [date]) UPSI at the time of the trade?"
2. **Research Studio:** "My client received the information from [outside counsel / banker]. Does the legitimate purpose defence under Regulation 3(3) PIT Regulations apply? What records must exist?"
3. **✍ Draft:** Reply to SEBI Show Cause Notice
4. If AO order is adverse: **✍ Draft:** SAT Appeal (file within 45 days of order — Section 15T)

---

### Workflow D: FEMA Compounding with RBI

1. **Research Studio:** "My client allotted shares to a US investor on [date] but filed FCGPR only on [date] — [X] months late. What specific FEMA Regulation and Notification has been violated? What is the compounding process and expected compounding amount?"
2. **Regularise first:** Ensure late filing is completed, RBI acknowledged.
3. **✍ Draft:** FEMA Compounding Application
4. **Research Studio:** "Does this delay in FCGPR filing also create any PMLA exposure? Can the ED treat this as a predicate FEMA offence?"

---

## Citation Policy in Corporate Law

| Source | Reliability | What the AI does |
|---|---|---|
| IBC — 5 SC landmark cases | High confidence | Cited directly with `[REF: CASE]` |
| NCLT/NCLAT orders | Low confidence | Marked `[UNCERTAIN:]` |
| SEBI Act sections | High confidence | Cited directly |
| SAT/HC orders | Low confidence | Marked `[UNCERTAIN:]` + recommend verifying on sebi.gov.in |
| FEMA Regulations / RBI Master Directions | High confidence | Cited directly by regulation name |
| ATFE / FEMA case law | Low confidence | Marked `[UNCERTAIN:]` |

**The 5 IBC SC cases you can cite with confidence (the AI knows these precisely):**
1. *Swiss Ribbons v. Union of India* (2019) 4 SCC 17 — constitutional validity of IBC
2. *Innoventive Industries v. ICICI Bank* (2018) 1 SCC 407 — moratorium is automatic on admission
3. *Pioneer Urban Land v. Union of India* (2019) 8 SCC 416 — homebuyers as financial creditors
4. *CoC of Essar Steel v. Satish Kumar Gupta* (2020) 8 SCC 531 — CoC commercial wisdom is supreme
5. *Mobilox Innovations v. Kirusa Software* (2018) 1 SCC 353 — pre-existing dispute test (Section 9)

---

## What Is Not Covered

| Area | Why |
|---|---|
| RBI Banking Regulation Act enforcement / PCA | Specialist banking supervision — not in scope |
| Competition Act 2002 / CCI proceedings | Distinct regulatory area |
| PMLA standalone proceedings | Cross-referenced in FEMA context only; PMLA as primary subject not covered |
| IRDAI / Insurance regulation | Not in scope |
| Income Tax / GST / Customs | Tax practice requires separate specialist tooling |
| International arbitration (UNCITRAL / ICC) | Domestic arbitration only |

---

*All AI-generated research and drafts must be reviewed by a qualified senior advocate before filing. The AI provides a structured starting point — professional judgment on facts, strategy, and court-specific practice remains yours.*


---

## Source: corporate-compliance-coverage.md

# /corporate — Exhaustive Corporate Compliance Coverage Map
**Last updated:** 2026-05-27  
**Author:** Claude Code (claude-sonnet-4-6)  
**Purpose:** Full audit of every corporate compliance domain against what /corporate currently covers, with gap analysis and prioritised remediation roadmap.

---

## Legend
- ✅ **LIVE (Phase 1)** — built and deployed
- 🟡 **PARTIAL** — partially covered; gap noted
- 🔵 **PHASE 2/3** — designed, not yet built
- ⚫ **OUT OF SCOPE** — intentionally excluded by product decision
- 🔴 **GAP** — unaddressed; potential future opportunity

---

## DOMAIN A — Companies Act 2013: Annual Statutory Compliance

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Annual General Meeting (AGM)** — S.96–107 CA 2013 | Must be held within 6 months of FY end (31 Mar companies → by 30 Sep). First AGM within 9 months of incorporation. 21-day notice to members. Explanatory statement for special business. Proxy form. Quorum, chairman, e-voting for listed companies | ✅ **LIVE** — Compliance calendar auto-generates AGM deadline (30 Sep) by company type. AI drafts **AGM Notice & Agenda** with S.101–107 compliance; verifies 21-day notice period, explanatory statement requirement, and proxy clause. Research mode handles AGM procedural queries |
| **Annual Return — MGT-7 / MGT-7A** — S.92 CA 2013 | Filed within 60 days of AGM. MGT-7A is abridged form for OPC / small companies. Discloses shareholding, directors, key changes. CS signs. Listed companies: additional SEBI disclosures | ✅ **LIVE** — Compliance calendar generates MGT-7 deadline (29 Nov). AI in research mode explains MGT-7 structure and filing obligations. Draft mode covers covering letter format; does not generate actual MGT-7 XML/form (ROC form filling is out of scope by design) |
| **Financial Statements Filing — AOC-4 / AOC-4 CFS** — S.137 CA 2013 | Filed within 30 days of AGM. Includes Balance Sheet, P&L, Cash Flow, Directors' Report, Auditors' Report. CFS for companies with subsidiaries. XBRL tagging for listed and large companies | 🟡 **PARTIAL** — Compliance calendar generates AOC-4 deadline. AI drafts **Directors' Report** (key disclosures section) and **Directors' Responsibility Statement**. Does not generate financials or XBRL — correctly out of scope (requires accounting data) |
| **Directors' Report** — S.134 CA 2013 | Annual statutory report covering: state of company affairs, dividends, directors/KMPs, audit observations, RPTs, CSR, vigil mechanism, risk management, subsidiary performance | ✅ **LIVE** — Dedicated drafting template **"Directors' Report (key disclosures)"** in SYSTEM_CORPORATE. AI generates legal/statutory disclosure sections based on company particulars provided |
| **Board Meetings** — S.173 CA 2013 | Minimum 4 board meetings/year; gap between any two meetings ≤ 120 days. First meeting within 30 days of incorporation. Minutes must be signed within 30 days | 🔵 **PHASE 3** — Compliance calendar generates 4 quarterly board meeting reminders. Board meeting scheduling and minute-book tracking are Phase 3 (client portal / matter tracker). AI handles research on quorum, meeting procedure, and notice requirements |
| **Director KYC — DIR-3 KYC** | All directors with DIN must file DIR-3 KYC annually by 30 Sep. KYC-Web for directors who filed previously with no change. Failure deactivates DIN | ✅ **LIVE** — Compliance calendar auto-generates DIR-3 deadline (30 Sep). AI explains DIN deactivation consequences and filing procedure in research mode |
| **Secretarial Audit — Form MR-3** | Mandatory for listed companies + public companies (paid-up ≥ ₹50 Cr or turnover ≥ ₹250 Cr). Conducted by a Company Secretary in Practice. Report attached to Directors' Report | 🟡 **PARTIAL** — **Secretarial Audit Observation Response** is a dedicated drafting template — AI drafts counsel's reply to adverse observations. Underlying audit-triggering framework (MR-3, ICSI standards) handled in research mode only. No audit-tracking |
| **Statutory Registers** — S.85–94 CA 2013 | Register of Members, Directors & KMP, Charges, Contracts (RPT), Loans/Investments (S.186), Foreign Register. Must be maintained at registered office; available for inspection | 🔴 **GAP** — No template, checklist, or guidance specifically for statutory register maintenance. AI can answer research queries but there is no dedicated workflow, checklist, or compliance reminder |
| **CSR Compliance** — S.135 CA 2013 | Triggered at: net worth ≥ ₹500 Cr, or turnover ₹1,000 Cr+, or net profit ₹5 Cr+. CSR Committee (≥3 directors, ≥1 independent), 2% average 3-year net profit spend. Unspent → PM Relief Fund within 6 months. Annual CSR Report | 🔴 **GAP** — CSR is not covered as a dedicated domain. No CSR template, compliance calendar entry, or spending tracker. Significant gap for large company clients |

---

## DOMAIN B — Companies Act 2013: Event-Based / Triggered Compliance

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Share Allotment** — S.39, 42, 62, PAS-3, MGT-14 | Private placement: S.42 + PAS-4 offer letter, PAS-5 record of holders, PAS-3 (Return of Allotment within 15 days) + MGT-14 for special resolution. Rights issue: S.62(1)(a). ESOP: S.62(1)(b). FDI allotment: FCGPR within 30 days | ✅ **LIVE** — **Board Resolution: Share Allotment** template covers Board authorisation step. FEMA domain handles FCGPR. Research mode explains S.39/42/62 process, PAS forms, and pricing rules. PAS-3 form filing not generated (ROC form out of scope) |
| **Director Appointment** — S.152, DIR-12 | Appointment by Board (casual vacancy) or shareholders (AGM/EGM). DIR-12 within 30 days. Consent (DIR-2), disclosure of interest (MBP-1/DIR-8). DIN, disqualification check (S.164) | ✅ **LIVE** — **Board Resolution: Director Appointment** template with S.152 compliance, consent recital, DIN recital. DIR-12 filing explained in research mode. Independent Director letter of appointment is not yet a separate template |
| **Director Resignation** — S.168, DIR-11, DIR-12 | Director files DIR-11 with ROC within 30 days. Company files DIR-12 within 30 days. Resignation letter; board noting | ✅ **LIVE** — **Board Resolution: Director Resignation** template. Includes S.168 compliance, noting at next board meeting, DIR-12 filing reminder |
| **Registered Office Change** — INC-22, MGT-14 | Within city: Board resolution + INC-22. Outside city within state: Special Resolution + MGT-14 + INC-22. Outside state: NCLT approval (S.13) + special resolution. Public notice required | ✅ **LIVE** — **Board Resolution: Registered Office Change** template. Research mode explains intra-city/inter-city/inter-state distinction and approval pathway |
| **Charges** — S.77, CHG-1/CHG-4 | Creation: CHG-1 within 30 days (extendable to 300 days with ROC fees). Modification: CHG-1. Satisfaction: CHG-4 within 30 days. Condonation of delay: NCLT application if beyond 300 days | 🔴 **GAP** — No dedicated charge registration template or compliance reminder. AI handles research queries on CHG-1/CHG-4 but there is no drafting template for charge creation Board Resolution or satisfaction application |
| **Related Party Transactions (RPT)** — S.188, Reg 23 LODR | Listed: Audit Committee pre-approval (Reg 23 LODR). Material RPT: shareholder special resolution (non-related party votes only). Unlisted: Board approval if no conflict; S.188 Board resolution for contracts. AOC-2 disclosure in Directors' Report | ✅ **LIVE** — **Board Resolution: RPT (S.188)** template with materiality threshold, arm's-length recital, S.184 disclosure reference, and audit committee cross-reference for listed companies |
| **Loans to Directors** — S.185 | Prohibited to directors/their relatives/companies where director is director/member. Exceptions: holding-subsidiary, loan from listed company, special resolution + SEBI compliance | 🟡 **PARTIAL** — AI handles S.185 research queries accurately. No dedicated drafting template for the exceptional cases |
| **Loans, Investments & Guarantees** — S.186 | Limits: 60% of paid-up+free reserves or 100% of free reserves (higher). Board resolution within limits; special resolution beyond. No double-layer investment for investment companies. Prior approval from public financial institutions | ✅ **LIVE** — **Board Resolution: Investment/Loan/Guarantee (S.186)** template with 60%/100% threshold check, double-layer restriction flag, PFI consent reminder |
| **Borrowing Powers** — S.180(1)(c) | Borrowing beyond paid-up capital + free reserves requires special resolution. Board cannot exceed limits without shareholder approval | ✅ **LIVE** — **Board Resolution: Borrowing Powers (S.180)** template with shareholder resolution trigger check |
| **Share Capital Reduction / Buyback** — S.68–70 | Buyback: up to 10% via Board resolution, 25% via shareholder SR. 1-year cooling period. No buyback if default subsisting. SEBI SAST implications if listed | 🔴 **GAP** — No dedicated template. Research mode covers buyback rules. SAST implication analysis accessible via SEBI research block |
| **EGM** — S.100–101 | Any member holding 10%+ can requisition EGM. Company must call within 45 days of requisition. NCLT can order EGM if impossible to call otherwise | ✅ **LIVE** — **EGM Notice & Agenda** drafting template. AI includes S.100 requisition law, 21-day notice, quorum, and voting rules |
| **Key Managerial Personnel Changes** — S.203, MR-1/MR-2 | MD/WTD/CEO/CFO/CS appointments and changes: Board + (sometimes) SR. MR-1 (appointment) within 60 days. MR-2 (consent). Terms of appointment disclosed | 🔴 **GAP** — No dedicated KMP appointment/resignation template. Research mode explains S.203 obligations. Board resolution template covers resolution text when prompted but no dedicated KMP workflow |

---

## DOMAIN C — Board Governance

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Board Resolution Library** | Comprehensive, accurate, company-type-specific resolutions for all routine and triggered situations. CS can produce a certified extract from any resolution | ✅ **LIVE** — 10 board resolution templates: RPT (S.188), Director Appointment, Director Resignation, Share Allotment, Bank Account, Borrowing Powers (S.180), Registered Office Change, Investment/Loan/Guarantee (S.186), General Authority, Miscellaneous. Each includes certified extract format with CS signature block |
| **Ordinary vs. Special Resolution Classification** | SR required for: name change, MOA alteration, capital reduction, buyback beyond 10%, RPT at threshold, certain auditor appointments. MGT-14 filing for SRs within 30 days | 🟡 **PARTIAL** — AI correctly identifies SR vs OR in research mode. Draft templates include the appropriate "special/ordinary resolution" heading. No standalone SR/OR classification checker tool |
| **Board Committees** — S.177–178 | Audit Committee: mandatory for listed + S.177 threshold companies. NRC: mandatory for listed. SRC: mandatory for listed + threshold companies. CSR Committee: S.135 companies. Risk Management Committee: LODR Reg 21. Each: composition rules, terms of reference | 🟡 **PARTIAL** — AI explains committee composition requirements in research mode. LODR Reg 17–21 committee rules in SYSTEM_CORPORATE. No dedicated Board Resolution templates specifically for Committee constitution/terms of reference or Board Evaluation |
| **Independent Directors** — S.149, Schedule IV | Eligibility criteria, declaration of independence, re-appointment (max 2 consecutive terms of 5 years). Letter of appointment, D&O responsibilities. IEPF registration for listed companies | 🔴 **GAP** — No independent director-specific template (letter of appointment, independence declaration, IEPF data bank compliance). Research mode answers eligibility questions. A gap for listed company clients |
| **Minutes & Record-Keeping** — S.118 | Board minutes within 30 days of meeting. Signed by Chairman. Permanent record. Minutes presumed correct (S.118(8)). MGT-15 for GM minutes | 🔴 **GAP** — No minutes drafting template. AI can draft minutes if prompted in free-form but there is no structured template. Significant gap for CS/compliance officer audience |

---

## DOMAIN D — SEBI: Listed Company Ongoing Compliance (LODR 2015)

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Quarterly Financial Results** — Reg 33 LODR | Within 45 days of quarter end (Q1–Q3); within 60 days for Q4/full year. Format prescribed by SEBI. Simultaneous submission to exchange and publishing on website | 🟡 **PARTIAL** — Compliance calendar for Listed company type includes SEBI quarterly filings. AI handles research queries on Reg 33 deadlines, format, and consequences of default. No drafting template for the results announcement or Board resolution authorising results |
| **Corporate Governance Report** — Reg 27 | Within 21 days of each quarter end. Disclosure of board composition, committee details, GM details, RPT, penalties. Annual CG Report in Annual Report | 🟡 **PARTIAL** — Compliance calendar includes CG Report deadline. Research mode explains Reg 27 requirements. No drafting template for the CG Report itself |
| **Shareholding Pattern** — Reg 31 | Within 15 days of end of each quarter. Promoter/public/institution breakdown. Encumbrance disclosure | 🔵 **PHASE 3** — Compliance calendar includes this. Research mode covers rules. No template; Phase 3 client portal would enable structured tracking |
| **Continuous Disclosure — Reg 30 (UPSI / Material Events)** | Immediate disclosure of material events/UPSI: results, M&A, regulatory action, change in director/KMP, fraud, default, litigations. Within 24 hours of occurrence | 🟡 **PARTIAL** — SYSTEM_CORPORATE covers Reg 30 in SEBI block. AI can draft Reg 30 disclosure text if prompted. No dedicated template for stock exchange intimation letter. UPSI definition, materiality test, and timing analysis well covered in research mode |
| **Insider Trading Compliance Programme (ITCP)** — PIT Reg 9 | Mandatory for listed companies: Code of Fair Disclosure, Code of Conduct for employees. Trading window closure procedures, pre-clearance system, SDD (Structured Digital Database), UPSI sharing log, annual report disclosure | 🔴 **GAP** — SYSTEM_CORPORATE covers insider trading *enforcement defence* thoroughly (SCN reply, SAT appeal). But the **compliance side** — setting up and maintaining an ITCP, Code of Conduct drafting, SDD guidance, trading window policy — is not covered. Very high-demand for listed company in-house teams |
| **Board Composition** — Reg 17 | Min 6 directors; 50% non-executive; 1/3 independent (1/2 if executive chairman). At least 1 woman director. Non-executive chair preferred | 🟡 **PARTIAL** — Reg 17 composition rules are in SYSTEM_CORPORATE and AI correctly applies them in research queries. No composition audit tool or readiness checklist |
| **Related Party Transactions — Reg 23 LODR** | Audit committee pre-approval for all RPTs. Material RPT: shareholder approval (only non-related parties vote). Quarterly submission to audit committee. Annual disclosure in Annual Report | ✅ **LIVE** — Board Resolution RPT template includes Reg 23 audit committee reference. AI explains materiality threshold and voting restriction in research mode |
| **Annual Report — LODR** | Submission within 21 working days of AGM. Includes CG Report, Business Responsibility and Sustainability Report (BRSR — mandatory for top 1,000 listed companies by market cap), Directors' Report (LODR-enhanced), financials | 🟡 **PARTIAL** — Directors' Report template covers LODR-required disclosures. **BRSR is a gap** — it is a 100+ indicator ESG report and a new high-demand requirement for large listed companies |

---

## DOMAIN E — SEBI: Capital Market Transactions

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Insider Trading Defence** — PIT Regs 2015 | SCN reply: establish non-UPSI, timing disconnect, no nexus. SAT Appeal. Trading plan defence (Reg 5). Legitimate purpose / connected person challenge | ✅ **LIVE** — Highly detailed in SYSTEM_CORPORATE. UPSI definition, all defences, SCN reply template, SAT Appeal template. 5 anchor SC/SAT cases with [REF] tags. One of the strongest parts of the module |
| **SAST / Takeover Code 2011** | Open offer trigger: 25% acquisition or 5% annual change for 25%+ holders. Open offer: 26% of total shares at Reg 8 price. Creeping acquisition exemption. Reg 10 exemptions | ✅ **LIVE** — SAST covered in SYSTEM_CORPORATE with trigger thresholds, open offer pricing, creeping acquisition. Research mode handles takeover structuring queries |
| **ICDR — Capital Raising** | IPO, FPO, rights issue, preferential allotment — SEBI ICDR Regulations 2018. Lock-in periods, pricing formula, disclosure requirements, basis of allotment | 🟡 **PARTIAL** — ICDR covered in general sense in research mode. No dedicated ICDR template for offer documents or pre-IPO Board resolutions. A deeper ICDR specialist block would be needed for capital markets boutiques |
| **SEBI SCN Reply** | Adjudication proceedings: S.15-I SEBI Act (penalty by AO), WTM proceedings. Reply structured para-wise, limitation argument, mitigation submissions | ✅ **LIVE** — Dedicated **SEBI SCN Reply** template. Para-wise reply, limitation (3-year bar), hearing request, prayer menu. Covers PIT, SAST, and LODR violations |
| **SAT Appeal** — S.15T SEBI Act | Filed within 45 days of AO/Board order. Grounds: error of law, NJ violation, perverse findings, disproportionate penalty. Stay application | ✅ **LIVE** — Dedicated **SAT Appeal** template with complete grounds structure and stay prayer |

---

## DOMAIN F — IBC 2016: Insolvency Proceedings

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **CIRP — S.7 Financial Creditor** | Minimum default ₹1 Cr. Form 1 + affidavit + documents. Moratorium (S.14), IRP appointment, CIRP 180/330-day timeline, CoC formation, resolution plan (66%+ approval), liquidation | ✅ **LIVE** — Dedicated **IBC S.7 Application** template with 4-Part Form 1 structure, NPA/default averments, IRP details, S.14 moratorium prayer. Swiss Ribbons / Essar Steel / Innoventive cited with [REF] tags |
| **CIRP — S.9 Operational Creditor** | ₹1 Cr minimum. 10-day demand notice (S.8). Form 5 five-part structure. Mobilox pre-existing dispute test. IRP nomination | ✅ **LIVE** — Dedicated **IBC S.9 Application** template with complete demand-notice chain, Mobilox averment, Form 5 structure |
| **S.12A Withdrawal** | 90% CoC approval + NCLT sanction. Settlement before information memorandum (IM) issued. Form FA application to NCLT. Post-IM: SC intervention required | 🟡 **PARTIAL** — S.12A procedure, 90% threshold, pre-IM timing are in SYSTEM_CORPORATE. Research mode only; no dedicated S.12A Application drafting template |
| **Pre-Pack Insolvency (PPIRP)** — S.54A, Chapter IIIA | MSMEs only (paid-up ≤ ₹25 Cr, turnover ≤ ₹250 Cr). Base plan submitted before NCLT. 90-day timeline. IRP + existing management. Faster and cheaper than CIRP | 🟡 **PARTIAL** — PPIRP covered in SYSTEM_CORPORATE research block. No dedicated PPIRP application drafting template. Gap given the MSME client base for many corporate advocates |
| **Avoidance Applications** — S.43–66 | Preferential transactions (S.43 — look-back 1 year/2 years for related party), undervalue transactions (S.45), extortionate credit (S.50), fraudulent/wrongful trading (S.66). Filed by Resolution Professional against ex-management | 🔴 **GAP** — SYSTEM_CORPORATE does not have a dedicated avoidance applications block. Look-back periods, burden of proof, and relief structure are not in the specialist prompts. Increasingly important as CIRP matures in India |
| **Liquidation** — S.33+ | NCLT order → Liquidator appointed. Secured creditor opt-out (S.52). S.53 waterfall: CIRP costs → secured → workmen (24M) → other employees (12M) → unsecured → govt → residue. Schedule 1 asset sale process | ✅ **LIVE** — S.53 liquidation waterfall explicitly in SYSTEM_CORPORATE. Research mode handles liquidation queries, secured creditor strategy, priority disputes |
| **Personal Guarantee Insolvency** — S.95–100 IBC | Application by creditor against personal guarantor of corporate debtor. Separate proceedings. SC upheld in Surendra B. Jiwrajka (2023). Moratorium for guarantor | 🟡 **PARTIAL** — S.95 mentioned in SYSTEM_CORPORATE. Research mode handles queries. No dedicated S.95 Application drafting template — a gap given recent SC ruling increased personal guarantee proceedings significantly |
| **Cross-Border Insolvency** | S.234/235 IBC (bilateral agreements — no agreement yet in force). UNCITRAL Model Law (Chapter IV IBC, not yet notified). Practical approach: HC letters rogatory | 🔴 **GAP** — Not in SYSTEM_CORPORATE. Research queries about cross-border insolvency would not get specialist depth |

---

## DOMAIN G — FEMA / Cross-Border Transactions

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **FDI Compliance — Inbound** | FCGPR filing within 30 days of allotment. Pricing at FMV (FEMA OI Rules 2022 / Rule 21). Sectoral caps (automatic vs approval route). Downstream investment rules. Annual return on foreign liabilities (FLA — by 15 Jul) | ✅ **LIVE** — FEMA block covers FDI: automatic vs approval route, FCGPR timing, OI Rules 2022 pricing. FLA annual return: not a dedicated template (RBI form out of scope by design) |
| **ODI — Outbound Investment** | OI Rules 2022: step-down subsidiary rules, financial commitment cap (400% of net worth). RBI approval for certain structures. Annual performance reports | 🟡 **PARTIAL** — FEMA block mentions ODI in research context. No dedicated ODI compliance template or financial commitment calculator |
| **ECB — External Commercial Borrowings** | All-in-cost ceiling by tenure. Automatic route (by amount, borrower, end-use) vs approval route. EBRC reporting. End-use restrictions (no real estate/equity). Refinancing limits | 🟡 **PARTIAL** — ECB covered in FEMA research block. All-in-cost ceilings and automatic/approval route distinction explained. No ECB agreement drafting template |
| **FEMA Compounding — S.15** | Online portal only from 1 June 2026. Application to RBI Compounding Authority (regional office). Four parts: facts, violation, mitigating factors, undertaking. Expected compounding amount formula | ✅ **LIVE** — Dedicated **FEMA Compounding Application** template with four-part structure, specific FEMA regulation citation, regularisation steps, undertaking clause. SYSTEM_CORPORATE includes 1 June 2026 online-portal update |
| **ED / FEMA SCN Reply** | Preliminary objections: vagueness, S.16(4) 2-year limitation. Para-wise reply. Defences: permissible transaction, AD bank compliance, RBI Master Direction permits, compounding closure. PMLA separation argument | ✅ **LIVE** — Dedicated **ED FEMA SCN Reply** template covering all standard defences and limitation arguments |
| **Transfer of Shares (FCTRS)** | Between resident and non-resident: FCTRS within 60 days of receipt of funds or transfer. Pricing: sale at ≥ FMV for resident selling; ≤ FMV for resident buying | 🟡 **PARTIAL** — Research mode covers FCTRS rules. No dedicated FCTRS compliance checklist or Board Resolution template for the share transfer |
| **FEMA Compounding — June 2026 update** | From 1 June 2026: exclusively online portal. Physical submissions no longer accepted. CA certificate required | ✅ **LIVE** — SYSTEM_CORPORATE explicitly includes the June 2026 change. Current and accurate |

---

## DOMAIN H — ED / PMLA Defence

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Predicate Offence Analysis** | PMLA attaches only if predicate offence exists (Schedule to PMLA). Challenge: dispute predicate or show quashed/acquitted. If predicate quashed → attachment order falls | ✅ **LIVE** — Predicate offence analysis explicitly in SYSTEM_CORPORATE ED block. Key defence: predicate offence challenge as primary strategy |
| **Provisional Attachment — S.5 PMLA** | PA Order → Adjudicating Authority confirmation within 180 days → PMLA Appellate Tribunal → HC. Independent inquiry by AA. Burden on ED to establish PoC link | 🟡 **PARTIAL** — Attachment challenge process in research mode. No dedicated Attachment Challenge Application drafting template |
| **Bail — S.45 PMLA Twin Conditions** | (a) Reasonable grounds not guilty; (b) not likely to commit further offence. Stringent threshold. HC jurisdiction available. SC has modified but twin conditions survive | ✅ **LIVE** — S.45 bail conditions covered in SYSTEM_CORPORATE. Research mode provides detailed analysis of twin conditions and SC developments |
| **ED SCN Reply** | Para-wise reply to each allegation, establish legitimate source of funds, challenge PoC nexus, predicate offence link, limitation | ✅ **LIVE** — Dedicated **ED SCN Reply** template. Covers all standard defences |
| **PMLA Appellate Tribunal** | Appeal from AA order. Limited grounds. Deposit requirement. PMLA AT order challengeable before HC under S.26 PMLA | 🔴 **GAP** — No dedicated PMLA AT Appeal template. Research mode covers the process |

---

## DOMAIN I — NCLT Litigation

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Oppression & Mismanagement** — S.241–242 | Locus: S.244 (10% threshold or 100 members). "Oppressive" standard. Relief: share purchase, director removal, winding up (last resort), injunction. Consent orders don't bar fresh claims | ✅ **LIVE** — Dedicated **NCLT Company Petition (S.241–242)** template. Shanti Prasad Jain [UNCERTAIN] cited. SYSTEM_CORPORATE covers S.244 locus, S.242 relief menu, interim relief under Rule 54 |
| **Class Action** — S.245 | Members (≥100 or 10%) or depositors may sue company/directors/auditors/experts for acts prejudicial to members. NCLT can award damages or injunction | 🟡 **PARTIAL** — Class action mentioned in research coverage. No dedicated S.245 Petition template |
| **Winding Up** — S.271–272 | Grounds: inability to pay debts, special resolution, just and equitable. NCLT triggers liquidation. Creditor's winding up petition vs company petition. Company Liquidator appointment | 🟡 **PARTIAL** — Winding up covered in research mode. No dedicated winding-up petition template. IBC S.7/S.9 is preferred route (fully covered) but just-and-equitable winding up still used |
| **Scheme of Arrangement** — S.230–232 | 3/4 majority approval by class. NCLT approval binds all. Two NCLT hearings. ROC / creditor objections. Listed company: SEBI comment required | 🟡 **PARTIAL** — S.230–233 merger framework in SYSTEM_CORPORATE. No Scheme Petition drafting template. Major CA practice area — a significant template gap |
| **Fast-Track Merger** — S.233 | Holding-subsidiary or two small companies. No NCLT approval; ROC filing only. Declaration of solvency + auditors' report | 🔴 **GAP** — S.233 mentioned in research knowledge but no dedicated S.233 fast-track merger application or Board resolution template. High-demand for holding-subsidiary restructures |
| **Cross-Border Merger** — S.234 + FEMA OI Rules | Inbound/outbound. RBI approval + NCLT approval. S.234 + FEMA OI Rules 2022 | 🔴 **GAP** — S.234 in research knowledge but no template |

---

## DOMAIN J — Regulatory Intelligence & Monitoring

| Compliance Aspect | Industry Standard — What It Entails | How /corporate Manages It |
|---|---|---|
| **Live Regulatory Feed** | Real-time/near-real-time alerts on SEBI circulars, MCA notifications, IBBI amendments, RBI guidelines. High-priority flagging for deadline changes and penalty increases | 🔵 **PHASE 2** — Architecture fully designed (6 RSS feeds confirmed live, Supabase `regulatory_updates` table schema, cron architecture). UI already built in corporate.html (filter strip, reg item cards, high-priority badge). Not yet connected — backend functions not yet built |
| **Personalised Compliance Calendar** | Deadlines auto-generated from company profile (type, AGM date, FY end). Customisable with matter-specific deadlines. Reminder emails/WhatsApp | ✅ **LIVE (static)** — Auto-generated in corporate.html by company type (Private/Listed/LLP/OPC). Shows AGM, ROC, DIR-3, board meetings, SEBI deadlines. 🔵 **PHASE 3** — Personalised by actual company AGM date + automated email/WA reminders |
| **High-Priority Regulatory Alerts** | Email alert when high-priority regulatory update (deadline extension, new circular, penalty change) arrives | 🔵 **PHASE 2** — Designed: Resend email to corporate subscribers for `is_high_priority` feed items. Not yet live |
| **eCourts / NCLT Case Tracking** | Live case status for NCLT/NCLAT/SAT matters. Hearing date alerts | 🔴 **GAP** — Not in scope currently. Noted in Advocate module backlog. Would require NCLT/NCLAT case number tracking per matter |

---

## DOMAIN K — Out-of-Scope Domains (By Design)

| Domain | What It Entails | /corporate Status |
|---|---|---|
| **M&A — Transaction Structuring** | SPA/SHA drafting, due diligence checklists, representations & warranties, conditions precedent, indemnity mechanics | ⚫ **OUT OF SCOPE** — NCLT merger approval (S.232) is in scope; M&A transaction document drafting is not. Rationale: requires deep deal-specific facts; typically handled by Tier 1 firms |
| **Competition Law / CCI** | Combination filings (merger clearance — mandatory if thresholds met), anti-competitive agreements (S.3), abuse of dominance (S.4), CCI investigation defence | ⚫ **OUT OF SCOPE** — Distinct specialist area. Gap for clients where SEBI + CCI clearance is needed simultaneously (e.g., open offers) |
| **Direct Taxation (IT Act)** | Corporate tax planning, transfer pricing (S.92–92F), MAT, advance pricing agreements, tax litigation (CIT appeals, ITAT) | ⚫ **OUT OF SCOPE** — Requires accounting data and CA expertise |
| **GST / Indirect Taxation** | GST compliance, GSTAT appeals, anti-profiteering, customs | ⚫ **OUT OF SCOPE** |
| **Intellectual Property** | Trademark registration, patent prosecution, IP licensing, copyright infringement | ⚫ **OUT OF SCOPE** |
| **Insurance / IRDAI** | IRDAI product approval, insurance company compliance, policyholder litigation | ⚫ **OUT OF SCOPE** |
| **Banking Regulation Act / RBI Supervision** | Banking licence conditions, PCA framework, RBI inspection responses, NBFC registration | ⚫ **OUT OF SCOPE** — RBI banking *supervision* excluded. Note: FEMA compounding (which involves RBI) is in scope |
| **Labour & Employment (corporate context)** | POSH committee, Factories Act compliance, PF/ESI, Works Committees, retrenchment compliance | ⚫ **OUT OF SCOPE** |
| **Environmental Compliance** | EIA clearance, NGT proceedings, pollution consent, CPCB compliance | ⚫ **OUT OF SCOPE** |
| **International Arbitration (UNCITRAL/ICC)** | Seat of arbitration, institutional rules, enforcement of foreign awards under NY Convention | ⚫ **OUT OF SCOPE** — Domestic arbitration (Commercial Courts Act) is in scope |
| **DPDP 2023 / Data Privacy (Corporate)** | Data Fiduciary obligations, consent architecture, breach notification to DPBI, cross-border data transfer restrictions, children's data rules | 🔴 **GAP** — DPDP is live in the Advocate/Citizen module (May 2026). For corporate clients (who are Data Fiduciaries), DPDP compliance is a fast-growing practice area not yet in SYSTEM_CORPORATE |
| **NBFC / Fintech Regulatory Compliance** | RBI Master Directions for NBFCs, fair practices code, KYC/AML programme, digital lending guidelines (Sep 2022), co-lending, FLDG norms | 🔴 **GAP** — Very high demand. The IH demo persona is a Fintech company (IndiaFirst Fintech). Not in SYSTEM_CORPORATE. Significant gap for in-house counsel mode |

---

## Summary Scorecard

| Domain | Templates | Research Depth | Compliance Calendar | Overall |
|---|---|---|---|---|
| Companies Act — Annual | 🟡 Partial | ✅ Strong | ✅ Live | 🟡 Medium — CSR, statutory registers missing |
| Companies Act — Event-Based | 🟡 Partial | ✅ Strong | ✅ Live | 🟡 Medium — Charges, KMP, buyback templates missing |
| Board Governance | ✅ Strong | ✅ Strong | 🔵 Phase 3 | 🟡 Medium — Minutes, ID appointment, committee resolutions missing |
| SEBI LODR (ongoing) | 🟡 Partial | ✅ Strong | ✅ Live | 🔴 High gap — ITCP/Code of Conduct, BRSR, Reg 30 intimation missing |
| SEBI Capital Markets | ✅ Strong | ✅ Strong | n/a | ✅ Well covered |
| IBC / Insolvency | 🟡 Partial | ✅ Strong | n/a | 🟡 Medium — S.12A, S.95, PPIRP, avoidance apps missing |
| FEMA / Cross-Border | ✅ Strong | ✅ Strong | n/a | ✅ Well covered |
| ED / PMLA | ✅ Strong | ✅ Strong | n/a | ✅ Well covered — PMLA AT Appeal template missing |
| NCLT Litigation | 🟡 Partial | ✅ Strong | n/a | 🟡 Medium — Winding-up, S.233, Scheme petitions missing |
| Regulatory Intelligence | ⬜ Built, not live | n/a | ✅ Static live | 🔵 Phase 2 is the product differentiator |
| DPDP (corporate) | ⬜ Not in module | ⬜ | ⬜ | 🔴 Growing demand, easy add |
| NBFC / Fintech | ⬜ Not in module | ⬜ | ⬜ | 🔴 IH demo is Fintech; gap is stark |
| M&A Transactions | ⚫ By design | ⚫ | ⚫ | Intentional exclusion |
| Tax / CCI / IP / Labour | ⚫ By design | ⚫ | ⚫ | Intentional exclusion |

---

## Top 5 High-Priority Gaps to Address

| Priority | Gap | Why It Matters | Effort |
|---|---|---|---|
| **P1** | **Insider Trading Compliance Programme (ITCP)** — Code of Conduct, SDD guidance, trading window policy drafting | Every listed company client needs this. Currently strong on enforcement defence but not on the compliance programme that *prevents* enforcement. Huge in-house counsel use case | Medium — 1 specialist block in SYSTEM_CORPORATE + 2 drafting templates (Code of Conduct, SDD policy) |
| **P2** | **Phase 2 Regulatory Feed going live** | Compliance calendar + RSS feed is the core product differentiator. Currently calendar is static (hardcoded deadlines). Live RSS + email alerts = primary reason to maintain the subscription | High — `regulatory-feed-cron.js`, `regulatory-feed.js`, Supabase `regulatory_updates` table |
| **P3** | **DPDP Rules 2025 for Corporate Data Fiduciaries** | Already built in the main platform (May 2026). One DPDP specialist block in SYSTEM_CORPORATE covers consent framework, DPBI breach notification, cross-border transfer rules. Hot new practice area | Low — ~2 hours. Copy/adapt DPDP block from SYSTEM_ADVOCATE into SYSTEM_CORPORATE |
| **P4** | **NBFC / Fintech RBI compliance block** | The in-house counsel demo persona is a Fintech company. RBI Master Directions for NBFCs, digital lending guidelines, co-lending norms are entirely absent. Many of our target corporate users are Fintech / NBFC in-house teams | Medium — 1 new specialist block in SYSTEM_CORPORATE covering NBFC licence, digital lending, KYC/AML, co-lending norms |
| **P5** | **Missing NCLT templates: S.233 Fast-Track Merger, Winding-Up Petition, Avoidance Application** | S.233 fast-track is heavily used for holding-subsidiary restructures. Winding-up petitions still filed (just-and-equitable ground). Avoidance applications are increasingly filed as IBC matures | Low-medium — 3 additional drafting templates to add to the existing SYSTEM_CORPORATE drafting block |

---

## Complete Template Inventory (Phase 1 — LIVE)

### Litigation & Enforcement (8 templates)
1. NCLT Company Petition — Oppression & Mismanagement (S.241–242 CA 2013)
2. NCLAT Appeal (S.61 IBC / S.421 CA 2013)
3. IBC Section 7 Application — Financial Creditor
4. IBC Section 9 Application — Operational Creditor
5. SAT Appeal — Section 15T SEBI Act
6. Reply to SEBI Show Cause Notice
7. FEMA Compounding Application — Section 15 FEMA 1999
8. Reply to ED Show Cause Notice — FEMA

### Compliance Documents (15 templates)
9. Board Resolution: RPT (S.188)
10. Board Resolution: Director Appointment
11. Board Resolution: Director Resignation
12. Board Resolution: Share Allotment
13. Board Resolution: Bank Account
14. Board Resolution: Borrowing Powers (S.180)
15. Board Resolution: Registered Office Change
16. Board Resolution: Investment/Loan/Guarantee (S.186)
17. Board Resolution: General Authority
18. Board Resolution: Miscellaneous
19. AGM Notice & Agenda
20. EGM Notice & Agenda
21. Directors' Report (key disclosures)
22. Secretarial Audit Observation Response
23. Directors' Responsibility Statement

**Total: 23 templates**

---

*All AI-generated research and drafts must be reviewed by a qualified senior advocate before filing or use. This coverage map reflects the state of the /corporate module as of 2026-05-27.*


---

## Source: notebooklm-corporate-demo-prompt.md

# NotebookLM — Corporate Demo Video Script Prompt

## HOW TO USE THIS FILE

1. Open NotebookLM at [notebooklm.google.com](https://notebooklm.google.com)
2. Create a new notebook titled **"Nyaya Saathi Pro — Corporate Demo"**
3. **Upload sources:**
   - Upload this file (`notebooklm-corporate-demo-prompt.md`) as a source
   - Upload all 9 screenshots from `documentation/screenshots/` as image sources
     (upload in order: 01 through 09)
4. Once sources are indexed, paste the **QUERY** at the bottom into the chat
5. Ask it to generate the **Audio Overview** for a podcast-style walkthrough

---

## SOURCE DOCUMENT — Product Brief

### Product: Nyaya Saathi Pro — Corporate Intelligence Panel
**URL:** legalaidai.in/corporate  
**Target users:** Corporate lawyers, in-house counsel, company secretaries, law firms handling NCLT/SEBI/IBC matters  
**Platform:** Browser-based SPA (Single Page Application), desktop-first  
**Pricing:** ₹2,950/month (M1 — 200 AI units) · ₹5,900/month (M2+ — 300 AI units)

---

### What Makes It Unique

Nyaya Saathi Pro Corporate is an AI-powered legal intelligence workspace built specifically for Indian corporate law. It is the **only tool that combines:**

1. **Litigation & Enforcement defence** — NCLT, NCLAT, IBC, SEBI/SAT, FEMA, ED/PMLA
2. **Companies Act 2013 annual compliance calendar** — auto-generated per company type
3. **Indian Kanoon RAG** — real-time case law retrieval from India's largest legal database
4. **CREAC-structured AI output** — every research answer follows the 5-section legal writing standard (Conclusion → Rule → Explanation → Application → Counter-arguments)
5. **23 court-ready templates** — from NCLT O&M petitions to Board Resolutions to AGM notices
6. **Live regulatory feed** — SEBI, RBI, MCA, IBC, court updates every 6 hours

All client data stays in the user's browser (localStorage) — nothing is uploaded to our servers. The AI engine runs on Claude Sonnet via a secure Netlify function.

---

### The 5 Screens

#### Screen 1 — Portfolio Home (Screenshot 01 & 08-dark)
The landing screen after login. Shows:
- **4 headline stats:** Total Clients · Active Matters · Overdue Filings · Active Enforcement
- **⚡ Deadline Radar:** The most important widget — 4 urgency zones side by side:
  - OVERDUE (red) — filings already past deadline, shown with client name + form
  - < 7 DAYS (amber) — critical this week
  - < 30 DAYS (blue) — due this month
  - UPCOMING (green) — on the horizon
  - Each chip is clickable. "View full calendar →" link at top right
- **My Clients grid:** 2-column layout. Each card shows company name, CIN, company type badge, sector tag, active matter count, city, and a colour-coded urgency indicator. Cards for: Agarwal Synthetics (textiles/NCLT), TechNova Solutions (IT/SEBI enforcement), Bharat Green Energy (LLP/FEMA), Meridian Healthcare (pharma/oppression), Paramount Infra (real estate/RERA), IndiaFirst Fintech (fintech/RBI)
- **Right panel:** Upcoming Deadlines list with calendar date-boxes + Regulatory Highlights feed
- **Sidebar:** Units bar (84/200 used), user name, My Clients nav active

Dark mode (Screenshot 08): Warm near-black background (#0F0F0F), amber accents throughout, Deadline Radar zones use rich tinted dark backgrounds, client cards legible with amber "Open →" links.

---

#### Screen 2 — Company Dashboard (Screenshot 02 & 09-dark)
Opened by clicking any client card. Shows the full profile of one company — here: **Agarwal Synthetics Pvt Ltd** (Private Ltd, textiles, New Delhi, CIN: U17291DL2008PTC178234, incorporated 2008).

- **Breadcrumb:** My Clients / Agarwal Synthetics
- **Company header card:** Company name in Crimson Pro serif, CIN in monospace, type badge (Pvt Ltd), city, incorporation date
- **Alert banner:** Amber dismissible banner — "1 overdue filing for Agarwal Synthetics — action required"
- **Compliance Health widget:** Canvas donut chart — 7/8 filings tracked. Segments: Overdue (red, 1), Due soon (amber, 0), Upcoming (blue, 7), On track (green, 0). Legend with counts. "View compliance calendar →" CTA.
- **3 Quick Action tiles:** Research (CREAC analysis + IK RAG) · Draft (23 court-ready templates) · Compliance (Filing calendar + tracker) — click any to open the relevant workspace tab
- **Active Matters list:** 3 matters:
  1. CIRP — Application by Union Bank of India (₹42 Cr NPA) — litigation · NCLT · active [red left border]
  2. Interim Moratorium — Supply Chain Creditors (S.14 IBC) — litigation · NCLT · active [red left border]
  3. Restructuring Advisory — Pre-Pack Settlement — advisory · NCLT · active [blue left border]
  Each matter card has an "Open →" link to the Matter Detail screen.
- **Right panel:** "At a Glance" stats card (Active Matters: 3, Overdue: 1, Total Filings: 8, Next: DPT-3 Deposit Return 30 Jun) + Recent Sessions (empty on first use)
- **Sidebar:** Company context card shows Agarwal Synthetics + CIN + Pvt Ltd badge. Nav: Dashboard (active), Compliance Calendar, Research, Draft, Regulatory Updates

---

#### Screen 3 — Compliance Calendar (Screenshot 03)
Opened via "Compliance Calendar" nav item or "View compliance calendar →" link. Full-screen calendar for **Agarwal Synthetics**.

- **Title:** "Agarwal Synthetics — Compliance Calendar · FY 2025–26 · Pvt Ltd Company"
- **4 urgency stat cards** (clickable filters): Overdue (1, red) · Due This Month (0, amber) · Upcoming (7, blue) · Completed (0, green)
- **Monthly bar chart** — "Deadline Distribution — FY 2025-26": 12 columns Apr→Mar with deadline counts. Current month (May) highlighted. Click a bar to filter rows to that month.
- **Filter chips:** All · Pending · Overdue · Done · MCA · SEBI · RBI
- **Filing rows** — each row has:
  - **fi-cal date-box** (large day number + month abbreviation in a square widget — e.g., "30 SEP", "29 NOV", "15 OCT")
  - Form name + description
  - Category tag (MCA / SEBI / RBI)
  - Status badge (Upcoming / Overdue / Done)
  - **✍ Draft →** button — clicking this opens the Workspace Draft tab with the relevant template pre-selected. This is the key workflow connector.
  - Filings shown: AOC-4 (Financial Statements) · MGT-7A (Annual Return) · ADT-1 (Auditor Appointment) · AGM (Annual General Meeting) · and more below the fold

---

#### Screen 4 — Matter Detail (Screenshot 04)
Opened by clicking "Open →" on any matter card. Shows: **CIRP — Application by Union Bank of India (₹42 Cr NPA)**

- **Breadcrumb:** My Clients / Agarwal Synthetics / CIRP — Application by Union Bank of India (₹42 Cr NPA)
- **Matter header card:** Red urgency bar at top. Matter title in large Crimson Pro. Badges: litigation · active. Deadline display (right side).
- **3 Quick Action buttons:** 🔍 Research this matter · ✍️ Draft document · 📡 Regulatory updates — each opens the Workspace with context pre-set to this matter
- **Matter Sessions panel** (left): "No sessions yet — start researching or drafting above." — fills with AI session history as the user works the matter
- **Matter Details panel** (right): Practice Area: NCLT · Status: active · Next Deadline: — · Assigned To: —

---

#### Screen 5 — Workspace: Research Tab (Screenshot 05)
The AI research interface. Context: Agarwal Synthetics.

- **Title:** "Workspace — Agarwal Synthetics · CREAC legal analysis with Indian Kanoon RAG"
- **3 tabs:** Research (active) · Draft · Updates
- **Context strip:** Company (Agarwal Synthetics, pre-filled, non-editable) · Matter (dropdown: General/no matter or specific matter) · Practice Area (dropdown: NCLT/IBC/SEBI/FEMA/General Corporate) · Citation Standard (Indian Law AIR/SCC)
- **Query box:** Large textarea, 800-char limit, counter shown (0/800). Placeholder: "Ask a legal question — e.g., 'What are the grounds for oppression and mismanagement under S.241 Companies Act 2013?'"
- **Research ↗ button** (blue, right)
- **Output area:** Empty on first load ("Ask a research question above to get a structured CREAC analysis with verified precedents"). On use: renders 5-section CREAC output (Conclusion → Rule → Explanation → Application → Counter-arguments) with clickable Indian Kanoon case links.

---

#### Screen 6 — Workspace: Draft Tab (Screenshot 06)
23 court-ready templates in 3 groups, 3-column grid, each tile shows icon + name + subtitle.

**Group 1 — ⚖ Litigation & Enforcement (8 templates):**
- NCLT — O&M Petition (S.241–242 · Oppression)
- NCLAT Appeal (S.421 · Appellate)
- IBC S.7 — Fin. Creditor (Insolvency · NCLT)
- IBC S.9 — Op. Creditor (Insolvency · NCLT)
- IBC S.12A — Withdrawal (CIRP Withdrawal)
- SEBI SCN Reply (Enforcement Defence)
- FEMA Compounding (RBI · S.15 FEMA)
- ED / PMLA SCN Reply (Enforcement · ED)

**Group 2 — 📋 Board & Governance (9 templates):**
- Board Res — RPT (S.188 · Related Party)
- Board Res — Director (Appointment · S.152)
- Board Res — Borrowing (S.180 · Financial)
- Board Res — Share Allotment (Corporate · Equity)
- Board Res — Investment (S.186 · Investment)
- AGM — Resolutions (Ordinary & Special)
- Directors' Report (S.134 · CA 2013)
- CG Report (SEBI LODR · Quarterly)
- SHA / Investment Agmt (Framework)

**Group 3 — 📜 Compliance Documents (6 templates):** (visible on scroll)
- AGM Notice & Agenda · MGT-7A (Annual Return) · AOC-4 (Financial Stmts) · MSME Form I · DIR-3 KYC · BEN-2 Beneficial Owner

Clicking any template pre-fills the query area and runs the AI draft.

---

#### Screen 7 — Workspace: Regulatory Updates Tab (Screenshot 07)
Live feed of regulatory changes. Context: Agarwal Synthetics.

- **Title:** "Workspace — Agarwal Synthetics · Live regulatory feed — SEBI / MCA / RBI / IBC"
- **Filter pills:** All (active, blue) · RBI · SEBI · MCA · IBC · Court
- **Feed cards** (colour-coded category badges):
  - IBC (purple): IBBI amends Insolvency Resolution Process for Corporate Persons Regulations — pre-packaged CIRP timelines revised (15 May 2026)
  - SEBI (blue): SEBI tightens RPT disclosure norms under LODR — material threshold revised to ₹100 crore or 5% of turnover (12 May 2026)
  - MCA (amber): MCA notifies Companies (Significant Beneficial Ownership) Amendment Rules 2026 — BEN-2 filing timeline extended (8 May 2026)
  - RBI (green): RBI circular on External Commercial Borrowings — revised framework for eligible borrowers and end-use restrictions (5 May 2026)
  - Court (grey): NCLT (Amendment) Rules 2026 — e-filing mandatory for all company law petitions from 1 June 2026 (30 Apr 2026)
  - SEBI: SEBI issues consultation paper on AI governance for listed companies — board-level AI risk oversight framework proposed (25 Apr 2026)

Feed is populated every 6 hours via a cron function pulling from 6 RSS sources: RBI notifications, RBI press releases, Bar & Bench, Google News SEBI/MCA/IBC aggregates.

---

### Key Differentiators for the Script

1. **One platform, two worlds** — litigation defence AND annual compliance in the same workspace. No switching between tools.
2. **Deadline Radar on login** — the first thing you see every morning is which filings need attention today. Zero cognitive load.
3. **Draft → button on every filing** — from the compliance calendar, one click pre-selects the right template and opens the AI drafter. The calendar and drafting tool are directly connected.
4. **Matter-centric workflow** — research, drafting, and sessions are all tied to a specific matter. Nothing gets lost across a portfolio of 6–10 companies.
5. **Indian Kanoon RAG** — citations are pulled live from India's largest case law database, not from a static training dataset. The AI identifies relevant precedents in real time.
6. **CREAC structure** — every research answer follows the Conclusion → Rule → Explanation → Application → Counter-arguments format used by courts. Ready to use in pleadings.
7. **Privacy by design** — client data never leaves the browser. No data upload, no cloud sync.
8. **Regulatory feed** — SEBI circulars, RBI notifications, MCA amendments, court orders — all in one filtered feed, updated every 6 hours.

---

### Workflow Narrative (for narration guide)

**The typical user journey in 5 minutes:**

1. Advocate/in-house counsel logs in → immediately sees **Deadline Radar** — knows exactly what's overdue and what's due this week without clicking anything.
2. Clicks a client card (e.g., Agarwal Synthetics) → sees the **Company Dashboard** — donut chart shows 1 overdue, 7 upcoming. Alert banner calls it out.
3. Clicks "View compliance calendar →" → **Compliance Calendar** shows all 8 filings for the FY, with date-boxes, categories, and Draft buttons.
4. Sees "AOC-4 (Financial Statements) — 30 Sep — Upcoming" → clicks **✍ Draft →** → Workspace opens on Draft tab, AOC-4 template is pre-selected.
5. Or, switches to Research tab → types "What are the grounds for CIRP initiation by a financial creditor under IBC Section 7?" → receives a full CREAC analysis with SC and NCLAT precedents linked to Indian Kanoon.
6. From the Matter Detail screen for the CIRP matter → clicks "Research this matter" → the query box is pre-filled with matter context, saving setup time.
7. Checks Regulatory Updates → sees the new NCLT e-filing rule effective 1 June → knows to act before the deadline.

---

## NOTEBOOKLM QUERY (paste this into the chat box)

```
You are a professional legal tech demo video scriptwriter. Using the product brief and the 9 screenshots provided as sources, write a complete narrated demo video script for Nyaya Saathi Pro — Corporate Intelligence Panel.

The video will use the screenshots as slides in this order:
1. Screenshot 01 — Portfolio Home (light mode)
2. Screenshot 02 — Company Dashboard (light mode)  
3. Screenshot 03 — Compliance Calendar
4. Screenshot 04 — Matter Detail
5. Screenshot 05 — Workspace: Research tab
6. Screenshot 06 — Workspace: Draft tab (templates)
7. Screenshot 07 — Workspace: Regulatory Updates
8. Screenshot 08 — Portfolio Home (dark mode)
9. Screenshot 09 — Company Dashboard (dark mode)

Please produce:

**PART A — Video Script (narration + on-screen callouts)**
For each screenshot, write:
- Narration text (what the presenter says, 30–60 seconds per screen)
- 2–3 on-screen callout labels (text overlays that point to key UI elements)
- A TRANSITION line to the next screen

The tone should be: confident, professional, Indian legal market context. Not salesy — the features speak for themselves. Speak to a senior advocate or in-house counsel. Assume they know NCLT, IBC, SEBI, LODR.

Total video length: 4–5 minutes.

**PART B — Opening Hook (first 15 seconds)**
A strong opening statement before the first screenshot appears. Should convey the core problem being solved: managing compliance deadlines, enforcement matters, and AI-powered legal research — all in one workspace.

**PART C — Closing (last 20 seconds)**
A closing statement covering: Indian Kanoon RAG, CREAC structure, 23 templates, privacy-first (data stays in browser), pricing (₹2,950/month). Include a CTA: "Request access at legalaidai.in/corporate"

**PART D — Chapter Markers**
A list of timestamps for a 4.5-minute video (00:00, 00:15, etc.) matching each section/screenshot, for YouTube chapter markers.

Format the output clearly with PART A, B, C, D headers. Use the exact UI labels visible in the screenshots when calling out features (e.g., "Deadline Radar", "Compliance Health", "✍ Draft →").
```

---

## OPTIONAL: Audio Overview Prompt

If you want NotebookLM to generate a podcast-style audio overview instead of a script, use this alternative query:

```
Generate an Audio Overview of the Nyaya Saathi Pro Corporate panel as a 4-minute product demo podcast. The hosts should walk through the 5 screens in order — Portfolio Home, Company Dashboard, Compliance Calendar, Matter Detail, and the Workspace (Research, Draft, Regulatory Updates tabs). Highlight: Deadline Radar, donut chart, Draft→ buttons on calendar rows, 23 templates, Indian Kanoon RAG, CREAC structure, and the live regulatory feed. Target audience: senior corporate advocates and in-house counsel at Indian companies. Tone: expert, peer-to-peer, not a sales pitch.
```


---

## Source: corporate-inhouse-pending.md

# Corporate Module — In-House Counsel Mode (Pending)

## Concept
A single-company view for in-house legal teams. Instead of a "My Clients" grid,
the app opens directly on the company's dashboard.

## Key Differences vs. Law Firm Mode

| Feature | Law Firm (current) | In-House (pending) |
|---|---|---|
| Home screen | Client grid (all clients) | Company dashboard (one company) |
| Client switching | Yes | No — single pinned company |
| "Add Client" button | Yes | Hidden — replaced by "Edit Company" |
| Compliance calendar | Secondary (per client) | Front and centre on home |
| Regulatory feed | All sectors | Filtered to company's sector |
| Matters view | Per client | All matters, sorted by urgency |

## Proposed Home Screen Layout

```
┌─────────────────────────────────────────────────────┐
│ IndiaFirst Fintech Services Ltd  L65100MH2019PLC…   │
│ Financial Services / Fintech · Mumbai               │
├──────────┬──────────┬──────────┬────────────────────┤
│ 6 Active │ 2 Enforce│ 1 Overdue│ Next: 3d  DIR-3    │
├──────────┴──────────┴──────────┴────────────────────┤
│  ACTIVE MATTERS                       + Add Matter  │
│  🔴 RBI PPI Enforcement — reply 15 Jun              │
│  🔴 SEBI IA Registration — ongoing                  │
│  🟡 NBFC-MFI Conversion — ongoing                   │
├─────────────────────────────────────────────────────┤
│  COMPLIANCE CALENDAR                                │
│  ⚠ 3 Jun   MCA — DIR-3 KYC                         │
│  ⚠ 15 Jun  RBI — Reply to SCN                      │
│     30 Jun  ROC — Annual Return (MGT-7)             │
├─────────────────────────────────────────────────────┤
│  REGULATORY FEED (RBI · SEBI · MCA)                │
└─────────────────────────────────────────────────────┘
```

## Implementation Plan

### Settings toggle
- Add "Mode" setting: **Law Firm** (default) | **In-House**
- In-house mode: prompts user to pick/pin one company from their client list
- Persisted in localStorage as `nsp_co_mode = 'inhouse'` + `nsp_co_pinned_client = <id>`

### Home screen (S1) changes
- If `mode === 'inhouse'` and a pinned client exists → skip client grid, go to company dashboard
- Company dashboard = enhanced S2 with compliance calendar expanded to full width
- Regulatory feed filtered to `state.userData.sector` or company sector
- "Add Client" fab and section button hidden
- "Edit Company" button in topbar instead

### Navigation changes
- Sidebar shows: Dashboard · Matters · Research · Drafting · Compliance · Settings
- No "Back to clients" breadcrumb

### Matters view
- All matters shown grouped by type: Litigation | Enforcement | Advisory | Transactional
- Each matter has urgency colour: red (overdue/enforcement) · amber (due soon) · grey (routine)

### Compliance calendar
- Promoted to primary panel on home screen
- Pre-populated with standard statutory deadlines by company type:
  - Private Ltd: MGT-7, AOC-4, DIR-3 KYC, ITR, GST
  - Listed (Public): above + LODR quarterly filings, SEBI disclosures
  - LLP: LLP-11, LLP-8

## Status
- [ ] Settings toggle (law firm / in-house)
- [ ] S1 bypass when in-house mode + pinned client
- [ ] Enhanced company dashboard layout
- [ ] Compliance calendar as primary panel
- [ ] Sector-filtered regulatory feed
- [ ] Statutory deadline pre-population by company type
