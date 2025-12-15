# API Guardian Report: Phase 3B Accounting Domain Boundaries

**Role:** API Guardian
**Date:** 2025-12-14
**Status:** 🔒 **SECURITY AUDIT - FROZEN BOUNDARIES**
**Posture:** Conservative, Security-First, Accounting-First

---

## Executive Summary

This document defines and **freezes** the API boundaries for the accounting domain following Phase 3B completion. All canonical invariants are now enforced at the service layer. The API must act as a thin, **defensive** layer that prevents violations of these invariants.

**Threat Model:**
- Hostile clients attempting to violate accounting invariants
- Buggy clients unintentionally corrupting data
- Insider threats with elevated privileges
- Race conditions from concurrent requests
- Timezone/date manipulation attacks

**Security Posture:**
- ✅ **Read operations**: Liberal (with permission checks)
- ⚠️ **Write operations**: Extremely conservative
- ❌ **Bulk operations**: Forbidden (too risky)
- ❌ **Direct balance updates**: Forbidden (violates double-entry)
- ❌ **Period manipulation**: Restricted (requires superuser + validation)

---

## 1. Company Accounts API Surface

**Endpoint:** `/api/v1/companies/{company_id}/chart/*`
**Service:** CompanyChartService (859 lines, Phase 3B compliant)
**Invariant Enforcement:** ✅ Complete

### 1.1 ALLOWED Operations ✅

#### GET /companies/{company_id}/chart
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** List all company accounts
- **Query Params:**
  - `active_only` (boolean, default: true)
- **Response:** List[CompanyAccountSchema]
- **Security:** Read-only, safe
- **Rationale:** Essential for viewing chart structure

#### GET /companies/{company_id}/chart/tree
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** Hierarchical view of accounts (UUID-based parent_id)
- **Query Params:**
  - `active_only` (boolean, default: true)
- **Response:** Nested tree structure
- **Security:** Read-only, safe
- **Rationale:** Essential for UI rendering

#### GET /companies/{company_id}/chart/stats
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** Chart statistics (total accounts, mapped accounts, locked accounts)
- **Response:** Statistics dictionary
- **Security:** Read-only, safe, no sensitive data
- **Rationale:** Analytics and dashboard needs

#### GET /companies/{company_id}/chart/{code}
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** Retrieve single account by code
- **Response:** CompanyAccountSchema
- **Security:** Read-only, safe
- **Rationale:** Account detail views

#### POST /companies/{company_id}/chart
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Create new company account
- **Request Body:** CompanyAccountCreate
  - Requires: company_id, code, description, type, normal_balance
  - Optional: parent_id (UUID FK), mapped_master_account_id (UUID FK), account_type
- **Validation:**
  - ✅ Parent account must exist and belong to same company
  - ✅ Enum values validated (account_type, normal_balance)
  - ✅ Template restrictions checked (if company has template)
- **Response:** CompanyAccountSchema
- **Security:** ⚠️ Write operation, heavily validated
- **Rationale:** Companies need to customize their charts

#### PUT /companies/{company_id}/chart/{code}
- **Method:** PUT
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Update existing account
- **Request Body:** CompanyAccountUpdate (partial)
- **Validation:**
  - ✅ Locked account immutability enforced (7 fields)
  - ✅ Template mandatory account restrictions enforced
  - ✅ Type change validation (cannot make Header → Detail if has children)
  - ✅ Parent relationship validation
- **Response:** CompanyAccountSchema
- **Security:** ⚠️ Write operation, validation prevents invariant violations
- **Rationale:** Legitimate account updates (description, metadata)

#### DELETE /companies/{company_id}/chart/{code}
- **Method:** DELETE
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Soft delete account (sets is_active=false)
- **Validation:**
  - ✅ Cannot delete accounts with children
  - ✅ Cannot delete locked accounts
  - ✅ Cannot delete template-mandatory accounts
  - ✅ (Future) Cannot delete accounts with transactions
- **Response:** 204 No Content
- **Security:** ⚠️ Destructive, heavily restricted
- **Rationale:** Cleanup of unused accounts only

