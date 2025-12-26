-- Kernel 2025.2 Compliance Verification SQL
-- Run this after master chart reseed to verify compliance

-- =============================================================================
-- CHECK 1: L0 Universal Kernel Completeness (20/20 accounts)
-- =============================================================================

SELECT 'L0 Kernel Completeness' AS check_name;

WITH kernel_l0 AS (
  SELECT unnest(ARRAY[
    '10000', '10100', '12000', '14000', '15000', '15900',
    '20000', '21000', '22000', '23000',
    '30000', '32000', '39999',
    '40000', '49000', '50000',
    '60000', '61000', '62000', '69000'
  ]) AS required_code
)
SELECT
  k.required_code,
  CASE WHEN ma.code IS NOT NULL THEN '✓' ELSE '✗ MISSING' END AS status,
  ma.description
FROM kernel_l0 k
LEFT JOIN master_accounts ma ON k.required_code = ma.code
ORDER BY k.required_code;

-- Expected: 20 rows, all with status '✓'

-- =============================================================================
-- CHECK 2: System Accounts (Retained Earnings, Current Period Earnings)
-- =============================================================================

SELECT 'System Accounts' AS check_name;

SELECT
  code,
  description,
  category,
  CASE
    WHEN code = '32000' THEN '✓ Retained Earnings'
    WHEN code = '39999' THEN '✓ Current Period Earnings'
    ELSE '? Unknown System Account'
  END AS validation
FROM master_accounts
WHERE code IN ('32000', '39999')
ORDER BY code;

-- Expected: 2 rows (32000 and 39999)

-- =============================================================================
-- CHECK 3: L1 Standard Kernel Completeness (35/35 accounts)
-- =============================================================================

SELECT 'L1 Kernel Completeness' AS check_name;

WITH kernel_l1 AS (
  SELECT unnest(ARRAY[
    -- L0 accounts (20)
    '10000', '10100', '12000', '14000', '15000', '15900',
    '20000', '21000', '22000', '23000',
    '30000', '32000', '39999',
    '40000', '49000', '50000',
    '60000', '61000', '62000', '69000',
    -- L1 additional accounts (15)
    '11000', '13000', '16000',
    '24000', '25000',
    '31000',
    '41000', '42000',
    '51000', '52000',
    '63000', '64000', '65000', '66000', '67000'
  ]) AS required_code
)
SELECT
  COUNT(CASE WHEN ma.code IS NOT NULL THEN 1 END) AS present_count,
  35 AS expected_count,
  CASE
    WHEN COUNT(CASE WHEN ma.code IS NOT NULL THEN 1 END) = 35 THEN '✅ PASS'
    ELSE '❌ FAIL'
  END AS status
FROM kernel_l1 k
LEFT JOIN master_accounts ma ON k.required_code = ma.code;

-- Expected: present_count = 35, status = '✅ PASS'

-- =============================================================================
-- CHECK 4: Parent Relationships Integrity
-- =============================================================================

SELECT 'Parent Relationships' AS check_name;

SELECT
  ma.code,
  ma.description,
  p.code AS parent_code,
  p.description AS parent_description
FROM master_accounts ma
LEFT JOIN master_accounts p ON ma.parent_id = p.id
WHERE ma.parent_id IS NOT NULL
ORDER BY ma.code;

-- Expected: Multiple rows with valid parent references

-- Verify no broken parent references
SELECT 'Broken Parent References' AS check_name;

SELECT
  code,
  description,
  parent_code AS expected_parent_code,
  CASE
    WHEN parent_id IS NULL AND parent_code IS NOT NULL THEN '❌ BROKEN'
    ELSE '✓ OK'
  END AS status
FROM master_accounts
WHERE parent_code IS NOT NULL AND parent_id IS NULL;

-- Expected: 0 rows (no broken references)

-- =============================================================================
-- CHECK 5: Category Distribution
-- =============================================================================

SELECT 'Category Distribution' AS check_name;

SELECT
  category,
  COUNT(*) AS account_count
FROM master_accounts
GROUP BY category
ORDER BY category;

-- Expected categories: Asset, Liability, Equity, Revenue, Cost of Goods Sold, Expense

-- =============================================================================
-- CHECK 6: Version Tagging
-- =============================================================================

SELECT 'Version Tagging' AS check_name;

SELECT
  version,
  COUNT(*) AS account_count
FROM master_accounts
GROUP BY version
ORDER BY version;

-- Expected: version = '2025.2' for all kernel accounts

-- =============================================================================
-- CHECK 7: Normal Balance Correctness
-- =============================================================================

SELECT 'Normal Balance Validation' AS check_name;

SELECT
  category,
  normal_balance,
  COUNT(*) AS count,
  CASE
    WHEN category IN ('Asset', 'Expense', 'Cost of Goods Sold') AND normal_balance = 'Debit' THEN '✓'
    WHEN category IN ('Liability', 'Equity', 'Revenue') AND normal_balance = 'Credit' THEN '✓'
    ELSE '❌ INCORRECT'
  END AS validation
FROM master_accounts
GROUP BY category, normal_balance
ORDER BY category, normal_balance;

-- Expected: All validation = '✓'

-- =============================================================================
-- SUMMARY REPORT
-- =============================================================================

SELECT '=== KERNEL 2025.2 COMPLIANCE SUMMARY ===' AS report;

WITH
  l0_check AS (
    SELECT COUNT(*) = 20 AS passed
    FROM master_accounts
    WHERE code IN (
      '10000', '10100', '12000', '14000', '15000', '15900',
      '20000', '21000', '22000', '23000',
      '30000', '32000', '39999',
      '40000', '49000', '50000',
      '60000', '61000', '62000', '69000'
    )
  ),
  l1_check AS (
    SELECT COUNT(*) = 35 AS passed
    FROM master_accounts
    WHERE code IN (
      '10000', '10100', '12000', '14000', '15000', '15900',
      '20000', '21000', '22000', '23000',
      '30000', '32000', '39999',
      '40000', '49000', '50000',
      '60000', '61000', '62000', '69000',
      '11000', '13000', '16000',
      '24000', '25000',
      '31000',
      '41000', '42000',
      '51000', '52000',
      '63000', '64000', '65000', '66000', '67000'
    )
  ),
  system_check AS (
    SELECT COUNT(*) = 2 AS passed
    FROM master_accounts
    WHERE code IN ('32000', '39999')
  )
SELECT
  CASE WHEN l0.passed THEN '✅' ELSE '❌' END || ' L0 Kernel (20 accounts)' AS check_1,
  CASE WHEN l1.passed THEN '✅' ELSE '❌' END || ' L1 Kernel (35 accounts)' AS check_2,
  CASE WHEN sys.passed THEN '✅' ELSE '❌' END || ' System Accounts' AS check_3,
  CASE WHEN l0.passed AND l1.passed AND sys.passed THEN '✅ COMPLIANCE: PASS' ELSE '❌ COMPLIANCE: FAIL' END AS overall_status
FROM l0_check l0, l1_check l1, system_check sys;
