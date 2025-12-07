import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  ChartBar,
  Shield,
  Zap,
  CheckCircle,
  ArrowRight,
  Users,
  TrendingUp,
  Lock,
  Cloud,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: ChartBar,
      title: 'Chart of Accounts',
      description: 'AI-powered chart of accounts management with 345 US-GAAP master accounts',
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
    },
    {
      icon: Building2,
      title: 'Multi-Company',
      description: 'Manage multiple companies from a single dashboard with role-based access',
      color: 'text-navy-600',
      bgColor: 'bg-navy-50',
    },
    {
      icon: Zap,
      title: 'QuickBooks Integration',
      description: 'Seamless sync with QuickBooks Online for automatic account mapping',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Bank-level encryption with role-based permissions and audit trails',
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description: 'Invite team members with granular permissions and company access',
      color: 'text-navy-600',
      bgColor: 'bg-navy-50',
    },
    {
      icon: TrendingUp,
      title: 'Real-time Analytics',
      description: 'Live dashboards with financial insights and performance metrics',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
  ];

  const stats = [
    { value: '345', label: 'US-GAAP Accounts' },
    { value: '99%', label: 'Mapping Accuracy' },
    { value: '10k+', label: 'Accounts Managed' },
    { value: '24/7', label: 'Support Available' },
  ];

  const benefits = [
    'Automated account mapping with AI',
    'QuickBooks Online integration',
    'Multi-company management',
    'Role-based access control',
    'Comprehensive audit trails',
    'Export to Excel & templates',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Building2 className="h-8 w-8 text-teal-600" />
              <span className="text-2xl font-bold text-gray-900">aequitas</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/login')}
                className="text-gray-700 hover:text-gray-900"
              >
                Sign In
              </Button>
              <Button
                onClick={() => navigate('/register')}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
                Intelligent
                <span className="block text-teal-600">Chart of Accounts</span>
                Management
              </h1>
              <p className="mt-6 text-xl text-gray-600 leading-relaxed">
                Transform your accounting workflow with AI-powered account mapping,
                seamless QuickBooks integration, and comprehensive US-GAAP compliance.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  onClick={() => navigate('/register')}
                  className="bg-teal-600 hover:bg-teal-700 text-white text-lg px-8 py-6"
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/login')}
                  className="border-2 border-gray-300 text-lg px-8 py-6"
                >
                  Watch Demo
                </Button>
              </div>
              <div className="mt-8 flex items-center gap-6 text-sm text-gray-600">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                  No credit card required
                </div>
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                  14-day free trial
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="relative">
                <div className="absolute -inset-4 bg-gradient-to-r from-teal-400 to-blue-500 rounded-3xl blur-2xl opacity-20"></div>
                <Card className="relative bg-white shadow-2xl border-0">
                  <CardContent className="p-8">
                    <div className="space-y-6">
                      {/* Mock Dashboard Preview */}
                      <div className="flex items-center justify-between pb-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Dashboard Overview</h3>
                        <div className="flex space-x-2">
                          <div className="w-3 h-3 rounded-full bg-red-400"></div>
                          <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                          <div className="w-3 h-3 rounded-full bg-green-400"></div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {stats.map((stat, index) => (
                          <div
                            key={index}
                            className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4"
                          >
                            <div className="text-2xl font-bold text-teal-600">{stat.value}</div>
                            <div className="text-sm text-gray-600 mt-1">{stat.label}</div>
                          </div>
                        ))}
                      </div>
                      <div className="h-32 bg-gradient-to-r from-teal-100 to-blue-100 rounded-xl flex items-end justify-around p-4">
                        {[40, 70, 45, 85, 60, 95, 75].map((height, i) => (
                          <div
                            key={i}
                            className="bg-teal-600 rounded-t w-8"
                            style={{ height: `${height}%` }}
                          ></div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 -z-10 opacity-30">
          <div className="w-96 h-96 bg-teal-200 rounded-full blur-3xl"></div>
        </div>
        <div className="absolute bottom-0 left-0 -z-10 opacity-30">
          <div className="w-96 h-96 bg-blue-200 rounded-full blur-3xl"></div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-900">
              Everything you need to manage your accounts
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Powerful features designed for modern accounting teams
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <Card className="h-full hover:shadow-xl transition-all duration-300 border-0 bg-white">
                  <CardContent className="p-6">
                    <div
                      className={`${feature.bgColor} w-12 h-12 rounded-xl flex items-center justify-center mb-4`}
                    >
                      <feature.icon className={`h-6 w-6 ${feature.color}`} />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                Built for accountants, by accountants
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Aequitas combines decades of accounting expertise with cutting-edge AI
                technology to deliver the most comprehensive chart of accounts management
                system available.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="flex items-start"
                  >
                    <CheckCircle className="h-6 w-6 text-teal-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 text-lg">{benefit}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="relative"
            >
              <Card className="bg-gradient-to-br from-teal-600 to-blue-600 text-white border-0 shadow-2xl">
                <CardContent className="p-8">
                  <div className="flex items-center mb-6">
                    <Lock className="h-8 w-8 mr-3" />
                    <h3 className="text-2xl font-bold">Enterprise Security</h3>
                  </div>
                  <p className="text-teal-50 mb-6 text-lg">
                    Your financial data is protected with bank-level encryption, SOC 2
                    compliance, and comprehensive audit trails.
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                      <Shield className="h-6 w-6 mb-2" />
                      <div className="text-sm font-semibold">256-bit Encryption</div>
                    </div>
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                      <Cloud className="h-6 w-6 mb-2" />
                      <div className="text-sm font-semibold">Cloud Backup</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-teal-600 to-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to transform your accounting workflow?
            </h2>
            <p className="text-xl text-teal-50 mb-8">
              Join thousands of accountants who trust Aequitas for their chart of accounts
              management.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/register')}
                className="bg-white text-teal-600 hover:bg-gray-100 text-lg px-8 py-6"
              >
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-6"
              >
                Schedule Demo
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Building2 className="h-6 w-6 text-teal-500" />
                <span className="text-xl font-bold text-white">aequitas</span>
              </div>
              <p className="text-sm">
                Intelligent chart of accounts management for modern accounting teams.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li>Features</li>
                <li>Pricing</li>
                <li>Security</li>
                <li>Integrations</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li>About</li>
                <li>Blog</li>
                <li>Careers</li>
                <li>Contact</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li>Privacy Policy</li>
                <li>Terms of Service</li>
                <li>Cookie Policy</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            <p>&copy; 2024 Aequitas. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
