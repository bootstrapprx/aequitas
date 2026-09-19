import csv
import io
import uuid
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models.bank_statement import BankStatement, BankStatementLine, StatementLineStatus


class BankStatementService:
    """Service to ingest and manage bank statements."""

    def __init__(self, db: Session):
        self.db = db

    def import_csv_statement(
        self,
        company_id: UUID,
        cash_account_id: UUID,
        statement_date: date,
        csv_text: str,
    ) -> BankStatement:
        """Import a CSV bank statement."""
        statement = BankStatement(
            id=uuid.uuid4(),
            company_id=company_id,
            cash_account_id=cash_account_id,
            statement_date=statement_date,
        )
        self.db.add(statement)
        self.db.flush()

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        line_num = 1
        for row in reader:
            # Parse date
            txn_date = datetime.strptime(row["Date"].strip(), "%Y-%m-%d").date()
            amount = Decimal(row["Amount"].strip())
            desc = row.get("Description", "").strip()
            ref = row.get("Reference", "").strip()

            line = BankStatementLine(
                id=uuid.uuid4(),
                statement_id=statement.id,
                line_number=line_num,
                transaction_date=txn_date,
                description=desc,
                reference=ref,
                amount=amount,
                status=StatementLineStatus.UNMATCHED,
            )
            self.db.add(line)
            line_num += 1

        self.db.commit()
        self.db.refresh(statement)
        return statement
