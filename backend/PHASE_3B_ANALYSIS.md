# Phase 3B: API & Service Layer Alignment - Analysis & Plan

**Date:** 2025-12-14
**Author:** Claude Code (Tech Lead)
**Status:** 🚧 IN PROGRESS
**Prerequisites:** Phase 3A Complete ✅

---

## Executive Summary

Phase 3B requires comprehensive refactoring of the service layer and API endpoints to eliminate all use of deprecated string-code foreign keys (`parent_code`, `master_account_code`) and replace them with UUID-based foreign keys (`parent_id`, `mapped_master_account_id`).

**Critical Issues Identified:**
1. ❌ `companychart_service.py` - Extensively uses `parent_code` and `master_account_code`
2. ❌ `mapping_service.py` - Uses string codes instead of UUID FKs
3. ❌ API responses - Return deprecated fields to frontend
4. ⚠️ Missing account locking service methods
5. ⚠️ Missing invariant enforcement (locked accounts, debit=credit, mandatory accounts)

---

## 1. Service Layer Analysis

### 1.1 companychart_service.py - CRITICAL REFACTOR REQUIRED

**File:** `backend/app/services/companychart_service.py`

**Problem Areas:**

#### A. Parent Relationship Logic (Lines 89-96, 134-139, 161-167)
```python
# ❌ CURRENT (uses parent_code)
if account_data.parent_code:
    parent = self.get_account_by_code(company_id, account_data.parent_code)
    if not parent:
        raise ValueError(f"Parent account with code {account_data.parent_code} not found.")

# ✅ REQUIRED (use parent_id)
if account_data.parent_id:
    parent = self.get_account_by_id(account_data.parent_id)
    if not parent or parent.company_id != company_id:
        raise ValueError(f"Parent account not found or belongs to different company.")
```

#### B. Tree Building (Lines 173-224)
```python
# ❌ CURRENT (uses parent_code for hierarchy)
"parent_code": acc.parent_code,
if acc.parent_code and acc.parent_code in account_map:
    continue

# ✅ REQUIRED (use parent_id)
"parent_id": str(acc.parent_id) if acc.parent_id else None,
if acc.parent_id and acc.parent_id in account_map:
    continue
```

#### C. Initialization from Master Chart (Lines 251-296)
```python
# ❌ CURRENT (sets deprecated fields)
company_acc = CompanyAccount(
    company_id=company_id,
    code=master_acc.code,
    description=master_acc.description,
    type=master_acc.type,
    parent_code=master_acc.parent_code,  # ❌ DEPRECATED
    master_account_code=master_acc.code,  # ❌ DEPRECATED
    ...
)

# ✅ REQUIRED (use UUID FKs)
company_acc = CompanyAccount(
    company_id=company_id,
    code=master_acc.code,
    description=master_acc.description,
    type=master_acc.type,
    parent_id=parent_account_uuid,  # ✅ UUID FK
    mapped_master_account_id=master_acc.id,  # ✅ UUID FK
    account_type=determine_account_type(master_acc.category),
    normal_balance=NormalBalance(master_acc.normal_balance),
    ...
)
```

#### D. Statistics (Lines 238)
```python
# ❌ CURRENT
mapped_count = sum(1 for acc in active_accounts if acc.master_account_code)

# ✅ REQUIRED
mapped_count = sum(1 for acc in active_accounts if acc.mapped_master_account_id)
```

**Impact:**
- 🔴 HIGH - Core service used by all chart operations
- 🔴 BREAKING - Changes affect all API endpoints
- 🔴 DATA - Must handle accounts created before Phase 3B

---

### 1.2 mapping_service.py - MODERATE REFACTOR REQUIRED

**File:** `backend/app/services/mapping_service.py`

**Problem Areas:**

#### A. Mapping Creation (Lines 106-158)
```python
# ❌ CURRENT (uses string code)
def create_mapping(
    self,
    company_account_id: UUID,
    master_code: str,  # ❌ String code
    confidence: float,
    ...
) -> AccountMapping:
    # Verify master code exists
    master_account = self.master_chart_service.get_account_by_code(master_code)
    if not master_account:
        raise ValueError(f"Master account {master_code} not found")

# ✅ REQUIRED (use UUID)
def create_mapping(
    self,
    company_account_id: UUID,
    mapped_master_account_id: UUID,  # ✅ UUID FK
    confidence: float,
    ...
) -> AccountMapping:
    # Verify master account exists
    master_account = self.db.query(MasterAccount).filter(
        MasterAccount.id == mapped_master_account_id
    ).first()
    if not master_account:
        raise ValueError(f"Master account {mapped_master_account_id} not found")
```

**Note:** This is a less critical issue because the AccountMapping table still uses `master_code` (String) as a foreign key. This table may need schema changes in a future phase, but for now we can leave it as-is while ensuring CompanyAccount uses `mapped_master_account_id`.

