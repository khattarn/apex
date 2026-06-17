// Promotion Mandate — live view of the Apex promotion strategy

const AGENTS = [
  {
    num: 'Agent 1', name: 'Prospector', owner: 'VP Marketing · agents/prospector.py',
    status: 'live',
    bullets: [
      'Queries Google Maps Places API by business type + city',
      'Deduplicates by place_id — never inserts twice',
      'Feeds new leads into Supabase leads table',
      'Supports: dentist · salon · accountant · physio · lawyer',
    ],
  },
  {
    num: 'Agent 2', name: 'Personalizer', owner: 'VP Marketing · agents/personalizer.py',
    status: 'live',
    bullets: [
      'Claude Haiku generates a personalised WA message per lead',
      'Uses vertical-specific pain points from copy.yaml',
      'Adapts tone by market (AU / US / CA / IN)',
      'Output consumed by Agent 3 (Outreach)',
    ],
  },
  {
    num: 'Agent 3', name: 'Outreach', owner: 'VP Marketing · agents/outreach.py',
    status: 'live',
    bullets: [
      'Sends personalised WA messages via Meta Cloud API',
      'Uses dedicated outreach number +1 385-363-3720',
      'Marks lead status "contacted" on send',
      'Hourly cron: 10am–5:30pm local business time only',
    ],
  },
  {
    num: 'Agent 4', name: 'Reply Handler', owner: 'GM Care · agents/reply_handler.py',
    status: 'build',
    bullets: [
      'Catches inbound WA replies to the outreach number',
      'Claude Haiku classifies intent: interested / question / not_interested / OOO',
      'Updates lead status in Supabase',
      'If question → auto-replies; if interested → hands off to Agent 5',
    ],
  },
  {
    num: 'Agent 5', name: 'Demo Booking', owner: 'GM Care · Aria (Dograh)',
    status: 'live',
    bullets: [
      'Triggered on interested signal from Reply Handler',
      'Aria books demo via Cal.com API (Event ID 5901537)',
      'Sends confirmation WA message with Zoom link',
      'Lead status updated to "replied"',
    ],
  },
  {
    num: 'Agent 6', name: 'WA Follow-up', owner: 'VP Marketing · agents/followup.py',
    status: 'live',
    bullets: [
      'Fires after 3 days of silence since first WA message',
      'Vertical-specific follow-up copy from copy.yaml',
      'Respects send-window: 10am–5:30pm local time',
      'Maximum 1 follow-up per lead',
    ],
  },
  {
    num: 'Agent 7', name: 'Voice Follow-up (Sophie / Henry / Priya)', owner: 'GM Care · agents/voice_outreach.py',
    status: 'live',
    bullets: [
      'Triggers after 5 days of WA silence → Dograh outbound call',
      'Sophie: international (AU/US/CA) via Vobiz free number',
      'Priya: India inbound on +91 9262171423 (Dograh workflow 6243)',
      'Henry: international inbound (Dograh workflow caa24f24)',
      'Call cron: 11am–5pm local time, Mon–Fri',
    ],
  },
  {
    num: 'Agent 8', name: 'Content Agent', owner: 'VP Marketing · agents/content_agent.py',
    status: 'live',
    bullets: [
      'Single source of truth for all outbound copy',
      'Generates: WA templates · email · voice scripts · social posts',
      'Informed by Signal feedback loop (reply rates, open rates)',
      'VP Marketing approval required before deploy',
      'Covers both PracticeDesk and LegalAidAI verticals',
    ],
  },
  {
    num: 'Agent 9', name: 'Re-engagement', owner: 'VP Marketing',
    status: 'plan',
    bullets: [
      'Win-back sequences for churned / gone-cold leads',
      'Triggers at 30-day silence with new angle / offer',
      'Separate copy track from cold outreach',
    ],
  },
  {
    num: 'Agent 10', name: 'Observatory', owner: 'Reports to CEO directly',
    status: 'live',
    bullets: [
      'Daily 7am IST cron → posts digest to founder's personal WA',
      'Reports: Anthropic spend · leads added · conversions · voice minutes',
      'Tracks pipeline last run time and campaign health',
    ],
  },
  {
    num: 'Agent 11', name: 'Affiliate Tracker', owner: 'VP Marketing · LegalAidAI only',
    status: 'plan',
    bullets: [
      'Referral links: legalaidai.in/advocate?ref=CODE',
      '₹500 on first paid subscription · ₹500 on first renewal',
      'Tracks affiliates, referrals, commissions in Supabase',
      'Targets: advocate bar-roll network in India',
    ],
  },
  {
    num: 'Agent 12', name: 'VP Marketing Agent', owner: 'Reports to CEO · orchestrates A1–3, 6, 8, 9, 11',
    status: 'live',
    bullets: [
      'Receives Signal feedback → issues content briefs',
      'Plans weekly campaign calendar',
      'Endpoint: POST /api/vp-marketing/plan',
      'Wires Signal → Content Agent feedback loop',
    ],
  },
]

