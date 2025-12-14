# Phase 2A Migration Guide: Schema Normalization (Structured Template Tables)

**Version:** 1.0
**Date:** 2025-12-13
**Migrations:** 013 through 018
**Target:** Chart of Accounts Schema Normalization
**Prerequisite:** Phase 1 Complete (migrations 003-012)

---

## Overview

Phase 2A implements schema normalization to replace JSON blob templates with structured, relational template architecture. This phase establishes proper account hierarchy, master chart mapping, and template compliance enforcement.

**Total Migrations:** 6
**Estimated Duration:** 1-2 weeks
**Complexity:** Medium (requires data validation, no breaking schema changes)
**Rollback:** Supported via Alembic downgrade

---

## What Phase 2A Accomplishes

### Before Phase 2A:
- Account hierarchy via `parent_code` (String, no FK enforcement)
- Master mapping via `master_account_code` (String, no FK enforcement)
- Templates as JSON blobs in `coa_templates.data`
- No hierarchy cycle prevention
- No cross-company parent protection
- No mandatory account enforcement

### After Phase 2A:
- Account hierarchy via `parent_id` (UUID FK, cascade-protected)
- Master mapping via `mapped_master_account_id` (UUID FK, type-validated)
- Templates as structured relational data (`chart_templates`, `chart_template_accounts`)
- Hierarchy cycles prevented via database triggers
- Cross-company parents prevented via database triggers
- Master mapping consistency enforced (account_type must match master category)
- Locked accounts cannot change hierarchy or mapping
- Mandatory accounts cannot be deleted or deactivated
- Company charts linked to templates via `company_template_usage`

---

## Migration Sequence

### Summary Table

| Migration | File | Description | Breaking | Data Migration | Estimated Time |
|-----------|------|-------------|----------|----------------|----------------|
| 013 | `add_hierarchy_and_mapping_columns.py` | Add parent_id and mapped_master_account_id | ❌ No | Backfill from strings | 10 min |
| 014 | `create_chart_templates.py` | Create chart_templates table | ❌ No | Seed initial templates | 5 min |
| 015 | `create_chart_template_accounts.py` | Create chart_template_accounts table | ❌ No | Schema only | 5 min |
| 016 | `add_uniqueness_constraints.py` | Add UNIQUE(company_id, code/name) | ✅ Yes | Validation only | 5 min |
| 017 | `add_hierarchy_and_mapping_triggers.py` | Hierarchy and mapping enforcement | ❌ No | Trigger only | 5 min |
| 018 | `add_mandatory_account_enforcement.py` | Mandatory account protection | ❌ No | Schema + triggers | 10 min |

**Total estimated time:** ~40 minutes (excluding data cleanup)

---

## Breaking Changes

### Migration 016: Uniqueness Constraints

**What breaks:**
- Multiple company accounts with same code in same company
- Multiple company accounts with same name in same company

**Error message:**
```
ERROR:  Cannot add UNIQUE(company_id, code) constraint: X duplicate code groups exist
ERROR:  duplicate key value violates unique constraint "uq_company_accounts_company_code"
```

**Remediation:**

```sql
-- Identify duplicate codes
SELECT company_id, code, COUNT(*)
FROM company_accounts
GROUP BY company_id, code
HAVING COUNT(*) > 1;

-- Option 1: Append suffix to duplicates
UPDATE company_accounts
SET code = code || '-2'
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id, code ORDER BY created_at) as rn
        FROM company_accounts
    ) ranked
    WHERE rn > 1
);

-- Option 2: Delete duplicate accounts (if truly duplicates)
DELETE FROM company_accounts
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id, code ORDER BY created_at DESC) as rn
        FROM company_accounts
    ) ranked
    WHERE rn > 1
);

-- Identify duplicate names
SELECT company_id, name, COUNT(*)
FROM company_accounts
WHERE name IS NOT NULL
GROUP BY company_id, name
HAVING COUNT(*) > 1;

-- Remediation similar to codes above
```

---

## Non-Breaking Changes

### Migration 013: Hierarchy and Mapping Columns

**Changes:** Adds `parent_id` and `mapped_master_account_id` columns

**Data migration:**
- Automatically backfills `parent_id` from `parent_code` via same-company lookup
- Automatically backfills `mapped_master_account_id` from `master_account_code` via code lookup

**Warnings:**
- Accounts with `parent_code` that don't match any existing account will have `parent_id = NULL`
- Accounts with `master_account_code` that don't exist in `master_accounts` will have `mapped_master_account_id = NULL`

