from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.journal_entry import EntryStatus
from app.api.v1.auth import get_current_user
from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryPost,
    JournalEntryVoid,
    JournalEntryList,
    JournalEntryLineResponse
)
from app.services.journal_entry_service import JournalEntryService
from app.services.ledger_service import LedgerService
from app.services.permission_service import PermissionService

router = APIRouter()


@router.post("/", response_model=JournalEntryResponse, status_code=201)
def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new journal entry.

    Requires:
    - At least 2 lines
    - Debits must equal credits
    - All accounts must belong to the company
    - Fiscal period must be open
    - Entry date must be within fiscal period
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry_data.company_id):
        raise HTTPException(status_code=403, detail="No permission to create journal entries for this company")

    # Create entry
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

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=JournalEntryList)
def list_journal_entries(
    company_id: UUID,
    fiscal_period_id: Optional[UUID] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List journal entries with optional filters.

    Query params:
    - company_id: Required
    - fiscal_period_id: Optional period filter
    - status: Optional status filter (draft, posted, void)
    - start_date: Optional start date
    - end_date: Optional end date
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view journal entries for this company")

    # Get entries
    service = JournalEntryService(db)

    entry_status = None
    if status:
        try:
            entry_status = EntryStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    offset = (page - 1) * page_size

    entries = service.get_journal_entries(
        company_id=company_id,
        fiscal_period_id=fiscal_period_id,
        status=entry_status,
        start_date=start_date,
        end_date=end_date,
        limit=page_size,
        offset=offset
    )

    # Build response list
    entry_responses = []
    for entry in entries:
        total_debit, total_credit = service.get_entry_totals(entry)
        response = JournalEntryResponse(
            **entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )
        entry_responses.append(response)

    return JournalEntryList(
        entries=entry_responses,
        total=len(entries),  # TODO: Add count query for accurate total
        page=page,
        page_size=page_size
    )


@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific journal entry by ID."""
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, entry.company_id):
        raise HTTPException(status_code=403, detail="No permission to view this journal entry")

    total_debit, total_credit = service.get_entry_totals(entry)

    return JournalEntryResponse(
        **entry.__dict__,
        lines=[JournalEntryLineResponse(**line.__dict__) for line in entry.lines],
        total_debit=total_debit,
        total_credit=total_credit
    )


@router.put("/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: UUID,
    update_data: JournalEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a journal entry (only drafts can be updated).

    You can update:
    - Entry date
    - Description
    - Reference
    - Lines (all lines will be replaced)
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(status_code=403, detail="No permission to update this journal entry")

    try:
        updated_entry = service.update_journal_entry(entry_id, update_data)

        total_debit, total_credit = service.get_entry_totals(updated_entry)

        return JournalEntryResponse(
            **updated_entry.__dict__,
            lines=[JournalEntryLineResponse(**line.__dict__) for line in updated_entry.lines],
            total_debit=total_debit,
            total_credit=total_credit
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
def post_journal_entry(
    entry_id: UUID,
    post_data: JournalEntryPost,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post a journal entry (make it permanent and update account balances).

    Once posted:
    - Entry cannot be edited or deleted
    - Account balances are updated
    - Entry can only be voided (not deleted)
    """
    je_service = JournalEntryService(db)
    entry = je_service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(status_code=403, detail="No permission to post this journal entry")

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

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/void", response_model=JournalEntryResponse)
def void_journal_entry(
    entry_id: UUID,
    void_data: JournalEntryVoid,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Void a posted journal entry.

    Voiding marks the entry as void but does not reverse it.
    To reverse balances, create a reversing entry.
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(status_code=403, detail="No permission to void this journal entry")

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

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}", status_code=204)
def delete_journal_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a journal entry (only drafts can be deleted).

    Posted entries cannot be deleted - they must be voided instead.
    """
    service = JournalEntryService(db)
    entry = service.get_journal_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, entry.company_id):
        raise HTTPException(status_code=403, detail="No permission to delete this journal entry")

    try:
        service.delete_journal_entry(entry_id)
        return None

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
