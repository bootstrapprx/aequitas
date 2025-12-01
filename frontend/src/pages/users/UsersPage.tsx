import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/integrations/api';
import { User, UserCreate } from '@/types/user';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Loader2 } from 'lucide-react';
import UserForm from '@/components/users/UserForm';
import UsersList from '@/components/users/UsersList';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';

const UsersPage: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showForm, setShowForm] = useState(false);
  const { user: currentUser } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Check if current user is superuser
  const isSuperuser = currentUser?.is_superuser || false;

  const { data: users, isLoading, isError } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get('/users/');
      return response.data;
    },
    enabled: isSuperuser, // Only fetch if superuser
  });

  const createMutation = useMutation({
    mutationFn: async (userData: UserCreate) => {
      const response = await api.post('/users/', userData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: 'Success',
        description: 'User created successfully',
      });
      setShowForm(false);
      setSelectedUser(null);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create user',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<User> }) => {
      const response = await api.put(`/users/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: 'Success',
        description: 'User updated successfully',
      });
      setSelectedUser(null);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/users/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: 'Success',
        description: 'User deleted successfully',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete user',
        variant: 'destructive',
      });
    },
  });

  const handleFormSubmit = (userData: UserCreate | Partial<User>) => {
    if (selectedUser) {
      updateMutation.mutate({ id: selectedUser.id, data: userData });
    } else {
      createMutation.mutate(userData as UserCreate);
    }
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setShowForm(true);
  };

  const handleNew = () => {
    setSelectedUser(null);
    setShowForm(true);
  };

  if (!isSuperuser) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Users</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">
              You need superuser privileges to manage users.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">User Management</h1>
        <Button onClick={handleNew}>
          <Plus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <UsersList
          users={users || []}
          onDelete={handleDelete}
          onEdit={handleEdit}
          isLoading={isLoading}
          isError={isError}
        />
        {(showForm || selectedUser) && (
          <UserForm
            onSubmit={handleFormSubmit}
            initialData={selectedUser}
            onCancel={() => {
              setShowForm(false);
              setSelectedUser(null);
            }}
            isSubmitting={createMutation.isPending || updateMutation.isPending}
          />
        )}
      </div>
    </div>
  );
};

export default UsersPage;