**Action:** Migration logs warnings for unresolved references. Review and correct if needed.

---

### Migration 014: Chart Templates Table

**Changes:** Creates `chart_templates` table

**Data migration:** Seeds 4 initial templates:
1. US GAAP - Standard Business (2024.1) [ACTIVE]
2. IFRS - International Standard (2024.1) [ACTIVE]
3. US GAAP - Small Business (2024.1-SMB) [ACTIVE]
4. US GAAP - Non-Profit (2024.1-NPO) [INACTIVE]

**No action required** - automatic seeding.

---

### Migration 015: Chart Template Accounts Table

**Changes:** Creates `chart_template_accounts` table

**Data migration:** None (schema only)

**Next Step:** Application layer must populate template accounts from master chart data.

---

### Migration 017: Hierarchy and Mapping Triggers

**Changes:** Adds database triggers for enforcement

**Impact:** Future operations will be blocked if they violate rules. No existing data is modified.

**Triggers:**
- `prevent_company_account_hierarchy_cycle`: Blocks circular hierarchies
- `enforce_same_company_parent`: Blocks cross-company parents
- `enforce_master_mapping_consistency`: Validates account_type matches master category
- `prevent_locked_account_hierarchy_mutation`: Prevents changing hierarchy/mapping on locked accounts

**No action required** - enforcement only.

---

### Migration 018: Mandatory Account Enforcement

**Changes:** Creates `company_template_usage` table, adds `template_account_id` column, adds triggers

**Impact:**
- Companies can be linked to templates via `company_template_usage`
- Company accounts can be linked to template accounts via `template_account_id`
- Accounts linked to mandatory template accounts cannot be deleted or deactivated

**No action required** - schema and enforcement only.

---

## Pre-Migration Checklist

**Before applying Phase 2A migrations, complete the following:**

### 1. Verify Phase 1 Complete

```bash
cd backend
alembic current
```

**Expected output:**
```
012 (head)
```

**If different:** Apply Phase 1 migrations first.

---

### 2. Backup Database

```bash
pg_dump -U user -d aequitas_dev -F c -f aequitas_phase2a_backup_$(date +%Y%m%d).dump
```

**Restore command** (if rollback needed):
```bash
pg_restore -U user -d aequitas_dev -c aequitas_phase2a_backup_YYYYMMDD.dump
```

---

### 3. Run Pre-Migration Validation Script

```bash
cd backend/alembic/versions
psql -U user -d aequitas_dev -f phase2a_pre_migration_validation.sql
```

**Expected output:**
```
VALIDATION SUMMARY
Status: PASSED
All validations passed successfully.
```

**If FAILED:**
- Review violation details in script output
- Apply remediations listed
- Re-run validation until PASSED

**Validations performed:**
1. Phase 1 prerequisite check
2. Duplicate account codes
3. Duplicate account names
4. Orphaned parent references
5. Invalid master account references
6. Hierarchy cycles
7. Cross-company parent references
8. Account type / master category mismatches
9. Phase 1 invariants still hold

---

### 4. Application Downtime Planning

**Required downtime:** Not strictly required (read-only mode recommended)

**Rationale:**
- Migration 016 may fail if concurrent writes create duplicate codes/names
- Total migration time: ~40 minutes
- Conservative approach: Schedule maintenance window

**Alternative:** Read-only mode
```sql
-- Set database to read-only during migration
ALTER DATABASE aequitas_dev SET default_transaction_read_only = on;

-- After migration complete
ALTER DATABASE aequitas_dev SET default_transaction_read_only = off;
```

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
018 (head)
```

**Verify table structure:**
```sql
-- Check new columns added to company_accounts
\d company_accounts

-- Expected new columns:
-- - parent_id (uuid)
-- - mapped_master_account_id (uuid)
-- - template_account_id (uuid)

-- Check new tables
\dt chart_templates
\dt chart_template_accounts
\dt company_template_usage

-- Check new constraints
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'company_accounts'::regclass
  AND conname LIKE '%company_%';

-- Expected constraints:
-- - uq_company_accounts_company_code (UNIQUE)
-- - uq_company_accounts_company_name (UNIQUE)

-- Check new triggers
SELECT tgname, tgrelid::regclass
FROM pg_trigger
WHERE tgname LIKE 'trg_%hierarchy%'
   OR tgname LIKE 'trg_%mapping%'
   OR tgname LIKE 'trg_%mandatory%'
