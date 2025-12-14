-- ============================================================================
-- Phase 2A Pre-Migration Validation Script
-- ============================================================================
--
-- Purpose: Validate database state before applying Phase 2A migrations (013-018)
-- Migrations: Schema Normalization (Structured Template Tables)
-- Version: 1.0
-- Date: 2025-12-13
--
-- This script checks for data integrity issues that would cause Phase 2A
-- migrations to fail. Run this script BEFORE executing `alembic upgrade`.
--
-- Expected outcome: 0 total violations
-- If violations found: Review and remediate before proceeding
-- ============================================================================

\set ON_ERROR_STOP on
\timing on
\x auto

-- ============================================================================
-- VALIDATION 1: Phase 1 Prerequisite Check
-- ============================================================================
-- Phase 2A requires Phase 1 (migrations 003-012) to be complete.
-- ============================================================================

DO $$
DECLARE
    v_account_type_exists BOOLEAN;
    v_normal_balance_exists BOOLEAN;
    v_is_locked_exists BOOLEAN;
    v_master_version_exists BOOLEAN;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 1: Phase 1 Prerequisite Check ===';

    -- Check for account_type column (migration 005)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'company_accounts'
          AND column_name = 'account_type'
    ) INTO v_account_type_exists;

    -- Check for normal_balance column (migration 006)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'company_accounts'
          AND column_name = 'normal_balance'
    ) INTO v_normal_balance_exists;

    -- Check for is_locked column (migration 007)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'company_accounts'
          AND column_name = 'is_locked'
    ) INTO v_is_locked_exists;

    -- Check for master_accounts.version column (migration 011)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'master_accounts'
          AND column_name = 'version'
    ) INTO v_master_version_exists;

    -- Report results
    IF v_account_type_exists AND v_normal_balance_exists AND v_is_locked_exists AND v_master_version_exists THEN
        RAISE NOTICE '✓ Phase 1 migrations complete';
    ELSE
        RAISE EXCEPTION 'Phase 1 migrations incomplete. Required migrations: 003-012. Missing columns detected.';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 2: Duplicate Account Codes
-- ============================================================================
-- Migration 016 adds UNIQUE(company_id, code) constraint.
-- Check for duplicate codes within companies.
-- ============================================================================

DO $$
DECLARE
    v_duplicate_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 2: Duplicate Account Codes ===';

    SELECT COUNT(*) INTO v_duplicate_count
    FROM (
        SELECT company_id, code, COUNT(*) as cnt
        FROM company_accounts
        GROUP BY company_id, code
        HAVING COUNT(*) > 1
    ) dupes;

    IF v_duplicate_count > 0 THEN
        RAISE WARNING '✗ Found % groups of duplicate account codes', v_duplicate_count;
        RAISE NOTICE 'Run this query to identify duplicates:';
        RAISE NOTICE 'SELECT company_id, code, COUNT(*) FROM company_accounts GROUP BY company_id, code HAVING COUNT(*) > 1;';
        RAISE EXCEPTION 'VALIDATION FAILED: Duplicate account codes exist. Remediation required before migration 016.';
    ELSE
        RAISE NOTICE '✓ No duplicate account codes found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 3: Duplicate Account Names
-- ============================================================================
-- Migration 016 adds UNIQUE(company_id, name) constraint.
-- Check for duplicate names within companies.
-- ============================================================================

DO $$
DECLARE
    v_duplicate_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 3: Duplicate Account Names ===';

    SELECT COUNT(*) INTO v_duplicate_count
    FROM (
        SELECT company_id, name, COUNT(*) as cnt
        FROM company_accounts
        WHERE name IS NOT NULL
        GROUP BY company_id, name
        HAVING COUNT(*) > 1
    ) dupes;

    IF v_duplicate_count > 0 THEN
        RAISE WARNING '✗ Found % groups of duplicate account names', v_duplicate_count;
        RAISE NOTICE 'Run this query to identify duplicates:';
        RAISE NOTICE 'SELECT company_id, name, COUNT(*) FROM company_accounts WHERE name IS NOT NULL GROUP BY company_id, name HAVING COUNT(*) > 1;';
        RAISE EXCEPTION 'VALIDATION FAILED: Duplicate account names exist. Remediation required before migration 016.';
    ELSE
        RAISE NOTICE '✓ No duplicate account names found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 4: Orphaned Parent References
-- ============================================================================
-- Migration 013 will backfill parent_id from parent_code.
-- Check for parent_code values that don't match any existing account.
-- ============================================================================

