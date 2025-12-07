import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { groupsApi, PropagateMappingsRequest, Company } from '@/lib/api/groups';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';

interface PropagateMappingsDialogProps {
  groupId: string;
  companies: Company[];
  open: boolean;
  onClose: () => void;
}

const PropagateMappingsDialog: React.FC<PropagateMappingsDialogProps> = ({
  groupId,
  companies,
  open,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [sourceCompanyId, setSourceCompanyId] = useState<string>('');
  const [targetCompanyId, setTargetCompanyId] = useState<string>('');
  const [force, setForce] = useState(false);

  const propagateMutation = useMutation({
    mutationFn: (request: PropagateMappingsRequest) =>
      groupsApi.propagateMappings(groupId, request),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['groups', groupId] });
      toast.success(
        `Mappings propagated: ${result.created} created, ${result.updated} updated, ${result.skipped} skipped`
      );
      onClose();
      setSourceCompanyId('');
      setTargetCompanyId('');
      setForce(false);
    },
    onError: (error: any) => {
      toast.error(error?.details?.detail || 'Failed to propagate mappings');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceCompanyId) {
      toast.error('Please select a source company');
      return;
    }

    propagateMutation.mutate({
      source_company_id: sourceCompanyId,
      target_company_id: targetCompanyId || undefined,
      force,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Propagate Account Mappings</DialogTitle>
          <DialogDescription>
            Copy account mappings from one company to others in the group.
            Mappings will have reduced confidence when propagated.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="source">Source Company *</Label>
            <Select value={sourceCompanyId} onValueChange={setSourceCompanyId}>
              <SelectTrigger id="source">
                <SelectValue placeholder="Select source company" />
              </SelectTrigger>
              <SelectContent>
                {companies.map((company) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name} ({company.ucid})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="target">Target Company (Optional)</Label>
            <Select value={targetCompanyId} onValueChange={setTargetCompanyId}>
              <SelectTrigger id="target">
                <SelectValue placeholder="All companies (leave empty for all)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All companies in group</SelectItem>
                {companies
                  .filter((c) => c.id !== sourceCompanyId)
                  .map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.name} ({company.ucid})
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="force"
              checked={force}
              onCheckedChange={(checked) => setForce(checked === true)}
            />
            <Label
              htmlFor="force"
              className="text-sm font-normal cursor-pointer"
            >
              Force overwrite existing mappings
            </Label>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={propagateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!sourceCompanyId || propagateMutation.isPending}
            >
              {propagateMutation.isPending ? 'Propagating...' : 'Propagate'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default PropagateMappingsDialog;
