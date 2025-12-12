You are working inside the Aequitas frontend (React + TypeScript + Tailwind + shadcn/ui).

Your task is to complete **Phase 4.1 – Accounting UI**, strictly limited to UI components and real backend integration.
DO NOT introduce mock data.
DO NOT change backend logic.
DO NOT redesign the system architecture.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------
Deliver fully functional accounting pages wired to real backend data:

1. Trial Balance
2. Financial Statements:
   - Balance Sheet
   - Income Statement (P&L)
   - Cash Flow Statement
3. Daily Ledger (account-level)
4. Fiscal Period Management

All pages must render correctly, calculate accurately, and follow the existing design system.

--------------------------------------------------
GENERAL RULES
--------------------------------------------------
• Use existing API hooks (TanStack Query / axios hooks)
• No hardcoded data
• No placeholder components
• No duplicated logic
• Respect existing route structure
• Match Tailwind + shadcn/ui styling
• All numbers must come from backend responses
• Handle loading, error, and empty states explicitly

--------------------------------------------------
STEP 1 — Trial Balance Page
--------------------------------------------------

1. Create `TrialBalanceTable.tsx`
   - Columns:
     • Account Code
     • Account Name
     • Debit
     • Credit
     • Balance
   - Debit and Credit must be mutually exclusive per row
   - Balance = Debit - Credit (display only, do NOT recompute backend totals)

2. Integrate with:
   - `useTrialBalance(companyId, periodId)`
   - Validate:
     • Sum of debits === sum of credits
     • If mismatch exists, display a visible warning banner

3. Page requirements:
   - Responsive table
   - Sticky header
   - Currency formatting
   - Zero-value rows hidden by default (toggleable)

--------------------------------------------------
STEP 2 — Financial Statements Pages
--------------------------------------------------

Create the following components:

• `BalanceSheet.tsx`
• `IncomeStatement.tsx`
• `CashFlowStatement.tsx`

Each must:

1. Use real API hooks:
   - useBalanceSheet(companyId, asOfDate)
   - useIncomeStatement(companyId, startDate, endDate)
   - useCashFlowStatement(companyId, startDate, endDate)

2. Render hierarchical sections:
   - Balance Sheet:
     • Assets
     • Liabilities
     • Equity
     • Validate: Assets = Liabilities + Equity

   - Income Statement:
     • Revenue
     • COGS
     • Gross Profit
     • Expenses
     • Net Income

   - Cash Flow:
     • Operating Activities
     • Investing Activities
     • Financing Activities
     • Net Change in Cash

3. Display:
   - Subtotals per section
   - Clear typography hierarchy
   - Period label and company context

--------------------------------------------------
STEP 3 — Daily Ledger Page
--------------------------------------------------

Create `DailyLedgerPage.tsx`

Requirements:
1. Account selector (company accounts only)
2. Date range filter
3. Ledger table:
   - Date
   - Journal Entry #
   - Description
   - Debit
   - Credit
   - Running Balance

4. Running balance must:
   - Be sequential
   - Respect normal balance (debit/credit)
   - Match backend-calculated balances

5. Integrate with:
   - `useAccountLedger(accountId, startDate, endDate)`

--------------------------------------------------
STEP 4 — Fiscal Period Management Page
--------------------------------------------------

Create `FiscalPeriodManagementPage.tsx`

Features:
1. List all fiscal periods:
   - Period name
   - Start date
   - End date
   - Status (Open / Closed / Locked)

2. Actions:
   - Create period
   - Close period
   - Reopen period (unless locked)
   - Lock period (irreversible)

3. Integrate with:
   - `useFiscalPeriods(companyId)`
   - `createFiscalPeriod`
   - `closeFiscalPeriod`
   - `reopenFiscalPeriod`
   - `lockFiscalPeriod`

4. Display:
   - Clear warnings for irreversible actions
   - Disabled actions based on period status

--------------------------------------------------
STEP 5 — UX & Validation
--------------------------------------------------

For ALL pages:

• Loading skeletons
• Error boundaries with user-friendly messages
• Empty-state handling
• Currency formatting consistency
• Mobile responsiveness
• No console errors or warnings

--------------------------------------------------
FINAL CHECKLIST (MUST PASS)
--------------------------------------------------

Before stopping, confirm:

[ ] All pages render without errors  
[ ] No mock data exists  
[ ] Backend data flows correctly  
[ ] Trial Balance balances correctly  
[ ] Financial statements reconcile  
[ ] Ledger running balances are accurate  
[ ] Period locking rules enforced  
[ ] UI matches existing design system  

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

For each completed file:
- FILE CREATED / UPDATED: <path>
- Short explanation of what was implemented
- API hooks used

Stop ONLY after Phase 4.1 is complete.