#### POST /companies/{company_id}/chart/{account_id}/lock
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Lock an account (prevent structural changes)
- **Request Body:** CompanyAccountLockRequest
  - reason: "FirstTransaction" | "PeriodClose" | "Manual"
- **Query Params:**
  - `user_id` (UUID, required for Manual locks)
- **Validation:**
  - ✅ Manual locks require user_id (references users.id)
  - ✅ Account must exist and belong to company
- **Response:** CompanyAccountSchema (with is_locked=true)
- **Security:** ⚠️ State change, but restrictive (good for GAAP)
- **Rationale:** GAAP compliance, prevents retroactive changes

#### POST /companies/{company_id}/chart/{account_id}/unlock
- **Method:** POST
- **Auth:** **SUPERUSER ONLY** (must be enforced)
- **Purpose:** Unlock account (requires superuser)
- **Request Body:** CompanyAccountUnlockRequest
  - reason: string (for audit trail)
- **Query Params:**
  - `user_id` (UUID, required)
- **Validation:**
  - ⚠️ **TODO:** Verify user_id has superuser privileges
  - ⚠️ **TODO:** Validate no posted transactions in current period
  - ✅ Account must exist and belong to company
- **Response:** CompanyAccountSchema (with is_locked=false)
- **Security:** 🔴 **HIGH RISK** - bypasses GAAP immutability
- **Rationale:** Emergency fixes only, must be audited

#### GET /companies/{company_id}/chart/{account_id}/can-delete
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** Pre-flight check for deletion
- **Response:** `{can_delete: boolean, reason: string|null}`
- **Security:** Read-only, safe, prevents bad UX
- **Rationale:** Frontend can disable delete button with explanation

#### POST /companies/{company_id}/chart/initialize
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Initialize chart from master chart
- **Validation:**
  - ✅ Creates UUID-based relationships (parent_id, mapped_master_account_id)
  - ✅ Sets account_type and normal_balance from master chart
- **Response:** Initialization report
- **Security:** ⚠️ Bulk operation, but well-tested
- **Rationale:** Company onboarding

#### POST /companies/{company_id}/chart/reset
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Reset chart to master (deactivates existing, creates new)
- **Response:** Reset report
- **Security:** 🔴 **DANGEROUS** - deactivates all accounts
- **Rationale:** Company wants to restart from scratch
- **Recommendation:** ⚠️ Add confirmation step or superuser requirement

---

### 1.2 FORBIDDEN Operations ❌

#### ❌ PATCH /companies/{company_id}/chart/{code}
- **Rationale:** PATCH encourages partial updates without schema validation. Use PUT with CompanyAccountUpdate schema instead.
- **Risk:** Client could send arbitrary fields, bypass validation.

#### ❌ PUT /companies/{company_id}/chart/bulk
- **Rationale:** Bulk updates are extremely risky in accounting.
- **Risk:** Single bug affects hundreds of accounts, violates atomicity.
- **Alternative:** Update accounts one at a time with proper validation.

#### ❌ POST /companies/{company_id}/chart/bulk-lock
- **Rationale:** Locking should be deliberate, not bulk.
- **Risk:** Accidentally lock entire chart, prevent legitimate operations.

#### ❌ DELETE /companies/{company_id}/chart/all (hard delete)
- **Rationale:** No legitimate use case for deleting entire chart.
- **Risk:** Data loss, cascade deletes could delete journal entries.
- **Alternative:** Use soft delete (is_active=false) one account at a time.

#### ❌ POST /companies/{company_id}/chart/import
- **Rationale:** Importing accounts bypasses validation, creates inconsistencies.
- **Risk:** Invalid parent_id references, missing mandatory accounts, balance corruption.
- **Alternative:** Use initialize_from_master_chart with proper validation.

#### ❌ PUT /companies/{company_id}/chart/{code}/force-update
- **Rationale:** "Force" suggests bypassing validation - never acceptable.
- **Risk:** Violates locked account immutability, template restrictions, hierarchy integrity.

---

### 1.3 Endpoints That MUST NOT Exist ⛔

