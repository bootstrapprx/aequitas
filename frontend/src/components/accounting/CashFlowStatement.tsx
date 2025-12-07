import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { CashFlowStatement as CashFlowStatementType } from '@/types/accounting';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CashFlowStatementProps {
  cashFlowStatement: CashFlowStatementType;
}

export function CashFlowStatement({ cashFlowStatement }: CashFlowStatementProps) {
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
    section: CashFlowStatementType['operating_activities'],
    netTotal: number
  ) => {
    return (
      <div className="space-y-2">
        <h3 className="font-bold text-base uppercase tracking-wide text-muted-foreground">
          {title}
        </h3>
        <div className="space-y-1">
          {section.accounts.map((account, index) => (
            <div
              key={`${account.code}-${index}`}
              className={`flex justify-between py-1 ${
                account.is_header ? 'font-semibold mt-2' : 'pl-6'
              }`}
              style={{ paddingLeft: account.is_header ? '0' : `${account.level * 1.5}rem` }}
            >
              <span className={account.is_header ? 'text-sm' : 'text-sm'}>
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
        <div className="border-t-2 border-gray-400 pt-2 flex justify-between font-bold">
          <span>Net Cash from {title}</span>
          <span className={`font-mono ${netTotal >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
            {formatCurrency(netTotal)}
          </span>
        </div>
      </div>
    );
  };

  const cashChange = cashFlowStatement.net_change_in_cash;
  const isPositive = cashChange >= 0;
  const isNeutral = Math.abs(cashChange) < 0.01;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <CardTitle className="text-2xl mb-1">{cashFlowStatement.company_name}</CardTitle>
            <h2 className="text-xl font-semibold">Cash Flow Statement</h2>
            <p className="text-sm text-muted-foreground mt-1">
              For the period {formatDate(cashFlowStatement.period_start)} to{' '}
              {formatDate(cashFlowStatement.period_end)}
            </p>
          </div>
          <div>
            {isNeutral ? (
              <Badge variant="outline">
                <Minus className="w-3 h-3 mr-1" />
                Neutral
              </Badge>
            ) : isPositive ? (
              <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                <TrendingUp className="w-3 h-3 mr-1" />
                Cash Increase
              </Badge>
            ) : (
              <Badge variant="destructive">
                <TrendingDown className="w-3 h-3 mr-1" />
                Cash Decrease
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Operating Activities */}
          {renderSection(
            'Operating Activities',
            cashFlowStatement.operating_activities,
            cashFlowStatement.net_cash_from_operations
          )}

          {/* Investing Activities */}
          {renderSection(
            'Investing Activities',
            cashFlowStatement.investing_activities,
            cashFlowStatement.net_cash_from_investing
          )}

          {/* Financing Activities */}
          {renderSection(
            'Financing Activities',
            cashFlowStatement.financing_activities,
            cashFlowStatement.net_cash_from_financing
          )}

          {/* Net Change in Cash */}
          <div className="border-t-4 border-primary pt-4 mt-6 space-y-3">
            <div
              className={`flex justify-between items-center font-bold text-base p-3 rounded ${
                isPositive
                  ? 'bg-green-50 dark:bg-green-900/20'
                  : isNeutral
                  ? 'bg-gray-50 dark:bg-gray-900/20'
                  : 'bg-red-50 dark:bg-red-900/20'
              }`}
            >
              <span className={isPositive ? 'text-green-800 dark:text-green-200' : isNeutral ? '' : 'text-red-800 dark:text-red-200'}>
                Net {isPositive ? 'Increase' : isNeutral ? 'Change' : 'Decrease'} in Cash
              </span>
              <span className={`font-mono ${isPositive ? 'text-green-800 dark:text-green-200' : isNeutral ? '' : 'text-red-800 dark:text-red-200'}`}>
                {formatCurrency(cashChange)}
              </span>
            </div>

            {/* Cash Reconciliation */}
            <div className="bg-muted/30 p-3 rounded space-y-2">
              <div className="flex justify-between text-sm">
                <span>Beginning Cash Balance</span>
                <span className="font-mono">{formatCurrency(cashFlowStatement.beginning_cash_balance)}</span>
              </div>
              <div className="flex justify-between text-sm border-t pt-2">
                <span>Net Change in Cash</span>
                <span className="font-mono">{formatCurrency(cashChange)}</span>
              </div>
              <div className="flex justify-between font-bold text-base border-t-2 border-primary pt-2">
                <span>Ending Cash Balance</span>
                <span className="font-mono">{formatCurrency(cashFlowStatement.ending_cash_balance)}</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
