import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { api, ApiError } from '@/lib/api';
import { RefreshCw, AlertTriangle, CheckCircle, Database } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CompanyStatus {
  company_id: string;
  ucid: string;
  name: string;
  status: 'kernel_compliant' | 'missing_kernel';
  missing_kernel_codes: string[];
}

interface ChartStatus {
  catalog: {
    loaded: boolean;
    account_count: number;
  };
  kernel: {
    required_count: number;
    required_codes: string[];
  };
  companies: {
    total: number;
    kernel_compliant: number;
    kernel_missing: number;
    details: CompanyStatus[];
  };
}

export default function ChartStatusPanel() {
  const { toast } = useToast();

  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'chart-status'],
    queryFn: async () => {
      return api.get<ChartStatus>('/admin/chart-status');
    },
  });

  const migrateMutation = useMutation({
    mutationFn: async () => {
      return api.post('/admin/migrate-company-charts', {});
    },
    onSuccess: (data: any) => {
      toast({
        title: 'Kernel Accounts Remediated',
        description: `Updated ${data.remediated} companies, skipped ${data.skipped}`,
      });
      refetch();
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError
        ? error.getUserMessage()
        : error instanceof Error
          ? error.message
          : 'Failed to remediate kernel accounts';
      toast({
        title: 'Remediation Failed',
        description: message,
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

  const hasIssues = status.companies.kernel_missing > 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chart of Accounts Status</CardTitle>
              <CardDescription>Kernel compliance and catalog availability</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Kernel Status */}
          <div>
            <h3 className="font-semibold mb-3">Kernel Accounts</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold">{status.kernel.required_count}</div>
                <div className="text-sm text-muted-foreground">Required L0 Codes</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600">
                  {status.companies.kernel_compliant}
                </div>
                <div className="text-sm text-muted-foreground">Kernel Compliant</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-600">
                  {status.companies.kernel_missing}
                </div>
                <div className="text-sm text-muted-foreground">Missing Kernel</div>
              </div>
            </div>
          </div>

          {/* Catalog Status */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Account Catalog (Optional)
            </h3>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <div className="font-medium">Master Chart Catalog</div>
                <div className="text-sm text-muted-foreground">
                  {status.catalog.account_count} accounts
                </div>
              </div>
              {status.catalog.loaded ? (
                <Badge variant="default" className="bg-green-500">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Available
                </Badge>
              ) : (
                <Badge variant="secondary">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Not Loaded
                </Badge>
              )}
            </div>

            {!status.catalog.loaded && (
              <Alert className="mt-3">
                <AlertTitle>Catalog Optional</AlertTitle>
                <AlertDescription>
                  The catalog is only needed when adding new accounts. You can import it later if desired.
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Companies needing kernel remediation */}
          {status.companies.kernel_missing > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">Companies Missing Kernel Accounts</h3>
                <Button
                  onClick={() => migrateMutation.mutate()}
                  disabled={migrateMutation.isPending}
                  size="sm"
                >
                  {migrateMutation.isPending ? 'Remediating...' : 'Add Missing Kernel Accounts'}
                </Button>
              </div>

              <div className="border rounded-lg divide-y">
                {status.companies.details
                  .filter((c) => c.status === 'missing_kernel')
                  .map((company) => (
                    <div key={company.company_id} className="p-3 flex items-center justify-between">
                      <div>
                        <div className="font-medium">{company.name}</div>
                        <div className="text-sm text-muted-foreground">UCID: {company.ucid}</div>
                        {company.missing_kernel_codes.length > 0 && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Missing: {company.missing_kernel_codes.slice(0, 6).join(', ')}
                            {company.missing_kernel_codes.length > 6 ? '...' : ''}
                          </div>
                        )}
                      </div>
                      <Badge variant="outline">Kernel Missing</Badge>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Success message */}
          {!hasIssues && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Kernel Ready</AlertTitle>
              <AlertDescription>
                All active companies have required kernel accounts. You can add accounts from the catalog as needed.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
