/**
 * Step 2: Choose Accounting Template
 *
 * CRITICAL UX MOMENT:
 * - This choice cannot be changed after accounts are created
 * - Requires mandatory confirmation modal
 * - Clear warning banner
 *
 * Template cards show:
 * - Jurisdiction
 * - Business type
 * - Number of accounts
 * - Compliance notes
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, AlertTriangle, Check, Loader2, Shield, Book, BookOpen, CheckCircle2, XCircle } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent, WaxSealBadge } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { api } from '@/lib/api';

interface Step2TemplateSelectionProps {
  companyId: string;
  onNext: () => void;
  onBack: () => void;
  status: any;
}

interface ChartTemplate {
  id: string;
  name: string;
  jurisdiction: string;
  version: string;
  description: string;
  is_active: boolean;
  account_count?: number;
}

// Template metadata for enhanced display
const TEMPLATE_DISPLAY_INFO: Record<string, {
  title: string;
  subtitle: string;
  badge: string;
  description: string;
  features: { label: string; supported: boolean }[];
  footerHint?: string;
  buttonText: string;
  icon: 'standard' | 'simplified' | 'disabled';
}> = {
  'US GAAP Standard': {
    title: 'US GAAP — Standard',
    subtitle: 'United States · Full Canonical Kernel',
    badge: '≈ 150 Accounts · Complete GAAP Structure',
    description: 'A complete, canon-aligned Chart of Accounts following US GAAP. Includes all core assets, liabilities, equity, revenue, expenses, taxes, and closing accounts required for full double-entry bookkeeping, period closing, and financial reporting.\n\nDesigned for companies that need accuracy, auditability, and long-term scalability.',
    features: [
      { label: 'Journaling', supported: true },
      { label: 'Period Closing', supported: true },
      { label: 'Reporting', supported: true },
      { label: 'Account Detail', supported: true },
      { label: 'Future Extensions', supported: true },
    ],
    footerHint: 'Includes retained earnings & system closing accounts',
    buttonText: 'Use Standard Kernel',
    icon: 'standard',
  },
  'US GAAP Simplified': {
    title: 'US GAAP — Simplified',
    subtitle: 'United States · Pruned Canonical Kernel',
    badge: '≈ 50 Accounts · Simplified but Complete',
    description: 'A simplified version of the US GAAP kernel with collapsed categories. Maintains full accounting integrity while reducing chart complexity.\n\nBest for small teams and straightforward operations that still require correct journaling, closing, and reporting.',
    features: [
      { label: 'Journaling', supported: true },
      { label: 'Period Closing', supported: true },
      { label: 'Reporting', supported: true },
      { label: 'Account Detail', supported: false },
      { label: 'Future Extensions', supported: false },
    ],
    footerHint: 'No loss of accounting integrity',
    buttonText: 'Use Simplified Kernel',
    icon: 'simplified',
  },
  'IFRS Standard': {
    title: 'IFRS — Standard',
    subtitle: 'International · Mapping Pending',
    badge: 'Unavailable',
    description: 'IFRS support requires a regulatory mapping layer that is not yet implemented. This template is intentionally disabled to prevent incomplete or misleading accounting setups.\n\nComing after master chart regulatory mapping is introduced.',
    features: [],
    buttonText: 'Disabled',
    icon: 'disabled',
  },
};

const Step2TemplateSelection: React.FC<Step2TemplateSelectionProps> = ({
  companyId,
  onNext,
  onBack,
  status
}) => {
  const queryClient = useQueryClient();
  const [selectedTemplate, setSelectedTemplate] = useState<ChartTemplate | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmationChecked, setConfirmationChecked] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Fetch available templates
  const { data: templates, isLoading } = useQuery<ChartTemplate[]>({
    queryKey: ['chart-templates'],
    queryFn: async () => {
      const response = await api.get('/templates');
      return response as any;
    }
  });

  // Mutation to select template
  const selectMutation = useMutation({
    mutationFn: async (templateId: string) => {
      const response = await api.post(`/onboarding/${companyId}/select-template`, {
        template_id: templateId,
        confirmed: true
      });
      return response as any;
    },
    onSuccess: () => {
      setApiError(null);
      setShowConfirmModal(false);
      queryClient.invalidateQueries({ queryKey: ['onboarding-status', companyId] });
      onNext();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to select template. Please try again.';
      setApiError(errorMessage);
    }
  });

  const handleTemplateClick = (template: ChartTemplate) => {
    // Prevent selection of disabled templates
    if (!template.is_active) {
      return;
    }
    setSelectedTemplate(template);
    setShowConfirmModal(true);
    setConfirmationChecked(false);
  };

  const handleConfirm = () => {
    if (selectedTemplate && confirmationChecked) {
      selectMutation.mutate(selectedTemplate.id);
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
          Choose Your Accounting Template
        </h2>
        <p className="text-gray-600">
          Select the template that matches your jurisdiction and business type.
        </p>
      </div>

      {/* Warning Banner */}
      <Alert className="border-amber-300 bg-amber-50">
        <AlertTriangle className="h-5 w-5 text-amber-600" />
        <AlertDescription className="text-amber-900">
          <strong>Important:</strong> This choice cannot be changed after your chart of accounts is created.
          Choose carefully based on your jurisdiction and compliance requirements.
        </AlertDescription>
      </Alert>

      {/* Error Alert */}
      {apiError && (
        <Alert variant="destructive">
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      )}

      {/* Template Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2 text-sm text-gray-600">
          All templates create a complete, working accounting system. You can customize accounts later.
        </div>
        <AnimatePresence>
          {templates?.map((template, index) => {
            const displayInfo = TEMPLATE_DISPLAY_INFO[template.name];
            const isDisabled = !template.is_active;

            // Icon selection
            const IconComponent = displayInfo?.icon === 'standard'
              ? Book
              : displayInfo?.icon === 'simplified'
              ? BookOpen
              : FileText;

            return (
              <motion.div
                key={template.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <AtheneumCard
                  hover={!isDisabled}
                  className={`transition-all ${
                    isDisabled
                      ? 'opacity-60 cursor-not-allowed bg-gray-50'
                      : 'cursor-pointer hover:shadow-xl'
                  } ${
                    selectedTemplate?.id === template.id
                      ? 'ring-2 ring-emerald-500 shadow-lg'
                      : 'shadow-md'
                  }`}
                  onClick={() => handleTemplateClick(template)}
                >
                  <AtheneumCardHeader
                    icon={<IconComponent className={`h-5 w-5 ${isDisabled ? 'text-gray-400' : 'text-emerald-600'}`} />}
                    embossed={!isDisabled}
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex-1">
                        <h3 className={`text-lg font-bold ${isDisabled ? 'text-gray-600' : 'text-gray-900'}`}>
                          {displayInfo?.title || template.name}
                        </h3>
                        <p className="text-xs text-gray-500 font-medium mt-0.5">
                          {displayInfo?.subtitle || `${template.jurisdiction} · ${template.version}`}
                        </p>
                      </div>
                      {!isDisabled && (
                        <WaxSealBadge type="approved" size="sm" />
                      )}
                    </div>
                  </AtheneumCardHeader>

                  <AtheneumCardContent>
                    <div className="space-y-4">
                      {/* Kernel Size Badge */}
                      <div className={`inline-flex items-center px-3 py-1.5 rounded-md font-semibold text-sm ${
                        isDisabled
                          ? 'bg-gray-200 text-gray-600'
                          : 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                      }`}>
                        {displayInfo?.badge || `${template.account_count || 0} accounts`}
                      </div>

                      {/* Description */}
                      <div className="space-y-2">
                        <p className={`text-sm leading-relaxed whitespace-pre-line ${
                          isDisabled ? 'text-gray-600' : 'text-gray-700'
                        }`}>
                          {displayInfo?.description || template.description}
                        </p>
                        {template.name === 'US GAAP Simplified' && (
                          <p className="text-xs text-gray-500 mt-2">
                            Simplified reduces chart complexity without removing required accounting structure.
                          </p>
                        )}
                        {template.name === 'IFRS Standard' && (
                          <p className="text-xs text-gray-500 mt-2">
                            IFRS requires a regulatory mapping layer that is not yet implemented.
                          </p>
                        )}
                      </div>

                      {/* Feature Comparison (for active templates only) */}
                      {!isDisabled && displayInfo?.features && displayInfo.features.length > 0 && (
                        <div className="pt-3 border-t border-gray-200">
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {displayInfo.features.map((feature, idx) => (
                              <div key={idx} className="flex items-center space-x-1.5">
                                {feature.supported ? (
                                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                                ) : (
                                  <XCircle className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
                                )}
                                <span className={feature.supported ? 'text-gray-700' : 'text-gray-500'}>
                                  {feature.label}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Footer Hint */}
                      {!isDisabled && displayInfo?.footerHint && (
                        <div className="pt-2">
                          <p className="text-xs text-gray-500 italic">
                            {displayInfo.footerHint}
                          </p>
                        </div>
                      )}

                      {/* Select Button */}
                      <Button
                        className={`w-full mt-4 ${
                          isDisabled
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed hover:bg-gray-300'
                            : 'shadow-gold'
                        }`}
                        disabled={isDisabled}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTemplateClick(template);
                        }}
                      >
                        {displayInfo?.buttonText || 'Use This Template'}
                      </Button>
                    </div>
                  </AtheneumCardContent>
                </AtheneumCard>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* No Templates Available */}
      {templates && templates.length === 0 && (
        <Alert>
          <AlertDescription>
            No templates are currently available. Please contact support to request a template for your jurisdiction.
          </AlertDescription>
        </Alert>
      )}

      {/* Confirmation Modal */}
      <Dialog open={showConfirmModal} onOpenChange={setShowConfirmModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-amber-600" />
              <span>Confirm Template Selection</span>
            </DialogTitle>
            <DialogDescription>
              Please confirm your template selection.
            </DialogDescription>


            <div className="space-y-4 pt-4">
              {selectedTemplate && (() => {
                const displayInfo = TEMPLATE_DISPLAY_INFO[selectedTemplate.name];
                return (
                  <>
                    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                      <h4 className="font-bold text-emerald-900 mb-1">
                        {displayInfo?.title || selectedTemplate.name}
                      </h4>
                      <p className="text-sm text-emerald-700">
                        {displayInfo?.subtitle || `${selectedTemplate.jurisdiction} · ${selectedTemplate.version}`}
                      </p>
                      <div className="mt-2 inline-flex items-center px-2 py-1 bg-emerald-100 rounded text-xs font-semibold text-emerald-900">
                        {displayInfo?.badge || `${selectedTemplate.account_count || 0} accounts`}
                      </div>
                    </div>

                    <Alert className="border-amber-300 bg-amber-50">
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                      <AlertDescription className="text-amber-900 text-sm">
                        <strong>This choice cannot be changed</strong> after your chart of accounts is created.
                        The template will define your account structure permanently.
                      </AlertDescription>
                    </Alert>

                    {displayInfo?.features && displayInfo.features.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-semibold">This template provides:</p>
                        <div className="grid grid-cols-2 gap-2">
                          {displayInfo.features.map((feature, idx) => (
                            <div key={idx} className="flex items-center space-x-1.5 text-sm">
                              {feature.supported ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                              ) : (
                                <XCircle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                              )}
                              <span className={feature.supported ? 'text-gray-700' : 'text-gray-500'}>
                                {feature.label}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-start space-x-2 pt-4">
                      <Checkbox
                        id="confirm"
                        checked={confirmationChecked}
                        onCheckedChange={(checked) => setConfirmationChecked(checked as boolean)}
                      />
                      <label
                        htmlFor="confirm"
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                      >
                        I understand that this choice cannot be changed after chart creation
                      </label>
                    </div>
                  </>
                );
              })()}
            </div>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowConfirmModal(false)}
              disabled={selectMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={!confirmationChecked || selectMutation.isPending}
              className="shadow-gold"
            >
              {selectMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Selecting...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Confirm Selection
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Action Buttons */}
      <div className="flex justify-between pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={selectMutation.isPending}
        >
          Back
        </Button>

        <div className="text-sm text-gray-500 self-center">
          Select a template to continue
        </div>
      </div>
    </motion.div >
  );
};

export default Step2TemplateSelection;
