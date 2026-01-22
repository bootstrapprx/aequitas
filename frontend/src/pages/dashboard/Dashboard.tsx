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
    total_cash_delta?: number | null;
    net_revenue_delta?: number | null;
    operating_income_delta?: number | null;
    net_working_capital_delta?: number | null;
    current_ratio_delta?: number | null;
}

interface KernelLayerStatus {
    layer: 'L0' | 'L1' | 'L2';
    state: 'implemented' | 'placeholder';
}

interface KernelLayerBindings {
    company_id: string;
    kernel_version: string | null;
    kernel_layer: 'L0' | 'L1' | 'L2' | null;
    layers: KernelLayerStatus[];
}

const Dashboard = () => {
    const { selectedCompanyId } = useCompany();
    const { data: dashboardContext, isLoading: isContextLoading } = useDashboardContext();

    // Fetch Core Metrics from backend
    const { data: metrics, isLoading: isMetricsLoading, error } = useQuery({
        queryKey: ['company', 'core-metrics', selectedCompanyId],
        queryFn: async () => {
            return await api.get<CoreMetrics>('/accounting/core-metrics', {
                params: { company_id: selectedCompanyId },
            });
        },
        enabled: !!selectedCompanyId,
    });

    const { data: kernelLayers, isLoading: isKernelLayersLoading } = useQuery({
        queryKey: ['company', 'kernel-layer-bindings', selectedCompanyId],
        queryFn: async () => {
            return await api.get<KernelLayerBindings>('/accounting/kernel-layers', {
                params: { company_id: selectedCompanyId },
            });
        },
        enabled: !!selectedCompanyId,
    });

    const isLoading = isContextLoading || isMetricsLoading;
    const accountingActive = dashboardContext?.accounting_active || false;
    const kernelVersion = kernelLayers?.kernel_version ?? dashboardContext?.kernel_version ?? null;
    const kernelLayer = kernelLayers?.kernel_layer ?? dashboardContext?.kernel_layer ?? null;

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

    // Format delta values (neutral, explicit sign)
    const formatDelta = (value: number | null | undefined, isCurrency: boolean = true): string | undefined => {
        if (value === null || value === undefined) return undefined;
        const sign = value >= 0 ? '+' : '';
        if (isCurrency) {
            return `${sign}${formatCurrency(value)}`;
        }
        return `${sign}${value.toFixed(2)}`;
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
                {/* Constitutional Warning */}
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
                            <strong>Accounting system not active.</strong> Core Metrics are unavailable until activation.
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
                    ) : error ? (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                                Core Metrics unavailable for the selected company and period.
                            </AlertDescription>
                        </Alert>
                    ) : metrics ? (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                        >
                            {/* Total Cash */}
                            <StatsCard
                                title="Total Cash"
                                value={formatCurrency(metrics.total_cash)}
                                delta={formatDelta(metrics.total_cash_delta)}
                                subtitle="Accounts: 10000, 10100"
                                icon={Wallet}
                                color="teal"
                            />

                            {/* Net Revenue */}
                            <StatsCard
                                title="Net Revenue"
                                value={formatCurrency(metrics.net_revenue)}
                                delta={formatDelta(metrics.net_revenue_delta)}
                                subtitle="Accounts: 40000, 49000"
                                icon={DollarSign}
                                color="navy"
                            />

                            {/* Operating Income */}
                            <StatsCard
                                title="Operating Income"
                                value={formatCurrency(metrics.operating_income)}
                                delta={formatDelta(metrics.operating_income_delta)}
                                subtitle="Accounts: 40000, 49000, 50000, 60000, 61000, 62000"
                                icon={Activity}
                                color="yellow"
                            />

                            {/* Net Working Capital */}
                            <StatsCard
                                title="Net Working Capital"
                                value={formatCurrency(metrics.net_working_capital)}
                                delta={formatDelta(metrics.net_working_capital_delta)}
                                subtitle="Accounts: 10000, 10100, 12000, 14000, 20000, 21000, 22000, 23000"
                                icon={TrendingUp}
                                color="navy"
                            />

                            {/* Current Ratio */}
                            <StatsCard
                                title="Current Ratio"
                                value={formatRatio(metrics.current_ratio)}
                                delta={formatDelta(metrics.current_ratio_delta, false)}
                                subtitle="Current Assets / Current Liabilities"
                                icon={Scale}
                                color="navy"
                            />
                        </motion.div>
                    ) : (
                        <Alert className="border-muted bg-background">
                            <Info className="h-4 w-4" />
                            <AlertDescription className="text-sm text-muted-foreground">
                                Core Metrics are not available without a selected company.
                            </AlertDescription>
                        </Alert>
                    )}
                </div>

                {/* Kernel Binding */}
                <Card className="border-border bg-muted/30">
                    <CardHeader>
                        <CardTitle className="text-lg font-heading">Kernel Binding</CardTitle>
                        <CardDescription>
                            Company kernel metadata
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                            <div>
                                <p className="text-muted-foreground">Kernel Version</p>
                                <p className="text-foreground font-semibold">{kernelVersion ?? 'N/A'}</p>
                            </div>
                            <div>
                                <p className="text-muted-foreground">Kernel Layer</p>
                                <p className="text-foreground font-semibold">{kernelLayer ?? 'N/A'}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Kernel Layer Placeholders */}
                <Card className="border-border bg-muted/30">
                    <CardHeader>
                        <CardTitle className="text-lg font-heading">Kernel Layers</CardTitle>
                        <CardDescription>
                            L0 implemented, L1/L2 placeholders
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isKernelLayersLoading ? (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {[...Array(3)].map((_, i) => (
                                    <Skeleton key={i} className="h-16" />
                                ))}
                            </div>
                        ) : kernelLayers ? (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                {kernelLayers.layers.map((layer) => (
                                    <div key={layer.layer} className="rounded border border-border p-3">
                                        <p className="text-muted-foreground">Layer {layer.layer}</p>
                                        <p className="text-foreground font-semibold">{layer.state}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">Kernel layer status unavailable.</p>
                        )}
                    </CardContent>
                </Card>

                {/* Metric Definitions */}
                <Card className="border-border bg-muted/30">
                    <CardHeader>
                        <CardTitle className="text-lg font-heading">Metric Definitions</CardTitle>
                        <CardDescription>
                            Accounts and formulas (Kernel L0 only)
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Wallet className="h-4 w-4 text-teal-600" />
                                    Total Cash
                                </h3>
                                <p className="text-sm text-muted-foreground">Accounts: 10000, 10100</p>
                                <p className="text-sm text-muted-foreground">Formula: 10000 + 10100</p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <DollarSign className="h-4 w-4 text-navy-600" />
                                    Net Revenue
                                </h3>
                                <p className="text-sm text-muted-foreground">Accounts: 40000, 49000</p>
                                <p className="text-sm text-muted-foreground">Formula: 40000 − 49000</p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Activity className="h-4 w-4 text-yellow-600" />
                                    Operating Income
                                </h3>
                                <p className="text-sm text-muted-foreground">Accounts: 40000, 49000, 50000, 60000, 61000, 62000</p>
                                <p className="text-sm text-muted-foreground">Formula: Net Revenue − 50000 − 60000 − 61000 − 62000</p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-teal-600" />
                                    Net Working Capital
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Current Assets: 10000, 10100, 12000, 14000
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    Current Liabilities: 20000, 21000, 22000, 23000
                                </p>
                                <p className="text-sm text-muted-foreground">Formula: Assets − Liabilities</p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Scale className="h-4 w-4 text-navy-600" />
                                    Current Ratio
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    Formula: Current Assets / Current Liabilities
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    Rule: If liabilities = 0 → N/A
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
            </main>
        </div>
    );
};

export default Dashboard;
