# API Boundaries - Accounting Domain
## Security-First API Surface Definition

**Document Version:** 1.0
**Last Updated:** 2025-12-16
**Status:** FROZEN - Phase 3B Complete
**Authority:** api-guardian role

---

## Executive Summary

This document defines and freezes the API boundaries for Aequitas's accounting domain. It explicitly maps allowed operations, forbidden operations, and provides security rationale for each boundary decision.

**Core Principle:** Assume hostile or buggy clients. Every endpoint must enforce invariants at the service layer.

---

## 1. Company Chart of Accounts API

**Base Path:** `/api/v1/companies/{company_id}/chart`

### 1.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Purpose |
|----------|--------|------------|---------------|---------|
| `/companies/{company_id}/chart` | GET | None | Yes | List all accounts (flat) |
| `/companies/{company_id}/chart/tree` | GET | None | Yes | Get hierarchical tree |
| `/companies/{company_id}/chart/stats` | GET | None | Yes | Chart statistics |
| `/companies/{company_id}/chart/{code}` | GET | None | Yes | Get single account by code |
| `/companies/{company_id}/chart` | POST | Write | Yes | Create new account |
| `/companies/{company_id}/chart/{code}` | PUT | Write | Yes | Update account (restricted if locked) |
| `/companies/{company_id}/chart/{code}` | DELETE | Write | Yes | Soft-delete account (validation enforced) |
| `/companies/{company_id}/chart/{account_id}/can-delete` | GET | None | Yes | Pre-deletion validation |
| `/companies/{company_id}/chart/reset` | POST | Write | Yes | Reset to master chart |
| `/companies/{company_id}/chart/initialize` | POST | Write | Yes | Initialize from master chart |

**Security Invariants:**
1. All operations require authenticated user with company access
2. Company ID in path MUST match company_id in request body (where applicable)
3. Account codes must be unique within company
4. Account hierarchy must remain valid (no orphaned accounts)
5. UUID-based relationships are mandatory for all foreign keys

### 1.2 RESTRICTED Operations (Locked Accounts)

When an account is **locked** (via FirstTransaction, PeriodClose, or Manual lock):

**IMMUTABLE FIELDS (Cannot be changed):**
- `name` - Account name
- `type` - Header (H) or Detail (D)
- `code` - Account code
- `account_type` - Asset, Liability, Equity, Revenue, Expense
- `normal_balance` - Debit or Credit
- `parent_id` - Hierarchical parent reference
- `mapped_master_account_id` - Master chart mapping

**MUTABLE FIELDS (Can still be changed):**
- `description` - Account description
- `currency` - Currency code
- `json_data` - Arbitrary JSON metadata

**Enforcement:** `CompanyChartService.update_account()` validates lock status before allowing changes.

### 1.3 DELETION RESTRICTIONS

**Accounts CANNOT be deleted if:**
1. Account has children (must remove or reparent first)
2. Account is locked (must unlock first - requires superuser)
3. Account is template-mandatory (flagged as required by template)
4. Account has posted transactions (GAAP compliance - immutable)

**Enforcement:** `CompanyChartService.delete_account()` performs all validation checks.

**Pre-deletion validation:** Use `GET /companies/{company_id}/chart/{account_id}/can-delete` to check before attempting deletion.

---

## 2. Account Locking API

**Base Path:** `/api/v1/companies/{company_id}/chart/{account_id}`

### 2.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Superuser Required | Purpose |
|----------|--------|------------|---------------|--------------------|---------|
| `/{account_id}/lock` | POST | Write | Yes | No | Lock an account |
| `/{account_id}/unlock` | POST | Critical | Yes | **YES** | Unlock an account |

### 2.2 Locking Reasons (LockedReason enum)

**Automatic Locks:**
1. **FirstTransaction** - Automatically locked after first posted transaction
   - Triggered by: Journal entry posting
   - Purpose: Prevent structural changes after accounting activity

2. **PeriodClose** - Locked during fiscal period close
   - Triggered by: Fiscal period close operation
   - Purpose: Freeze accounts for period-end reporting

**Manual Locks:**
3. **Manual** - Manually locked by superuser
   - Requires: `user_id` parameter for audit trail
   - Purpose: Administrative control, compliance requirements