ORDER BY tgrelid::regclass::text;

-- Expected triggers:
-- - trg_prevent_company_account_hierarchy_cycle
-- - trg_enforce_same_company_parent
-- - trg_enforce_master_mapping_consistency
-- - trg_prevent_locked_account_hierarchy_mutation
-- - trg_prevent_mandatory_account_deletion
-- - trg_prevent_mandatory_account_deactivation
```

---

### Step 3: Post-Migration Validation

Run comprehensive validation tests:

```sql
-- 1. Verify parent_id backfill
SELECT COUNT(*) FROM company_accounts WHERE parent_code IS NOT NULL;
-- vs
SELECT COUNT(*) FROM company_accounts WHERE parent_id IS NOT NULL;
-- Should be equal or close (orphaned parent_codes will have NULL parent_id)

-- 2. Verify mapped_master_account_id backfill
SELECT COUNT(*) FROM company_accounts WHERE master_account_code IS NOT NULL;
-- vs
SELECT COUNT(*) FROM company_accounts WHERE mapped_master_account_id IS NOT NULL;
-- Should be equal or close (invalid master_account_codes will have NULL mapped_master_account_id)

-- 3. Verify uniqueness constraints
SELECT COUNT(*) FROM (
    SELECT company_id, code, COUNT(*)
    FROM company_accounts
    GROUP BY company_id, code
    HAVING COUNT(*) > 1
) dupes;
-- Expected: 0

SELECT COUNT(*) FROM (
    SELECT company_id, name, COUNT(*)
    FROM company_accounts
    WHERE name IS NOT NULL
    GROUP BY company_id, name
    HAVING COUNT(*) > 1
) dupes;
-- Expected: 0

-- 4. Verify templates seeded
SELECT COUNT(*) FROM chart_templates;
-- Expected: 4

SELECT name, jurisdiction, version, is_active
FROM chart_templates
ORDER BY jurisdiction, version;
-- Expected:
-- - IFRS - International Standard | IFRS | 2024.1 | true
-- - US GAAP - Non-Profit | US-GAAP | 2024.1-NPO | false
-- - US GAAP - Small Business | US-GAAP | 2024.1-SMB | true
-- - US GAAP - Standard Business | US-GAAP | 2024.1 | true

-- 5. Verify hierarchy triggers work
-- Try to create a cycle (should fail)
DO $$
DECLARE
    v_company_id UUID;
    v_account1_id UUID;
    v_account2_id UUID;
BEGIN
    -- Get a test company
    SELECT id INTO v_company_id FROM companies LIMIT 1;

    -- Create account 1
    INSERT INTO company_accounts (company_id, code, description, type, account_type, normal_balance)
    VALUES (v_company_id, 'TEST.1', 'Test Account 1', 'D', 'Asset', 'Debit')
    RETURNING id INTO v_account1_id;

    -- Create account 2 with parent = account 1
    INSERT INTO company_accounts (company_id, code, description, type, account_type, normal_balance, parent_id)
    VALUES (v_company_id, 'TEST.2', 'Test Account 2', 'D', 'Asset', 'Debit', v_account1_id)
    RETURNING id INTO v_account2_id;

    -- Try to make account 1's parent = account 2 (creates cycle, should fail)
    UPDATE company_accounts
    SET parent_id = v_account2_id
    WHERE id = v_account1_id;

    RAISE EXCEPTION 'ERROR: Cycle prevention trigger did not fire!';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLERRM LIKE '%hierarchy cycle%' THEN
            RAISE NOTICE 'SUCCESS: Hierarchy cycle prevented correctly';
            -- Cleanup
            DELETE FROM company_accounts WHERE id IN (v_account1_id, v_account2_id);
        ELSE
            RAISE;
        END IF;
