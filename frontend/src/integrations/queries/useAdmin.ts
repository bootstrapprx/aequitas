import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/lib/api/admin';
import { adminKeys } from '@/lib/queryKeys';
import { toast } from '@/hooks/use-toast';
import type { User } from '@/types/user';
import type { SystemSettings, SystemSettingsUpdate } from '@/types/admin';

// --- Query to get all users ---
export const useGetAllUsers = () => {
  return useQuery({
    queryKey: adminKeys.users(),
    queryFn: adminApi.getAllUsers,
  });
};

// --- Mutation to promote user to superuser ---
export const usePromoteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => adminApi.promoteUser(userId),
    onSuccess: (updatedUser: User) => {
      toast({
        title: 'Success',
        description: `User ${updatedUser.email} has been promoted to superuser.`,
      });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: `Failed to promote user: ${error.message}`,
        variant: 'destructive',
      });
    },
  });
};

// --- Mutation to demote user from superuser ---
export const useDemoteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => adminApi.demoteUser(userId),
    onSuccess: (updatedUser: User) => {
      toast({
        title: 'Success',
        description: `User ${updatedUser.email} has been demoted from superuser.`,
      });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: `Failed to demote user: ${error.message}`,
        variant: 'destructive',
      });
    },
  });
};

// --- Query to get system settings ---
export const useGetSettings = () => {
  return useQuery({
    queryKey: adminKeys.settings(),
    queryFn: adminApi.getSettings,
  });
};

// --- Mutation to update system settings ---
export const useUpdateSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: SystemSettingsUpdate) => adminApi.updateSettings(settings),
    onSuccess: (updatedSettings: SystemSettings) => {
      toast({
        title: 'Success',
        description: 'System settings updated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: adminKeys.settings() });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: `Failed to update settings: ${error.message}`,
        variant: 'destructive',
      });
    },
  });
};
