/**
 * TanStack Query hooks for Users Management module.
 * Provides data fetching and mutation hooks with automatic cache management.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAllUsers,
  getUsersByCompany,
  getUser,
  createUser,
  updateUser,
  deactivateUser,
  deleteUser,
  reactivateUser,
  resetUserPassword,
} from '@/lib/api/usersManagement';
import {
  UserListItem,
  UserDetail,
  UserCreateRequest,
  UserUpdateRequest,
  UserCreateResponse,
  UserDeactivateRequest,
  UsersFilterParams,
} from '@/types/user';

/**
 * Query keys for cache management
 */
export const usersManagementKeys = {
  all: ['usersManagement'] as const,
  lists: () => [...usersManagementKeys.all, 'list'] as const,
  list: (filters?: UsersFilterParams) => [...usersManagementKeys.lists(), filters] as const,
  details: () => [...usersManagementKeys.all, 'detail'] as const,
  detail: (id: string) => [...usersManagementKeys.details(), id] as const,
  byCompany: (companyId: string) => [...usersManagementKeys.all, 'company', companyId] as const,
};

/**
 * Fetch all users (superuser only)
 */
export const useAllUsersQuery = (filters?: UsersFilterParams) => {
  return useQuery<UserListItem[]>({
    queryKey: usersManagementKeys.list(filters),
    queryFn: () => getAllUsers(filters),
  });
};

/**
 * Fetch users by company
 */
export const useCompanyUsersQuery = (
  companyId: string,
  filters?: UsersFilterParams,
  enabled: boolean = true
) => {
  return useQuery<UserListItem[]>({
    queryKey: usersManagementKeys.byCompany(companyId),
    queryFn: () => getUsersByCompany(companyId, filters),
    enabled,
  });
};

/**
 * Fetch user details
 */
export const useUserDetailsQuery = (userId: string, enabled: boolean = true) => {
  return useQuery<UserDetail>({
    queryKey: usersManagementKeys.detail(userId),
    queryFn: () => getUser(userId),
    enabled,
  });
};

/**
 * Create new user
 */
export const useCreateUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<UserCreateResponse, Error, UserCreateRequest>({
    mutationFn: createUser,
    onSuccess: () => {
      // Invalidate all user lists to refetch
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.all });
    },
  });
};

/**
 * Update user
 */
export const useUpdateUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<
    UserDetail,
    Error,
    { userId: string; data: UserUpdateRequest }
  >({
    mutationFn: ({ userId, data }) => updateUser(userId, data),
    onSuccess: (data) => {
      // Update specific user in cache
      queryClient.setQueryData(usersManagementKeys.detail(data.id), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.all });
    },
  });
};

/**
 * Deactivate user (soft delete)
 */
export const useDeactivateUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<
    UserDetail,
    Error,
    { userId: string; data?: UserDeactivateRequest }
  >({
    mutationFn: ({ userId, data }) => deactivateUser(userId, data),
    onSuccess: (data) => {
      // Update specific user in cache
      queryClient.setQueryData(usersManagementKeys.detail(data.id), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.all });
    },
  });
};

/**
 * Delete user (hard delete, superuser only)
 */
export const useDeleteUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteUser,
    onSuccess: (_, userId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: usersManagementKeys.detail(userId) });
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.all });
    },
  });
};

/**
 * Reactivate user
 */
export const useReactivateUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<UserDetail, Error, string>({
    mutationFn: reactivateUser,
    onSuccess: (data) => {
      // Update specific user in cache
      queryClient.setQueryData(usersManagementKeys.detail(data.id), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.lists() });
      queryClient.invalidateQueries({ queryKey: usersManagementKeys.all });
    },
  });
};

/**
 * Reset user password
 */
export const useResetUserPasswordMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<
    UserDetail,
    Error,
    { userId: string; newPassword: string }
  >({
    mutationFn: ({ userId, newPassword }) => resetUserPassword(userId, newPassword),
    onSuccess: (data) => {
      // Update specific user in cache
      queryClient.setQueryData(usersManagementKeys.detail(data.id), data);
    },
  });
};
