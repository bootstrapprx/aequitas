import React from 'react';
import { useForm } from 'react-hook-form';
import { GroupCompanyCreate } from '@/lib/api/groups';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface GroupFormProps {
  onSubmit: (data: GroupCompanyCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
  defaultValues?: Partial<GroupCompanyCreate>;
}

const GroupForm: React.FC<GroupFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  defaultValues,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<GroupCompanyCreate>({
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Group Name *</Label>
        <Input
          id="name"
          {...register('name', { required: 'Group name is required' })}
          placeholder="Enter group name"
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          {...register('description')}
          placeholder="Enter group description (optional)"
          rows={3}
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Group'}
        </Button>
      </div>
    </form>
  );
};

export default GroupForm;
