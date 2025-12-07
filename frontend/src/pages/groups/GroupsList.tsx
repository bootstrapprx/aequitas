import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderOpen } from 'lucide-react';
import { toast } from 'sonner';

import { groupsApi, GroupCompany, GroupCompanyCreate } from '@/lib/api/groups';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import GroupForm from '@/components/groups/GroupForm';

const GroupsList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);

  const { data: groups, isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.listGroups(),
  });

  const createMutation = useMutation({
    mutationFn: (data: GroupCompanyCreate) => groupsApi.createGroup(data),
    onSuccess: (newGroup) => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      toast.success('Group created successfully');
      setIsCreating(false);
      navigate(`/groups/${newGroup.id}`);
    },
    onError: (error: any) => {
      toast.error(error?.details?.detail || 'Failed to create group');
    },
  });

  const handleCreate = (data: GroupCompanyCreate) => {
    createMutation.mutate(data);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <p>Loading groups...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Company Groups</h1>
          <p className="text-muted-foreground">
            Manage groups of companies with shared chart of accounts mappings
          </p>
        </div>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Group
        </Button>
      </div>

      {isCreating && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create New Group</CardTitle>
            <CardDescription>
              Create a group to manage multiple companies under a single umbrella
            </CardDescription>
          </CardHeader>
          <CardContent>
            <GroupForm
              onSubmit={handleCreate}
              onCancel={() => setIsCreating(false)}
              isLoading={createMutation.isPending}
            />
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {groups?.map((group) => (
          <Card
            key={group.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => navigate(`/groups/${group.id}`)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <FolderOpen className="h-8 w-8 text-primary" />
              </div>
              <CardTitle className="mt-4">{group.name}</CardTitle>
              {group.description && (
                <CardDescription>{group.description}</CardDescription>
              )}
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Created {new Date(group.created_at).toLocaleDateString()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {(!groups || groups.length === 0) && !isCreating && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FolderOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No groups yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first group to start managing multiple companies
            </p>
            <Button onClick={() => setIsCreating(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create First Group
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GroupsList;
