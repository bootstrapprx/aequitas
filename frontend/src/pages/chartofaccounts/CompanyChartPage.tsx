import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api, ApiError } from '@/lib/api';
import { Search, Plus, RefreshCw, Lock, Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useCompany } from '@/contexts/CompanyContext';
import { useToast } from '@/hooks/use-toast';
import type { CompanyAccount } from '@/types/company_account';
import type { MasterAccount } from '@/types/masterchart';

interface CompanyChartStats {
  total_accounts: number;
  active_accounts: number;
  inactive_accounts: number;
  header_count: number;
  detail_count: number;
  mapped_accounts: number;
  unmapped_accounts: number;
}

export default function CompanyChartPage() {
  const [search, setSearch] = useState('');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState('');
  const [selectedCatalogId, setSelectedCatalogId] = useState<string | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { selectedCompanyId, selectedCompany } = useCompany();
  const isActiveCompany = selectedCompany?.onboarding_status === 'ACTIVE';

  // Get company chart
  const {
    data: accounts,
    isLoading: accountsLoading,
    refetch: refetchAccounts,
  } = useQuery({
    queryKey: ['company-chart', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return [] as CompanyAccount[];
      return api.get<CompanyAccount[]>(`/companies/${selectedCompanyId}/chart`);
    },
    enabled: !!selectedCompanyId,
  });

  // Get company chart stats
  const { data: stats } = useQuery({
    queryKey: ['company-chart-stats', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return null;
      return api.get<CompanyChartStats>(`/companies/${selectedCompanyId}/chart/stats`);
    },
    enabled: !!selectedCompanyId,
  });

  // Fetch template catalog for add-account flow
  const { data: catalogAccounts = [], isLoading: catalogLoading } = useQuery({
    queryKey: ['template-catalog', catalogSearch, isAddOpen],
    queryFn: async () => {
      const params = catalogSearch ? { search: catalogSearch } : undefined;
      return api.get<MasterAccount[]>('/catalog/accounts', { params });
    },
    enabled: isAddOpen,
  });

  const addMutation = useMutation({
    mutationFn: async (catalogAccountId: string) => {
      if (!selectedCompanyId) throw new Error('Company not selected');
      return api.post(`/companies/${selectedCompanyId}/chart/add-from-catalog`, {
        catalog_account_id: catalogAccountId,
      });
    },
    onSuccess: () => {
      toast({
        title: 'Account added',
        description: 'The account was added to your chart of accounts.',
      });
      setIsAddOpen(false);
      setCatalogSearch('');
      setSelectedCatalogId(null);
      queryClient.invalidateQueries({ queryKey: ['company-chart', selectedCompanyId] });
      queryClient.invalidateQueries({ queryKey: ['company-chart-stats', selectedCompanyId] });
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.getUserMessage()
        : error instanceof Error
          ? error.message
          : 'Failed to add account.';
      toast({
        title: 'Add account failed',
        description: message,
        variant: 'destructive',
      });
    },
  });

  const filteredAccounts = useMemo(() => {
    if (!accounts) return [];
    if (!search) return accounts;

    const searchLower = search.toLowerCase();
    return accounts.filter(
      (acc) =>
        acc.code.toLowerCase().includes(searchLower) ||
        acc.description.toLowerCase().includes(searchLower) ||
        (acc.name || '').toLowerCase().includes(searchLower)
    );
  }, [accounts, search]);

  const accountById = useMemo(() => {
    const map = new Map<string, CompanyAccount>();
    (accounts || []).forEach((acc) => map.set(acc.id, acc));
    return map;
  }, [accounts]);

  const existingCodes = useMemo(() => new Set((accounts || []).map((acc) => acc.code)), [accounts]);
  const hasAccounts = (accounts || []).length > 0;

  const selectedCatalog = catalogAccounts.find((acc) => acc.id === selectedCatalogId) || null;
  const displayCatalog = catalogAccounts.slice(0, 50);

  if (!selectedCompanyId) {
    return (
      <div className="p-6">
        <Alert>
          <AlertDescription>
            No company selected. Please select a company from the dropdown above.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Chart of Accounts</h1>
        <p className="text-muted-foreground mt-2">
          Manage your company's chart of accounts
        </p>
      </div>

      {hasAccounts && (
        <Alert className="bg-emerald-50 border-emerald-200">
          <AlertDescription className="text-emerald-900">
            Your chart of accounts is ready. You can add more accounts if needed.
          </AlertDescription>
        </Alert>
      )}

      {isActiveCompany && (
        <Alert className="bg-muted/40 border-border">
          <div className="flex items-start gap-2">
            <Lock className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <div className="space-y-2">
              <AlertDescription className="text-foreground">
                This chart is now protected. You may add new accounts, but existing structure and history are preserved.
              </AlertDescription>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="inline-flex items-center gap-2 text-xs text-muted-foreground cursor-default">
                    <Info className="h-3.5 w-3.5" />
                    <span>This structure is protected after activation.</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  This structure is protected after activation.
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </Alert>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Accounts</CardDescription>
              <CardTitle className="text-3xl">{stats.active_accounts}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Header Accounts</CardDescription>
              <CardTitle className="text-3xl">{stats.header_count}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Detail Accounts</CardDescription>
              <CardTitle className="text-3xl">{stats.detail_count}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Mapped to Catalog</CardDescription>
              <CardTitle className="text-3xl">{stats.mapped_accounts}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex-1 flex items-center space-x-2">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search accounts..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={() => refetchAccounts()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Account
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Add an Account</DialogTitle>
                    <DialogDescription>
                      Select one account from the catalog to add to your company chart.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4">
                    <Input
                      placeholder="Search the catalog by code or name..."
                      value={catalogSearch}
                      onChange={(e) => setCatalogSearch(e.target.value)}
                    />

                    {catalogLoading ? (
                      <div className="space-y-2">
                        {[...Array(6)].map((_, i) => (
                          <Skeleton key={i} className="h-10 w-full" />
                        ))}
                      </div>
                    ) : (
                      <ScrollArea className="h-64 rounded-md border">
                        <div className="p-2 space-y-2">
                          {displayCatalog.length === 0 ? (
                            <div className="text-sm text-muted-foreground p-4 text-center">
                              Catalog is empty. Please contact support to load additional accounts.
                            </div>
                          ) : (
                            displayCatalog.map((account) => {
                              const alreadyAdded = existingCodes.has(account.code);
                              const isSelected = selectedCatalogId === account.id;
                              return (
                                <button
                                  key={account.id}
                                  type="button"
                                  disabled={alreadyAdded}
                                  onClick={() => setSelectedCatalogId(account.id)}
                                  className={`w-full text-left rounded-md border px-3 py-2 transition-colors ${
                                    alreadyAdded
                                      ? 'cursor-not-allowed opacity-60'
                                      : 'hover:bg-muted/50'
                                  } ${isSelected ? 'border-primary bg-muted' : 'border-border'}`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <div className="font-mono text-xs text-muted-foreground">{account.code}</div>
                                      <div className="text-sm font-medium">
                                        {account.description}
                                      </div>
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {alreadyAdded ? 'Already in chart' : account.category}
                                    </div>
                                  </div>
                                </button>
                              );
                            })
                          )}
                        </div>
                      </ScrollArea>
                    )}
                  </div>

                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={() => selectedCatalogId && addMutation.mutate(selectedCatalogId)}
                      disabled={!selectedCatalog || addMutation.isPending}
                    >
                      {addMutation.isPending ? 'Adding...' : 'Add Account'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {accountsLoading ? (
            <div className="space-y-2">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-3 font-semibold">Code</th>
                    <th className="text-left p-3 font-semibold">Description</th>
                    <th className="text-left p-3 font-semibold">Type</th>
                    <th className="text-left p-3 font-semibold">Parent</th>
                    <th className="text-left p-3 font-semibold">Mapped</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAccounts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center p-6 text-muted-foreground">
                        No accounts found
                      </td>
                    </tr>
                  ) : (
                    filteredAccounts.map((account) => {
                      const parent = account.parent_id ? accountById.get(account.parent_id) : null;
                      return (
                        <tr
                          key={account.id}
                          className="border-t hover:bg-muted/50 transition-colors"
                        >
                          <td className="p-3 font-mono text-sm">{account.code}</td>
                          <td className="p-3">{account.description}</td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-1 rounded text-xs font-semibold ${account.type === 'H'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                                }`}
                            >
                              {account.type === 'H' ? 'Header' : 'Detail'}
                            </span>
                          </td>
                          <td className="p-3 font-mono text-sm text-muted-foreground">
                            {parent?.code || '-'}
                          </td>
                          <td className="p-3 text-sm">
                            {account.mapped_master_account_id ? (
                              <span className="text-green-600">✓</span>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
