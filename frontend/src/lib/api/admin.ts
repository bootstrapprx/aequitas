import { api } from '../api';
import type { User } from '../../types/user';
import type { SystemSettings, SystemSettingsUpdate } from '../../types/admin';

/**
 * Admin API Client
 * All endpoints require superuser privileges
 */

export const adminApi = {
  // User Management
  getAllUsers: async (): Promise<User[]> => {
    const token = localStorage.getItem('token');
    return api.get<User[]>('/admin/users', {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  promoteUser: async (userId: string): Promise<User> => {
    const token = localStorage.getItem('token');
    return api.put<User>(`/admin/users/${userId}/promote`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  demoteUser: async (userId: string): Promise<User> => {
    const token = localStorage.getItem('token');
    return api.put<User>(`/admin/users/${userId}/demote`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  // System Settings
  getSettings: async (): Promise<SystemSettings> => {
    const token = localStorage.getItem('token');
    return api.get<SystemSettings>('/admin/settings', {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  updateSettings: async (settings: SystemSettingsUpdate): Promise<SystemSettings> => {
    const token = localStorage.getItem('token');
    return api.put<SystemSettings>('/admin/settings', settings, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },
};
