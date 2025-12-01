-- Run this in Supabase SQL Editor to add region column

-- Add region column
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS region TEXT;

-- Create index for region filtering
CREATE INDEX IF NOT EXISTS idx_jobs_region ON jobs(region);