**Impact:**
- 🟡 MEDIUM - Mapping service is secondary to chart service
- 🟡 PARTIAL - AccountMapping table schema may need future work
- ✅ OPTIONAL - Can be deferred if AccountMapping table keeps string FK

---

### 1.3 Missing Service Methods

#### A. Account Locking Service Methods
**File:** New methods needed in `companychart_service.py`

```python
def lock_account(
    self,
    account_id: UUID,
    reason: LockedReason,
    user_id: Optional[UUID] = None
) -> CompanyAccount:
    """Lock an account to prevent type/code/hierarchy changes"""

def unlock_account(
    self,
    account_id: UUID,
    user_id: UUID
) -> CompanyAccount:
    """Unlock an account (superuser only, service layer must verify)"""

def can_delete_account(
    self,
    account_id: UUID
) -> tuple[bool, Optional[str]]:
    """Check if account can be deleted (no transactions, not mandatory)"""
```

#### B. Invariant Enforcement Methods
**File:** New service or validator class

```python
def validate_journal_entry_balance(
    entry_lines: List[JournalEntryLine]
) -> tuple[bool, Optional[str]]:
    """Ensure debits equal credits"""

def validate_locked_account_mutation(
    account: CompanyAccount,
    update_data: dict
) -> tuple[bool, Optional[str]]:
    """Prevent locked account type/code changes"""

def validate_mandatory_account_deletion(
    account: CompanyAccount
) -> tuple[bool, Optional[str]]:
    """Prevent deletion of template-mandatory accounts"""
```

**Impact:**
- 🟡 MEDIUM - Required for GAAP compliance
- 🟠 IMPORTANT - Database triggers exist, but service-layer validation improves UX
- ✅ NEW FUNCTIONALITY - Adds proper business rules

---

## 2. API Endpoint Analysis

### 2.1 companychart.py - Response Schema Issues

**File:** `backend/app/api/v1/companychart.py`

**Problem:**
```python
# API returns CompanyAccountSchema which includes deprecated fields
@router.get("/companies/{company_id}/chart", response_model=List[CompanyAccountSchema])
def get_company_chart(...):
    ...
```

**Current Response (INCORRECT):**
```json
{
  "id": "uuid",
  "code": "1.10.10",
  "description": "Cash - Operating",
  "parent_code": "1.10",  // ❌ DEPRECATED - should not be returned
  "master_account_code": "1.10.10.10",  // ❌ DEPRECATED
  "type": "D"
}
```

**Required Response (CORRECT):**
```json
{
  "id": "uuid",
  "code": "1.10.10",
  "description": "Cash - Operating",
  "parent_id": "parent-uuid",  // ✅ UUID FK
  "mapped_master_account_id": "master-uuid",  // ✅ UUID FK
  "account_type": "Asset",  // ✅ Enum
  "normal_balance": "Debit",  // ✅ Enum
  "is_locked": false,  // ✅ New field
  "locked_reason": null,  // ✅ New field
  "type": "D"
}
```

**Impact:**
- 🔴 BREAKING - Frontend expects these fields
- 🔴 HIGH - All chart API endpoints affected
- 🔴 COORDINATED - Requires frontend updates

---

### 2.2 Missing API Endpoints

#### A. Account Locking Endpoints
**File:** `backend/app/api/v1/companychart.py` (add new endpoints)

```python
@router.post(
    "/companies/{company_id}/chart/{account_id}/lock",
    response_model=CompanyAccountSchema
)
def lock_company_account(...):
    """Lock an account to prevent structural changes"""

@router.post(
    "/companies/{company_id}/chart/{account_id}/unlock",
    response_model=CompanyAccountSchema
)
def unlock_company_account(...):
    """Unlock an account (superuser only)"""
```

#### B. Account Hierarchy Endpoint (UUID-based)
**File:** `backend/app/api/v1/companychart.py`

```python
@router.get(
    "/companies/{company_id}/chart/tree-uuids",
    response_model=List[CompanyAccountTree]
)
def get_company_chart_tree_uuids(...):
    """Get hierarchical tree using UUID relationships (not codes)"""
```

**Impact:**
- ✅ NEW FUNCTIONALITY - Improves API surface
- 🟢 NON-BREAKING - Additive changes only
- 🔵 ENHANCEMENT - Better frontend UX

---

## 3. Data Migration Considerations

### 3.1 Existing Accounts with Deprecated Fields

**Problem:**
Accounts created before Phase 3B may have:
- `parent_code` set (string) but `parent_id` = NULL
- `master_account_code` set (string) but `mapped_master_account_id` = NULL

**Migration Strategy:**

