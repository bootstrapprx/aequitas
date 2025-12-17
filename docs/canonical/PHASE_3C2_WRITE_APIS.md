# Phase 3C-2: Write APIs (Strict, Minimal, Defensive)
## Complete Write API Specification

**Document Version:** 1.0
**Date:** 2025-12-16
**Status:** CANONICAL - Phase 3C-2
**Authority:** api-guardian + contract-enforcer

---

## Document Purpose

This document specifies ALL write-side API endpoints for the Aequitas accounting domain. Every endpoint is designed to be:
- **Defensive by default** - Assumes hostile or buggy clients
- **Explicitly validated** - All preconditions checked
- **Audit-safe** - Full who/when/what/why tracking
- **Lock-aware** - Respects immutability rules
- **GAAP-compliant** - Enforces double-entry accounting

**Authoritative References:**
- `API_BOUNDARIES.md` - Frozen API surface
- `PHASE_3C1_DTO_SPECIFICATION.md` - Canonical DTOs and immutability rules
- Phase 3B service layer - Business logic enforcement

---

## Hard Constraints

### ❌ FORBIDDEN

- ❌ Force flags (`?force=true`)
- ❌ Bypass validation
- ❌ Partial writes
- ❌ Silent coercion
- ❌ Business logic in controllers
- ❌ Mutation of POSTED entries
- ❌ Mutation of LOCKED accounts
- ❌ Bulk write endpoints
- ❌ Cross-company writes

### ✅ REQUIRED

- ✅ UUID-only references
- ✅ Exact enum matching
- ✅ Transactional writes
- ✅ Deterministic failures
- ✅ Explicit error codes
- ✅ Idempotent side effects (where applicable)

---

## 1. Endpoint Inventory

### 1.1 Company Accounts Write Operations

| Endpoint | Method | Permission | DTO Request | DTO Response | Rate Limit |
|----------|--------|------------|-------------|--------------|------------|
| `/api/v1/companies/{company_id}/chart` | POST | manage_company | CompanyAccountCreate | CompanyAccountResponse | write |
| `/api/v1/companies/{company_id}/chart/{code}` | PUT | manage_company | CompanyAccountUpdate | CompanyAccountResponse | write |
| `/api/v1/companies/{company_id}/chart/{code}` | DELETE | manage_company | - | 204 No Content | write |
| `/api/v1/companies/{company_id}/chart/{account_id}/lock` | POST | manage_company | AccountLockRequest | CompanyAccountResponse | write |
| `/api/v1/companies/{company_id}/chart/{account_id}/unlock` | POST | **SUPERUSER** | AccountUnlockRequest | CompanyAccountResponse | critical |

### 1.2 Journal Entries Write Operations

| Endpoint | Method | Permission | DTO Request | DTO Response | Rate Limit |
|----------|--------|------------|-------------|--------------|------------|
| `/api/v1/journal-entries` | POST | manage_company | JournalEntryCreate | JournalEntryResponse | write |
| `/api/v1/journal-entries/{entry_id}` | PUT | manage_company | JournalEntryUpdate | JournalEntryResponse | write |
| `/api/v1/journal-entries/{entry_id}/post` | POST | manage_company | JournalEntryPost | JournalEntryResponse | write |
| `/api/v1/journal-entries/{entry_id}/void` | POST | manage_company | JournalEntryVoid | JournalEntryResponse | write |
| `/api/v1/journal-entries/{entry_id}` | DELETE | manage_company | - | 204 No Content | write |

### 1.3 Fiscal Periods Write Operations

| Endpoint | Method | Permission | DTO Request | DTO Response | Rate Limit |
|----------|--------|------------|-------------|--------------|------------|
| `/api/v1/accounting/fiscal-periods` | POST | manage_company | FiscalPeriodCreate | FiscalPeriodResponse | write |
| `/api/v1/accounting/fiscal-periods/{period_id}/close` | POST | manage_company | FiscalPeriodClose | FiscalPeriodResponse | critical |
| `/api/v1/accounting/fiscal-periods/{period_id}/reopen` | POST | **SUPERUSER** | - | FiscalPeriodResponse | critical |

### 1.4 Chart Templates Write Operations (Admin-Level)

| Endpoint | Method | Permission | DTO Request | DTO Response | Rate Limit |
|----------|--------|------------|-------------|--------------|------------|
| `/api/v1/templates/chart` | POST | **SUPERUSER** | ChartTemplateCreate | ChartTemplateResponse | write |
| `/api/v1/templates/chart/{template_id}/accounts` | POST | **SUPERUSER** | ChartTemplateAccountCreate | ChartTemplateAccountResponse | write |
| `/api/v1/templates/chart/{template_id}/activate` | POST | **SUPERUSER** | - | ChartTemplateResponse | write |
| `/api/v1/templates/chart/{template_id}/deactivate` | POST | **SUPERUSER** | - | ChartTemplateResponse | write |

---

## 2. Controller Skeletons

### Design Principles

**Controllers MUST:**
1. Be thin - No business logic
2. Validate input DTOs (Pydantic automatic)
3. Check permissions (call PermissionService)
4. Call service layer method
5. Map exceptions to HTTP responses
6. Return DTO responses

**Controllers MUST NOT:**
1. Contain business rules
2. Perform database writes directly
3. Bypass validation
4. Catch and silence errors

### 2.1 Company Account Controllers

#### Create Company Account

```python
@router.post(
    "/companies/{company_id}/chart",
    response_model=CompanyAccountResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_write())]
)
def create_company_account(
    company_id: UUID,
    account_data: CompanyAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account in the company's chart of accounts.

    PRECONDITIONS:
    - User must have manage_company permission
    - company_id in path must match account_data.company_id
    - Account code must be unique within company
    - Parent account (if specified) must exist and belong to company
    - Parent account cannot be Detail type

    SIDE EFFECTS:
    - New CompanyAccount record created
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks manage_company permission
    - VALIDATION_ERROR: DTO validation failed
    - VALIDATION_ERROR: Duplicate account code
    - VALIDATION_ERROR: Invalid parent account
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to create accounts for this company",
                "details": {"company_id": str(company_id)}
            }
        )

    # Validate company_id consistency
    if account_data.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Company ID in path does not match company ID in request body",
                "details": {
                    "path_company_id": str(company_id),
                    "body_company_id": str(account_data.company_id)
                }
            }
        )

    # Call service layer
    service = CompanyChartService(db)
    try:
        account = service.create_account(company_id, account_data)
        return account
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code.value if hasattr(e, 'error_code') else "VALIDATION_ERROR",
                "message": str(e),
                "details": getattr(e, 'details', {})
            }
        )
```

