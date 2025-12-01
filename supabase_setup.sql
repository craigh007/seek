-- Run this in Supabase SQL Editor (Database > SQL Editor)

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
    salary TEXT,
    date_listed TEXT,
    job_type TEXT,
    description TEXT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    triage_status TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_triage ON jobs(triage_status);

-- CV profile table (stores your CV for AI matching)
CREATE TABLE IF NOT EXISTS cv_profile (
    id BIGSERIAL PRIMARY KEY,
    cv_text TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_profile ENABLE ROW LEVEL SECURITY;

-- Allow all operations with anon key (for simplicity)
-- For production, you'd want more restrictive policies
CREATE POLICY "Allow all on jobs" ON jobs FOR ALL USING (true);
CREATE POLICY "Allow all on cv_profile" ON cv_profile FOR ALL USING (true);
