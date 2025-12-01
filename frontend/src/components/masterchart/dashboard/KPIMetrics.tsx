// frontend/src/components/masterchart/dashboard/KPIMetrics.tsx
import React from 'react';
import { MasterChartStats } from '@/types/masterchart';
import { Card, CardContent } from '@/components/ui/card';
import { BarChart3, Folder, FileText, AlertTriangle, FolderTree, Tags } from 'lucide-react';
import { motion } from 'framer-motion';

interface KPIMetricsProps {
    stats: MasterChartStats;
    isLoading: boolean;
    categoriesCount?: number;
    uniqueTagsCount?: number;
}

const KPICard = ({
    title,
    value,
    icon: Icon,
    index
}: {
    title: string;
    value: string | number;
    icon: React.ElementType;
    index: number;
}) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: index * 0.1 }}
    >
        <Card className="rounded-2xl shadow-lg shadow-black/10 dark:shadow-black/30 border-border/50 hover:-translate-y-1 transition-transform duration-200">
            <CardContent className="p-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5">
                        <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                        <p className="text-sm text-muted-foreground font-medium">{title}</p>
                        <p className="text-3xl font-bold mt-1">{value}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    </motion.div>
);

const KPIMetrics: React.FC<KPIMetricsProps> = ({
    stats,
    isLoading,
    categoriesCount = 0,
    uniqueTagsCount = 0
}) => {
    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-28 bg-muted rounded-2xl animate-pulse" />
                ))}
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="text-center text-muted-foreground py-8">
                Could not load statistics.
            </div>
        );
    }

    const kpis = [
        { title: 'Total Accounts', value: stats.total_accounts, icon: BarChart3 },
        { title: 'Header Accounts', value: stats.header_count, icon: Folder },
        { title: 'Detail Accounts', value: stats.detail_count, icon: FileText },
        { title: 'Orphan Accounts', value: stats.orphans, icon: AlertTriangle },
        { title: 'Categories', value: categoriesCount, icon: FolderTree },
        { title: 'Unique Tags', value: uniqueTagsCount, icon: Tags },
    ];

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {kpis.map((kpi, index) => (
                <KPICard key={kpi.title} {...kpi} index={index} />
            ))}
        </div>
    );
};

export default KPIMetrics;
