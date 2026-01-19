/**
 * User Context Hook - Dashboard Authority
 * 
 * CANON II: Backend Creates Truth
 * 
 * This hook provides THE ONLY source of truth for dashboard state.
 * UI must NEVER infer state from absence or side effects.
 * 
 * All dashboard widgets must wait for context before rendering.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface UserContext {
    // User identity
    user_id: string;
    email: string;
    full_name: string | null;

    // Current company (OPERATIONAL CONTEXT)
    current_company_id: string | null;
    current_company_name: string | null;
    current_company_ucid: string | null;
    total_companies: number;

    // Accounting state (CANONICAL - no inference)
    accounting_active: boolean;  // True = activated
    onboarding_status: string | null;

    // Kernel binding (CANONICAL - no guessing)
    kernel_version: string | null;  // e.g., "2025.2"
    kernel_layer: string | null;    // "L0" | "L1" | "L2"
    protected_structure: boolean;   // kernel-bound + locked

    // Chart state (BACKEND COUNT - not inferred)
    total_accounts: number;

    // Fiscal state (BACKEND COUNT - not inferred)
    open_periods: number;
}

/**
 * useDashboardContext - Get authoritative dashboard state
 * 
 * Rules:
 * - Returns backend truth ONLY
 * - No optimistic rendering
 * - Widgets must wait for isLoading = false
 * - No inference from localStorage or cache
 */
export function useDashboardContext() {
    return useQuery<UserContext>({
        queryKey: ['dashboard-context'],
        queryFn: async () => {
            const response = await api.get<UserContext>('/me/context');
            return response as UserContext;
        },
        staleTime: 1000 * 60, // 1 minute
        refetchOnWindowFocus: true,
    });
}

/**
 * Company Selector Visibility Rules (HARD):
 * 
 * - 0 companies: Don't show (onboarding only)
 * - 1 company: DON'T SHOW (no point)
 * - 2+ companies: SHOW selector
 */
export function shouldShowCompanySelector(totalCompanies: number): boolean {
    return totalCompanies >= 2;
}

/**
 * Dashboard Readiness Check
 * 
 * Dashboard should not render widgets until:
 * 1. Context is loaded
 * 2. User has a current company
 * 3. Company is ACTIVE
 */
export function isDashboardReady(
    context: UserContext | undefined,
    isLoading: boolean
): boolean {
    if (isLoading || !context) return false;
    if (!context.current_company_id) return false;
    if (!context.accounting_active) return false;
    return true;
}
