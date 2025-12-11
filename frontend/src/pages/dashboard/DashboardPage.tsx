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
  Scroll,
  Feather,
  Landmark,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { cn } from '@/lib/utils';

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
      title: 'Active Companies',
      value: 0,
      description: 'Entities in the Agora',
      icon: Building2,
      link: '/companies',
    },
    {
      title: 'Council Members',
      value: 0,
      description: 'Active scribes & auditors',
      icon: Users,
      link: '/registration/users',
    },
    {
      title: 'Last Access',
      value: 'N/A',
      description: 'Most recently visited chamber',
      icon: Clock,
    },
    {
      title: 'Master Ledger',
      value: 345,
      description: 'Standardized accounts',
      icon: TrendingUp,
      link: '/chartforge/masterchart',
    },
  ]);

  const [activities, setActivities] = useState<ActivityItem[]>([
    {
      id: '1',
      user: 'System',
      action: 'The Atrium has been opened',
      timestamp: 'Just now',
      type: 'success',
    },
    {
      id: '2',
      user: 'Chief Scribe',
      action: 'Master ledger updated with 345 entries',
      timestamp: '1 minute ago',
      type: 'info',
    },
    {
      id: '3',
      user: 'System',
      action: 'Archives secured and backed up',
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
        type: "spring" as const,
        stiffness: 100,
      },
    },
  };

  return (
    <div className="p-10 space-y-8 relative overflow-hidden min-h-full">
      {/* Background Elements */}
      <div className="absolute inset-0 marble-texture opacity-30 pointer-events-none" />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10"
      >
        <h1 className="text-4xl font-heading font-bold text-gradient-gold mb-2 tracking-wide">
          The Atrium
        </h1>
        <p className="text-lg text-muted-foreground font-body max-w-2xl">
          Welcome to the heart of Aequitas. Oversee your financial empire from this central hall.
        </p>
      </motion.div>

      {/* Stats Cards - The Mosaic */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div key={stat.title} variants={itemVariants}>
              <Card className="hover:shadow-card hover:-translate-y-1 transition-all duration-300 cursor-pointer border-0 bg-card/80 backdrop-blur-sm stone-border group overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Icon className="h-24 w-24 -mr-8 -mt-8" />
                </div>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                  <CardTitle className="text-sm font-medium font-heading uppercase tracking-wider text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-gold" />
                </CardHeader>
                <CardContent className="relative z-10">
                  <div className="text-2xl font-bold font-heading text-foreground">{stat.value}</div>
                  <p className="text-xs text-muted-foreground mt-1 font-body">
                    {stat.description}
                  </p>
                  {stat.link && (
                    <Link
                      to={stat.link}
                      className="text-xs text-gold hover:text-gold-light mt-2 inline-flex items-center gap-1 font-medium group/link"
                    >
                      Enter Chamber <span className="group-hover/link:translate-x-0.5 transition-transform">→</span>
                    </Link>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Quick Actions - Herald's Desk */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        className="relative z-10"
      >
        <Card className="border-0 bg-card/50 stone-border shadow-inset">
          <CardHeader>
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <Feather className="h-5 w-5 text-gold" />
              Herald's Desk
            </CardTitle>
            <CardDescription className="font-body">
              Common decrees and actions
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-4">
            <Link to="/companies">
              <Button className="gap-2 bg-gradient-emerald text-white font-heading shadow-glow hover:brightness-110 border-0">
                <Plus className="h-4 w-4" />
                Establish Entity
              </Button>
            </Link>
            <Link to="/chartforge/import">
              <Button variant="outline" className="gap-2 border-gold/30 hover:border-gold hover:bg-gold/5 text-foreground">
                <Upload className="h-4 w-4" />
                Import Scrolls
              </Button>
            </Link>
            <Link to="/reports/statements">
              <Button variant="outline" className="gap-2 border-gold/30 hover:border-gold hover:bg-gold/5 text-foreground">
                <FileText className="h-4 w-4" />
                Consult Reports
              </Button>
            </Link>
            <Link to="/chartforge/masterchart">
              <Button variant="outline" className="gap-2 border-gold/30 hover:border-gold hover:bg-gold/5 text-foreground">
                <TrendingUp className="h-4 w-4" />
                View Master Ledger
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Activity - Scribe's Log */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="relative z-10"
      >
        <Card className="border-0 bg-card/80 stone-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 font-heading text-xl">
                  <Scroll className="h-5 w-5 text-gold" />
                  Scribe's Log
                </CardTitle>
                <CardDescription className="font-body">
                  Recent inscriptions in the archives
                </CardDescription>
              </div>
              <Link to="/admin/audit">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-gold">
                  View Full Chronicle
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start space-x-4 p-4 rounded-lg bg-background/50 border border-border/50 hover:border-gold/30 transition-colors animate-fade-up"
                >
                  <div
                    className={cn(
                      "w-2 h-2 mt-2 rounded-full shadow-[0_0_8px]",
                      activity.type === 'success' ? 'bg-emerald-500 shadow-emerald-500/50' :
                        activity.type === 'warning' ? 'bg-amber-500 shadow-amber-500/50' :
                          'bg-blue-500 shadow-blue-500/50'
                    )}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-bold font-heading text-foreground">
                      {activity.user}
                    </p>
                    <p className="text-sm text-muted-foreground font-body">
                      {activity.action}
                    </p>
                    <p className="text-xs text-muted-foreground/50 mt-1 font-mono">
                      {activity.timestamp}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Getting Started Guide - The Path */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        className="relative z-10 pb-10"
      >
        <Card className="bg-gradient-marble border-0 stone-border">
          <CardHeader>
            <CardTitle className="font-heading text-xl text-center text-foreground">The Path to Order</CardTitle>
            <CardDescription className="text-center font-body">
              Follow these steps to bring balance to your ledger
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-lg hover:bg-gold/5 transition-colors group cursor-pointer">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gold text-background font-bold font-heading shadow-gold group-hover:scale-110 transition-transform">
                  I
                </div>
                <Link to="/companies" className="font-bold text-foreground group-hover:text-gold transition-colors font-heading">Register Entity</Link>
                <span className="text-xs text-muted-foreground">Define the company structure</span>
              </div>

              <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-lg hover:bg-gold/5 transition-colors group cursor-pointer">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gold text-background font-bold font-heading shadow-gold group-hover:scale-110 transition-transform">
                  II
                </div>
                <Link to="/chartforge/import" className="font-bold text-foreground group-hover:text-gold transition-colors font-heading">Import Charts</Link>
                <span className="text-xs text-muted-foreground">Bring in existing accounts</span>
              </div>

              <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-lg hover:bg-gold/5 transition-colors group cursor-pointer">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gold text-background font-bold font-heading shadow-gold group-hover:scale-110 transition-transform">
                  III
                </div>
                <Link to="/chartforge/mapping" className="font-bold text-foreground group-hover:text-gold transition-colors font-heading">Map Accounts</Link>
                <span className="text-xs text-muted-foreground">Align with Master Ledger</span>
              </div>

              <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-lg hover:bg-muted transition-colors opacity-60">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted text-muted-foreground font-bold font-heading border border-muted-foreground/30">
                  IV
                </div>
                <span className="font-bold text-muted-foreground font-heading">Record Entries</span>
                <span className="text-xs text-muted-foreground">(Awaiting Activation)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default DashboardPage;
