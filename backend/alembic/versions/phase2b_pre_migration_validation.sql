-- ============================================================================
-- PHASE 2B PRE-MIGRATION VALIDATION SCRIPT
-- ============================================================================
-- Purpose: Validate database state before executing Phase 2B migrations
-- Phase: 2B - Schema Cleanup and Optimization
-- Prerequisites: Phase 1 and Phase 2A complete (migration 018)
-- Date: 2025-12-13
--
-- EXECUTE THIS SCRIPT BEFORE RUNNING PHASE 2B MIGRATIONS
--
-- Expected Result: All checks should return 0 violations
-- If any check fails, remediate the issue before proceeding
-- ============================================================================

\set ON_ERROR_STOP on
\timing on

-- ============================================================================
-- PREREQUISITE CHECK 1: Verify Phase 2A Complete
-- ============================================================================
-- Migration 018 must be the current version
-- ============================================================================

DO $$
DECLARE
    v_current_version TEXT;
BEGIN
    SELECT version_num INTO v_current_version FROM alembic_version;

    IF v_current_version != '018' THEN
        RAISE EXCEPTION 'Phase 2A incomplete. Current migration: %, Expected: 018', v_current_version
            USING HINT = 'Run `alembic upgrade 018` before executing Phase 2B';
    END IF;

    RAISE NOTICE '✓ Prerequisite Check 1: Phase 2A complete (migration 018)';
END $$;

-- ============================================================================
-- VALIDATION CHECK 1: Verify Legacy Column Migration Complete
-- ============================================================================
-- All parent_code values should be migrated to parent_id
-- All master_account_code values should be migrated to mapped_master_account_id
-- ============================================================================

-- Check 1a: Unmigrated parent_code values
SELECT
    COUNT(*) as unmigrated_parent_code_count,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ PASS'
        ELSE '✗ FAIL - ' || COUNT(*) || ' unmigrated parent_code values'
    END as status
FROM company_accounts
WHERE parent_code IS NOT NULL
  AND parent_id IS NULL;

-- Check 1b: Unmigrated master_account_code values
SELECT
    COUNT(*) as unmigrated_master_code_count,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ PASS'
        ELSE '✗ FAIL - ' || COUNT(*) || ' unmigrated master_account_code values'
    END as status
FROM company_accounts
WHERE master_account_code IS NOT NULL
  AND mapped_master_account_id IS NULL;

-- ============================================================================
-- VALIDATION CHECK 2: Verify NULL Value Candidates for NOT NULL Constraints
-- ============================================================================
-- Check which columns can safely have NOT NULL constraints added
-- ============================================================================

-- Check 2a: is_locked NULL values
SELECT
    COUNT(*) FILTER (WHERE is_locked IS NULL) as null_is_locked_count,
    COUNT(*) as total_accounts,
    CASE
        WHEN COUNT(*) FILTER (WHERE is_locked IS NULL) = 0 THEN '✓ PASS - Can add NOT NULL to is_locked'
        ELSE '⚠ WARNING - ' || COUNT(*) FILTER (WHERE is_locked IS NULL) || ' NULL is_locked values'
    END as status
FROM company_accounts;

-- Check 2b: normal_balance NULL values
SELECT
    COUNT(*) FILTER (WHERE normal_balance IS NULL) as null_normal_balance_count,
    COUNT(*) as total_accounts,
    CASE
        WHEN COUNT(*) FILTER (WHERE normal_balance IS NULL) = 0 THEN '✓ PASS - Can add NOT NULL to normal_balance'
        ELSE '⚠ WARNING - ' || COUNT(*) FILTER (WHERE normal_balance IS NULL) || ' NULL normal_balance values'
    END as status
FROM company_accounts;

-- Check 2c: account_type NULL values
SELECT
    COUNT(*) FILTER (WHERE account_type IS NULL) as null_account_type_count,
    COUNT(*) as total_accounts,
    CASE
        WHEN COUNT(*) FILTER (WHERE account_type IS NULL) = 0 THEN '✓ PASS - Can add NOT NULL to account_type'
        ELSE '⚠ WARNING - ' || COUNT(*) FILTER (WHERE account_type IS NULL) || ' NULL account_type values'
    END as status
FROM company_accounts;

-- ============================================================================
-- VALIDATION CHECK 3: Verify locked_by References
-- ============================================================================
-- All locked_by values must reference valid users
-- ============================================================================

SELECT
    COUNT(*) as orphaned_locked_by_count,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ PASS - All locked_by references valid'
        ELSE '✗ FAIL - ' || COUNT(*) || ' orphaned locked_by references'
    END as status
FROM company_accounts ca
WHERE ca.locked_by IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM users u WHERE u.id = ca.locked_by
  );

