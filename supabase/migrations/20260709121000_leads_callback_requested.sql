-- Migration: leads.callback_requested
--
-- server.py's Vapi and Dograh webhook handlers both call
-- update_lead(lead_id, {"callback_requested": True}) whenever a Sophie call's
-- outcome is "callback_requested" — but this column never existed on the
-- live leads table. Every such call hit an unhandled Postgrest error and
-- 500'd the webhook, before reaching the log_activity()/notify_founder()
-- calls right after it — so a genuine "prospect wants a human to call them"
-- signal silently produced neither a founder alert nor a lead_activities row.

ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS callback_requested boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_leads_callback_requested ON leads (callback_requested) WHERE callback_requested;
