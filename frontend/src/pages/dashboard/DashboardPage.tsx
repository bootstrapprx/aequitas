import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Building2,
  Users,
  Clock,
  TrendingUp,
  Plus,
  Upload,
  FileText,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface StatCard {
  title: string;
  value: string | number;
  description: string;
  icon: React.ElementType;
  trend?: string;
  link?: string;
}

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  timestamp: string;
  type: 'success' | 'info' | 'warning';
}

const DashboardPage = () => {
  const [stats, setStats] = useState<StatCard[]>([
    {
      title: 'Companies',
      value: 0,
      description: 'Total companies registered',
      icon: Building2,
      link: '/companies',
    },
    {
      title: 'Users',
      value: 0,
      description: 'Active users in system',
      icon: Users,
      link: '/registration/users',
    },
    {
      title: 'Last Access',
      value: 'N/A',
      description: 'Most recently accessed company',
      icon: Clock,
    },
    {
      title: 'Master Accounts',
      value: 345,
      description: 'US-GAAP master chart accounts',
      icon: TrendingUp,
      link: '/chartforge/masterchart',
    },
  ]);

  const [activities, setActivities] = useState<ActivityItem[]>([
    {
      id: '1',
      user: 'System',
      action: 'Aequitas system initialized',
      timestamp: 'Just now',
      type: 'success',
    },
    {
      id: '2',
      user: 'Admin',
      action: 'Master chart loaded with 345 accounts',
      timestamp: '1 minute ago',
      type: 'info',
    },
    {
      id: '3',
      user: 'System',
      action: 'Database backup completed',
      timestamp: '1 hour ago',
      type: 'success',
    },
  ]);

  // Fetch real data from API
  useEffect(() => {
    // TODO: Fetch companies count
    // TODO: Fetch users count
    // TODO: Fetch last accessed company
    // TODO: Fetch recent activities
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
      },
    },
  };

  return (
    <div className="p-10 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome to Aequitas
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Integrated Accounting System
        </p>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <motion.div key={stat.title} variants={itemVariants}>
              <Card className="hover:shadow-xl transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stat.description}
                  </p>
                  {stat.link && (
                    <Link
                      to={stat.link}
                      className="text-xs text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 mt-2 inline-block"
                    >
                      View details →
                    </Link>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks to get you started
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-4">
            <Link to="/companies">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                New Company
              </Button>
            </Link>
            <Link to="/chartforge/import">
              <Button variant="outline" className="gap-2">
                <Upload className="h-4 w-4" />
                Import Data
              </Button>
            </Link>
            <Link to="/reports/statements">
              <Button variant="outline" className="gap-2">
                <FileText className="h-4 w-4" />
                View Reports
              </Button>
            </Link>
            <Link to="/chartforge/masterchart">
              <Button variant="outline" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                Master Chart
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Recent Activity
                </CardTitle>
                <CardDescription>
                  Latest actions in your system
                </CardDescription>
              </div>
              <Link to="/admin/audit">
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start space-x-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div
                    className={`w-2 h-2 mt-2 rounded-full ${activity.type === 'success'
                        ? 'bg-green-500'
                        : activity.type === 'warning'
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {activity.user}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {activity.action}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {activity.timestamp}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Getting Started Guide */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
      >
        <Card className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 border-green-200 dark:border-green-800">
          <CardHeader>
            <CardTitle>Getting Started with Aequitas</CardTitle>
            <CardDescription className="text-gray-700 dark:text-gray-300">
              Follow these steps to set up your accounting system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-xs font-bold">
                  1
                </div>
                <Link
                  to="/companies"
                  className="text-sm text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400"
                >
                  Register your first company
                </Link>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-xs font-bold">
                  2
                </div>
                <Link
                  to="/chartforge/import"
                  className="text-sm text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400"
                >
                  Import your chart of accounts
                </Link>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-xs font-bold">
                  3
                </div>
                <Link
                  to="/chartforge/mapping"
                  className="text-sm text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400"
                >
                  Map accounts to master chart
                </Link>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-400 text-white text-xs font-bold">
                  4
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Start recording transactions (coming soon)
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default DashboardPage;