### 2.3 Unlock Security Requirements

**CRITICAL SECURITY BOUNDARY:**

Unlocking an account requires:
1. **Superuser privileges** (enforced via `check_superuser()`)
2. **Authenticated user** (for audit trail - `current_user.id`)
3. **No posted transactions in current fiscal period**
4. **Unlock reason** (for audit log)

**Rationale:**
- Unlocking allows retroactive structural changes to accounting data
- Could violate GAAP if not carefully controlled
- Must be auditable and traceable
- Only superusers understand accounting implications

**Enforcement:** `CompanyChartService.unlock_account()` checks transaction history before unlocking.

### 2.4 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Bulk unlock endpoints
- ❌ Unlock without superuser privileges
- ❌ Unlock without audit trail (anonymous unlock)
- ❌ Force unlock (bypassing transaction validation)
- ❌ Unlock without reason

**Why:** Each unlock is a significant accounting event requiring individual review and justification.

---

## 3. Chart Templates API

**Base Path:** `/api/v1/templates`

### 3.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Purpose |
|----------|--------|------------|---------------|---------|
| `/templates` | GET | None | Yes | List available templates |
| `/templates/{template_name}` | GET | None | Yes | Preview template structure |
| `/templates/apply/{template_name}` | POST | Write | Yes | Apply template to master chart |
| `/templates/validate` | POST | None | Yes | Validate custom template file |
| `/templates/custom` | POST | Write | Yes | Upload custom template |

**Security Invariants:**
1. Templates only apply to **master chart** (not company charts directly)
2. Template validation must pass before upload
3. Template names must be unique
4. Templates cannot contain malicious code or SQL injection

### 3.2 Template Application Flow

**Safe Application Process:**
1. Template loaded from disk or database
2. Validation performed (structure, required fields, data types)
3. Missing accounts created in master chart
4. Hierarchy rebuilt to ensure consistency
5. Operation report returned (accounts created, errors encountered)

**Company Impact:**
- Templates do NOT directly modify company charts
- Companies can initialize/reset from master chart after template application
- This two-step process prevents accidental data loss

### 3.3 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Direct template application to company charts (bypasses validation)
- ❌ Template deletion (templates are append-only)
- ❌ Template modification after creation (immutable)
- ❌ Unvalidated template upload

**Why:** Templates are foundational data structures. Changes must be deliberate and validated.

---

## 4. Journal Entries API (Read-Only for Phase 3B)

**Base Path:** `/api/v1/journal-entries`

### 4.1 ALLOWED Operations (Read Path)

| Endpoint | Method | Rate Limit | Auth Required | Purpose |
|----------|--------|------------|---------------|---------|
| `/journal-entries/` | GET | None | Yes | List entries (with filters) |
| `/journal-entries/{entry_id}` | GET | None | Yes | Get single entry |

**Query Filters:**
- `company_id` (required)
- `fiscal_period_id` (optional)
- `status` (optional: draft, posted, void)
- `start_date` / `end_date` (optional)
- `page` / `page_size` (pagination)

**Security Invariants:**
1. User must have `can_view_company` permission
2. Entries filtered by company access
3. Cross-company queries forbidden

### 4.2 WRITE Operations (Allowed but Heavily Validated)

| Endpoint | Method | Rate Limit | Auth Required | Purpose | Validation Required |
|----------|--------|------------|---------------|---------|---------------------|
| `/journal-entries/` | POST | Write | Yes | Create entry | ✓ Double-entry, period open |
| `/journal-entries/{entry_id}` | PUT | Write | Yes | Update entry | ✓ Draft only |
| `/journal-entries/{entry_id}/post` | POST | Write | Yes | Post entry | ✓ GAAP validation |
| `/journal-entries/{entry_id}/void` | POST | Write | Yes | Void entry | ✓ Posted only |
| `/journal-entries/{entry_id}` | DELETE | Write | Yes | Delete entry | ✓ Draft only |

**Double-Entry Validation (Mandatory):**
1. Minimum 2 lines required
2. Debits MUST equal credits (exact decimal precision)
3. All accounts must belong to company
4. Fiscal period must be open
5. Entry date must be within fiscal period
6. Account types must have valid normal balances