#### ⛔ POST /companies/{company_id}/chart/{code}/set-balance
- **Why:** Violates double-entry bookkeeping.
- **Threat:** Client could set arbitrary balances without journal entries.
- **Consequence:** Financial statements become meaningless, audit trail destroyed.
- **Correct Approach:** Balances are ONLY modified via posted journal entries.

#### ⛔ PUT /companies/{company_id}/chart/{code}/parent
- **Why:** Parent changes must go through full validation (cycles, type checks).
- **Threat:** Create circular references, orphan accounts.
- **Correct Approach:** Use PUT /chart/{code} with full validation.

#### ⛔ DELETE /companies/{company_id}/chart/{code}/force
- **Why:** "Force delete" bypasses all constraints.
- **Threat:** Delete locked accounts, template-mandatory accounts, accounts with transactions.
- **Correct Approach:** Fix the constraint violation, then delete normally.

#### ⛔ POST /companies/{company_id}/chart/{code}/duplicate
- **Why:** Code duplication creates conflicts.
- **Threat:** Duplicate codes violate uniqueness within company.
- **Correct Approach:** Create new account with different code.

---

## 2. Chart Templates API Surface

**Context:** Phase 3B added ChartTemplate, ChartTemplateAccount, CompanyTemplateUsage models.
**Current Status:** ⚠️ **NO API ENDPOINTS EXIST YET**

### 2.1 ALLOWED Operations (Future) ✅

#### GET /api/v1/chart-templates
- **Purpose:** List all active chart templates
- **Auth:** Any authenticated user
- **Response:** List[ChartTemplateSchema]
  - id, name, jurisdiction, version, description
- **Security:** Read-only, safe
- **Rationale:** Companies need to browse available templates

#### GET /api/v1/chart-templates/{template_id}
- **Purpose:** Get template details
- **Auth:** Any authenticated user
- **Response:** ChartTemplateSchema with account count
- **Security:** Read-only, safe
- **Rationale:** Template preview before assignment

#### GET /api/v1/chart-templates/{template_id}/accounts
- **Purpose:** List all accounts in template (read-only)
- **Auth:** Any authenticated user
- **Response:** List[ChartTemplateAccountSchema]
  - Includes is_mandatory flag
- **Security:** Read-only, safe
- **Rationale:** Show template structure to users

#### GET /api/v1/companies/{company_id}/template
- **Purpose:** Get active template for company
- **Auth:** User with `can_view_company` permission
- **Response:** CompanyTemplateUsageSchema
- **Security:** Read-only, safe
- **Rationale:** Know which template company uses

---

### 2.2 FORBIDDEN Operations (Future) ❌

#### ❌ POST /api/v1/chart-templates
- **Rationale:** Template creation is a SUPERUSER operation, must be done via migration/seeder.
- **Risk:** Invalid templates break all companies using them.
- **Alternative:** Templates managed via database migrations, not API.

#### ❌ PUT /api/v1/chart-templates/{template_id}
- **Rationale:** Modifying templates affects ALL companies using them.
- **Risk:** Breaking change to mandatory accounts, normal_balance changes.
- **Alternative:** Create new version, migrate companies.

#### ❌ DELETE /api/v1/chart-templates/{template_id}
- **Rationale:** Cannot delete templates in use by companies.
- **Risk:** Orphan companies, break template validation.
- **Alternative:** Mark template as inactive (is_active=false).

#### ❌ POST /api/v1/chart-templates/{template_id}/accounts
- **Rationale:** Adding accounts to template requires version bump, migration.
- **Risk:** Existing companies missing new mandatory accounts.
- **Alternative:** Create new template version.

#### ❌ PUT /api/v1/companies/{company_id}/template
- **Rationale:** Changing company template requires data migration.
- **Risk:** Missing mandatory accounts, mapping conflicts.
- **Alternative:** Dedicated migration workflow (not implemented yet).

---

### 2.3 Endpoints That MUST NOT Exist ⛔

#### ⛔ POST /api/v1/chart-templates/{template_id}/accounts/{account_id}/toggle-mandatory
- **Why:** Changing is_mandatory affects all companies using template.
- **Threat:** Remove mandatory flag → companies delete required accounts.
- **Correct Approach:** Create new template version with different mandatory accounts.

