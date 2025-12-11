import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Receipt, Plus, Filter, Download, Calendar, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700">Draft</Badge>;
      case 'posted':
        return <Badge variant="default" className="bg-green-50 text-green-700">Posted</Badge>;
      case 'void':
        return <Badge variant="destructive" className="bg-red-50 text-red-700">Void</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (!companies || companies.length === 0) {
    return (
      <div className="p-10">
        <Card>
          <CardHeader>
            <CardTitle>No Companies Found</CardTitle>
            <CardDescription>
              Please create a company first to manage journal entries.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-4">
            <Receipt className="h-8 w-8 text-green-600 dark:text-green-400" />
            <div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                Daily Ledger
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Record and manage daily journal entries
              </p>
            </div>
          </div>
          <Button onClick={() => setCreateDialogOpen(true)} size="lg">
            <Plus className="h-5 w-5 mr-2" />
            New Journal Entry
          </Button>
        </div>
      </motion.div>

      {/* Company Selector */}
      {companies && companies.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Company</CardTitle>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      {/* Journal Entries Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Journal Entries</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                Refresh
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
          <CardDescription>
            {filteredEntries.length} {filteredEntries.length === 1 ? 'entry' : 'entries'} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredEntries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No journal entries found. Create your first entry to get started.
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
        </CardContent>
      </Card>

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
