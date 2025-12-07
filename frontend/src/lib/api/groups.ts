// frontend/src/lib/api/groups.ts
import { api } from '@/lib/api';

export interface GroupCompany {
  id: string;
  name: string;
  description?: string;
  owner_user_id: string;
  created_at: string;
  updated_at?: string;
}

export interface Company {
  id: string;
  name: string;
  ucid: string;
  email?: string;
  phone?: string;
  is_active: boolean;
}

export interface GroupCompanyWithMembers extends GroupCompany {
  companies: Company[];
}

export interface GroupCompanyCreate {
  name: string;
  description?: string;
}

export interface AddCompanyToGroupRequest {
  company_id: string;
}

export interface PropagateMappingsRequest {
  source_company_id: string;
  target_company_id?: string;
  force?: boolean;
}

export interface PropagateMappingsResponse {
  source_company_id: string;
  target_companies: number;
  source_mappings: number;
  created: number;
  updated: number;
  skipped: number;
}

export interface SUCreateCompanyRequest {
  name: string;
  email?: string;
  phone?: string;
  website?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  industry?: string;
  description?: string;
  group_company_id?: string;
}

export const groupsApi = {
  // List all groups
  async listGroups(): Promise<GroupCompany[]> {
    return api.get('/groups');
  },

  // Create a new group
  async createGroup(data: GroupCompanyCreate): Promise<GroupCompany> {
    return api.post('/groups', { body: data });
  },

  // Get a specific group with members
  async getGroup(groupId: string): Promise<GroupCompanyWithMembers> {
    return api.get(`/groups/${groupId}`);
  },

  // Add company to group
  async addCompanyToGroup(groupId: string, companyId: string): Promise<{ message: string; member_id: string }> {
    return api.post(`/groups/${groupId}/companies`, {
      body: { company_id: companyId }
    });
  },

  // Remove company from group
  async removeCompanyFromGroup(groupId: string, companyId: string): Promise<{ message: string }> {
    return api.delete(`/groups/${groupId}/companies/${companyId}`);
  },

  // Propagate mappings
  async propagateMappings(
    groupId: string,
    request: PropagateMappingsRequest
  ): Promise<PropagateMappingsResponse> {
    return api.post(`/groups/${groupId}/propagate-mappings`, { body: request });
  },

  // SU create company
  async suCreateCompany(data: SUCreateCompanyRequest): Promise<Company> {
    return api.post('/companies/su-create', { body: data });
  }
};
