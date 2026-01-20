/**
 * Step 6: Activate Accounting (Point of No Return)
 *
 * CRITICAL OPERATION:
 * - Requires checkbox confirmation
 * - Requires typed acknowledgment
 * - Shows summary of what's being activated
 * - Irreversible
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Zap, Check, Loader2, AlertCircle } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent, WaxSealBadge } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { api, ApiError } from '@/lib/api';
import { useCompany } from '@/contexts/CompanyContext';

interface Step6ActivationProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

const ACKNOWLEDGMENT_TEXT = "I understand that accounting will be activated";

const Step6Activation: React.FC<Step6ActivationProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [confirmed, setConfirmed] = useState(false);
  const [acknowledgment, setAcknowledgment] = useState('');
  const [jointStockAmount, setJointStockAmount] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const { refreshCompanies, setSelectedCompanyId } = useCompany();

  const isAcknowledgmentValid = acknowledgment.trim().toLowerCase() === ACKNOWLEDGMENT_TEXT.toLowerCase();

  // Mutation to activate
  const activateMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {
        confirmed: true,
        acknowledgment_text: acknowledgment,
      };
      if (jointStockAmount.trim() !== '') {
        payload.joint_stock_amount = Number(jointStockAmount);
      }
      const response = await api.post(`/onboarding/${companyId}/activate`, payload);
      return response;
    },
    onSuccess: async () => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });
      await refreshCompanies();
      setSelectedCompanyId(companyId);
      onNext();
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof ApiError
        ? error.getUserMessage()
        : error instanceof Error
          ? error.message
          : 'Failed to activate accounting.';
      setApiError(errorMessage);
    }
  });

  const handleActivate = () => {
    if (confirmed && isAcknowledgmentValid) {
      activateMutation.mutate();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center mb-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
          className="inline-block mb-4"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-amber-500 to-amber-700 rounded-full flex items-center justify-center mx-auto shadow-gold">
            <Zap className="h-10 w-10 text-white" />
          </div>
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2 embossed-gold">
          Activate Accounting
        </h2>
        <p className="text-gray-600">
          You're ready to activate accounting for {status?.company_name}.
        </p>
      </div>

      {/* Critical Warning */}
      <Alert className="border-amber-200 bg-amber-50">
        <AlertTriangle className="h-5 w-5 text-amber-600" />
        <AlertDescription className="text-amber-900 space-y-2">
          <div className="font-semibold">Before you activate</div>
          <ul className="list-disc list-inside text-sm space-y-1 text-amber-900">
            <li>Activating finalizes your accounting structure.</li>
            <li>Accounts and periods become protected.</li>
            <li>History cannot be rewritten.</li>
            <li>You can still add transactions and new accounts later.</li>
          </ul>
          <p className="text-sm pt-1">Take a moment to review before continuing.</p>
        </AlertDescription>
      </Alert>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {/* Setup Summary */}
      <AtheneumCard>
        <AtheneumCardHeader icon={<Shield className="h-5 w-5" />} embossed>
          Setup Summary
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded">
              <div className="flex items-center space-x-3">
                <Check className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium">Company Details</span>
              </div>
              <WaxSealBadge type="approved" size="sm" />
            </div>

            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded">
              <div className="flex items-center space-x-3">
                <Check className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium">Template Selected</span>
              </div>
              <WaxSealBadge type="approved" size="sm" />
            </div>

            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded">
              <div className="flex items-center space-x-3">
                <Check className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium">Chart of Accounts Created</span>
              </div>
              <WaxSealBadge type="approved" size="sm" />
            </div>

            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded">
              <div className="flex items-center space-x-3">
                <Check className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium">Accounts Reviewed</span>
              </div>
              <WaxSealBadge type="approved" size="sm" />
            </div>

            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded">
              <div className="flex items-center space-x-3">
                <Check className="h-5 w-5 text-emerald-600" />
                <span className="text-sm font-medium">Fiscal Periods Configured</span>
              </div>
              <WaxSealBadge type="approved" size="sm" />
            </div>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Initial Capital */}
      <AtheneumCard>
        <AtheneumCardHeader embossed>
          Joint-Stock (Initial Capital)
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <div className="space-y-2">
            <Label htmlFor="joint-stock-amount">
              Joint-Stock Value (Share Capital)
            </Label>
            <Input
              id="joint-stock-amount"
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
              placeholder="0.00"
              value={jointStockAmount}
              onChange={(e) => setJointStockAmount(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              If provided, Aequitas will record an opening entry in the first open period.
            </p>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* After Activation */}
      <AtheneumCard>
        <AtheneumCardHeader embossed>
          What Happens After Activation
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <ul className="space-y-3 text-sm text-gray-700">
            <li className="flex items-start space-x-3">
              <Check className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>Accounting rules are enforced automatically</span>
            </li>
            <li className="flex items-start space-x-3">
              <Check className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>Account properties lock after first transaction</span>
            </li>
            <li className="flex items-start space-x-3">
              <Check className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>You can still add accounts and periods later</span>
            </li>
            <li className="flex items-start space-x-3">
              <Check className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>Full audit trail begins tracking all changes</span>
            </li>
          </ul>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Confirmation */}
      <AtheneumCard>
        <AtheneumCardContent>
          <div className="space-y-4">
            {/* Checkbox Confirmation */}
            <div className="flex items-start space-x-3">
              <Checkbox
                id="confirm"
                checked={confirmed}
                onCheckedChange={(checked) => setConfirmed(checked as boolean)}
              />
              <label
                htmlFor="confirm"
                className="text-sm font-medium cursor-pointer leading-tight"
              >
                I understand that after activation, accounting rules will be enforced and history will be protected
              </label>
            </div>

            {/* Typed Acknowledgment */}
            <div>
              <Label htmlFor="acknowledgment">
                Type the following to confirm: <span className="font-mono text-emerald-700">{ACKNOWLEDGMENT_TEXT}</span>
              </Label>
              <Input
                id="acknowledgment"
                value={acknowledgment}
                onChange={(e) => setAcknowledgment(e.target.value)}
                placeholder="Type confirmation phrase..."
                className={`mt-2 ${acknowledgment && !isAcknowledgmentValid ? 'border-red-500' : ''} ${isAcknowledgmentValid ? 'border-emerald-500' : ''}`}
              />
              {acknowledgment && !isAcknowledgmentValid && (
                <p className="text-xs text-red-600 mt-1">Text does not match. Please type exactly as shown.</p>
              )}
              {isAcknowledgmentValid && (
                <p className="text-xs text-emerald-600 mt-1 flex items-center">
                  <Check className="h-3 w-3 mr-1" /> Confirmed
                </p>
              )}
            </div>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Action Buttons */}
      <div className="flex justify-between pt-4">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={activateMutation.isPending}
        >
          Back
        </Button>

        <Button
          onClick={handleActivate}
          disabled={!confirmed || !isAcknowledgmentValid || activateMutation.isPending}
          size="lg"
          className="bg-emerald-600 hover:bg-emerald-700 shadow-gold"
          title="Activation protects accounting history. It does not post any transactions."
        >
          {activateMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Activating...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-5 w-5" />
              Activate Accounting
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
};

export default Step6Activation;