**State Transitions:**
```
DRAFT → [post] → POSTED → [void] → VOID
  ↓
[delete] (only drafts)
```

**Enforcement:** `JournalEntryService.create_journal_entry()` and `JournalEntryService.post_journal_entry()` enforce all validation rules.

### 4.3 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Edit posted entries (immutable after posting)
- ❌ Delete posted entries (must void instead)
- ❌ Create entries with unbalanced debits/credits
- ❌ Create entries in closed/locked fiscal periods
- ❌ Bypass double-entry validation
- ❌ Create entries with non-existent accounts
- ❌ Create entries with locked accounts (unless lock allows transactions)
- ❌ Void draft entries (only posted can be voided)
- ❌ Reverse void operation (voids are permanent)

**Why:** Journal entries are the foundation of accounting integrity. Once posted, they represent historical truth and cannot be altered.

---

## 5. Accounting Reports API (Read-Only)

**Base Path:** `/api/v1/accounting`

### 5.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Purpose |
|----------|--------|------------|---------------|---------|
| `/accounting/ledger/account/{account_id}` | GET | None | Yes | Account ledger with running balance |
| `/accounting/trial-balance` | GET | None | Yes | Trial balance report |
| `/accounting/balances` | GET | None | Yes | All account balances for period |
| `/accounting/balance-sheet` | GET | None | Yes | Balance sheet (as of date) |
| `/accounting/income-statement` | GET | None | Yes | Income statement (date range) |
| `/accounting/cash-flow` | GET | None | Yes | Cash flow statement (indirect method) |

**Security Invariants:**
1. All reports require `can_view_company` permission
2. Reports are read-only (no mutations)
3. Reports reflect **posted transactions only** (drafts excluded)
4. Date ranges must be validated (start ≤ end)

### 5.2 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Modify reported balances directly (must create journal entries)
- ❌ Adjust trial balance totals (must be computed from transactions)
- ❌ Edit financial statements (reports are calculated, not stored)
- ❌ Bypass permission checks
- ❌ Cross-company aggregate reports (unless group feature enabled)

**Why:** Financial reports are derived data, not source data. All changes must flow through journal entries.

---

## 6. Fiscal Periods API

**Base Path:** `/api/v1/accounting/fiscal-periods`

### 6.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Superuser Required | Purpose |
|----------|--------|------------|---------------|--------------------|---------|
| `/fiscal-periods` | POST | Write | Yes | No | Create fiscal period |
| `/fiscal-periods` | GET | None | Yes | No | List periods (with filters) |
| `/fiscal-periods/{period_id}/close` | POST | Critical | Yes | No | Close period |
| `/fiscal-periods/{period_id}/reopen` | POST | Critical | Yes | **YES** | Reopen closed period |
| `/fiscal-periods/create-monthly/{company_id}/{year}` | POST | Write | Yes | No | Create 12 monthly periods |

**Period Types:**
- `month` - Monthly periods
- `quarter` - Quarterly periods
- `year` - Annual periods

**Period Status State Machine:**
```
OPEN → [close] → CLOSED → [lock] → LOCKED
              ↑ [reopen - superuser only]
```

### 6.2 Close Period Validation

**Requirements to close a period:**
1. All journal entries must be posted (no drafts)
2. Period must currently be OPEN
3. User must have `can_manage_company` permission

**Side Effects:**
1. Period status → CLOSED
2. Accounts may be locked (PeriodClose reason)
3. `closed_at` timestamp recorded
4. `closed_by` user ID recorded

### 6.3 Reopen Period Security

**CRITICAL SECURITY BOUNDARY:**

Reopening a closed period requires:
1. **Superuser privileges** (enforced via `check_superuser()`)
2. Period must be CLOSED (not LOCKED)
3. User must have `can_manage_company` permission

**LOCKED periods CANNOT be reopened** (immutable for regulatory compliance)

**Rationale:**
- Reopening a period allows retroactive changes to financial records
- Could violate regulatory requirements (SOX, GAAP)
- Only superusers understand accounting and legal implications
- Audit trail records who reopened and when

