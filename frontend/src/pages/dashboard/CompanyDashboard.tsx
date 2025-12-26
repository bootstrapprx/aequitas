import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  TrendingUp,
  Users,
  FileText,
  RefreshCw,
  Download,
  Settings,
  Bell,
  MoreVertical,
  ShieldCheck,
  CheckCircle2,
  X,
  Info,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useGetCompanies } from '@/integrations/queries/useCompanies';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useNavigate } from 'react-router-dom';

// Interfaces matching backend schema
interface CompanyChartStatus {
  master_chart_loaded: boolean;
  company_chart_initialized: boolean;
  account_count: number;
  mapping_coverage: number;
  onboarding_status: string;
}

interface DashboardActivity {
  id: string;
  user: string;
  action: string;
  timestamp: string; // ISO string from API
  type: string;
}

interface CompanyDashboardStats {
  chart_status: CompanyChartStatus;
  active_users_count: number;
  pending_reviews_count: number;
  recent_activity: DashboardActivity[];
  account_distribution: Record<string, number>;
}


const CompanyDashboard = () => {
  const { user, currentCompanyId, switchCompany } = useAuth();
  const navigate = useNavigate();
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(currentCompanyId || '');
  const [showPostActivationPanel, setShowPostActivationPanel] = useState(false);

  // Fetch companies
  const { data: companies, isLoading: isCompaniesLoading } = useGetCompanies();

  // Sync selected company from auth context
  useEffect(() => {
    if (currentCompanyId) {
      setSelectedCompanyId(currentCompanyId);
    }
  }, [currentCompanyId]);

  // Fetch Dashboard Stats (Canonical Fix: One aggregate endpoint)
  const { data: stats, isLoading: isStatsLoading } = useQuery({
    queryKey: ['company', 'dashboard-stats', selectedCompanyId],
    queryFn: () => api.get<CompanyDashboardStats>(`/companies/${selectedCompanyId}/dashboard-stats`),
    enabled: !!selectedCompanyId,
  });

  const handleCompanyChange = (companyId: string) => {
    setSelectedCompanyId(companyId);
    switchCompany(companyId);
  };

  const selectedCompany = companies?.find((c) => c.id === selectedCompanyId);
  const isLoading = isCompaniesLoading || (!!selectedCompanyId && isStatsLoading);
  const isActiveCompany = selectedCompany?.onboarding_status === 'ACTIVE' || selectedCompany?.is_active;

  const dismissalKey = useMemo(() => {
    if (!selectedCompanyId) return null;
    const userKey = user?.id || user?.user_uid || user?.email || 'anonymous';
    return `aequitas_post_activation_ack_${userKey}_${selectedCompanyId}`;
  }, [selectedCompanyId, user?.email, user?.id, user?.user_uid]);

  useEffect(() => {
    if (isActiveCompany && dismissalKey) {
      const stored = localStorage.getItem(dismissalKey);
      setShowPostActivationPanel(stored !== 'dismissed');
    } else {
      setShowPostActivationPanel(false);
    }
  }, [dismissalKey, isActiveCompany]);

  const acknowledgePanel = () => {
    if (dismissalKey) {
      localStorage.setItem(dismissalKey, 'dismissed');
    }
    setShowPostActivationPanel(false);
  };

  // Derived metrics from real data
  const chartStatus = stats?.chart_status;
  const totalAccounts = chartStatus?.account_count || 0;
  const mappedPercentage = chartStatus?.mapping_coverage || 0;
  const activeUsers = stats?.active_users_count || 0;
  const pendingReviews = stats?.pending_reviews_count || 0;
  const activities = stats?.recent_activity || [];
  const distribution = stats?.account_distribution || {};

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b sticky top-0 z-40">
        <div className="px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo + Company Selector */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Building2 className="h-6 w-6 text-primary" />
                <span className="text-xl font-bold text-foreground">aequitas</span>
              </div>
              <div className="h-8 w-px bg-border"></div>
              <div className="min-w-[250px]">
                <Select value={selectedCompanyId} onValueChange={handleCompanyChange} disabled={isCompaniesLoading}>
                  <SelectTrigger className="border-0 text-lg font-semibold text-foreground hover:bg-muted/50">
                    <SelectValue placeholder={isCompaniesLoading ? "Loading..." : "Select company..."} />
                  </SelectTrigger>
                  <SelectContent>
                    {companies?.map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        <div className="flex flex-col">
                          <span className="font-semibold">{company.name}</span>
                          <span className="text-xs text-gray-500">{company.ucid}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Center: Page Title */}
            <div>
              <h1 className="text-xl font-semibold text-foreground">Overview</h1>
            </div>

            {/* Right: Icon Toolbar */}
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="icon" className="hover:bg-muted">
                <RefreshCw className="h-5 w-5 text-muted-foreground" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-muted">
                <Download className="h-5 w-5 text-muted-foreground" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-muted">
                <Settings className="h-5 w-5 text-muted-foreground" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-primary/10">
                <Bell className="h-5 w-5 text-primary" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-muted">
                <MoreVertical className="h-5 w-5 text-muted-foreground" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-8 space-y-8">
        {isActiveCompany && (
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="outline" className="flex items-center gap-2 border-green-600 text-green-700 bg-green-50">
              <ShieldCheck className="h-4 w-4" />
              Accounting Active
            </Badge>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 text-sm text-muted-foreground border border-dashed border-border px-3 py-1.5 rounded-lg cursor-default">
                  <Info className="h-4 w-4" />
                  Protected structure
                </div>
              </TooltipTrigger>
              <TooltipContent>
                This structure is protected after activation.
              </TooltipContent>
            </Tooltip>
          </div>
        )}

        {/* Welcome Banner */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-gradient-to-r from-primary to-secondary border-0 text-primary-foreground">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">
                    Welcome back, {user?.email?.split('@')[0] || 'User'}!
                  </h2>
                  <p className="text-teal-50">
                    {selectedCompany
                      ? `Managing ${selectedCompany.name}`
                      : 'Select a company to get started'}
                  </p>
                </div>
                {chartStatus?.onboarding_status !== 'ready' && !!selectedCompanyId && (
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 text-center">
                    <div className="text-lg font-bold text-white mb-1">
                      {chartStatus?.onboarding_status === 'not_started' ? 'Setup Required' : 'Setup In Progress'}
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="w-full text-xs h-7"
                      onClick={() => window.location.href = `/onboarding/${selectedCompanyId}`}
                    >
                      Continue Setup
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {isActiveCompany && showPostActivationPanel && (
          <Card className="border border-border bg-muted/40">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle className="text-xl">Your accounting system is active.</CardTitle>
                <CardDescription className="mt-2 space-y-1 text-base text-foreground">
                  <p>Your chart of accounts and fiscal structure are now protected.</p>
                  <p>Accounting history cannot be rewritten.</p>
                  <p>You remain fully in control of all entries and decisions.</p>
                </CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={acknowledgePanel} aria-label="Dismiss post-activation summary">
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-foreground">Allowed actions</p>
                  <div className="space-y-2">
                    {['Record journal entries', 'View financial reports', 'Use Sandbox for planning'].map((action) => (
                      <div key={action} className="flex items-center gap-2 text-sm text-foreground">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span>{action}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-foreground">Explicit non-actions</p>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>The system will never post entries automatically.</p>
                    <p>No data is changed without your action.</p>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={acknowledgePanel}>Continue to dashboard</Button>
                <Button variant="outline" onClick={() => { acknowledgePanel(); navigate('/chartofaccounts'); }}>
                  Review accounting structure
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              <StatsCard
                title="Total Accounts"
                value={totalAccounts}
                subtitle="In chart of accounts"
                icon={FileText}
                color="teal"
              />
              <StatsCard
                title="Mapped Accounts"
                value={chartStatus?.company_chart_initialized ? Math.round((totalAccounts * mappedPercentage) / 100) : 0}
                subtitle={`${mappedPercentage}% completion`}
                icon={TrendingUp}
                trend={{ value: 12, isPositive: true }} // TODO: Real trend
                color="navy"
              />
              <StatsCard
                title="Active Users"
                value={activeUsers}
                subtitle="Team members"
                icon={Users}
                color="yellow"
              />
              <StatsCard
                title="Pending Mappings"
                value={pendingReviews}
                subtitle="Accounts to map"
                icon={Bell}
                color={pendingReviews > 0 ? "red" : "green"}
              />
            </motion.div>

            {/* Dashboard Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Account Distribution (Real Data) */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow bg-card text-card-foreground h-full">
                  <CardHeader>
                    <CardTitle className="text-foreground">Account Distribution</CardTitle>
                    <CardDescription className="text-muted-foreground">By category</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(distribution).map(([type, count]) => {
                        const percentage = totalAccounts > 0 ? Math.round((count / totalAccounts) * 100) : 0;
                        let colorClass = "bg-primary";
                        if (type === "Asset") colorClass = "bg-emerald-500";
                        if (type === "Liability") colorClass = "bg-red-500";
                        if (type === "Equity") colorClass = "bg-blue-500";
                        if (type === "Revenue") colorClass = "bg-green-500";
                        if (type === "Expense") colorClass = "bg-amber-500";

                        return (
                          <div key={type} className="space-y-1">
                            <div className="flex justify-between items-center text-sm">
                              <span className="font-medium">{type}</span>
                              <div className="flex gap-2 text-muted-foreground">
                                <span>{count}</span>
                                <span>({percentage}%)</span>
                              </div>
                            </div>
                            <div className="h-2 w-full bg-secondary/30 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${percentage}%` }}
                                className={`h-full ${colorClass}`}
                              />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Recent Activity (Expanded) */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="lg:col-span-2"
              >
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow bg-card text-card-foreground h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-foreground">Recent Activity</CardTitle>
                        <CardDescription className="text-muted-foreground">Latest updates across your company</CardDescription>
                      </div>
                      <Button variant="outline" size="sm" className="border-border text-foreground hover:bg-muted">
                        View All
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {activities.length === 0 ? (
                        <div className="text-center text-muted-foreground py-4">No recent activity</div>
                      ) : (
                        activities.map((activity) => (
                          <div
                            key={activity.id}
                            className="flex items-start space-x-4 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                          >
                            <div
                              className={`p-2 rounded-lg ${activity.type === 'mapping'
                                ? 'bg-primary/10'
                                : activity.type === 'user'
                                  ? 'bg-secondary/10'
                                  : activity.type === 'export'
                                    ? 'bg-accent/10'
                                    : 'bg-muted'
                                }`}
                            >
                              {activity.type === 'mapping' && (
                                <TrendingUp className="h-4 w-4 text-primary" />
                              )}
                              {activity.type === 'user' && (
                                <Users className="h-4 w-4 text-secondary" />
                              )}
                              {activity.type === 'export' && (
                                <Download className="h-4 w-4 text-accent-foreground" />
                              )}
                              {activity.type === 'sync' && (
                                <RefreshCw className="h-4 w-4 text-muted-foreground" />
                              )}
                              {activity.type === 'info' && (
                                <FileText className="h-4 w-4 text-muted-foreground" />
                              )}
                              {activity.type === 'success' && (
                                <TrendingUp className="h-4 w-4 text-green-500" />
                              )}
                              {activity.type === 'warning' && (
                                <Bell className="h-4 w-4 text-amber-500" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground">
                                {activity.action}
                              </p>
                              <p className="text-sm text-muted-foreground">{activity.user}</p>
                            </div>
                            <span className="text-xs text-muted-foreground whitespace-nowrap">
                              {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                            </span>
                          </div>
                        )))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default CompanyDashboard;
