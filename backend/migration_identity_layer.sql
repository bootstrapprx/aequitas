-- Migration: Add identity layer fields to users table
-- This migration adds user_uid and preferred_company_id to support the foundational identity layer

BEGIN;

-- Add user_uid column (unique user identifier)
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_uid VARCHAR UNIQUE NOT NULL DEFAULT gen_random_uuid()::text;

-- Add index on user_uid for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_user_uid ON users(user_uid);

-- Add preferred_company_id column
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

-- Populate user_uid for existing users (generate UUIDs)
UPDATE users SET user_uid = gen_random_uuid()::text WHERE user_uid IS NULL OR user_uid = '';

-- Set preferred_company_id to the first company the user has access to (if any)
WITH first_companies AS (
    SELECT DISTINCT ON (user_id) user_id, company_id
    FROM user_companies
    ORDER BY user_id, created_at ASC
)
UPDATE users u
SET preferred_company_id = fc.company_id
FROM first_companies fc
WHERE u.id = fc.user_id AND u.preferred_company_id IS NULL;

COMMIT;