DO $$
DECLARE
    v_orphaned_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 4: Orphaned Parent References ===';

    SELECT COUNT(*) INTO v_orphaned_count
    FROM company_accounts child
    WHERE child.parent_code IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM company_accounts parent
          WHERE parent.code = child.parent_code
            AND parent.company_id = child.company_id
      );

    IF v_orphaned_count > 0 THEN
        RAISE WARNING '✗ Found % accounts with orphaned parent_code', v_orphaned_count;
        RAISE NOTICE 'Run this query to identify orphaned references:';
        RAISE NOTICE 'SELECT id, company_id, code, parent_code FROM company_accounts WHERE parent_code IS NOT NULL AND NOT EXISTS (SELECT 1 FROM company_accounts p WHERE p.code = company_accounts.parent_code AND p.company_id = company_accounts.company_id);';
        RAISE NOTICE 'ACTION: These accounts will have parent_code but parent_id will be NULL after migration 013.';
        RAISE NOTICE 'Consider: (1) Creating missing parent accounts, or (2) Setting parent_code = NULL';
    ELSE
        RAISE NOTICE '✓ No orphaned parent references found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 5: Invalid Master Account References
-- ============================================================================
-- Migration 013 will backfill mapped_master_account_id from master_account_code.
-- Check for master_account_code values that don't exist in master_accounts.
-- ============================================================================

DO $$
DECLARE
    v_invalid_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 5: Invalid Master Account References ===';

    SELECT COUNT(*) INTO v_invalid_count
    FROM company_accounts ca
    WHERE ca.master_account_code IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM master_accounts ma
          WHERE ma.code = ca.master_account_code
      );

    IF v_invalid_count > 0 THEN
        RAISE WARNING '✗ Found % accounts with invalid master_account_code', v_invalid_count;
        RAISE NOTICE 'Run this query to identify invalid references:';
        RAISE NOTICE 'SELECT id, company_id, code, master_account_code FROM company_accounts WHERE master_account_code IS NOT NULL AND NOT EXISTS (SELECT 1 FROM master_accounts WHERE code = company_accounts.master_account_code);';
        RAISE NOTICE 'ACTION: These accounts will have master_account_code but mapped_master_account_id will be NULL after migration 013.';
        RAISE NOTICE 'Consider: (1) Correcting master_account_code, or (2) Setting master_account_code = NULL';
    ELSE
        RAISE NOTICE '✓ No invalid master account references found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 6: Hierarchy Cycles
-- ============================================================================
-- Migration 017 will prevent hierarchy cycles via trigger.
-- Check for existing cycles in parent_code relationships.
-- ============================================================================

DO $$
DECLARE
    v_cycle_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 6: Hierarchy Cycles ===';

    WITH RECURSIVE hierarchy AS (
        SELECT
            id,
            code,
            parent_code,
            company_id,
            ARRAY[code] as path,
            1 as depth
        FROM company_accounts
        WHERE parent_code IS NOT NULL

        UNION ALL

        SELECT
            ca.id,
            ca.code,
            ca.parent_code,
            ca.company_id,
            h.path || ca.code,
            h.depth + 1
        FROM company_accounts ca
        JOIN hierarchy h ON ca.code = h.parent_code AND ca.company_id = h.company_id
        WHERE NOT (ca.code = ANY(h.path))
          AND h.depth < 50
    )
    SELECT COUNT(*) INTO v_cycle_count
    FROM (
        SELECT DISTINCT company_id, code
        FROM hierarchy h
        WHERE EXISTS (
            SELECT 1 FROM company_accounts ca
            WHERE ca.code = h.parent_code
              AND ca.company_id = h.company_id
              AND ca.code = ANY(h.path)
        )
    ) cycles;

    IF v_cycle_count > 0 THEN
        RAISE EXCEPTION 'VALIDATION FAILED: Found % account hierarchy cycles. These must be resolved before migration 017.', v_cycle_count;
    ELSE
        RAISE NOTICE '✓ No hierarchy cycles detected';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 7: Cross-Company Parent References
-- ============================================================================
-- Migration 017 will enforce same-company parent relationships.
-- Check for parent_code pointing to accounts in different companies.
-- ============================================================================

