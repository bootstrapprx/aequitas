import { api } from '@/lib/api';

export type MappingReviewItem = {
  id: string;
  company_account: {
    id: string;
    code: string;
    name?: string;
    description?: string;
  };
  master_account?: {
    id?: string;
    code?: string;
    description?: string;
  };
  confidence: number;
  mapping_status?: string;
  decision_status: string;
  decision_reason?: string;
  decided_at?: string;
  decided_by?: string;
  status: string;
  notes?: string;
};

export const getPendingMappings = (companyId: string) =>
  api.get<MappingReviewItem[]>(`/integrations/mapping-review/pending`, {
    params: { company_id: companyId },
  });

export const acceptMapping = (mappingId: string, reason: string) =>
  api.post<MappingReviewItem>(`/integrations/mapping-review/${mappingId}/accept`, { reason });

export const overrideMapping = (mappingId: string, masterAccountId: string, reason: string) =>
  api.post<MappingReviewItem>(`/integrations/mapping-review/${mappingId}/override`, {
    reason,
    master_account_id: masterAccountId,
  });

export const rejectMapping = (mappingId: string, reason: string) =>
  api.post<MappingReviewItem>(`/integrations/mapping-review/${mappingId}/reject`, { reason });
