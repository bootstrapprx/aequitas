# Existing Company Remediation Strategy

**Purpose:** Handle companies that onboarded under broken or incomplete templates, without rewriting history.

**Authority:** Canon III (Evolution and State) — History is immutable, changes are additive and forward-only.
**Date:** 2025-12-24
**Status:** Design-Only

---

## Problem Statement

**Before Kernel 2025.2:**
- Onboarding templates contained only 5-6 accounts
- Companies onboarded with structurally incomplete charts
- Missing critical accounts:
  - `32000` — Retained Earnings (required for fiscal closing)
  - `39999` — Current Period Earnings (system-calculated equity)
  - Taxes Payable, Accrued Liabilities, and other L0 core accounts

**Impact:**
- Companies cannot close fiscal periods
- Balance sheets cannot balance
- Financial reporting is broken

**Constraint:**
- We CANNOT rewrite history
- We CANNOT delete posted transactions
- We MUST preserve audit trail

**Solution:**
- Detect non-compliant companies
- Add missing accounts (forward-only, additive)
- Preserve all existing data

---

## Detection Logic

### Identifying Non-Kernel-Compliant Companies

A company is **non-compliant** if its chart is missing any L0 kernel account.

#### Detection Query
```sql
-- Check if company has all 20 L0 kernel accounts
WITH kernel_l0 AS (
  SELECT unnest(ARRAY[
    '10000', '10100', '12000', '14000', '15000', '15900',
    '20000', '21000', '22000', '23000',
    '30000', '32000', '39999',
    '40000', '49000', '50000',
    '60000', '61000', '62000', '69000'
  ]) AS required_code
),
company_codes AS (
  SELECT DISTINCT code
  FROM company_accounts
  WHERE company_id = :company_id
)
SELECT k.required_code
FROM kernel_l0 k
LEFT JOIN company_codes c ON k.required_code = c.code
WHERE c.code IS NULL;

-- If this returns any rows, the company is non-compliant
```

#### Detection Service (Python)
```python
# Example detection logic (reference only, not executable)

def is_company_kernel_compliant(company_id: uuid.UUID, db: Session) -> bool:
    """Check if company has all L0 kernel accounts."""

    L0_KERNEL_CODES = {
        '10000', '10100', '12000', '14000', '15000', '15900',
        '20000', '21000', '22000', '23000',
        '30000', '32000', '39999',
        '40000', '49000', '50000',
        '60000', '61000', '62000', '69000'
    }

    company_codes = {
        acc.code for acc in
        db.query(CompanyAccount.code)
          .filter(CompanyAccount.company_id == company_id)
          .all()
    }

    missing = L0_KERNEL_CODES - company_codes

    return len(missing) == 0


def get_missing_kernel_accounts(company_id: uuid.UUID, db: Session) -> list[str]:
    """Return list of missing L0 kernel account codes."""

    L0_KERNEL_CODES = {...}  # Same as above

    company_codes = {...}  # Same as above

    return sorted(list(L0_KERNEL_CODES - company_codes))
```

---

## Remediation Paths

### Option A: Auto-Add Missing Kernel Accounts (Non-Disruptive)

**When to Use:**
- Companies with no posted transactions
- Companies in early onboarding
- System-initiated repair (background job)

**Approach:**
1. Detect missing L0 accounts
2. Create missing `CompanyAccount` records
3. Map to corresponding `MasterAccount` entries
4. Preserve `sort_order` and hierarchy

