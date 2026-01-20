import React from 'react';
import { motion } from 'framer-motion';
import {
    DollarSign,
    TrendingUp,
    Activity,
    Wallet,
    Scale,
    Info,
    AlertCircle,
} from 'lucide-react';
import { useCompany } from '@/contexts/CompanyContext';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useDashboardContext } from '@/hooks/useDashboardContext';

/**
 * Dashboard - Kernel Dashboard Intelligence
 * 
 * CONSTITUTIONAL COMPLIANCE:
 * - Implements Core Metrics as defined in CANON_KERNEL_DASHBOARD_INTELLIGENCE §4
 * - All metrics are derived from Kernel L0 accounts only
 * - No projections, no assumptions, no recommendations
 * - The dashboard is an observer, never an actor
 * - Follows Interpretation Boundary Rule (§8)
 * - Adheres to Minimal Vector Doctrine (§9)
 */

interface CoreMetrics {
    total_cash: number;
    net_revenue: number;
    operating_income: number;
    net_working_capital: number;
    current_ratio: number | null;
}

const Dashboard = () => {
    const { selectedCompanyId } = useCompany();
    const { data: dashboardContext, isLoading: isContextLoading } = useDashboardContext();

    // Fetch Core Metrics from backend (when endpoint is available)
    const { data: metrics, isLoading: isMetricsLoading, error } = useQuery({
        queryKey: ['company', 'core-metrics', selectedCompanyId],
        queryFn: async () => {
            // TODO: Replace with actual endpoint when backend implements Core Metrics
            // For now, return placeholder data
            return {
                total_cash: 0,
                net_revenue: 0,
                operating_income: 0,
                net_working_capital: 0,
                current_ratio: null,
            } as CoreMetrics;
        },
        enabled: !!selectedCompanyId,
    });

    const isLoading = isContextLoading || isMetricsLoading;
    const accountingActive = dashboardContext?.accounting_active || false;

    // Format currency values
    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    // Format ratio values
    const formatRatio = (value: number | null): string => {
        if (value === null) return 'N/A';
        return value.toFixed(2);
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Page Header */}
            <header className="bg-card border-b sticky top-0 z-40">
                <div className="px-8 py-6">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground font-heading">Dashboard</h1>
                        <p className="text-muted-foreground mt-1">
                            Kernel Dashboard Intelligence — Core Metrics
                        </p>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="p-8 space-y-8">
                {/* Constitutional Notice */}
                <Alert className="border-gold/20 bg-gold/5">
                    <Info className="h-4 w-4 text-gold" />
                    <AlertDescription className="text-foreground">
                        <strong>Interpretation Boundary:</strong> This dashboard explains financial reality derived from Kernel L0 accounts.
                        It does not decide reality, make recommendations, or replace professional judgment.
                    </AlertDescription>
                </Alert>

                {/* Accounting Status Check */}
                {!accountingActive && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                            <strong>Accounting system not active.</strong> Core Metrics require an active accounting system.
                            Please complete onboarding to view financial data.
                        </AlertDescription>
                    </Alert>
                )}

                {/* Core Metrics Section */}
                <div>
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-foreground font-heading">Core Metrics</h2>
                        <p className="text-sm text-muted-foreground mt-1">
                            Survival and immediacy — answers the question: "Can this company continue operating right now?"
                        </p>
                    </div>

                    {isLoading ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {[...Array(5)].map((_, i) => (
                                <Skeleton key={i} className="h-32" />
                            ))}
                        </div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                        >
                            {/* Total Cash */}
                            <StatsCard
                                title="Total Cash"
                                value={formatCurrency(metrics?.total_cash || 0)}
                                subtitle="Available liquidity"
                                icon={Wallet}
                                color="teal"
                            />

                            {/* Net Revenue */}
                            <StatsCard
                                title="Net Revenue"
                                value={formatCurrency(metrics?.net_revenue || 0)}
                                subtitle="Revenue recognition"
                                icon={DollarSign}
                                color="navy"
                            />

                            {/* Operating Income */}
                            <StatsCard
                                title="Operating Income"
                                value={formatCurrency(metrics?.operating_income || 0)}
                                subtitle="Operational result"
                                icon={Activity}
                                color="yellow"
                            />

                            {/* Net Working Capital */}
                            <StatsCard
                                title="Net Working Capital"
                                value={formatCurrency(metrics?.net_working_capital || 0)}
                                subtitle="Short-term financial health"
                                icon={TrendingUp}
                                color={metrics && metrics.net_working_capital < 0 ? "red" : "green"}
                            />

                            {/* Current Ratio */}
                            <StatsCard
                                title="Current Ratio"
                                value={formatRatio(metrics?.current_ratio || null)}
                                subtitle="Kernel approximation"
                                icon={Scale}
                                color="navy"
                            />
                        </motion.div>
                    )}
                </div>

                {/* Metric Explanations */}
                <Card className="border-border bg-muted/30">
                    <CardHeader>
                        <CardTitle className="text-lg font-heading">About Core Metrics</CardTitle>
                        <CardDescription>
                            Understanding the fundamentals
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Wallet className="h-4 w-4 text-teal-600" />
                                    Total Cash
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    All cash and cash equivalents available to the company. This is the most fundamental survival metric.
                                </p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <DollarSign className="h-4 w-4 text-navy-600" />
                                    Net Revenue
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Revenue after direct reductions. Shows the company's earning capacity.
                                </p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Activity className="h-4 w-4 text-yellow-600" />
                                    Operating Income
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Profit from core business operations. Indicates operational efficiency before financing and taxes.
                                </p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-green-600" />
                                    Net Working Capital
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Current assets minus current liabilities. A negative value indicates potential liquidity stress.
                                </p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Scale className="h-4 w-4 text-navy-600" />
                                    Current Ratio
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Current assets divided by current liabilities. Values above 1.0 generally indicate good short-term health.
                                </p>
                            </div>
                        </div>

                        <Alert className="border-muted bg-background">
                            <Info className="h-4 w-4" />
                            <AlertDescription className="text-sm text-muted-foreground">
                                <strong>Constitutional Note:</strong> All metrics shown are absolute values or simple ratios directly traceable to Kernel L0 accounts.
                                No projections, assumptions, or accrual interpretations are included. These metrics never contradict each other and require no accounting knowledge to understand.
                            </AlertDescription>
                        </Alert>
                    </CardContent>
                </Card>

                {/* Future Metrics Notice */}
                {accountingActive && (
                    <Card className="border-dashed border-muted">
                        <CardContent className="p-6">
                            <div className="flex items-start gap-4">
                                <Info className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                                <div className="space-y-2">
                                    <p className="text-sm font-medium text-foreground">
                                        Advanced Metrics and Diagnostic Metrics
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Additional metric classes (Advanced Metrics for operational efficiency and Diagnostic Metrics for accounting truth verification)
                                        will be available in future updates once backend endpoints are implemented.
                                    </p>
                                    <p className="text-xs text-muted-foreground italic">
                                        Per CANON §4.94: "If Core Metrics indicate distress, no other class may be shown by default."
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
