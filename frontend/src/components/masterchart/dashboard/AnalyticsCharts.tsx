// frontend/src/components/masterchart/dashboard/AnalyticsCharts.tsx
import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
    BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { MasterAccount, MasterChartStats } from '@/types/masterchart';
import { useTheme } from 'next-themes';

interface AnalyticsChartsProps {
    accounts: MasterAccount[];
    stats: MasterChartStats;
}

const COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
    'hsl(var(--chart-5))',
];

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ accounts, stats }) => {
    const { theme } = useTheme();
    const isDark = theme === 'dark';
    // Account Types Distribution
    const typeDistribution = useMemo(() => {
        const categoryCounts: Record<string, number> = {};
        accounts.forEach(acc => {
            categoryCounts[acc.category] = (categoryCounts[acc.category] || 0) + 1;
        });

        return Object.entries(categoryCounts).map(([name, value]) => ({
            name,
            value
        }));
    }, [accounts]);

    // Categories Breakdown
    const categoriesBreakdown = useMemo(() => {
        const breakdown: Record<string, { headers: number; details: number }> = {};
        accounts.forEach(acc => {
            if (!breakdown[acc.category]) {
                breakdown[acc.category] = { headers: 0, details: 0 };
            }
            if (acc.type === 'H') {
                breakdown[acc.category].headers++;
            } else {
                breakdown[acc.category].details++;
            }
        });

        return Object.entries(breakdown).map(([category, counts]) => ({
            category,
            headers: counts.headers,
            details: counts.details
        }));
    }, [accounts]);

    // Hierarchy Depth
    const hierarchyDepth = useMemo(() => {
        const levelCounts: Record<number, number> = {};
        accounts.forEach(acc => {
            levelCounts[acc.level] = (levelCounts[acc.level] || 0) + 1;
        });

        return Object.entries(levelCounts).map(([level, count]) => ({
            level: `Level ${level}`,
            count
        }));
    }, [accounts]);

    return (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Account Types Distribution - Pie Chart */}
            <Card className="rounded-xl border shadow">
                <CardHeader>
                    <CardTitle className="text-base">Account Types Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie
                                data={typeDistribution}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={(props) => {
                                    const { name, percent, cx, cy, midAngle, innerRadius, outerRadius } = props;
                                    const RADIAN = Math.PI / 180;
                                    const radius = outerRadius + 25;
                                    const x = cx + radius * Math.cos(-midAngle * RADIAN);
                                    const y = cy + radius * Math.sin(-midAngle * RADIAN);
                                    return (
                                        <text
                                            x={x}
                                            y={y}
                                            fill={isDark ? 'hsl(var(--foreground))' : 'hsl(var(--foreground))'}
                                            textAnchor={x > cx ? 'start' : 'end'}
                                            dominantBaseline="central"
                                            fontSize={12}
                                        >
                                            {`${name} ${(percent * 100).toFixed(0)}%`}
                                        </text>
                                    );
                                }}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                                animationDuration={800}
                            >
                                {typeDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Categories Breakdown - Bar Chart */}
            <Card className="rounded-xl border shadow">
                <CardHeader>
                    <CardTitle className="text-base">Categories Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={categoriesBreakdown}>
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                                opacity={isDark ? 0.2 : 0.1}
                            />
                            <XAxis
                                dataKey="category"
                                tick={{ fontSize: 12, fill: isDark ? 'hsl(var(--foreground))' : 'hsl(var(--foreground))' }}
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                            />
                            <YAxis
                                tick={{ fontSize: 12, fill: isDark ? 'hsl(var(--foreground))' : 'hsl(var(--foreground))' }}
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: isDark ? 'hsl(var(--popover))' : 'hsl(var(--popover))',
                                    borderColor: isDark ? 'hsl(var(--border))' : 'hsl(var(--border))',
                                    color: isDark ? 'hsl(var(--popover-foreground))' : 'hsl(var(--popover-foreground))'
                                }}
                            />
                            <Legend />
                            <Bar dataKey="headers" fill={COLORS[0]} name="Headers" animationDuration={800} />
                            <Bar dataKey="details" fill={COLORS[1]} name="Details" animationDuration={800} />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Hierarchy Depth - Bar Chart */}
            <Card className="rounded-xl border shadow">
                <CardHeader>
                    <CardTitle className="text-base">Hierarchy Depth</CardTitle>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={hierarchyDepth}>
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                                opacity={isDark ? 0.2 : 0.1}
                            />
                            <XAxis
                                dataKey="level"
                                tick={{ fontSize: 12, fill: isDark ? 'hsl(var(--foreground))' : 'hsl(var(--foreground))' }}
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                            />
                            <YAxis
                                tick={{ fontSize: 12, fill: isDark ? 'hsl(var(--foreground))' : 'hsl(var(--foreground))' }}
                                stroke={isDark ? 'hsl(var(--border))' : 'hsl(var(--border))'}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: isDark ? 'hsl(var(--popover))' : 'hsl(var(--popover))',
                                    borderColor: isDark ? 'hsl(var(--border))' : 'hsl(var(--border))',
                                    color: isDark ? 'hsl(var(--popover-foreground))' : 'hsl(var(--popover-foreground))'
                                }}
                            />
                            <Bar dataKey="count" fill={COLORS[2]} name="Accounts" animationDuration={800} />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>
        </div>
    );
};

export default AnalyticsCharts;
