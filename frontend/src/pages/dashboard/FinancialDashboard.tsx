import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Building2,
    TrendingUp,
    TrendingDown,
    DollarSign,
    Activity,
    AlertCircle,
    CheckCircle2,
    Clock,
    FileText,
    Users,
    ChevronRight,
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip as RechartsTooltip,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    AreaChart,
    Area,
} from 'recharts';
import { useAuth } from '@/contexts/AuthContext';
import { useCompany } from '@/contexts/CompanyContext';
import { useDashboardContext } from '@/hooks/useDashboardContext';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { UtilitiesPanel } from '@/components/dashboard/UtilitiesPanel';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

const CHART_COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
    'hsl(var(--chart-5))',
];

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
    timestamp: string;
    type: string;
}

interface CompanyDashboardStats {
    chart_status: CompanyChartStatus;
    active_users_count: number;
    pending_reviews_count: number;
    recent_activity: DashboardActivity[];
    account_distribution: Record<string, number>;
}

const FinancialDashboard = () => {
    const { user } = useAuth();
    const { selectedCompanyId, selectedCompany, isLoadingCompanies } = useCompany();
    const navigate = useNavigate();

    // Get authoritative dashboard context
    const { data: dashboardContext, isLoading: isContextLoading } = useDashboardContext();

    // Fetch Dashboard Stats
    const { data: stats, isLoading: isStatsLoading } = useQuery({
        queryKey: ['company', 'dashboard-stats', selectedCompanyId],
        queryFn: () => api.get<CompanyDashboardStats>(`/companies/${selectedCompanyId}/dashboard-stats`),
        enabled: !!selectedCompanyId,
    });

    const isLoading = isLoadingCompanies || isContextLoading || (!!selectedCompanyId && isStatsLoading);

    // Extract data from dashboard context
    const accountingActive = dashboardContext?.accounting_active || false;
    const protectedStructure = dashboardContext?.protected_structure || false;
    const totalAccounts = dashboardContext?.total_accounts || 0;
    const openPeriods = dashboardContext?.open_periods || 0;

    // Extract data from stats
    const chartStatus = stats?.chart_status;
    const mappedPercentage = chartStatus?.mapping_coverage || 0;
    const activeUsers = stats?.active_users_count || 0;
    const pendingReviews = stats?.pending_reviews_count || 0;
    const activities = stats?.recent_activity || [];
    const distribution = stats?.account_distribution || {};

    // Calculate derived metrics
    const mappedCount = chartStatus?.company_chart_initialized
        ? Math.round((totalAccounts * mappedPercentage) / 100)
        : 0;
    const unmappedCount = Math.max(totalAccounts - mappedCount, 0);

    const distributionSeries = useMemo(() => {
        return Object.entries(distribution)
            .map(([name, value]) => ({ name, value }))
            .filter((entry) => entry.value > 0);
    }, [distribution]);

    // Mock financial data (TODO: Replace with real data from API)
    const mockFinancialMetrics = {
        revenue: 0,
        expenses: 0,
        netIncome: 0,
        cashFlow: 0,
    };

    // Mock trend data for charts
    const mockTrendData = [
        { month: 'Jan', revenue: 0, expenses: 0 },
        { month: 'Feb', revenue: 0, expenses: 0 },
        { month: 'Mar', revenue: 0, expenses: 0 },
        { month: 'Apr', revenue: 0, expenses: 0 },
        { month: 'May', revenue: 0, expenses: 0 },
        { month: 'Jun', revenue: 0, expenses: 0 },
    ];

    return (
        <div className="min-h-screen bg-background">
            {/* Header Section */}
            <div className="bg-gradient-to-r from-primary to-secondary text-primary-foreground px-8 py-6 mb-6">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold mb-2">
                                    Financial Dashboard
                                </h1>
                                <p className="text-teal-50 flex items-center gap-2">
                                    <Building2 className="h-4 w-4" />
                                    {selectedCompany?.name || 'Select a company'}
                                    {selectedCompany?.ucid && (
                                        <span className="text-xs opacity-75">· {selectedCompany.ucid}</span>
                                    )}
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                {accountingActive && (
                                    <Badge variant="outline" className="bg-white/20 border-white/40 text-white">
                                        <CheckCircle2 className="h-3 w-3 mr-1" />
                                        Accounting Active
                                    </Badge>
                                )}
                                {protectedStructure && (
                                    <Badge variant="outline" className="bg-white/20 border-white/40 text-white">
                                        Protected Structure
                                    </Badge>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-8 pb-8 space-y-6">

                {/* Alert if not activated */}
                {!accountingActive && selectedCompanyId && (
                    <Alert className="border-amber-200 bg-amber-50">
                        <AlertCircle className="h-4 w-4 text-amber-600" />
                        <AlertTitle className="text-amber-900">Onboarding Required</AlertTitle>
                        <AlertDescription className="text-amber-700">
                            Complete the onboarding wizard to activate accounting features and unlock the full dashboard.
                            <Button
                                variant="link"
                                className="h-auto p-0 ml-2 text-amber-900 font-semibold"
                                onClick={() => navigate(`/onboarding/${selectedCompanyId}`)}
                            >
                                Continue Onboarding →
                            </Button>
                        </AlertDescription>
                    </Alert>
                )}

                {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                ) : (
                    <>
                        {/* Financial Metrics Row */}
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
                                title="Mapped Coverage"
                                value={`${mappedPercentage}%`}
                                subtitle={`${mappedCount} of ${totalAccounts} accounts`}
                                icon={TrendingUp}
                                color="navy"
                            />
                            <StatsCard
                                title="Open Periods"
                                value={openPeriods}
                                subtitle="Active fiscal periods"
                                icon={Clock}
                                color="yellow"
                            />
                            <StatsCard
                                title="Pending Reviews"
                                value={pendingReviews}
                                subtitle="Accounts to review"
                                icon={AlertCircle}
                                color={pendingReviews > 0 ? 'red' : 'green'}
                            />
                        </motion.div>

                        {/* Utilities Panel */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                        >
                            <UtilitiesPanel
                                accountingActive={accountingActive}
                                unmappedCount={unmappedCount}
                                openPeriods={openPeriods}
                            />
                        </motion.div>

                        {/* Charts and Activity Row */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                            {/* Account Distribution Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.3 }}
                            >
                                <Card className="border-0 shadow-md h-full">
                                    <CardHeader>
                                        <CardTitle>Account Distribution</CardTitle>
                                        <CardDescription>Breakdown by category</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {distributionSeries.length === 0 ? (
                                            <div className="h-64 flex items-center justify-center text-muted-foreground">
                                                No account data available yet
                                            </div>
                                        ) : (
                                            <div className="h-64">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <PieChart>
                                                        <Pie
                                                            data={distributionSeries}
                                                            dataKey="value"
                                                            nameKey="name"
                                                            cx="50%"
                                                            cy="50%"
                                                            innerRadius={60}
                                                            outerRadius={90}
                                                            paddingAngle={5}
                                                            label
                                                        >
                                                            {distributionSeries.map((entry, index) => (
                                                                <Cell
                                                                    key={entry.name}
                                                                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                                                                />
                                                            ))}
                                                        </Pie>
                                                        <RechartsTooltip
                                                            formatter={(value: number) => [`${value}`, 'Accounts']}
                                                            contentStyle={{
                                                                backgroundColor: 'hsl(var(--popover))',
                                                                borderColor: 'hsl(var(--border))',
                                                                color: 'hsl(var(--popover-foreground))',
                                                            }}
                                                        />
                                                    </PieChart>
                                                </ResponsiveContainer>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* Recent Activity */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.4 }}
                            >
                                <Card className="border-0 shadow-md h-full">
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <CardTitle>Recent Activity</CardTitle>
                                                <CardDescription>Latest updates</CardDescription>
                                            </div>
                                            <Button variant="ghost" size="sm">
                                                View All
                                                <ChevronRight className="h-4 w-4 ml-1" />
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {activities.length === 0 ? (
                                            <div className="h-64 flex items-center justify-center text-muted-foreground">
                                                No recent activity
                                            </div>
                                        ) : (
                                            <div className="space-y-4 max-h-64 overflow-y-auto">
                                                {activities.slice(0, 5).map((activity) => (
                                                    <div
                                                        key={activity.id}
                                                        className="flex items-start gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                                                    >
                                                        <div className="p-2 rounded-lg bg-primary/10">
                                                            <Activity className="h-4 w-4 text-primary" />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-sm font-medium text-foreground">
                                                                {activity.action}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground">{activity.user}</p>
                                                        </div>
                                                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                                                            {formatDistanceToNow(new Date(activity.timestamp), {
                                                                addSuffix: true,
                                                            })}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Financial Trend Chart (Placeholder for future) */}
                        {accountingActive && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.5 }}
                            >
                                <Card className="border-0 shadow-md">
                                    <CardHeader>
                                        <CardTitle>Financial Trends</CardTitle>
                                        <CardDescription>
                                            Revenue and expense overview (Coming soon)
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-64 flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                                            <div className="text-center">
                                                <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                                <p>Financial trend charts will appear here</p>
                                                <p className="text-xs mt-1">
                                                    After recording journal entries and closing periods
                                                </p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}

                        {/* Company Info Summary */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.6 }}
                        >
                            <Card className="border-0 shadow-md">
                                <CardHeader>
                                    <CardTitle>Company Context</CardTitle>
                                    <CardDescription>Current operational status</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div className="space-y-1">
                                            <p className="text-xs uppercase tracking-wide text-muted-foreground">
                                                Company
                                            </p>
                                            <p className="text-lg font-semibold text-foreground">
                                                {selectedCompany?.name || 'N/A'}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {selectedCompany?.ucid || 'UCID not assigned'}
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-xs uppercase tracking-wide text-muted-foreground">
                                                Kernel Binding
                                            </p>
                                            <p className="text-sm font-medium text-foreground">
                                                {dashboardContext?.kernel_version
                                                    ? `v${dashboardContext.kernel_version} · ${dashboardContext.kernel_layer}`
                                                    : 'Not bound'}
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-xs uppercase tracking-wide text-muted-foreground">
                                                Status
                                            </p>
                                            <p className="text-sm font-medium text-foreground">
                                                {accountingActive ? 'Active' : 'Setup in progress'}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </>
                )}
            </div>
        </div>
    );
};

export default FinancialDashboard;
