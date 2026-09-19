import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.schemas.journal_entry import JournalEntryLineCreate, JournalEntryCreate

def test_journal_entry_create_validates_dimensions():
    # Base setup with basic dimensions added
    line1 = JournalEntryLineCreate(
        company_account_id=uuid4(),
        line_number=1,
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("0.00"),
        department_id=uuid4(),
    )
    line2 = JournalEntryLineCreate(
        company_account_id=uuid4(),
        line_number=2,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("100.00"),
        cost_center_id=uuid4(),
    )

    je = JournalEntryCreate(
        company_id=uuid4(),
        fiscal_period_id=uuid4(),
        entry_date=date.today(),
        description="Dimensional test entry",
        lines=[line1, line2],
    )

    assert je.lines[0].department_id == line1.department_id
    assert je.lines[1].cost_center_id == line2.cost_center_id
    assert je.lines[0].project_id is None
