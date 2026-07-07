-- Migration 007: leads.source (category/tag) + Google Places rating columns
--
-- agents/prospector.py and agents/ingest.py have both been inserting "rating",
-- "user_ratings_total" and (ingest.py only) "source" on every save_lead() call, but none
-- of the three columns exist on the live leads table — every insert through either path
-- currently fails with a Postgrest 42703 "column does not exist" error.
--
-- "source" doubles as the category/tag column for identifying how a lead was acquired,
-- e.g. 'new_business_manual', 'job_ad_indeed', or unset (null) for the normal Maps sweep.

ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS source text,
  ADD COLUMN IF NOT EXISTS rating numeric,
  ADD COLUMN IF NOT EXISTS user_ratings_total integer;

CREATE INDEX IF NOT EXISTS idx_leads_source ON leads (source);
