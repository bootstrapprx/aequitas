// frontend/src/types/masterchart.ts

export interface MasterAccount {
  id: string; // Assuming UUIDs are strings
  code: string;
  description: string;
  category: string;
  type: 'H' | 'D'; // Header or Detail
  level: number;
  parent_code: string | null;
  parent_id?: string | null;
  notes?: string | null;
  start_date?: string | null; // ISO date string
  end_date?: string | null; // ISO date string
}

export type MasterAccountCreate = Omit<MasterAccount, 'id' | 'level'>;

export interface MasterAccountNode extends MasterAccount {
  children: MasterAccountNode[];
}

export interface MasterChartStats {
    total_accounts: number;
    header_count: number;
    detail_count: number;
    max_depth: number;
    orphans: number;
    missing_parents: string[];
    needs_rebuild: boolean;
}