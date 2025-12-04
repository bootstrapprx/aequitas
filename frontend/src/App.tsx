import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ErrorBoundary";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";

// Layouts
import DashboardLayout from "./components/dashboard/DashboardLayout";

// General Pages
import Landing from "./pages/Landing";
import NotFound from "./pages/NotFound";

// Dashboard
import DashboardPage from "./pages/dashboard/DashboardPage";

// Registration Module
import Companies from "./pages/Companies";
import CompanyRegistration from "./pages/companies/CompanyRegistration";
import UsersListPage from "./pages/registration/users/UsersListPage";
import SimpleCoAPage from "./pages/registration/coa/SimpleCoAPage";

// ChartForge Module (formerly masterchart)
import MasterChartDashboard from "./pages/masterchart/MasterChartDashboard";
import MasterChartTreePage from "./pages/masterchart/MasterChartTreePage";
import MasterChartInteractivePage from "./pages/masterchart/MasterChartInteractivePage";
import MasterChartImportPage from "./components/integrations/masterchart/MasterChartImportPage";
import MasterChartExportPage from "./components/integrations/masterchart/MasterChartExportPage";
import Mappings from "./pages/Mappings";
import OrganizerPage from "./pages/organizer/OrganizerPage";
import OrganizerReviewPage from "./pages/organizer/OrganizerReviewPage";

// Accountancy Module
import DailyLedgerPage from "./pages/accountancy/ledger/DailyLedgerPage";
import JournalEntriesPage from "./pages/accountancy/journal/JournalEntriesPage";
import TrialBalancePage from "./pages/accountancy/trial-balance/TrialBalancePage";

// Reports Module
import FinancialStatementsPage from "./pages/reports/statements/FinancialStatementsPage";
import CustomReportsPage from "./pages/reports/custom/CustomReportsPage";
import ExportCenterPage from "./pages/reports/export/ExportCenterPage";

// Administration Module
import SuperuserPanel from "./pages/admin/SuperuserPanel";
import SystemSettingsPage from "./pages/admin/system/SystemSettingsPage";
import IntegrationsPage from "./pages/admin/integrations/IntegrationsPage";
import AuditLogPage from "./pages/admin/audit/AuditLogPage";
import AdminRequests from "./pages/admin/AdminRequests";

// Legacy pages (to be reorganized or removed)
import UploadPage from "./pages/Upload";
import SettingsPage from "./pages/SettingsPage";
import TemplatesPage from "./pages/Templates";
import SnapshotsPage from "./pages/snapshots/SnapshotsPage";
import QuickBooksSyncPage from "./pages/sync/QuickBooksSyncPage";
import DocumentationPage from "./pages/DocumentationPage";

// Auth Pages
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";

// User Management Pages (legacy)
import UsersPage from "./pages/users/UsersPage";
import PermissionsPage from "./pages/permissions/PermissionsPage";

const App = () => (
  <ErrorBoundary>
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <TooltipProvider>
        <AuthProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />

              {/* Auth Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Dashboard Routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                {/* Main Dashboard */}
                <Route path="dashboard" element={<DashboardPage />} />

                {/* Registration Module */}
                <Route path="companies" element={<Companies />} />
                <Route path="companies/register" element={<CompanyRegistration />} />
                <Route path="registration/users" element={<UsersListPage />} />
                <Route path="registration/coa" element={<SimpleCoAPage />} />

                {/* ChartForge Module */}
                <Route path="chartforge/masterchart" element={<MasterChartDashboard />} />
                <Route path="chartforge/masterchart/tree" element={<MasterChartTreePage />} />
                <Route path="chartforge/masterchart/interactive" element={<MasterChartInteractivePage />} />
                <Route path="chartforge/masterchart/import" element={<MasterChartImportPage />} />
                <Route path="chartforge/masterchart/export" element={<MasterChartExportPage />} />
                <Route path="chartforge/mapping" element={<Mappings />} />
                <Route path="chartforge/import" element={<MasterChartImportPage />} />
                <Route path="chartforge/organizer" element={<OrganizerPage />} />
                <Route path="chartforge/organizer/review" element={<OrganizerReviewPage />} />

                {/* Accountancy Module */}
                <Route path="accountancy/ledger" element={<DailyLedgerPage />} />
                <Route path="accountancy/journal" element={<JournalEntriesPage />} />
                <Route path="accountancy/trial-balance" element={<TrialBalancePage />} />

                {/* Reports Module */}
                <Route path="reports/statements" element={<FinancialStatementsPage />} />
                <Route path="reports/custom" element={<CustomReportsPage />} />
                <Route path="reports/export" element={<ExportCenterPage />} />

                {/* Administration Module */}
                <Route path="admin/superuser" element={<SuperuserPanel />} />
                <Route path="admin/system" element={<SystemSettingsPage />} />
                <Route path="admin/integrations" element={<IntegrationsPage />} />
                <Route path="admin/audit" element={<AuditLogPage />} />
                <Route path="admin/requests" element={<AdminRequests />} />

                {/* Legacy Routes (backward compatibility) */}
                <Route path="masterchart" element={<MasterChartDashboard />} />
                <Route path="masterchart/tree" element={<MasterChartTreePage />} />
                <Route path="masterchart/interactive" element={<MasterChartInteractivePage />} />
                <Route path="masterchart/import" element={<MasterChartImportPage />} />
                <Route path="masterchart/export" element={<MasterChartExportPage />} />
                <Route path="organizer" element={<OrganizerPage />} />
                <Route path="organizer/review" element={<OrganizerReviewPage />} />
                <Route path="mappings" element={<Mappings />} />
                <Route path="snapshots" element={<SnapshotsPage />} />
                <Route path="sync/quickbooks" element={<QuickBooksSyncPage />} />
                <Route path="upload" element={<UploadPage />} />
                <Route path="templates" element={<TemplatesPage />} />
                <Route path="users" element={<UsersPage />} />
                <Route path="permissions" element={<PermissionsPage />} />

                {/* Settings */}
                <Route path="settings" element={<SettingsPage />} />

                {/* Documentation */}
                <Route path="docs" element={<DocumentationPage />} />
              </Route>

              {/* Catch-all */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </TooltipProvider>
    </ThemeProvider>
  </ErrorBoundary>
);

export default App;
