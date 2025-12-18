/**
 * Onboarding Banner Component
 *
 * Shows on dashboard when company onboarding is incomplete.
 * Prompts user to resume wizard.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Scroll, ArrowRight, X } from 'lucide-react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { api } from '@/lib/api';

interface OnboardingBannerProps {
  companyId: string;
}

interface OnboardingStatus {
  company_id: string;
  company_name: string;
  onboarding_status: 'DRAFT' | 'TEMPLATE_SELECTED' | 'CHART_READY' | 'CHART_FINALIZED' | 'ACTIVE';
  current_step: number;
  can_resume: boolean;
  step_6_activated: boolean;
}

const OnboardingBanner: React.FC<OnboardingBannerProps> = ({ companyId }) => {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = React.useState(false);

  // Fetch onboarding status
  const { data: status } = useQuery<OnboardingStatus>({
    queryKey: ['onboarding-status', companyId],
    queryFn: async () => {
      const response = await api.get(`/onboarding/status/${companyId}`);
      return response as any;
    },
    enabled: !!companyId && !dismissed,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Don't show if completed or dismissed
  if (!status || status.step_6_activated || dismissed) {
    return null;
  }

  // Calculate progress
  const progress = ((status.current_step + 1) / 8) * 100;

  const handleResume = () => {
    navigate(`/onboarding/${companyId}`);
  };

  const handleDismiss = () => {
    setDismissed(true);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className="mb-6"
      >
        <Alert className="border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50 relative">
          <div className="flex items-start space-x-4">
            {/* Icon */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                <Scroll className="h-6 w-6 text-amber-700" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-lg font-bold text-amber-900">
                    Complete Your Accounting Setup
                  </h3>
                  <p className="text-sm text-amber-800 mt-1">
                    You're {Math.round(progress)}% done. Resume where you left off to activate accounting for{' '}
                    <strong>{status.company_name}</strong>.
                  </p>
                </div>

                {/* Close Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDismiss}
                  className="flex-shrink-0 -mr-2 -mt-1 text-amber-700 hover:text-amber-900"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Progress Bar */}
              <div className="mb-3">
                <Progress value={progress} className="h-2 bg-amber-200" />
                <p className="text-xs text-amber-700 mt-1">
                  Step {status.current_step + 1} of 8
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-3">
                <Button
                  onClick={handleResume}
                  className="bg-amber-600 hover:bg-amber-700 text-white shadow-lg"
                >
                  Resume Setup
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>

                <span className="text-xs text-amber-700">
                  Takes ~{Math.ceil((8 - status.current_step) * 2)} minutes to complete
                </span>
              </div>
            </div>
          </div>
        </Alert>
      </motion.div>
    </AnimatePresence>
  );
};

export default OnboardingBanner;