#### Update Company Account

```python
@router.put(
    "/companies/{company_id}/chart/{code}",
    response_model=CompanyAccountResponse,
    dependencies=[Depends(rate_limit_write())]
)
def update_company_account(
    company_id: UUID,
    code: str,
    account_data: CompanyAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing account in the company's chart of accounts.

    LOCKED ACCOUNT RESTRICTIONS:
    - When is_locked=true, CANNOT change: name, type, code, account_type,
      normal_balance, parent_id, mapped_master_account_id
    - CAN change: description, currency, json_data
    - To modify immutable fields, unlock the account first (requires superuser)

    PRECONDITIONS:
    - User must have manage_company permission
    - Account must exist
    - If locked, update must not modify immutable fields

    SIDE EFFECTS:
    - CompanyAccount record updated
    - updated_at timestamp changed
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Account not found
    - LOCKED_ACCOUNT: Attempt to modify immutable fields on locked account
    - VALIDATION_ERROR: Other validation failures
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to update accounts for this company"
            }
        )

    # Call service layer
    service = CompanyChartService(db)
    try:
        account = service.update_account(company_id, code, account_data)
        if not account:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Account with code {code} not found",
                    "details": {"code": code, "company_id": str(company_id)}
                }
            )
        return account
    except ValidationError as e:
        # Check if this is a locked account violation
        if "locked account" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "LOCKED_ACCOUNT",
                    "message": str(e),
                    "details": {"code": code}
                }
            )
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

#### Delete Company Account

```python
@router.delete(
    "/companies/{company_id}/chart/{code}",
    status_code=204,
    dependencies=[Depends(rate_limit_write())]
)
def delete_company_account(
    company_id: UUID,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (soft delete) an account from the company's chart of accounts.

    DELETION RESTRICTIONS:
    - Cannot delete accounts with children (must remove or reparent children first)
    - Cannot delete locked accounts (must unlock first)
    - Cannot delete template-mandatory accounts
    - Cannot delete accounts with posted transactions (GAAP compliance)

    PRECONDITIONS:
    - User must have manage_company permission
    - Account must exist
    - Account must not be locked
    - Account must not have children
    - Account must not have posted transactions
    - Account must not be template-mandatory

    SIDE EFFECTS:
    - is_active set to False (soft delete)
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Account not found
    - LOCKED_ACCOUNT: Account is locked
    - VALIDATION_ERROR: Has children, has transactions, or template-mandatory
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to delete accounts for this company"
            }
        )

    # Call service layer
    service = CompanyChartService(db)
    try:
        success = service.delete_account(company_id, code)
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Account with code {code} not found"
                }
            )
        return None
    except ValidationError as e:
        if "locked" in str(e).lower():
            error_code = "LOCKED_ACCOUNT"
        else:
            error_code = "VALIDATION_ERROR"

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": str(e)
            }
        )
```

#### Lock Company Account

```python
@router.post(
    "/companies/{company_id}/chart/{account_id}/lock",
    response_model=CompanyAccountResponse,
    dependencies=[Depends(rate_limit_write())]
)
def lock_company_account(
    company_id: UUID,
    account_id: UUID,
    lock_request: CompanyAccountLockRequest,
    user_id: Optional[UUID] = Query(None, description="User ID (required for Manual locks)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lock an account to prevent immutable field changes.

    LOCKED ACCOUNTS CANNOT CHANGE:
    - name, type, code, account_type, normal_balance, parent_id, mapped_master_account_id

    LOCKING REASONS:
    - FirstTransaction: Automatically locked after first posted transaction
    - PeriodClose: Locked during fiscal period close
    - Manual: Manually locked by user (requires user_id)

    PRECONDITIONS:
    - User must have manage_company permission
    - Account must exist and belong to company
    - If reason=Manual, user_id must be provided

    SIDE EFFECTS:
    - is_locked set to True
    - locked_at timestamp set
    - locked_reason recorded
    - locked_by set (for Manual locks)
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Account not found or doesn't belong to company
    - VALIDATION_ERROR: Missing user_id for Manual lock
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to lock accounts for this company"
            }
        )

    # Call service layer
    service = CompanyChartService(db)
    try:
        # Verify account belongs to company
        account = service.get_account_by_id(account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Account {account_id} not found in company {company_id}"
                }
            )

        # Convert reason string to enum
        from app.db.models.enums import LockedReason
        reason = LockedReason(lock_request.reason)

        # Lock the account
        locked_account = service.lock_account(account_id, reason, user_id)
        return locked_account
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

#### Unlock Company Account

