import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { groupsApi, SUCreateCompanyRequest } from '@/lib/api/groups';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface SUCreateCompanyDialogProps {
  groupId?: string;
  open: boolean;
  onClose: () => void;
}

const SUCreateCompanyDialog: React.FC<SUCreateCompanyDialogProps> = ({
  groupId,
  open,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SUCreateCompanyRequest>();

  const createMutation = useMutation({
    mutationFn: (data: SUCreateCompanyRequest) => {
      const payload = groupId ? { ...data, group_company_id: groupId } : data;
      return groupsApi.suCreateCompany(payload);
    },
    onSuccess: () => {
      if (groupId) {
        queryClient.invalidateQueries({ queryKey: ['groups', groupId] });
      }
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      toast.success('Company created successfully (NATIVE subscription)');
      reset();
      onClose();
    },
    onError: (error: any) => {
      toast.error(error?.details?.detail || 'Failed to create company');
    },
  });

  const onSubmit = (data: SUCreateCompanyRequest) => {
    createMutation.mutate(data);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Company (Superuser)</DialogTitle>
          <DialogDescription>
            Create a company with NATIVE subscription (bypasses payment).
            {groupId && ' The company will be automatically added to this group.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-2">
              <Label htmlFor="name">Company Name *</Label>
              <Input
                id="name"
                {...register('name', { required: 'Company name is required' })}
                placeholder="Enter company name"
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                {...register('email')}
                placeholder="company@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                {...register('phone')}
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="address_line1">Address Line 1</Label>
              <Input
                id="address_line1"
                {...register('address_line1')}
                placeholder="Street address"
              />
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="address_line2">Address Line 2</Label>
              <Input
                id="address_line2"
                {...register('address_line2')}
                placeholder="Apartment, suite, etc."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input id="city" {...register('city')} placeholder="City" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="state">State</Label>
              <Input id="state" {...register('state')} placeholder="State" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="postal_code">Postal Code</Label>
              <Input
                id="postal_code"
                {...register('postal_code')}
                placeholder="12345"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input id="country" {...register('country')} placeholder="Country" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tax_id">Tax ID</Label>
              <Input
                id="tax_id"
                {...register('tax_id')}
                placeholder="Tax ID / EIN"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                {...register('industry')}
                placeholder="Industry"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Company'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default SUCreateCompanyDialog;
