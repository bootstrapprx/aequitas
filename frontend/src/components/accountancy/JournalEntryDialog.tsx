import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { CompanyAccount } from '@/types/company_account';
import type { AccountBalance } from '@/types/accounting';

interface JournalEntryLine {
  line_number: number;
  company_account_id: string;
  description: string;
  debit_amount: number;
  credit_amount: number;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  companyId: string;
  onSuccess: () => void;
}

export default function JournalEntryDialog({ open, onOpenChange, companyId, onSuccess }: Props) {
  const { toast } = useToast();

  const [entryDate, setEntryDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [reference, setReference] = useState('');
  const [entryType, setEntryType] = useState('standard');
  const [fiscalPeriodId, setFiscalPeriodId] = useState('');
  const [lines, setLines] = useState<JournalEntryLine[]>([
    { line_number: 1, company_account_id: '', description: '', debit_amount: 0, credit_amount: 0 },
    { line_number: 2, company_account_id: '', description: '', debit_amount: 0, credit_amount: 0 },
  ]);

  // Fetch company accounts
  const { data: accounts } = useQuery({
    queryKey: ['company-chart', companyId],
    queryFn: async () => {
      const response = await api.get(`/companies/${companyId}/chart`);
      return response.filter((acc: CompanyAccount) => acc.type === 'D' && acc.is_active); // Only detail accounts
    },
    enabled: !!companyId && open,
  });

  // Fetch fiscal periods
  const { data: fiscalPeriods } = useQuery({
    queryKey: ['fiscal-periods', companyId],
    queryFn: async () => {
      const response = await api.get(`/accounting/fiscal-periods?company_id=${companyId}`);
      return response.filter((period: any) => String(period.status).toUpperCase() === 'OPEN');
    },
    enabled: !!companyId && open,
  });

  const { data: accountBalances = [] } = useQuery({
    queryKey: ['account-balances', companyId, fiscalPeriodId],
    queryFn: async () => {
      if (!fiscalPeriodId) return [];
      return await api.get<AccountBalance[]>('/accounting/balances', {
        params: { company_id: companyId, fiscal_period_id: fiscalPeriodId },
      });
    },
    enabled: !!companyId && !!fiscalPeriodId && open,
  });

  const accountsById = useMemo(() => {
    const map = new Map<string, CompanyAccount>();
    (accounts || []).forEach((account) => {
      map.set(account.id, account);
    });
    return map;
  }, [accounts]);

  const balancesByAccountId = useMemo(() => {
    const map = new Map<string, number>();
    accountBalances.forEach((balance) => {
      map.set(balance.company_account_id, Number(balance.ending_balance || 0));
    });
    return map;
  }, [accountBalances]);

  const accountDeltaById = useMemo(() => {
    const map = new Map<string, { debit: number; credit: number }>();
    lines.forEach((line) => {
      if (!line.company_account_id) return;
      const debit = Number(line.debit_amount || 0);
      const credit = Number(line.credit_amount || 0);
      const current = map.get(line.company_account_id) || { debit: 0, credit: 0 };
      map.set(line.company_account_id, {
        debit: current.debit + debit,
        credit: current.credit + credit,
      });
    });
    return map;
  }, [lines]);

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
    const currentBalance = balancesByAccountId.get(line.company_account_id) || 0;
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

  const hasBalanceIssue = lines.some((line) => {
    const info = getLineBalanceInfo(line);
    return info?.insufficient;
  });

  // Auto-select first open fiscal period
  useEffect(() => {
    if (fiscalPeriods && fiscalPeriods.length > 0 && !fiscalPeriodId) {
      setFiscalPeriodId(fiscalPeriods[0].id);
    }
  }, [fiscalPeriods, fiscalPeriodId]);

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/journal-entries/', data);
      return response;
    },
    onSuccess: () => {
      onSuccess();
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'Error Creating Entry',
        description: error.response?.data?.detail || 'Failed to create journal entry',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setEntryDate(new Date().toISOString().split('T')[0]);
    setDescription('');
    setReference('');
    setEntryType('standard');
    setLines([
      { line_number: 1, company_account_id: '', description: '', debit_amount: 0, credit_amount: 0 },
      { line_number: 2, company_account_id: '', description: '', debit_amount: 0, credit_amount: 0 },
    ]);
  };

  const addLine = () => {
    setLines([
      ...lines,
      {
        line_number: lines.length + 1,
        company_account_id: '',
        description: '',
        debit_amount: 0,
        credit_amount: 0,
      },
    ]);
  };

  const removeLine = (index: number) => {
    if (lines.length <= 2) {
      toast({
        title: 'Minimum Lines Required',
        description: 'A journal entry must have at least 2 lines',
        variant: 'destructive',
      });
      return;
    }
    setLines(lines.filter((_, i) => i !== index));
  };

  const updateLine = (index: number, field: keyof JournalEntryLine, value: any) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  };

  const getTotalDebits = () => {
    return lines.reduce((sum, line) => sum + Number(line.debit_amount || 0), 0);
  };

  const getTotalCredits = () => {
    return lines.reduce((sum, line) => sum + Number(line.credit_amount || 0), 0);
  };

  const isBalanced = () => {
    const debits = getTotalDebits();
    const credits = getTotalCredits();
    return Math.abs(debits - credits) < 0.01 && debits > 0; // Allow for small floating point differences
  };

  const handleSubmit = () => {
    if (!fiscalPeriodId) {
      toast({
        title: 'Fiscal Period Required',
        description: 'Please select a fiscal period',
        variant: 'destructive',
      });
      return;
    }

    if (!isBalanced()) {
      toast({
        title: 'Entry Not Balanced',
        description: 'Debits must equal credits',
        variant: 'destructive',
      });
      return;
    }

    // Validate all lines have accounts
    if (lines.some(line => !line.company_account_id)) {
      toast({
        title: 'Invalid Lines',
        description: 'All lines must have an account selected',
        variant: 'destructive',
      });
      return;
    }

    if (hasBalanceIssue) {
      toast({
        title: 'Insufficient Balance',
        description: 'One or more lines would create a negative balance.',
        variant: 'destructive',
      });
      return;
    }

    const data = {
      company_id: companyId,
      fiscal_period_id: fiscalPeriodId,
      entry_date: entryDate,
      description,
      reference: reference || null,
      entry_type: entryType.toUpperCase(),
      lines: lines.map(line => ({
        company_account_id: line.company_account_id,
        line_number: line.line_number,
        description: line.description || null,
        debit_amount: Number(line.debit_amount),
        credit_amount: Number(line.credit_amount),
      })),
    };

    createMutation.mutate(data);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Journal Entry</DialogTitle>
          <DialogDescription>
            Record a new journal entry with debits and credits
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Header Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Entry Date *</Label>
              <Input
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
              />
            </div>
            <div>
              <Label>Fiscal Period *</Label>
              <Select value={fiscalPeriodId} onValueChange={setFiscalPeriodId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select period" />
                </SelectTrigger>
                <SelectContent>
                  {fiscalPeriods?.map((period: any) => (
                    <SelectItem key={period.id} value={period.id}>
                      {period.period_number || period.name} ({period.start_date} to {period.end_date})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Description *</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter a description of this journal entry"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Reference (Optional)</Label>
              <Input
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                placeholder="Invoice #, Check #, etc."
              />
            </div>
            <div>
              <Label>Entry Type</Label>
              <Select value={entryType} onValueChange={setEntryType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="adjusting">Adjusting</SelectItem>
                  <SelectItem value="closing">Closing</SelectItem>
                  <SelectItem value="reversing">Reversing</SelectItem>
                  <SelectItem value="opening">Opening</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Journal Entry Lines */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-base font-semibold">Journal Entry Lines</Label>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-4 w-4 mr-2" />
                Add Line
              </Button>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-2 text-sm font-medium">Account *</th>
                    <th className="text-left p-2 text-sm font-medium">Description</th>
                    <th className="text-right p-2 text-sm font-medium">Debit</th>
                    <th className="text-right p-2 text-sm font-medium">Credit</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, index) => (
                    <tr key={index} className="border-t">
                      <td className="p-2">
                        <Select
                          value={line.company_account_id}
                          onValueChange={(value) => updateLine(index, 'company_account_id', value)}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select account" />
                          </SelectTrigger>
                          <SelectContent>
                            {accounts?.map((account: CompanyAccount) => {
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
                      </td>
                      <td className="p-2">
                        <Input
                          value={line.description}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                          placeholder="Line description"
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="0.01"
                          value={line.debit_amount || ''}
                          onChange={(e) => {
                            updateLine(index, 'debit_amount', e.target.value);
                            if (e.target.value) updateLine(index, 'credit_amount', 0);
                          }}
                          placeholder="0.00"
                          className="text-right"
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="0.01"
                          value={line.credit_amount || ''}
                          onChange={(e) => {
                            updateLine(index, 'credit_amount', e.target.value);
                            if (e.target.value) updateLine(index, 'debit_amount', 0);
                          }}
                          placeholder="0.00"
                          className="text-right"
                        />
                      </td>
                      <td className="p-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeLine(index)}
                          disabled={lines.length <= 2}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-muted border-t-2">
                  <tr>
                    <td colSpan={2} className="p-2 text-right font-semibold">Totals:</td>
                    <td className="p-2 text-right font-semibold">
                      ${getTotalDebits().toFixed(2)}
                    </td>
                    <td className="p-2 text-right font-semibold">
                      ${getTotalCredits().toFixed(2)}
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* Balance Warning */}
          {!isBalanced() && getTotalDebits() + getTotalCredits() > 0 && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Entry is not balanced. Debits (${getTotalDebits().toFixed(2)}) must equal Credits (${getTotalCredits().toFixed(2)}).
                Difference: ${Math.abs(getTotalDebits() - getTotalCredits()).toFixed(2)}
              </AlertDescription>
            </Alert>
          )}
          {hasBalanceIssue && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                One or more lines would create a negative balance.
              </AlertDescription>
            </Alert>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                onOpenChange(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!isBalanced() || hasBalanceIssue || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Entry'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
