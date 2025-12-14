# Phase 1 Migration Guide: Critical Data Integrity

**Version:** 1.0
**Date:** 2025-12-13
**Migrations:** 003 through 012
**Target:** Chart of Accounts Canonical Compliance

---

## Overview

Phase 1 implements critical database-level integrity constraints to ensure GAAP compliance and prevent data corruption in the Aequitas accounting system. These migrations add foundational enforcement that cannot be bypassed by application code.

**Total Migrations:** 10
**Estimated Duration:** 2-3 weeks
**Complexity:** High (breaking changes require data validation)
**Rollback:** Supported via Alembic downgrade

---

## Migration Sequence

### Summary Table

| Migration | File | Description | Breaking | Data Migration | Estimated Time |
|-----------|------|-------------|----------|----------------|----------------|
| 003 | `add_journal_entry_line_constraints.py` | Positive amounts, debit XOR credit | ✅ Yes | Validation only | 5 min |
| 004 | `add_double_entry_balance_trigger.py` | Balance validation for POSTED entries | ✅ Yes | Validation only | 10 min |
| 005 | `add_account_type_to_company_accounts.py` | Add account_type enum | ✅ Yes | Backfill from master | 15 min |
| 006 | `add_normal_balance_to_company_accounts.py` | Add normal_balance enum | ❌ No | Auto-derive from type | 5 min |
| 007 | `add_account_locking_fields.py` | Add locking mechanism | ❌ No | Lock accounts with txns | 10 min |
| 008 | `add_account_auto_lock_trigger.py` | Auto-lock on first use | ❌ No | Trigger only | 2 min |
| 009 | `add_account_immutability_trigger.py` | Prevent locked account changes | ❌ No | Trigger only | 2 min |
| 010 | `add_posted_entry_immutability_trigger.py` | Prevent posted entry edits | ❌ No | Trigger only | 5 min |
| 011 | `add_master_account_version.py` | Version tracking | ❌ No | Default to '2024.1' | 2 min |
| 012 | `add_fiscal_period_overlap_prevention.py` | Prevent overlapping periods | ✅ Yes | Validation only | 5 min |

**Total estimated time:** ~60 minutes (excluding data cleanup)

---

## Breaking Changes

### Migration 003: Journal Entry Line Constraints

**What breaks:**
- Existing journal entry lines with negative amounts
- Lines with both debit AND credit non-zero
- Lines with both debit AND credit zero

**Error message:**
```
ERROR:  new row for relation "journal_entry_lines" violates check constraint "jel_positive_amounts"
ERROR:  new row for relation "journal_entry_lines" violates check constraint "jel_debit_xor_credit"
```

**Remediation:**
```sql
-- Fix negative amounts (make absolute)
UPDATE journal_entry_lines
SET debit_amount = ABS(debit_amount),
    credit_amount = ABS(credit_amount)
WHERE debit_amount < 0 OR credit_amount < 0;

-- Delete lines with no amount
DELETE FROM journal_entry_lines
WHERE debit_amount = 0 AND credit_amount = 0;

-- Fix lines with both debit and credit (manual review required)
-- Determine which side is correct for each line
```

---

### Migration 004: Double-Entry Balance Trigger

**What breaks:**
- POSTED journal entries where SUM(debits) ≠ SUM(credits)
- POSTED entries with no lines

**Error message:**
```
ERROR:  Journal entry JE-2024-001 (id: ...) does not balance: debits = 1000.00, credits = 950.00
ERROR:  Cannot post journal entry JE-2024-002 with no lines
```

**Remediation:**
```sql
-- Identify unbalanced POSTED entries
SELECT
    je.id,
    je.entry_number,
    SUM(jel.debit_amount) as total_debits,
    SUM(jel.credit_amount) as total_credits,
    SUM(jel.debit_amount) - SUM(jel.credit_amount) as difference
FROM journal_entries je
JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
WHERE je.status = 'POSTED'
GROUP BY je.id, je.entry_number
HAVING SUM(jel.debit_amount) != SUM(jel.credit_amount);

-- Option 1: Change status to DRAFT
UPDATE journal_entries
SET status = 'DRAFT'
WHERE id IN (...unbalanced entry ids...);

-- Option 2: Add adjusting line to balance
-- (requires manual determination of correct account)

-- Delete entries with no lines
DELETE FROM journal_entries
WHERE id NOT IN (SELECT DISTINCT journal_entry_id FROM journal_entry_lines);
```