-- ============================================================================
-- VALIDATION CHECK 4: Verify Chart Template Accounts Seeded
-- ============================================================================
-- chart_template_accounts should be populated for active templates
-- ============================================================================

SELECT
    ct.id,
    ct.name,
    ct.jurisdiction,
    ct.version,
    COUNT(cta.id) as account_count,
    CASE
        WHEN COUNT(cta.id) >= 50 THEN '✓ PASS'
        WHEN COUNT(cta.id) = 0 THEN '✗ FAIL - No accounts seeded'
        ELSE '⚠ WARNING - Only ' || COUNT(cta.id) || ' accounts (expected >= 50)'
    END as status
FROM chart_templates ct
LEFT JOIN chart_template_accounts cta ON cta.template_id = ct.id
WHERE ct.is_active = true
GROUP BY ct.id, ct.name, ct.jurisdiction, ct.version
ORDER BY ct.jurisdiction, ct.version;

-- ============================================================================
-- VALIDATION CHECK 5: Verify Master Accounts Exist
-- ============================================================================
-- master_accounts table must be populated for template seeding
-- ============================================================================

SELECT
    COUNT(*) as master_account_count,
    COUNT(CASE WHEN type = 'H' THEN 1 END) as header_count,
    COUNT(CASE WHEN type = 'D' THEN 1 END) as detail_count,
    CASE
        WHEN COUNT(*) >= 300 THEN '✓ PASS - Master accounts populated'
        WHEN COUNT(*) = 0 THEN '✗ FAIL - No master accounts (run seeder first)'
        ELSE '⚠ WARNING - Only ' || COUNT(*) || ' master accounts (expected >= 300)'
    END as status
FROM master_accounts;

-- ============================================================================
-- VALIDATION CHECK 6: Phase 1 Invariants Still Intact
-- ============================================================================
-- Verify all Phase 1 triggers and constraints still functioning
-- ============================================================================

-- Check 6a: Trigger existence
SELECT
    COUNT(*) as trigger_count,
    CASE
        WHEN COUNT(*) >= 7 THEN '✓ PASS - All Phase 1 triggers exist'
        ELSE '✗ FAIL - Missing triggers: ' || (7 - COUNT(*))
    END as status
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
      'trg_enforce_debit_xor_credit',
      'trg_auto_lock_account_on_first_transaction',
      'trg_prevent_locked_account_mutation',
      'trg_prevent_posted_entry_mutation',
      'trg_prevent_company_account_hierarchy_cycle',
      'trg_enforce_same_company_parent',
      'trg_enforce_master_mapping_consistency'
  );

-- Check 6b: Constraint existence
SELECT
    COUNT(*) as constraint_count,
    CASE
        WHEN COUNT(*) >= 5 THEN '✓ PASS - All Phase 1 constraints exist'
        ELSE '✗ FAIL - Missing constraints: ' || (5 - COUNT(*))
    END as status
FROM information_schema.table_constraints
WHERE constraint_schema = 'public'
  AND constraint_name IN (
      'chk_debit_xor_credit',
      'chk_lock_consistency',
      'exclude_fiscal_period_overlap',
      'uq_company_accounts_company_code',
      'uq_company_accounts_company_name'
  );

-- ============================================================================
-- VALIDATION CHECK 7: Verify Phase 2A Tables Exist
-- ============================================================================
-- All Phase 2A tables must exist before Phase 2B
-- ============================================================================

SELECT
    COUNT(*) as table_count,
    CASE
        WHEN COUNT(*) = 3 THEN '✓ PASS - All Phase 2A tables exist'
        ELSE '✗ FAIL - Missing tables: ' || (3 - COUNT(*))
    END as status
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'chart_templates',
      'chart_template_accounts',
      'company_template_usage'
  );

-- ============================================================================
-- VALIDATION CHECK 8: Verify No Data Loss Risk
-- ============================================================================
-- Check that parent_code and master_account_code have been successfully
-- migrated before we drop them
-- ============================================================================

-- Check 8a: Compare parent_code vs parent_id population
WITH migration_status AS (
    SELECT
        COUNT(*) FILTER (WHERE parent_code IS NOT NULL) as has_parent_code,
        COUNT(*) FILTER (WHERE parent_id IS NOT NULL) as has_parent_id,
        COUNT(*) FILTER (WHERE parent_code IS NOT NULL AND parent_id IS NULL) as unmigrated
    FROM company_accounts
)
SELECT
    has_parent_code,
    has_parent_id,
    unmigrated,
    CASE
        WHEN unmigrated = 0 THEN '✓ PASS - Safe to drop parent_code'
        ELSE '✗ FAIL - Cannot drop parent_code: ' || unmigrated || ' unmigrated records'
    END as status
