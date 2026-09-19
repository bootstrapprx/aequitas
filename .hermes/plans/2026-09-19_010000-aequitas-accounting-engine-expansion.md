# Aequitas Accounting Engine Expansion Plan

> **For Hermes:** Use test-driven-development and subagent-driven-development workflows to implement this plan phase-by-phase.

**Goal:** Expand the Aequitas accounting core from a foundational General Ledger engine into an enterprise-grade accounting and ERP system with Year-End Closing, Multi-Dimensional Cost Allocation, Multi-Currency FX, AR/AP Sub-Ledgers, Bank Reconciliation, and Intercompany Eliminations.

**Architecture:** Build on existing Canon I (Accounting Truth) invariants and the layered Chart of Accounts (Kernel L0 through L3). Add dedicated domain services and database models in `backend/app/db/models` and `backend/app/services`, strictly validating through `JournalEntryService` and `FiscalPeriodGuard` to maintain double-entry immutability and multi-tenant isolation.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2.0, PostgreSQL (with SQLite compatibility fallbacks in tests), Pydantic v2, pytest-asyncio.

---

## Current Baseline & Invariants

- Implemented: Double-entry invariant balance check (`sum(debits) == sum(credits)`), `AccountBalance` aggregation, `FiscalPeriod` overlap & lock guards, `FinancialStatementService` (Balance Sheet, Income Statement, Cash Flow), `MasterChartService`, `CompanyChartService`, and Deterministic `FiscalEngine`.
- Canon Invariants to Preserve:
  1. No journal entry may be posted if `sum(debits) != sum(credits)`.
  2. No write operations may target a `CLOSED` or `LOCKED` fiscal period.
  3. Posted transactions are immutable; adjustments require reversal or adjusting entries.
  4. Multi-tenant isolation: every operational entity references `company_id`.

---

## Phase 1: Year-End Closing & Accrual Reversals

### Task 1.1: Automated Year-End Closing Engine
**Objective:** Zero out nominal accounts (Revenue `4xxxx`, Expenses `5xxxx`/`6xxxx`) at fiscal year-end and post net income/loss to Retained Earnings (`39000`).

**Files:**
- Create: `backend/app/services/year_end_closing_service.py`
- Create: `backend/tests/services/test_year_end_closing_service.py`
- Modify: `backend/app/api/v1/accounting.py`

**Steps:**
1. Write unit tests in `test_year_end_closing_service.py` verifying nominal balances are zeroed and Retained Earnings is credited/debited by exact Net Income.
2. Implement `YearEndClosingService.generate_closing_entry(company_id, fiscal_year)` creating an `EntryType.CLOSING` journal entry.
3. Add API endpoint `POST /api/v1/accounting/fiscal-years/{year}/close` guarded by `require_superuser` or company admin.
4. Run tests: `pytest tests/services/test_year_end_closing_service.py -v`.

---

### Task 1.2: Scheduled Auto-Reversing Accrual Entries
**Objective:** Support accrual entries marked `auto_reverse=True` that automatically generate and post an inverse journal entry on the first day of the following fiscal period.

**Files:**
- Modify: `backend/app/db/models/journal_entry.py` (add `auto_reverse: Boolean`, `reversed_by_id: UUID`, `reversal_date: Date`)
- Modify: `backend/app/services/journal_entry_service.py`
- Create: `backend/tests/test_journal_auto_reversal.py`

**Steps:**
1. Write tests verifying posting an auto-reversing entry schedules/creates a paired inverted entry on `reversal_date`.
2. Add fields to `JournalEntry` and update `JournalEntryService.post_entry()` to trigger paired reversal entry generation.
3. Run tests: `pytest tests/test_journal_auto_reversal.py -v`.

---

## Phase 2: Multi-Dimensional Accounting (Dimensions & Cost Centers)

### Task 2.1: Line-Level Dimensional Tagging
**Objective:** Enable financial tracking by Department, Cost Center, Project, and Location without polluting the Chart of Accounts hierarchy.