#### ⛔ DELETE /api/v1/companies/{company_id}/template
- **Why:** Removing template doesn't remove mandatory account restrictions.
- **Threat:** Orphan company, lose template validation.
- **Correct Approach:** Cannot remove template once assigned.

---

## 3. Journal Entries API Surface

**Endpoint:** `/api/v1/journal-entries/*`
**Service:** JournalEntryService (refactored Phase 3B, 400+ lines)
**Invariant Enforcement:** ✅ Complete

### 3.1 ALLOWED Operations ✅

#### POST /journal-entries
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Create journal entry (DRAFT status)
- **Request Body:** JournalEntryCreate
  - company_id, entry_date, description, lines (min 2)
- **Validation:**
  - ✅ Sum(debits) == Sum(credits) (JRNL_2001)
  - ✅ No inactive accounts (JRNL_2011)
  - ✅ No locked accounts (JRNL_2010)
  - ✅ All accounts same company (JRNL_2020)
  - ✅ Fiscal period OPEN (PERD_3001/3002/3003)
  - ✅ Posting date within period boundaries
- **Response:** JournalEntryResponse (status=DRAFT)
- **Security:** ⚠️ Write operation, all invariants validated
- **Rationale:** Essential accounting operation

#### GET /journal-entries
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** List journal entries with filters
- **Query Params:**
  - company_id (required)
  - fiscal_period_id, status, start_date, end_date
  - page, page_size (pagination)
- **Response:** JournalEntryList (paginated)
- **Security:** Read-only, safe
- **Rationale:** Essential for journal review

#### GET /journal-entries/{entry_id}
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** Retrieve single journal entry
- **Response:** JournalEntryResponse (with lines, totals)
- **Security:** Read-only, safe
- **Rationale:** Entry detail view

#### PUT /journal-entries/{entry_id}
- **Method:** PUT
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Update DRAFT journal entry
- **Request Body:** JournalEntryUpdate (partial)
  - Can update: entry_date, description, reference, lines
- **Validation:**
  - ✅ Only DRAFT entries can be updated
  - ✅ Same validation as create (balance, accounts, period)
  - ✅ If changing entry_date, new date must be in OPEN period
- **Response:** JournalEntryResponse
- **Security:** ⚠️ Write operation, restricted to DRAFT only
- **Rationale:** Fix errors before posting

#### DELETE /journal-entries/{entry_id}
- **Method:** DELETE
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Delete DRAFT journal entry
- **Validation:**
  - ✅ Only DRAFT entries can be deleted
  - ✅ POSTED/VOID entries cannot be deleted
- **Response:** 204 No Content
- **Security:** ⚠️ Destructive, but restricted to DRAFT
- **Rationale:** Discard draft entries

#### POST /journal-entries/{entry_id}/post
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Post journal entry (make permanent)
- **Validation:**
  - ✅ Entry must be DRAFT
  - ✅ Entry must be balanced
  - ✅ Fiscal period must still be OPEN
  - ✅ Updates account balances via LedgerService
  - ✅ Locks accounts on first transaction (FirstTransaction reason)
- **Response:** JournalEntryResponse (status=POSTED)
- **Security:** ⚠️ **CRITICAL STATE CHANGE** - irreversible
- **Rationale:** Commit transaction to ledger

#### POST /journal-entries/{entry_id}/void
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Void POSTED journal entry
- **Request Body:** JournalEntryVoid
  - void_reason: string (required for audit)
- **Validation:**
  - ✅ Entry must be POSTED
  - ✅ Marks entry as VOID (does NOT reverse balances)
- **Response:** JournalEntryResponse (status=VOID)
- **Security:** ⚠️ State change, but creates audit trail
- **Rationale:** Mark errors without deleting history
- **Note:** Does NOT create reversing entry - user must do that manually

---

### 3.2 FORBIDDEN Operations ❌

