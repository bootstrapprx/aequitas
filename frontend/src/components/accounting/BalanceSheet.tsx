import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { BalanceSheet as BalanceSheetType } from '@/types/accounting';
import { CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface BalanceSheetProps {
  balanceSheet: BalanceSheetType;
}

export function BalanceSheet({ balanceSheet }: BalanceSheetProps) {
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

  const renderSection = (
    title: string,
    section: BalanceSheetType['assets'],
    total: number
  ) => {
    return (
      <div className="space-y-2">
        <h3 className="font-bold text-lg uppercase tracking-wide border-b-2 border-primary pb-2">
          {title}
        </h3>
        <div className="space-y-1">
          {section.accounts.map((account, index) => (
            <div
              key={`${account.code}-${index}`}
              className={`flex justify-between py-1 ${
                account.is_header ? 'font-semibold mt-3' : 'pl-6'
              }`}
              style={{ paddingLeft: account.is_header ? '0' : `${account.level * 1.5}rem` }}
            >
              <span className={account.is_header ? 'text-base' : 'text-sm'}>
                {account.code && !account.is_header && (
                  <span className="font-mono text-xs text-muted-foreground mr-2">
                    {account.code}
                  </span>
                )}
                {account.description}
              </span>
              <span className={`font-mono ${account.is_header ? 'font-semibold' : ''}`}>
                {account.amount !== 0 && formatCurrency(account.amount)}
              </span>
            </div>
          ))}
        </div>
        <div className="border-t-2 border-gray-400 mt-3 pt-2 flex justify-between font-bold text-base">
          <span>Total {title}</span>
          <span className="font-mono">{formatCurrency(total)}</span>
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <CardTitle className="text-2xl mb-1">{balanceSheet.company_name}</CardTitle>
            <h2 className="text-xl font-semibold">Balance Sheet</h2>
            <p className="text-sm text-muted-foreground mt-1">
              As of {formatDate(balanceSheet.as_of_date)}
            </p>
          </div>
          <div>
            {balanceSheet.is_balanced ? (
              <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                <CheckCircle className="w-3 h-3 mr-1" />
                Balanced
              </Badge>
            ) : (
              <Badge variant="destructive">
                <XCircle className="w-3 h-3 mr-1" />
                Out of Balance
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          {/* Assets Section */}
          {renderSection('Assets', balanceSheet.assets, balanceSheet.total_assets)}

          {/* Liabilities Section */}
          {renderSection('Liabilities', balanceSheet.liabilities, balanceSheet.total_liabilities)}

          {/* Equity Section */}
          {renderSection('Equity', balanceSheet.equity, balanceSheet.total_equity)}

          {/* Balance Check */}
          <div className="border-t-4 border-primary pt-4 mt-6">
            <div className="flex justify-between items-center font-bold text-lg bg-muted/50 p-3 rounded">
              <span>Total Liabilities & Equity</span>
              <span className="font-mono">
                {formatCurrency(balanceSheet.total_liabilities + balanceSheet.total_equity)}
              </span>
            </div>
            {balanceSheet.is_balanced && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-2 text-center">
                Assets = Liabilities + Equity ({formatCurrency(balanceSheet.total_assets)})
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
