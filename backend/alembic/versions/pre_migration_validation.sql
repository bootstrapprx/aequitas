-- ============================================================================
-- PRE-MIGRATION VALIDATION SCRIPT
-- Phase 1: Critical Data Integrity Migrations (003-012)
--
-- PURPOSE:
-- Validate existing data before applying Phase 1 migrations.
-- Identify violations that would cause migrations to fail.
-- Provide remediation guidance for each violation type.
--
-- USAGE:
-- Run this script BEFORE applying Phase 1 migrations:
--   psql -U user -d aequitas_dev -f pre_migration_validation.sql
--
-- If any violations are found, fix them before proceeding with migrations.
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'PRE-MIGRATION VALIDATION - PHASE 1'
\echo 'Aequitas Chart of Accounts Canonical Compliance'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- VALIDATION 1: Journal Entry Line Constraints
-- Migration: 003_add_journal_entry_line_constraints.py
-- ============================================================================

\echo 'VALIDATION 1: Checking journal entry lines for constraint violations...'
\echo ''

-- Check for negative amounts
\echo '  1a. Checking for negative debit/credit amounts...'
SELECT 'VIOLATION' as severity,
       '1a' as check_id,
       'Negative amounts in journal_entry_lines' as violation_type,
       COUNT(*) as violation_count,
       'UPDATE journal_entry_lines SET debit_amount = ABS(debit_amount), credit_amount = ABS(credit_amount) WHERE debit_amount < 0 OR credit_amount < 0;' as remediation
FROM journal_entry_lines
WHERE debit_amount < 0 OR credit_amount < 0
HAVING COUNT(*) > 0;

-- Check for debit XOR credit violations (both non-zero)
\echo '  1b. Checking for lines with both debit AND credit...'
SELECT 'VIOLATION' as severity,
       '1b' as check_id,
       'Lines with both debit AND credit' as violation_type,
       COUNT(*) as violation_count,
       'Manual review required. Determine which side is correct and zero out the other.' as remediation
FROM journal_entry_lines
WHERE debit_amount > 0 AND credit_amount > 0
HAVING COUNT(*) > 0;

-- Check for debit XOR credit violations (both zero)
\echo '  1c. Checking for lines with neither debit NOR credit...'
SELECT 'VIOLATION' as severity,
       '1c' as check_id,
       'Lines with neither debit NOR credit' as violation_type,
       COUNT(*) as violation_count,
       'DELETE FROM journal_entry_lines WHERE debit_amount = 0 AND credit_amount = 0;' as remediation
FROM journal_entry_lines
WHERE debit_amount = 0 AND credit_amount = 0
HAVING COUNT(*) > 0;

\echo ''
\echo '  ✓ Journal entry line constraints check complete.'
\echo ''

-- ============================================================================
-- VALIDATION 2: Double-Entry Balance
-- Migration: 004_add_double_entry_balance_trigger.py
-- ============================================================================

\echo 'VALIDATION 2: Checking for unbalanced journal entries...'
\echo ''

-- Check for unbalanced POSTED entries
\echo '  2a. Checking POSTED entries for balance violations...'
WITH unbalanced AS (
    SELECT
        je.id,
        je.entry_number,
        je.status,
        SUM(jel.debit_amount) as total_debits,
        SUM(jel.credit_amount) as total_credits,
        SUM(jel.debit_amount) - SUM(jel.credit_amount) as difference
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    WHERE je.status = 'POSTED'
    GROUP BY je.id, je.entry_number, je.status
    HAVING SUM(jel.debit_amount) != SUM(jel.credit_amount)
)
SELECT 'VIOLATION' as severity,
       '2a' as check_id,
       'Unbalanced POSTED journal entries' as violation_type,
       COUNT(*) as violation_count,
       'Manual review required. Adjust journal entry lines to balance or change status to DRAFT.' as remediation
FROM unbalanced
HAVING COUNT(*) > 0;

-- Check for entries with no lines
\echo '  2b. Checking for entries with no lines...'
SELECT 'VIOLATION' as severity,
       '2b' as check_id,
       'Journal entries with no lines' as violation_type,
       COUNT(*) as violation_count,
       'DELETE FROM journal_entries WHERE id NOT IN (SELECT DISTINCT journal_entry_id FROM journal_entry_lines);' as remediation
FROM journal_entries je
WHERE NOT EXISTS (
    SELECT 1 FROM journal_entry_lines WHERE journal_entry_id = je.id
)
HAVING COUNT(*) > 0;

\echo ''
\echo '  ✓ Double-entry balance check complete.'
\echo ''

-- ============================================================================
-- VALIDATION 3: Account Type Classification
-- Migration: 005_add_account_type_to_company_accounts.py
-- ============================================================================

\echo 'VALIDATION 3: Checking account type mapping readiness...'
\echo ''

-- Check for unmapped accounts (no master_account_code)
\echo '  3a. Checking for unmapped company accounts...'
SELECT 'WARNING' as severity,
       '3a' as check_id,
       'Company accounts without master_account_code' as violation_type,
       COUNT(*) as violation_count,
       'Accounts will be classified using code prefix heuristics (1=Asset, 2=Liability, 3=Equity, 4=Revenue, 5-6=Expense)' as remediation
FROM company_accounts
WHERE master_account_code IS NULL
HAVING COUNT(*) > 0;

