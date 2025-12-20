/**
 * Step 1: Company Details
 *
 * Fields:
 * - Legal name (required)
 * - Trade name / DBA (optional)
 * - Country (required, ISO 3166-1 alpha-2)
 * - Currency (required, ISO 4217)
 * - Timezone (required, IANA)
 * - Email, Phone (optional)
 *
 * UX Rules:
 * - Currency/country lock after template selection
 * - All changes saved automatically
 * - Form validation before proceeding
 */

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Building2, AlertCircle, Loader2 } from 'lucide-react';

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
import { api } from '@/lib/api';

interface Step1CompanyDetailsProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

interface CompanyDetailsForm {
  name: string;
  trade_name?: string;
  country: string;
  currency: string;
  timezone: string;
  email?: string;
  phone?: string;
}

const COUNTRIES = [
  { code: 'US', name: 'United States' },
  { code: 'CA', name: 'Canada' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'AU', name: 'Australia' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'IE', name: 'Ireland' },
];

const CURRENCIES = [
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' },
  { code: 'GBP', name: 'British Pound', symbol: '£' },
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'AUD', name: 'Australian Dollar', symbol: 'A$' },
  { code: 'NZD', name: 'New Zealand Dollar', symbol: 'NZ$' },
];

const TIMEZONES = [
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'America/Toronto', label: 'Toronto' },
  { value: 'America/Vancouver', label: 'Vancouver' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Dublin', label: 'Dublin' },
  { value: 'Australia/Sydney', label: 'Sydney' },
  { value: 'Pacific/Auckland', label: 'Auckland' },
];

const Step1CompanyDetails: React.FC<Step1CompanyDetailsProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [apiError, setApiError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors }, setValue, watch } = useForm<CompanyDetailsForm>({
    defaultValues: {
      name: '',
      trade_name: '',
      country: 'US',
      currency: 'USD',
      timezone: 'America/New_York',
      email: '',
      phone: ''
    }
  });

  const selectedCountry = watch('country');
  const selectedCurrency = watch('currency');
  const selectedTimezone = watch('timezone');

  // Check if fields are locked (after template selection)
  // Lock if template has been selected (Step 3 completed)
  const isLocked = status?.step_3_template_selected;

  // Mutation to save company details
  const saveMutation = useMutation({
    mutationFn: async (data: CompanyDetailsForm) => {
      const response = await api.post(`/onboarding/${companyId}/company-details`, data);
      return response as any;
    },
    onSuccess: (data) => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });
      onNext();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to save company details. Please check your inputs.';
      setApiError(errorMessage);
    }
  });

  const onSubmit = (data: CompanyDetailsForm) => {
    saveMutation.mutate(data);
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
          Tell Us About Your Company
        </h2>
        <p className="text-gray-600">
          This information helps us configure the right accounting standards and templates.
        </p>
      </div>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {/* Locked Warning */}
      {isLocked && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Currency and country are locked after template selection. Other fields can still be edited.
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Company Identity */}
        <AtheneumCard>
          <AtheneumCardHeader icon={<Building2 className="h-5 w-5" />} embossed>
            Company Identity
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <div className="space-y-4">
              {/* Legal Name */}
              <div>
                <Label htmlFor="name" className="required">Legal Company Name</Label>
                <Input
                  id="name"
                  {...register('name', {
                    required: 'Legal name is required',
                    minLength: { value: 2, message: 'Name must be at least 2 characters' }
                  })}
                  placeholder="Acme Corporation Inc."
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>
                )}
              </div>

              {/* Trade Name */}
              <div>
                <Label htmlFor="trade_name">Trade Name / DBA (Optional)</Label>
                <Input
                  id="trade_name"
                  {...register('trade_name')}
                  placeholder="Acme Services"
                />
                <p className="text-xs text-gray-500 mt-1">
                  The name you use for business operations, if different from legal name
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>

        {/* Jurisdiction & Currency */}
        <AtheneumCard>
          <AtheneumCardHeader embossed>
            Jurisdiction & Currency
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Country */}
              <div>
                <Label htmlFor="country" className="required">Country</Label>
                <Select
                  value={selectedCountry}
                  onValueChange={(value) => setValue('country', value)}
                  disabled={isLocked}
                >
                  <SelectTrigger className={isLocked ? 'opacity-60' : ''}>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRIES.map((country) => (
                      <SelectItem key={country.code} value={country.code}>
                        {country.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  {isLocked ? '🔒 Locked after template selection' : 'Determines accounting standards'}
                </p>
              </div>

              {/* Currency */}
              <div>
                <Label htmlFor="currency" className="required">Default Currency</Label>
                <Select
                  value={selectedCurrency}
                  onValueChange={(value) => setValue('currency', value)}
                  disabled={isLocked}
                >
                  <SelectTrigger className={isLocked ? 'opacity-60' : ''}>
                    <SelectValue placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map((currency) => (
                      <SelectItem key={currency.code} value={currency.code}>
                        {currency.symbol} {currency.name} ({currency.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  {isLocked ? '🔒 Cannot be changed later' : 'All transactions will use this currency'}
                </p>
              </div>

              {/* Timezone */}
              <div className="md:col-span-2">
                <Label htmlFor="timezone" className="required">Timezone</Label>
                <Select
                  value={selectedTimezone}
                  onValueChange={(value) => setValue('timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz.value} value={tz.value}>
                        {tz.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  Used for transaction timestamps and reporting
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>

        {/* Contact Information (Optional) */}
        <AtheneumCard>
          <AtheneumCardHeader embossed>
            Contact Information (Optional)
          </AtheneumCardHeader>
          <AtheneumCardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email', {
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: 'Invalid email format'
                    }
                  })}
                  placeholder="contact@acme.com"
                  className={errors.email ? 'border-red-500' : ''}
                />
                {errors.email && (
                  <p className="text-xs text-red-600 mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  {...register('phone')}
                  placeholder="+1 (555) 123-4567"
                />
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
          >
            Back
          </Button>

          <Button
            type="submit"
            className="shadow-gold"
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Continue'
            )}
          </Button>
        </div>
      </form>
    </motion.div>
  );
};

export default Step1CompanyDetails;
