// frontend/src/pages/masterchart/MasterChartDashboard.tsx
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Link } from 'react-router-dom';
import { ArrowUpRight, Plus } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    useTemplateCatalogTree,
    useTemplateCatalogStats,
    useTemplateCatalogAccounts,
} from '@/hooks/api/useTemplateCatalog';
import { ViewMode, FilterState, MasterAccount, MasterAccountNode } from '@/types/masterchart';
import type { CompanyAccount } from '@/types/company_account';
import { useCompany } from '@/contexts/CompanyContext';
import { useToast } from '@/hooks/use-toast';
import { api, ApiError } from '@/lib/api';

// Import components
import KPIMetrics from '@/components/masterchart/dashboard/KPIMetrics';
import AnalyticsCharts from '@/components/masterchart/dashboard/AnalyticsCharts';
import ViewSelector from '@/components/masterchart/dashboard/ViewSelector';
import FilterBar from '@/components/masterchart/dashboard/FilterBar';
import TreeView from '@/components/masterchart/dashboard/views/TreeView';
import ListView from '@/components/masterchart/dashboard/views/ListView';
import CardsView from '@/components/masterchart/dashboard/views/CardsView';
import AccountDetailsPanel from '@/components/masterchart/dashboard/AccountDetailsPanel';

const buildCatalogTree = (accounts: MasterAccount[]): MasterAccountNode[] => {
    const nodes = new Map<string, MasterAccountNode>();
    const codeToHeaderId = new Map<string, string>();
    const codeToFirstId = new Map<string, string>();

    accounts.forEach((account) => {
        const node: MasterAccountNode = { ...account, children: [] };
        nodes.set(account.id, node);
        if (!codeToFirstId.has(account.code)) {
            codeToFirstId.set(account.code, account.id);
        }
        if (account.type === 'H') {
            codeToHeaderId.set(account.code, account.id);
        }
    });

    const roots: MasterAccountNode[] = [];
    nodes.forEach((node) => {
        const parentCode = node.parent_code;
        const parentId = parentCode
            ? codeToHeaderId.get(parentCode) || codeToFirstId.get(parentCode)
            : undefined;
        if (parentId && nodes.has(parentId) && parentId !== node.id) {
            nodes.get(parentId)!.children.push(node);
        } else {
            roots.push(node);
        }
    });

    const sortNodes = (node: MasterAccountNode) => {
        node.children.sort((a, b) => a.code.localeCompare(b.code));
        node.children.forEach(sortNodes);
    };

    roots.sort((a, b) => a.code.localeCompare(b.code));
    roots.forEach(sortNodes);

    return roots;
};

