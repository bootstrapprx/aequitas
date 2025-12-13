import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Scroll, Download, AlertCircle, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

import {
  PageHeader,
  AtheneumCard,
  AtheneumCardHeader,
  AtheneumCardContent,
  ScrollUnfurl,
} from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAccountLedger, useCompanyAccounts } from '@/hooks/useAccounting';
import { useCompany } from '@/contexts/CompanyContext';
import type { AccountLedger, LedgerEntry } from '@/types/accounting';

const DailyLedgerPage = () => {
  const { selectedCompanyId } = useCompany();
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Fetch company accounts for the selector
  const { data: companyAccounts = [], isLoading: accountsLoading } = useCompanyAccounts(
    selectedCompanyId || undefined
  );

  // Fetch account ledger
  const {
    data: ledger,
    isLoading: ledgerLoading,
    error: ledgerError,
  } = useAccountLedger(selectedCompanyId || undefined, selectedAccountId, {
    start_date: startDate,
    end_date: endDate,
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleExport = () => {
    if (!ledger) {
      toast.error('No ledger data to export');
      return;
    }

    // Create CSV content
    const headers = ['Date', 'Entry #', 'Description', 'Reference', 'Debit', 'Credit', 'Balance'];
    const rows = ledger.entries.map((entry: LedgerEntry) => [
      entry.entry_date,
      entry.entry_number,
      entry.description,
      entry.reference || '',
      entry.debit_amount > 0 ? entry.debit_amount.toFixed(2) : '',
      entry.credit_amount > 0 ? entry.credit_amount.toFixed(2) : '',
      entry.running_balance.toFixed(2),
    ]);

    const csvContent = [
      `"${ledger.account_code} - ${ledger.account_description}"`,
      `"Date Range: ${startDate || 'All'} to ${endDate || 'All'}"`,
      `"Beginning Balance: ${ledger.beginning_balance.toFixed(2)}"`,
      '',
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
      '',
      `"Ending Balance: ${ledger.ending_balance.toFixed(2)}"`,
      `"Total Debits: ${ledger.total_debits.toFixed(2)}"`,
      `"Total Credits: ${ledger.total_credits.toFixed(2)}"`,
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ledger-${ledger.account_code}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success('Ledger exported successfully');
  };

  const isLoading = accountsLoading || ledgerLoading;
  const showLedger = ledger && !isLoading;

  // Empty state when no company is selected
  if (!selectedCompanyId) {
    return (
      <div className="p-10 space-y-8">
        <PageHeader
          title="Ledger of Days"
          subtitle="Chronicle the daily transactions in the grand book of accounts"
          icon={Scroll}
        />
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <Scroll className="h-16 w-16 text-muted-foreground opacity-50" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Company Selected</h3>
                <p className="text-muted-foreground">
                  Please select a company from the dropdown above to view account ledgers.
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      </div>
    );
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header - Using Athenaeum PageHeader */}
      <PageHeader
        title="Ledger of Days"
        subtitle="Chronicle the daily transactions in the grand book of accounts"
        icon={Scroll}
        actions={
          showLedger && (
            <Button onClick={handleExport} variant="outline" className="shadow-gold">
              <Download className="w-4 h-4 mr-2" />
              Export to CSV
            </Button>
          )
        }
      />

      {/* Account Selection - Using Athenaeum Card */}
      <AtheneumCard hover>
        <AtheneumCardHeader icon={<BookOpen className="w-5 h-5" />}>
          Ledger Parameters
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Select an account and optional date range to view the ledger entries
          </p>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Label>Account</Label>
                <Select
                  value={selectedAccountId}
                  onValueChange={setSelectedAccountId}
                  disabled={accountsLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an account" />
                  </SelectTrigger>
                  <SelectContent>
                    {companyAccounts.length === 0 ? (
                      <SelectItem value="none" disabled>
                        No accounts available
                      </SelectItem>
                    ) : (
                      companyAccounts.map((account: any) => (
                        <SelectItem key={account.id} value={account.id}>
                          {account.account_code} - {account.account_description}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Start Date (Optional)</Label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="Start date"
                />
              </div>

              <div className="space-y-2">
                <Label>End Date (Optional)</Label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="End date"
                />
              </div>
            </div>

            {companyAccounts.length === 0 && !accountsLoading && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>No Accounts</AlertTitle>
                <AlertDescription>
                  You need to set up your chart of accounts before viewing ledgers.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {ledgerError && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>Failed to load ledger. Please try again.</AlertDescription>
          </Alert>
        </motion.div>
      )}

      {isLoading && (
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 py-16">
              <Scroll className="h-12 w-12 animate-pulse-glow text-primary" />
              <p className="text-muted-foreground">Loading ledger...</p>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      )}

      {showLedger && (
        <ScrollUnfurl
          title={`${ledger.account_code} - ${ledger.account_description}`}
          subtitle={`Normal Balance: ${ledger.normal_balance}`}
        >
          <AtheneumCard>
            <AtheneumCardContent>
              {/* Summary Section */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-muted/30 rounded-lg">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Beginning Balance
                  </p>
                  <p className="text-lg font-mono font-semibold">
                    {formatCurrency(ledger.beginning_balance)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Total Debits
                  </p>
                  <p className="text-lg font-mono font-semibold text-green-700 dark:text-green-400">
                    {formatCurrency(ledger.total_debits)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Total Credits
                  </p>
                  <p className="text-lg font-mono font-semibold text-red-700 dark:text-red-400">
                    {formatCurrency(ledger.total_credits)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Ending Balance
                  </p>
                  <p className="text-lg font-mono font-semibold">
                    {formatCurrency(ledger.ending_balance)}
                  </p>
                </div>
              </div>

              {/* Ledger Entries Table */}
              {ledger.entries.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Scroll className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No ledger entries found for the selected criteria</p>
                </div>
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader className="sticky top-0 bg-background">
                      <TableRow>
                        <TableHead className="w-[110px]">Date</TableHead>
                        <TableHead className="w-[110px]">Entry #</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="w-[120px]">Reference</TableHead>
                        <TableHead className="text-right w-[130px]">Debit</TableHead>
                        <TableHead className="text-right w-[130px]">Credit</TableHead>
                        <TableHead className="text-right w-[150px]">Balance</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {ledger.entries.map((entry: LedgerEntry, index: number) => (
                        <TableRow key={`${entry.journal_entry_line_id}-${index}`}>
                          <TableCell className="font-mono text-sm">
                            {formatDate(entry.entry_date)}
                          </TableCell>
                          <TableCell className="font-mono text-sm text-muted-foreground">
                            {entry.entry_number}
                          </TableCell>
                          <TableCell className="max-w-xs">{entry.description}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {entry.reference || '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            {entry.debit_amount > 0 ? formatCurrency(entry.debit_amount) : '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            {entry.credit_amount > 0 ? formatCurrency(entry.credit_amount) : '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono font-semibold">
                            {formatCurrency(entry.running_balance)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </AtheneumCardContent>
          </AtheneumCard>
        </ScrollUnfurl>
      )}

      {!isLoading && !ledger && !ledgerError && (
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <Scroll className="h-16 w-16 text-muted-foreground" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Account Selected</h3>
                <p className="text-muted-foreground">
                  Select an account above to view its ledger entries
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      )}
    </div>
  );
};

export default DailyLedgerPage;
