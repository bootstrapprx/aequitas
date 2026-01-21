/**
 * Completion Screen
 *
 * Success message with:
 * - Celebration animation
 * - Summary of what was accomplished
 * - Suggested next actions
 * - Navigation to dashboard or first journal entry
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PartyPopper, FileText, Scale, Users, ArrowRight } from 'lucide-react';

import { ScrollUnfurl, AtheneumCard, AtheneumCardContent, WaxSealBadge } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';

interface StepCompletionProps {
  companyId: string;
  status: any;
}

const StepCompletion: React.FC<StepCompletionProps> = ({ companyId, status }) => {
  const navigate = useNavigate();
  const kernelVersion = status?.kernel_version ?? 'N/A';
  const kernelLayer = status?.kernel_layer ?? 'N/A';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="space-y-8"
    >
      {/* Celebration Header */}
      <div className="text-center py-8">
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
          className="inline-block mb-6"
        >
          <div className="w-32 h-32 bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-full flex items-center justify-center mx-auto shadow-gold">
            <PartyPopper className="h-16 w-16 text-white" />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4 embossed-gold"
        >
          Accounting Is Ready!
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto"
        >
          Your company, <strong className="text-gray-900 dark:text-gray-100">{status?.company_name}</strong>, is now ready to record
          transactions and generate financial reports.
        </motion.p>
      </div>

      {/* Success Summary */}
      <ScrollUnfurl title="Setup Complete" subtitle={`Activated on ${new Date().toLocaleDateString()}`}>
        <div className="space-y-4 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <AtheneumCard>
              <AtheneumCardContent>
                <div className="text-center py-4">
                  <FileText className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-emerald-800">{status?.total_accounts || 0}</p>
                  <p className="text-sm text-gray-600">Active Accounts</p>
                </div>
              </AtheneumCardContent>
            </AtheneumCard>

            <AtheneumCard>
              <AtheneumCardContent>
                <div className="text-center py-4">
                  <Scale className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-blue-800">{status?.open_periods || 0} Open</p>
                  <p className="text-sm text-gray-600">Fiscal Periods</p>
                </div>
              </AtheneumCardContent>
            </AtheneumCard>

            <AtheneumCard>
              <AtheneumCardContent>
                <div className="text-center py-4">
                  <WaxSealBadge type="approved" size="lg" />
                  <p className="text-2xl font-bold text-purple-800 mt-2">Kernel {kernelVersion}</p>
                  <p className="text-sm text-gray-600">Layer {kernelLayer}</p>
                </div>
              </AtheneumCardContent>
            </AtheneumCard>
          </div>
        </div>
      </ScrollUnfurl>

      {/* Next Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="py-6 space-y-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 text-center mb-6">
                What would you like to do next?
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Create First Journal Entry */}
                <Button
                  variant="outline"
                  size="lg"
                  className="h-auto py-6 flex flex-col items-start hover:border-emerald-500 hover:shadow-gold transition-all"
                  onClick={() => window.location.href = '/accountancy/journal'}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <FileText className="h-6 w-6 text-emerald-600" />
                    <span className="font-bold text-lg">Create First Journal Entry</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 text-left">
                    Start recording transactions in the Scribe's Chamber
                  </p>
                  <ArrowRight className="h-4 w-4 ml-auto mt-2 text-emerald-600" />
                </Button>

                {/* View Trial Balance */}
                <Button
                  variant="outline"
                  size="lg"
                  className="h-auto py-6 flex flex-col items-start hover:border-blue-500 hover:shadow-gold transition-all"
                  onClick={() => window.location.href = '/accountancy/trial-balance'}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <Scale className="h-6 w-6 text-blue-600" />
                    <span className="font-bold text-lg">View Trial Balance</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 text-left">
                    Check the balance of your accounts in the Hall of Balance
                  </p>
                  <ArrowRight className="h-4 w-4 ml-auto mt-2 text-blue-600" />
                </Button>

                {/* Invite Team Members */}
                <Button
                  variant="outline"
                  size="lg"
                  className="h-auto py-6 flex flex-col items-start hover:border-purple-500 hover:shadow-gold transition-all"
                  onClick={() => window.location.href = '/admin/users'}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <Users className="h-6 w-6 text-purple-600" />
                    <span className="font-bold text-lg">Invite Team Members</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 text-left">
                    Add users and assign permissions to your accounting team
                  </p>
                  <ArrowRight className="h-4 w-4 ml-auto mt-2 text-purple-600" />
                </Button>

                {/* Go to Dashboard */}
                <Button
                  size="lg"
                  className="h-auto py-6 flex flex-col items-start shadow-gold bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => window.location.href = '/dashboard'}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="font-bold text-lg">Go to Dashboard</span>
                  </div>
                  <p className="text-sm text-emerald-100 text-left">
                    View your company overview and get started
                  </p>
                  <ArrowRight className="h-4 w-4 ml-auto mt-2" />
                </Button>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      </motion.div>

      {/* Footer Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="text-center text-sm text-gray-500 pt-6 border-t border-gray-200"
      >
        <p>
          Need help getting started? Check out the{' '}
          <a href="/help" className="text-emerald-600 hover:underline">
            documentation
          </a>{' '}
          or{' '}
          <a href="/support" className="text-emerald-600 hover:underline">
            contact support
          </a>
          .
        </p>
      </motion.div>
    </motion.div>
  );
};

export default StepCompletion;