### 6.4 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Create overlapping periods (dates must not overlap)
- ❌ Close period with draft journal entries
- ❌ Reopen locked periods (regulatory immutability)
- ❌ Reopen without superuser privileges
- ❌ Delete fiscal periods (soft delete only, audit trail required)
- ❌ Create entries in closed/locked periods
- ❌ Bypass period validation

**Why:** Fiscal periods define accounting boundaries. Their integrity is essential for GAAP compliance and audit trails.

---

## 7. Account Mappings API

**Base Path:** `/api/v1/mappings`

### 7.1 ALLOWED Operations

| Endpoint | Method | Rate Limit | Auth Required | Purpose |
|----------|--------|------------|---------------|---------|
| `/mappings` | GET | None | Yes | Get company mappings (with filters) |
| `/mappings/{mapping_id}` | GET | None | Yes | Get single mapping |
| `/mappings` | POST | Write | Yes | Create mapping manually |
| `/mappings/{mapping_id}` | DELETE | Write | Yes | Delete mapping |
| `/mappings/suggest` | POST | None | Yes | AI-powered single suggestion |
| `/mappings/suggest-all` | POST | None | Yes | Bulk AI suggestions for company |
| `/mappings/{mapping_id}/confirm` | POST | Write | Yes | Confirm suggested mapping |
| `/mappings/{mapping_id}/reject` | POST | Write | Yes | Reject suggested mapping |
| `/mappings/{mapping_id}/review` | POST | Write | Yes | Flag for manual review |
| `/mappings/confirm-high-confidence` | POST | Write | Yes | Bulk confirm high-confidence mappings |
| `/mappings/stats/{company_id}` | GET | None | Yes | Mapping statistics |
| `/mappings/semantic-search/{company_account_id}` | GET | None | Yes | pgvector semantic similarity |
| `/mappings/suggest-blended` | POST | None | Yes | AI + semantic hybrid suggestions |
| `/mappings/propagate` | POST | Write | Yes | Propagate mappings to group companies |

**Mapping Status Workflow:**
```
suggested → [confirm] → confirmed
         ↓ [reject]  → rejected
         ↓ [review]  → manual_review
```

**Security Invariants:**
1. Mappings link company accounts to master chart accounts
2. `company_account_id` must reference valid company account (UUID)
3. `master_code` must reference valid master account
4. Confidence scores must be 0.0 ≤ confidence ≤ 1.0
5. Status must be valid enum value

### 7.2 AI Suggestion Security

**Suggestion Methods:**
1. **AI-based** - Uses Ollama/Cloudflare Workers AI for classification
2. **Semantic** - Uses pgvector embeddings for similarity search
3. **Blended** - Weighted combination of AI + semantic

**Safety Controls:**
1. AI suggestions create `status: suggested` (not auto-confirmed)
2. High-confidence auto-confirm requires explicit user action
3. Confidence threshold configurable (default 0.85)
4. Audit trail tracks suggestion method and confidence

### 7.3 Group Propagation Security

**Propagation Workflow:**
1. Source company mappings (confirmed only by default)
2. Find matching accounts in target companies (by account code)
3. Create `status: suggested` mappings in targets
4. Track propagation source in metadata

**Safety Controls:**
1. Does NOT auto-confirm in target companies
2. Only propagates confirmed mappings (unless `only_confirmed=false`)
3. Skips existing mappings (no overwrites)
4. Returns statistics for review

### 7.4 FORBIDDEN Operations

**NOT ALLOWED:**
- ❌ Create mappings with non-existent accounts
- ❌ Create duplicate mappings (one company account → one master account)
- ❌ Modify confirmed mappings (must delete and recreate)
- ❌ Bypass confidence validation (0.0-1.0 range)
- ❌ Auto-confirm without explicit user action
- ❌ Propagate to companies user doesn't have access to

**Why:** Mappings affect financial reporting classification. All changes must be deliberate and validated.

---

## 8. Endpoints That MUST NOT Exist

The following endpoints are explicitly **FORBIDDEN** and must not be implemented:

### 8.1 Dangerous Write Operations

❌ **Bulk Account Deletion**
- `DELETE /companies/{company_id}/chart` (delete all accounts)
- **Why:** Could destroy entire chart of accounts, no undo

