-- Migration: Update OnboardingStatus enum to canonical states
-- Purpose: Migrate from DRAFT/TEMPLATE_SELECTED/CHART_READY/CHART_FINALIZED/ACTIVE
--          to NOT_STARTED/MATERIALIZING/ACTIVE
--
-- IMPORTANT: Run this migration if you have an existing database with onboarding data.
-- For new databases, the enum will be created with the correct values automatically.

-- Step 1: Add new enum values to the existing onboardingstatus type
ALTER TYPE onboardingstatus ADD VALUE IF NOT EXISTS 'NOT_STARTED';
ALTER TYPE onboardingstatus ADD VALUE IF NOT EXISTS 'MATERIALIZING';

-- Step 2: Migrate existing data to new values
-- DRAFT → NOT_STARTED
UPDATE companies
SET onboarding_status = 'NOT_STARTED'
WHERE onboarding_status = 'DRAFT';

-- TEMPLATE_SELECTED → MATERIALIZING
UPDATE companies
SET onboarding_status = 'MATERIALIZING'
WHERE onboarding_status = 'TEMPLATE_SELECTED';

-- CHART_READY → MATERIALIZING
UPDATE companies
SET onboarding_status = 'MATERIALIZING'
WHERE onboarding_status = 'CHART_READY';

-- CHART_FINALIZED → MATERIALIZING
UPDATE companies
SET onboarding_status = 'MATERIALIZING'
WHERE onboarding_status = 'CHART_FINALIZED';

-- ACTIVE stays as ACTIVE (no change needed)

-- Step 3: Remove old enum values
-- WARNING: This requires recreating the enum type, which is complex in PostgreSQL
-- For simplicity, we'll leave the old values in the enum type but they won't be used
-- If you want to completely remove them, you'll need to:
-- 1. Create a new enum type with only the new values
-- 2. Alter the column to use the new type
-- 3. Drop the old enum type
--
-- For now, the old values remain in the enum definition but are not used.

-- Verify the migration
SELECT
    onboarding_status,
    COUNT(*) as count
FROM companies
GROUP BY onboarding_status
ORDER BY onboarding_status;

-- Expected results:
-- NOT_STARTED (companies that were DRAFT)
-- MATERIALIZING (companies that were TEMPLATE_SELECTED, CHART_READY, or CHART_FINALIZED)
-- ACTIVE (companies that were ACTIVE)