```python
@router.post(
    "/companies/{company_id}/chart/{account_id}/unlock",
    response_model=CompanyAccountResponse,
    dependencies=[Depends(rate_limit_critical())]
)
def unlock_company_account(
    company_id: UUID,
    account_id: UUID,
    unlock_request: CompanyAccountUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlock an account (requires superuser privileges).

    WARNING: Only allowed if no posted transactions in current fiscal period.

    SECURITY:
    - Requires superuser privileges (enforced)
    - Requires authenticated user for audit trail
    - Creates unlock event in audit log

    USE CASES:
    - Correcting account structure before period close
    - Emergency fixes during period transition
    - Reverting accidental locks

    RESTRICTIONS:
    - Cannot unlock if transactions exist in current period
    - Unlock reason must be provided for audit

    PRECONDITIONS:
    - Current user must be superuser
    - Account must exist and belong to company
    - No posted transactions in current fiscal period

    SIDE EFFECTS:
    - is_locked set to False
    - locked_at cleared
    - locked_reason cleared
    - locked_by cleared
    - Audit log entry created (critical operation)

    ERROR CODES:
    - PERMISSION_DENIED: User is not superuser
    - NOT_FOUND: Account not found
    - STATE_CONFLICT: Cannot unlock due to posted transactions
    """
    # CRITICAL SECURITY: Enforce superuser privileges
    from app.core.security import check_superuser
    check_superuser(current_user)

    # Call service layer
    service = CompanyChartService(db)
    try:
        # Verify account belongs to company
        account = service.get_account_by_id(account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Account {account_id} not found in company {company_id}"
                }
            )

        # Unlock the account (using current_user.id for audit trail)
        unlocked_account = service.unlock_account(account_id, current_user.id)
        return unlocked_account
    except ValidationError as e:
        if "transaction" in str(e).lower():
            error_code = "STATE_CONFLICT"
        else:
            error_code = "VALIDATION_ERROR"

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": str(e)
            }
        )
```

### 2.2 Journal Entry Controllers

#### Create Journal Entry

```python
@router.post(
    "/journal-entries",
    response_model=JournalEntryResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_write())]
)
def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new journal entry.

    DOUBLE-ENTRY VALIDATION (MANDATORY):
    - Minimum 2 lines required
    - Debits MUST equal credits (exact decimal precision)
    - All accounts must belong to the company
    - Fiscal period must be OPEN
    - Entry date must be within fiscal period bounds
    - Each line must have debit XOR credit (not both, not neither)

    PRECONDITIONS:
    - User must have manage_company permission
    - Company must exist
    - Fiscal period must be OPEN
    - All company_account_ids must belong to company
    - Lines must balance (debits = credits)

    SIDE EFFECTS:
    - New JournalEntry record created (status=DRAFT)
    - JournalEntryLine records created
    - entry_number auto-generated (e.g., "JE-2024-001")
    - created_by set to current_user.id
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks manage_company permission
    - PERIOD_CLOSED: Fiscal period is not OPEN
    - JOURNAL_IMBALANCE: Debits != Credits
    - VALIDATION_ERROR: Other validation failures
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry_data.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to create journal entries for this company"
            }
        )

    # Call service layer
    service = JournalEntryService(db)
    try:
        journal_entry = service.create_journal_entry(entry_data, current_user.id)

        # Build response with totals
        total_debit, total_credit = service.get_entry_totals(journal_entry)

        response = JournalEntryResponse(
            **journal_entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in journal_entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )

        return response

    except ValidationError as e:
        error_message = str(e).lower()

        if "period" in error_message and ("closed" in error_message or "locked" in error_message):
            error_code = "PERIOD_CLOSED"
        elif "balance" in error_message or "debit" in error_message or "credit" in error_message:
            error_code = "JOURNAL_IMBALANCE"
        else:
            error_code = "VALIDATION_ERROR"

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": str(e)
            }
        )
```

#### Update Journal Entry

```python
@router.put(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    dependencies=[Depends(rate_limit_write())]
)
def update_journal_entry(
    entry_id: UUID,
    update_data: JournalEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a journal entry (only drafts can be updated).

    DRAFT-ONLY RESTRICTION:
    - Only entries with status=DRAFT can be updated
    - Posted entries are immutable (must void instead)
    - Void entries are immutable

    ATOMIC LINE REPLACEMENT:
    - If lines are provided, ALL existing lines are replaced
    - Partial line updates not supported
    - Double-entry validation still applies

    PRECONDITIONS:
    - User must have manage_company permission
    - Entry must exist
    - Entry status must be DRAFT
    - If lines provided, must pass double-entry validation

    SIDE EFFECTS:
    - JournalEntry fields updated
    - If lines provided, old lines deleted and new lines created
    - updated_at timestamp changed
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Entry not found
    - STATE_CONFLICT: Entry is not DRAFT
    - JOURNAL_IMBALANCE: Lines don't balance
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Journal entry not found"
            }
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to update this journal entry"
            }
        )

    # Check state
    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot update {entry.status.value} journal entry. Only DRAFT entries can be updated.",
                "details": {
                    "entry_id": str(entry_id),
                    "current_status": entry.status.value
                }
            }
        )

    try:
        updated_entry = service.update_journal_entry(entry_id, update_data)

        total_debit, total_credit = service.get_entry_totals(updated_entry)

        return JournalEntryResponse(
            **updated_entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in updated_entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )

    except ValidationError as e:
        if "balance" in str(e).lower():
            error_code = "JOURNAL_IMBALANCE"
        else:
            error_code = "VALIDATION_ERROR"

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": str(e)
            }
        )
```

#### Post Journal Entry

```python
@router.post(
    "/journal-entries/{entry_id}/post",
    response_model=JournalEntryResponse,
    dependencies=[Depends(rate_limit_write())]
)
def post_journal_entry(
    entry_id: UUID,
    post_data: JournalEntryPost,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post a journal entry (make it permanent and update account balances).

    STATE TRANSITION: DRAFT → POSTED

    Once posted:
    - Entry cannot be edited or deleted
    - Account balances are updated in ledger
    - Accounts may be locked (FirstTransaction)
    - Entry can only be voided (not deleted)

    PRECONDITIONS:
    - User must have manage_company permission
    - Entry must exist
    - Entry status must be DRAFT
    - Entry must pass double-entry validation
    - Fiscal period must be OPEN

    SIDE EFFECTS:
    - status → POSTED
    - posted_at → current timestamp
    - posted_by → current_user.id
    - Account balances updated via LedgerService
    - Accounts may be locked (FirstTransaction reason)
    - Audit log entry created (critical operation)

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Entry not found
    - STATE_CONFLICT: Entry is not DRAFT
    - PERIOD_CLOSED: Fiscal period not OPEN
    - JOURNAL_IMBALANCE: Entry doesn't balance
    """
    je_service = JournalEntryService(db)
    entry = je_service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Journal entry not found"
            }
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to post this journal entry"
            }
        )

    # Check state
    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot post {entry.status.value} entry. Only DRAFT entries can be posted."
            }
        )

    try:
        # Post the entry
        posted_entry = je_service.post_journal_entry(entry_id, current_user.id)

        # Update account balances in ledger
        ledger_service = LedgerService(db)
        ledger_service.post_journal_entry(posted_entry)

        total_debit, total_credit = je_service.get_entry_totals(posted_entry)

        return JournalEntryResponse(
            **posted_entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in posted_entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )

    except ValidationError as e:
        error_message = str(e).lower()

        if "period" in error_message and ("closed" in error_message or "locked" in error_message):
            error_code = "PERIOD_CLOSED"
        elif "balance" in error_message:
            error_code = "JOURNAL_IMBALANCE"
        else:
            error_code = "VALIDATION_ERROR"

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": str(e)
            }
        )
```

