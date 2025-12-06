import { useState } from 'react';
import { format } from 'date-fns';
import { MoreVertical, Eye, Edit, CheckCircle, XCircle, Trash2 } from 'lucide-react';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { JournalEntryStatusBadge } from './JournalEntryStatusBadge';
import type { JournalEntry } from '@/types/accounting';

interface JournalEntryListProps {
  entries: JournalEntry[];
  onView?: (entry: JournalEntry) => void;
  onEdit?: (entry: JournalEntry) => void;
  onPost?: (entry: JournalEntry) => void;
  onVoid?: (entry: JournalEntry, reason: string) => void;
  onDelete?: (entry: JournalEntry) => void;
  isLoading?: boolean;
}

export function JournalEntryList({
  entries,
  onView,
  onEdit,
  onPost,
  onVoid,
  onDelete,
  isLoading = false,
}: JournalEntryListProps) {
  const [voidDialogOpen, setVoidDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [voidReason, setVoidReason] = useState('');

  const handleVoidClick = (entry: JournalEntry) => {
    setSelectedEntry(entry);
    setVoidDialogOpen(true);
  };

  const handleDeleteClick = (entry: JournalEntry) => {
    setSelectedEntry(entry);
    setDeleteDialogOpen(true);
  };

  const handleVoidConfirm = () => {
    if (selectedEntry && onVoid && voidReason.trim()) {
      onVoid(selectedEntry, voidReason);
      setVoidDialogOpen(false);
      setVoidReason('');
      setSelectedEntry(null);
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedEntry && onDelete) {
      onDelete(selectedEntry);
      setDeleteDialogOpen(false);
      setSelectedEntry(null);
    }
  };

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No journal entries found.</p>
        <p className="text-sm mt-2">Create your first journal entry to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Entry #</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Reference</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Debit</TableHead>
              <TableHead className="text-right">Credit</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((entry) => (
              <TableRow key={entry.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">{entry.entry_number}</TableCell>
                <TableCell>{entry.entry_date ? format(new Date(entry.entry_date), 'MMM dd, yyyy') : '-'}</TableCell>
                <TableCell className="max-w-xs truncate">{entry.description}</TableCell>
                <TableCell>{entry.reference || '-'}</TableCell>
                <TableCell className="capitalize">{entry.entry_type}</TableCell>
                <TableCell className="text-right font-mono">
                  ${entry.total_debit?.toFixed(2) || '0.00'}
                </TableCell>
                <TableCell className="text-right font-mono">
                  ${entry.total_credit?.toFixed(2) || '0.00'}
                </TableCell>
                <TableCell>
                  <JournalEntryStatusBadge status={entry.status || 'draft'} />
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" disabled={isLoading}>
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator />

                      {onView && (
                        <DropdownMenuItem onClick={() => onView(entry)}>
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                      )}

                      {onEdit && entry.status === 'draft' && (
                        <DropdownMenuItem onClick={() => onEdit(entry)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                      )}

                      {onPost && entry.status === 'draft' && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => onPost(entry)}>
                            <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
                            Post Entry
                          </DropdownMenuItem>
                        </>
                      )}

                      {onVoid && entry.status === 'posted' && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleVoidClick(entry)}>
                            <XCircle className="mr-2 h-4 w-4 text-orange-600" />
                            Void Entry
                          </DropdownMenuItem>
                        </>
                      )}

                      {onDelete && entry.status === 'draft' && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleDeleteClick(entry)}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Void Dialog */}
      <AlertDialog open={voidDialogOpen} onOpenChange={setVoidDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Void Journal Entry</AlertDialogTitle>
            <AlertDialogDescription>
              This will mark entry {selectedEntry?.entry_number} as void. Please provide a reason.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 py-4">
            <Label htmlFor="void-reason">Void Reason *</Label>
            <Textarea
              id="void-reason"
              placeholder="Enter reason for voiding this entry..."
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
              rows={3}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleVoidConfirm}
              disabled={!voidReason.trim()}
              className="bg-destructive hover:bg-destructive/90"
            >
              Void Entry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Journal Entry</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete entry {selectedEntry?.entry_number}? This action cannot be undone.
              Only draft entries can be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive hover:bg-destructive/90"
            >
              Delete Entry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
