import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ErrorBoundary";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { AuthProvider } from "@/contexts/AuthContext";
import { CompanyProvider } from "@/contexts/CompanyContext";
import { MetatheosAuthProvider } from "@/contexts/MetatheosAuthContext";
import { MetatheosThemeProvider } from "@/contexts/MetatheosThemeContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import MetatheosProtectedRoute from "@/components/metatheos/MetatheosProtectedRoute";
import PasswordResetGuard from "@/components/auth/PasswordResetGuard";
import OnboardingGuard from "@/components/auth/OnboardingGuard";

// Layouts
import DashboardLayout from "./components/dashboard/DashboardLayout";
import MetatheosAppShell from "./components/metatheos/AppShell";

// General Pages
import Landing from "./pages/Landing";
import LandingPage from "./pages/LandingPage";
import MetatheosLanding from "./pages/metatheos/Landing";
import MetatheosLogin from "./pages/metatheos/Login";
import MetatheosHome from "./pages/metatheos/Home";
import MetatheosPhases from "./pages/metatheos/Phases";
import MetatheosTimeline from "./pages/metatheos/Timeline";
import MetatheosPlaceholder from "./pages/metatheos/Placeholder";
import NotFound from "./pages/NotFound";
import { SessionLogger } from "./components/SessionLogger";

// Dashboard
import DashboardPage from "./pages/dashboard/DashboardPage";
import CompanyDashboard from "./pages/dashboard/CompanyDashboard";

// Registration Module
import Companies from "./pages/Companies";
import CompanyRegistration from "./pages/companies/CompanyRegistration";
import UsersListPage from "./pages/registration/users/UsersListPage";

// Chart of Accounts Module
import CompanyChartPage from "./pages/chartofaccounts/CompanyChartPage";
import MasterChartDashboard from "./pages/masterchart/MasterChartDashboard";
import MasterChartTreePage from "./pages/masterchart/MasterChartTreePage";
import MasterChartInteractivePage from "./pages/masterchart/MasterChartInteractivePage";
import MasterChartImportPage from "./components/integrations/masterchart/MasterChartImportPage";
import MasterChartExportPage from "./components/integrations/masterchart/MasterChartExportPage";
import Mappings from "./pages/Mappings";
import OrganizerPage from "./pages/organizer/OrganizerPage";
import OrganizerReviewPage from "./pages/organizer/OrganizerReviewPage";
import MappingReviewPage from "./pages/integrations/MappingReviewPage";

// Accountancy Module
import DailyLedgerPage from "./pages/accountancy/ledger/DailyLedgerPage";
import JournalEntriesPage from "./pages/accountancy/journal/JournalEntriesPage";
import TrialBalancePage from "./pages/accountancy/trial-balance/TrialBalancePage";
import FiscalPeriodsPage from "./pages/accountancy/fiscal-periods/FiscalPeriodsPage";

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
import RegisterPage, { LegacyCompanyRegisterPage } from "./pages/auth/RegisterPage";
import PaymentSuccessPage from "./pages/auth/PaymentSuccessPage";
import ChangePasswordPage from "./pages/auth/ChangePasswordPage";
import OAuthCallbackPage from "./pages/auth/OAuthCallbackPage";
import PostAuthSetupPage from "./pages/auth/PostAuthSetupPage";

// User Management Pages (legacy)
import UsersPage from "./pages/users/UsersPage";
import PermissionsPage from "./pages/permissions/PermissionsPage";

// Groups Module
import GroupsList from "./pages/groups/GroupsList";
import GroupDetail from "./pages/groups/GroupDetail";

// Onboarding Module (Phase 5)
import OnboardingWizard from "./pages/onboarding/OnboardingWizard";

