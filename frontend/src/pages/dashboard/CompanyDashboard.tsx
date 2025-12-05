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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo + Company Selector */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Building2 className="h-6 w-6 text-teal-600" />
                <span className="text-xl font-bold text-gray-900">aequitas</span>
              </div>
              <div className="h-8 w-px bg-gray-300"></div>
              <div className="min-w-[250px]">
                <Select value={selectedCompanyId} onValueChange={handleCompanyChange}>
                  <SelectTrigger className="border-0 text-lg font-semibold text-gray-900 hover:bg-gray-50">
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
              <h1 className="text-xl font-semibold text-gray-900">Overview</h1>
            </div>

            {/* Right: Icon Toolbar */}
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="icon" className="hover:bg-gray-100">
                <RefreshCw className="h-5 w-5 text-gray-600" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-gray-100">
                <Download className="h-5 w-5 text-gray-600" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-gray-100">
                <Settings className="h-5 w-5 text-gray-600" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-teal-50">
                <Bell className="h-5 w-5 text-teal-600" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-gray-100">
                <MoreVertical className="h-5 w-5 text-gray-600" />
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
          <Card className="bg-gradient-to-r from-teal-600 to-blue-600 border-0 text-white">
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
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Account Mapping Progress</CardTitle>
                        <CardDescription>Monthly mapping activity</CardDescription>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm">
                            Last 30 days
                            <ChevronDown className="ml-2 h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Last 7 days</DropdownMenuItem>
                          <DropdownMenuItem>Last 30 days</DropdownMenuItem>
                          <DropdownMenuItem>Last 90 days</DropdownMenuItem>
                          <DropdownMenuItem>This year</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Mock Chart - Replace with actual chart library */}
                    <div className="h-64 flex items-end justify-around space-x-2 p-4 bg-gradient-to-t from-gray-50 to-transparent rounded-lg">
                      {[65, 80, 55, 90, 70, 85, 75, 95, 80, 85, 90, 93].map((height, i) => (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <div
                            className="w-full bg-gradient-to-t from-teal-600 to-teal-400 rounded-t-lg transition-all hover:opacity-80"
                            style={{ height: `${height}%` }}
                          ></div>
                          <span className="text-xs text-gray-500 mt-2">
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
                <Card className="border-0 shadow-md hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <CardTitle>Account Distribution</CardTitle>
                    <CardDescription>By category</CardDescription>
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
                          stroke="#1A2B4A"
                          strokeWidth="20"
                          strokeDasharray="113 377"
                        />
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="none"
                          stroke="#F8B739"
                          strokeWidth="20"
                          strokeDasharray="132 377"
                          strokeDashoffset="-113"
                        />
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="none"
                          stroke="#00B8A9"
                          strokeWidth="20"
                          strokeDasharray="132 377"
                          strokeDashoffset="-245"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">
                            {mappingPercentage}%
                          </div>
                          <div className="text-xs text-gray-500">Mapped</div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-6 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-[#1A2B4A] mr-2"></div>
                          <span className="text-sm text-gray-700">Assets</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">30%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-[#F8B739] mr-2"></div>
                          <span className="text-sm text-gray-700">Liabilities</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">35%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-3 h-3 rounded-full bg-[#00B8A9] mr-2"></div>
                          <span className="text-sm text-gray-700">Equity</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">35%</span>
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
              <Card className="border-0 shadow-md hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Recent Activity</CardTitle>
                      <CardDescription>Latest updates across your company</CardDescription>
                    </div>
                    <Button variant="outline" size="sm">
                      View All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockMetrics.recentActivity.map((activity) => (
                      <div
                        key={activity.id}
                        className="flex items-start space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div
                          className={`p-2 rounded-lg ${
                            activity.type === 'mapping'
                              ? 'bg-teal-50'
                              : activity.type === 'user'
                              ? 'bg-blue-50'
                              : activity.type === 'export'
                              ? 'bg-yellow-50'
                              : 'bg-purple-50'
                          }`}
                        >
                          {activity.type === 'mapping' && (
                            <TrendingUp className="h-4 w-4 text-teal-600" />
                          )}
                          {activity.type === 'user' && (
                            <Users className="h-4 w-4 text-blue-600" />
                          )}
                          {activity.type === 'export' && (
                            <Download className="h-4 w-4 text-yellow-600" />
                          )}
                          {activity.type === 'sync' && (
                            <RefreshCw className="h-4 w-4 text-purple-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {activity.action}
                          </p>
                          <p className="text-sm text-gray-500">{activity.user}</p>
                        </div>
                        <span className="text-xs text-gray-400 whitespace-nowrap">
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
