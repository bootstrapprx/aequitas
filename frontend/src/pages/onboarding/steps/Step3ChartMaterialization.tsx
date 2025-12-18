/**
 * Step 3: Build Your Chart (Materialization)
 *
 * SYSTEM-CONTROLLED STEP:
 * - User clicks button to start
 * - System creates all accounts atomically
 * - Progress indicator shows status
 * - On completion, auto-advances
 *
 * UX Rule:
 * - This step is never partially visible
 * - Either "in progress" or "complete"
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Hammer, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent, QuillIcon } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { api } from '@/lib/api';

interface Step3ChartMaterializationProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

const Step3ChartMaterialization: React.FC<Step3ChartMaterializationProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);
  const [currentAction, setCurrentAction] = useState('Preparing...');
  const [isComplete, setIsComplete] = useState(status?.step_3_chart_materialized || false);
  const [accountsCreated, setAccountsCreated] = useState(0);
  const [apiError, setApiError] = useState<string | null>(null);

  // Mutation to materialize chart
  const materializeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/onboarding/${companyId}/materialize-chart`, {
        confirm_proceed: true
      });
      return response as any;
    },
    onSuccess: (data) => {
      setApiError(null);
      setAccountsCreated(data.accounts_created);
      setIsComplete(true);
      setProgress(100);
      setCurrentAction('Complete!');
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });

      // Auto-advance after 2 seconds
      setTimeout(() => {
        onNext();
      }, 2000);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to create chart of accounts. Please try again.';
      setApiError(errorMessage);
      setProgress(0);
      setCurrentAction('Failed');
    }
  });

  const handleStart = () => {
    setProgress(10);
    setCurrentAction('Creating account hierarchy...');

    // Simulate progress updates
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    setCurrentAction('Applying accounting rules...');

    setTimeout(() => {
      setCurrentAction('Finalizing structure...');
      materializeMutation.mutate();
      clearInterval(interval);
    }, 600);
  };

  // If already materialized, show completion state
  if (isComplete || status?.step_3_chart_materialized) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="space-y-6"
      >
        <div className="text-center py-12">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="inline-block mb-6"
          >
            <div className="w-24 h-24 bg-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-gold">
              <CheckCircle2 className="h-12 w-12 text-white" />
            </div>
          </motion.div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2 embossed-gold">
            Chart of Accounts Created!
          </h2>
          <p className="text-gray-600 mb-6">
            Your chart of accounts is ready for review and customization.
          </p>

          {accountsCreated > 0 && (
            <div className="inline-block bg-emerald-50 rounded-lg px-6 py-3 mb-6">
              <p className="text-sm text-emerald-800">
                <strong className="text-2xl">{accountsCreated}</strong> accounts created
              </p>
            </div>
          )}

          <Button onClick={onNext} size="lg" className="shadow-gold">
            Review Accounts
          </Button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 embossed-gold">
          Build Your Chart of Accounts
        </h2>
        <p className="text-gray-600">
          We'll create your complete chart of accounts from the selected template.
        </p>
      </div>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {/* Explanation Card */}
      {!materializeMutation.isPending && (
        <AtheneumCard>
          <AtheneumCardHeader icon={<Hammer className="h-5 w-5" />} embossed>
            What Happens Next
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <ul className="space-y-3 text-sm text-gray-700">
              <li className="flex items-start space-x-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>All accounts from the template will be copied to your company</span>
              </li>
              <li className="flex items-start space-x-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>Account hierarchy and structure will be preserved</span>
              </li>
              <li className="flex items-start space-x-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>Mandatory accounts will be marked (cannot be deleted)</span>
              </li>
              <li className="flex items-start space-x-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>You'll be able to customize and add accounts in the next step</span>
              </li>
            </ul>

            <Alert className="mt-6 border-blue-200 bg-blue-50">
              <AlertDescription className="text-blue-900 text-sm">
                <strong>Note:</strong> This operation is atomic. If anything fails, the entire operation will be rolled back automatically.
              </AlertDescription>
            </Alert>
          </AtheneumCardContent>
        </AtheneumCard>
      )}

      {/* Progress Card (shown when materializing) */}
      {materializeMutation.isPending && (
        <AtheneumCard glow>
          <AtheneumCardContent>
            <div className="py-8 space-y-6">
              {/* Animated Icon */}
              <div className="flex justify-center">
                <QuillIcon isWriting={true} size="lg" />
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <Progress value={progress} className="h-3" />
                <p className="text-center text-sm text-gray-600">
                  {currentAction}
                </p>
              </div>

              {/* Please Wait */}
              <p className="text-center text-xs text-gray-500">
                Please wait while we create your chart of accounts...
              </p>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={materializeMutation.isPending}
        >
          Back
        </Button>

        {!materializeMutation.isPending && !isComplete && (
          <Button
            onClick={handleStart}
            size="lg"
            className="shadow-gold"
          >
            <Hammer className="mr-2 h-5 w-5" />
            Create Chart of Accounts
          </Button>
        )}

        {materializeMutation.isPending && (
          <Button disabled size="lg">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Creating...
          </Button>
        )}
      </div>
    </motion.div>
  );
};

export default Step3ChartMaterialization;
