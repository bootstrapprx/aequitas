import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Filter, Download, Feather } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { PageHeader, AtheneumCard, AtheneumCardHeader, AtheneumCardContent, QuillIcon } from '@/components/athenaeum';
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
import { useCompany } from '@/contexts/CompanyContext';
import type { JournalEntry, EntryStatus } from '@/types/accounting';

const JournalEntriesPage = () => {
  const { user } = useAuth();
  const { selectedCompanyId, selectedCompany } = useCompany();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<EntryStatus | 'all'>('all');
  const [filterPeriod, setFilterPeriod] = useState<string>('all');

  // Fetch data
  const { data: fiscalPeriods = [] } = useFiscalPeriods(selectedCompanyId || undefined);
  const { data: companyAccounts = [] } = useCompanyAccounts(selectedCompanyId || undefined);
  const { data: entriesData, isLoading } = useJournalEntries(selectedCompanyId || '', {
    status: filterStatus !== 'all' ? filterStatus : undefined,
    fiscal_period_id: filterPeriod !== 'all' ? filterPeriod : undefined,
  });

  // Mutations
  const createMutation = useCreateJournalEntry();
  const postMutation = usePostJournalEntry();
  const voidMutation = useVoidJournalEntry();
  const deleteMutation = useDeleteJournalEntry();

  const entries = entriesData?.entries || [];

  // Empty state when no company is selected
  if (!selectedCompanyId) {
    return (
      <div className="p-10 space-y-8">
        <PageHeader
          title="Scribe's Chamber"
          subtitle="Record transactions in the ledger with ancient precision"
          icon={Feather}
        />
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <Feather className="h-16 w-16 text-muted-foreground opacity-50" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Company Selected</h3>
                <p className="text-muted-foreground">
                  Please select a company from the dropdown above to view and manage journal entries.
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      </div>
    );
  }

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
      {/* Header - Using Athenaeum PageHeader */}
      <PageHeader
        title="Scribe's Chamber"
        subtitle="Record transactions in the ledger with ancient precision"
        icon={Feather}
        actions={
          <Button onClick={() => setCreateDialogOpen(true)} className="shadow-gold">
            <QuillIcon isWriting={createMutation.isPending} className="mr-2" />
            New Journal Entry
          </Button>
        }
      />

      {selectedCompany && selectedCompany.onboarding_status === 'ACTIVE' && (
        <Card>
          <CardContent className="flex items-start gap-3 py-4">
            <Feather className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-foreground">
              Entries are recorded exactly as submitted. Corrections are made with new entries.
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters - Using Athenaeum Card */}
      <AtheneumCard hover>
        <AtheneumCardHeader icon={<Filter className="w-5 h-5" />}>
          Filters
        </AtheneumCardHeader>
        <AtheneumCardContent>
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
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Entries List - Using Athenaeum Card */}
      <AtheneumCard glow>
        <AtheneumCardHeader
          icon={<Feather className="w-5 h-5" />}
          embossed
        >
          All Journal Entries
          <span className="text-sm font-normal text-muted-foreground ml-3">
            {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
          </span>
        </AtheneumCardHeader>
        <AtheneumCardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <QuillIcon isWriting className="mx-auto mb-2" size="lg" />
              <p>Loading journal entries...</p>
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
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Journal Entry</DialogTitle>
          </DialogHeader>
          <JournalEntryForm
            companyId={selectedCompanyId || ''}
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