---

### Migration 005: Account Type to CompanyAccount

**What breaks:**
- Company accounts without valid master_account_code mapping
- Company accounts with codes that don't match standard prefixes

**Error message:**
```
WARNING:  Found X company accounts without account_type classification
```

**Remediation:**
Migration handles most cases via backfill logic:
1. Maps from master_account.category (if master_account_code exists)
2. Falls back to code prefix heuristics:
   - `1.*` → Asset
   - `2.*` → Liability
   - `3.*` → Equity
   - `4.*` → Revenue
   - `5-6.*` → Expense

**Manual fix for unmapped accounts:**
```sql
-- Identify unmapped accounts
SELECT id, company_id, code, description
FROM company_accounts
WHERE account_type IS NULL;

-- Manually classify (example)
UPDATE company_accounts
SET account_type = 'Asset'
WHERE id = '...';
```

---

### Migration 012: Fiscal Period Overlap Prevention

**What breaks:**
- Overlapping fiscal periods for the same company

**Error message:**
```
ERROR:  Cannot add overlap prevention constraint: X overlapping periods exist
ERROR:  conflicting key value violates exclusion constraint "exclude_overlapping_fiscal_periods"
```

**Remediation:**
```sql
-- Identify overlapping periods
SELECT
    fp1.company_id,
    fp1.period_number,
    fp1.start_date,
    fp1.end_date,
    fp2.period_number,
    fp2.start_date,
    fp2.end_date
FROM fiscal_periods fp1
JOIN fiscal_periods fp2
    ON fp1.company_id = fp2.company_id
    AND fp1.id < fp2.id
    AND daterange(fp1.start_date, fp1.end_date, '[]')
        && daterange(fp2.start_date, fp2.end_date, '[]')
WHERE fp1.status != 'ARCHIVED' AND fp2.status != 'ARCHIVED';

-- Option 1: Adjust dates to eliminate overlap
UPDATE fiscal_periods
SET end_date = '2024-01-31'
WHERE id = '...';

-- Option 2: Delete duplicate period
DELETE FROM fiscal_periods
WHERE id = '...';

-- Option 3: Archive historical period
UPDATE fiscal_periods
SET status = 'ARCHIVED'
WHERE id = '...';
```

---

## Non-Breaking Changes

### Migration 006: Normal Balance

**Changes:** Adds `normal_balance` enum column to `company_accounts`

**Data migration:** Auto-derives from `account_type`:
- Asset → Debit
- Expense → Debit
- Liability → Credit
- Equity → Credit
- Revenue → Credit

**No action required** if Migration 005 succeeds.

---

### Migration 007: Account Locking Fields

**Changes:** Adds `is_locked`, `locked_at`, `locked_by`, `locked_reason` to `company_accounts`

**Data migration:** Automatically locks accounts that have been used in POSTED journal entries.

**Impact:** Accounts with transaction history will be locked. Changes to `account_type`, `code`, `normal_balance` will be prevented by subsequent triggers.

**No action required** - automatic backfill.

---

### Migrations 008-010: Triggers

**Changes:** Add database triggers for enforcement

**Impact:** Future operations will be blocked if they violate rules. No existing data is modified.

**No action required** - enforcement only.

---

### Migration 011: Master Account Version

**Changes:** Adds `version` VARCHAR field to `master_accounts`

**Data migration:** Sets all existing accounts to version '2024.1'

**No action required** - automatic backfill.

---

## Pre-Migration Checklist

**Before applying Phase 1 migrations, complete the following:**

### 1. Backup Database

```bash
pg_dump -U user -d aequitas_dev -F c -f aequitas_backup_$(date +%Y%m%d).dump
```

**Restore command** (if rollback needed):
```bash
pg_restore -U user -d aequitas_dev -c aequitas_backup_YYYYMMDD.dump
```

---

### 2. Run Pre-Migration Validation Script

```bash
cd backend/alembic/versions
psql -U user -d aequitas_dev -f pre_migration_validation.sql
```

**Expected output:**
```
VALIDATION SUMMARY
============================================================================

total_violations | status
-----------------+----------------------------------------
               0 | PASSED - Ready for Phase 1 migrations
```

**If FAILED:**
- Review violation details in script output
- Apply remediations listed
- Re-run validation until PASSED

---

### 3. Application Downtime Planning

**Required downtime:** Recommended but not strictly required

