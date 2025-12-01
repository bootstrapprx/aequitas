// frontend/src/pages/masterchart/MasterChartDashboard.tsx
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { Network, FileInput, FileOutput, Plus } from 'lucide-react';
import { useManualMode } from '@/contexts/ManualModeContext';
import { useMasterChartTree, useMasterChartStats } from '@/hooks/api/useMasterChart';
import { ViewMode, FilterState, MasterAccount } from '@/types/masterchart';

// Import components
import KPIMetrics from '@/components/masterchart/dashboard/KPIMetrics';
import AnalyticsCharts from '@/components/masterchart/dashboard/AnalyticsCharts';
import ViewSelector from '@/components/masterchart/dashboard/ViewSelector';
import FilterBar from '@/components/masterchart/dashboard/FilterBar';
import TreeView from '@/components/masterchart/dashboard/views/TreeView';
import ListView from '@/components/masterchart/dashboard/views/ListView';
import CardsView from '@/components/masterchart/dashboard/views/CardsView';
import AccountDetailsPanel from '@/components/masterchart/dashboard/AccountDetailsPanel';

const MasterChartDashboard = () => {
    const { isManualMode } = useManualMode();
    const { data: tree, isLoading: isLoadingTree } = useMasterChartTree();
    const { data: stats, isLoading: isLoadingStats } = useMasterChartStats();

    // State
    const [activeView, setActiveView] = useState<ViewMode>('tree');
    const [selectedAccount, setSelectedAccount] = useState<MasterAccount | null>(null);
    const [filters, setFilters] = useState<FilterState>({
        search: '',
        category: 'all',
        type: 'all',
        normalBalance: 'all',
        tags: [],
    });

    // Flatten tree for list/cards view
    const flatAccounts = useMemo(() => {
        if (!tree) return [];
        const flatten = (nodes: any[]): MasterAccount[] => {
            return nodes.reduce((acc, node) => {
                const { children, ...account } = node;
                acc.push(account);
                if (children && children.length > 0) {
                    acc.push(...flatten(children));
                }
                return acc;
            }, [] as MasterAccount[]);
        };
        return flatten(tree);
    }, [tree]);

    // Apply filters
    const filteredAccounts = useMemo(() => {
        return flatAccounts.filter((account) => {
            // Search filter
            if (filters.search) {
                const searchLower = filters.search.toLowerCase();
                const matchesSearch =
                    account.code.toLowerCase().includes(searchLower) ||
                    account.description.toLowerCase().includes(searchLower);
                if (!matchesSearch) return false;
            }

            // Category filter
            if (filters.category !== 'all' && account.category !== filters.category) {
                return false;
            }

            // Type filter
            if (filters.type !== 'all' && account.type !== filters.type) {
                return false;
            }

            return true;
        });
    }, [flatAccounts, filters]);

    // Get unique categories
    const categories = useMemo(() => {
        return Array.from(new Set(flatAccounts.map((acc) => acc.category)));
    }, [flatAccounts]);

    // Calculate additional stats
    const categoriesCount = categories.length;
    const uniqueTagsCount = 0; // TODO: Calculate from extended data when available

    return (
        <div className="space-y-8 p-8 md:p-10">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-semibold">Master Chart Dashboard</h1>
                        <p className="text-lg text-muted-foreground mt-1">
                            Complete overview and management of your chart of accounts
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button asChild>
                            <Link to="/masterchart/interactive">
                                <Network className="h-4 w-4 mr-2" />
                                Interactive Editor
                            </Link>
                        </Button>
                        <Button asChild variant="outline">
                            <Link to="/masterchart/tree">
                                <Network className="h-4 w-4 mr-2" />
                                View Tree
                            </Link>
                        </Button>
                        {!isManualMode && (
                            <>
                                <Button asChild variant="outline">
                                    <Link to="/masterchart/import">
                                        <FileInput className="h-4 w-4 mr-2" />
                                        Import
                                    </Link>
                                </Button>
                                <Button asChild variant="outline">
                                    <Link to="/masterchart/export">
                                        <FileOutput className="h-4 w-4 mr-2" />
                                        Export
                                    </Link>
                                </Button>
                            </>
                        )}
                    </div>
                </div>
            </motion.div>

            {/* KPI Metrics */}
            <KPIMetrics
                stats={stats!}
                isLoading={isLoadingStats}
                categoriesCount={categoriesCount}
                uniqueTagsCount={uniqueTagsCount}
            />

            {/* Analytics & Insights */}
            {!isLoadingTree && tree && stats && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                >
                    <h2 className="text-xl font-semibold mb-4">Analytics & Insights</h2>
                    <AnalyticsCharts accounts={flatAccounts} stats={stats} />
                </motion.div>
            )}

            {/* Filter Bar */}
            <FilterBar
                filters={filters}
                onFiltersChange={setFilters}
                categories={categories}
            />

            {/* View Selector */}
            <div className="flex items-center justify-between">
                <ViewSelector activeView={activeView} onViewChange={setActiveView} />
                <Button variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Account
                </Button>
            </div>

            {/* Views */}
            {isLoadingTree ? (
                <div className="h-96 flex items-center justify-center">
                    <div className="text-muted-foreground">Loading accounts...</div>
                </div>
            ) : (
                <motion.div
                    key={activeView}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3 }}
                >
                    {activeView === 'tree' && tree && (
                        <TreeView tree={tree} onSelectAccount={setSelectedAccount} />
                    )}
                    {activeView === 'list' && (
                        <ListView accounts={filteredAccounts} onSelectAccount={setSelectedAccount} />
                    )}
                    {activeView === 'cards' && (
                        <CardsView accounts={filteredAccounts} onSelectAccount={setSelectedAccount} />
                    )}
                </motion.div>
            )}

            {/* Account Details Panel */}
            <AccountDetailsPanel
                account={selectedAccount}
                isOpen={!!selectedAccount}
                onClose={() => setSelectedAccount(null)}
            />
        </div>
    );
};

export default MasterChartDashboard;
