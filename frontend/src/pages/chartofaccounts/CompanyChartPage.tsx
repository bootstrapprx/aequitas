import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { Search, Plus, RefreshCw, FileText, Lock, Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { Company } from '@/types/company';

interface CompanyAccount {
  id: string;
  code: string;
  description: string;
  type: string;
  parent_code: string | null;
  name: string | null;
  currency: string;
  is_active: boolean;
  master_account_code: string | null;
}

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
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);

  // Get companies
  const { data: companies } = useQuery<Company[]>({
    queryKey: ['companies'],
    queryFn: async () => {
      const response = await api.get<Company[]>('/companies/');
      return response.data;
    },
  });
  const selectedCompanyData = companies?.find((company) => company.id === selectedCompanyId);
  const isActiveCompany = selectedCompanyData?.onboarding_status === 'ACTIVE' || selectedCompanyData?.is_active;

  // Auto-select first company
  React.useEffect(() => {
    if (companies && companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  // Get company chart
  const {
    data: accounts,
    isLoading: accountsLoading,
    refetch: refetchAccounts,
  } = useQuery({
    queryKey: ['company-chart', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const response = await api.get(`/companies/${selectedCompanyId}/chart`);
      return response.data as CompanyAccount[];
    },
    enabled: !!selectedCompanyId,
  });

  // Get company chart stats
  const { data: stats } = useQuery({
    queryKey: ['company-chart-stats', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return null;
      const response = await api.get(`/companies/${selectedCompanyId}/chart/stats`);
      return response.data as CompanyChartStats;
    },
    enabled: !!selectedCompanyId,
  });

  const filteredAccounts = React.useMemo(() => {
    if (!accounts) return [];
    if (!search) return accounts;

    const searchLower = search.toLowerCase();
    return accounts.filter(
      (acc) =>
        acc.code.toLowerCase().includes(searchLower) ||
        acc.description.toLowerCase().includes(searchLower)
    );
  }, [accounts, search]);

  const handleReset = async () => {
    if (!selectedCompanyId) return;
    if (!confirm('Are you sure you want to reset the chart of accounts to the master chart? This will deactivate all existing accounts and create new ones.')) {
      return;
    }

    try {
      await api.post(`/companies/${selectedCompanyId}/chart/reset`);
      refetchAccounts();
    } catch (error) {
      console.error('Failed to reset chart:', error);
    }
  };

  if (!companies || companies.length === 0) {
    return (
      <div className="p-6">
        <Alert>
          <AlertDescription>
            No companies found. Please create a company first.
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

      {/* Company Selector */}
      {companies && companies.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Company</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              className="w-full p-2 border rounded"
              value={selectedCompanyId || ''}
              onChange={(e) => setSelectedCompanyId(e.target.value)}
            >
              {companies.map((company: any) => (
                <option key={company.id} value={company.id}>
                  {company.name} ({company.ucid})
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
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
              <CardDescription>Mapped to Master</CardDescription>
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
              <Button variant="outline" size="sm" onClick={handleReset}>
                <FileText className="h-4 w-4 mr-2" />
                Reset to Master
              </Button>
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
                    filteredAccounts.map((account) => (
                      <tr
                        key={account.id}
                        className="border-t hover:bg-muted/50 transition-colors"
                      >
                        <td className="p-3 font-mono text-sm">{account.code}</td>
                        <td className="p-3">{account.description}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              account.type === 'H'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {account.type === 'H' ? 'Header' : 'Detail'}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-sm text-muted-foreground">
                          {account.parent_code || '-'}
                        </td>
                        <td className="p-3 text-sm">
                          {account.master_account_code ? (
                            <span className="text-green-600">✓ {account.master_account_code}</span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                      </tr>
                    ))
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
