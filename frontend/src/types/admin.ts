export interface SystemSettings {
  id: number;
  maintenance_mode: boolean;
  allow_public_signup: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemSettingsUpdate {
  maintenance_mode?: boolean;
  allow_public_signup?: boolean;
}
