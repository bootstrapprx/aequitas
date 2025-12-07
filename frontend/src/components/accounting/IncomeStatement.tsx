import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { IncomeStatement as IncomeStatementType } from '@/types/accounting';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface IncomeStatementProps {
  incomeStatement: IncomeStatementType;
}

export function IncomeStatement({ incomeStatement }: IncomeStatementProps) {
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

  const formatPercentage = (value?: number) => {
    if (value === undefined || value === null) return '';
    return `${(value * 100).toFixed(1)}%`;
  };

  const renderSection = (
    title: string,
    section: IncomeStatementType['revenue'],
    total?: number
  ) => {
    if (section.accounts.length === 0) return null;

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
        {total !== undefined && (
          <div className="border-t pt-2 flex justify-between font-bold">
            <span>Total {title}</span>
            <span className="font-mono">{formatCurrency(total)}</span>
          </div>
        )}
      </div>
    );
  };

  const isProfit = incomeStatement.net_income >= 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <CardTitle className="text-2xl mb-1">{incomeStatement.company_name}</CardTitle>
            <h2 className="text-xl font-semibold">Income Statement</h2>
            <p className="text-sm text-muted-foreground mt-1">
              For the period {formatDate(incomeStatement.period_start)} to{' '}
              {formatDate(incomeStatement.period_end)}
            </p>
          </div>
          <div>
            {isProfit ? (
              <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                <TrendingUp className="w-3 h-3 mr-1" />
                Profit
              </Badge>
            ) : (
              <Badge variant="destructive">
                <TrendingDown className="w-3 h-3 mr-1" />
                Loss
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Revenue Section */}
          {renderSection('Revenue', incomeStatement.revenue, incomeStatement.total_revenue)}

          {/* Cost of Goods Sold Section */}
          {incomeStatement.cost_of_goods_sold.accounts.length > 0 && (
            <>
              {renderSection(
                'Cost of Goods Sold',
                incomeStatement.cost_of_goods_sold,
                incomeStatement.total_cogs
              )}

              {/* Gross Profit */}
              <div className="border-t-2 border-gray-400 pt-2 flex justify-between font-bold text-base bg-muted/30 p-2 rounded">
                <span>Gross Profit</span>
                <div className="text-right">
                  <span className="font-mono mr-3">{formatCurrency(incomeStatement.gross_profit)}</span>
                  {incomeStatement.gross_profit_margin !== undefined && (
                    <span className="text-sm text-muted-foreground">
                      ({formatPercentage(incomeStatement.gross_profit_margin)})
                    </span>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Expenses Section */}
          {renderSection('Operating Expenses', incomeStatement.expenses, incomeStatement.total_expenses)}

          {/* Other Income Section */}
          {incomeStatement.other_income.accounts.length > 0 &&
            renderSection(
              'Other Income',
              incomeStatement.other_income,
              incomeStatement.total_other_income
            )}

          {/* Net Income */}
          <div className="border-t-4 border-primary pt-4 mt-6">
            <div
              className={`flex justify-between items-center font-bold text-lg p-3 rounded ${
                isProfit
                  ? 'bg-green-50 dark:bg-green-900/20'
                  : 'bg-red-50 dark:bg-red-900/20'
              }`}
            >
              <span className={isProfit ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}>
                Net {isProfit ? 'Income' : 'Loss'}
              </span>
              <div className="text-right">
                <span className={`font-mono ${isProfit ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                  {formatCurrency(Math.abs(incomeStatement.net_income))}
                </span>
                {incomeStatement.net_profit_margin !== undefined && (
                  <span className={`ml-3 text-sm ${isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    ({formatPercentage(incomeStatement.net_profit_margin)})
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
