import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  TrendingUp,
  DollarSign,
  Users,
  FileText,
  ChevronDown,
  RefreshCw,
  Download,
  Settings,
  Bell,
  MoreVertical,
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

// Mock data - replace with actual API calls
const mockCompanies = [
  { id: '1', name: 'Acme Corporation', ucid: 'ACME001' },
  { id: '2', name: 'TechStart Inc.', ucid: 'TECH002' },
  { id: '3', name: 'Global Enterprises', ucid: 'GLOB003' },
];

const mockMetrics = {
  totalAccounts: 342,
  mappedAccounts: 318,
  activeUsers: 12,
  pendingReviews: 5,
  recentActivity: [
    { id: 1, action: 'Account mapped', user: 'John Doe', time: '2 hours ago', type: 'mapping' },
    { id: 2, action: 'User invited', user: 'Jane Smith', time: '4 hours ago', type: 'user' },
    { id: 3, action: 'Chart exported', user: 'Bob Wilson', time: '1 day ago', type: 'export' },
    { id: 4, action: 'QBO synced', user: 'System', time: '1 day ago', type: 'sync' },
  ],
};

const CompanyDashboard = () => {
  const { user, currentCompanyId, switchCompany } = useAuth();
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(currentCompanyId || '');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, [selectedCompanyId]);

  const handleCompanyChange = (companyId: string) => {
    setSelectedCompanyId(companyId);
    switchCompany(companyId);
    setIsLoading(true);
  };

  const selectedCompany = mockCompanies.find((c) => c.id === selectedCompanyId);
  const mappingPercentage = Math.round(
    (mockMetrics.mappedAccounts / mockMetrics.totalAccounts) * 100
  );

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
                <Select value={selectedCompanyId} onValueChange={handleCompanyChange}>
                  <SelectTrigger className="border-0 text-lg font-semibold text-foreground hover:bg-muted/50">
                    <SelectValue placeholder="Select company..." />
                  </SelectTrigger>
                  <SelectContent>
                    {mockCompanies.map((company) => (
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
                {mockMetrics.pendingReviews > 0 && (
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 text-center">
                    <div className="text-3xl font-bold">{mockMetrics.pendingReviews}</div>
                    <div className="text-sm text-teal-50">Pending Reviews</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

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
                value={mockMetrics.totalAccounts}
                subtitle="In chart of accounts"
                icon={FileText}
                color="teal"
              />
              <StatsCard
                title="Mapped Accounts"
                value={mockMetrics.mappedAccounts}
                subtitle={`${mappingPercentage}% completion`}
                icon={TrendingUp}
                trend={{ value: 12, isPositive: true }}
                color="navy"
              />
              <StatsCard
                title="Active Users"
                value={mockMetrics.activeUsers}
                subtitle="Team members"
                icon={Users}
                color="yellow"
              />
              <StatsCard
                title="Pending Reviews"
                value={mockMetrics.pendingReviews}
                subtitle="Requires attention"
                icon={Bell}
                color="red"
              />
            </motion.div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Account Distribution */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="lg:col-span-2"
              >
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow bg-card text-card-foreground">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-foreground">Account Mapping Progress</CardTitle>
                        <CardDescription className="text-muted-foreground">Monthly mapping activity</CardDescription>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm" className="border-border text-foreground hover:bg-muted">
                            Last 30 days
                            <ChevronDown className="ml-2 h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-popover text-popover-foreground border-border">
                          <DropdownMenuItem className="hover:bg-muted">Last 7 days</DropdownMenuItem>
                          <DropdownMenuItem className="hover:bg-muted">Last 30 days</DropdownMenuItem>
                          <DropdownMenuItem className="hover:bg-muted">Last 90 days</DropdownMenuItem>
                          <DropdownMenuItem className="hover:bg-muted">This year</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Mock Chart - Replace with actual chart library */}
                    <div className="h-64 flex items-end justify-around space-x-2 p-4 bg-gradient-to-t from-muted/20 to-transparent rounded-lg">
                      {[65, 80, 55, 90, 70, 85, 75, 95, 80, 85, 90, 93].map((height, i) => (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <div
                            className="w-full bg-gradient-to-t from-primary to-primary/60 rounded-t-lg transition-all hover:opacity-80"
                            style={{ height: `${height}%` }}
                          ></div>
                          <span className="text-xs text-muted-foreground mt-2">
                            {['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'][i]}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Account Categories */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow bg-card text-card-foreground">
                  <CardHeader>
                    <CardTitle className="text-foreground">Account Distribution</CardTitle>
                    <CardDescription className="text-muted-foreground">By category</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Mock Donut Chart */}
                    <div className="relative flex items-center justify-center h-48">
                      <svg className="w-40 h-40 transform -rotate-90">
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="none"
                          stroke="hsl(var(--secondary))"
                          strokeWidth="20"
                          strokeDasharray="113 377"
                        />
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="none"
                          stroke="hsl(var(--accent))"
                          strokeWidth="20"
                          strokeDasharray="132 377"
                          strokeDashoffset="-113"
                        />
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="none"
                          stroke="hsl(var(--primary))"
                          strokeWidth="20"
                          strokeDasharray="132 377"
                          strokeDashoffset="-245"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-foreground">
                            {mappingPercentage}%
                          </div>
                          <div className="text-xs text-muted-foreground">Mapped</div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-6 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-secondary mr-2"></div>
                          <span className="text-sm text-foreground">Assets</span>
                        </div>
                        <span className="text-sm font-semibold text-foreground">30%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-accent mr-2"></div>
                          <span className="text-sm text-foreground">Liabilities</span>
                        </div>
                        <span className="text-sm font-semibold text-foreground">35%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-primary mr-2"></div>
                          <span className="text-sm text-foreground">Equity</span>
                        </div>
                        <span className="text-sm font-semibold text-foreground">35%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Recent Activity */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Card className="border-0 shadow-md hover:shadow-lg transition-shadow bg-card text-card-foreground">
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
                    {mockMetrics.recentActivity.map((activity) => (
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
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground">
                            {activity.action}
                          </p>
                          <p className="text-sm text-muted-foreground">{activity.user}</p>
                        </div>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {activity.time}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </>
        )}
      </main>
    </div>
  );
};

export default CompanyDashboard;
