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
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import { Feather, CheckCircle2, Circle, Lock } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

import { PageHeader } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { api } from '@/lib/api';

// Step components
import Step0Welcome from './steps/Step0Welcome';
import Step1CompanyDetails from './steps/Step1CompanyDetails';
import Step2CompanyType from './steps/Step2CompanyType';
import Step3TemplateSelection from './steps/Step2TemplateSelection'; // Alias for legacy file
import Step4ModuleSelection from './steps/Step4ModuleSelection';
import Step5OrganizationScope from './steps/Step5OrganizationScope';
import Step6AccountReview from './steps/Step4AccountReview'; // Alias
import Step7FiscalPeriods from './steps/Step5FiscalPeriods'; // Alias
import Step8Activation from './steps/Step6Activation'; // Alias
import StepCompletion from './steps/StepCompletion';
import { DexterSidebar } from '@/components/dexter/DexterSidebar';
import { DexterProvider } from '@/contexts/DexterContext';


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
  trade_name?: string | null;
  country?: string | null;
  currency?: string | null;
  timezone?: string | null;
  email?: string | null;
  phone?: string | null;
  legal_nature?: string | null;
  economic_activity?: string | null;
  is_standalone?: boolean | null;
  kernel_version?: string | null;
  kernel_layer?: 'L0' | 'L1' | 'L2' | null;
  step_0_welcome_seen: boolean;
  step_1_company_details_complete: boolean;
  step_2_company_type_complete: boolean;
  step_3_template_selected: boolean;
  step_4_modules_complete: boolean;
  step_5_scope_complete: boolean;
  step_6_account_review_complete: boolean;
  step_7_fiscal_periods_complete: boolean;
  step_8_activated: boolean;
}

const STEP_TITLES = [
  'Welcome',
  'Company Details',
  'Type & Activity',
  'Choose Template',
  'Modules',
  'Scope',
  'Review Accounts',
  'Fiscal Periods',
  'Activate',
  'Complete'
];

const STEP_KEYS = [
  'welcome',
  'company_details',
  'company_type',
  'template_selection',
  'modules',
  'scope',
  'account_review',
  'fiscal_periods',
  'activation',
  'completion'
];