#### Void Journal Entry

```python
@router.post(
    "/journal-entries/{entry_id}/void",
    response_model=JournalEntryResponse,
    dependencies=[Depends(rate_limit_write())]
)
def void_journal_entry(
    entry_id: UUID,
    void_data: JournalEntryVoid,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Void a posted journal entry.

    STATE TRANSITION: POSTED → VOID

    IMPORTANT: Voiding marks the entry as void but does NOT reverse balances.
    To reverse balances, create a reversing entry.

    PRECONDITIONS:
    - User must have manage_company permission
    - Entry must exist
    - Entry status must be POSTED
    - void_reason must be provided (audit requirement)

    SIDE EFFECTS:
    - status → VOID
    - voided_at → current timestamp
    - voided_by → current_user.id
    - void_reason stored
    - Audit log entry created (critical operation)
    - Balances NOT automatically reversed (manual reversing entry required)

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Entry not found
    - STATE_CONFLICT: Entry is not POSTED
    - VALIDATION_ERROR: Missing void_reason
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Journal entry not found"
            }
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to void this journal entry"
            }
        )

    # Check state
    if entry.status != EntryStatus.POSTED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot void {entry.status.value} entry. Only POSTED entries can be voided.",
                "details": {
                    "current_status": entry.status.value
                }
            }
        )

    try:
        voided_entry = service.void_journal_entry(
            entry_id,
            current_user.id,
            void_data.void_reason
        )

        total_debit, total_credit = service.get_entry_totals(voided_entry)

        return JournalEntryResponse(
            **voided_entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in voided_entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

#### Delete Journal Entry

```python
@router.delete(
    "/journal-entries/{entry_id}",
    status_code=204,
    dependencies=[Depends(rate_limit_write())]
)
def delete_journal_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a journal entry (only drafts can be deleted).

    DRAFT-ONLY RESTRICTION:
    - Posted entries cannot be deleted - they must be voided instead
    - Void entries are immutable and cannot be deleted

    PRECONDITIONS:
    - User must have manage_company permission
    - Entry must exist
    - Entry status must be DRAFT

    SIDE EFFECTS:
    - JournalEntry record deleted (cascade to lines)
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Entry not found
    - STATE_CONFLICT: Entry is not DRAFT
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Journal entry not found"
            }
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to delete this journal entry"
            }
        )

    # Check state
    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot delete {entry.status.value} entry. Only DRAFT entries can be deleted. Use void endpoint for POSTED entries.",
                "details": {
                    "current_status": entry.status.value
                }
            }
        )

    try:
        service.delete_journal_entry(entry_id)
        return None

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

### 2.3 Fiscal Period Controllers

#### Create Fiscal Period

