# Master Chart Reseed Plan

**Purpose:** Define a safe, auditable plan to bring the database Master Chart into full conformity with Kernel 2025.2.

**Status:** Design-Only (No Execution)
**Authority:** Kernel 2025.2 is canonical. Database must conform.
**Date:** 2025-12-24

---

## Current State Assessment

### Database Master Chart Analysis

**Current Structure:**
- **Total Accounts:** 345
- **Code Scheme:** Sequential numeric (10000, 10001, 10069, 10138, ...)
- **Header Accounts:** 10000, 20000, 30000, 40000, 50000, 60000, 80000
- **Detail Accounts:** Sequential numeric codes between headers

**Kernel 2025.2 Requirements:**
- **Code Scheme:** Hierarchical 5-digit (10000, 10100, 12000, 14000, ...)
- **L0 Universal Kernel:** 20 specific accounts
- **L1 Standard Kernel:** 35 accounts (includes L0)
- **L2 Simplified Kernel:** 20 accounts (same as L0)

### Mismatch Analysis

| Category | Current State | Kernel Requirement | Risk Level |
|----------|---------------|-------------------|------------|
| **L0 Codes** | Only 6 match (10000, 20000, 30000, 40000, 50000, 60000) | 20 required (including 10100, 12000, 14000, etc.) | 🛑 **CRITICAL** |
| **System Accounts** | Missing `32000`, `39999` | Required for fiscal closing | 🛑 **CRITICAL** |
| **Code Scheme** | Sequential (10001, 10069, 10138) | Hierarchical (10100, 12000, 14000) | 🔴 **HIGH** |
| **Hierarchy** | Flat with `parent_code` strings | UUID-based with strict hierarchy | 🟠 **MEDIUM** |

**Verdict:** The current master chart CANNOT instantiate Kernel 2025.2 without structural changes.

---

## Target State

### Kernel-Aligned Master Chart

The target master chart must contain AT MINIMUM:

#### L0 Universal Kernel (20 Accounts — MANDATORY)

| Code | Name | Category | Required |
|------|------|----------|----------|
| 10000 | Operating Cash | ASSET | ✅ |
| 10100 | Undeposited Funds | ASSET | ✅ |
| 12000 | Accounts Receivable | ASSET | ✅ |
| 14000 | Prepaid Expenses | ASSET | ✅ |
| 15000 | Fixed Assets | ASSET | ✅ |
| 15900 | Accumulated Depreciation | ASSET | ✅ |
| 20000 | Accounts Payable | LIABILITY | ✅ |
| 21000 | Accrued Liabilities | LIABILITY | ✅ |
| 22000 | Taxes Payable | LIABILITY | ✅ |
| 23000 | Deferred Revenue | LIABILITY | ✅ |
| 30000 | Owners Equity / Capital | EQUITY | ✅ |
| 32000 | **Retained Earnings** | EQUITY | ✅ **SYSTEM** |
| 39999 | **Current Period Earnings** | EQUITY | ✅ **SYSTEM** |
| 40000 | General Operating Revenue | REVENUE | ✅ |
| 49000 | Refunds / Allowances | REVENUE | ✅ |
| 50000 | Cost of Goods Sold | COGS | ✅ |
| 60000 | General Operating Expenses | EXPENSE | ✅ |
| 61000 | Payroll Expense | EXPENSE | ✅ |
| 62000 | Depreciation Expense | EXPENSE | ✅ |
| 69000 | Tax Expense | EXPENSE | ✅ |

#### L1 Standard Kernel (35 Accounts — OPTIONAL)

L1 includes all L0 accounts plus 15 additional accounts:

| Code | Name | Category | Parent |
|------|------|----------|--------|
| 11000 | Savings Account | ASSET | 10000 |
| 13000 | Inventory | ASSET | — |
| 16000 | Intangible Assets | ASSET | — |
| 24000 | Short-term Debt | LIABILITY | — |
| 25000 | Long-term Debt | LIABILITY | — |
| 31000 | Partner Distributions | EQUITY | — |
| 41000 | Service Revenue | REVENUE | 40000 |
| 42000 | Product Sales | REVENUE | 40000 |
| 51000 | Materials Cost | COGS | 50000 |
| 52000 | Labor Cost | COGS | 50000 |
| 63000 | Rent Expense | EXPENSE | 60000 |
| 64000 | Utilities Expense | EXPENSE | 60000 |
| 65000 | Insurance Expense | EXPENSE | 60000 |
| 66000 | Marketing Expense | EXPENSE | 60000 |
| 67000 | Professional Fees | EXPENSE | 60000 |