END $$;
```

---

### Step 4: Test Critical User Flows

**Manual testing checklist:**

- [ ] Create new company account
- [ ] Set parent_id to existing account (should succeed)
- [ ] Try to set parent_id to account in different company (should fail)
- [ ] Try to create hierarchy cycle (should fail)
- [ ] Map account to master account
- [ ] Try to set account_type that doesn't match master (should fail)
- [ ] Lock account (via posting transaction)
- [ ] Try to change parent_id on locked account (should fail)
- [ ] Try to change mapped_master_account_id on locked account (should fail)
- [ ] Create template account marked as mandatory
- [ ] Link company account to mandatory template account
- [ ] Try to delete mandatory account (should fail)
- [ ] Try to deactivate mandatory account (should fail)

---

## Rollback Procedure

**If migration causes critical issues, rollback to migration 012:**

### Step 1: Downgrade Database

```bash
cd backend
alembic downgrade 012
```

**This will:**
- Drop `company_template_usage` table
- Drop `chart_template_accounts` table
- Drop `chart_templates` table
- Remove `template_account_id` column from `company_accounts`
- Remove `mapped_master_account_id` column from `company_accounts`
- Remove `parent_id` column from `company_accounts`
- Drop all uniqueness constraints added in Phase 2A
- Drop all triggers created in Phase 2A
- **Preserve all original data** (parent_code, master_account_code still exist)

---

### Step 2: Restore from Backup (If Needed)

If downgrade fails or data corruption occurs:

```bash
pg_restore -U user -d aequitas_dev -c aequitas_phase2a_backup_YYYYMMDD.dump
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

### Issue 1: Migration 013 warns about unresolved parent_code

**Symptom:**
```
WARNING:  X company accounts have parent_code but no matching parent in same company
```

**Solution:**
This is informational. Accounts with unresolved `parent_code` will have `parent_id = NULL` but retain `parent_code` for reference.

**Action:**
```sql
-- Identify accounts
SELECT id, company_id, code, parent_code
FROM company_accounts
WHERE parent_code IS NOT NULL AND parent_id IS NULL;

-- Option 1: Create missing parent account
INSERT INTO company_accounts (company_id, code, description, type, account_type, normal_balance)
VALUES (...);

-- Then update child:
UPDATE company_accounts child
SET parent_id = (SELECT id FROM company_accounts WHERE code = child.parent_code AND company_id = child.company_id)
WHERE child.parent_code IS NOT NULL AND child.parent_id IS NULL;

-- Option 2: Clear invalid parent_code
UPDATE company_accounts
SET parent_code = NULL
WHERE parent_code IS NOT NULL AND parent_id IS NULL;
```

---

### Issue 2: Migration 016 fails with duplicate codes

**Symptom:**
```
ERROR:  Cannot add UNIQUE(company_id, code) constraint: X duplicate code groups exist
```

**Solution:**
```sql
-- Identify duplicates
SELECT company_id, code, COUNT(*), ARRAY_AGG(id ORDER BY created_at) as account_ids
FROM company_accounts
GROUP BY company_id, code
HAVING COUNT(*) > 1;

-- Option 1: Append suffix to make unique
UPDATE company_accounts
SET code = code || '-' || ROW_NUMBER() OVER (PARTITION BY company_id, code ORDER BY created_at)
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id, code ORDER BY created_at) as rn
        FROM company_accounts
    ) ranked
    WHERE rn > 1
);

-- Option 2: Delete true duplicates (if accounts are identical)
DELETE FROM company_accounts
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id, code ORDER BY created_at DESC) as rn
        FROM company_accounts
    ) ranked
    WHERE rn > 1
);
```

Re-run migration.

---

### Issue 3: Migration 017 trigger blocks legitimate operation

**Symptom:**
```
ERROR:  Cannot create hierarchy cycle: account "..." would become its own ancestor
```

**Solution:**
This is expected behavior. Review the parent_id assignment to ensure it doesn't create a cycle.

**Action:**
```sql
-- Verify hierarchy path
WITH RECURSIVE hierarchy AS (
    SELECT id, parent_id, code, 1 as depth, ARRAY[code] as path
    FROM company_accounts
    WHERE id = '...'  -- problematic account

    UNION ALL

    SELECT ca.id, ca.parent_id, ca.code, h.depth + 1, h.path || ca.code
    FROM company_accounts ca
    JOIN hierarchy h ON ca.id = h.parent_id
    WHERE h.depth < 50
)
SELECT * FROM hierarchy;
```

If cycle is legitimate business logic error, fix the parent assignment. If trigger is incorrectly blocking valid hierarchy, report as bug.

---

### Issue 4: Trigger prevents changing locked account hierarchy

**Symptom:**
```
ERROR:  Cannot change parent_id of locked account "...". Account locked since ...
```

**Solution:**
This is expected behavior. Locked accounts cannot change hierarchy to preserve financial statement integrity.

