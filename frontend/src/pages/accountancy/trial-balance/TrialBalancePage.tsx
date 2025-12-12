import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Scale, Download, Calendar, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  PageHeader,
  AtheneumCard,
  AtheneumCardHeader,
  AtheneumCardContent,
  ScrollUnfurl,
} from '@/components/athenaeum';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { TrialBalanceTable } from '@/components/accounting/TrialBalanceTable';
import { useTrialBalance, useFiscalPeriods } from '@/hooks/useAccounting';
import { useAuth } from '@/contexts/AuthContext';

const TrialBalancePage = () => {
  const { currentCompanyId } = useAuth();
  const [selectedPeriodId, setSelectedPeriodId] = useState<string>('');
  const [asOfDate, setAsOfDate] = useState<string>('');
  const [viewMode, setViewMode] = useState<'period' | 'date'>('period');

  // Fetch fiscal periods
  const { data: fiscalPeriods = [], isLoading: periodsLoading } =
    useFiscalPeriods(currentCompanyId || undefined);

  // Determine query options based on view mode
  const trialBalanceOptions = useMemo(() => {
    if (viewMode === 'period' && selectedPeriodId) {
      return { fiscal_period_id: selectedPeriodId };
    } else if (viewMode === 'date' && asOfDate) {
      return { as_of_date: asOfDate };
    }
    return undefined;
  }, [viewMode, selectedPeriodId, asOfDate]);

  // Fetch trial balance
  const {
    data: trialBalance,
    isLoading: trialBalanceLoading,
    error: trialBalanceError,
  } = useTrialBalance(currentCompanyId || undefined, trialBalanceOptions);

  const handleExport = () => {
    if (!trialBalance) {
      toast.error('No trial balance data to export');
      return;
    }

    // Create CSV content
    const headers = ['Account Code', 'Account Name', 'Type', 'Category', 'Debit', 'Credit'];
    const rows = trialBalance.accounts.map((account) => [
      account.account_code,
      account.account_description,
      account.account_type,
      account.category,
      account.debit_balance.toFixed(2),
      account.credit_balance.toFixed(2),
    ]);
    rows.push([
      '',
      '',
      '',
      'TOTALS',
      trialBalance.total_debits.toFixed(2),
      trialBalance.total_credits.toFixed(2),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trial-balance-${trialBalance.period_end}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success('Trial balance exported successfully');
  };

  const isLoading = periodsLoading || trialBalanceLoading;
  const showTrialBalance = trialBalance && !isLoading;

  return (
    <div className="p-10 space-y-8">
      {/* Header - Using Athenaeum PageHeader */}
      <PageHeader
        title="Hall of Balance"
        subtitle="Weigh the ancient scales of debits and credits"
        icon={Scale}
        actions={
          showTrialBalance && (
            <Button onClick={handleExport} variant="outline" className="shadow-gold">
              <Download className="w-4 h-4 mr-2" />
              Export to CSV
            </Button>
          )
        }
      />

      {/* Report Parameters - Using Athenaeum Card */}
      <AtheneumCard hover>
        <AtheneumCardHeader icon={<Calendar className="w-5 h-5" />}>
          Report Parameters
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Select a fiscal period or specify a date to generate the trial balance
          </p>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>View Mode</Label>
                <Select
                  value={viewMode}
                  onValueChange={(value: 'period' | 'date') => {
                    setViewMode(value);
                    setSelectedPeriodId('');
                    setAsOfDate('');
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="period">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-2" />
                        By Fiscal Period
                      </div>
                    </SelectItem>
                    <SelectItem value="date">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-2" />
                        By Specific Date
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {viewMode === 'period' ? (
                <div className="space-y-2">
                  <Label>Fiscal Period</Label>
                  <Select
                    value={selectedPeriodId}
                    onValueChange={setSelectedPeriodId}
                    disabled={periodsLoading}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a fiscal period" />
                    </SelectTrigger>
                    <SelectContent>
                      {fiscalPeriods.length === 0 ? (
                        <SelectItem value="none" disabled>
                          No fiscal periods available
                        </SelectItem>
                      ) : (
                        fiscalPeriods.map((period: any) => (
                          <SelectItem key={period.id} value={period.id}>
                            {period.period_number} ({period.start_date} to {period.end_date})
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div className="space-y-2">
                  <Label>As of Date</Label>
                  <Input
                    type="date"
                    value={asOfDate}
                    onChange={(e) => setAsOfDate(e.target.value)}
                    placeholder="Select a date"
                  />
                </div>
              )}
            </div>

            {fiscalPeriods.length === 0 && !periodsLoading && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>No Fiscal Periods</AlertTitle>
                <AlertDescription>
                  You need to create fiscal periods before generating a trial balance. Go to
                  the Fiscal Periods page to create them.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {trialBalanceError && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              Failed to load trial balance. Please try again.
            </AlertDescription>
          </Alert>
        </motion.div>
      )}

      {isLoading && (
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 py-16">
              <Scale className="h-12 w-12 animate-pulse-glow text-primary" />
              <p className="text-muted-foreground">Loading trial balance...</p>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      )}

      {showTrialBalance && (
        <ScrollUnfurl
          title="Trial Balance"
          subtitle={`Period: ${trialBalance.period_start} to ${trialBalance.period_end}`}
        >
          <TrialBalanceTable trialBalance={trialBalance} />
        </ScrollUnfurl>
      )}

      {!isLoading && !trialBalance && !trialBalanceError && (
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <Scale className="h-16 w-16 text-muted-foreground" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Trial Balance Selected</h3>
                <p className="text-muted-foreground">
                  Select a fiscal period or date above to generate the trial balance report
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      )}
    </div>
  );
};

export default TrialBalancePage;