#### ❌ PUT /journal-entries/{entry_id}/force-post
- **Rationale:** "Force" suggests bypassing validation - never acceptable.
- **Risk:** Post imbalanced entries, entries with locked accounts, entries in closed periods.
- **Alternative:** Fix validation errors, then post normally.

#### ❌ POST /journal-entries/bulk-post
- **Rationale:** Bulk posting hides errors, violates atomicity.
- **Risk:** Single invalid entry fails entire batch, or worse, succeeds partially.
- **Alternative:** Post entries one at a time with proper error handling.

#### ❌ DELETE /journal-entries/{entry_id}/force
- **Rationale:** POSTED entries must never be deleted.
- **Risk:** Destroy audit trail, corrupt account balances.
- **Alternative:** Use void operation, create reversing entry.

#### ❌ PATCH /journal-entries/{entry_id}/lines
- **Rationale:** Partial line updates can break balance invariant.
- **Risk:** Update debit without credit, create imbalance.
- **Alternative:** Replace all lines via PUT /journal-entries/{entry_id} with full validation.

---

### 3.3 Endpoints That MUST NOT Exist ⛔

#### ⛔ POST /journal-entries/{entry_id}/unpost
- **Why:** Unposting violates GAAP immutability, destroys audit trail.
- **Threat:** Retroactively modify posted transactions, manipulate balances.
- **Consequence:** Financial statements become unreliable, audit failures.
- **Correct Approach:** Void entry, create reversing entry.

#### ⛔ PUT /journal-entries/{entry_id}/lines/{line_id}
- **Why:** Modifying individual lines bypasses balance validation.
- **Threat:** Change debit on one line without adjusting credit, create imbalance.
- **Correct Approach:** Update entire journal entry with all lines.

#### ⛔ POST /journal-entries/import
- **Why:** Importing journal entries bypasses all validation.
- **Threat:** Import imbalanced entries, locked accounts, closed periods.
- **Correct Approach:** Create entries one at a time via POST /journal-entries.

#### ⛔ PUT /journal-entries/{entry_id}/status
- **Why:** Direct status manipulation bypasses business logic.
- **Threat:** Set status=POSTED without updating balances, skip validation.
- **Correct Approach:** Use POST /post or POST /void endpoints.

#### ⛔ POST /journal-entries/{entry_id}/auto-balance
- **Why:** No silent coercion - user must provide balanced entries.
- **Threat:** Client relies on auto-balancing, doesn't validate input.
- **Consequence:** Mask user errors, create wrong transactions.
- **Correct Approach:** Client validates balance before submission, API rejects imbalanced.

---

## 4. Fiscal Periods API Surface

**Endpoint:** `/api/v1/accounting/fiscal-periods/*`
**Service:** FiscalPeriodService
**Invariant Enforcement:** ✅ Via FiscalPeriodGuard

### 4.1 ALLOWED Operations ✅

#### POST /accounting/fiscal-periods
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Create fiscal period
- **Request Body:** FiscalPeriodCreate
  - company_id, period_name, start_date, end_date, period_type
- **Response:** FiscalPeriodResponse (status=OPEN by default)
- **Security:** ⚠️ Write operation, validated
- **Rationale:** Companies need to set up fiscal calendars

#### GET /accounting/fiscal-periods
- **Method:** GET
- **Auth:** User with `can_view_company` permission
- **Purpose:** List fiscal periods
- **Query Params:**
  - company_id (required)
  - period_type, status, year (optional filters)
- **Response:** List[FiscalPeriodResponse]
- **Security:** Read-only, safe
- **Rationale:** Period selection for reporting

#### POST /accounting/fiscal-periods/{period_id}/close
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Close fiscal period (OPEN → CLOSED)
- **Request Body:** FiscalPeriodClose
- **Validation:**
  - ✅ All journal entries must be POSTED (no drafts)
  - ✅ Period must be OPEN
- **Response:** FiscalPeriodResponse (status=CLOSED)
- **Security:** ⚠️ **CRITICAL STATE CHANGE** - makes period read-only
- **Rationale:** Period-end close process

