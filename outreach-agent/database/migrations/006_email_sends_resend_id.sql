-- Migration 006: Add resend_email_id to email_sends + email tracking columns on leads
-- Fixes broken open/click webhook tracking.

-- ── email_sends: add resend_email_id for webhook lookup ───────────────────────
ALTER TABLE email_sends ADD COLUMN IF NOT EXISTS resend_email_id TEXT;
ALTER TABLE email_sends ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_email_sends_resend_id ON email_sends(resend_email_id);

-- ── leads: add open/click timestamp columns if missing ────────────────────────
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_opened_at   TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_clicked_at  TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_clicked_link TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS resend_email_id   TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_bounced     BOOLEAN DEFAULT FALSE;
