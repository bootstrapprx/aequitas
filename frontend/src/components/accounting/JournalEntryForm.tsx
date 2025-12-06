import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { JournalEntryLineEditor } from './JournalEntryLineEditor';
import type { JournalEntry, JournalEntryLine, FiscalPeriod } from '@/types/accounting';
import { cn } from '@/lib/utils';

const journalEntrySchema = z.object({
  company_id: z.string().min(1, 'Company is required'),
  fiscal_period_id: z.string().min(1, 'Fiscal period is required'),
  entry_date: z.date({ required_error: 'Entry date is required' }),
  description: z.string().min(1, 'Description is required'),
  reference: z.string().optional(),
  entry_type: z.enum(['standard', 'adjusting', 'closing', 'reversing', 'opening']),
  lines: z.array(z.any()).min(2, 'At least 2 lines are required'),
});

type JournalEntryFormData = z.infer<typeof journalEntrySchema>;

interface JournalEntryFormProps {
  companyId: string;
  fiscalPeriods: FiscalPeriod[];
  accounts: Array<{ id: string; code: string; description: string }>;
  initialData?: Partial<JournalEntry>;
  onSubmit: (data: JournalEntry) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function JournalEntryForm({
  companyId,
  fiscalPeriods,
  accounts,
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
}: JournalEntryFormProps) {
  const [lines, setLines] = useState<JournalEntryLine[]>(
    initialData?.lines || [
      { company_account_id: '', line_number: 1, debit_amount: 0, credit_amount: 0 },
      { company_account_id: '', line_number: 2, debit_amount: 0, credit_amount: 0 },
    ]
  );

  const form = useForm<JournalEntryFormData>({
    resolver: zodResolver(journalEntrySchema),
    defaultValues: {
      company_id: companyId,
      fiscal_period_id: initialData?.fiscal_period_id || '',
      entry_date: initialData?.entry_date ? new Date(initialData.entry_date) : new Date(),
      description: initialData?.description || '',
      reference: initialData?.reference || '',
      entry_type: initialData?.entry_type || 'standard',
      lines: lines,
    },
  });

  useEffect(() => {
    form.setValue('lines', lines);
  }, [lines, form]);

  const handleSubmit = (data: JournalEntryFormData) => {
    // Validate balance
    const totalDebit = lines.reduce((sum, line) => sum + (parseFloat(String(line.debit_amount)) || 0), 0);
    const totalCredit = lines.reduce((sum, line) => sum + (parseFloat(String(line.credit_amount)) || 0), 0);

    if (Math.abs(totalDebit - totalCredit) >= 0.01) {
      form.setError('lines', { message: 'Journal entry must be balanced (debits = credits)' });
      return;
    }

    // Validate all lines have accounts selected
    const invalidLines = lines.filter(line => !line.company_account_id);
    if (invalidLines.length > 0) {
      form.setError('lines', { message: 'All lines must have an account selected' });
      return;
    }

    // Validate all lines have either debit or credit (not both, not neither)
    const invalidAmounts = lines.filter(line => {
      const debit = parseFloat(String(line.debit_amount)) || 0;
      const credit = parseFloat(String(line.credit_amount)) || 0;
      return (debit > 0 && credit > 0) || (debit === 0 && credit === 0);
    });

    if (invalidAmounts.length > 0) {
      form.setError('lines', { message: 'Each line must have either a debit or credit amount (not both, not neither)' });
      return;
    }

    const journalEntry: JournalEntry = {
      ...initialData,
      company_id: data.company_id,
      fiscal_period_id: data.fiscal_period_id,
      entry_date: format(data.entry_date, 'yyyy-MM-dd'),
      description: data.description,
      reference: data.reference,
      entry_type: data.entry_type,
      lines: lines.map((line, index) => ({
        ...line,
        line_number: index + 1,
        debit_amount: parseFloat(String(line.debit_amount)) || 0,
        credit_amount: parseFloat(String(line.credit_amount)) || 0,
      })),
    };

    onSubmit(journalEntry);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Header Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Fiscal Period */}
          <FormField
            control={form.control}
            name="fiscal_period_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Fiscal Period *</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select period..." />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {fiscalPeriods
                      .filter(p => p.status === 'open')
                      .map((period) => (
                        <SelectItem key={period.id} value={period.id}>
                          {period.period_number} ({period.start_date} to {period.end_date})
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Entry Date */}
          <FormField
            control={form.control}
            name="entry_date"
            render={({ field }) => (
              <FormItem className="flex flex-col">
                <FormLabel>Entry Date *</FormLabel>
                <Popover>
                  <PopoverTrigger asChild>
                    <FormControl>
                      <Button
                        variant="outline"
                        className={cn(
                          'w-full pl-3 text-left font-normal',
                          !field.value && 'text-muted-foreground'
                        )}
                      >
                        {field.value ? format(field.value, 'PPP') : <span>Pick a date</span>}
                        <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                      </Button>
                    </FormControl>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={field.value}
                      onSelect={field.onChange}
                      disabled={(date) =>
                        date > new Date() || date < new Date('1900-01-01')
                      }
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Entry Type */}
          <FormField
            control={form.control}
            name="entry_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Entry Type *</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="adjusting">Adjusting</SelectItem>
                    <SelectItem value="closing">Closing</SelectItem>
                    <SelectItem value="reversing">Reversing</SelectItem>
                    <SelectItem value="opening">Opening</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Reference */}
          <FormField
            control={form.control}
            name="reference"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Reference (Optional)</FormLabel>
                <FormControl>
                  <Input placeholder="Invoice #, Check #, etc." {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Description */}
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description *</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter journal entry description..."
                  className="resize-none"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Lines Editor */}
        <div>
          <JournalEntryLineEditor
            lines={lines}
            accounts={accounts}
            onChange={setLines}
            disabled={isLoading}
          />
          {form.formState.errors.lines && (
            <p className="text-sm text-destructive mt-2">
              {form.formState.errors.lines.message}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Saving...' : initialData?.id ? 'Update Entry' : 'Create Entry'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
