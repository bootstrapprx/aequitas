import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { groupsApi } from '@/lib/api/groups';
import { api } from '@/lib/api';
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

interface AddCompanyToGroupDialogProps {
  groupId: string;
  open: boolean;
  onClose: () => void;
}

interface Company {
  id: string;
  name: string;
  ucid: string;
  is_active: boolean;
}

const AddCompanyToGroupDialog: React.FC<AddCompanyToGroupDialogProps> = ({
  groupId,
  open,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');

  const { data: companies } = useQuery<Company[]>({
    queryKey: ['companies'],
    queryFn: () => api.get('/companies'),
    enabled: open,
  });

  const addMutation = useMutation({
    mutationFn: () => groupsApi.addCompanyToGroup(groupId, selectedCompanyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups', groupId] });
      toast.success('Company added to group successfully');
      onClose();
      setSelectedCompanyId('');
    },
    onError: (error: any) => {
      toast.error(error?.details?.detail || 'Failed to add company to group');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedCompanyId) {
      addMutation.mutate();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Company to Group</DialogTitle>
          <DialogDescription>
            Select an existing company to add to this group
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company">Company</Label>
            <Select value={selectedCompanyId} onValueChange={setSelectedCompanyId}>
              <SelectTrigger id="company">
                <SelectValue placeholder="Select a company" />
              </SelectTrigger>
              <SelectContent>
                {companies
                  ?.filter((c) => c.is_active)
                  .map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.name} ({company.ucid})
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={addMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!selectedCompanyId || addMutation.isPending}>
              {addMutation.isPending ? 'Adding...' : 'Add Company'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AddCompanyToGroupDialog;
