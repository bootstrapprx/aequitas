import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FileText,
    Calendar,
    Scale,
    ListChecks,
    FileDown,
    MapPin,
    RefreshCw,
    TrendingUp,
    DollarSign,
    BarChart3,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface UtilityAction {
    id: string;
    title: string;
    description: string;
    icon: React.ElementType;
    route: string;
    color: string;
    badge?: string;
    badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

interface UtilitiesPanelProps {
    accountingActive: boolean;
    unmappedCount?: number;
    openPeriods?: number;
    className?: string;
}

export const UtilitiesPanel: React.FC<UtilitiesPanelProps> = ({
    accountingActive,
    unmappedCount = 0,
    openPeriods = 0,
    className,
}) => {
    const navigate = useNavigate();

    const utilities: UtilityAction[] = [
        {
            id: 'journal-entry',
            title: 'Journal Entry',
            description: 'Record a transaction',
            icon: FileText,
            route: '/accountancy/journal',
            color: 'text-blue-600',
        },
        {
            id: 'fiscal-periods',
            title: 'Fiscal Periods',
            description: 'Manage accounting periods',
            icon: Calendar,
            route: '/accountancy/fiscal-periods',
            color: 'text-purple-600',
            badge: openPeriods > 0 ? `${openPeriods} open` : undefined,
            badgeVariant: 'secondary',
        },
        {
            id: 'trial-balance',
            title: 'Trial Balance',
            description: 'Quick balance check',
            icon: Scale,
            route: '/accountancy/trial-balance',
            color: 'text-green-600',
        },
        {
            id: 'chart-of-accounts',
            title: 'Chart of Accounts',
            description: 'Review account structure',
            icon: ListChecks,
            route: '/chartofaccounts',
            color: 'text-teal-600',
        },
        {
            id: 'financial-statements',
            title: 'Financial Statements',
            description: 'Export reports',
            icon: FileDown,
            route: '/reports/statements',
            color: 'text-orange-600',
        },
        {
            id: 'map-accounts',
            title: 'Map Accounts',
            description: 'Map to master chart',
            icon: MapPin,
            route: '/chartofaccounts/mapping',
            color: 'text-pink-600',
            badge: unmappedCount > 0 ? `${unmappedCount} unmapped` : undefined,
            badgeVariant: unmappedCount > 0 ? 'destructive' : undefined,
        },
    ];

    // Filter utilities based on accounting status
    const visibleUtilities = accountingActive
        ? utilities
        : utilities.filter(u => ['chart-of-accounts', 'map-accounts', 'fiscal-periods'].includes(u.id));

    return (
        <Card className={cn('border-0 shadow-md', className)}>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Quick Actions
                </CardTitle>
                <CardDescription>Common accounting workflows</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {visibleUtilities.map((utility) => {
                        const Icon = utility.icon;
                        return (
                            <Button
                                key={utility.id}
                                variant="outline"
                                className="h-auto p-4 flex flex-col items-start gap-2 hover:bg-muted/50 hover:border-primary transition-all"
                                onClick={() => navigate(utility.route)}
                            >
                                <div className="flex items-center justify-between w-full">
                                    <Icon className={cn('h-5 w-5', utility.color)} />
                                    {utility.badge && (
                                        <Badge variant={utility.badgeVariant} className="text-xs">
                                            {utility.badge}
                                        </Badge>
                                    )}
                                </div>
                                <div className="text-left w-full">
                                    <div className="font-semibold text-sm text-foreground">
                                        {utility.title}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        {utility.description}
                                    </div>
                                </div>
                            </Button>
                        );
                    })}
                </div>

                {!accountingActive && (
                    <div className="mt-4 p-4 bg-muted/30 rounded-lg border border-dashed">
                        <p className="text-sm text-muted-foreground text-center">
                            Complete onboarding to unlock all utilities
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
