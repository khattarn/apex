-- Migration 005: Signal funnel metrics, projections, and targets
-- Run after 004_signal_ceo_tables.sql

-- ── Funnel Metrics ────────────────────────────────────────────────────────────
-- Computed conversion rates at every funnel stage per vertical × country × period.

CREATE TABLE IF NOT EXISTS funnel_metrics (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_type    TEXT NOT NULL,
  country          TEXT NOT NULL,
  channel          TEXT NOT NULL DEFAULT 'all',
  period           TEXT NOT NULL,           -- 'YYYY-MM' or 'all_time'
  prospects        INT DEFAULT 0,
  contacts         INT DEFAULT 0,
  wa_replies       INT DEFAULT 0,
  email_opens      INT DEFAULT 0,
  email_clicks     INT DEFAULT 0,
  interested       INT DEFAULT 0,
  demos            INT DEFAULT 0,
  calls_placed     INT DEFAULT 0,
  converted        INT DEFAULT 0,
  contact_rate     FLOAT DEFAULT 0,
  wa_reply_rate    FLOAT DEFAULT 0,
  email_open_rate  FLOAT DEFAULT 0,
  email_click_rate FLOAT DEFAULT 0,
  interest_rate    FLOAT DEFAULT 0,
  demo_rate        FLOAT DEFAULT 0,
  conversion_rate  FLOAT DEFAULT 0,
  computed_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE(business_type, country, period)
);

-- ── Projections ───────────────────────────────────────────────────────────────
-- Forward-looking revenue model per vertical × country × scenario.

CREATE TABLE IF NOT EXISTS projections (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_type       TEXT NOT NULL,
  country             TEXT NOT NULL,
  scenario            TEXT NOT NULL DEFAULT 'base',  -- base | optimistic | pessimistic
  horizon             TEXT DEFAULT '3_6_12_months',
  monthly_prospects   INT DEFAULT 50,
  data_source         TEXT,              -- 'real_data' | 'benchmark_defaults'
  contact_rate        FLOAT DEFAULT 0,
  wa_reply_rate       FLOAT DEFAULT 0,
  email_open_rate     FLOAT DEFAULT 0,
  email_click_rate    FLOAT DEFAULT 0,
  interest_rate       FLOAT DEFAULT 0,
  demo_rate           FLOAT DEFAULT 0,
  conversion_rate     FLOAT DEFAULT 0,
  demos_per_month     FLOAT DEFAULT 0,
  paid_new_per_month  FLOAT DEFAULT 0,
  paid_3mo            FLOAT DEFAULT 0,   -- cumulative paid customers at 3 months
  paid_6mo            FLOAT DEFAULT 0,
  paid_12mo           FLOAT DEFAULT 0,
  mrr_3mo             FLOAT DEFAULT 0,   -- USD
  mrr_6mo             FLOAT DEFAULT 0,
  mrr_12mo            FLOAT DEFAULT 0,
  confidence          TEXT DEFAULT 'low', -- high | medium | low
  generated_at        TIMESTAMPTZ DEFAULT now(),
  UNIQUE(business_type, country, scenario)
);

-- ── Targets ───────────────────────────────────────────────────────────────────
-- Achievable targets set by Signal. Tracked weekly vs actuals.

CREATE TABLE IF NOT EXISTS targets (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_type  TEXT NOT NULL,
  country        TEXT NOT NULL,
  channel        TEXT DEFAULT 'all',
  metric         TEXT NOT NULL,       -- 'wa_reply_rate' | 'email_open_rate' | 'demo_rate' | 'mrr' | 'paid_customers'
  period         TEXT NOT NULL,       -- 'YYYY-QN' quarter
  target_value   FLOAT NOT NULL,
  actual_value   FLOAT DEFAULT 0,
  variance       FLOAT DEFAULT 0,     -- actual - target (negative = behind)
  status         TEXT DEFAULT 'active',
  -- active | on_track | behind | missed | exceeded | dead_end | abandoned
  set_by         TEXT DEFAULT 'signal',
  rationale      TEXT,
  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now(),
  UNIQUE(business_type, country, metric, period)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_funnel_metrics_lookup    ON funnel_metrics(business_type, country, period);
CREATE INDEX IF NOT EXISTS idx_projections_lookup       ON projections(business_type, country, scenario);
CREATE INDEX IF NOT EXISTS idx_targets_period           ON targets(period, status);
CREATE INDEX IF NOT EXISTS idx_targets_lookup           ON targets(business_type, country, metric);
