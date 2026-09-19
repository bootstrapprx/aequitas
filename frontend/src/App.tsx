import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ErrorBoundary";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
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
import { SessionLogger } from "./components/SessionLogger";

// General Pages (Lazy Loaded)
const Landing = lazy(() => import("./pages/Landing"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const MetatheosLanding = lazy(() => import("./pages/metatheos/Landing"));
const MetatheosLogin = lazy(() => import("./pages/metatheos/Login"));
const MetatheosHome = lazy(() => import("./pages/metatheos/Home"));
const MetatheosPhases = lazy(() => import("./pages/metatheos/Phases"));
const MetatheosTimeline = lazy(() => import("./pages/metatheos/Timeline"));
const MetatheosPlaceholder = lazy(() => import("./pages/metatheos/Placeholder"));
const NotFound = lazy(() => import("./pages/NotFound"));

// Dashboard Pages (Lazy Loaded)
const DashboardPage = lazy(() => import("./pages/dashboard/DashboardPage"));
const CompanyDashboard = lazy(() => import("./pages/dashboard/CompanyDashboard"));
const FinancialDashboard = lazy(() => import("./pages/dashboard/FinancialDashboard"));
const Dashboard = lazy(() => import("./pages/dashboard/Dashboard"));

// Registration Module (Lazy Loaded)
const Companies = lazy(() => import("./pages/Companies"));
const CompanyRegistration = lazy(() => import("./pages/companies/CompanyRegistration"));
const UsersListPage = lazy(() => import("./pages/registration/users/UsersListPage"));

// Chart of Accounts Module (Lazy Loaded)
const CompanyChartPage = lazy(() => import("./pages/chartofaccounts/CompanyChartPage"));
const MasterChartDashboard = lazy(() => import("./pages/masterchart/MasterChartDashboard"));
const MasterChartTreePage = lazy(() => import("./pages/masterchart/MasterChartTreePage"));
const MasterChartInteractivePage = lazy(() => import("./pages/masterchart/MasterChartInteractivePage"));
const MasterChartImportPage = lazy(() => import("./components/integrations/masterchart/MasterChartImportPage"));
const MasterChartExportPage = lazy(() => import("./components/integrations/masterchart/MasterChartExportPage"));
const Mappings = lazy(() => import("./pages/Mappings"));
const OrganizerPage = lazy(() => import("./pages/organizer/OrganizerPage"));
const OrganizerReviewPage = lazy(() => import("./pages/organizer/OrganizerReviewPage"));
const MappingReviewPage = lazy(() => import("./pages/integrations/MappingReviewPage"));

// Accountancy Module (Lazy Loaded)
const DailyLedgerPage = lazy(() => import("./pages/accountancy/ledger/DailyLedgerPage"));
const JournalEntriesPage = lazy(() => import("./pages/accountancy/journal/JournalEntriesPage"));
const TrialBalancePage = lazy(() => import("./pages/accountancy/trial-balance/TrialBalancePage"));
const FiscalPeriodsPage = lazy(() => import("./pages/accountancy/fiscal-periods/FiscalPeriodsPage"));

// Reports Module (Lazy Loaded)
const FinancialStatementsPage = lazy(() => import("./pages/reports/statements/FinancialStatementsPage"));
const CustomReportsPage = lazy(() => import("./pages/reports/custom/CustomReportsPage"));
const ExportCenterPage = lazy(() => import("./pages/reports/export/ExportCenterPage"));

// Administration Module (Lazy Loaded)
const SuperuserPanel = lazy(() => import("./pages/admin/SuperuserPanel"));
const SystemSettingsPage = lazy(() => import("./pages/admin/system/SystemSettingsPage"));
const IntegrationsPage = lazy(() => import("./pages/admin/integrations/IntegrationsPage"));
const AuditLogPage = lazy(() => import("./pages/admin/audit/AuditLogPage"));
const AdminRequests = lazy(() => import("./pages/admin/AdminRequests"));

// Legacy pages (Lazy Loaded)
const UploadPage = lazy(() => import("./pages/Upload"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const TemplatesPage = lazy(() => import("./pages/Templates"));
const SnapshotsPage = lazy(() => import("./pages/snapshots/SnapshotsPage"));
const QuickBooksSyncPage = lazy(() => import("./pages/sync/QuickBooksSyncPage"));
const DocumentationPage = lazy(() => import("./pages/DocumentationPage"));

// Auth Pages (Lazy Loaded)
const LoginPage = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"));
const LegacyCompanyRegisterPage = lazy(() =>
  import("./pages/auth/RegisterPage").then((m) => ({ default: m.LegacyCompanyRegisterPage }))
);
const PaymentSuccessPage = lazy(() => import("./pages/auth/PaymentSuccessPage"));
const ChangePasswordPage = lazy(() => import("./pages/auth/ChangePasswordPage"));
const OAuthCallbackPage = lazy(() => import("./pages/auth/OAuthCallbackPage"));
const PostAuthSetupPage = lazy(() => import("./pages/auth/PostAuthSetupPage"));

// User Management Pages (Lazy Loaded)
const UsersPage = lazy(() => import("./pages/users/UsersPage"));
const PermissionsPage = lazy(() => import("./pages/permissions/PermissionsPage"));

// Groups Module (Lazy Loaded)
const GroupsList = lazy(() => import("./pages/groups/GroupsList"));
const GroupDetail = lazy(() => import("./pages/groups/GroupDetail"));

// Onboarding Module (Lazy Loaded)
const OnboardingWizard = lazy(() => import("./pages/onboarding/OnboardingWizard"));

const PageLoader = () => (
  <div className="flex h-[50vh] w-full items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
  </div>
);

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
                  <Suspense fallback={<PageLoader />}>
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
                        <Route
                          path="goals"
                          element={
                            <MetatheosPlaceholder
                              title="Goals"
                              description="Governance targets and checkpoints."
                            />
                          }
                        />
                        <Route path="timeline" element={<MetatheosTimeline />} />
                        <Route
                          path="audits"
                          element={
                            <MetatheosPlaceholder
                              title="Audits"
                              description="Review trails and attestations."
                            />
                          }
                        />
                        <Route
                          path="prompts"
                          element={
                            <MetatheosPlaceholder
                              title="Prompts"
                              description="Directive inputs and constraints."
                            />
                          }
                        />
                        <Route
                          path="assistant"
                          element={
                            <MetatheosPlaceholder
                              title="Assistant"
                              description="Guided analysis and synthesis."
                            />
                          }
                        />
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

                      {/* Change Password Route */}
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
                        <Route index element={<Navigate to="/dashboard" replace />} />
                        <Route path="dashboard" element={<CompanyDashboard />} />
                        <Route path="dashboard/company-overview" element={<CompanyDashboard />} />
                        <Route path="dashboard/intelligence" element={<Dashboard />} />
                        <Route path="dashboard/financial" element={<FinancialDashboard />} />
                        <Route path="dashboard/old" element={<DashboardPage />} />

                        {/* Registration Module */}
                        <Route path="companies" element={<Companies />} />
                        <Route path="companies/register" element={<CompanyRegistration />} />
                        <Route path="registration/users" element={<UsersListPage />} />

                        {/* Chart of Accounts Module (Unified) */}
                        <Route path="chartofaccounts" element={<CompanyChartPage />} />
                        <Route path="chartofaccounts/master" element={<MasterChartDashboard />} />
                        <Route path="chartofaccounts/master/tree" element={<MasterChartTreePage />} />
                        <Route
                          path="chartofaccounts/master/interactive"
                          element={<MasterChartInteractivePage />}
                        />
                        <Route path="chartofaccounts/mapping" element={<Mappings />} />
                        <Route path="chartofaccounts/import" element={<MasterChartImportPage />} />
                        <Route path="chartofaccounts/export" element={<MasterChartExportPage />} />
                        <Route path="chartofaccounts/organizer" element={<OrganizerPage />} />
                        <Route path="chartofaccounts/organizer/review" element={<OrganizerReviewPage />} />
                        <Route path="integrations/mapping-review" element={<MappingReviewPage />} />

                        {/* Legacy ChartForge Routes (redirect to new paths) */}
                        <Route path="chartforge/masterchart" element={<CompanyChartPage />} />
                        <Route path="chartforge/masterchart/tree" element={<MasterChartTreePage />} />
                        <Route
                          path="chartforge/masterchart/interactive"
                          element={<MasterChartInteractivePage />}
                        />
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
                  </Suspense>
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