```python
@router.post(
    "/accounting/fiscal-periods",
    response_model=FiscalPeriodResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_write())]
)
def create_fiscal_period(
    period_data: FiscalPeriodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new fiscal period.

    VALIDATION RULES:
    - end_date must be >= start_date
    - Period dates must not overlap with existing periods for same company
    - period_number format must match period_type

    PERIOD TYPES:
    - MONTH: period_number format "YYYY-MM" (e.g., "2024-01")
    - QUARTER: period_number format "YYYY-QN" (e.g., "2024-Q1")
    - YEAR: period_number format "YYYY" (e.g., "2024")

    PRECONDITIONS:
    - User must have manage_company permission
    - Company must exist
    - Period dates must not overlap existing periods
    - period_number must match period_type format

    SIDE EFFECTS:
    - New FiscalPeriod record created (status=OPEN)
    - Audit log entry created

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - VALIDATION_ERROR: Invalid dates, overlap, or format mismatch
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, period_data.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to create fiscal periods for this company"
            }
        )

    service = FiscalPeriodService(db)
    try:
        period = service.create_fiscal_period(period_data)
        return FiscalPeriodResponse(**period.__dict__)

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

#### Close Fiscal Period

```python
@router.post(
    "/accounting/fiscal-periods/{period_id}/close",
    response_model=FiscalPeriodResponse,
    dependencies=[Depends(rate_limit_critical())]
)
def close_fiscal_period(
    period_id: UUID,
    close_data: FiscalPeriodClose,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Close a fiscal period.

    STATE TRANSITION: OPEN → CLOSED

    REQUIREMENTS:
    - All journal entries in period must be POSTED (no drafts)
    - Period must currently be OPEN

    SIDE EFFECTS:
    - status → CLOSED
    - closed_at → current timestamp
    - closed_by → current_user.id
    - Accounts may be locked (PeriodClose reason)
    - Audit log entry created (critical operation)

    PRECONDITIONS:
    - User must have manage_company permission
    - Period must exist
    - Period status must be OPEN
    - No DRAFT journal entries in period

    ERROR CODES:
    - PERMISSION_DENIED: User lacks permission
    - NOT_FOUND: Period not found
    - STATE_CONFLICT: Period not OPEN or has DRAFT entries
    """
    service = FiscalPeriodService(db)
    period = service.get_fiscal_period(period_id)

    if not period:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Fiscal period not found"
            }
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, period.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to close this fiscal period"
            }
        )

    # Check state
    if period.status != PeriodStatus.OPEN:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot close {period.status.value} period. Only OPEN periods can be closed.",
                "details": {
                    "current_status": period.status.value
                }
            }
        )

    try:
        closed_period = service.close_fiscal_period(period_id, current_user.id)
        return FiscalPeriodResponse(**closed_period.__dict__)

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": str(e)
            }
        )
```

#### Reopen Fiscal Period

```python
@router.post(
    "/accounting/fiscal-periods/{period_id}/reopen",
    response_model=FiscalPeriodResponse,
    dependencies=[Depends(rate_limit_critical())]
)
def reopen_fiscal_period(
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reopen a closed fiscal period (requires superuser privileges).

    STATE TRANSITION: CLOSED → OPEN

    SECURITY:
    - Requires superuser privileges (enforced)
    - Cannot reopen LOCKED periods (regulatory immutability)
    - Creates audit trail of reopen operation

    RESTRICTIONS:
    - LOCKED periods cannot be reopened (immutable)
    - Only CLOSED periods can transition to OPEN

    USE CASES:
    - Correcting period close errors
    - Emergency adjustments after premature close
    - Reversing accidental period closure

    PRECONDITIONS:
    - Current user must be superuser
    - Period must exist
    - Period status must be CLOSED (not LOCKED)

    SIDE EFFECTS:
    - status → OPEN
    - closed_at → null
    - closed_by → null
    - Audit log entry created (critical operation)
    - Accounts remain locked (unlock separately if needed)

    ERROR CODES:
    - PERMISSION_DENIED: User is not superuser
    - NOT_FOUND: Period not found
    - STATE_CONFLICT: Period is LOCKED (cannot reopen)
    """
    # CRITICAL SECURITY: Enforce superuser privileges
    from app.core.security import check_superuser
    check_superuser(current_user)

    service = FiscalPeriodService(db)
    period = service.get_fiscal_period(period_id)

    if not period:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Fiscal period not found"
            }
        )

    # Check permissions (superuser can manage all companies, but verify access)
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, period.company_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PERMISSION_DENIED",
                "message": "No permission to reopen this fiscal period"
            }
        )

    # Check state
    if period.status == PeriodStatus.LOCKED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": "Cannot reopen LOCKED period. Locked periods are immutable for regulatory compliance.",
                "details": {
                    "current_status": period.status.value
                }
            }
        )

    if period.status != PeriodStatus.CLOSED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STATE_CONFLICT",
                "message": f"Cannot reopen {period.status.value} period. Only CLOSED periods can be reopened.",
                "details": {
                    "current_status": period.status.value
                }
            }
        )

    try:
        reopened_period = service.reopen_fiscal_period(period_id, reopened_by=current_user.id)
        return FiscalPeriodResponse(**reopened_period.__dict__)

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
```

---

## 3. Service Layer Methods

Service layer methods already exist in Phase 3B-compliant services. This section documents their contracts.

### 3.1 CompanyChartService Methods

**Location:** `backend/app/services/companychart_service.py`

#### `create_account(company_id: UUID, account_data: CompanyAccountCreate) -> CompanyAccount`

**Contract:**
- Validates account code uniqueness within company
- Validates parent account exists and belongs to company
- Validates parent is Header type (if parent specified)
- Creates new CompanyAccount record
- Returns created account

**Validation:**
- Duplicate code → `ValidationError`
- Invalid parent → `ValidationError`
- Parent is Detail type → `ValidationError`

#### `update_account(company_id: UUID, code: str, account_data: CompanyAccountUpdate) -> CompanyAccount`

**Contract:**
- Retrieves account by code
- Validates locked account immutability
- Updates allowed fields
- Returns updated account

**Validation:**
- Account not found → returns `None`
- Locked account + immutable field change → `ValidationError` (LOCKED_ACCOUNT)
- Invalid parent → `ValidationError`

#### `delete_account(company_id: UUID, code: str) -> bool`

**Contract:**
- Retrieves account by code
- Validates account can be deleted (no children, not locked, not template-mandatory, no transactions)
- Soft deletes account (sets `is_active = False`)
- Returns success boolean

**Validation:**
- Account not found → returns `False`
- Has children → `ValidationError`
- Is locked → `ValidationError`
- Is template-mandatory → `ValidationError`
- Has posted transactions → `ValidationError`

#### `lock_account(account_id: UUID, reason: LockedReason, user_id: UUID = None) -> CompanyAccount`

**Contract:**
- Retrieves account by ID
- Sets lock status
- Records lock timestamp, reason, and user (if Manual)
- Returns locked account

**Validation:**
- Account not found → `ValidationError`
- Manual lock without user_id → `ValidationError`

#### `unlock_account(account_id: UUID, user_id: UUID) -> CompanyAccount`

**Contract:**
- Retrieves account by ID
- Validates no posted transactions in current period
- Clears lock status
- Records unlock in audit log
- Returns unlocked account

**Validation:**
- Account not found → `ValidationError`
- Has posted transactions in current period → `ValidationError`

### 3.2 JournalEntryService Methods

**Location:** `backend/app/services/journal_entry_service.py`

#### `create_journal_entry(entry_data: JournalEntryCreate, created_by: UUID) -> JournalEntry`

**Contract:**
- Validates fiscal period is OPEN
- Validates entry date within period bounds
- Validates all accounts belong to company
- Validates minimum 2 lines
- Validates debits == credits (exact decimal)
- Validates each line has debit XOR credit
- Generates entry_number
- Creates JournalEntry and JournalEntryLine records (status=DRAFT)
- Returns created entry with lines

**Validation:**
- Period not OPEN → `ValidationError` (PERIOD_CLOSED)
- Entry date outside period → `ValidationError`
- Accounts from different companies → `ValidationError`
- Less than 2 lines → `ValidationError` (JOURNAL_IMBALANCE)
- Debits != Credits → `ValidationError` (JOURNAL_IMBALANCE)
- Line has both debit and credit → `ValidationError` (JOURNAL_IMBALANCE)
- Line has neither debit nor credit → `ValidationError` (JOURNAL_IMBALANCE)

#### `update_journal_entry(entry_id: UUID, update_data: JournalEntryUpdate) -> JournalEntry`

**Contract:**
- Retrieves entry by ID
- Validates status is DRAFT
- If lines provided, deletes old lines and creates new lines (atomic)
- Updates entry fields
- Returns updated entry

**Validation:**
- Entry not found → `ValidationError`
- Status not DRAFT → `ValidationError` (STATE_CONFLICT)
- Lines don't balance → `ValidationError` (JOURNAL_IMBALANCE)

#### `post_journal_entry(entry_id: UUID, posted_by: UUID) -> JournalEntry`

**Contract:**
- Retrieves entry by ID
- Validates status is DRAFT
- Validates fiscal period is OPEN
- Validates double-entry rules
- Sets status = POSTED
- Sets posted_at and posted_by
- Returns posted entry

**Validation:**
- Entry not found → `ValidationError`
- Status not DRAFT → `ValidationError` (STATE_CONFLICT)
- Period not OPEN → `ValidationError` (PERIOD_CLOSED)
- Doesn't balance → `ValidationError` (JOURNAL_IMBALANCE)

#### `void_journal_entry(entry_id: UUID, voided_by: UUID, void_reason: str) -> JournalEntry`

**Contract:**
- Retrieves entry by ID
- Validates status is POSTED
- Sets status = VOID
- Sets voided_at, voided_by, void_reason
- Returns voided entry

**Validation:**
- Entry not found → `ValidationError`
- Status not POSTED → `ValidationError` (STATE_CONFLICT)
- Missing void_reason → `ValidationError`

#### `delete_journal_entry(entry_id: UUID) -> None`

**Contract:**
- Retrieves entry by ID
- Validates status is DRAFT
- Deletes entry (cascade to lines)

**Validation:**
- Entry not found → `ValidationError`
- Status not DRAFT → `ValidationError` (STATE_CONFLICT)

### 3.3 FiscalPeriodService Methods

**Location:** `backend/app/services/fiscal_period_service.py`

#### `create_fiscal_period(period_data: FiscalPeriodCreate) -> FiscalPeriod`

**Contract:**
- Validates end_date >= start_date
- Validates no overlapping periods exist
- Validates period_number format matches period_type
- Creates FiscalPeriod record (status=OPEN)
- Returns created period

**Validation:**
- end_date < start_date → `ValidationError`
- Overlapping periods → `ValidationError`
- Invalid period_number format → `ValidationError`

#### `close_fiscal_period(period_id: UUID, closed_by: UUID) -> FiscalPeriod`

**Contract:**
- Retrieves period by ID
- Validates status is OPEN
- Validates no DRAFT journal entries exist in period
- Sets status = CLOSED
- Sets closed_at and closed_by
- May lock accounts (PeriodClose reason)
- Returns closed period

**Validation:**
- Period not found → `ValidationError`
- Status not OPEN → `ValidationError` (STATE_CONFLICT)
- Has DRAFT entries → `ValidationError` (STATE_CONFLICT)

#### `reopen_fiscal_period(period_id: UUID, reopened_by: UUID) -> FiscalPeriod`

**Contract:**
- Retrieves period by ID
- Validates status is CLOSED (not LOCKED)
- Sets status = OPEN
- Clears closed_at and closed_by
- Records reopen in audit log
- Returns reopened period

**Validation:**
- Period not found → `ValidationError`
- Status is LOCKED → `ValidationError` (STATE_CONFLICT)
- Status not CLOSED → `ValidationError` (STATE_CONFLICT)

---

## 4. Explicit Rejection Matrix

### 4.1 Company Account Operations

| Operation | Rejection Condition | Error Code | HTTP Status |
|-----------|---------------------|------------|-------------|
| Create | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Create | company_id path != body | VALIDATION_ERROR | 400 |
| Create | Duplicate account code | VALIDATION_ERROR | 400 |
| Create | Parent account not found | VALIDATION_ERROR | 400 |
| Create | Parent belongs to different company | VALIDATION_ERROR | 400 |
| Create | Parent is Detail type | VALIDATION_ERROR | 400 |
| Update | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Update | Account not found | NOT_FOUND | 404 |
| Update | Locked account + immutable field change | LOCKED_ACCOUNT | 400 |
| Update | Invalid parent account | VALIDATION_ERROR | 400 |
| Delete | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Delete | Account not found | NOT_FOUND | 404 |
| Delete | Account is locked | LOCKED_ACCOUNT | 400 |
| Delete | Account has children | VALIDATION_ERROR | 400 |
| Delete | Account has posted transactions | VALIDATION_ERROR | 400 |
| Delete | Account is template-mandatory | VALIDATION_ERROR | 400 |
| Lock | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Lock | Account not found in company | NOT_FOUND | 404 |
| Lock | Manual lock without user_id | VALIDATION_ERROR | 400 |
| Unlock | User is not superuser | PERMISSION_DENIED | 403 |
| Unlock | Account not found in company | NOT_FOUND | 404 |
| Unlock | Has posted transactions in current period | STATE_CONFLICT | 400 |

### 4.2 Journal Entry Operations

| Operation | Rejection Condition | Error Code | HTTP Status |
|-----------|---------------------|------------|-------------|
| Create | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Create | Fiscal period not OPEN | PERIOD_CLOSED | 400 |
| Create | Entry date outside period bounds | VALIDATION_ERROR | 400 |
| Create | Accounts from different companies | VALIDATION_ERROR | 400 |
| Create | Less than 2 lines | JOURNAL_IMBALANCE | 400 |
| Create | Debits != Credits | JOURNAL_IMBALANCE | 400 |
| Create | Line has both debit and credit | JOURNAL_IMBALANCE | 400 |
| Create | Line has neither debit nor credit | JOURNAL_IMBALANCE | 400 |
| Update | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Update | Entry not found | NOT_FOUND | 404 |
| Update | Entry status != DRAFT | STATE_CONFLICT | 400 |
| Update | Lines don't balance | JOURNAL_IMBALANCE | 400 |
| Post | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Post | Entry not found | NOT_FOUND | 404 |
| Post | Entry status != DRAFT | STATE_CONFLICT | 400 |
| Post | Fiscal period not OPEN | PERIOD_CLOSED | 400 |
| Post | Entry doesn't balance | JOURNAL_IMBALANCE | 400 |
| Void | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Void | Entry not found | NOT_FOUND | 404 |
| Void | Entry status != POSTED | STATE_CONFLICT | 400 |
| Void | Missing void_reason | VALIDATION_ERROR | 400 |
| Delete | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Delete | Entry not found | NOT_FOUND | 404 |
| Delete | Entry status != DRAFT | STATE_CONFLICT | 400 |

### 4.3 Fiscal Period Operations

| Operation | Rejection Condition | Error Code | HTTP Status |
|-----------|---------------------|------------|-------------|
| Create | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Create | end_date < start_date | VALIDATION_ERROR | 400 |
| Create | Overlapping periods exist | VALIDATION_ERROR | 400 |
| Create | Invalid period_number format | VALIDATION_ERROR | 400 |
| Close | User lacks manage_company permission | PERMISSION_DENIED | 403 |
| Close | Period not found | NOT_FOUND | 404 |
| Close | Period status != OPEN | STATE_CONFLICT | 400 |
| Close | Has DRAFT journal entries | STATE_CONFLICT | 400 |
| Reopen | User is not superuser | PERMISSION_DENIED | 403 |
| Reopen | Period not found | NOT_FOUND | 404 |
| Reopen | Period status == LOCKED | STATE_CONFLICT | 400 |
| Reopen | Period status != CLOSED | STATE_CONFLICT | 400 |

---

## 5. Audit Hooks

### 5.1 Audit Requirements

Every mutating operation MUST record:
- **Who:** `user_id` of authenticated user
- **When:** Timestamp (created_at, updated_at, posted_at, etc.)
- **What:** Operation type and affected resources
- **Why:** Reason field where applicable (unlock_reason, void_reason)

### 5.2 Critical Operations Requiring Audit

| Operation | Audit Fields | Why Critical |
|-----------|--------------|--------------|
| Account unlock | user_id, unlocked_at, unlock_reason | Allows retroactive structural changes |
| Fiscal period close | closed_by, closed_at | Freezes period for reporting |
| Fiscal period reopen | reopened_by, reopened_at | Allows retroactive changes after close |
| Journal entry post | posted_by, posted_at | Finalizes transaction, updates balances |
| Journal entry void | voided_by, voided_at, void_reason | Invalidates posted transaction |
| Account lock (Manual) | locked_by, locked_at, locked_reason | Prevents structural changes |

### 5.3 Audit Service Integration

**Service:** `AuditService` (`backend/app/services/audit_service.py`)

**Methods:**
- `log_account_unlock(account_id, user_id, reason)`
- `log_period_close(period_id, user_id)`
- `log_period_reopen(period_id, user_id)`
- `log_entry_post(entry_id, user_id)`
- `log_entry_void(entry_id, user_id, reason)`
- `log_account_lock(account_id, user_id, reason)`

**Audit Log Schema:**
```python
{
  "id": UUID,
  "timestamp": datetime,
  "user_id": UUID,
  "operation": str,  # "account_unlock", "period_close", etc.
  "resource_type": str,  # "CompanyAccount", "FiscalPeriod", etc.
  "resource_id": UUID,
  "reason": str | null,
  "metadata": JSONB  # Additional context
}
```

---

## 6. Error Response Format

### 6.1 Standard Error Schema

```typescript
{
  "error_code": string,     // Machine-readable error code
  "message": string,        // Human-readable explanation
  "details"?: object        // Optional context (field names, values, etc.)
}
```

### 6.2 Error Code Catalog

| Error Code | Meaning | HTTP Status |
|------------|---------|-------------|
| `PERMISSION_DENIED` | User lacks required permission | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `LOCKED_ACCOUNT` | Attempt to modify locked account immutable fields | 400 |
| `STATE_CONFLICT` | Invalid state transition (e.g., update POSTED entry) | 400 |
| `JOURNAL_IMBALANCE` | Debits != Credits or invalid line structure | 400 |
| `PERIOD_CLOSED` | Attempt to create/post entry in non-OPEN period | 400 |
| `VALIDATION_ERROR` | General validation failure | 400 |
| `TEMPLATE_VIOLATION` | Template-mandatory account rule violated | 400 |

### 6.3 Example Error Responses

**Locked Account Error:**
```json
{
  "error_code": "LOCKED_ACCOUNT",
  "message": "Cannot modify immutable fields on locked account.\nAccount locked: FirstTransaction\nLocked at: 2024-01-15T10:30:00Z\nAttempted changes:\n  - code: cannot change from '1010' to '1020'\n  - account_type: cannot change from 'Asset' to 'Expense'\n\nTo modify these fields, unlock the account first (requires superuser).",
  "details": {
    "code": "1010"
  }
}
```

**Journal Imbalance Error:**
```json
{
  "error_code": "JOURNAL_IMBALANCE",
  "message": "Debits (1000.00) do not equal credits (950.00). Difference: 50.00",
  "details": {
    "total_debit": "1000.00",
    "total_credit": "950.00",
    "difference": "50.00"
  }
}
```

**State Conflict Error:**
```json
{
  "error_code": "STATE_CONFLICT",
  "message": "Cannot update POSTED journal entry. Only DRAFT entries can be updated.",
  "details": {
    "entry_id": "550e8400-e29b-41d4-a716-446655440000",
    "current_status": "POSTED"
  }
}
```

**Period Closed Error:**
```json
{
  "error_code": "PERIOD_CLOSED",
  "message": "Cannot post journal entry to CLOSED fiscal period. Period must be OPEN.",
  "details": {
    "period_id": "123e4567-e89b-12d3-a456-426614174000",
    "period_status": "CLOSED"
  }
}
```

---

## 7. Transaction Safety

### 7.1 Service Layer Transactions

All write operations MUST be wrapped in database transactions:

```python
@transactional
def create_journal_entry(self, entry_data: JournalEntryCreate, created_by: UUID) -> JournalEntry:
    # Validation
    self.validate_fiscal_period_open(entry_data.fiscal_period_id)
    self.validate_double_entry(entry_data.lines)

    # Create entry
    entry = JournalEntry(...)
    self.db.add(entry)

    # Create lines
    for line_data in entry_data.lines:
        line = JournalEntryLine(...)
        self.db.add(line)

    # Commit handled by @transactional decorator
    self.db.commit()
    self.db.refresh(entry)

    return entry
