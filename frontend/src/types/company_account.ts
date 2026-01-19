// frontend/src/types/company_account.ts

export interface CompanyAccount {
  id: string;
  company_id: string;
  code: string;
  name: string | null;
  description: string;
  type: string;
  account_type: string | null;
  normal_balance: 'Debit' | 'Credit' | string;
  parent_id: string | null;
  mapped_master_account_id: string | null;
  template_account_id?: string | null;
  currency: string | null;
  is_active: boolean | null;
  is_locked: boolean | null;
  locked_at?: string | null;
  locked_reason?: string | null;
  locked_by?: string | null;
  json_data?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}