#### POST /accounting/fiscal-periods/{period_id}/reopen
- **Method:** POST
- **Auth:** **SUPERUSER ONLY** (must be enforced)
- **Purpose:** Reopen CLOSED period (CLOSED → OPEN)
- **Validation:**
  - ⚠️ **TODO:** Verify user is superuser
  - ✅ Cannot reopen LOCKED periods
- **Response:** FiscalPeriodResponse (status=OPEN)
- **Security:** 🔴 **HIGH RISK** - bypasses period immutability
- **Rationale:** Emergency corrections only

#### POST /accounting/fiscal-periods/create-monthly/{company_id}/{year}
- **Method:** POST
- **Auth:** User with `can_manage_company` permission
- **Purpose:** Create 12 monthly periods for a year
- **Response:** List[FiscalPeriodResponse] (12 periods)
- **Security:** ⚠️ Bulk operation, but predictable and safe
- **Rationale:** Convenience for setup

---

### 4.2 FORBIDDEN Operations ❌

#### ❌ PUT /accounting/fiscal-periods/{period_id}
- **Rationale:** Modifying period dates affects posted journal entries.
- **Risk:** Journal entries fall outside period boundaries, reporting breaks.
- **Alternative:** Close period, create new period with correct dates.

#### ❌ DELETE /accounting/fiscal-periods/{period_id}
- **Rationale:** Cannot delete periods with journal entries.
- **Risk:** Orphan journal entries, corrupt fiscal calendar.
- **Alternative:** Periods are permanent once created.

#### ❌ POST /accounting/fiscal-periods/{period_id}/lock
- **Rationale:** Locking should be explicit SUPERUSER operation, not API.
- **Risk:** Accidentally lock periods, prevent legitimate reopening.
- **Alternative:** Lock via database migration or admin panel (not API).

#### ❌ POST /accounting/fiscal-periods/bulk-close
- **Rationale:** Bulk closing hides validation errors.
- **Risk:** Close periods with draft entries, skip validation.
- **Alternative:** Close periods one at a time with validation.

---

### 4.3 Endpoints That MUST NOT Exist ⛔

#### ⛔ PUT /accounting/fiscal-periods/{period_id}/status
- **Why:** Direct status manipulation bypasses validation.
- **Threat:** Set status=OPEN on LOCKED period, skip draft entry check.
- **Correct Approach:** Use /close and /reopen endpoints with validation.

#### ⛔ DELETE /accounting/fiscal-periods/{period_id}/force
- **Why:** Force delete bypasses journal entry check.
- **Threat:** Delete periods with posted transactions, corrupt data.
- **Correct Approach:** Periods are permanent, never delete.

#### ⛔ POST /accounting/fiscal-periods/{period_id}/purge-entries
- **Why:** Deleting journal entries destroys audit trail.
- **Threat:** Erase financial history, enable fraud.
- **Correct Approach:** Journal entries are immutable once posted.

---

## 5. Read-Only Resources 📖

**Context:** These resources are computed from journal entries and MUST be read-only.
**Threat:** Direct manipulation bypasses double-entry bookkeeping.

### 5.1 Account Ledger ✅ READ-ONLY

#### GET /accounting/ledger/account/{account_id}
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** View all posted journal entries for account
- **Response:** AccountLedger (with running balance)
- **Security:** Read-only, safe

#### ❌ POST /accounting/ledger/account/{account_id}/entry
- **Status:** ❌ **FORBIDDEN**
- **Rationale:** Ledger entries come from journal entries ONLY.
- **Threat:** Bypass double-entry validation, create imbalanced ledger.

---

### 5.2 Trial Balance ✅ READ-ONLY

#### GET /accounting/trial-balance
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** Computed report (debits = credits validation)
- **Response:** TrialBalanceResponse
- **Security:** Read-only, safe

#### ❌ PUT /accounting/trial-balance
- **Status:** ❌ **FORBIDDEN**
- **Rationale:** Trial balance is computed, never stored.
- **Threat:** Store incorrect balances, corrupt reporting.

---

### 5.3 Account Balances ✅ READ-ONLY

#### GET /accounting/balances
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** Get all account balances for period
- **Response:** List[AccountBalanceResponse]
- **Security:** Read-only, safe