**Files:**
- Create: `backend/app/db/models/accounting_dimension.py` (`AccountingDimension`, `DimensionValue`)
- Modify: `backend/app/db/models/journal_entry_line.py` (add `cost_center_id`, `department_id`, `project_id`, `location_id`)
- Modify: `backend/app/schemas/journal_entry.py`
- Create: `backend/tests/test_accounting_dimensions.py`

**Steps:**
1. Write tests verifying dimensional tags are recorded on journal entry lines and validated against active dimensions.
2. Implement `accounting_dimension.py` models and update `JournalEntryLine`.
3. Update `JournalEntryService` validation to verify dimension IDs belong to the same `company_id`.
4. Run tests: `pytest tests/test_accounting_dimensions.py -v`.

---

### Task 2.2: Dimensional P&L and Segment Reporting
**Objective:** Allow filtering Income Statements and Trial Balances by specific cost centers, projects, or departments.

**Files:**
- Modify: `backend/app/services/financial_statement_service.py`
- Modify: `backend/app/services/ledger_service.py`
- Modify: `backend/app/api/v1/accounting.py`
- Create: `backend/tests/test_dimensional_reporting.py`

**Steps:**
1. Write tests asserting P&L totals match exact filtered line activity when `department_id` or `cost_center_id` is supplied.
2. Update `FinancialStatementService.generate_income_statement` and `LedgerService.get_trial_balance` with dimension filters.
3. Run tests: `pytest tests/test_dimensional_reporting.py -v`.

---

## Phase 3: Multi-Currency & FX Revaluation

### Task 3.1: Currency Definition & Exchange Rate Store
**Objective:** Maintain exchange rates (daily, spot, period-average) and multi-currency transaction inputs.

**Files:**
- Create: `backend/app/db/models/currency.py` (`Currency`, `ExchangeRate`)
- Modify: `backend/app/db/models/company.py` (add `functional_currency: String(3) default 'USD'`)
- Modify: `backend/app/db/models/journal_entry_line.py` (add `currency_code`, `exchange_rate`, `foreign_debit_amount`, `foreign_credit_amount`)
- Create: `backend/app/services/fx_rate_service.py`
- Create: `backend/tests/test_fx_engine.py`

**Steps:**
1. Write tests for exchange rate lookups and line currency conversions to base functional currency.
2. Implement `Currency`, `ExchangeRate`, and `FxRateService`.
3. Validate that `debit_amount` and `credit_amount` in functional currency always balance, regardless of foreign currency mix.
4. Run tests: `pytest tests/test_fx_engine.py -v`.

---

### Task 3.2: Period-End Unrealized FX Revaluation Engine
**Objective:** Revalue foreign monetary asset and liability balances at period-end closing rates, generating unrealized FX Gain/Loss entries.

**Files:**
- Create: `backend/app/services/fx_revaluation_service.py`
- Modify: `backend/app/services/fiscal_period_service.py`
- Create: `backend/tests/services/test_fx_revaluation_service.py`

**Steps:**
1. Write tests verifying foreign currency cash/receivable revaluation posts balanced entries to Unrealized Gain/Loss accounts.
2. Implement `FxRevaluationService.run_period_revaluation(company_id, fiscal_period_id)`.
3. Run tests: `pytest tests/services/test_fx_revaluation_service.py -v`.

---

## Phase 4: Subsidiary Accounting (AR & AP Sub-Ledgers)

### Task 4.1: Party Registry & Accounts Receivable (AR) Sub-ledger
**Objective:** Manage Customer accounts, Invoices, Payment Receipts, and AR Aging schedules (Current, 30, 60, 90+ days).

**Files:**
- Create: `backend/app/db/models/party.py` (`Party`: Customer, Vendor, Employee)
- Create: `backend/app/db/models/ar_invoice.py` (`ARInvoice`, `ARInvoiceLine`, `ARPaymentApplication`)
- Create: `backend/app/services/ar_service.py`
- Create: `backend/tests/services/test_ar_service.py`

**Steps:**
1. Write tests verifying invoice creation auto-posts balanced GL entries (`Debit: AR 12000`, `Credit: Revenue 40000`) and payment application settles open balances.
2. Implement models and `ARService` with aging calculation.
3. Run tests: `pytest tests/services/test_ar_service.py -v`.

---