**Rationale:**
- Migrations 003, 004, 012 add constraints that may fail if concurrent writes occur
- Total migration time: ~60 minutes
- Conservative approach: Schedule maintenance window

**Alternative:** Read-only mode
```sql
-- Set database to read-only during migration
ALTER DATABASE aequitas_dev SET default_transaction_read_only = on;

-- After migration complete
ALTER DATABASE aequitas_dev SET default_transaction_read_only = off;
```

---

### 4. Review Current Alembic State

```bash
cd backend
alembic current
```

**Expected output:**
```
002 (head)
```

**If different:**
- Ensure all prior migrations are applied
- Resolve any pending migrations before Phase 1

---

## Migration Execution

### Step 1: Apply Migrations

```bash
cd backend
alembic upgrade head
```

**Output monitoring:**
- Watch for `RAISE WARNING` messages indicating data issues
- Watch for `RAISE NOTICE` messages with migration progress
- Watch for `ERROR` messages that halt migration

**If migration fails midway:**
1. Note which migration failed
2. Review error message
3. Apply remediation from "Breaking Changes" section above
4. Resume: `alembic upgrade head`

---

### Step 2: Verify Migration Success

```bash
alembic current
```

**Expected output:**
```
012 (head)
```

**Verify table structure:**
```sql
-- Check new columns added
\d company_accounts

-- Expected columns:
-- - account_type (accounttype enum)
-- - normal_balance (normalbalance enum)
-- - is_locked (boolean)
-- - locked_at (timestamp)
-- - locked_by (uuid)
-- - locked_reason (lockedreason enum)

-- Check new constraints
\d journal_entry_lines

-- Expected constraints:
-- - jel_positive_amounts
-- - jel_debit_xor_credit

-- Check new triggers
SELECT tgname, tgrelid::regclass, tgtype
FROM pg_trigger
WHERE tgname LIKE 'trg_%'
ORDER BY tgrelid::regclass::text;

-- Expected triggers:
-- - trg_validate_balance_after_insert (journal_entry_lines)
-- - trg_validate_balance_after_update (journal_entry_lines)
-- - trg_validate_balance_after_delete (journal_entry_lines)
-- - trg_validate_balance_on_status_change (journal_entries)
-- - trg_auto_lock_account_on_first_transaction (journal_entry_lines)
-- - trg_prevent_locked_account_mutation (company_accounts)
-- - trg_prevent_posted_entry_modification (journal_entries)
-- - trg_prevent_posted_entry_deletion (journal_entries)
-- - trg_prevent_posted_line_modification (journal_entry_lines)
-- - trg_prevent_posted_line_deletion (journal_entry_lines)
```

---

### Step 3: Post-Migration Validation

Run comprehensive validation tests:

```sql
-- 1. Verify all journal entries balance
SELECT COUNT(*) FROM (
  SELECT je.id
  FROM journal_entries je
  JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
  WHERE je.status = 'POSTED'
  GROUP BY je.id
  HAVING SUM(jel.debit_amount) != SUM(jel.credit_amount)
) unbalanced;
-- Expected: 0

-- 2. Verify all company accounts have account_type and normal_balance
SELECT COUNT(*) FROM company_accounts
WHERE account_type IS NULL OR normal_balance IS NULL;
-- Expected: 0

-- 3. Verify accounts with transactions are locked
SELECT COUNT(*) FROM company_accounts ca
WHERE EXISTS (
  SELECT 1 FROM journal_entry_lines jel
  JOIN journal_entries je ON jel.journal_entry_id = je.id
  WHERE jel.company_account_id = ca.id
    AND je.status = 'POSTED'
) AND ca.is_locked = false;
-- Expected: 0

-- 4. Verify no overlapping fiscal periods
SELECT COUNT(*) FROM (
  SELECT fp1.id
  FROM fiscal_periods fp1
  JOIN fiscal_periods fp2
    ON fp1.company_id = fp2.company_id
    AND fp1.id != fp2.id
    AND daterange(fp1.start_date, fp1.end_date, '[]')
        && daterange(fp2.start_date, fp2.end_date, '[]')
  WHERE fp1.status != 'ARCHIVED' AND fp2.status != 'ARCHIVED'
) overlaps;
-- Expected: 0
```

---

### Step 4: Test Critical User Flows

**Manual testing checklist:**

