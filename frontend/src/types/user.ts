export interface User {
  id: string;
  user_uid: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  preferred_company_id?: string;
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