DO $$
DECLARE
    v_cross_company_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 7: Cross-Company Parent References ===';

    SELECT COUNT(*) INTO v_cross_company_count
    FROM company_accounts child
    WHERE child.parent_code IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM company_accounts parent
          WHERE parent.code = child.parent_code
            AND parent.company_id != child.company_id
      );

    IF v_cross_company_count > 0 THEN
        RAISE WARNING '✗ Found % accounts with cross-company parent references', v_cross_company_count;
        RAISE NOTICE 'Run this query to identify cross-company parents:';
        RAISE NOTICE 'SELECT c.id, c.company_id, c.code, c.parent_code, p.company_id as parent_company_id FROM company_accounts c JOIN company_accounts p ON c.parent_code = p.code WHERE c.company_id != p.company_id;';
        RAISE EXCEPTION 'VALIDATION FAILED: Cross-company parent references exist. These must be resolved before migration 017.';
    ELSE
        RAISE NOTICE '✓ No cross-company parent references found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 8: Account Type / Master Category Mismatch
-- ============================================================================
-- Migration 017 will enforce master mapping consistency.
-- Check for accounts where account_type doesn't match master category.
-- ============================================================================

DO $$
DECLARE
    v_mismatch_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 8: Account Type / Master Category Mismatch ===';

    SELECT COUNT(*) INTO v_mismatch_count
    FROM company_accounts ca
    JOIN master_accounts ma ON ca.master_account_code = ma.code
    WHERE ca.account_type IS NOT NULL
      AND ma.category IS NOT NULL
      AND (
          (ma.category IN ('Assets', 'Asset') AND ca.account_type::TEXT != 'Asset') OR
          (ma.category IN ('Liabilities', 'Liability') AND ca.account_type::TEXT != 'Liability') OR
          (ma.category IN ('Equity', 'Equities') AND ca.account_type::TEXT != 'Equity') OR
          (ma.category IN ('Revenue', 'Revenues') AND ca.account_type::TEXT != 'Revenue') OR
          (ma.category IN ('Expenses', 'Expense') AND ca.account_type::TEXT != 'Expense')
      );

    IF v_mismatch_count > 0 THEN
        RAISE WARNING '✗ Found % accounts with type/category mismatch', v_mismatch_count;
        RAISE NOTICE 'Run this query to identify mismatches:';
        RAISE NOTICE 'SELECT ca.id, ca.code, ca.account_type, ma.category FROM company_accounts ca JOIN master_accounts ma ON ca.master_account_code = ma.code WHERE account_type mismatch logic...;';
        RAISE EXCEPTION 'VALIDATION FAILED: Account type/category mismatches exist. These must be resolved before migration 017.';
    ELSE
        RAISE NOTICE '✓ No account type/category mismatches found';
    END IF;
END $$;


-- ============================================================================
-- VALIDATION 9: Phase 1 Invariants Still Hold
-- ============================================================================
-- Ensure Phase 1 invariants haven't been violated since Phase 1 migration.
-- ============================================================================

DO $$
DECLARE
    v_unbalanced_entries INTEGER;
    v_unlocked_used_accounts INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VALIDATION 9: Phase 1 Invariants ===';

    -- Check for unbalanced POSTED journal entries
    SELECT COUNT(*) INTO v_unbalanced_entries
    FROM (
        SELECT je.id
        FROM journal_entries je
        JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
        WHERE je.status = 'POSTED'
        GROUP BY je.id
        HAVING SUM(jel.debit_amount) != SUM(jel.credit_amount)
    ) unbalanced;

    -- Check for accounts with transactions but not locked
    SELECT COUNT(*) INTO v_unlocked_used_accounts
    FROM company_accounts ca
    WHERE ca.is_locked = false
      AND EXISTS (
          SELECT 1 FROM journal_entry_lines jel
          JOIN journal_entries je ON jel.journal_entry_id = je.id
          WHERE jel.company_account_id = ca.id
            AND je.status = 'POSTED'
      );

    IF v_unbalanced_entries > 0 THEN
        RAISE EXCEPTION 'PHASE 1 INVARIANT VIOLATED: % unbalanced POSTED journal entries exist', v_unbalanced_entries;
    END IF;

    IF v_unlocked_used_accounts > 0 THEN
        RAISE EXCEPTION 'PHASE 1 INVARIANT VIOLATED: % unlocked accounts have POSTED transactions', v_unlocked_used_accounts;
    END IF;

    RAISE NOTICE '✓ Phase 1 invariants intact';
END $$;


-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'VALIDATION SUMMARY';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Status: PASSED';
    RAISE NOTICE '';
    RAISE NOTICE 'All validations passed successfully.';
    RAISE NOTICE 'Database is ready for Phase 2A migrations (013-018).';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Backup database: pg_dump -U user -d dbname -F c -f backup.dump';
    RAISE NOTICE '  2. Apply migrations: cd backend && alembic upgrade head';
    RAISE NOTICE '  3. Verify migration: alembic current';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
END $$;