#### L2 Simplified Kernel (20 Accounts)

L2 = L0 (identical set)

### Extended Master Chart (Beyond Kernel)

The master chart MAY contain additional accounts beyond L1 (up to 345 total), but:
- These are **template-level extensions**, not kernel-governed
- They do NOT affect kernel compliance
- They are NOT frozen or version-controlled
- Companies MAY use them, but are not required to

---

## Reseed Strategy

### Strategy A: Fresh Install (Recommended for New Deployments)

**When to Use:**
- New Aequitas installations
- Development/staging environments
- Companies with no posted transactions

**Approach:**
1. **Drop existing master chart** (if no dependencies exist)
2. **Seed kernel-aligned accounts first** (L0 → L1 → Extended)
3. **Validate hierarchy and UUIDs**
4. **Seed chart templates** using `seed_chart_templates.py`

**Safety:**
- No data loss (no posted transactions)
- Clean hierarchy from start
- Full kernel compliance guaranteed

---

### Strategy B: Additive Migration (Required for Existing Deployments)

**When to Use:**
- Production environments
- Companies with posted transactions
- Existing master chart with dependencies

**Approach:**

#### Phase 1: Add Missing Kernel Accounts (Non-Destructive)
```sql
-- Example: Add missing L0 accounts
INSERT INTO master_accounts (id, code, description, category, type, ...)
VALUES
  (uuid_generate_v4(), '10100', 'Undeposited Funds', 'Asset', 'D', ...),
  (uuid_generate_v4(), '12000', 'Accounts Receivable', 'Asset', 'D', ...),
  (uuid_generate_v4(), '32000', 'Retained Earnings', 'Equity', 'D', ...),
  (uuid_generate_v4(), '39999', 'Current Period Earnings', 'Equity', 'D', ...)
  -- ... (all missing L0 accounts)
;
```

#### Phase 2: Mark Legacy Accounts as Deprecated (Non-Destructive)
- Do NOT delete accounts with `code IN (10001, 10069, 10138, ...)`
- Set `end_date = '2025-12-24'` to mark as deprecated
- Preserve for historical audit trail

#### Phase 3: Update Chart Templates
- Archive old templates (`is_active = false`)
- Seed new kernel-aligned templates
- New companies use kernel templates
- Existing companies keep their charts

**Safety Rules:**
- ✅ **ALLOWED:** Add new accounts
- ✅ **ALLOWED:** Mark accounts as deprecated (set `end_date`)
- ✅ **ALLOWED:** Update template references
- ❌ **FORBIDDEN:** Delete accounts with posted transactions
- ❌ **FORBIDDEN:** Change codes of existing accounts
- ❌ **FORBIDDEN:** Remap posted entries

---

### Strategy C: Dual-Track (Pragmatic Hybrid)

**Approach:**
- Maintain BOTH old sequential codes AND new kernel codes
- Use `regulatory_mapping` field to link equivalents
- Allow gradual migration over time

**Example:**
```json
{
  "code": "10001",
  "description": "Loans to Others (Legacy)",
  "end_date": "2025-12-24",
  "regulatory_mapping": {
    "kernel_2025_2_equivalent": "12000"
  }
}
```

**Benefit:**
- Zero disruption to existing companies
- New companies get clean kernel structure
- Historical data preserved

**Cost:**
- Dual maintenance burden
- Requires careful reporting logic

---

## Migration Safety Rules

### Absolute Prohibitions

1. **NEVER delete accounts with posted transactions**
   - Deleting breaks audit trail
   - Violates double-entry integrity

2. **NEVER change account codes on existing accounts**
   - Breaks historical references
   - Invalidates prior period reports

3. **NEVER remap posted journal entries**
   - History is immutable (Canon III)
   - Retroactive changes violate GAAP

### Permitted Operations

1. ✅ **Add new accounts** (forward-only)
2. ✅ **Deprecate old accounts** (set `end_date`, do not delete)
3. ✅ **Update templates** (new companies only)
4. ✅ **Add metadata** (`regulatory_mapping`, `notes`)

### Version Control

- Current master chart version: `2024.1`
- Post-reseed version: `2025.2` (kernel-aligned)
- Use `version` field to track evolution

---

## Verification Checklist

### Pre-Migration Verification