#### Option A: One-Time Data Migration (RECOMMENDED)
```sql
-- Migrate parent_code to parent_id
UPDATE company_accounts ca
SET parent_id = (
    SELECT id FROM company_accounts parent
    WHERE parent.company_id = ca.company_id
    AND parent.code = ca.parent_code
)
WHERE ca.parent_code IS NOT NULL
AND ca.parent_id IS NULL;

-- Migrate master_account_code to mapped_master_account_id
UPDATE company_accounts ca
SET mapped_master_account_id = (
    SELECT id FROM master_accounts ma
    WHERE ma.code = ca.master_account_code
)
WHERE ca.master_account_code IS NOT NULL
AND ca.mapped_master_account_id IS NULL;
```

**When to run:** Before deploying Phase 3B services

#### Option B: Service-Layer Fallback (TEMPORARY)
```python
def get_parent_id(account: CompanyAccount) -> Optional[UUID]:
    """
    Get parent_id with fallback to parent_code lookup.
    TEMPORARY: Remove after data migration.
    """
    if account.parent_id:
        return account.parent_id

    # Fallback: lookup parent by code
    if account.parent_code:
        parent = self.get_account_by_code(account.company_id, account.parent_code)
        return parent.id if parent else None

    return None
```

**Impact:**
- 🔴 CRITICAL - Must handle existing data
- 🟠 ONE-TIME - Migration needed before Phase 3B deployment
- ✅ REVERSIBLE - Can keep deprecated columns for rollback

---

## 4. Refactoring Plan

### Phase 3B.1: Data Migration (CRITICAL - DO FIRST)
1. ✅ Verify all company_accounts have `account_type` and `normal_balance`
2. ✅ Run SQL migration to populate `parent_id` from `parent_code`
3. ✅ Run SQL migration to populate `mapped_master_account_id` from `master_account_code`
4. ✅ Verify data integrity (no orphaned references)

### Phase 3B.2: Service Layer Refactoring
1. ✅ Create account locking service methods
2. ✅ Refactor `companychart_service.py` to use UUID FKs
3. ✅ Update `build_tree()` to use `parent_id`
4. ✅ Update `initialize_from_master_chart()` to set UUID FKs
5. ✅ Add invariant validation methods

### Phase 3B.3: API Endpoint Updates
1. ✅ Update response schemas (remove deprecated fields)
2. ✅ Add account locking endpoints
3. ✅ Update documentation

### Phase 3B.4: Verification & Testing
1. ✅ Test account creation with parent_id
2. ✅ Test tree building with UUID relationships
3. ✅ Test account locking workflow
4. ✅ Verify all deprecated field references removed

---

## 5. Breaking Changes Summary

### For Frontend Developers

**⚠️ BREAKING CHANGES:**

❌ **Removed from API responses:**
```json
{
  "parent_code": "1.10",  // ❌ NO LONGER RETURNED
  "master_account_code": "1.10.10.10"  // ❌ NO LONGER RETURNED
}
```

✅ **Added to API responses:**
```json
{
  "parent_id": "uuid-of-parent",  // ✅ NEW
  "mapped_master_account_id": "uuid-of-master",  // ✅ NEW
  "account_type": "Asset",  // ✅ NEW
  "normal_balance": "Debit",  // ✅ NEW
  "is_locked": false,  // ✅ NEW
  "locked_at": null,  // ✅ NEW
  "locked_reason": null,  // ✅ NEW
  "locked_by": null  // ✅ NEW
}
```

**Migration Required:**
- Update all frontend code using `parent_code` to use `parent_id`
- Update all frontend code using `master_account_code` to use `mapped_master_account_id`
- Store account lookups by ID, not code
- Add UI for account locking status

---

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing data has NULL UUID FKs | 🔴 HIGH | Run data migration SQL before deploying |
| Frontend breaks on missing fields | 🔴 HIGH | Coordinate frontend update with backend deployment |
| Service logic breaks during refactor | 🟡 MEDIUM | Comprehensive unit testing before deployment |
| Rollback difficulty | 🟡 MEDIUM | Keep deprecated columns in database (don't drop) |
| Performance degradation | 🟢 LOW | UUID joins are well-indexed |

---

## 7. Next Steps

1. **Create Data Migration Script** - SQL to populate UUID FKs
2. **Refactor companychart_service.py** - Remove all `parent_code`/`master_account_code` usage
3. **Add Locking Service Methods** - Implement account locking workflow
4. **Update API Schemas** - Remove deprecated fields from responses
5. **Add New Endpoints** - Lock/unlock account endpoints
6. **Testing** - Comprehensive service and API testing
7. **Documentation** - Update API docs and frontend migration guide

---

**Phase 3B Status:** 🚧 **IN PROGRESS** (Analysis Complete, Ready for Implementation)
**Estimated Complexity:** 🔴 HIGH
**Estimated Impact:** 🔴 BREAKING (Requires coordinated frontend update)

**Sign-off:** Claude Code (Tech Lead)
**Date:** 2025-12-14