const App = () => (
  <ErrorBoundary>
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      storageKey="aequitas-theme"
    >
      <TooltipProvider>
        <AuthProvider>
          <CompanyProvider>
            <MetatheosAuthProvider>
              <MetatheosThemeProvider>
                <Toaster />
                <Sonner />
                <BrowserRouter
                  future={{
                    v7_startTransition: true,
                    v7_relativeSplatPath: true,
                  }}
                >
                  <SessionLogger />
                  <Routes>
                    <Route path="/metatheos" element={<MetatheosLanding />} />
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/landing-old" element={<Landing />} />

                    {/* Metatheos Auth Routes */}
                    <Route path="/metatheos/login" element={<MetatheosLogin />} />

                    {/* Metatheos Protected Routes */}
                    <Route
                      path="/metatheos"
                      element={
                        <MetatheosProtectedRoute>
                          <MetatheosAppShell />
                        </MetatheosProtectedRoute>
                      }
                    >
                      <Route index element={<MetatheosHome />} />
                      <Route path="home" element={<MetatheosHome />} />
                      <Route path="phases" element={<MetatheosPhases />} />
                      <Route path="goals" element={<MetatheosPlaceholder title="Goals" description="Governance targets and checkpoints." />} />
                      <Route path="timeline" element={<MetatheosTimeline />} />
                      <Route path="audits" element={<MetatheosPlaceholder title="Audits" description="Review trails and attestations." />} />
                      <Route path="prompts" element={<MetatheosPlaceholder title="Prompts" description="Directive inputs and constraints." />} />
                      <Route path="assistant" element={<MetatheosPlaceholder title="Assistant" description="Guided analysis and synthesis." />} />
                    </Route>

                    {/* Auth Routes */}
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/register/company" element={<LegacyCompanyRegisterPage />} />
                    <Route path="/auth/payment-success" element={<PaymentSuccessPage />} />
                    <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
                    <Route
                      path="/auth/setup"
                      element={
                        <ProtectedRoute>
                          <PostAuthSetupPage />
                        </ProtectedRoute>
                      }
                    />

                    {/* Change Password Route - Protected but accessible even with force_password_reset */}
                    <Route
                      path="/change-password"
                      element={
                        <ProtectedRoute>
                          <ChangePasswordPage />
                        </ProtectedRoute>
                      }
                    />

                    {/* Phase 5 - Onboarding Wizard (Outside Dashboard Layout) */}
                    <Route
                      path="/onboarding/:companyId"
                      element={
                        <ProtectedRoute>
                          <OnboardingWizard />
                        </ProtectedRoute>
                      }
                    />

                    {/* Protected Dashboard Routes */}
                    <Route
                      path="/"
                      element={
                        <ProtectedRoute>
                          <PasswordResetGuard>
                            <OnboardingGuard>
                              <DashboardLayout />
                            </OnboardingGuard>
                          </PasswordResetGuard>
                        </ProtectedRoute>
                      }
                    >
                      {/* Main Dashboard */}
                      <Route path="dashboard" element={<CompanyDashboard />} />
                      <Route path="dashboard/overview" element={<CompanyDashboard />} />
                      <Route path="dashboard/old" element={<DashboardPage />} />

                      {/* Registration Module */}
                      <Route path="companies" element={<Companies />} />
                      <Route path="companies/register" element={<CompanyRegistration />} />
                      <Route path="registration/users" element={<UsersListPage />} />



                      {/* Chart of Accounts Module (Unified) */}
                      <Route path="chartofaccounts" element={<CompanyChartPage />} />
                      <Route path="chartofaccounts/master" element={<MasterChartDashboard />} />
                      <Route path="chartofaccounts/master/tree" element={<MasterChartTreePage />} />
                      <Route path="chartofaccounts/master/interactive" element={<MasterChartInteractivePage />} />
                      <Route path="chartofaccounts/mapping" element={<Mappings />} />
                      <Route path="chartofaccounts/import" element={<MasterChartImportPage />} />
                      <Route path="chartofaccounts/export" element={<MasterChartExportPage />} />
                      <Route path="chartofaccounts/organizer" element={<OrganizerPage />} />
                      <Route path="chartofaccounts/organizer/review" element={<OrganizerReviewPage />} />
                      <Route path="integrations/mapping-review" element={<MappingReviewPage />} />

                      {/* Legacy ChartForge Routes (redirect to new paths) */}
                      <Route path="chartforge/masterchart" element={<CompanyChartPage />} />
                      <Route path="chartforge/masterchart/tree" element={<MasterChartTreePage />} />
                      <Route path="chartforge/masterchart/interactive" element={<MasterChartInteractivePage />} />
                      <Route path="chartforge/masterchart/import" element={<MasterChartImportPage />} />
                      <Route path="chartforge/masterchart/export" element={<MasterChartExportPage />} />
                      <Route path="chartforge/mapping" element={<Mappings />} />
                      <Route path="chartforge/import" element={<MasterChartImportPage />} />
                      <Route path="chartforge/organizer" element={<OrganizerPage />} />
                      <Route path="chartforge/organizer/review" element={<OrganizerReviewPage />} />
                      <Route path="registration/coa" element={<CompanyChartPage />} />

                      {/* Accountancy Module */}
                      <Route path="accountancy/ledger" element={<DailyLedgerPage />} />
                      <Route path="accountancy/journal" element={<JournalEntriesPage />} />
                      <Route path="accountancy/trial-balance" element={<TrialBalancePage />} />
                      <Route path="accountancy/fiscal-periods" element={<FiscalPeriodsPage />} />

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

                      {/* Groups Module */}
                      <Route path="groups" element={<GroupsList />} />
                      <Route path="groups/:groupId" element={<GroupDetail />} />

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
              </MetatheosThemeProvider>
            </MetatheosAuthProvider>
          </CompanyProvider>
        </AuthProvider>
      </TooltipProvider>
    </ThemeProvider>
  </ErrorBoundary>
);

export default App;