- [ ] **Backup database** (full snapshot)
- [ ] **Count existing accounts:** `SELECT COUNT(*) FROM master_accounts;`
- [ ] **Identify dependencies:** `SELECT COUNT(*) FROM company_accounts;`
- [ ] **Check posted transactions:** `SELECT COUNT(*) FROM journal_entries;`

### Post-Migration Verification

#### L0 Kernel Completeness
```sql
-- Verify all 20 L0 accounts exist
SELECT code, description FROM master_accounts
WHERE code IN (
  '10000', '10100', '12000', '14000', '15000', '15900',
  '20000', '21000', '22000', '23000',
  '30000', '32000', '39999',
  '40000', '49000', '50000',
  '60000', '61000', '62000', '69000'
)
ORDER BY code;

-- Expected: 20 rows
```

#### System Account Validation
```sql
-- Verify critical system accounts exist
SELECT code, description, category FROM master_accounts
WHERE code IN ('32000', '39999');

-- Expected: 2 rows (Retained Earnings, Current Period Earnings)
```

#### Hierarchy Integrity
```sql
-- Verify parent_id references are valid
SELECT ma.code, ma.description, p.code as parent_code
FROM master_accounts ma
LEFT JOIN master_accounts p ON ma.parent_id = p.id
WHERE ma.parent_id IS NOT NULL;

-- No NULL parent_code values should appear
```

#### Template Validation
```sql
-- Verify new templates reference kernel accounts only
SELECT t.name, COUNT(ta.id) as account_count
FROM chart_templates t
JOIN chart_template_accounts ta ON ta.template_id = t.id
WHERE t.version = '2025.2-kernel'
GROUP BY t.name;

-- Expected:
-- US GAAP Standard: 35 accounts
-- US GAAP Simplified: 20 accounts
```

### Kernel Compliance Audit

Run the verification script:
```bash
cd /docs/canonical/kernels
python3 verify_kernel_compliance.py --database=production
```

Expected output:
```
✅ L0 Kernel: 20/20 accounts present
✅ System Accounts: Retained Earnings, Current Period Earnings present
✅ Hierarchy: Valid UUID references
✅ Templates: Kernel-aligned
✅ COMPLIANCE: PASS
```

---

## Rollback Plan

If migration fails:

1. **Restore from backup** (pre-migration snapshot)
2. **Investigate failure cause**
3. **Do NOT attempt manual repair** (high risk of data corruption)
4. **Escalate to canonical authority**

**Never:**
- Manually delete accounts to "fix" duplicates
- Change codes to resolve conflicts
- Skip validation steps

---

## Implementation Sequence

### Phase 1: Preparation (No Database Changes)
- [ ] Review this plan
- [ ] Get approval from canonical authority
- [ ] Schedule maintenance window
- [ ] Create full database backup
- [ ] Prepare verification scripts

### Phase 2: Execution (Database Changes)
- [ ] Execute reseed strategy (A, B, or C)
- [ ] Add missing L0 kernel accounts
- [ ] Add missing L1 kernel accounts
- [ ] Update chart templates
- [ ] Mark legacy accounts as deprecated

### Phase 3: Validation (Audit)
- [ ] Run L0 completeness check
- [ ] Run system account validation
- [ ] Run hierarchy integrity check
- [ ] Run template validation
- [ ] Run full kernel compliance audit

### Phase 4: Activation
- [ ] Enable new kernel templates for onboarding
- [ ] Document migration in changelog
- [ ] Update deployment documentation
- [ ] Monitor new company onboardings

---

## Dependencies

**Blocks:**
- Chart template seeding (`seed_chart_templates.py`)
- New company onboarding
- Fiscal period closing (missing system accounts)

**Blocked By:**
- Kernel 2025.2 ratification ✅ COMPLETE
- Database backup capability
- Maintenance window approval

---

## Success Criteria

Migration is successful when:

1. ✅ All 20 L0 accounts exist in master chart
2. ✅ System accounts (`32000`, `39999`) are present
3. ✅ Chart templates reference kernel accounts only
4. ✅ No existing transactions are disrupted
5. ✅ New companies onboard with kernel-aligned charts
6. ✅ Kernel compliance audit passes

---

**Authority:** This plan conforms to Kernel 2025.2 (frozen, immutable).
**Prepared By:** Aequitas Systems Architecture
**Date:** 2025-12-24
**Status:** DESIGN-ONLY (Awaiting Approval)
