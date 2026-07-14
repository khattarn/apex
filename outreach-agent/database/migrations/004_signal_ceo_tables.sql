-- Migration 004: Signal Agent + CEO Agent tables
-- Run in Supabase SQL editor before activating Signal or CEO agents.

-- ── CEO Agent Tables ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_registry (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT UNIQUE NOT NULL,     -- 'wa_followup', 'voice_outreach', etc.
  description     TEXT,
  status          TEXT DEFAULT 'active',    -- active | paused | error
  last_run_at     TIMESTAMPTZ,
  last_run_result JSONB,                   -- {processed, sent, failed, error}
  config          JSONB DEFAULT '{}',       -- adjustable params per agent
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_directives (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent       TEXT NOT NULL,
  directive   TEXT NOT NULL,              -- PAUSE | ADJUST_INTERVAL | CHANGE_TEMPLATE | TARGET | ABORT_LEAD
  params      JSONB DEFAULT '{}',
  status      TEXT DEFAULT 'pending',     -- pending | applied | expired
  issued_by   TEXT DEFAULT 'ceo',
  created_at  TIMESTAMPTZ DEFAULT now(),
  applied_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS system_journal (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_type  TEXT NOT NULL,             -- health_check | alert | decision | directive_issued | signal_auto_promote | signal_auto_kill | signal_proposal
  summary     TEXT,
  detail      JSONB DEFAULT '{}',
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS architecture_reviews (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  triggered_by    TEXT DEFAULT 'scheduled',  -- scheduled | neeraj_request | ceo_request | signal_request
  summary         TEXT,
  recommendations JSONB,                     -- [{agent, verdict, rationale, cost_impact}]
  status          TEXT DEFAULT 'proposed',   -- proposed | awaiting_neeraj | approved | rejected | partial
  neeraj_response TEXT,
  approved_items  JSONB,
  implemented_at  TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ── Signal Agent Tables ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS template_scores (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name   TEXT NOT NULL,
  channel         TEXT NOT NULL,           -- wa | email | voice | sms
  business_type   TEXT NOT NULL,
  country         TEXT NOT NULL,
  sends           INT DEFAULT 0,
  replies         INT DEFAULT 0,
  reply_rate      FLOAT DEFAULT 0,
  opens           INT DEFAULT 0,
  open_rate       FLOAT DEFAULT 0,
  clicks          INT DEFAULT 0,
  click_rate      FLOAT DEFAULT 0,
  status          TEXT DEFAULT 'active',   -- active | paused | killed | replaced
  scored_at       TIMESTAMPTZ DEFAULT now(),
  UNIQUE(template_name, channel, business_type, country)
);

CREATE TABLE IF NOT EXISTS ab_tests (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name       TEXT NOT NULL,
  channel             TEXT NOT NULL,
  business_type       TEXT NOT NULL,
  country             TEXT NOT NULL,
  control_copy        TEXT,
  variant_copy        TEXT,
  control_sends       INT DEFAULT 0,
  variant_sends       INT DEFAULT 0,
  control_replies     INT DEFAULT 0,
  variant_replies     INT DEFAULT 0,
  status              TEXT DEFAULT 'running',  -- running | variant_won | control_won | control_killed | inconclusive | proposed
  autonomous          BOOLEAN DEFAULT TRUE,    -- false = required CEO/Neeraj approval
  rationale           TEXT,
  winner              TEXT,                    -- 'control' | 'variant' | null
  lift                FLOAT,                   -- variant_rate / control_rate
  created_at          TIMESTAMPTZ DEFAULT now(),
  concluded_at        TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS objections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  objection_text  TEXT NOT NULL,
  business_type   TEXT,
  country         TEXT,
  channel         TEXT,
  frequency       INT DEFAULT 1,
  winning_rebuttal TEXT,
  rebuttal_effectiveness TEXT,             -- high | medium | low | untested
  source          TEXT DEFAULT 'transcript', -- transcript | wa_reply | email_reply
  last_seen_at    TIMESTAMPTZ DEFAULT now(),
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS learnings (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category     TEXT NOT NULL,             -- message_effectiveness | timing | client_voice | geo_preference
  insight      TEXT NOT NULL,
  business_type TEXT,
  country      TEXT,
  confidence   FLOAT DEFAULT 0.5,         -- 0-1 based on sample size
  data_points  INT DEFAULT 0,
  period_start TIMESTAMPTZ,
  period_end   TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Named signal_knowledge_base, not knowledge_base: that name is already taken by
-- PracticeDesk's per-practice FAQ table (professional_id/question/answer) in the
-- same shared Supabase project. This table stores a different shape of data
-- (topic/content summaries) for the Signal agent.
CREATE TABLE IF NOT EXISTS signal_knowledge_base (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic      TEXT UNIQUE NOT NULL,        -- 'top_performing_messages_AU_dentist', 'objection_map_CA'
  content    TEXT,                        -- markdown or structured JSON summary
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Seed: agent_registry with existing agents ─────────────────────────────────

INSERT INTO agent_registry (name, description, status) VALUES
  ('prospector',      'Google Maps lead discovery by business type and city', 'active'),
  ('email_scraper',   'Extracts email addresses from prospect websites',       'active'),
  ('personalizer',    'Generates personalised WA messages per lead',           'active'),
  ('email_personalizer', 'Generates personalised email sequences per lead',    'active'),
  ('reply_handler',   'Classifies WA reply intent, auto-responds',            'active'),
  ('wa_followup',     'Sends WA follow-up to leads silent after 3 days',       'active'),
  ('voice_outreach',  'Vapi outbound call to leads silent after 5 days',       'active'),
  ('click_caller',    'Aria 7-phase sales call to email-clicked hot leads',    'active'),
  ('email_sender',    'Sends 6-step email drip sequence',                      'active'),
  ('observatory',     'Daily system digest sent to founder via WhatsApp',      'active'),
  ('ceo',             'System orchestrator — heartbeat, directives, WA Q&A',   'inactive'),
  ('signal',          'Campaign intelligence — scoring, A/B tests, proposals', 'inactive')
ON CONFLICT (name) DO NOTHING;

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_agent_directives_agent_status ON agent_directives(agent, status);
CREATE INDEX IF NOT EXISTS idx_system_journal_entry_type ON system_journal(entry_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_template_scores_lookup ON template_scores(business_type, country, channel);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_objections_business_country ON objections(business_type, country);
CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category, business_type, country);
