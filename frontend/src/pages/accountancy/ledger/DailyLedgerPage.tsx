import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Receipt, Plus, Filter, Download, Calendar, Search, Scroll } from 'lucide-react';
import {
  PageHeader,
  AtheneumCard,
  AtheneumCardHeader,
  AtheneumCardContent,
  WaxSealBadge,
  QuillIcon,
} from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import JournalEntryDialog from '@/components/accountancy/JournalEntryDialog';
import JournalEntryViewDialog from '@/components/accountancy/JournalEntryViewDialog';

interface JournalEntryLine {
  id: string;
  company_account_id: string;
  line_number: number;
  description: string | null;
  debit_amount: number;
  credit_amount: number;
}

interface JournalEntry {
  id: string;
  company_id: string;
  fiscal_period_id: string;
  entry_number: string;
  entry_date: string;
  description: string;
  reference: string | null;
  entry_type: string;
  status: 'draft' | 'posted' | 'void';
  created_at: string;
  lines: JournalEntryLine[];
  total_debit: number;
  total_credit: number;
}

const DailyLedgerPage = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);

  // Fetch companies
  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const response = await api.get('/companies/');
      return response.data;
    },
  });

  // Auto-select first company
  React.useEffect(() => {
    if (companies && companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  // Fetch journal entries
  const { data: journalEntries, isLoading, refetch } = useQuery({
    queryKey: ['journal-entries', selectedCompanyId, statusFilter, startDate, endDate],
    queryFn: async () => {
      if (!selectedCompanyId) return { entries: [] };

      const params = new URLSearchParams({
        company_id: selectedCompanyId,
      });

      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (startDate) {
        params.append('start_date', startDate);
      }
      if (endDate) {
        params.append('end_date', endDate);
      }

      const response = await api.get(`/journal-entries/?${params.toString()}`);
      return response.data;
    },
    enabled: !!selectedCompanyId,
  });

  // Filter entries by search query
  const filteredEntries = React.useMemo(() => {
    if (!journalEntries?.entries) return [];
    if (!searchQuery) return journalEntries.entries;

    const query = searchQuery.toLowerCase();
    return journalEntries.entries.filter((entry: JournalEntry) =>
      entry.entry_number.toLowerCase().includes(query) ||
      entry.description.toLowerCase().includes(query) ||
      (entry.reference && entry.reference.toLowerCase().includes(query))
    );
  }, [journalEntries, searchQuery]);

  const handleViewEntry = (entry: JournalEntry) => {
    setSelectedEntry(entry);
    setViewDialogOpen(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <WaxSealBadge type="pending" size="sm" />;
      case 'posted':
        return <WaxSealBadge type="approved" size="sm" />;
      case 'void':
        return <WaxSealBadge type="rejected" size="sm" />;
      default:
        return <WaxSealBadge type="pending" size="sm" />;
    }
  };

  if (!companies || companies.length === 0) {
    return (
      <div className="p-10">
        <AtheneumCard>
          <AtheneumCardHeader>No Companies Found</AtheneumCardHeader>
          <AtheneumCardContent>
            <p className="text-muted-foreground">
              Please create a company first to manage journal entries.
            </p>
          </AtheneumCardContent>
        </AtheneumCard>
      </div>
    );
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header - Using Athenaeum PageHeader */}
      <PageHeader
        title="Ledger of Days"
        subtitle="Chronicle the daily records in the grand book of accounts"
        icon={Scroll}
        actions={
          <Button onClick={() => setCreateDialogOpen(true)} size="lg" className="shadow-gold">
            <QuillIcon isWriting={false} className="mr-2" />
            New Journal Entry
          </Button>
        }
      />

      {/* Company Selector - Using Athenaeum Card */}
      {companies && companies.length > 1 && (
        <AtheneumCard hover>
          <AtheneumCardHeader>Select Company</AtheneumCardHeader>
          <AtheneumCardContent>
            <Select value={selectedCompanyId || ''} onValueChange={setSelectedCompanyId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a company" />
              </SelectTrigger>
              <SelectContent>
                {companies.map((company: any) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name} ({company.ucid})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </AtheneumCardContent>
        </AtheneumCard>
      )}

      {/* Filters - Using Athenaeum Card */}
      <AtheneumCard hover>
        <AtheneumCardHeader icon={<Filter className="w-5 h-5" />}>
          Filters
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Entry #, description..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="posted">Posted</SelectItem>
                  <SelectItem value="void">Void</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Journal Entries Table - Using Athenaeum Card */}
      <AtheneumCard glow>
        <AtheneumCardHeader icon={<Scroll className="w-5 h-5" />} embossed>
          Journal Entries
          <span className="text-sm font-normal text-muted-foreground ml-3">
            {filteredEntries.length} {filteredEntries.length === 1 ? 'entry' : 'entries'} found
          </span>
          <div className="ml-auto flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Refresh
            </Button>
            <Button variant="outline" size="sm" className="shadow-gold">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </AtheneumCardHeader>
        <AtheneumCardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <QuillIcon isWriting className="mx-auto mb-2" size="lg" />
              <p>Loading journal entries...</p>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Scroll className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No journal entries found. Create your first entry to get started.</p>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Entry #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((entry: JournalEntry) => (
                    <TableRow
                      key={entry.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleViewEntry(entry)}
                    >
                      <TableCell className="font-mono text-sm">{entry.entry_number}</TableCell>
                      <TableCell>{format(new Date(entry.entry_date), 'MMM dd, yyyy')}</TableCell>
                      <TableCell className="max-w-xs truncate">{entry.description}</TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {entry.reference || '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        ${entry.total_debit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        ${entry.total_credit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell>{getStatusBadge(entry.status)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewEntry(entry);
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Dialogs */}
      {selectedCompanyId && (
        <JournalEntryDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          companyId={selectedCompanyId}
          onSuccess={() => {
            setCreateDialogOpen(false);
            refetch();
            toast({
              title: 'Journal Entry Created',
              description: 'The journal entry has been created successfully.',
            });
          }}
        />
      )}

      {selectedEntry && (
        <JournalEntryViewDialog
          open={viewDialogOpen}
          onOpenChange={setViewDialogOpen}
          entry={selectedEntry}
          onSuccess={() => {
            setViewDialogOpen(false);
            refetch();
          }}
        />
      )}
    </div>
  );
};

export default DailyLedgerPage;