**Implementation:**
```python
# Reference implementation (design only)

def auto_remediate_company(company_id: uuid.UUID, db: Session) -> dict:
    """
    Add missing L0 kernel accounts to a company's chart.

    Returns:
        dict with 'added_count' and 'added_codes'
    """

    missing_codes = get_missing_kernel_accounts(company_id, db)

    if not missing_codes:
        return {'added_count': 0, 'added_codes': []}

    # Get master accounts for missing codes
    master_accounts = db.query(MasterAccount).filter(
        MasterAccount.code.in_(missing_codes)
    ).all()

    master_by_code = {ma.code: ma for ma in master_accounts}

    # Create company accounts
    added_codes = []
    for code in missing_codes:
        if code not in master_by_code:
            # Log warning: master account missing
            continue

        master = master_by_code[code]

        company_account = CompanyAccount(
            id=uuid4(),
            company_id=company_id,
            code=code,
            name=master.description,
            type=master.type,
            category=master.category,
            mapped_master_account_id=master.id,
            is_active=True,
            is_system=code in ['32000', '39999'],  # Mark system accounts
            created_at=datetime.utcnow(),
        )

        db.add(company_account)
        added_codes.append(code)

    db.commit()

    return {
        'added_count': len(added_codes),
        'added_codes': added_codes
    }
```

**Safety:**
- ✅ **Additive only** (no deletions)
- ✅ **Preserves existing accounts**
- ✅ **No transaction impact** (adds accounts, not entries)
- ✅ **Audit trail preserved**

**Risks:**
- Low (adds missing structure only)

---

### Option B: Guided Remediation Wizard (User-Visible)

**When to Use:**
- Companies with posted transactions
- Companies requiring user consent
- Interactive remediation

**User Experience:**

#### Step 1: Detection & Notification
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  Chart of Accounts Update Required                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Your chart is missing 14 accounts required for fiscal      │
│ period closing and financial reporting.                     │
│                                                             │
│ This happened because you onboarded before December 2024,   │
│ when our templates were incomplete.                         │
│                                                             │
│ We can add these accounts for you automatically, with no    │
│ impact on your existing transactions.                       │
│                                                             │
│ Missing accounts include:                                   │
│   • Retained Earnings (required for closing)                │
│   • Current Period Earnings (system account)                │
│   • 12 other core accounts                                  │
│                                                             │
│ [View Full List] [Add Accounts Now] [Remind Me Later]      │
└─────────────────────────────────────────────────────────────┘
```

#### Step 2: Review Missing Accounts
```
┌─────────────────────────────────────────────────────────────┐
│ Missing Accounts to be Added                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✅ 10100 — Undeposited Funds                                │
│ ✅ 12000 — Accounts Receivable                              │
│ ✅ 14000 — Prepaid Expenses                                 │
│ ✅ 15000 — Fixed Assets                                     │
│ ✅ 15900 — Accumulated Depreciation                         │
│ ✅ 21000 — Accrued Liabilities                              │
│ ✅ 22000 — Taxes Payable                                    │
│ ✅ 23000 — Deferred Revenue                                 │
│ ✅ 32000 — Retained Earnings (System Account)               │
│ ✅ 39999 — Current Period Earnings (System Account)         │
│ ✅ 49000 — Refunds / Allowances                             │
│ ✅ 61000 — Payroll Expense                                  │
│ ✅ 62000 — Depreciation Expense                             │
│ ✅ 69000 — Tax Expense                                      │
│                                                             │
│ ℹ️  These accounts will be added to your chart but will     │
│    remain unused until you create transactions.             │
│                                                             │
│ ℹ️  Your existing accounts and transactions will NOT be     │
│    modified or deleted.                                     │
│                                                             │
│ [Cancel] [Add These Accounts]                               │
└─────────────────────────────────────────────────────────────┘
```

#### Step 3: Confirmation
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Chart Updated Successfully                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 14 accounts have been added to your chart.                  │
│                                                             │
│ You can now:                                                │
│   • Close fiscal periods                                    │
│   • Generate complete financial statements                  │
│   • Use all system features                                 │
│                                                             │
│ Your existing transactions remain unchanged.                │
│                                                             │
│ [View Updated Chart] [Continue]                             │
└─────────────────────────────────────────────────────────────┘
```

