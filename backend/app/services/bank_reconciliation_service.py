from decimal import Decimal
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.bank_statement import BankStatement, BankStatementLine, StatementLineStatus
from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.db.models.journal_entry_line import JournalEntryLine


class BankReconciliationService:
    """Service to automatically match and reconcile bank statement lines with GL transactions."""

    def __init__(self, db: Session):
        self.db = db

    def auto_match(
        self,
        statement_id: UUID,
        cash_account_id: UUID,
    ) -> Dict[str, Any]:
        """
        Auto-match bank statement lines to GL journal entry lines.
        Matching rules: Exact date and exact net transaction cash effect.
        """
        stmt_lines = self.db.query(BankStatementLine).filter(
            BankStatementLine.statement_id == statement_id,
            BankStatementLine.status == StatementLineStatus.UNMATCHED,
        ).all()

        matched_count = 0
        unmatched_count = 0

        # Query all posted GL lines for this cash account
        gl_lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            JournalEntryLine.company_account_id == cash_account_id,
            JournalEntry.status == EntryStatus.POSTED,
        ).all()

        already_matched_gl_ids = set()

        for s_line in stmt_lines:
            target_amount = s_line.amount
            match_found = None

            for gl in gl_lines:
                if gl.id in already_matched_gl_ids:
                    continue

                # Cash debit = positive bank deposit, Cash credit = negative bank withdrawal
                net_gl_cash = Decimal(str(gl.debit_amount)) - Decimal(str(gl.credit_amount))

                if gl.journal_entry.entry_date == s_line.transaction_date and net_gl_cash == target_amount:
                    match_found = gl
                    break

            if match_found:
                s_line.status = StatementLineStatus.MATCHED
                s_line.matched_journal_entry_line_id = match_found.id
                already_matched_gl_ids.add(match_found.id)
                matched_count += 1
            else:
                unmatched_count += 1

        self.db.commit()

        return {
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "total_processed": len(stmt_lines),
        }