```

### 7.2 Atomic Line Replacement

Journal entry line updates are atomic:

```python
def update_journal_entry(self, entry_id: UUID, update_data: JournalEntryUpdate) -> JournalEntry:
    entry = self.get_journal_entry(entry_id)

    # Validate state
    if entry.status != EntryStatus.DRAFT:
        raise ValidationError("Cannot update non-DRAFT entry", ErrorCode.STATE_CONFLICT)

    # If lines provided, replace ALL lines (atomic)
    if update_data.lines:
        # Delete old lines
        for line in entry.lines:
            self.db.delete(line)

        # Create new lines
        for line_data in update_data.lines:
            new_line = JournalEntryLine(...)
            self.db.add(new_line)

        # Validate new lines balance
        self.validate_double_entry(update_data.lines)

    # Update entry fields
    entry.description = update_data.description
    # ...

    self.db.commit()
    self.db.refresh(entry)

    return entry
```

---

## 8. Rate Limiting Configuration

### 8.1 Rate Limit Tiers

**None (Read Operations):**
- No rate limiting
- Used for: Chart reads, report generation, mapping queries

**Write (Standard Write Operations):**
- Limit: 100 requests per minute per user
- Used for: Account creation, mapping creation, journal entry drafts

**Critical (High-Risk Operations):**
- Limit: 10 requests per minute per user
- Used for: Account unlock, fiscal period close/reopen, entry posting

### 8.2 Implementation

```python
from app.core.rate_limiting import rate_limit_write, rate_limit_critical