FROM migration_status;

-- Check 8b: Compare master_account_code vs mapped_master_account_id population
WITH migration_status AS (
    SELECT
        COUNT(*) FILTER (WHERE master_account_code IS NOT NULL) as has_master_code,
        COUNT(*) FILTER (WHERE mapped_master_account_id IS NOT NULL) as has_master_id,
        COUNT(*) FILTER (WHERE master_account_code IS NOT NULL AND mapped_master_account_id IS NULL) as unmigrated
    FROM company_accounts
)
SELECT
    has_master_code,
    has_master_id,
    unmigrated,
    CASE
        WHEN unmigrated = 0 THEN '✓ PASS - Safe to drop master_account_code'
        ELSE '✗ FAIL - Cannot drop master_account_code: ' || unmigrated || ' unmigrated records'
    END as status
FROM migration_status;

-- ============================================================================
-- VALIDATION CHECK 9: Verify Index Candidates
-- ============================================================================
-- Identify performance optimization opportunities
-- ============================================================================

-- Check 9a: Existing indexes on company_accounts
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'company_accounts'
  AND schemaname = 'public'
ORDER BY indexname;

-- Check 9b: Table sizes for performance planning
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE relname IN ('company_accounts', 'chart_templates', 'chart_template_accounts', 'master_accounts')
ORDER BY pg_total_relation_size(relid) DESC;

-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================

DO $$
DECLARE
    v_unmigrated_parent INTEGER;
    v_unmigrated_master INTEGER;
    v_orphaned_locked_by INTEGER;
    v_master_account_count INTEGER;
    v_template_account_count INTEGER;
    v_ready_for_phase2b BOOLEAN := true;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=========================================================================';
    RAISE NOTICE 'PHASE 2B PRE-MIGRATION VALIDATION SUMMARY';
    RAISE NOTICE '=========================================================================';

    -- Count issues
    SELECT COUNT(*) INTO v_unmigrated_parent
    FROM company_accounts WHERE parent_code IS NOT NULL AND parent_id IS NULL;

    SELECT COUNT(*) INTO v_unmigrated_master
    FROM company_accounts WHERE master_account_code IS NOT NULL AND mapped_master_account_id IS NULL;

    SELECT COUNT(*) INTO v_orphaned_locked_by
    FROM company_accounts ca
    WHERE ca.locked_by IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = ca.locked_by);

    SELECT COUNT(*) INTO v_master_account_count FROM master_accounts;
    SELECT COUNT(*) INTO v_template_account_count FROM chart_template_accounts;

    -- Report
    RAISE NOTICE 'Unmigrated parent_code values: %', v_unmigrated_parent;
    RAISE NOTICE 'Unmigrated master_account_code values: %', v_unmigrated_master;
    RAISE NOTICE 'Orphaned locked_by references: %', v_orphaned_locked_by;
    RAISE NOTICE 'Master accounts populated: %', v_master_account_count;
    RAISE NOTICE 'Template accounts populated: %', v_template_account_count;
    RAISE NOTICE '';

    -- Determine readiness
    IF v_unmigrated_parent > 0 THEN
        v_ready_for_phase2b := false;
        RAISE NOTICE '✗ BLOCKER: Unmigrated parent_code values detected';
    END IF;

    IF v_unmigrated_master > 0 THEN
        v_ready_for_phase2b := false;
        RAISE NOTICE '✗ BLOCKER: Unmigrated master_account_code values detected';
    END IF;

    IF v_orphaned_locked_by > 0 THEN
        v_ready_for_phase2b := false;
        RAISE NOTICE '✗ BLOCKER: Orphaned locked_by references detected';
    END IF;

    IF v_master_account_count = 0 THEN
        v_ready_for_phase2b := false;
        RAISE NOTICE '✗ BLOCKER: Master accounts table empty (run migration 019 first)';
    END IF;

    RAISE NOTICE '';
    IF v_ready_for_phase2b THEN
        RAISE NOTICE '=========================================================================';
        RAISE NOTICE '✓ READY FOR PHASE 2B MIGRATIONS';
        RAISE NOTICE '=========================================================================';
        RAISE NOTICE 'All prerequisite checks passed.';
        RAISE NOTICE 'You may proceed with: alembic upgrade head';
    ELSE
        RAISE NOTICE '=========================================================================';
        RAISE NOTICE '✗ NOT READY FOR PHASE 2B';
        RAISE NOTICE '=========================================================================';
        RAISE NOTICE 'Resolve blockers above before proceeding.';
        RAISE EXCEPTION 'Phase 2B prerequisites not met';
    END IF;
END $$;