- [ ] Create new journal entry (DRAFT status)
- [ ] Add lines to journal entry
- [ ] Attempt to post unbalanced entry (should fail)
- [ ] Balance entry and post successfully
- [ ] Attempt to edit posted entry (should fail)
- [ ] Attempt to delete posted entry (should fail)
- [ ] Void posted entry (should succeed)
- [ ] Create new company account
- [ ] Attempt to change account type after posting transaction (should fail)
- [ ] Create new fiscal period
- [ ] Attempt to create overlapping fiscal period (should fail)

---

## Rollback Procedure

**If migration causes critical issues, rollback to migration 002:**

### Step 1: Downgrade Database

```bash
cd backend
alembic downgrade 002
```

**This will:**
- Drop all triggers created in Phase 1
- Drop all constraints added in Phase 1
- Remove new columns (is_locked, account_type, normal_balance, version)
- Drop ENUM types
- **Preserve all data** (columns are dropped but data is backed up via pg_dump)

---

### Step 2: Restore from Backup (If Needed)

If downgrade fails or data corruption occurs:

```bash
pg_restore -U user -d aequitas_dev -c aequitas_backup_YYYYMMDD.dump
```

---

### Step 3: Document Rollback Reason

Create incident report documenting:
- Which migration failed
- Error message
- Data state at time of failure
- Reason for rollback
- Remediation plan before retry

---

## Common Issues and Solutions

### Issue 1: Migration 003 fails with negative amounts

**Symptom:**
```
ERROR:  new row violates check constraint "jel_positive_amounts"
```

**Solution:**
```sql
UPDATE journal_entry_lines
SET debit_amount = ABS(debit_amount),
    credit_amount = ABS(credit_amount)
WHERE debit_amount < 0 OR credit_amount < 0;
```

Re-run migration.

---

### Issue 2: Migration 004 fails with unbalanced entries

**Symptom:**
```
ERROR:  Journal entry X does not balance: debits = Y, credits = Z
```

**Solution:**
Option 1 - Change to DRAFT:
```sql
UPDATE journal_entries SET status = 'DRAFT' WHERE entry_number = 'X';
```

Option 2 - Add balancing line (requires knowing correct account):
```sql
INSERT INTO journal_entry_lines (journal_entry_id, company_account_id, credit_amount, ...)
VALUES (...);
```

Re-run migration.

---

### Issue 3: Migration 005 produces unmapped accounts warning

**Symptom:**
```
WARNING:  Found X company accounts without account_type classification
```

**Solution:**
This is informational. Migration will use code prefix heuristics. Review accounts after migration:

```sql
SELECT * FROM company_accounts WHERE master_account_code IS NULL;
```

Manually classify if heuristics are incorrect.

---

### Issue 4: Migration 012 fails with overlapping periods

**Symptom:**
```
ERROR:  Cannot add overlap prevention constraint: X overlapping periods exist
```

**Solution:**
Identify and resolve overlaps:

```sql
SELECT * FROM fiscal_periods WHERE company_id IN (
  SELECT DISTINCT fp1.company_id
  FROM fiscal_periods fp1
  JOIN fiscal_periods fp2
    ON fp1.company_id = fp2.company_id
    AND fp1.id < fp2.id
    AND daterange(fp1.start_date, fp1.end_date, '[]')
        && daterange(fp2.start_date, fp2.end_date, '[]')
);
```

Adjust dates, delete duplicates, or archive as needed. Re-run migration.

---

### Issue 5: Trigger prevents legitimate operation

**Symptom:**
```
ERROR:  Cannot modify locked account ... Account is locked since ...
```

**Solution:**
This is expected behavior. To unlock account (requires superuser):

```sql
UPDATE company_accounts
SET is_locked = false,
    locked_at = NULL,
    locked_by = NULL,
    locked_reason = NULL
WHERE id = '...';
```

**WARNING:** Unlocking should be rare and requires audit justification.

---

## Application Code Changes Required

**After Phase 1 migrations complete, update application code:**

### 1. Update SQLAlchemy Models

Models to update:
- `backend/app/db/models/company_account.py`
- `backend/app/db/models/master_account.py`
- `backend/app/db/models/fiscal_period.py`

**Add new fields:**
```python
# company_account.py
account_type = Column(Enum(AccountType), nullable=False)
normal_balance = Column(Enum(NormalBalance), nullable=False)
is_locked = Column(Boolean, nullable=False, default=False)
locked_at = Column(DateTime, nullable=True)
locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
locked_reason = Column(Enum(LockedReason), nullable=True)

# master_account.py
version = Column(String(10), nullable=False, default='2024.1')
```

