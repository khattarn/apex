-- Agent 11: Affiliate Tracker — run this in Supabase SQL editor

CREATE TABLE affiliates (
  id              uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name            text,
  instagram_handle text UNIQUE NOT NULL,
  follower_count  integer,
  bio             text,
  bar_enrollment  text,
  upi_id          text,
  referral_code   text UNIQUE,
  phone           text,
  email           text,
  status          text DEFAULT 'prospect',   -- prospect | invited | active | inactive
  source          text DEFAULT 'instagram_scrape',
  scraped_at      timestamptz,
  invited_at      timestamptz,
  onboarded_at    timestamptz,
  notes           text,
  created_at      timestamptz DEFAULT now(),
  updated_at      timestamptz DEFAULT now()
);

CREATE TABLE referrals (
  id               uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  affiliate_id     uuid REFERENCES affiliates(id) ON DELETE SET NULL,
  referral_code    text NOT NULL,
  user_email       text,
  user_name        text,
  product          text DEFAULT 'legalaidai_advocate',
  signup_date      timestamptz DEFAULT now(),
  converted_to_paid boolean DEFAULT false,
  conversion_date  timestamptz,
  created_at       timestamptz DEFAULT now()
);

CREATE TABLE commissions (
  id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  affiliate_id uuid REFERENCES affiliates(id) ON DELETE SET NULL,
  referral_id  uuid REFERENCES referrals(id) ON DELETE SET NULL,
  amount       integer DEFAULT 500,
  type         text,   -- conversion | renewal
  status       text DEFAULT 'pending',  -- pending | paid
  paid_date    timestamptz,
  upi_id       text,
  notes        text,
  created_at   timestamptz DEFAULT now()
);

-- Index for quick referral code lookups at LegalAidAI signup
CREATE INDEX idx_affiliates_referral_code ON affiliates(referral_code);
CREATE INDEX idx_referrals_code           ON referrals(referral_code);
CREATE INDEX idx_referrals_affiliate      ON referrals(affiliate_id);
CREATE INDEX idx_commissions_affiliate    ON commissions(affiliate_id);
CREATE INDEX idx_commissions_status       ON commissions(status);