-- Check for master accounts with invalid category
\echo '  3b. Checking for master accounts with unrecognized category...'
SELECT 'VIOLATION' as severity,
       '3b' as check_id,
       'Master accounts with invalid category' as violation_type,
       COUNT(*) as violation_count,
       'UPDATE master_accounts SET category = [correct value] WHERE category NOT IN (''Assets'', ''Asset'', ''Liabilities'', ''Liability'', ''Equity'', ''Equities'', ''Revenue'', ''Revenues'', ''Expense'', ''Expenses'');' as remediation
FROM master_accounts
WHERE category NOT IN ('Assets', 'Asset', 'Liabilities', 'Liability', 'Equity', 'Equities', 'Revenue', 'Revenues', 'Expense', 'Expenses')
HAVING COUNT(*) > 0;

\echo ''
\echo '  ✓ Account type mapping check complete.'
\echo ''

-- ============================================================================
-- VALIDATION 4: Fiscal Period Overlap
-- Migration: 012_add_fiscal_period_overlap_prevention.py
-- ============================================================================

\echo 'VALIDATION 4: Checking for overlapping fiscal periods...'
\echo ''

-- Check for overlapping periods
\echo '  4a. Checking for overlapping fiscal periods...'
WITH overlap_check AS (
    SELECT DISTINCT
        fp1.company_id,
        fp1.period_number as period1,
        fp1.start_date as start1,
        fp1.end_date as end1,
        fp2.period_number as period2,
        fp2.start_date as start2,
        fp2.end_date as end2
    FROM fiscal_periods fp1
    JOIN fiscal_periods fp2
        ON fp1.company_id = fp2.company_id
        AND fp1.id < fp2.id
        AND daterange(fp1.start_date, fp1.end_date, '[]')
            && daterange(fp2.start_date, fp2.end_date, '[]')
)
SELECT 'VIOLATION' as severity,
       '4a' as check_id,
       'Overlapping fiscal periods' as violation_type,
       COUNT(*) as violation_count,
       'Manual review required. Adjust period dates or delete duplicate periods.' as remediation
FROM overlap_check
HAVING COUNT(*) > 0;

-- Detail overlapping periods (first 10)
SELECT
    company_id,
    period1,
    start1,
    end1,
    period2,
    start2,
    end2,
    'Periods overlap from ' || GREATEST(start1, start2)::text || ' to ' || LEAST(end1, end2)::text as overlap_range
FROM (
    SELECT
        fp1.company_id,
        fp1.period_number as period1,
        fp1.start_date as start1,
        fp1.end_date as end1,
        fp2.period_number as period2,
        fp2.start_date as start2,
        fp2.end_date as end2
    FROM fiscal_periods fp1
    JOIN fiscal_periods fp2
        ON fp1.company_id = fp2.company_id
        AND fp1.id < fp2.id
        AND daterange(fp1.start_date, fp1.end_date, '[]')
            && daterange(fp2.start_date, fp2.end_date, '[]')
    LIMIT 10
) AS overlap_detail;

\echo ''
\echo '  ✓ Fiscal period overlap check complete.'
\echo ''

-- ============================================================================
-- SUMMARY
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'VALIDATION SUMMARY'
\echo '============================================================================'
\echo ''

-- Count total violations
WITH violation_summary AS (
    -- Negative amounts
    SELECT '1a' as check_id, COUNT(*) as count
    FROM journal_entry_lines
    WHERE debit_amount < 0 OR credit_amount < 0

    UNION ALL

    -- Both debit and credit
    SELECT '1b', COUNT(*)
    FROM journal_entry_lines
    WHERE debit_amount > 0 AND credit_amount > 0

    UNION ALL

    -- Neither debit nor credit
    SELECT '1c', COUNT(*)
    FROM journal_entry_lines
    WHERE debit_amount = 0 AND credit_amount = 0

    UNION ALL

    -- Unbalanced POSTED entries
    SELECT '2a', COUNT(*)
    FROM (
        SELECT je.id
        FROM journal_entries je
        JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
        WHERE je.status = 'POSTED'
        GROUP BY je.id
        HAVING SUM(jel.debit_amount) != SUM(jel.credit_amount)
    ) AS unbalanced

    UNION ALL

    -- Entries with no lines
    SELECT '2b', COUNT(*)
    FROM journal_entries je
    WHERE NOT EXISTS (SELECT 1 FROM journal_entry_lines WHERE journal_entry_id = je.id)

    UNION ALL

    -- Invalid master account category
    SELECT '3b', COUNT(*)
    FROM master_accounts
    WHERE category NOT IN ('Assets', 'Asset', 'Liabilities', 'Liability', 'Equity', 'Equities', 'Revenue', 'Revenues', 'Expense', 'Expenses')

    UNION ALL

    -- Overlapping fiscal periods
    SELECT '4a', COUNT(*)
    FROM (
        SELECT DISTINCT fp1.id
        FROM fiscal_periods fp1
        JOIN fiscal_periods fp2
            ON fp1.company_id = fp2.company_id
            AND fp1.id < fp2.id
            AND daterange(fp1.start_date, fp1.end_date, '[]')
                && daterange(fp2.start_date, fp2.end_date, '[]')
    ) AS overlap_periods
)
SELECT
    SUM(count) as total_violations,
    CASE
        WHEN SUM(count) = 0 THEN 'PASSED - Ready for Phase 1 migrations'
        ELSE 'FAILED - Fix violations before proceeding'
    END as status
FROM violation_summary;

\echo ''
\echo 'If status = PASSED, proceed with Phase 1 migrations:'
\echo '  cd backend'
\echo '  alembic upgrade head'
\echo ''
\echo 'If status = FAILED, review violations above and apply remediations.'
\echo ''
\echo '============================================================================'