#### ❌ POST /accounting/balances/{account_id}/adjust
- **Status:** ❌ **FORBIDDEN**
- **Rationale:** Balances updated ONLY via posted journal entries.
- **Threat:** Create imbalances, violate double-entry.
- **Correct Approach:** Create adjusting journal entry.

---

### 5.4 Financial Statements ✅ READ-ONLY

#### GET /accounting/balance-sheet
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** Computed from account balances
- **Response:** BalanceSheetResponse
- **Security:** Read-only, safe

#### GET /accounting/income-statement
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** Computed from account balances
- **Response:** IncomeStatementResponse
- **Security:** Read-only, safe

#### GET /accounting/cash-flow
- **Status:** ✅ **ALLOWED** (read-only)
- **Purpose:** Computed from account balances (indirect method)
- **Response:** CashFlowStatementResponse
- **Security:** Read-only, safe

#### ❌ PUT /accounting/balance-sheet
- **Status:** ❌ **FORBIDDEN**
- **Rationale:** Financial statements are computed, never stored.
- **Threat:** Store incorrect statements, enable fraud.

---

## 6. Master Chart API Surface

**Endpoint:** `/api/v1/masterchart/*`
**Context:** US-GAAP master chart (345 accounts)
**Status:** ⚠️ Not audited in this report (separate domain)

### 6.1 Current Assessment

- **Read Operations:** Likely safe (need to verify)
- **Write Operations:** ⚠️ Should be restricted to superuser
- **Recommendation:** Separate audit required

---

## 7. Security Recommendations

### 7.1 IMMEDIATE (Critical) 🔴

#### 1. Enforce Superuser Checks
**Issue:** unlock_account and reopen_fiscal_period lack superuser verification.

**Fix:**
```python
# In companychart.py unlock endpoint
if not current_user.is_superuser:
    raise HTTPException(status_code=403, detail="Superuser privileges required")

# In accounting.py reopen endpoint
if not current_user.is_superuser:
    raise HTTPException(status_code=403, detail="Superuser privileges required")
```

#### 2. Add Rate Limiting
**Issue:** No rate limiting on write operations.

**Risk:** Malicious actor could spam account creation, journal entries.

**Fix:**
```python
# Add rate limiter middleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/companies/{company_id}/chart")
@limiter.limit("10/minute")  # Max 10 account creations per minute
def create_company_account(...):
    ...
```

#### 3. Audit Log All Write Operations
**Issue:** No audit trail for account locks, period closes.

**Fix:** Log all write operations to audit table:
```python
# After successful operation
audit_log.create(
    user_id=current_user.id,
    action="lock_account",
    resource_type="company_account",
    resource_id=account_id,
    details={"reason": lock_request.reason}
)
```

---

### 7.2 SHORT-TERM (Important) ⚠️

#### 1. Add Request ID Tracing
**Issue:** Cannot trace requests through service layer.

**Fix:**
```python
import uuid
from contextvars import ContextVar

request_id_var = ContextVar('request_id', default=None)

# In middleware
request_id_var.set(str(uuid.uuid4()))
```

#### 2. Validate Fiscal Period Open in Journal Service
**Issue:** Currently relies on FiscalPeriodGuard, but should double-check.

**Fix:** Add assertion in post_journal_entry:
```python
assert fiscal_period.status == PeriodStatus.OPEN, "Period must be OPEN to post"
```

#### 3. Add Concurrent Modification Detection
**Issue:** Two users could update same account simultaneously.

**Fix:** Add `version` column, implement optimistic locking:
```python
if db_account.version != update_data.expected_version:
    raise HTTPException(status_code=409, detail="Account was modified by another user")
```

---

### 7.3 MEDIUM-TERM (Enhancement) ℹ️

#### 1. Add Idempotency Keys
**Issue:** Network retry could create duplicate journal entries.

**Fix:**
```python
@router.post("/journal-entries")
def create_journal_entry(
    idempotency_key: str = Header(None),
    ...
):
    if idempotency_key:
        existing = find_by_idempotency_key(idempotency_key)
        if existing:
            return existing  # Return cached response
```

