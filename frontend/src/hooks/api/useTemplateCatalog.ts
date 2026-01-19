import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { MasterAccount, MasterAccountNode, MasterChartStats } from '@/types/masterchart';

const catalogKeys = {
  all: ['templateCatalog'] as const,
  tree: () => [...catalogKeys.all, 'tree'] as const,
  stats: () => [...catalogKeys.all, 'stats'] as const,
  accounts: (search?: string) => [...catalogKeys.all, 'accounts', search || 'all'] as const,
};

export const useTemplateCatalogTree = () => {
  return useQuery({
    queryKey: catalogKeys.tree(),
    queryFn: () => api.get<MasterAccountNode[]>('/catalog/tree'),
  });
};

export const useTemplateCatalogStats = () => {
  return useQuery({
    queryKey: catalogKeys.stats(),
    queryFn: () => api.get<MasterChartStats>('/catalog/stats'),
  });
};

export const useTemplateCatalogAccounts = (search?: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: catalogKeys.accounts(search),
    queryFn: () => {
      const params = search ? { search } : undefined;
      return api.get<MasterAccount[]>('/catalog/accounts', { params });
    },
    enabled,
  });
};
