-- Run once in Supabase dashboard (SQL Editor).
-- Tracks last successful run of each scheduler job for the heartbeat watchdog.

CREATE TABLE IF NOT EXISTS agent_health (
  job             TEXT PRIMARY KEY,
  last_success_at TIMESTAMPTZ,
  last_run_at     TIMESTAMPTZ,
  last_result     JSONB,
  last_alert_at   TIMESTAMPTZ,
  last_alert_kind TEXT,
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE agent_health IS
  'One row per scheduler job. Written by upsert_heartbeat() on each successful run.';
