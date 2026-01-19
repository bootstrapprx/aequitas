// Fiscal Period Types
export type PeriodStatus = 'OPEN' | 'CLOSED' | 'LOCKED';
export type PeriodType = 'MONTH' | 'QUARTER' | 'YEAR';

export interface FiscalPeriod {
  id: string;
  company_id: string;
  period_type: PeriodType;
  period_number: string;
  start_date: string;
  end_date: string;
  status: PeriodStatus;
  closed_at?: string;
  closed_by?: string;
  created_at: string;
  updated_at: string;
}

// Journal Entry Types
export type EntryStatus = 'draft' | 'posted' | 'void';
export type EntryType = 'standard' | 'adjusting' | 'closing' | 'reversing' | 'opening';

export interface JournalEntryLine {
  id?: string;
  company_account_id: string;
  line_number: number;
  description?: string;
  debit_amount: number;
  credit_amount: number;
}

export interface JournalEntry {
  id?: string;
  company_id: string;
  fiscal_period_id: string;
  entry_number?: string;
  entry_date: string;
  description: string;
  reference?: string;
  entry_type: EntryType;
  status?: EntryStatus;
  lines: JournalEntryLine[];
  total_debit?: number;
  total_credit?: number;
  created_by?: string;
  created_at?: string;
  posted_at?: string;
  posted_by?: string;
  voided_at?: string;
  voided_by?: string;
  void_reason?: string;
}

// Ledger Types
export interface LedgerEntry {
  journal_entry_id: string;
  journal_entry_line_id: string;
  entry_date: string;
  entry_number: string;
  description: string;
  reference?: string;
  debit_amount: number;
  credit_amount: number;
  running_balance: number;
  account_code: string;
  account_description: string;
}

export interface AccountLedger {
  company_id: string;
  company_account_id: string;
  account_code: string;
  account_description: string;
  normal_balance: string;
  beginning_balance: number;
  ending_balance: number;
  total_debits: number;
  total_credits: number;
  entries: LedgerEntry[];
}

// Trial Balance Types
export interface TrialBalanceAccount {
  account_code: string;
  account_description: string;
  account_type: string;
  category: string;
  normal_balance: string;
  debit_balance: number;
  credit_balance: number;
}

export interface TrialBalance {
  company_id: string;
  period_start: string;
  period_end: string;
  accounts: TrialBalanceAccount[];
  total_debits: number;
  total_credits: number;
  is_balanced: boolean;
  variance: number;
}

// Financial Statement Types
export interface FinancialStatementAccount {
  code: string;
  description: string;
  amount: number;
  level: number;
  is_header: boolean;
}

export interface FinancialStatementSection {
  name: string;
  accounts: FinancialStatementAccount[];
  total: number;
}

export interface BalanceSheet {
  company_id: string;
  company_name: string;
  as_of_date: string;
  assets: FinancialStatementSection;
  liabilities: FinancialStatementSection;
  equity: FinancialStatementSection;
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  is_balanced: boolean;
}

export interface IncomeStatement {
  company_id: string;
  company_name: string;
  period_start: string;
  period_end: string;
  revenue: FinancialStatementSection;
  cost_of_goods_sold: FinancialStatementSection;
  expenses: FinancialStatementSection;
  other_income: FinancialStatementSection;
  total_revenue: number;
  total_cogs: number;
  gross_profit: number;
  gross_profit_margin?: number;
  total_expenses: number;
  total_other_income: number;
  net_income: number;
  net_profit_margin?: number;
}

export interface CashFlowStatement {
  company_id: string;
  company_name: string;
  period_start: string;
  period_end: string;
  operating_activities: FinancialStatementSection;
  investing_activities: FinancialStatementSection;
  financing_activities: FinancialStatementSection;
  net_cash_from_operations: number;
  net_cash_from_investing: number;
  net_cash_from_financing: number;
  net_change_in_cash: number;
  beginning_cash_balance: number;
  ending_cash_balance: number;
}

// Account Balance Types
export interface AccountBalance {
  id: string;
  company_id: string;
  company_account_id: string;
  fiscal_period_id: string;
  beginning_balance: number;
  total_debits: number;
  total_credits: number;
  ending_balance: number;
  account_code?: string;
  account_description?: string;
}

// Helper types for forms
export interface JournalEntryFormData {
  company_id: string;
  fiscal_period_id: string;
  entry_date: string;
  description: string;
  reference?: string;
  entry_type: EntryType;
  lines: JournalEntryLine[];
}

export interface JournalEntryFilters {
  fiscal_period_id?: string;
  status?: EntryStatus;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}