❌ **Direct Balance Manipulation**
- `POST /accounting/balances/{account_id}/adjust`
- `PUT /accounting/trial-balance/override`
- **Why:** Balances must be derived from journal entries (GAAP)

❌ **Posted Entry Modification**
- `PUT /journal-entries/{entry_id}` (if status=posted)
- `PATCH /journal-entries/{entry_id}/lines/{line_id}` (if posted)
- **Why:** Posted entries are immutable (accounting integrity)

❌ **Fiscal Period Deletion**
- `DELETE /fiscal-periods/{period_id}` (hard delete)
- **Why:** Fiscal periods are part of audit trail (must retain)

❌ **Unlock Without Superuser**
- `POST /chart/{account_id}/unlock` (without superuser check)
- **Why:** Security boundary violation

❌ **Force Operations (Bypass Validation)**
- `POST /journal-entries?force=true`
- `DELETE /chart/{code}?force=true`
- **Why:** Validation exists for GAAP compliance, cannot bypass

### 8.2 Dangerous Read Operations

❌ **Cross-Company Aggregation (Without Group Context)**
- `GET /accounting/trial-balance/all-companies`
- **Why:** Permission boundary violation, data leakage risk

❌ **Unauthenticated Endpoints**
- `GET /public/journal-entries`
- **Why:** Financial data is always sensitive

❌ **Raw SQL Execution**
- `POST /admin/execute-sql`
- **Why:** SQL injection risk, audit trail bypass

### 8.3 Dangerous AI Operations

❌ **Auto-Apply AI Suggestions Without Review**
- `POST /mappings/ai-auto-map?confirm=true`
- **Why:** AI can be wrong, human review required

❌ **Bulk Journal Entry Generation**
- `POST /journal-entries/generate-from-ai`
- **Why:** Journal entries must be deliberately created and reviewed

---

## 9. Rate Limiting Strategy

Rate limits are applied using decorators:

**None (Read Operations):**
- Chart reads, report generation, mapping queries
- **Why:** Read operations don't risk data corruption

**Write (Standard Write Operations):**
- Account creation, mapping creation, journal entry drafts
- **Limit:** Reasonable write rate (configured per environment)
- **Why:** Prevents accidental bulk operations

**Critical (High-Risk Operations):**
- Account unlock, fiscal period close/reopen, entry posting
- **Limit:** Very restrictive (e.g., 10/minute)
- **Why:** These operations have significant accounting implications

**Enforcement:** `@Depends(rate_limit_write())` and `@Depends(rate_limit_critical())`

---

## 10. Permission Model

### 10.1 Permission Levels

**View Access:** `can_view_company(user_id, company_id)`
- Read journal entries, reports, charts, balances
- No mutations allowed

**Manage Access:** `can_manage_company(user_id, company_id)`
- Create/update/delete accounts, journal entries, mappings
- Close fiscal periods
- Inherits view access

**Superuser Access:** `check_superuser(current_user)`
- Unlock accounts
- Reopen fiscal periods
- System-wide operations
- Inherits all lower permissions

### 10.2 Enforcement

**Every endpoint must:**
1. Require `current_user: User = Depends(get_current_user)` (authentication)
2. Call `PermissionService.can_view_company()` or `can_manage_company()` (authorization)
3. Call `check_superuser()` for privileged operations
4. Validate company_id matches user's accessible companies

**Service Layer Responsibility:**
- Permission checks happen at **API layer**
- Service layer assumes authorization already verified
- Service layer focuses on business logic and GAAP validation

---

## 11. Data Integrity Guarantees

### 11.1 Referential Integrity

**All relationships use UUIDs:**
- `company_id` → Company table
- `company_account_id` → CompanyAccount table
- `master_account_id` → MasterAccount table
- `fiscal_period_id` → FiscalPeriod table
- `user_id` → User table

**Foreign key constraints enforced at database level:**
- CASCADE deletes where appropriate
- RESTRICT deletes where historical data must be preserved

### 11.2 Double-Entry Validation

