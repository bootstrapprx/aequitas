export interface User {
  id: string;
  user_uid: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  preferred_company_id?: string;
  force_password_reset?: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  company_ids?: string[];
  is_initial_signup?: boolean;
  company_name?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  company_ids?: string[];
  preferred_company_id?: string;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface UserCompany {
  id: string;
  user_id: string;
  company_id: string;
  is_admin: boolean;
  can_edit: boolean;
  can_view: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCompanyCreate {
  user_id: string;
  company_id: string;
  is_admin?: boolean;
  can_edit?: boolean;
  can_view?: boolean;
}

export interface UserCompanyUpdate {
  is_admin?: boolean;
  can_edit?: boolean;
  can_view?: boolean;
}

export interface UserWithPermissions extends User {
  companies?: UserCompany[];
}

// Users Management Module Types

export interface CompanyInfo {
  id: string;
  name: string;
  ucid: string;
  is_admin: boolean;
}

export interface UserListItem {
  id: string;
  email: string;
  user_uid: string;
  is_active: boolean;
  is_superuser: boolean;
  companies: CompanyInfo[];
  last_login?: string;
  created_at: string;
}

export interface UserDetail {
  id: string;
  email: string;
  user_uid: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  preferred_company_id?: string;
  companies: CompanyInfo[];
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyRoleAssignment {
  company_id: string;
  is_admin: boolean;
  can_edit: boolean;
  can_view: boolean;
}

export interface UserCreateRequest {
  email: string;
  password?: string;
  company_ids: string[];
  company_roles?: CompanyRoleAssignment[];
  is_active: boolean;
}

export interface UserUpdateRequest {
  email?: string;
  is_active?: boolean;
  company_ids?: string[];
  company_roles?: CompanyRoleAssignment[];
  password?: string;
}

export interface UserCreateResponse {
  user: UserDetail;
  temporary_password?: string;
}

export interface UserDeactivateRequest {
  reason?: string;
}

export interface UsersFilterParams {
  company_id?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

