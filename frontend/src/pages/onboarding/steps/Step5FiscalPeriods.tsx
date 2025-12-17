/**
 * Step 5: Set Fiscal Periods
 *
 * Fields:
 * - Fiscal year start date
 * - Period structure (monthly/quarterly)
 * - First open period
 *
 * UX Constraints:
 * - Prevent overlapping periods
 * - At least one OPEN period required
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Calendar, Check, Loader2, AlertCircle, Hourglass } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import api from '@/lib/api';

interface Step5FiscalPeriodsProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

interface FiscalPeriodForm {
  fiscal_year_start: string;
  period_count: number;
}

const Step5FiscalPeriods: React.FC<Step5FiscalPeriodsProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [apiError, setApiError] = useState<string | null>(null);
  const [fiscalYearStart, setFiscalYearStart] = useState('01-01');

  const { register, handleSubmit, formState: { errors } } = useForm<FiscalPeriodForm>({
    defaultValues: {
      fiscal_year_start: '01-01',
      period_count: 12
    }
  });

  // Mutation to create fiscal periods
  const createMutation = useMutation({
    mutationFn: async (data: FiscalPeriodForm) => {
      // Generate periods based on fiscal year start
      const currentYear = new Date().getFullYear();
      const periods = [];

      for (let i = 0; i < data.period_count; i++) {
        const startMonth = parseInt(data.fiscal_year_start.split('-')[0]);
        const monthIndex = (startMonth - 1 + i) % 12;
        const year = currentYear + Math.floor((startMonth - 1 + i) / 12);

        const startDate = new Date(year, monthIndex, 1);
        const endDate = new Date(year, monthIndex + 1, 0);

        periods.push({
          name: `Period ${i + 1} - ${startDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`,
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          period_type: 'MONTH',
          is_open: i === 0 // First period is open
        });
      }

      const response = await api.post(`/onboarding/${companyId}/fiscal-periods`, {
        fiscal_year_start: data.fiscal_year_start,
        periods
      });
      return response.data;
    },
    onSuccess: () => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });
      onNext();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to create fiscal periods.';
      setApiError(errorMessage);
    }
  });

  const onSubmit = (data: FiscalPeriodForm) => {
    createMutation.mutate(data);
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
        <h2 className="text-2xl font-bold text-gray-900 mb-2 embossed-gold">
          Define Fiscal Periods
        </h2>
        <p className="text-gray-600">
          Set up your fiscal year and accounting periods.
        </p>
      </div>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Fiscal Year Setup */}
        <AtheneumCard>
          <AtheneumCardHeader icon={<Calendar className="h-5 w-5" />} embossed>
            Fiscal Year Configuration
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <div className="space-y-4">
              {/* Fiscal Year Start */}
              <div>
                <Label htmlFor="fiscal_year_start" className="required">
                  Fiscal Year Start Date
                </Label>
                <Select
                  value={fiscalYearStart}
                  onValueChange={setFiscalYearStart}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select start month" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="01-01">January 1 (Calendar Year)</SelectItem>
                    <SelectItem value="04-01">April 1</SelectItem>
                    <SelectItem value="07-01">July 1</SelectItem>
                    <SelectItem value="10-01">October 1</SelectItem>
                  </SelectContent>
                </Select>
                <input type="hidden" {...register('fiscal_year_start')} value={fiscalYearStart} />
                <p className="text-xs text-gray-500 mt-1">
                  When does your fiscal year begin?
                </p>
              </div>

              {/* Period Count */}
              <div>
                <Label htmlFor="period_count" className="required">
                  Number of Periods
                </Label>
                <Select defaultValue="12">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="12">12 Monthly Periods</SelectItem>
                    <SelectItem value="4">4 Quarterly Periods</SelectItem>
                    <SelectItem value="1">1 Annual Period</SelectItem>
                  </SelectContent>
                </Select>
                <input type="hidden" {...register('period_count')} value={12} />
              </div>
            </div>

            <Alert className="mt-6 border-blue-200 bg-blue-50">
              <AlertDescription className="text-blue-900 text-sm">
                <strong>Note:</strong> The first period will be set as OPEN. You can manage period status later in the Fiscal Periods module.
              </AlertDescription>
            </Alert>
          </AtheneumCardContent>
        </AtheneumCard>

        {/* Timeline Preview */}
        <AtheneumCard>
          <AtheneumCardHeader icon={<Hourglass className="h-5 w-5" />} embossed>
            Period Preview
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-emerald-50 rounded border-l-4 border-emerald-600">
                <span className="text-sm font-semibold text-emerald-900">Period 1 (OPEN)</span>
                <span className="text-xs text-emerald-700">Current period</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">Period 2 (CLOSED)</span>
                <span className="text-xs text-gray-500">Future period</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">Period 3 (CLOSED)</span>
                <span className="text-xs text-gray-500">Future period</span>
              </div>
              <div className="text-center text-xs text-gray-400 pt-2">
                ... and more periods
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={onBack}
            disabled={createMutation.isPending}
          >
            Back
          </Button>

          <Button
            type="submit"
            className="shadow-gold"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Periods...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Create Periods
              </>
            )}
          </Button>
        </div>
      </form>
    </motion.div>
  );
};

export default Step5FiscalPeriods;