### Task 4.2: Accounts Payable (AP) Sub-ledger & Bill Processing
**Objective:** Manage Vendor accounts, Bills, Payment Runs, and AP Aging schedules.

**Files:**
- Create: `backend/app/db/models/ap_bill.py` (`APBill`, `APBillLine`, `APPaymentApplication`)
- Create: `backend/app/services/ap_service.py`
- Create: `backend/tests/services/test_ap_service.py`

**Steps:**
1. Write tests for bill posting (`Debit: Expense/Asset`, `Credit: AP 20000`) and payment clearance.
2. Implement `APService` with vendor aging reports and 1099 tracking classification.
3. Run tests: `pytest tests/services/test_ap_service.py -v`.

---

## Phase 5: Bank Reconciliation & Clearing Engine

### Task 5.1: Bank Statement Parsing & Transaction Staging
**Objective:** Ingest bank statement files (OFX, QFX, CSV) into a dedicated staging table for reconciliation matching.

**Files:**
- Create: `backend/app/db/models/bank_statement.py` (`BankStatement`, `BankStatementLine`)
- Create: `backend/app/services/bank_statement_service.py`
- Create: `backend/tests/services/test_bank_statement_service.py`

**Steps:**
1. Write tests parsing standard OFX and CSV bank statement formats.
2. Implement parser and statement persistence with SHA-256 duplicate line detection.
3. Run tests: `pytest tests/services/test_bank_statement_service.py -v`.

---

### Task 5.2: Automated Reconciliation Matching Engine
**Objective:** Match GL cash transactions with bank statement lines based on date, amount, reference number, and payee.

**Files:**
- Create: `backend/app/services/bank_reconciliation_service.py`
- Modify: `backend/app/db/models/journal_entry_line.py` (add `cleared_status: Enum('UNCLEARED', 'CLEARED', 'RECONCILED')`, `reconciled_at: DateTime`)
- Create: `backend/tests/services/test_bank_reconciliation_service.py`

**Steps:**
1. Write tests verifying rule-based auto-matching and manual reconciliation discrepancy reporting.
2. Implement `BankReconciliationService.auto_match()` and `finalize_reconciliation()`.
3. Run tests: `pytest tests/services/test_bank_reconciliation_service.py -v`.

---

## Phase 6: Intercompany Transactions & Consolidation

### Task 6.1: Paired Intercompany Journal Entries (Due To / Due From)
**Objective:** Automatically generate corresponding mirror entries between affiliated entities when an intercompany transaction is initiated.

**Files:**
- Create: `backend/app/db/models/intercompany_link.py`
- Modify: `backend/app/services/journal_entry_service.py`
- Create: `backend/app/services/intercompany_service.py`
- Create: `backend/tests/services/test_intercompany_service.py`

**Steps:**
1. Write tests asserting creating an intercompany charge in Company A creates an atomic pending reciprocal entry in Company B.
2. Implement `IntercompanyService` validating cross-company authority and account mapping.
3. Run tests: `pytest tests/services/test_intercompany_service.py -v`.

---

### Task 6.2: Consolidated Financial Statements with Auto-Eliminations
**Objective:** Generate group-level Balance Sheets and Income Statements that automatically eliminate intercompany receivables/payables and intercompany revenues/expenses.

**Files:**
- Create: `backend/app/services/consolidation_financial_service.py`
- Modify: `backend/app/api/v1/accounting.py`
- Create: `backend/tests/services/test_consolidation_financial_service.py`

**Steps:**
1. Write tests verifying combined multi-company statements eliminate matched Due To/Due From balances to prevent artificial asset/liability inflation.
2. Implement `ConsolidationFinancialService.generate_consolidated_balance_sheet()` and `generate_consolidated_income_statement()`.
3. Run tests: `pytest tests/services/test_consolidation_financial_service.py -v`.

---

## Verification & Acceptance Gate

1. All new models registered in `app/db/models/__init__.py` with SQLite compatibility fallbacks in `app/db/base.py`.
2. Clean module imports verified via `python scripts/validate_imports.py`.
3. Complete pytest test suite passes: `pytest tests/ -v`.
4. Zero regression on Canon accounting invariants (Canon I, II, III).
