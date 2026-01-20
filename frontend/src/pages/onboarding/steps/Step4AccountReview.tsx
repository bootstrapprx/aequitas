/**
 * Step 4: Review & Customize Accounts
 *
 * ALLOWED ACTIONS:
 * - Rename accounts
 * - Disable non-mandatory accounts
 * - Add custom accounts
 *
 * FORBIDDEN ACTIONS:
 * - Change account type
 * - Delete mandatory accounts
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FileText, Check, Loader2, AlertCircle } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { api, ApiError } from '@/lib/api';

interface Step4AccountReviewProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

const Step4AccountReview: React.FC<Step4AccountReviewProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [finalized, setFinalized] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Fetch company accounts
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['company-accounts', companyId],
    queryFn: async () => {
      const response = await api.get(`/companies/${companyId}/chart`);
      return response as any;
    }
  });

  // Mutation to finalize
  const finalizeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/onboarding/${companyId}/customize-accounts`, {
        customizations: [],
        custom_accounts: [],
        finalized: true
      });
      return response as any;
    },
    onSuccess: () => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });
      onNext();
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof ApiError
        ? error.getUserMessage()
        : error instanceof Error
          ? error.message
          : 'Failed to finalize accounts.';
      setApiError(errorMessage);
    }
  });

  const handleFinalize = () => {
    if (finalized) {
      finalizeMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
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
          Review Your Accounts
        </h2>
        <p className="text-gray-600">
          Your chart of accounts has been created. Review and customize if needed.
        </p>
        <div className="mt-3 text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-3">
          These are the standard accounts created for your company. You can rename, disable, or add accounts before activation.
        </div>
      </div>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {/* Account Summary */}
      <AtheneumCard>
        <AtheneumCardHeader icon={<FileText className="h-5 w-5" />} embossed>
          Chart Summary
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-3xl font-bold text-emerald-800">{accounts?.length || 0}</p>
              <p className="text-sm text-gray-600">Total Accounts</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-blue-800">{accounts?.filter((a: any) => a.is_active).length || 0}</p>
              <p className="text-sm text-gray-600">Active</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-600">{accounts?.filter((a: any) => !a.is_active).length || 0}</p>
              <p className="text-sm text-gray-600">Disabled</p>
            </div>
          </div>

          <Alert className="mt-6 border-blue-200 bg-blue-50">
            <AlertDescription className="text-blue-900 text-sm">
              <strong>Note:</strong> You can add, rename, or disable accounts later in the Chart of Accounts module.
              For now, review and proceed to set up fiscal periods.
              <br />
              <span className="inline-block mt-2 text-gray-700">
                This account is required for correct accounting and cannot be removed.
              </span>
            </AlertDescription>
          </Alert>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Finalize Confirmation */}
      <AtheneumCard>
        <AtheneumCardContent>
          <div className="flex items-start space-x-3 py-4">
            <Checkbox
              id="finalize"
              checked={finalized}
              onCheckedChange={(checked) => setFinalized(checked as boolean)}
            />
            <label
              htmlFor="finalize"
              className="text-sm font-medium cursor-pointer"
            >
              I have reviewed my chart of accounts and am ready to proceed to fiscal period setup
            </label>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Action Buttons */}
      <div className="flex justify-between pt-4">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={finalizeMutation.isPending}
        >
          Back
        </Button>

        <Button
          onClick={handleFinalize}
          disabled={!finalized || finalizeMutation.isPending}
          className="shadow-gold"
        >
          {finalizeMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Finalizing...
            </>
          ) : (
            <>
              <Check className="mr-2 h-4 w-4" />
              Finalize & Continue
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
};

export default Step4AccountReview;
