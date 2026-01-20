import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { JournalEntryLine } from '@/types/accounting';
import type { CompanyAccount } from '@/types/company_account';

interface JournalEntryLineEditorProps {
  lines: JournalEntryLine[];
  accounts: CompanyAccount[];
  accountBalances?: Record<string, number>;
  onChange: (lines: JournalEntryLine[]) => void;
  disabled?: boolean;
}

export function JournalEntryLineEditor({
  lines,
  accounts,
  accountBalances = {},
  onChange,
  disabled = false,
}: JournalEntryLineEditorProps) {
  const [localLines, setLocalLines] = useState<JournalEntryLine[]>(lines);

  useEffect(() => {
    setLocalLines(lines);
  }, [lines]);

  const handleLineChange = (index: number, field: keyof JournalEntryLine, value: any) => {
    const newLines = [...localLines];
    newLines[index] = { ...newLines[index], [field]: value };

    // If changing debit, clear credit (and vice versa)
    if (field === 'debit_amount' && parseFloat(value || '0') > 0) {
      newLines[index].credit_amount = 0;
    } else if (field === 'credit_amount' && parseFloat(value || '0') > 0) {
      newLines[index].debit_amount = 0;
    }

    setLocalLines(newLines);
    onChange(newLines);
  };

  const handleAddLine = () => {
    const newLine: JournalEntryLine = {
      company_account_id: '',
      line_number: localLines.length + 1,
      description: '',
      debit_amount: 0,
      credit_amount: 0,
    };
    const newLines = [...localLines, newLine];
    setLocalLines(newLines);
    onChange(newLines);
  };

  const handleRemoveLine = (index: number) => {
    if (localLines.length <= 2) return; // Minimum 2 lines required
    const newLines = localLines.filter((_, i) => i !== index);
    // Renumber lines
    newLines.forEach((line, i) => {
      line.line_number = i + 1;
    });
    setLocalLines(newLines);
    onChange(newLines);
  };

  const totalDebit = localLines.reduce((sum, line) => sum + (parseFloat(String(line.debit_amount)) || 0), 0);
  const totalCredit = localLines.reduce((sum, line) => sum + (parseFloat(String(line.credit_amount)) || 0), 0);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  const accountsById = new Map(accounts.map((account) => [account.id, account]));
  const accountDeltaById = localLines.reduce((map, line) => {
    if (!line.company_account_id) return map;
    const debit = parseFloat(String(line.debit_amount)) || 0;
    const credit = parseFloat(String(line.credit_amount)) || 0;
    const current = map.get(line.company_account_id) || { debit: 0, credit: 0 };
    map.set(line.company_account_id, {
      debit: current.debit + debit,
      credit: current.credit + credit,
    });
    return map;
  }, new Map<string, { debit: number; credit: number }>());

  const formatCurrency = (amount: number) =>
    amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

  const getAccountTone = (accountType?: string | null) => {
    switch (accountType) {
      case 'Asset':
        return { dot: 'bg-blue-500', text: 'text-blue-600' };
      case 'Liability':
        return { dot: 'bg-amber-500', text: 'text-amber-600' };
      case 'Equity':
        return { dot: 'bg-emerald-500', text: 'text-emerald-600' };
      case 'Revenue':
        return { dot: 'bg-teal-500', text: 'text-teal-600' };
      case 'Expense':
        return { dot: 'bg-rose-500', text: 'text-rose-600' };
      default:
        return { dot: 'bg-muted-foreground', text: 'text-muted-foreground' };
    }
  };

  const getLineBalanceInfo = (line: JournalEntryLine) => {
    if (!line.company_account_id) return null;
    const account = accountsById.get(line.company_account_id);
    const normalBalance = account?.normal_balance || 'Debit';
    const currentBalance = accountBalances[line.company_account_id] || 0;
    const delta = accountDeltaById.get(line.company_account_id) || { debit: 0, credit: 0 };
    const netChange =
      String(normalBalance).toLowerCase() === 'credit'
        ? delta.credit - delta.debit
        : delta.debit - delta.credit;
    const newBalance = currentBalance + netChange;
    return {
      currentBalance,
      newBalance,
      insufficient: newBalance < 0,
    };
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Journal Entry Lines</CardTitle>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddLine}
            disabled={disabled}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Line
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Header Row */}
          <div className="grid grid-cols-12 gap-2 text-sm font-medium text-muted-foreground px-2">
            <div className="col-span-1">#</div>
            <div className="col-span-4">Account</div>
            <div className="col-span-2">Description</div>
            <div className="col-span-2">Debit</div>
            <div className="col-span-2">Credit</div>
            <div className="col-span-1"></div>
          </div>

          {/* Lines */}
          {localLines.map((line, index) => (
            <div key={index} className="grid grid-cols-12 gap-2 items-start">
              {/* Line Number */}
              <div className="col-span-1 flex items-center h-10 px-2 text-sm text-muted-foreground">
                {line.line_number}
              </div>

              {/* Account Selection */}
              <div className="col-span-4">
                <Select
                  value={line.company_account_id}
                  onValueChange={(value) => handleLineChange(index, 'company_account_id', value)}
                  disabled={disabled}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select account..." />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map((account) => {
                      const tone = getAccountTone(account.account_type);
                      return (
                        <SelectItem key={account.id} value={account.id}>
                          <span className={`flex items-center gap-2 ${tone.text}`}>
                            <span className={`h-2 w-2 rounded-full ${tone.dot}`} />
                            {account.code} - {account.description}
                          </span>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
                {line.company_account_id && (() => {
                  const info = getLineBalanceInfo(line);
                  const account = accountsById.get(line.company_account_id);
                  const tone = getAccountTone(account?.account_type);
                  if (!info) return null;
                  return (
                    <div className={`mt-1 text-xs ${info.insufficient ? 'text-destructive' : 'text-muted-foreground'}`}>
                      <span className={tone.text}>{account?.account_type || 'Account'}</span> · Current: {formatCurrency(info.currentBalance)} · New: {formatCurrency(info.newBalance)}
                      {info.insufficient ? ' · Insufficient balance' : ''}
                    </div>
                  );
                })()}
              </div>

              {/* Description */}
              <div className="col-span-2">
                <Input
                  type="text"
                  value={line.description || ''}
                  onChange={(e) => handleLineChange(index, 'description', e.target.value)}
                  placeholder="Description (optional)"
                  disabled={disabled}
                />
              </div>

              {/* Debit Amount */}
              <div className="col-span-2">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={line.debit_amount || ''}
                  onChange={(e) => handleLineChange(index, 'debit_amount', e.target.value)}
                  placeholder="0.00"
                  disabled={disabled}
                  className="text-right"
                />
              </div>

              {/* Credit Amount */}
              <div className="col-span-2">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={line.credit_amount || ''}
                  onChange={(e) => handleLineChange(index, 'credit_amount', e.target.value)}
                  placeholder="0.00"
                  disabled={disabled}
                  className="text-right"
                />
              </div>

              {/* Remove Button */}
              <div className="col-span-1 flex items-center justify-center">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemoveLine(index)}
                  disabled={disabled || localLines.length <= 2}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))}

          {/* Totals Row */}
          <div className="grid grid-cols-12 gap-2 border-t pt-4 mt-4">
            <div className="col-span-7 text-right font-medium">Totals:</div>
            <div className="col-span-2">
              <div className="text-right font-bold">${totalDebit.toFixed(2)}</div>
            </div>
            <div className="col-span-2">
              <div className="text-right font-bold">${totalCredit.toFixed(2)}</div>
            </div>
            <div className="col-span-1"></div>
          </div>

          {/* Balance Validation */}
          <div className="flex items-center justify-between px-2 py-3 bg-muted rounded-md">
            <span className="text-sm font-medium">Entry Balance:</span>
            {isBalanced ? (
              <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                ✓ Balanced
              </span>
            ) : (
              <span className="text-sm text-destructive font-medium">
                ⚠ Out of balance by ${Math.abs(totalDebit - totalCredit).toFixed(2)}
              </span>
            )}
          </div>

          {localLines.length < 2 && (
            <p className="text-sm text-destructive">
              At least 2 lines are required for a journal entry.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