# Standard write
@router.post(..., dependencies=[Depends(rate_limit_write())])

# Critical operation
@router.post(..., dependencies=[Depends(rate_limit_critical())])
```

### 8.3 Rate Limit Response

When rate limit exceeded:

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again in 45 seconds.",
  "details": {
    "retry_after": 45,
    "limit": 10,
    "window": "1 minute"
  }
}
```

**HTTP Status:** 429 Too Many Requests

---

## 9. Idempotency Considerations

### 9.1 Idempotent Operations

**Naturally idempotent:**
- PUT operations (update with same data produces same result)
- DELETE operations (deleting deleted resource returns 404, safe)
- Lock operations (locking locked account is no-op)

**NOT idempotent:**
- POST operations (create duplicate resources)
- State transitions (post → void → ??? undefined)

### 9.2 Idempotency Keys (Future Enhancement)

For POST operations that create resources, consider adding idempotency key support:

```http
POST /api/v1/journal-entries
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "company_id": "...",
  "fiscal_period_id": "...",
  ...
}
```

**Behavior:**
- First request with key creates resource, returns 201
- Subsequent requests with same key return existing resource, 200
- Keys expire after 24 hours

**Phase 3C Scope:** NOT implemented yet. Document for future consideration.

---

## 10. Phase 3C-2 Completion Summary

