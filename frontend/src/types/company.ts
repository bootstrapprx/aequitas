export type OnboardingStatus = 'DRAFT' | 'TEMPLATE_SELECTED' | 'CHART_READY' | 'CHART_FINALIZED' | 'ACTIVE';
export type KernelLayer = 'L0' | 'L1' | 'L2';

export interface Company {
  id: string;
  name: string;
  ucid: string;
  trade_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  currency?: string | null;
  timezone?: string | null;
  tax_id?: string | null;
  industry?: string | null;
  description?: string | null;
  legal_nature?: string | null;
  economic_activity?: string | null;
  is_standalone?: boolean | null;
  created_at?: string;
  is_active?: boolean;

  // Onboarding fields
  onboarding_status: OnboardingStatus;
  onboarding_current_step?: number;
  onboarding_started_at?: string | null;
  onboarding_completed_at?: string | null;
  kernel_version?: string | null;
  kernel_layer?: KernelLayer | null;
}

export interface CompanyCreate {
  name: string;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  tax_id?: string | null;
  industry?: string | null;
  description?: string | null;
}

export interface CompanyUpdate extends Partial<CompanyCreate> { }

export interface CompanyInactivate {
  confirmation: string;
}
