import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Filter, Download, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { JournalEntryList } from '@/components/accounting/JournalEntryList';
import { JournalEntryForm } from '@/components/accounting/JournalEntryForm';
import {
  useJournalEntries,
  useCreateJournalEntry,
  usePostJournalEntry,
  useVoidJournalEntry,
  useDeleteJournalEntry,
  useFiscalPeriods,
  useCompanyAccounts,
} from '@/hooks/useAccounting';
import { useAuth } from '@/contexts/AuthContext';
import type { JournalEntry, EntryStatus } from '@/types/accounting';

const JournalEntriesPage = () => {
  const { user, currentCompanyId } = useAuth();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<EntryStatus | 'all'>('all');
  const [filterPeriod, setFilterPeriod] = useState<string>('all');

  // Fetch data
  const { data: fiscalPeriods = [] } = useFiscalPeriods(currentCompanyId || undefined);
  const { data: companyAccounts = [] } = useCompanyAccounts(currentCompanyId || undefined);
  const { data: entriesData, isLoading } = useJournalEntries(currentCompanyId || '', {
    status: filterStatus !== 'all' ? filterStatus : undefined,
    fiscal_period_id: filterPeriod !== 'all' ? filterPeriod : undefined,
  });

  // Mutations
  const createMutation = useCreateJournalEntry();
  const postMutation = usePostJournalEntry();
  const voidMutation = useVoidJournalEntry();
  const deleteMutation = useDeleteJournalEntry();

  const entries = entriesData?.entries || [];

  const handleCreate = async (entry: JournalEntry) => {
    try {
      await createMutation.mutateAsync(entry);
      toast.success('Journal entry created successfully');
      setCreateDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create journal entry');
    }
  };

  const handlePost = async (entry: JournalEntry) => {
    if (!entry.id || !user?.id) return;

    try {
      await postMutation.mutateAsync({
        entryId: entry.id,
        userId: user.id,
      });
      toast.success(`Entry ${entry.entry_number} posted successfully`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to post journal entry');
    }
  };

  const handleVoid = async (entry: JournalEntry, reason: string) => {
    if (!entry.id || !user?.id) return;

    try {
      await voidMutation.mutateAsync({
        entryId: entry.id,
        userId: user.id,
        reason,
      });
      toast.success(`Entry ${entry.entry_number} voided`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to void journal entry');
    }
  };

  const handleDelete = async (entry: JournalEntry) => {
    if (!entry.id) return;

    try {
      await deleteMutation.mutateAsync(entry.id);
      toast.success(`Entry ${entry.entry_number} deleted`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete journal entry');
    }
  };

  return (
    <div className="p-10 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-4 mb-2">
              <BookOpen className="h-8 w-8 text-green-600 dark:text-green-400" />
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                Journal Entries
              </h1>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Create and manage journal entries with double-entry accounting
            </p>
          </div>
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Journal Entry
          </Button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Filter className="mr-2 h-4 w-4" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="filter-status">Status</Label>
                <Select value={filterStatus} onValueChange={(value: any) => setFilterStatus(value)}>
                  <SelectTrigger id="filter-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="posted">Posted</SelectItem>
                    <SelectItem value="void">Void</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="filter-period">Fiscal Period</Label>
                <Select value={filterPeriod} onValueChange={setFilterPeriod}>
                  <SelectTrigger id="filter-period">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Periods</SelectItem>
                    {fiscalPeriods.map((period: any) => (
                      <SelectItem key={period.id} value={period.id}>
                        {period.period_number}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end">
                <Button variant="outline" className="w-full">
                  <Download className="mr-2 h-4 w-4" />
                  Export to Excel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Entries List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>All Journal Entries</span>
              <span className="text-sm font-normal text-muted-foreground">
                {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading journal entries...
              </div>
            ) : (
              <JournalEntryList
                entries={entries}
                onPost={handlePost}
                onVoid={handleVoid}
                onDelete={handleDelete}
                isLoading={
                  postMutation.isPending || voidMutation.isPending || deleteMutation.isPending
                }
              />
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Journal Entry</DialogTitle>
          </DialogHeader>
          <JournalEntryForm
            companyId={currentCompanyId || ''}
            fiscalPeriods={fiscalPeriods}
            accounts={companyAccounts}
            onSubmit={handleCreate}
            onCancel={() => setCreateDialogOpen(false)}
            isLoading={createMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default JournalEntriesPage;