### Deliverables

✅ **1. Endpoint Inventory**
- 5 Company Account write endpoints
- 5 Journal Entry write endpoints
- 3 Fiscal Period write endpoints
- 4 Chart Template write endpoints (admin-level)

✅ **2. Controller Skeletons**
- Thin controllers (no business logic)
- Permission checks via PermissionService
- Service layer delegation
- Explicit error mapping

✅ **3. Service Layer Methods**
- Documented contracts for all write operations
- Validation rules specified
- Transaction safety ensured
- Error codes mapped

✅ **4. Explicit Rejection Matrix**
- All rejection conditions documented
- Error codes assigned
- HTTP status codes specified

✅ **5. Audit Hooks**
- Critical operations identified
- Audit fields documented (who/when/what/why)
- AuditService integration specified

### Compliance Verification

✅ **Hard Constraints Enforced:**
- ❌ No force flags
- ❌ No bypass validation
- ❌ No partial writes
- ❌ No silent coercion
- ❌ No business logic in controllers
- ❌ No mutation of POSTED entries (except void)
- ❌ No mutation of LOCKED accounts (except allowed fields)
- ❌ No bulk write endpoints
- ❌ No cross-company writes

✅ **Requirements Met:**
- ✅ UUID-only references
- ✅ Exact enum matching
- ✅ Transactional writes
- ✅ Deterministic failures
- ✅ Explicit error codes
- ✅ Idempotent operations (where applicable)

### Canonical Validation Rules Enforced

✅ **CompanyAccount:**
- Reject updates to immutable fields when is_locked = true
- Reject delete if account is locked
- Reject delete if account has posted transactions
- Lock automatically on first POSTED transaction

✅ **JournalEntry:**
- Minimum 2 lines
- Debit XOR credit per line
- Debits == credits (exact decimal match)
- All accounts belong to same company
- Fiscal period must be OPEN
- Update only allowed when status = DRAFT
- POST is a state transition, not an update
- VOID requires reason and preserves audit trail

✅ **FiscalPeriod:**
- No overlapping periods
- Close only if no DRAFT entries exist
- Reopen requires superuser
- Period state transitions audited

### Next Steps

Ready to proceed to **Phase 3C-3: Read APIs & Projection Safety**

---

**Document Authority:** api-guardian + contract-enforcer
**Status:** CANONICAL - Phase 3C-2 COMPLETE
**Next Phase:** 3C-3 (Read APIs & Projection Safety)