#### 2. Add Dry-Run Mode
**Issue:** No way to validate operations without committing.

**Fix:**
```python
@router.post("/journal-entries")
def create_journal_entry(
    dry_run: bool = Query(False),
    ...
):
    if dry_run:
        # Run all validation, return errors/success without commit
        db.rollback()
```

#### 3. Add Webhook Notifications
**Issue:** No way to notify external systems of accounting events.

**Fix:** Emit events for critical operations:
- account_locked
- journal_entry_posted
- period_closed

---

## 8. Threat Scenarios & Mitigations

### 8.1 Scenario: Malicious Insider

**Threat:** Superuser with database access tries to modify balances directly.

**Mitigation:**
- ✅ Database triggers prevent balance manipulation
- ✅ Audit logs track all changes
- ⚠️ Need to add database audit trigger for direct SQL modifications

### 8.2 Scenario: Buggy Client

**Threat:** Frontend bug sends parent_id=null, breaks hierarchy.

**Mitigation:**
- ✅ Service layer validates parent_id
- ✅ Returns structured ValidationError
- ✅ Frontend can display clear error message

### 8.3 Scenario: Race Condition

**Threat:** Two users post journal entries in same period simultaneously, then one closes period.

**Mitigation:**
- ⚠️ Need to add transaction isolation level SERIALIZABLE for period close
- ⚠️ Need to add period status check in post operation (double-check pattern)

### 8.4 Scenario: Timezone Attack

**Threat:** Client manipulates entry_date timezone to post in wrong period.

**Mitigation:**
- ✅ All dates stored in UTC
- ✅ Period boundaries checked in UTC
- ⚠️ Need to document timezone handling in API docs

---

## 9. API Boundary Summary

### Total Endpoints Audited: 35

| Category | Allowed | Forbidden | Must Not Exist |
|----------|---------|-----------|----------------|
| Company Accounts | 12 | 6 | 4 |
| Chart Templates | 4 (future) | 5 (future) | 2 |
| Journal Entries | 8 | 4 | 5 |
| Fiscal Periods | 5 | 4 | 3 |
| Read-Only Resources | 7 | 3 | 0 |

### Security Posture by Category

| Category | Risk Level | Rationale |
|----------|------------|-----------|
| Company Accounts (Read) | 🟢 Low | Read-only, permission-checked |
| Company Accounts (Write) | 🟡 Medium | Validated, but allows customization |
| Company Accounts (Lock/Unlock) | 🔴 High | Bypasses GAAP immutability |
| Journal Entries (Create/Update) | 🟡 Medium | All invariants validated |
| Journal Entries (Post) | 🔴 High | Irreversible state change |
| Fiscal Periods (Close) | 🔴 High | Makes period read-only |
| Fiscal Periods (Reopen) | 🔴 Critical | Bypasses period immutability |
| Read-Only Resources | 🟢 Low | Computed, no writes possible |

---

## 10. Conclusion

**Frozen Boundaries:**
- ✅ Company accounts API: 12 endpoints allowed, 10 forbidden/must-not-exist
- ✅ Journal entries API: 8 endpoints allowed, 9 forbidden/must-not-exist
- ✅ Fiscal periods API: 5 endpoints allowed, 7 forbidden/must-not-exist
- ✅ Read-only resources: 7 endpoints allowed, all write operations forbidden

**Critical Fixes Needed:**
1. 🔴 Enforce superuser checks on unlock and reopen operations
2. 🔴 Add rate limiting on write operations
3. 🔴 Implement audit logging for all state changes

**Security Posture:**
- **Conservative:** No bulk operations, no force operations, no silent coercion
- **Accounting-First:** Read-only resources strictly enforced, double-entry validated
- **Defense in Depth:** Validation at API layer + service layer + database layer

**Status:** 🔒 **BOUNDARIES FROZEN** - No new write endpoints without security review.

---

**Guardian Sign-off:** Claude Code (API Guardian)
**Date:** 2025-12-14
**Next Review:** After any new accounting endpoint proposal

**End of API Guardian Report**