const statusStyle = {
  live:  { badge: 'bg-green-900/50 text-green-400',  dot: 'bg-green-400',  border: 'border-l-green-500',  label: '● Live' },
  build: { badge: 'bg-amber-900/50 text-amber-400',  dot: 'bg-amber-400',  border: 'border-l-amber-500',  label: '◐ Building' },
  plan:  { badge: 'bg-slate-800 text-slate-500 border border-slate-700', dot: 'bg-slate-600', border2: 'border-l-slate-600', label: '○ Planned' },
}

function Badge({ status }) {
  const s = statusStyle[status]
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${s.badge}`}>
      {s.label}
    </span>
  )
}

function AgentCard({ agent }) {
  const borderColor = {
    live:  'border-l-green-500',
    build: 'border-l-amber-500',
    plan:  'border-l-slate-600',
  }[agent.status]

  return (
    <div className={`bg-[#1e293b] border border-slate-700/40 border-l-2 ${borderColor} rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{agent.num}</span>
        <Badge status={agent.status} />
      </div>
      <div className="text-sm font-bold text-white mb-1">{agent.name}</div>
      <div className="text-[11px] text-slate-500 mb-3">{agent.owner}</div>
      <ul className="space-y-1">
        {agent.bullets.map((b, i) => (
          <li key={i} className="text-[12px] text-slate-400 flex gap-2">
            <span className="text-slate-600 shrink-0 mt-0.5">·</span>
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <span className="text-[11px] font-semibold uppercase tracking-widest text-indigo-400 whitespace-nowrap">{children}</span>
      <div className="flex-1 h-px bg-slate-700/60" />
    </div>
  )
}

function ChannelRow({ icon, name, bullets, status }) {
  const iconBg = { '💬': 'bg-green-900/30', '📧': 'bg-blue-900/30', '📞': 'bg-purple-900/30', '📣': 'bg-amber-900/30', '🤝': 'bg-slate-700/60' }
  return (
    <div className="flex gap-3 py-3 border-b border-slate-700/40 last:border-0 last:pb-0">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-base shrink-0 mt-0.5 ${iconBg[icon] || 'bg-slate-700/40'}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-semibold text-white mb-1">{name}</div>
        <ul className="space-y-0.5">
          {bullets.map((b, i) => (
            <li key={i} className="text-[11px] text-slate-400 flex gap-1.5">
              <span className="text-slate-600 shrink-0">·</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="shrink-0 pt-0.5">
        <Badge status={status} />
      </div>
    </div>
  )
}

function OrgDiagram() {
  return (
    <div className="bg-[#1e293b] border border-slate-700/40 rounded-xl p-6 overflow-x-auto">
      <div className="min-w-[580px]">
        {/* CEO */}
        <div className="flex justify-center mb-0">
          <div className="bg-[#1e1b4b] border border-indigo-500/60 rounded-lg px-5 py-2.5 text-center">
            <div className="text-sm font-bold text-indigo-400">CEO</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Neeraj Khattar (human)</div>
          </div>
        </div>

        {/* vertical stem */}
        <div className="flex justify-center">
          <div className="w-px h-5 bg-slate-600" />
        </div>

        {/* horizontal bar */}
        <div className="flex items-start justify-center gap-0 relative">
          <div className="absolute top-0 left-1/4 right-1/4 h-px bg-slate-600" style={{ left: '16.5%', right: '16.5%' }} />

          {/* VP Marketing column */}
          <div className="flex flex-col items-center" style={{ width: '33%' }}>
            <div className="w-px h-5 bg-slate-600" />
            <div className="bg-[#1e3a5f]/60 border border-blue-500/50 rounded-lg px-3 py-2 text-center w-full max-w-[160px]">
              <div className="text-[12px] font-bold text-blue-400">VP Marketing</div>
              <div className="text-[10px] text-slate-500">Neeraj acting (AI planned)</div>
            </div>
            <div className="w-px h-4 bg-slate-600" />
            <div className="flex gap-1 flex-wrap justify-center max-w-[200px]">
              {[['A1','Prosp.','live'],['A2','Person.','live'],['A3','Outreach','live'],['A6','Follow-up','live'],['A8','Content','live'],['A9','Re-eng.','plan'],['A11','Affiliate','plan'],['A12','VP Mktg','live']].map(([n,l,s]) => (
                <div key={n} className={`rounded px-1.5 py-1 text-center border ${s==='live' ? 'border-green-500/50 bg-green-900/20' : s==='build' ? 'border-amber-500/50 bg-amber-900/20' : 'border-slate-600/50 bg-slate-800/40'}`}>
                  <div className={`text-[10px] font-bold ${s==='live' ? 'text-green-400' : s==='build' ? 'text-amber-400' : 'text-slate-500'}`}>{n}</div>
                  <div className="text-[9px] text-slate-500">{l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* GM Care column */}
          <div className="flex flex-col items-center" style={{ width: '33%' }}>
            <div className="w-px h-5 bg-slate-600" />
            <div className="bg-purple-900/20 border border-purple-500/50 rounded-lg px-3 py-2 text-center w-full max-w-[140px]">
              <div className="text-[12px] font-bold text-purple-400">GM Care</div>
              <div className="text-[10px] text-slate-500">Neeraj acting (AI planned)</div>
            </div>
            <div className="w-px h-4 bg-slate-600" />
            <div className="flex gap-1 flex-wrap justify-center">
              {[['A4','Reply','build'],['A5','Demo Bk.','live'],['A7','Voice','live']].map(([n,l,s]) => (
                <div key={n} className={`rounded px-1.5 py-1 text-center border ${s==='live' ? 'border-green-500/50 bg-green-900/20' : s==='build' ? 'border-amber-500/50 bg-amber-900/20' : 'border-slate-600/50 bg-slate-800/40'}`}>
                  <div className={`text-[10px] font-bold ${s==='live' ? 'text-green-400' : s==='build' ? 'text-amber-400' : 'text-slate-500'}`}>{n}</div>
                  <div className="text-[9px] text-slate-500">{l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Observatory column */}
          <div className="flex flex-col items-center" style={{ width: '33%' }}>
            <div className="w-px h-5 bg-slate-600" />
            <div className="bg-amber-900/20 border border-amber-500/50 rounded-lg px-3 py-2 text-center w-full max-w-[140px]">
              <div className="text-[12px] font-bold text-amber-400">Observatory</div>
              <div className="text-[10px] text-slate-500">Agent 10 — AI only</div>
            </div>
            <div className="w-px h-4 bg-slate-600" />
            <div className="rounded px-1.5 py-1 text-center border border-amber-500/50 bg-amber-900/20">
              <div className="text-[10px] font-bold text-amber-400">A10</div>
              <div className="text-[9px] text-slate-500">Daily digest</div>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 mt-6 pt-4 border-t border-slate-700/40 justify-center flex-wrap">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full bg-green-400" /> Live
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Building
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full border border-slate-500" /> Planned
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Mandate() {
  return (
    <div className="p-4 md:p-6 space-y-8 max-w-6xl mx-auto">

      {/* Header */}
      <div className="border-b border-slate-700/60 pb-6">
        <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">
          Apex Internal · Promotion Mandate v1.0 · Issued June 2026 · CEO: Neeraj Khattar
        </div>
        <h2 className="text-xl font-bold text-white mb-1">Apex Promotion Mandate</h2>
        <p className="text-sm text-slate-400 mb-4">
          Multi-agent outreach &amp; promotion strategy for PracticeDesk and LegalAidAI / Nyaya Saathi
        </p>
        <div className="flex flex-wrap gap-2">
          {[
            ['● 8 Agents Live', 'border-green-500/60 text-green-400'],
            ['◐ 2 Agents Building / Planned', 'border-amber-500/60 text-amber-400'],
            ['2 Products', 'border-slate-600 text-slate-400'],
            ['4 Channels', 'border-slate-600 text-slate-400'],
            ['5 Markets', 'border-slate-600 text-slate-400'],
          ].map(([label, cls]) => (
            <span key={label} className={`text-[11px] px-3 py-1 rounded-full border ${cls}`}>{label}</span>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { val: '8',  label: 'Agents live on Railway',      color: 'text-green-400' },
          { val: '2',  label: 'Agents building or planned',  color: 'text-amber-400' },
          { val: '4',  label: 'Active channels',             color: 'text-blue-400' },
          { val: '5',  label: 'Markets (AU·US·CA·IN·Global)',color: 'text-purple-400' },
        ].map(s => (
          <div key={s.label} className="bg-[#1e293b] border border-slate-700/40 rounded-xl p-4">
            <div className={`text-3xl font-bold ${s.color}`}>{s.val}</div>
            <div className="text-[11px] text-slate-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Org diagram */}
      <div>
        <SectionTitle>Org Structure &amp; Delegation</SectionTitle>
        <OrgDiagram />
      </div>

      {/* Agent cards */}
      <div>
        <SectionTitle>All 12 Agents — Status &amp; Mandate</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {AGENTS.map(a => <AgentCard key={a.num} agent={a} />)}
        </div>
      </div>

      {/* Products */}
      <div>
        <SectionTitle>Promotion by Product</SectionTitle>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* PracticeDesk */}
          <div className="bg-[#1e293b] border border-slate-700/40 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700/40">
              <div className="text-base font-bold text-white mb-0.5">🦷 PracticeDesk</div>
              <div className="text-[12px] text-slate-400">Australia · USA · Canada · Global &nbsp;|&nbsp; $49–$180/mo USD</div>
            </div>
            <div className="px-5 py-4 space-y-0 divide-y divide-slate-700/40">
              <ChannelRow icon="💬" name="WhatsApp Outreach" status="live" bullets={[
                'Cold prospect via Google Maps (A1 → A2 → A3)',
                'Follow-up after 3 days silence (A6)',
                'Number: +1 385-363-3720 (Meta verified)',
                'Send window: 10am–5:30pm local · hourly cron',
                'Verticals: Dentist · Salon · Accountant · Physio · Lawyer',
              ]} />
              <ChannelRow icon="📧" name="Email Sequence" status="live" bullets={[
                '6-step drip: Day 0 / 3 / 6 / 9 / 12 / 30',
                'Timezone-aware · Mon–Fri 8:30am–7pm local',
                'Sent via Resend from practicedesk.live',
                'Open & click tracking live (webhook + Supabase)',
                '8 HTML templates, A/B subject lines',
              ]} />
              <ChannelRow icon="📞" name="Voice Follow-up (Sophie / Henry)" status="live" bullets={[
                'Sophie outbound: 5-day WA silence → Dograh call',
                'Henry inbound: answers calls to international number',
                '7-phase Aria sales playbook · 330s cap',
                'Interested → Aria books Cal.com demo automatically',
                'Cron: 11am–5pm local Mon–Fri',
              ]} />
              <ChannelRow icon="📣" name="Social Media" status="build" bullets={[
                'Content Agent generates LinkedIn + Instagram posts',
                'Vertical hooks: pain-first, stat-lead, outcome-first',
                'Currently founder-posted manually',
                'Future: auto-publish agent',
              ]} />
            </div>
          </div>

          {/* LegalAidAI */}
          <div className="bg-[#1e293b] border border-slate-700/40 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700/40">
              <div className="text-base font-bold text-white mb-0.5">⚖️ LegalAidAI / Nyaya Saathi</div>
              <div className="text-[12px] text-slate-400">India · 1.4B citizens · 1.7M advocates &nbsp;|&nbsp; ₹2,500–₹5,000/mo</div>
            </div>
            <div className="px-5 py-4">
              {/* Module chips */}
              <div className="space-y-2 mb-4">
                {[
                  { title: 'Advocate Module', chips: [['Voice (Priya)','live'],['WA Outreach','live'],['Email','live'],['Affiliate','plan']] },
                  { title: 'Corporate / In-house', chips: [['Voice','live'],['Email Sequence','live'],['Human Close','plan']] },
                  { title: 'Citizen Module',     chips: [['Social Media','live'],['WA Inbound','live'],['SMS','plan']] },
                ].map(m => (
                  <div key={m.title} className="bg-slate-800/50 rounded-lg px-3 py-2.5 border border-slate-700/40">
                    <div className="text-[12px] font-semibold text-white mb-1.5">{m.title}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.chips.map(([label, s]) => (
                        <span key={label} className={`text-[10px] font-medium px-2 py-0.5 rounded ${
                          s === 'live'  ? 'bg-green-900/50 text-green-400' :
                          s === 'build' ? 'bg-amber-900/50 text-amber-400' :
                          'bg-slate-700 text-slate-500 border border-slate-600'
                        }`}>{label}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="divide-y divide-slate-700/40">
                <ChannelRow icon="📞" name="Voice — Priya (India AI Agent)" status="live" bullets={[
                  'Inbound on +91 9262171423 (Dograh workflow 6243)',
                  'Handles advocate enquiries · books consultations',
                  'Telephony config 477 (Vobiz India SIP)',
                  'End-of-call webhook → Railway → Supabase (wired today)',
                ]} />
                <ChannelRow icon="💬" name="WhatsApp" status="build" bullets={[
                  'Advocate: outreach + reply handling',
                  'Citizen: inbound self-service queries',
                  'India-specific Hinglish copy templates',
                  'India WA number: +91 registration pending',
                ]} />
                <ChannelRow icon="📣" name="Social Media (Citizen focus)" status="live" bullets={[
                  'Instagram & LinkedIn content for citizen reach',
                  'Scraped advocate followee network for targeting',
                  'Content Agent generates Hindi + English posts',
                  'Founder-posted currently · publish agent planned',
                ]} />
                <ChannelRow icon="🤝" name="Affiliate Programme" status="plan" bullets={[
                  'Referral links: legalaidai.in/advocate?ref=CODE',
                  '₹500 on first paid sub · ₹500 on first renewal',
                  'Target: bar-roll advocate network across India',
                  'Agent 11 build not yet started',
                ]} />
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* India Expansion Timeline */}
      <div>
        <SectionTitle>India Expansion — PracticeDesk (Next Build)</SectionTitle>
        <div className="space-y-0">
          {[
            {
              phase: 'Phase 1 — Week 1–2', title: 'WhatsApp Outreach Agent (India)', status: 'plan',
              bullets: [
                'Register Indian +91 WA number (second WABA slot)',
                'Create agents/india_personalizer.py — Hinglish templates',
                'Add doctor + clinic business types to prospector',
                'Cities: Delhi · Mumbai · Bangalore · Hyderabad · Pune',
                'Add market=india + currency=INR flags to leads',
              ],
            },
            {
              phase: 'Phase 2 — Week 3–4', title: 'AI Telecalling Agent "Priya" (PracticeDesk)', status: 'plan',
              bullets: [
                'Exotel account + Indian DID number (TRAI/DLT registration)',
                'Exotel → Vapi SIP bridge · Priya 5-phase Hindi/English script',
                'NDNC scrubbing before each call batch · 9am–9pm IST Mon–Sat',
                'New endpoint: /api/cron/india-voice-followup',
              ],
            },
            {
              phase: 'Phase 3 — Week 5', title: 'Razorpay Billing + India Email Drip', status: 'plan',
              bullets: [
                'Razorpay subscription plans: ₹2,499 · ₹4,999 · ₹9,999 · ₹14,999',
                'UPI AutoPay mandate collected during free trial',
                'India email drip — Hinglish subjects · ₹ pricing · Indian social proof',
                'Admin dashboard: INR display for India leads',
              ],
            },
          ].map((item, i, arr) => (
            <div key={i} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 border ${
                  item.status === 'live' ? 'bg-green-400 border-green-400' :
                  item.status === 'build' ? 'bg-amber-400 border-amber-400' :
                  'border-slate-500'
                }`} />
                {i < arr.length - 1 && <div className="w-px flex-1 bg-slate-700/60 my-1" />}
              </div>
              <div className="pb-6">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">{item.phase}</div>
                <div className="text-[13px] font-semibold text-white mb-2">{item.title}</div>
                <ul className="space-y-1">
                  {item.bullets.map((b, j) => (
                    <li key={j} className="text-[12px] text-slate-400 flex gap-2">
                      <span className="text-slate-600 shrink-0 mt-0.5">→</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operating Windows */}
      <div>
        <SectionTitle>Operating Windows &amp; Cron Schedule</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[
            { icon: '💬', title: 'WhatsApp', bullets: ['10:00am – 5:30pm local business time','Cron: hourly with per-lead timezone gate','Markets: AU · US · CA · IN','Max: 5 leads per run (configurable)'] },
            { icon: '📞', title: 'Voice Calls', bullets: ['11:00am – 5:00pm local business time','Cron: hourly · Mon–Fri only','India: 9am–9pm IST · Mon–Sat (TRAI)','Dograh outbound via Sophie / Priya'] },
            { icon: '📧', title: 'Email', bullets: ['8:30am – 7:00pm local time','Cron: hourly · Mon–Fri only','Drip: 6 steps at Days 0/3/6/9/12/30','scrape_attempted guard prevents double-send'] },
            { icon: '📊', title: 'Observatory', bullets: ['Daily: 7:00am IST (01:30 UTC)','Covers: spend · leads · conversions · voice mins','Delivered to founder WA: +919810982019'] },
          ].map(w => (
            <div key={w.title} className="bg-[#1e293b] border border-slate-700/40 border-l-2 border-l-green-500 rounded-lg p-4">
              <div className="text-sm font-bold text-white mb-3">{w.icon} {w.title}</div>
              <ul className="space-y-1.5">
                {w.bullets.map((b, i) => (
                  <li key={i} className="text-[12px] text-slate-400 flex gap-2">
                    <span className="text-slate-600 shrink-0">·</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-700/40 pt-5 flex flex-col sm:flex-row justify-between gap-3">
        <div className="text-[11px] text-slate-500">Apex Promotion Mandate v1.0 · Issued June 2026 · CEO: Neeraj Khattar</div>
        <div className="flex gap-4 text-[11px] text-slate-500">
          <span>Railway: serene-passion-production-cd82.up.railway.app</span>
          <span>Dashboard: mpex.netlify.app</span>
        </div>
      </div>

    </div>
  )
}
