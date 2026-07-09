-- Migration: create content_approvals table
--
-- database/client.py (save_approval / get_approvals / update_approval) and the
-- /api/content/approvals endpoints in server.py have been reading/writing a
-- "content_approvals" table that was never created — every call from the
-- Content Agent screen (save to queue, approve, reject, edit) has been failing
-- with a Postgrest 42P01 "relation does not exist" error since the feature
-- was built.

CREATE TABLE IF NOT EXISTS content_approvals (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_type text NOT NULL,
  product      text NOT NULL,
  module       text NOT NULL,
  market       text NOT NULL DEFAULT 'AU',
  tone         text NOT NULL DEFAULT 'structured',
  language     text NOT NULL DEFAULT 'en',
  content      text NOT NULL,
  subject      text,
  source       text NOT NULL DEFAULT 'content_screen',
  status       text NOT NULL DEFAULT 'pending',
  notes        text,
  reviewed_at  timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_approvals_status ON content_approvals (status);
CREATE INDEX IF NOT EXISTS idx_content_approvals_created_at ON content_approvals (created_at DESC);