---

### 2. Update Pydantic Schemas

Schemas to update:
- `backend/app/schemas/company_account.py`
- `backend/app/schemas/master_account.py`

**Add new fields to response models.**

---

### 3. Update Services

Services to update:
- `backend/app/services/chart_service.py` (account type derivation)
- `backend/app/services/journal_entry_service.py` (remove application-level balance validation, rely on DB)
- `backend/app/services/fiscal_period_service.py` (remove overlap checks, rely on DB)

**Remove redundant validation** now enforced at database level.

---

### 4. Update Frontend

Frontend updates:
- Display `is_locked` status on account detail pages
- Show lock reason and timestamp
- Disable edit controls for locked accounts
- Display account_type and normal_balance in account lists
- Show master chart version in admin panel

---

## Performance Considerations

### Index Usage

Phase 1 migrations create the following indexes:

```sql
-- Migration 011
CREATE INDEX ix_master_accounts_version ON master_accounts (version);

-- Migration 012
CREATE INDEX ix_fiscal_periods_company_date_range
ON fiscal_periods (company_id, start_date, end_date);
```

**Query optimization:**
- Period lookups by company and date are now indexed
- Master chart queries by version are indexed
- Existing indexes on company_id, master_account_code preserved

---

### Trigger Performance

**Triggers added:** 11 total
- 3 on `journal_entry_lines` (balance validation)
- 1 on `journal_entries` (balance on post)
- 1 on `journal_entry_lines` (auto-lock)
- 1 on `company_accounts` (immutability)
- 4 on `journal_entries` and `journal_entry_lines` (posted immutability)

**Performance impact:**
- Balance validation triggers: O(N) where N = lines in entry (typically 2-10)
- Auto-lock trigger: O(1) single UPDATE
- Immutability triggers: O(1) comparison operations
- **Total overhead:** < 10ms per journal entry operation

**Mitigation:**
- Triggers only fire on INSERT/UPDATE/DELETE, not SELECT
- No nested trigger calls (no cascading)
- All triggers use efficient single-row operations

---

## Next Steps After Phase 1

**Phase 1 Complete → Proceed to Phase 2**

Phase 2 migrations (not included here) will add:
- ChartTemplate structure (industry, size_category, included_accounts)
- CompanyAccount parent_id FK (hierarchy)
- CompanyAccount mapped_master_account_id FK (proper UUID FK)
- AccountMapping master_account_id FK (replace master_code String)
- Unique constraints (company_id + code, company_id + entry_number)

**Estimated timeline:**
- Phase 1: 2-3 weeks (including testing)
- Phase 2: 2-3 weeks
- Phase 3: 1-2 weeks
- Total: 6-8 weeks to full canonical compliance

---

## Support and Escalation

**For migration issues:**
1. Review "Common Issues and Solutions" section above
2. Check Alembic migration logs: `backend/alembic/versions/*.py`
3. Consult canonical model: `CHART_OF_ACCOUNTS_MODEL.md`
4. Escalate to database-guardian agent or Lead Architect (Thome)

**For rollback decisions:**
- Rollback authority: Lead Architect
- Document all rollbacks in `backend/alembic/MIGRATION_LOG.md`

---

## Appendix: Migration Dependency Graph

```
002 (existing)
 │
 ├─> 003 (journal_entry_line constraints)
 │    └─> 004 (double-entry balance trigger)
 │         └─> 005 (account_type enum)
 │              └─> 006 (normal_balance enum)
 │                   └─> 007 (locking fields)
 │                        ├─> 008 (auto-lock trigger)
 │                        │    └─> 009 (immutability trigger)
 │                        │         └─> 010 (posted immutability)
 │                        │              ├─> 011 (master version)
 │                        │              │    └─> 012 (overlap prevention)
 │                        │              │
 │                        │              └─> (Phase 2 migrations...)
 │                        │
 │                        └─> (Parallel track for other Phase 1 work)
```

**Critical path:** 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 012
**Parallel path:** 011 (master version) can be applied independently

---

**END OF MIGRATION GUIDE**

This guide covers all Phase 1 migrations (003-012) for Chart of Accounts canonical compliance. Follow the steps in order and validate at each stage to ensure a successful migration.