**Every journal entry:**
1. Debits = Credits (exact decimal precision, no floating point)
2. Minimum 2 lines
3. All accounts belong to same company
4. Entry date within fiscal period bounds
5. Fiscal period is OPEN

**Enforcement:** `JournalEntryService.create_journal_entry()` validates before persisting.

### 11.3 Account Hierarchy Integrity

**Rules:**
1. No orphaned accounts (parent_id must reference valid account or be NULL)
2. No circular references (parent cannot be descendant)
3. Header accounts (type=H) cannot have transactions
4. Detail accounts (type=D) hold actual balances

**Enforcement:** `CompanyChartService` validates hierarchy on create/update.

---

## 12. Audit Trail Requirements

**Every mutating operation must record:**
1. **Who** - user_id of authenticated user
2. **When** - timestamp (created_at, updated_at)
3. **What** - operation type (create, update, delete, lock, unlock, close, reopen)
4. **Why** - reason field where applicable (unlock_reason, void_reason)

**Critical Operations Requiring Audit:**
- Account unlock
- Fiscal period close/reopen
- Journal entry post/void
- Account deletion

**Enforcement:** Database models include `created_by`, `updated_by`, `created_at`, `updated_at` fields.

---

## 13. Error Handling Standards

### 13.1 HTTP Status Codes

**200 OK** - Successful GET request
**201 Created** - Successful POST (resource created)
**204 No Content** - Successful DELETE
**400 Bad Request** - Validation error, business rule violation
**403 Forbidden** - Permission denied
**404 Not Found** - Resource not found
**429 Too Many Requests** - Rate limit exceeded
**500 Internal Server Error** - Unexpected error (should be rare)

### 13.2 Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

**For validation errors:**
```json
{
  "detail": "Debits (1000.00) do not equal credits (950.00)"
}
```

**For permission errors:**
```json
{
  "detail": "No permission to unlock accounts (requires superuser)"
}
```

---

## 14. Versioning and Deprecation Policy

**Current Version:** `/api/v1`

**Deprecation Process:**
1. New endpoint introduced in next version (e.g., `/api/v2`)
2. Old endpoint marked deprecated (warning in response headers)
3. Grace period announced (minimum 6 months)
4. Old endpoint removed after grace period

**No Breaking Changes in v1:**
- Existing endpoints will not change behavior
- New optional parameters may be added
- New endpoints may be added
- Response fields may be added (clients must ignore unknown fields)

---

## 15. Security Checklist for New Endpoints

Before adding any new accounting API endpoint, verify:

- [ ] Authentication required (`Depends(get_current_user)`)
- [ ] Authorization checked (`can_view_company` or `can_manage_company`)
- [ ] Superuser check if privileged operation (`check_superuser`)
- [ ] Rate limiting applied (write or critical)
- [ ] Input validation (Pydantic schemas)
- [ ] UUID-based relationships only
- [ ] GAAP compliance validated
- [ ] Double-entry rules enforced (if journal entry related)
- [ ] Fiscal period status checked (if transaction related)
- [ ] Account lock status checked (if account mutation)
- [ ] Audit trail recorded (who, when, what, why)
- [ ] Error messages safe (no PII or sensitive data leakage)
- [ ] Permission boundaries enforced
- [ ] No SQL injection vectors
- [ ] No mass assignment vulnerabilities

---

## 16. Conclusion

This document defines the **frozen API boundaries** for Aequitas accounting domain as of Phase 3B completion.

**Key Principles:**
1. **Security first** - Assume hostile clients
2. **GAAP compliance** - Accounting rules are non-negotiable
3. **Audit trail** - Every mutation must be traceable
4. **Immutability** - Posted transactions and locked accounts cannot be changed
5. **Permission boundaries** - Superuser privileges required for dangerous operations
6. **No shortcuts** - Validation cannot be bypassed

**Enforcement:**
- Service layer validates all business rules
- Database constraints enforce referential integrity
- API layer enforces authentication and authorization
- Rate limiting prevents abuse

**Change Control:**
Any additions or modifications to these API boundaries require:
1. Accounting-first justification
2. Security review
3. Documentation update
4. Team approval

---

**Document Authority:** api-guardian role
**Next Review:** Upon Phase 4 planning (if accounting domain expansion required)
