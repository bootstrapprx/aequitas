import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FileSpreadsheet, Download, Calendar, AlertCircle, Scroll } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { PageHeader, ScrollUnfurl, AtheneumCard, AtheneumCardHeader, AtheneumCardContent } from '@/components/athenaeum';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { BalanceSheet } from '@/components/accounting/BalanceSheet';
import { IncomeStatement } from '@/components/accounting/IncomeStatement';
import { CashFlowStatement } from '@/components/accounting/CashFlowStatement';
import {
  useBalanceSheet,
  useIncomeStatement,
  useCashFlowStatement,
} from '@/hooks/useAccounting';
import { useCompany } from '@/contexts/CompanyContext';

const FinancialStatementsPage = () => {
  const { selectedCompanyId } = useCompany();
  const [activeTab, setActiveTab] = useState<'balance-sheet' | 'income-statement' | 'cash-flow'>(
    'balance-sheet'
  );

  // For Balance Sheet - single date
  const [balanceSheetDate, setBalanceSheetDate] = useState<string>('');

  // For Income Statement and Cash Flow - date range
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Fetch data
  const {
    data: balanceSheet,
    isLoading: balanceSheetLoading,
    error: balanceSheetError,
  } = useBalanceSheet(selectedCompanyId || undefined, balanceSheetDate);

  const {
    data: incomeStatement,
    isLoading: incomeStatementLoading,
    error: incomeStatementError,
  } = useIncomeStatement(selectedCompanyId || undefined, startDate, endDate);

  const {
    data: cashFlowStatement,
    isLoading: cashFlowLoading,
    error: cashFlowError,
  } = useCashFlowStatement(selectedCompanyId || undefined, startDate, endDate);

  const handleExportBalanceSheet = () => {
    if (!balanceSheet) {
      toast.error('No balance sheet data to export');
      return;
    }

    // Create CSV content
    const headers = ['Account Code', 'Account Description', 'Amount'];
    const rows: string[][] = [];

    // Assets
    rows.push(['', 'ASSETS', '']);
    balanceSheet.assets.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Total Assets', balanceSheet.total_assets.toFixed(2)]);
    rows.push(['', '', '']);

    // Liabilities
    rows.push(['', 'LIABILITIES', '']);
    balanceSheet.liabilities.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Total Liabilities', balanceSheet.total_liabilities.toFixed(2)]);
    rows.push(['', '', '']);

    // Equity
    rows.push(['', 'EQUITY', '']);
    balanceSheet.equity.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Total Equity', balanceSheet.total_equity.toFixed(2)]);

    const csvContent = [
      `"${balanceSheet.company_name}"`,
      '"Balance Sheet"',
      `"As of ${balanceSheet.as_of_date}"`,
      '',
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    downloadFile(csvContent, `balance-sheet-${balanceSheet.as_of_date}.csv`);
    toast.success('Balance sheet exported successfully');
  };

  const handleExportIncomeStatement = () => {
    if (!incomeStatement) {
      toast.error('No income statement data to export');
      return;
    }

    const headers = ['Account Code', 'Account Description', 'Amount'];
    const rows: string[][] = [];

    // Revenue
    rows.push(['', 'REVENUE', '']);
    incomeStatement.revenue.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Total Revenue', incomeStatement.total_revenue.toFixed(2)]);
    rows.push(['', '', '']);

    // COGS
    if (incomeStatement.cost_of_goods_sold.accounts.length > 0) {
      rows.push(['', 'COST OF GOODS SOLD', '']);
      incomeStatement.cost_of_goods_sold.accounts.forEach((account) => {
        rows.push([account.code, account.description, account.amount.toFixed(2)]);
      });
      rows.push(['', 'Total COGS', incomeStatement.total_cogs.toFixed(2)]);
      rows.push(['', 'Gross Profit', incomeStatement.gross_profit.toFixed(2)]);
      rows.push(['', '', '']);
    }

    // Expenses
    rows.push(['', 'OPERATING EXPENSES', '']);
    incomeStatement.expenses.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Total Expenses', incomeStatement.total_expenses.toFixed(2)]);
    rows.push(['', '', '']);

    // Other Income
    if (incomeStatement.other_income.accounts.length > 0) {
      rows.push(['', 'OTHER INCOME', '']);
      incomeStatement.other_income.accounts.forEach((account) => {
        rows.push([account.code, account.description, account.amount.toFixed(2)]);
      });
      rows.push(['', 'Total Other Income', incomeStatement.total_other_income.toFixed(2)]);
      rows.push(['', '', '']);
    }

    rows.push(['', 'Net Income', incomeStatement.net_income.toFixed(2)]);

    const csvContent = [
      `"${incomeStatement.company_name}"`,
      '"Income Statement"',
      `"For the period ${incomeStatement.period_start} to ${incomeStatement.period_end}"`,
      '',
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    downloadFile(
      csvContent,
      `income-statement-${incomeStatement.period_start}-${incomeStatement.period_end}.csv`
    );
    toast.success('Income statement exported successfully');
  };

  const handleExportCashFlow = () => {
    if (!cashFlowStatement) {
      toast.error('No cash flow statement data to export');
      return;
    }

    const headers = ['Account Code', 'Account Description', 'Amount'];
    const rows: string[][] = [];

    // Operating Activities
    rows.push(['', 'OPERATING ACTIVITIES', '']);
    cashFlowStatement.operating_activities.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Net Cash from Operations', cashFlowStatement.net_cash_from_operations.toFixed(2)]);
    rows.push(['', '', '']);

    // Investing Activities
    rows.push(['', 'INVESTING ACTIVITIES', '']);
    cashFlowStatement.investing_activities.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Net Cash from Investing', cashFlowStatement.net_cash_from_investing.toFixed(2)]);
    rows.push(['', '', '']);

    // Financing Activities
    rows.push(['', 'FINANCING ACTIVITIES', '']);
    cashFlowStatement.financing_activities.accounts.forEach((account) => {
      rows.push([account.code, account.description, account.amount.toFixed(2)]);
    });
    rows.push(['', 'Net Cash from Financing', cashFlowStatement.net_cash_from_financing.toFixed(2)]);
    rows.push(['', '', '']);

    rows.push(['', 'Net Change in Cash', cashFlowStatement.net_change_in_cash.toFixed(2)]);
    rows.push(['', 'Beginning Cash Balance', cashFlowStatement.beginning_cash_balance.toFixed(2)]);
    rows.push(['', 'Ending Cash Balance', cashFlowStatement.ending_cash_balance.toFixed(2)]);

    const csvContent = [
      `"${cashFlowStatement.company_name}"`,
      '"Cash Flow Statement"',
      `"For the period ${cashFlowStatement.period_start} to ${cashFlowStatement.period_end}"`,
      '',
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    downloadFile(
      csvContent,
      `cash-flow-${cashFlowStatement.period_start}-${cashFlowStatement.period_end}.csv`
    );
    toast.success('Cash flow statement exported successfully');
  };

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const canExport = useMemo(() => {
    switch (activeTab) {
      case 'balance-sheet':
        return !!balanceSheet;
      case 'income-statement':
        return !!incomeStatement;
      case 'cash-flow':
        return !!cashFlowStatement;
      default:
        return false;
    }
  }, [activeTab, balanceSheet, incomeStatement, cashFlowStatement]);

  const handleExport = () => {
    switch (activeTab) {
      case 'balance-sheet':
        handleExportBalanceSheet();
        break;
      case 'income-statement':
        handleExportIncomeStatement();
        break;
      case 'cash-flow':
        handleExportCashFlow();
        break;
    }
  };

  // Empty state when no company is selected
  if (!selectedCompanyId) {
    return (
      <div className="p-10 space-y-8">
        <PageHeader
          title="Auditor's Tower"
          subtitle="Survey the financial landscape from the heights of precision"
          icon={Scroll}
        />
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <FileSpreadsheet className="h-16 w-16 text-muted-foreground opacity-50" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Company Selected</h3>
                <p className="text-muted-foreground">
                  Please select a company from the dropdown above to view financial statements.
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
      <PageHeader
        title="Auditor's Tower"
        subtitle="Review ancient scrolls of financial wisdom"
        icon={Scroll}
        actions={
          canExport && (
            <Button onClick={handleExport} variant="outline" className="shadow-gold">
              <Download className="w-4 h-4 mr-2" />
              Export to CSV
            </Button>
          )
        }
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <Tabs value={activeTab} onValueChange={(value: any) => setActiveTab(value)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="balance-sheet">Balance Sheet</TabsTrigger>
            <TabsTrigger value="income-statement">Income Statement</TabsTrigger>
            <TabsTrigger value="cash-flow">Cash Flow</TabsTrigger>
          </TabsList>

          <TabsContent value="balance-sheet" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Balance Sheet Parameters</CardTitle>
                <CardDescription>Select the date for the balance sheet</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-4">
                  <div className="flex-1 space-y-2">
                    <Label>As of Date</Label>
                    <Input
                      type="date"
                      value={balanceSheetDate}
                      onChange={(e) => setBalanceSheetDate(e.target.value)}
                      placeholder="Select a date"
                    />
                  </div>
                  <Button
                    onClick={() => setBalanceSheetDate(new Date().toISOString().split('T')[0])}
                    variant="outline"
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Today
                  </Button>
                </div>
              </CardContent>
            </Card>

            {balanceSheetError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>Failed to load balance sheet. Please try again.</AlertDescription>
              </Alert>
            )}

            {balanceSheetLoading && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    <p className="text-muted-foreground">Loading balance sheet...</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {balanceSheet && !balanceSheetLoading && (
              <ScrollUnfurl
                title="Balance Sheet"
                subtitle={`As of ${balanceSheet.as_of_date}`}
              >
                <BalanceSheet balanceSheet={balanceSheet} />
              </ScrollUnfurl>
            )}

            {!balanceSheet && !balanceSheetLoading && !balanceSheetError && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4 text-center">
                    <FileSpreadsheet className="h-16 w-16 text-muted-foreground" />
                    <div>
                      <h3 className="font-semibold text-lg mb-2">No Date Selected</h3>
                      <p className="text-muted-foreground">
                        Select a date above to generate the balance sheet
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="income-statement" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Income Statement Parameters</CardTitle>
                <CardDescription>Select the date range for the income statement</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      placeholder="Start date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      placeholder="End date"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {incomeStatementError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>
                  Failed to load income statement. Please try again.
                </AlertDescription>
              </Alert>
            )}

            {incomeStatementLoading && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    <p className="text-muted-foreground">Loading income statement...</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {incomeStatement && !incomeStatementLoading && (
              <ScrollUnfurl
                title="Income Statement"
                subtitle={`For the period ${incomeStatement.period_start} to ${incomeStatement.period_end}`}
                delay={0.1}
              >
                <IncomeStatement incomeStatement={incomeStatement} />
              </ScrollUnfurl>
            )}

            {!incomeStatement && !incomeStatementLoading && !incomeStatementError && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4 text-center">
                    <FileSpreadsheet className="h-16 w-16 text-muted-foreground" />
                    <div>
                      <h3 className="font-semibold text-lg mb-2">No Date Range Selected</h3>
                      <p className="text-muted-foreground">
                        Select start and end dates above to generate the income statement
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="cash-flow" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Cash Flow Statement Parameters</CardTitle>
                <CardDescription>
                  Select the date range for the cash flow statement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      placeholder="Start date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      placeholder="End date"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {cashFlowError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>
                  Failed to load cash flow statement. Please try again.
                </AlertDescription>
              </Alert>
            )}

            {cashFlowLoading && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    <p className="text-muted-foreground">Loading cash flow statement...</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {cashFlowStatement && !cashFlowLoading && (
              <ScrollUnfurl
                title="Cash Flow Statement"
                subtitle={`For the period ${cashFlowStatement.period_start} to ${cashFlowStatement.period_end}`}
                delay={0.2}
              >
                <CashFlowStatement cashFlowStatement={cashFlowStatement} />
              </ScrollUnfurl>
            )}

            {!cashFlowStatement && !cashFlowLoading && !cashFlowError && (
              <Card>
                <CardContent className="py-16">
                  <div className="flex flex-col items-center justify-center space-y-4 text-center">
                    <FileSpreadsheet className="h-16 w-16 text-muted-foreground" />
                    <div>
                      <h3 className="font-semibold text-lg mb-2">No Date Range Selected</h3>
                      <p className="text-muted-foreground">
                        Select start and end dates above to generate the cash flow statement
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default FinancialStatementsPage;
