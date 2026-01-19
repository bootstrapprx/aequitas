// frontend/src/components/dashboard/DashboardLayout.tsx
import { Outlet } from "react-router-dom";
import AequitasSidebar from "./AequitasSidebar";
import CompanySelector from "@/components/company/CompanySelector";
import { ManualModeProvider } from "@/contexts/ManualModeContext";
import { useDashboardContext, shouldShowCompanySelector } from "@/hooks/useDashboardContext";

/**
 * DashboardLayout - Main application shell
 * 
 * CANONICAL RULES (per stability patch):
 * - Company selector HIDDEN if user has 0 or 1 companies
 * - Company selector SHOWN only if user has 2+ companies
 * - No "you have access to one company" messaging
 */
const DashboardLayout = () => {
  const { data: context, isLoading } = useDashboardContext();

  // Determine if selector should be shown (BACKEND AUTHORITY)
  const showSelector = context ? shouldShowCompanySelector(context.total_companies) : false;

  return (
    <ManualModeProvider>
      <div className="flex min-h-screen bg-background">
        <AequitasSidebar />
        <main className="flex-1 overflow-y-auto">
          {/* Company Selector Header Bar - CONDITIONAL on total_companies */}
          {showSelector && (
            <div className="sticky top-0 z-20 bg-background/95 backdrop-blur-sm border-b border-border px-8 py-4">
              <div className="max-w-xs">
                <CompanySelector />
              </div>
            </div>
          )}

          {/* Page Content */}
          <Outlet />
        </main>
      </div>
    </ManualModeProvider>
  );
};

export default DashboardLayout;
