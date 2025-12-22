import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useCompany } from '@/contexts/CompanyContext';
import {
  acceptMapping,
  getPendingMappings,
  overrideMapping,
  rejectMapping,
  MappingReviewItem,
} from '@/api/mappings';
import MappingDecisionDialog from '@/components/mapping/MappingDecisionDialog';

type DialogState =
  | { open: false }
  | { open: true; mode: 'accept' | 'override' | 'reject'; mappingId: string };

const MappingReviewPage = () => {
  const { selectedCompanyId } = useCompany();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dialogState, setDialogState] = useState<DialogState>({ open: false });

  const { data: mappings, isLoading } = useQuery({
    queryKey: ['mapping-review', selectedCompanyId],
    queryFn: () => getPendingMappings(selectedCompanyId || ''),
    enabled: !!selectedCompanyId,
  });

  const acceptMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => acceptMapping(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mapping-review', selectedCompanyId] });
      toast({ title: 'Mapping accepted' });
    },
    onError: (err: any) => toast({ title: 'Failed to accept mapping', description: err?.message, variant: 'destructive' }),
  });

  const overrideMutation = useMutation({
    mutationFn: ({ id, masterAccountId, reason }: { id: string; masterAccountId: string; reason: string }) =>
      overrideMapping(id, masterAccountId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mapping-review', selectedCompanyId] });
      toast({ title: 'Mapping overridden' });
    },
    onError: (err: any) => toast({ title: 'Failed to override mapping', description: err?.message, variant: 'destructive' }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectMapping(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mapping-review', selectedCompanyId] });
      toast({ title: 'Mapping rejected' });
    },
    onError: (err: any) => toast({ title: 'Failed to reject mapping', description: err?.message, variant: 'destructive' }),
  });

  const handleDecision = (payload: { reason: string; masterAccountId?: string }) => {
    if (!dialogState.open) return;
    const { mappingId, mode } = dialogState;

    if (mode === 'accept') {
      acceptMutation.mutate({ id: mappingId, reason: payload.reason });
    } else if (mode === 'override' && payload.masterAccountId) {
      overrideMutation.mutate({ id: mappingId, masterAccountId: payload.masterAccountId, reason: payload.reason });
    } else if (mode === 'reject') {
      rejectMutation.mutate({ id: mappingId, reason: payload.reason });
    }
    setDialogState({ open: false });
  };

  const renderRow = (item: MappingReviewItem) => (
    <TableRow key={item.id}>
      <TableCell>
        <div className="font-semibold">{item.company_account.name || item.company_account.code}</div>
        <div className="text-xs text-muted-foreground">{item.company_account.code}</div>
      </TableCell>
      <TableCell>
        {item.master_account ? (
          <>
            <div className="font-medium">{item.master_account.code}</div>
            <div className="text-xs text-muted-foreground">{item.master_account.description}</div>
          </>
        ) : (
          <Badge variant="outline">Unmapped</Badge>
        )}
      </TableCell>
      <TableCell>
        <Badge variant="secondary">{Math.round(item.confidence * 100)}%</Badge>
      </TableCell>
      <TableCell>{item.decision_reason || item.notes || item.mapping_status}</TableCell>
      <TableCell className="space-x-2">
        <Button size="sm" onClick={() => setDialogState({ open: true, mode: 'accept', mappingId: item.id })}>
          Accept
        </Button>
        <Button variant="secondary" size="sm" onClick={() => setDialogState({ open: true, mode: 'override', mappingId: item.id })}>
          Override
        </Button>
        <Button variant="destructive" size="sm" onClick={() => setDialogState({ open: true, mode: 'reject', mappingId: item.id })}>
          Reject
        </Button>
      </TableCell>
    </TableRow>
  );

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Mapping Review</CardTitle>
          <CardDescription>Review and decide on pending mappings before they become authoritative.</CardDescription>
        </CardHeader>
        <CardContent>
          {!selectedCompanyId && <div>Please select a company to review mappings.</div>}
          {selectedCompanyId && (
            <>
              {isLoading && <div>Loading pending mappings...</div>}
              {!isLoading && (!mappings || mappings.length === 0) && <div>No pending mappings found.</div>}
              {!isLoading && mappings && mappings.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>External Account</TableHead>
                      <TableHead>Suggested Master Account</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>{mappings.map(renderRow)}</TableBody>
                </Table>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <MappingDecisionDialog
        open={dialogState.open}
        mode={dialogState.open ? dialogState.mode : 'accept'}
        onClose={() => setDialogState({ open: false })}
        onSubmit={handleDecision}
      />
    </div>
  );
};

export default MappingReviewPage;
