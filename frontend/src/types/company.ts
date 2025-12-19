export type OnboardingStatus = 'NOT_STARTED' | 'MATERIALIZING' | 'ACTIVE';

export interface Company {
  id: string;
  name: string;
  ucid: string;
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
  created_at?: string;
  is_active?: boolean;

  // Onboarding fields
  onboarding_status: OnboardingStatus;
  onboarding_current_step?: number;
  onboarding_started_at?: string | null;
  onboarding_completed_at?: string | null;
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
