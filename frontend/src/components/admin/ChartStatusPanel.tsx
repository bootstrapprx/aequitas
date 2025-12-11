import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { RefreshCw, AlertTriangle, CheckCircle, Database } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CompanyStatus {
  company_id: string;
  ucid: string;
  name: string;
  account_count: number;
  status: 'initialized' | 'not_initialized';
}

interface ChartStatus {
  master_chart: {
    loaded: boolean;
    account_count: number;
  };
  companies: {
    total: number;
    initialized: number;
    not_initialized: number;
    details: CompanyStatus[];
  };
}

export default function ChartStatusPanel() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'chart-status'],
    queryFn: async () => {
      const response = await api.get('/admin/chart-status');
      return response.data as ChartStatus;
    },
  });

  const migrateMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/admin/migrate-company-charts');
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: 'Migration Complete',
        description: `Migrated ${data.migrated} companies, skipped ${data.skipped}`,
      });
      refetch();
    },
    onError: (error: any) => {
      toast({
        title: 'Migration Failed',
        description: error.response?.data?.detail || 'Failed to migrate companies',
        variant: 'destructive',
      });
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart of Accounts Status</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!status) {
    return null;
  }

  const hasIssues = !status.master_chart.loaded || status.companies.not_initialized > 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chart of Accounts Status</CardTitle>
              <CardDescription>System-wide chart initialization status</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Master Chart Status */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Master Chart
            </h3>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <div className="font-medium">US-GAAP Master Chart</div>
                <div className="text-sm text-muted-foreground">
                  {status.master_chart.account_count} accounts
                </div>
              </div>
              {status.master_chart.loaded ? (
                <Badge variant="default" className="bg-green-500">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Loaded
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Not Loaded
                </Badge>
              )}
            </div>

            {!status.master_chart.loaded && (
              <Alert variant="destructive" className="mt-3">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Master Chart Not Loaded</AlertTitle>
                <AlertDescription>
                  The master chart must be seeded before companies can initialize their charts.
                  Run: <code className="bg-muted px-1 py-0.5 rounded">python -m app.data.seed_enriched_master_chart</code>
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Companies Status */}
          <div>
            <h3 className="font-semibold mb-3">Company Charts</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold">{status.companies.total}</div>
                <div className="text-sm text-muted-foreground">Total Companies</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600">
                  {status.companies.initialized}
                </div>
                <div className="text-sm text-muted-foreground">Initialized</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-600">
                  {status.companies.not_initialized}
                </div>
                <div className="text-sm text-muted-foreground">Not Initialized</div>
              </div>
            </div>
          </div>

          {/* Companies needing initialization */}
          {status.companies.not_initialized > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">Companies Needing Initialization</h3>
                <Button
                  onClick={() => migrateMutation.mutate()}
                  disabled={migrateMutation.isPending || !status.master_chart.loaded}
                  size="sm"
                >
                  {migrateMutation.isPending ? 'Migrating...' : 'Initialize All'}
                </Button>
              </div>

              {!status.master_chart.loaded && (
                <Alert className="mb-3">
                  <AlertDescription>
                    Cannot initialize companies until master chart is loaded.
                  </AlertDescription>
                </Alert>
              )}

              <div className="border rounded-lg divide-y">
                {status.companies.details
                  .filter((c) => c.status === 'not_initialized')
                  .map((company) => (
                    <div key={company.company_id} className="p-3 flex items-center justify-between">
                      <div>
                        <div className="font-medium">{company.name}</div>
                        <div className="text-sm text-muted-foreground">UCID: {company.ucid}</div>
                      </div>
                      <Badge variant="outline">No Accounts</Badge>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Success message */}
          {!hasIssues && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>All Systems Operational</AlertTitle>
              <AlertDescription>
                Master chart is loaded and all companies have their charts initialized.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
