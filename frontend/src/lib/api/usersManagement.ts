/**
 * API client for Users Management module.
 * Handles all user CRUD operations with company assignments and permissions.
 */
import { api } from '../api';
import {
  UserListItem,
  UserDetail,
  UserCreateRequest,
  UserUpdateRequest,
  UserCreateResponse,
  UserDeactivateRequest,
  UsersFilterParams,
} from '../../types/user';

/**
 * Get authentication token from localStorage
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * List all users in the system (superuser only)
 */
export const getAllUsers = async (
  params?: UsersFilterParams
): Promise<UserListItem[]> => {
  return api.get<UserListItem[]>('/admin/users', {
    headers: getAuthHeaders(),
    params: params as Record<string, string | number>,
  });
};

/**
 * List users belonging to a specific company
 */
export const getUsersByCompany = async (
  companyId: string,
  params?: UsersFilterParams
): Promise<UserListItem[]> => {
  return api.get<UserListItem[]>(`/companies/${companyId}/users`, {
    headers: getAuthHeaders(),
    params: params as Record<string, string | number>,
  });
};

/**
 * Get detailed information about a specific user
 */
export const getUser = async (userId: string): Promise<UserDetail> => {
  return api.get<UserDetail>(`/users/${userId}`, {
    headers: getAuthHeaders(),
  });
};

/**
 * Create a new user with company assignments
 */
export const createUser = async (
  data: UserCreateRequest
): Promise<UserCreateResponse> => {
  return api.post<UserCreateResponse>('/users', data, {
    headers: getAuthHeaders(),
  });
};

/**
 * Update user information and company assignments
 */
export const updateUser = async (
  userId: string,
  data: UserUpdateRequest
): Promise<UserDetail> => {
  return api.put<UserDetail>(`/users/${userId}`, data, {
    headers: getAuthHeaders(),
  });
};

/**
 * Deactivate a user (soft delete)
 */
export const deactivateUser = async (
  userId: string,
  data?: UserDeactivateRequest
): Promise<UserDetail> => {
  return api.post<UserDetail>(`/users/${userId}/deactivate`, data || {}, {
    headers: getAuthHeaders(),
  });
};

/**
 * Permanently delete a user (superuser only)
 */
export const deleteUser = async (userId: string): Promise<void> => {
  return api.delete<void>(`/users/${userId}`, {
    headers: getAuthHeaders(),
  });
};

/**
 * Reactivate a deactivated user
 */
export const reactivateUser = async (userId: string): Promise<UserDetail> => {
  return api.put<UserDetail>(
    `/users/${userId}`,
    { is_active: true },
    {
      headers: getAuthHeaders(),
    }
  );
};

/**
 * Reset user password (generate new temporary password)
 */
export const resetUserPassword = async (
  userId: string,
  newPassword: string
): Promise<UserDetail> => {
  return api.put<UserDetail>(
    `/users/${userId}`,
    { password: newPassword },
    {
      headers: getAuthHeaders(),
    }
  );
};
