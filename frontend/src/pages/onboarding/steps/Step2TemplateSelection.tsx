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
import { FileText, AlertTriangle, Check, Loader2, Shield } from 'lucide-react';

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
        <AnimatePresence>
          {templates?.map((template, index) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <AtheneumCard
                hover
                className={`cursor-pointer transition-all ${selectedTemplate?.id === template.id
                  ? 'ring-2 ring-emerald-500 shadow-lg'
                  : ''
                  }`}
                onClick={() => handleTemplateClick(template)}
              >
                <AtheneumCardHeader
                  icon={<FileText className="h-5 w-5 text-emerald-600" />}
                  embossed
                >
                  <div className="flex items-center justify-between w-full">
                    <span>{template.name}</span>
                    {template.is_active && (
                      <WaxSealBadge type="approved" size="sm" />
                    )}
                  </div>
                </AtheneumCardHeader>
                <AtheneumCardContent>
                  <div className="space-y-3">
                    {/* Jurisdiction */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Jurisdiction</p>
                      <p className="text-sm text-gray-900">{template.jurisdiction}</p>
                    </div>

                    {/* Version */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Version</p>
                      <p className="text-sm text-gray-900">{template.version}</p>
                    </div>

                    {/* Description */}
                    {template.description && (
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase">Description</p>
                        <p className="text-sm text-gray-700">{template.description}</p>
                      </div>
                    )}

                    {/* Account Count */}
                    {template.account_count && (
                      <div className="pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-600">
                          <strong>{template.account_count}</strong> accounts included
                        </p>
                      </div>
                    )}

                    {/* Select Button */}
                    <Button
                      className="w-full mt-4 shadow-gold"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTemplateClick(template);
                      }}
                    >
                      Use This Template
                    </Button>
                  </div>
                </AtheneumCardContent>
              </AtheneumCard>
            </motion.div>
          ))}
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
              <p>
                You are about to select <strong>{selectedTemplate?.name}</strong>.
              </p>

              <Alert className="border-amber-300 bg-amber-50">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-900 text-sm">
                  <strong>This choice cannot be changed</strong> after your chart of accounts is created.
                  The template will define your account structure permanently.
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <p className="text-sm font-semibold">This template includes:</p>
                <ul className="text-sm space-y-1 pl-4">
                  <li>✓ Jurisdiction: {selectedTemplate?.jurisdiction}</li>
                  <li>✓ Version: {selectedTemplate?.version}</li>
                  {selectedTemplate?.account_count && (
                    <li>✓ {selectedTemplate.account_count} pre-configured accounts</li>
                  )}
                </ul>
              </div>

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
