/agent frontend-architect

Implement Milestone 4.1: Complete Accounting UI for the Aequitas project.

--------------------------------------------------
SCOPE (STRICT)
--------------------------------------------------
This task is LIMITED to frontend implementation and real backend integration.

DO NOT:
- Modify backend logic or API behavior
- Modify database schemas or accounting rules
- Introduce mock, placeholder, or hardcoded data
- Recalculate financial values already computed by the backend

--------------------------------------------------
DELIVERABLES
--------------------------------------------------
Implement the following production-ready UI pages:

1. Trial Balance page with real data
2. Financial Statements pages:
   - Balance Sheet
   - Income Statement
   - Cash Flow Statement
3. Daily Ledger page with account-level detail
4. Fiscal Period Management interface

--------------------------------------------------
TECHNICAL TASKS
--------------------------------------------------

1. Trial Balance
   - Create `TrialBalanceTable.tsx`
   - Columns:
     • Account Code
     • Account Name
     • Debit
     • Credit
     • Balance
   - Integrate with `useTrialBalance(companyId, periodId)`
   - Debit and Credit must be mutually exclusive per row
   - Validate that total debits === total credits
   - If mismatch exists, display a visible warning banner
   - Currency formatting, responsive layout, and sticky headers required

2. Financial Statements
   - Create:
     • `BalanceSheet.tsx`
     • `IncomeStatement.tsx`
     • `CashFlowStatement.tsx`
   - Integrate with:
     • `useBalanceSheet`
     • `useIncomeStatement`
     • `useCashFlowStatement`
   - Render hierarchical sections with subtotals
   - Display correct company and fiscal period context
   - Do NOT recompute backend totals

3. Daily Ledger
   - Create `DailyLedgerPage.tsx`
   - Features:
     • Account selector (company accounts only)
     • Date range filter
     • Ledger table with:
       - Date
       - Journal entry reference
       - Description
       - Debit
       - Credit
       - Running balance
   - Integrate with `useAccountLedger(accountId, startDate, endDate)`
   - Running balance must be sequential and visually clear

4. Fiscal Period Management
   - Create `FiscalPeriodManagementPage.tsx`
   - Display:
     • Period name
     • Start date
     • End date
     • Status (Open / Closed / Locked)
   - Actions:
     • Create period
     • Close period
     • Reopen period (unless locked)
     • Lock period (irreversible)
   - Integrate with existing fiscal period API hooks
   - Show confirmation dialogs for irreversible actions
   - Disable actions based on period status

--------------------------------------------------
UI & UX REQUIREMENTS
--------------------------------------------------
For ALL pages:
- Loading states (skeletons or spinners)
- Error handling with user-friendly messages
- Empty states
- Responsive design (desktop + tablet)
- Consistent currency formatting
- Match Tailwind + shadcn/ui design system
- Zero console errors or warnings

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------
Before stopping, confirm:
[ ] All pages render without runtime errors
[ ] All data comes from real backend APIs
[ ] No mock or hardcoded data exists
[ ] Trial Balance validates correctly
[ ] Financial statements display accurate totals
[ ] Ledger running balances are correct
[ ] UI is responsive and consistent

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
For each file created or updated:
- FILE CREATED / UPDATED: <path>
- Brief description of changes
- API hooks used

Stop once Milestone 4.1 is fully implemented.