**If change is absolutely necessary** (requires superuser justification):
```sql
-- Temporarily unlock account
UPDATE company_accounts
SET is_locked = false,
    locked_at = NULL,
    locked_by = NULL,
    locked_reason = NULL
WHERE id = '...';

-- Make hierarchy change
UPDATE company_accounts
SET parent_id = '...'
WHERE id = '...';

-- Re-lock account
UPDATE company_accounts
SET is_locked = true,
    locked_at = now(),
    locked_by = '...',  -- current user ID
    locked_reason = 'Manual'
WHERE id = '...';
```

**WARNING:** Unlocking should be rare and requires audit justification.

---

## Application Code Changes Required

**After Phase 2A migrations complete, update application code:**

### 1. Update SQLAlchemy Models

Models to update:
- `backend/app/db/models/company_account.py`
- `backend/app/db/models/chart_template.py` (NEW)
- `backend/app/db/models/chart_template_account.py` (NEW)
- `backend/app/db/models/company_template_usage.py` (NEW)

**Add new fields to company_account.py:**
```python
parent_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete='CASCADE'), nullable=True)
mapped_master_account_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id", ondelete='SET NULL'), nullable=True)
template_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_template_accounts.id", ondelete='SET NULL'), nullable=True)

# Add relationships
parent = relationship("CompanyAccount", remote_side=[id], back_populates="children")
children = relationship("CompanyAccount", back_populates="parent", cascade="all, delete-orphan")
mapped_master = relationship("MasterAccount", foreign_keys=[mapped_master_account_id])
template_account = relationship("ChartTemplateAccount")
```

**Create new models:**
- `backend/app/db/models/chart_template.py` (based on migration 014 schema)
- `backend/app/db/models/chart_template_account.py` (based on migration 015 schema)
- `backend/app/db/models/company_template_usage.py` (based on migration 018 schema)

---

### 2. Update Pydantic Schemas

Schemas to update:
- `backend/app/schemas/company_account.py`
- Create: `backend/app/schemas/chart_template.py`
- Create: `backend/app/schemas/chart_template_account.py`

**Add new fields to response models:**
```python
class CompanyAccountResponse(BaseModel):
    id: UUID
    # ... existing fields ...
    parent_id: Optional[UUID]
    mapped_master_account_id: Optional[UUID]
    template_account_id: Optional[UUID]

    class Config:
        orm_mode = True
```

---

### 3. Update Services

Services to update:
- `backend/app/services/chart_service.py` (use parent_id instead of parent_code)
- `backend/app/services/template_service.py` (NEW - manage templates)
- `backend/app/services/mapping_service.py` (use mapped_master_account_id instead of master_account_code)

**Key changes:**
- Replace `parent_code` string lookups with `parent_id` FK navigation
- Replace `master_account_code` string lookups with `mapped_master_account_id` FK navigation
- Add template management service for CRUD operations on templates
- Add mandatory account validation when assigning templates

---

### 4. Update Frontend

Frontend updates:
- Display `parent_id` hierarchy in account tree views
- Show master account mapping status
- Display template information in company setup
- Show mandatory account indicators
- Disable delete/deactivate buttons for mandatory accounts

---

## Performance Considerations

### Index Usage

Phase 2A migrations create the following indexes:

```sql
-- Migration 013
CREATE INDEX ix_company_accounts_parent_id ON company_accounts (parent_id);
CREATE INDEX ix_company_accounts_mapped_master_account_id ON company_accounts (mapped_master_account_id);

-- Migration 014
CREATE INDEX ix_chart_templates_jurisdiction ON chart_templates (jurisdiction);
CREATE INDEX ix_chart_templates_is_active ON chart_templates (is_active);
CREATE INDEX ix_chart_templates_jurisdiction_active ON chart_templates (jurisdiction, is_active);

-- Migration 015
CREATE INDEX ix_chart_template_accounts_template_id ON chart_template_accounts (template_id);
CREATE INDEX ix_chart_template_accounts_parent_id ON chart_template_accounts (parent_id);
CREATE INDEX ix_chart_template_accounts_master_account_id ON chart_template_accounts (master_account_id);
CREATE INDEX ix_chart_template_accounts_is_mandatory ON chart_template_accounts (template_id, is_mandatory);
CREATE INDEX ix_chart_template_accounts_sort_order ON chart_template_accounts (template_id, parent_id, sort_order);

-- Migration 016
CREATE UNIQUE INDEX ix_company_accounts_company_code ON company_accounts (company_id, code);
CREATE UNIQUE INDEX ix_company_accounts_company_name ON company_accounts (company_id, name);

-- Migration 018
CREATE INDEX ix_company_template_usage_company_id ON company_template_usage (company_id);
CREATE INDEX ix_company_template_usage_template_id ON company_template_usage (template_id);
CREATE INDEX ix_company_accounts_template_account_id ON company_accounts (template_account_id);
```

