import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  JournalEntry,
  JournalEntryFilters,
  FiscalPeriod,
  TrialBalance,
  BalanceSheet,
  IncomeStatement,
  CashFlowStatement,
  AccountLedger,
  AccountBalance,
} from '@/types/accounting';

// ===== Journal Entry Hooks =====

export const useJournalEntries = (companyId: string, filters?: JournalEntryFilters) => {
  return useQuery({
    queryKey: ['journal-entries', companyId, filters],
    queryFn: async () => {
      const params: Record<string, any> = { company_id: companyId, ...filters };
      const response = await api.get('/journal-entries', { params });
      return response;
    },
    enabled: !!companyId,
  });
};

export const useJournalEntry = (entryId?: string) => {
  return useQuery({
    queryKey: ['journal-entry', entryId],
    queryFn: async () => {
      if (!entryId) return null;
      return await api.get(`/journal-entries/${entryId}`);
    },
    enabled: !!entryId,
  });
};

export const useCreateJournalEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entry: JournalEntry) => {
      return await api.post('/journal-entries', { body: entry });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    },
  });
};

export const useUpdateJournalEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, data }: { entryId: string; data: Partial<JournalEntry> }) => {
      return await api.put(`/journal-entries/${entryId}`, { body: data });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
      queryClient.invalidateQueries({ queryKey: ['journal-entry', variables.entryId] });
    },
  });
};

export const usePostJournalEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, userId }: { entryId: string; userId: string }) => {
      return await api.post(`/journal-entries/${entryId}/post`, {
        body: { posted_by: userId },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
      queryClient.invalidateQueries({ queryKey: ['trial-balance'] });
      queryClient.invalidateQueries({ queryKey: ['account-balances'] });
    },
  });
};

export const useVoidJournalEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      entryId,
      userId,
      reason,
    }: {
      entryId: string;
      userId: string;
      reason: string;
    }) => {
      return await api.post(`/journal-entries/${entryId}/void`, {
        body: { voided_by: userId, void_reason: reason },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    },
  });
};

export const useDeleteJournalEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      return await api.delete(`/journal-entries/${entryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    },
  });
};

// ===== Fiscal Period Hooks =====

export const useFiscalPeriods = (companyId?: string, filters?: {
  period_type?: string;
  status?: string;
  year?: number;
}) => {
  return useQuery({
    queryKey: ['fiscal-periods', companyId, filters],
    queryFn: async () => {
      if (!companyId) return [];
      const params = { company_id: companyId, ...filters };
      return await api.get('/accounting/fiscal-periods', { params });
    },
    enabled: !!companyId,
  });
};

export const useCreateFiscalPeriod = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (period: Partial<FiscalPeriod>) => {
      return await api.post('/accounting/fiscal-periods', { body: period });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
    },
  });
};

export const useCloseFiscalPeriod = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ periodId, userId }: { periodId: string; userId: string }) => {
      return await api.post(`/accounting/fiscal-periods/${periodId}/close`, {
        body: { closed_by: userId },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
    },
  });
};

export const useCreateMonthlyPeriods = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ companyId, year }: { companyId: string; year: number }) => {
      return await api.post(`/accounting/fiscal-periods/create-monthly/${companyId}/${year}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
    },
  });
};

// ===== Ledger Hooks =====

export const useAccountLedger = (
  companyId?: string,
  accountId?: string,
  filters?: {
    fiscal_period_id?: string;
    start_date?: string;
    end_date?: string;
  }
) => {
  return useQuery({
    queryKey: ['account-ledger', companyId, accountId, filters],
    queryFn: async () => {
      if (!companyId || !accountId) return null;
      const params = { company_id: companyId, ...filters };
      return await api.get<AccountLedger>(`/accounting/ledger/account/${accountId}`, { params });
    },
    enabled: !!companyId && !!accountId,
  });
};

export const useTrialBalance = (
  companyId?: string,
  options?: {
    fiscal_period_id?: string;
    as_of_date?: string;
  }
) => {
  return useQuery({
    queryKey: ['trial-balance', companyId, options],
    queryFn: async () => {
      if (!companyId) return null;
      const params = { company_id: companyId, ...options };
      return await api.get<TrialBalance>('/accounting/trial-balance', { params });
    },
    enabled: !!companyId && (!!options?.fiscal_period_id || !!options?.as_of_date),
  });
};

export const useAccountBalances = (companyId?: string, fiscalPeriodId?: string) => {
  return useQuery({
    queryKey: ['account-balances', companyId, fiscalPeriodId],
    queryFn: async () => {
      if (!companyId || !fiscalPeriodId) return [];
      const params = { company_id: companyId, fiscal_period_id: fiscalPeriodId };
      return await api.get<AccountBalance[]>('/accounting/balances', { params });
    },
    enabled: !!companyId && !!fiscalPeriodId,
  });
};

// ===== Financial Statement Hooks =====

export const useBalanceSheet = (companyId?: string, asOfDate?: string) => {
  return useQuery({
    queryKey: ['balance-sheet', companyId, asOfDate],
    queryFn: async () => {
      if (!companyId || !asOfDate) return null;
      const params = { company_id: companyId, as_of_date: asOfDate };
      return await api.get<BalanceSheet>('/accounting/balance-sheet', { params });
    },
    enabled: !!companyId && !!asOfDate,
  });
};

export const useIncomeStatement = (
  companyId?: string,
  startDate?: string,
  endDate?: string
) => {
  return useQuery({
    queryKey: ['income-statement', companyId, startDate, endDate],
    queryFn: async () => {
      if (!companyId || !startDate || !endDate) return null;
      const params = { company_id: companyId, start_date: startDate, end_date: endDate };
      return await api.get<IncomeStatement>('/accounting/income-statement', { params });
    },
    enabled: !!companyId && !!startDate && !!endDate,
  });
};

export const useCashFlowStatement = (
  companyId?: string,
  startDate?: string,
  endDate?: string
) => {
  return useQuery({
    queryKey: ['cash-flow-statement', companyId, startDate, endDate],
    queryFn: async () => {
      if (!companyId || !startDate || !endDate) return null;
      const params = { company_id: companyId, start_date: startDate, end_date: endDate };
      return await api.get<CashFlowStatement>('/accounting/cash-flow', { params });
    },
    enabled: !!companyId && !!startDate && !!endDate,
  });
};