const MasterChartDashboard = () => {
    const queryClient = useQueryClient();
    const { toast } = useToast();
    const { selectedCompanyId, selectedCompany } = useCompany();
    const { data: tree, isLoading: isLoadingTree, error: treeError } = useTemplateCatalogTree();
    const { data: stats, isLoading: isLoadingStats } = useTemplateCatalogStats();
    const {
        data: catalogAccounts = [],
        isLoading: isLoadingCatalogAccounts,
        error: catalogAccountsError,
    } = useTemplateCatalogAccounts();

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

    const { data: companyAccounts = [] } = useQuery({
        queryKey: ['company-chart', selectedCompanyId],
        queryFn: async () => {
            if (!selectedCompanyId) return [] as CompanyAccount[];
            return api.get<CompanyAccount[]>(`/companies/${selectedCompanyId}/chart`);
        },
        enabled: !!selectedCompanyId,
    });

    const existingCodes = useMemo(
        () => new Set(companyAccounts.map((account) => account.code)),
        [companyAccounts]
    );

    const addMutation = useMutation({
        mutationFn: async (account: MasterAccount) => {
            if (!selectedCompanyId) {
                throw new Error('Select a company before adding accounts.');
            }
            return api.post(`/companies/${selectedCompanyId}/chart/add-from-catalog`, {
                catalog_account_id: account.id,
            });
        },
        onSuccess: () => {
            toast({
                title: 'Account added',
                description: 'The account was added to your company chart.',
            });
            queryClient.invalidateQueries({ queryKey: ['company-chart', selectedCompanyId] });
        },
        onError: (error) => {
            const message = error instanceof ApiError
                ? error.getUserMessage()
                : error instanceof Error
                    ? error.message
                    : 'Failed to add account.';
            toast({
                title: 'Add account failed',
                description: message,
                variant: 'destructive',
            });
        },
    });

    // Flatten tree for list/cards view
    const effectiveTree = useMemo(() => {
        if (tree && tree.length > 0) {
            return tree;
        }
        if (catalogAccounts.length > 0) {
            return buildCatalogTree(catalogAccounts);
        }
        return [];
    }, [tree, catalogAccounts]);

    const flatAccounts = useMemo(() => {
        if (effectiveTree.length === 0 && catalogAccounts.length > 0) {
            return catalogAccounts;
        }
        if (effectiveTree.length === 0) return [];
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
        return flatten(effectiveTree);
    }, [effectiveTree, catalogAccounts]);

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

            // Normal balance filter
            if (filters.normalBalance !== 'all' && account.normal_balance !== filters.normalBalance) {
                return false;
            }

            return true;
        });
    }, [flatAccounts, filters]);

    // Get unique categories
    const categories = useMemo(() => {
        return Array.from(
            new Set(flatAccounts.map((acc) => acc.category).filter((category) => category))
        );
    }, [flatAccounts]);

    // Calculate additional stats
    const categoriesCount = categories.length;
    const uniqueTagsCount = new Set(
        flatAccounts.flatMap((account) => account.tags || [])
    ).size;

    const selectedIsAdded = selectedAccount ? existingCodes.has(selectedAccount.code) : false;
    const isLoadingCatalog = isLoadingTree || isLoadingCatalogAccounts;
    const catalogError = treeError || catalogAccountsError;
    const catalogErrorMessage = catalogError instanceof ApiError
        ? catalogError.getUserMessage()
        : 'Failed to load the template account catalog.';

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
                        <h1 className="text-3xl font-semibold">Template Account Catalog</h1>
                        <p className="text-lg text-muted-foreground mt-1">
                            Browse the optional account catalog and add entries to your company chart.
                        </p>
                        {selectedCompany && (
                            <p className="text-sm text-muted-foreground mt-2">
                                Adding to: <span className="font-medium">{selectedCompany.name}</span>
                            </p>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Button asChild variant="outline">
                            <Link to="/chartofaccounts">
                                <ArrowUpRight className="h-4 w-4 mr-2" />
                                View My Chart
                            </Link>
                        </Button>
                    </div>
                </div>
            </motion.div>

            {!selectedCompanyId && (
                <Alert className="bg-muted/40 border-border">
                    <AlertDescription>
                        Select a company to add catalog accounts to a chart of accounts.
                    </AlertDescription>
                </Alert>
            )}
            {catalogError && (
                <Alert variant="destructive">
                    <AlertDescription>{catalogErrorMessage}</AlertDescription>
                </Alert>
            )}

            {/* KPI Metrics */}
            <KPIMetrics
                stats={stats!}
                isLoading={isLoadingStats}
                categoriesCount={categoriesCount}
                uniqueTagsCount={uniqueTagsCount}
            />

            {/* Analytics & Insights */}
            {!isLoadingCatalog && effectiveTree.length > 0 && stats && (
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
                <Button
                    variant="outline"
                    size="sm"
                    disabled={!selectedCompanyId || !selectedAccount || selectedIsAdded || addMutation.isPending}
                    onClick={() => selectedAccount && addMutation.mutate(selectedAccount)}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    {selectedIsAdded ? 'Already in Chart' : 'Add Selected'}
                </Button>
            </div>

            {/* Views */}
            {isLoadingCatalog ? (
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
                    {activeView === 'tree' && effectiveTree.length > 0 && (
                        <TreeView tree={effectiveTree} onSelectAccount={setSelectedAccount} />
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
                onAddAccount={(account) => addMutation.mutate(account)}
                isAdded={selectedIsAdded}
                isAdding={addMutation.isPending}
                companyName={selectedCompany?.name || null}
            />
        </div>
    );
};

export default MasterChartDashboard;
