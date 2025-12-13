/**
 * Centralized query keys for React Query.
 * Using a structured approach helps avoid key collisions and simplifies invalidation.
 *
 * See: https://tanstack.com/query/v5/docs/react/guides/query-keys
 */

export enum QueryKey {
  COMPANIES = 'companies',
  MASTER_CHART = 'masterChart',
  COMPANY_CHART = 'companyChart',
  TEMPLATES = 'templates',
  ADMIN = 'admin',
  JOURNAL_ENTRIES = 'journal-entries',
  FISCAL_PERIODS = 'fiscal-periods',
  ACCOUNT_LEDGER = 'account-ledger',
  TRIAL_BALANCE = 'trial-balance',
  BALANCE_SHEET = 'balance-sheet',
  INCOME_STATEMENT = 'income-statement',
  CASH_FLOW = 'cash-flow-statement',
  ACCOUNT_BALANCES = 'account-balances',
  COMPANY_ACCOUNTS = 'company-accounts',
}

export const masterChartKeys = {
  all: [QueryKey.MASTER_CHART] as const,
  lists: () => [...masterChartKeys.all, 'list'] as const,
  list: (filters: string) => [...masterChartKeys.lists(), { filters }] as const,
  details: () => [...masterChartKeys.all, 'detail'] as const,
  detail: (id: string) => [...masterChartKeys.details(), id] as const,
};

export const companyChartKeys = {
  all: [QueryKey.COMPANY_CHART] as const,
  lists: () => [...companyChartKeys.all, 'list'] as const,
  list: (filters: string) => [...companyChartKeys.lists(), { filters }] as const,
  details: () => [...companyChartKeys.all, 'detail'] as const,
  detail: (id: string) => [...companyChartKeys.details(), id] as const,
};

export const companyKeys = {
  all: [QueryKey.COMPANIES] as const,
  lists: () => [...companyKeys.all, 'list'] as const,
  list: (filters: string) => [...companyKeys.lists(), { filters }] as const,
  details: () => [...companyKeys.all, 'detail'] as const,
  detail: (id: string) => [...companyKeys.details(), id] as const,
};

export const templateKeys = {
    all: [QueryKey.TEMPLATES] as const,
    lists: () => [...templateKeys.all, 'list'] as const,
    list: (filters: string) => [...templateKeys.lists(), { filters }] as const,
    details: () => [...templateKeys.all, 'detail'] as const,
    detail: (id: string) => [...templateKeys.details(), id] as const,
};

export const adminKeys = {
  all: [QueryKey.ADMIN] as const,
  users: () => [...adminKeys.all, 'users'] as const,
  settings: () => [...adminKeys.all, 'settings'] as const,
};

// Accounting module keys - company-scoped
export const journalEntryKeys = {
  all: [QueryKey.JOURNAL_ENTRIES] as const,
  byCompany: (companyId: string) => [...journalEntryKeys.all, companyId] as const,
  filtered: (companyId: string, filters: Record<string, any>) =>
    [...journalEntryKeys.byCompany(companyId), filters] as const,
  detail: (entryId: string) => [...journalEntryKeys.all, entryId] as const,
};

export const fiscalPeriodKeys = {
  all: [QueryKey.FISCAL_PERIODS] as const,
  byCompany: (companyId: string) => [...fiscalPeriodKeys.all, companyId] as const,
  filtered: (companyId: string, filters: Record<string, any>) =>
    [...fiscalPeriodKeys.byCompany(companyId), filters] as const,
};

export const accountLedgerKeys = {
  all: [QueryKey.ACCOUNT_LEDGER] as const,
  byCompanyAndAccount: (companyId: string, accountId: string) =>
    [...accountLedgerKeys.all, companyId, accountId] as const,
  filtered: (companyId: string, accountId: string, filters: Record<string, any>) =>
    [...accountLedgerKeys.byCompanyAndAccount(companyId, accountId), filters] as const,
};

export const trialBalanceKeys = {
  all: [QueryKey.TRIAL_BALANCE] as const,
  byCompany: (companyId: string, options: Record<string, any>) =>
    [...trialBalanceKeys.all, companyId, options] as const,
};

export const balanceSheetKeys = {
  all: [QueryKey.BALANCE_SHEET] as const,
  byCompany: (companyId: string, asOfDate: string) =>
    [...balanceSheetKeys.all, companyId, asOfDate] as const,
};

export const incomeStatementKeys = {
  all: [QueryKey.INCOME_STATEMENT] as const,
  byCompany: (companyId: string, startDate: string, endDate: string) =>
    [...incomeStatementKeys.all, companyId, startDate, endDate] as const,
};

export const cashFlowKeys = {
  all: [QueryKey.CASH_FLOW] as const,
  byCompany: (companyId: string, startDate: string, endDate: string) =>
    [...cashFlowKeys.all, companyId, startDate, endDate] as const,
};

export const accountBalanceKeys = {
  all: [QueryKey.ACCOUNT_BALANCES] as const,
  byCompany: (companyId: string, fiscalPeriodId: string) =>
    [...accountBalanceKeys.all, companyId, fiscalPeriodId] as const,
};

export const companyAccountKeys = {
  all: [QueryKey.COMPANY_ACCOUNTS] as const,
  byCompany: (companyId: string) => [...companyAccountKeys.all, companyId] as const,
};
