import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { TrialBalance } from '@/types/accounting';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface TrialBalanceTableProps {
  trialBalance: TrialBalance;
}

export function TrialBalanceTable({ trialBalance }: TrialBalanceTableProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Trial Balance</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Period: {formatDate(trialBalance.period_start)} to{' '}
              {formatDate(trialBalance.period_end)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {trialBalance.is_balanced ? (
              <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                <CheckCircle className="w-3 h-3 mr-1" />
                Balanced
              </Badge>
            ) : (
              <Badge variant="destructive">
                <XCircle className="w-3 h-3 mr-1" />
                Out of Balance (${Math.abs(trialBalance.variance).toFixed(2)})
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Warning Banner for Unbalanced Trial Balance */}
        {!trialBalance.is_balanced && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Trial Balance is Out of Balance</AlertTitle>
            <AlertDescription>
              Total debits ({formatCurrency(trialBalance.total_debits)}) do not equal total
              credits ({formatCurrency(trialBalance.total_credits)}). The variance is{' '}
              {formatCurrency(Math.abs(trialBalance.variance))}. Please review journal entries
              for errors.
            </AlertDescription>
          </Alert>
        )}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Account Code</TableHead>
                <TableHead>Account Name</TableHead>
                <TableHead className="w-[150px]">Type</TableHead>
                <TableHead className="w-[150px]">Category</TableHead>
                <TableHead className="text-right w-[150px]">Debit</TableHead>
                <TableHead className="text-right w-[150px]">Credit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trialBalance.accounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No accounts with balances for this period
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {trialBalance.accounts.map((account) => (
                    <TableRow key={account.account_code}>
                      <TableCell className="font-mono font-medium">
                        {account.account_code}
                      </TableCell>
                      <TableCell>{account.account_description}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {account.account_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {account.category}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {account.debit_balance > 0
                          ? formatCurrency(account.debit_balance)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {account.credit_balance > 0
                          ? formatCurrency(account.credit_balance)
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="border-t-2 font-bold bg-muted/50">
                    <TableCell colSpan={4} className="text-right">
                      TOTALS:
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(trialBalance.total_debits)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(trialBalance.total_credits)}
                    </TableCell>
                  </TableRow>
                  {!trialBalance.is_balanced && (
                    <TableRow className="bg-red-50 dark:bg-red-900/20">
                      <TableCell colSpan={4} className="text-right text-red-600 dark:text-red-400">
                        Variance:
                      </TableCell>
                      <TableCell
                        colSpan={2}
                        className="text-right font-mono text-red-600 dark:text-red-400 font-bold"
                      >
                        {formatCurrency(Math.abs(trialBalance.variance))}
                      </TableCell>
                    </TableRow>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
