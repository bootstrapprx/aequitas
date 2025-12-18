/**
 * Phase 5 Company Onboarding Wizard
 *
 * CANONICAL REFERENCE:
 * - docs/canonical/PHASE_5_ONBOARDING_GUIDE.md
 *
 * A stateful, linear wizard that guides users through:
 * 1. Welcome
 * 2. Company Details
 * 3. Template Selection
 * 4. Chart Materialization
 * 5. Account Review
 * 6. Fiscal Periods
 * 7. Activation
 *
 * Key Features:
 * - Auto-save and resume
 * - Session locking (multi-session protection)
 * - Irreversible state transitions
 * - Athenaeum theme integration
 * - User-friendly error messages
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import { Feather, CheckCircle2, Circle, Lock } from 'lucide-react';

import { PageHeader } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { api } from '@/lib/api';

// Step components
import Step0Welcome from './steps/Step0Welcome';
import Step1CompanyDetails from './steps/Step1CompanyDetails';
import Step2TemplateSelection from './steps/Step2TemplateSelection';
import Step3ChartMaterialization from './steps/Step3ChartMaterialization';
import Step4AccountReview from './steps/Step4AccountReview';
import Step5FiscalPeriods from './steps/Step5FiscalPeriods';
import Step6Activation from './steps/Step6Activation';
import StepCompletion from './steps/StepCompletion';

// Types
interface OnboardingStatus {
  company_id: string;
  company_name: string;
  onboarding_status: 'DRAFT' | 'TEMPLATE_SELECTED' | 'CHART_READY' | 'CHART_FINALIZED' | 'ACTIVE';
  current_step: number;
  can_resume: boolean;
  is_locked: boolean;
  locked_by_session: string | null;
  started_at: string | null;
  completed_at: string | null;
  step_0_welcome_seen: boolean;
  step_1_company_details_complete: boolean;
  step_2_template_selected: boolean;
  step_3_chart_materialized: boolean;
  step_4_chart_finalized: boolean;
  step_5_fiscal_periods_complete: boolean;
  step_6_activated: boolean;
}

const STEP_TITLES = [
  'Welcome',
  'Company Details',
  'Choose Template',
  'Build Chart',
  'Review Accounts',
  'Fiscal Periods',
  'Activate Accounting',
  'Complete'
];

const OnboardingWizard: React.FC = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [sessionId] = useState(() => uuidv4());
  const [currentStep, setCurrentStep] = useState(0);
  const [lockError, setLockError] = useState<string | null>(null);

  // Fetch onboarding status
  const { data: status, isLoading, error, refetch } = useQuery<OnboardingStatus>({
    queryKey: ['onboarding-status', companyId],
    queryFn: async () => {
      const response = await api.get(`/onboarding/status/${companyId}`);
      return response as any;
    },
    refetchInterval: 10000, // Refetch every 10 seconds to check lock status
  });

  // Acquire session lock on mount
  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/onboarding/lock/${companyId}`, {
        session_id: sessionId
      });
      return response as any;
    },
    onSuccess: (data) => {
      if (!data.locked) {
        setLockError('Another user is currently editing this company onboarding. Please wait and try again.');
      } else {
        setLockError(null);
      }
    }
  });

  // Release session lock on unmount
  useEffect(() => {
    lockMutation.mutate();

    return () => {
      api.delete(`/onboarding/lock/${companyId}`, {
        data: { session_id: sessionId }
      }).catch(() => {
        // Ignore errors on cleanup
      });
    };
  }, [companyId]);

  // Sync current step with backend status
  useEffect(() => {
    if (status) {
      setCurrentStep(status.current_step);

      // If already completed, redirect to completion
      if (status.step_6_activated) {
        setCurrentStep(7); // Completion screen
      }
    }
  }, [status]);

  // Handle step navigation
  const handleNext = () => {
    setCurrentStep(prev => Math.min(prev + 1, 7));
    refetch();
  };

  const handleBack = () => {
    // Prevent going back after irreversible steps
    if (status) {
      if (status.onboarding_status === 'ACTIVE') {
        return; // No going back after activation
      }
      if (status.step_3_chart_materialized && currentStep <= 3) {
        // Cannot go back before chart materialization
        return;
      }
    }
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleStepClick = (stepIndex: number) => {
    // Only allow clicking on completed or current step
    if (!status) return;

    // Cannot skip ahead
    if (stepIndex > currentStep) return;

    // Cannot go back past irreversible steps
    if (status.step_3_chart_materialized && stepIndex < 3) return;
    if (status.step_6_activated && stepIndex < 7) return;

    setCurrentStep(stepIndex);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading onboarding wizard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-10">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load onboarding status. Please refresh the page or contact support.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (lockError) {
    return (
      <div className="p-10">
        <Alert variant="destructive">
          <Lock className="h-4 w-4" />
          <AlertDescription>{lockError}</AlertDescription>
        </Alert>
        <Button onClick={() => lockMutation.mutate()} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  // Calculate progress
  const progress = ((currentStep + 1) / 8) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 to-stone-100">
      {/* Header */}
      <PageHeader
        title="Company Onboarding"
        subtitle={`Set up accounting for ${status?.company_name || 'your company'}`}
        icon={Feather}
      />

      {/* Progress Indicator */}
      <div className="max-w-6xl mx-auto px-10 py-6">
        <div className="mb-8">
          <Progress value={progress} className="h-2 mb-4" />
          <div className="flex justify-between items-start">
            {STEP_TITLES.map((title, index) => {
              const isComplete = status && (
                (index === 0 && status.step_0_welcome_seen) ||
                (index === 1 && status.step_1_company_details_complete) ||
                (index === 2 && status.step_2_template_selected) ||
                (index === 3 && status.step_3_chart_materialized) ||
                (index === 4 && status.step_4_chart_finalized) ||
                (index === 5 && status.step_5_fiscal_periods_complete) ||
                (index === 6 && status.step_6_activated) ||
                (index === 7 && status.step_6_activated)
              );
              const isCurrent = index === currentStep;
              const isClickable = index <= currentStep &&
                !(status?.step_3_chart_materialized && index < 3) &&
                !(status?.step_6_activated && index < 7);

              return (
                <div
                  key={index}
                  className={`flex flex-col items-center flex-1 ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                  onClick={() => handleStepClick(index)}
                >
                  <div className={`
                    flex items-center justify-center w-10 h-10 rounded-full mb-2 transition-all
                    ${isComplete ? 'bg-emerald-600 text-white' : ''}
                    ${isCurrent && !isComplete ? 'bg-amber-500 text-white ring-4 ring-amber-200' : ''}
                    ${!isComplete && !isCurrent ? 'bg-gray-200 text-gray-400' : ''}
                  `}>
                    {isComplete ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <Circle className="h-5 w-5" />
                    )}
                  </div>
                  <span className={`text-xs text-center ${isCurrent ? 'font-semibold text-emerald-900' : 'text-gray-600'}`}>
                    {title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
          {currentStep === 0 && <Step0Welcome onNext={handleNext} status={status} />}
          {currentStep === 1 && (
            <Step1CompanyDetails
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 2 && (
            <Step2TemplateSelection
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 3 && (
            <Step3ChartMaterialization
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 4 && (
            <Step4AccountReview
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 5 && (
            <Step5FiscalPeriods
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 6 && (
            <Step6Activation
              companyId={companyId!}
              onNext={handleNext}
              onBack={handleBack}
              status={status}
            />
          )}
          {currentStep === 7 && <StepCompletion companyId={companyId!} status={status} />}
        </div>

        {/* Save & Exit */}
        {currentStep < 6 && (
          <div className="text-center text-sm text-gray-600">
            <p>Your progress is automatically saved. You can exit and resume anytime.</p>
            <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mt-2">
              Save & Exit
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingWizard;