**Backend Implementation:**
- Same as Option A (auto-add logic)
- Triggered by user consent (not automatic)
- Log remediation event in audit trail

**Safety:**
- ✅ **User consent required**
- ✅ **Transparent (user sees what's added)**
- ✅ **Additive only**
- ✅ **Audit trail preserved**

---

## What Is Forbidden

### Absolute Prohibitions

1. ❌ **NEVER delete existing accounts**
   - Even if they seem "wrong" or "duplicate"
   - Deletion breaks historical references

2. ❌ **NEVER remap posted journal entries**
   - Do not change `account_id` on existing entries
   - History is immutable (Canon III)

3. ❌ **NEVER modify account codes**
   - Do not change `code` field on existing accounts
   - Breaks prior period reports

4. ❌ **NEVER auto-post transactions**
   - Remediation adds STRUCTURE, not DATA
   - Journal entries require human intent

### Permitted Operations

1. ✅ **Add missing accounts** (forward-only)
2. ✅ **Mark accounts as system** (`is_system = true`)
3. ✅ **Update metadata** (`notes`, `description`)
4. ✅ **Log remediation events** (audit trail)

---

## Audit Guarantees

### How Remediation Preserves Accounting Truth

**Before Remediation:**
```
Company Chart:
  10000 — Cash
  20000 — Accounts Payable
  30000 — Equity
  40000 — Revenue
  50000 — COGS
  60000 — Expenses

Journal Entries:
  Entry #1: Debit 60000 ($1000), Credit 10000 ($1000)
  Entry #2: Debit 10000 ($500), Credit 40000 ($500)
```

**After Remediation (Option A or B):**
```
Company Chart:
  10000 — Cash
  10100 — Undeposited Funds (ADDED)
  12000 — Accounts Receivable (ADDED)
  20000 — Accounts Payable
  21000 — Accrued Liabilities (ADDED)
  22000 — Taxes Payable (ADDED)
  30000 — Equity
  32000 — Retained Earnings (ADDED, SYSTEM)
  39999 — Current Period Earnings (ADDED, SYSTEM)
  40000 — Revenue
  49000 — Refunds / Allowances (ADDED)
  50000 — COGS
  60000 — Expenses
  61000 — Payroll Expense (ADDED)
  62000 — Depreciation Expense (ADDED)
  69000 — Tax Expense (ADDED)

Journal Entries:
  Entry #1: Debit 60000 ($1000), Credit 10000 ($1000)  [UNCHANGED]
  Entry #2: Debit 10000 ($500), Credit 40000 ($500)    [UNCHANGED]
```

**Guarantees:**

1. **Double-Entry Integrity Preserved**
   - All existing entries still balance (debits = credits)
   - No retroactive changes

2. **Audit Trail Intact**
   - All historical transactions remain unchanged
   - Original account references preserved

3. **Accounting Equation Solvable**
   - Added equity accounts enable period closing
   - Balance sheet can now balance

4. **Forward Compatibility**
   - Company can now use all system features
   - Fiscal period closing enabled

---

## Remediation Workflow

### Automated Background Job (Option A)

```python
# Reference design (not executable)

def remediate_non_compliant_companies(db: Session, dry_run: bool = True):
    """
    Background job to remediate all non-compliant companies.

    Args:
        dry_run: If True, only log what would be done (don't modify)
    """

    companies = db.query(Company).filter(Company.is_active == True).all()

    results = {
        'total': len(companies),
        'compliant': 0,
        'remediated': 0,
        'failed': 0,
        'errors': []
    }

    for company in companies:
        try:
            if is_company_kernel_compliant(company.id, db):
                results['compliant'] += 1
                continue

            missing = get_missing_kernel_accounts(company.id, db)

            if dry_run:
                logger.info(f"Company {company.id} missing {len(missing)} accounts: {missing}")
                continue

            # Execute remediation
            result = auto_remediate_company(company.id, db)

            # Log event
            log_remediation_event(
                company_id=company.id,
                added_codes=result['added_codes'],
                timestamp=datetime.utcnow()
            )

            results['remediated'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'company_id': str(company.id),
                'error': str(e)
            })

    return results
```

**Execution:**
```bash
# Dry run first (audit mode)
python manage.py remediate_companies --dry-run

# Execute remediation
python manage.py remediate_companies --execute
```

---

### Manual Wizard Flow (Option B)

**Trigger:**
- User attempts to close fiscal period
- Dashboard shows "Chart Incomplete" warning
- Admin manually triggers remediation

**Backend Endpoint:**
```python
@router.post("/companies/{company_id}/remediate-chart")
def remediate_company_chart(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add missing L0 kernel accounts to company chart.
    Requires user authentication and company ownership.
    """

    # Verify user owns company
    if not user_owns_company(current_user.id, company_id, db):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if remediation needed
    missing = get_missing_kernel_accounts(company_id, db)

    if not missing:
        return {"message": "Chart is already compliant", "added_count": 0}

    # Execute remediation
    result = auto_remediate_company(company_id, db)

    # Log event
    log_remediation_event(
        company_id=company_id,
        user_id=current_user.id,
        added_codes=result['added_codes'],
        timestamp=datetime.utcnow()
    )

    return {
        "message": "Chart remediated successfully",
        "added_count": result['added_count'],
        "added_codes": result['added_codes']
    }
```

---

## Remediation Event Logging

Every remediation MUST be logged for audit trail.

**Event Schema:**
```python
class RemediationEvent(Base):
    __tablename__ = "remediation_events"

    id = Column(UUID, primary_key=True, default=uuid4)
    company_id = Column(UUID, ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)  # Null if automated

    remediation_type = Column(String)  # 'kernel_compliance', 'manual', 'automated'
    accounts_added = Column(ARRAY(String))  # ['32000', '39999', ...]
    account_count = Column(Integer)

    triggered_by = Column(String)  # 'user_action', 'background_job', 'system_check'

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    notes = Column(Text, nullable=True)
```

**Example Log Entry:**
```json
{
  "id": "uuid",
  "company_id": "company-uuid",
  "user_id": null,
  "remediation_type": "kernel_compliance",
  "accounts_added": ["32000", "39999", "10100", "12000", ...],
  "account_count": 14,
  "triggered_by": "background_job",
  "created_at": "2025-12-24T20:00:00Z",
  "notes": "Auto-remediation: Added missing L0 kernel accounts"
}
```

---

## Rollback Plan

If remediation introduces issues:

1. **Identify problematic accounts**
   - Check remediation event logs
   - Query `remediation_events` table

2. **Mark added accounts as inactive** (do NOT delete)
   ```sql
   UPDATE company_accounts
   SET is_active = false
   WHERE company_id = :company_id
   AND code IN (SELECT unnest(accounts_added) FROM remediation_events WHERE id = :event_id);
   ```

3. **Preserve audit trail**
   - Log rollback event
   - Document reason for rollback

4. **Never:**
   - Delete accounts (breaks references)
   - Modify historical entries

---

## Success Criteria

Remediation is successful when:

1. ✅ All non-compliant companies have L0 kernel accounts
2. ✅ No existing transactions are modified
3. ✅ Fiscal period closing is enabled for all companies
4. ✅ Remediation events are logged for audit
5. ✅ User experience is transparent (Option B) or invisible (Option A)

---

## Dependencies

**Requires:**
- Master Chart Reseed (L0 accounts must exist in master chart)
- Kernel 2025.2 ratification ✅ COMPLETE

**Enables:**
- Fiscal period closing for existing companies
- Complete financial reporting
- Full system feature access

---

**Authority:** This strategy conforms to Canon III (immutable history, additive changes).
**Prepared By:** Aequitas Systems Architecture
**Date:** 2025-12-24
**Status:** DESIGN-ONLY (Awaiting Approval)
