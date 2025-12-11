import React, { useState } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CheckCircle, XCircle, Edit, Trash2, FileCheck } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';

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
  posted_at?: string;
  voided_at?: string;
  void_reason?: string;
  lines: JournalEntryLine[];
  total_debit: number;
  total_credit: number;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entry: JournalEntry;
  onSuccess: () => void;
}

export default function JournalEntryViewDialog({ open, onOpenChange, entry, onSuccess }: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [showPostDialog, setShowPostDialog] = useState(false);
  const [showVoidDialog, setShowVoidDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [voidReason, setVoidReason] = useState('');

  // Fetch account details for each line
  const { data: accounts } = useQuery({
    queryKey: ['company-chart', entry.company_id],
    queryFn: async () => {
      const response = await api.get(`/companies/${entry.company_id}/chart`);
      return response.data;
    },
    enabled: open,
  });

  const getAccountName = (accountId: string) => {
    if (!accounts) return 'Loading...';
    const account = accounts.find((a: any) => a.id === accountId);
    return account ? `${account.code} - ${account.description}` : 'Unknown Account';
  };

  // Post mutation
  const postMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/journal-entries/${entry.id}/post`, {});
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Entry Posted',
        description: 'The journal entry has been posted successfully.',
      });
      setShowPostDialog(false);
      onSuccess();
    },
    onError: (error: any) => {
      toast({
        title: 'Error Posting Entry',
        description: error.response?.data?.detail || 'Failed to post journal entry',
        variant: 'destructive',
      });
    },
  });

  // Void mutation
  const voidMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/journal-entries/${entry.id}/void`, {
        void_reason: voidReason,
      });
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Entry Voided',
        description: 'The journal entry has been voided.',
      });
      setShowVoidDialog(false);
      setVoidReason('');
      onSuccess();
    },
    onError: (error: any) => {
      toast({
        title: 'Error Voiding Entry',
        description: error.response?.data?.detail || 'Failed to void journal entry',
        variant: 'destructive',
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/journal-entries/${entry.id}`);
    },
    onSuccess: () => {
      toast({
        title: 'Entry Deleted',
        description: 'The journal entry has been deleted.',
      });
      setShowDeleteDialog(false);
      onSuccess();
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Error Deleting Entry',
        description: error.response?.data?.detail || 'Failed to delete journal entry',
        variant: 'destructive',
      });
    },
  });

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

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>Journal Entry: {entry.entry_number}</DialogTitle>
                <DialogDescription>
                  {format(new Date(entry.entry_date), 'MMMM dd, yyyy')}
                </DialogDescription>
              </div>
              {getStatusBadge(entry.status)}
            </div>
          </DialogHeader>

          <div className="space-y-6">
            {/* Entry Details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Description</div>
                <div className="font-medium">{entry.description}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Reference</div>
                <div className="font-medium">{entry.reference || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Entry Type</div>
                <div className="font-medium capitalize">{entry.entry_type}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Created</div>
                <div className="font-medium">{format(new Date(entry.created_at), 'MMM dd, yyyy HH:mm')}</div>
              </div>
            </div>

            {/* Posted/Voided Info */}
            {entry.posted_at && (
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-green-800 dark:text-green-200 font-medium mb-2">
                  <CheckCircle className="h-5 w-5" />
                  Posted
                </div>
                <div className="text-sm text-green-700 dark:text-green-300">
                  Posted on {format(new Date(entry.posted_at), 'MMMM dd, yyyy HH:mm')}
                </div>
              </div>
            )}

            {entry.voided_at && (
              <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-red-800 dark:text-red-200 font-medium mb-2">
                  <XCircle className="h-5 w-5" />
                  Voided
                </div>
                <div className="text-sm text-red-700 dark:text-red-300 mb-2">
                  Voided on {format(new Date(entry.voided_at), 'MMMM dd, yyyy HH:mm')}
                </div>
                {entry.void_reason && (
                  <div className="text-sm text-red-700 dark:text-red-300">
                    <strong>Reason:</strong> {entry.void_reason}
                  </div>
                )}
              </div>
            )}

            {/* Journal Entry Lines */}
            <div>
              <div className="font-semibold mb-3">Journal Entry Lines</div>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted">
                    <tr>
                      <th className="text-left p-3 font-medium">Account</th>
                      <th className="text-left p-3 font-medium">Description</th>
                      <th className="text-right p-3 font-medium">Debit</th>
                      <th className="text-right p-3 font-medium">Credit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entry.lines
                      .sort((a, b) => a.line_number - b.line_number)
                      .map((line) => (
                        <tr key={line.id} className="border-t">
                          <td className="p-3 text-sm">{getAccountName(line.company_account_id)}</td>
                          <td className="p-3 text-sm text-muted-foreground">
                            {line.description || '-'}
                          </td>
                          <td className="p-3 text-sm text-right font-mono">
                            {line.debit_amount > 0 ? `$${line.debit_amount.toFixed(2)}` : '-'}
                          </td>
                          <td className="p-3 text-sm text-right font-mono">
                            {line.credit_amount > 0 ? `$${line.credit_amount.toFixed(2)}` : '-'}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                  <tfoot className="bg-muted border-t-2">
                    <tr>
                      <td colSpan={2} className="p-3 text-right font-semibold">Totals:</td>
                      <td className="p-3 text-right font-semibold font-mono">
                        ${entry.total_debit.toFixed(2)}
                      </td>
                      <td className="p-3 text-right font-semibold font-mono">
                        ${entry.total_credit.toFixed(2)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center pt-4 border-t">
              <div className="flex gap-2">
                {entry.status === 'draft' && (
                  <>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setShowDeleteDialog(true)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </Button>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                {entry.status === 'draft' && (
                  <Button onClick={() => setShowPostDialog(true)}>
                    <FileCheck className="h-4 w-4 mr-2" />
                    Post Entry
                  </Button>
                )}
                {entry.status === 'posted' && (
                  <Button
                    variant="destructive"
                    onClick={() => setShowVoidDialog(true)}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Void Entry
                  </Button>
                )}
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Post Confirmation Dialog */}
      <AlertDialog open={showPostDialog} onOpenChange={setShowPostDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Post Journal Entry?</AlertDialogTitle>
            <AlertDialogDescription>
              Posting this entry will:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Update account balances</li>
                <li>Make the entry permanent (cannot be edited or deleted)</li>
                <li>Allow the entry to be included in financial reports</li>
              </ul>
              <div className="mt-3 font-semibold">
                This action cannot be undone, but the entry can be voided later if needed.
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => postMutation.mutate()}>
              Post Entry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Void Confirmation Dialog */}
      <AlertDialog open={showVoidDialog} onOpenChange={setShowVoidDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Void Journal Entry?</AlertDialogTitle>
            <AlertDialogDescription>
              Voiding this entry will mark it as void but will NOT reverse the account balances.
              You may need to create a reversing entry manually.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Label>Void Reason (Optional)</Label>
            <Textarea
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
              placeholder="Enter a reason for voiding this entry..."
              rows={3}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => voidMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Void Entry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Journal Entry?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the journal entry. This action cannot be undone.
              Only draft entries can be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Entry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