**Query optimization:**
- Hierarchy traversal queries benefit from `parent_id` index
- Master mapping lookups benefit from `mapped_master_account_id` index
- Template queries by jurisdiction are indexed
- Account code/name lookups are now uniquely indexed

---

### Trigger Performance

**Triggers added:** 6 total
- 1 hierarchy cycle prevention (recursive CTE, O(depth))
- 1 same-company parent enforcement (O(1) lookup)
- 1 master mapping consistency (O(1) lookup)
- 1 locked account hierarchy mutation prevention (O(1) comparison)
- 2 mandatory account enforcement (O(1) lookup)

**Performance impact:**
- Cycle prevention: O(hierarchy depth), typically < 10 levels, < 5ms
- All other triggers: O(1) single-row lookups, < 1ms
- **Total overhead:** < 10ms per account mutation

**Mitigation:**
- Triggers only fire on INSERT/UPDATE/DELETE, not SELECT
- No nested trigger calls (no cascading)
- All triggers use efficient single-row or indexed operations
- Cycle prevention only traverses upward (limited by hierarchy depth)

---

## Next Steps After Phase 2A

**Phase 2A Complete → Proceed to Phase 2B**

Phase 2B migrations (not included here) may add:
- Seed `chart_template_accounts` from master chart data
- Deprecate `parent_code` and `master_account_code` columns (after validation)
- Add NOT NULL constraints to `parent_id` where appropriate
- Additional template features (industry-specific, size-based)

**Estimated timeline:**
- Phase 2A: 1-2 weeks (including testing)
- Phase 2B: 1-2 weeks
- Total: 2-4 weeks to full schema normalization

---

## Support and Escalation

**For migration issues:**
1. Review "Common Issues and Solutions" section above
2. Check Alembic migration logs: `backend/alembic/versions/*.py`
3. Consult validation script: `phase2a_pre_migration_validation.sql`
4. Escalate to database-guardian agent or Lead Architect (Thome)

**For rollback decisions:**
- Rollback authority: Lead Architect
- Document all rollbacks in `backend/alembic/MIGRATION_LOG.md`

---

## Appendix: Migration Dependency Graph

```
012 (Phase 1 complete)
 │
 ├─> 013 (hierarchy + mapping columns)
 │    └─> 014 (chart_templates table)
 │         └─> 015 (chart_template_accounts table)
 │              └─> 016 (uniqueness constraints)
 │                   └─> 017 (hierarchy + mapping triggers)
 │                        └─> 018 (mandatory account enforcement)
 │
 └─> (Phase 2B migrations...)
```

**Critical path:** 013 → 014 → 015 → 016 → 017 → 018
**All migrations are sequential** (no parallel tracks in Phase 2A)

---

## Appendix: Database Schema Diagram (After Phase 2A)

```
master_accounts
├── id (PK)
├── code (UNIQUE)
├── category
├── normal_balance
└── ...

chart_templates
├── id (PK)
├── jurisdiction
├── version
├── UNIQUE(jurisdiction, version)
└── ...

chart_template_accounts
├── id (PK)
├── template_id (FK → chart_templates)
├── master_account_id (FK → master_accounts)
├── parent_id (FK → chart_template_accounts, self-ref)
├── code
├── is_mandatory
├── UNIQUE(template_id, code)
└── ...

companies
├── id (PK)
└── ...

company_template_usage
├── id (PK)
├── company_id (FK → companies, UNIQUE)
├── template_id (FK → chart_templates)
└── ...

company_accounts
├── id (PK)
├── company_id (FK → companies)
├── code
├── name
├── parent_id (FK → company_accounts, self-ref)
├── mapped_master_account_id (FK → master_accounts)
├── template_account_id (FK → chart_template_accounts)
├── account_type
├── normal_balance
├── is_locked
├── UNIQUE(company_id, code)
├── UNIQUE(company_id, name)
└── ...
```

---

**END OF MIGRATION GUIDE**

This guide covers all Phase 2A migrations (013-018) for schema normalization. Follow the steps in order and validate at each stage to ensure a successful migration.