const OnboardingWizard: React.FC = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { logout } = useAuth();

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
    refetchInterval: 10000,
  });

  // Acquire session lock on mount
  const lockMutation = useMutation({
    mutationFn: async (vars: { force?: boolean } = {}) => {
      const response = await api.post(`/onboarding/lock/${companyId}`, {
        session_id: sessionId,
        force: vars.force || false
      });
      return response as any;
    },
    onSuccess: (data) => {
      if (!data.locked) {
        setLockError('One active session at a time. Continuing will invalidate your other session.');
      } else {
        setLockError(null);
      }
    }
  });

  // Release session lock on unmount
  useEffect(() => {
    lockMutation.mutate();

    return () => {
      // Release lock on unmount
      api.delete(`/onboarding/lock/${companyId}`, {
        body: { session_id: sessionId }
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
      if (status.step_8_activated) {
        setCurrentStep(9); // Completion screen
      }
    }
  }, [status]);

  // Handle step navigation
  const handleNext = () => {
    setCurrentStep(prev => Math.min(prev + 1, 9));
    refetch();
  };

  const handleBack = () => {
    // Prevent going back after irreversible steps
    if (status) {
      if (status.onboarding_status === 'ACTIVE') {
        return; // No going back after activation
      }
      // If chart materialized (Step 3 complete?), cannot go back to Template (Step 3) or Type (2)?
      // Actually materialization happens after Step 3. 
      // If step_3_template_selected is true (implies materialization in old logic? No, template selected is prep for materialization).
      // Let's use status flags.
      // If CHART_READY (Step 6? No, Step 3+), cannot go back to Template.
      if (status.onboarding_status === 'CHART_READY' && currentStep <= 3) {
        return;
      }
    }
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleStepClick = (stepIndex: number) => {
    if (!status) return;
    if (stepIndex > currentStep) return;

    // Irreversible checks
    if (status.onboarding_status === 'CHART_READY' && stepIndex < 3) return;
    if (status.step_8_activated && stepIndex < 9) return;

    setCurrentStep(stepIndex);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading onboarding wizard...</p>
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
        <Button onClick={() => lockMutation.mutate({ force: true })} className="mt-4">
          Take Over Session
        </Button>
      </div>
    );
  }

  const progress = ((currentStep + 1) / 10) * 100;

  return (
    <DexterProvider>
      <div className="relative min-h-screen bg-background text-foreground transition-colors duration-300">
        <div className="fixed top-6 right-6 z-[100] bg-white/50 dark:bg-slate-900/50 backdrop-blur-md rounded-full p-2 shadow-lg border border-stone-200 dark:border-slate-700">
          <ThemeToggle />
        </div>
        <PageHeader
          title="Company Onboarding"
          subtitle={`Set up accounting for ${status?.company_name || 'your company'}`}
          icon={Feather}
        />

        <div className="flex flex-1 h-[calc(100vh-80px)] overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-5xl mx-auto px-10 py-6">

              <div className="mb-8">
                <Progress value={progress} className="h-2 mb-4" />
                <div className="flex justify-between items-start">
                  {STEP_TITLES.map((title, index) => {
                    // Map index to status flag
                    let isComplete = false;
                    if (status) {
                      if (index === 0) isComplete = status.step_0_welcome_seen;
                      if (index === 1) isComplete = status.step_1_company_details_complete;
                      if (index === 2) isComplete = status.step_2_company_type_complete;
                      if (index === 3) isComplete = status.step_3_template_selected;
                      if (index === 4) isComplete = status.step_4_modules_complete;
                      if (index === 5) isComplete = status.step_5_scope_complete;
                      if (index === 6) isComplete = status.step_6_account_review_complete;
                      if (index === 7) isComplete = status.step_7_fiscal_periods_complete;
                      if (index === 8) isComplete = status.step_8_activated;
                      if (index === 9) isComplete = status.step_8_activated;
                    }

                    const isCurrent = index === currentStep;
                    // Clickable logic: Can execute if <= currentStep AND not blocked by irreversibility
                    const isClickable = index <= currentStep &&
                      !(status?.onboarding_status === 'CHART_READY' && index < 3) &&
                      !(status?.step_8_activated && index < 9);

                    return (
                      <div
                        key={index}
                        className={`flex flex-col items-center flex-1 ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                        onClick={() => isClickable && handleStepClick(index)}
                      >
                        <div className={`
                    flex items-center justify-center w-10 h-10 rounded-full mb-2 transition-all
                    ${isComplete ? 'bg-emerald-600 text-white' : ''}
                    ${isCurrent && !isComplete ? 'bg-amber-500 text-white ring-4 ring-amber-200 dark:ring-amber-900' : ''}
                    ${!isComplete && !isCurrent ? 'bg-gray-200 text-gray-400 dark:bg-slate-800 dark:text-gray-500' : ''}
                  `}>
                          {isComplete ? (
                            <CheckCircle2 className="h-5 w-5" />
                          ) : (
                            <Circle className="h-5 w-5" />
                          )}
                        </div>
                        <span className={`text-[10px] text-center ${isCurrent ? 'font-semibold text-emerald-900 dark:text-emerald-400' : 'text-gray-600 dark:text-gray-400'}`}>
                          {title}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-card text-card-foreground border border-border rounded-lg shadow-xl p-8 mb-6 transition-all duration-300">
                {currentStep === 0 && <Step0Welcome companyId={companyId!} onNext={handleNext} status={status} />}
                {currentStep === 1 && (
                  <Step1CompanyDetails
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 2 && (
                  <Step2CompanyType
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 3 && (
                  <Step3TemplateSelection
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 4 && (
                  <Step4ModuleSelection
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 5 && (
                  <Step5OrganizationScope
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 6 && (
                  <Step6AccountReview
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 7 && (
                  <Step7FiscalPeriods
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 8 && (
                  <Step8Activation
                    companyId={companyId!}
                    onNext={handleNext}
                    onBack={handleBack}
                    status={status}
                  />
                )}
                {currentStep === 9 && <StepCompletion companyId={companyId!} status={status} />}
              </div>

              {/* Save & Exit */}
              {currentStep < 6 && (
                <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                  <p>Your progress is automatically saved. You can exit and resume anytime.</p>
                  <Button variant="ghost" onClick={() => { logout(); navigate('/login'); }} className="mt-2 text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300">
                    Save & Logout
                  </Button>
                </div>
              )}
            </div>
          </main>

          <aside className="hidden xl:block w-80 h-full border-l bg-muted/10">
            <DexterSidebar
              step={STEP_KEYS[currentStep]}
              context={{ companyId }}
            />
          </aside>
        </div>
      </div>
    </DexterProvider>
  );
};


export default OnboardingWizard;
