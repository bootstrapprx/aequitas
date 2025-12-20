
import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Building, Building2, Check, ArrowRight, Network } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';

interface Step5Props {
    companyId: string;
    onNext: () => void;
    onBack: () => void;
    status: any;
}

const Step5OrganizationScope: React.FC<Step5Props> = ({ companyId, onNext, onBack, status }) => {
    const [isStandalone, setIsStandalone] = useState<boolean>(true);

    // Hydrate logic
    useEffect(() => {
        const fetchScope = async () => {
            try {
                const response = await api.get<any>(`/companies/${companyId}`);
                if (response.is_standalone !== undefined) {
                    setIsStandalone(response.is_standalone);
                }
            } catch (error) {
                console.error("Failed to fetch company scope", error);
            }
        };
        fetchScope();
    }, [companyId]);


    const mutation = useMutation({
        mutationFn: async () => {
            await api.post(`/onboarding/${companyId}/step-5`, {
                is_standalone: isStandalone
            });
            // Auto-trigger chart materialization as Step 5 completion
            // Confirmed=true is required by backend schema
            await api.post(`/onboarding/${companyId}/materialize-chart`, {
                confirm_proceed: true
            });
        },
        onSuccess: () => {
            onNext();
        },
        onError: (error) => {
            console.log('Error saving scope or materializing chart', error);
            // Proceed if chart already exists (idempotency fallback)
            // But for now, let it fail so user sees error.
        }
    });

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-semibold tracking-tight">Organization Scope</h2>
                <p className="text-muted-foreground">
                    Is this a standalone entity or part of a corporate group?
                </p>
            </div>

            <div className="grid gap-6 max-w-2xl mx-auto">
                <div
                    className={cn(
                        "relative flex cursor-pointer rounded-lg border-2 p-4 shadow-sm focus:outline-none transition-all",
                        isStandalone ? "border-emerald-600 ring-1 ring-emerald-600" : "border-stone-200 hover:border-emerald-500/50"
                    )}
                    onClick={() => setIsStandalone(true)}
                >
                    <span className="flex flex-1">
                        <span className="flex flex-col">
                            <span className="block text-sm font-medium text-stone-900 flex items-center gap-2">
                                <Building className="h-5 w-5 text-emerald-600" />
                                Standalone Entity
                            </span>
                            <span className="mt-1 flex items-center text-sm text-stone-500">
                                This company operates independently. It has its own chart of accounts and does not consolidate automatically with others.
                            </span>
                        </span>
                    </span>
                    <Check className={cn("h-5 w-5 text-emerald-600", isStandalone ? "opacity-100" : "opacity-0")} />
                    <span
                        className={cn(
                            "pointer-events-none absolute -inset-px rounded-lg border-2",
                            isStandalone ? "border-emerald-600" : "border-transparent"
                        )}
                        aria-hidden="true"
                    />
                </div>

                <div
                    className={cn(
                        "relative flex cursor-pointer rounded-lg border-2 p-4 shadow-sm focus:outline-none transition-all",
                        !isStandalone ? "border-emerald-600 ring-1 ring-emerald-600" : "border-stone-200 hover:border-emerald-500/50"
                    )}
                    onClick={() => setIsStandalone(false)}
                >
                    <span className="flex flex-1">
                        <span className="flex flex-col">
                            <span className="block text-sm font-medium text-stone-900 flex items-center gap-2">
                                <Network className="h-5 w-5 text-blue-600" />
                                Part of a Group (Subsidiary)
                            </span>
                            <span className="mt-1 flex items-center text-sm text-stone-500">
                                This company is part of a larger group. It may share chart of accounts templates or require consolidation features.
                            </span>
                        </span>
                    </span>
                    <Check className={cn("h-5 w-5 text-emerald-600", !isStandalone ? "opacity-100" : "opacity-0")} />
                    <span
                        className={cn(
                            "pointer-events-none absolute -inset-px rounded-lg border-2",
                            !isStandalone ? "border-emerald-600" : "border-transparent"
                        )}
                        aria-hidden="true"
                    />
                </div>
            </div>

            <div className="flex justify-between pt-8 border-t">
                <Button variant="outline" onClick={onBack}>
                    Back
                </Button>
                <Button
                    onClick={() => mutation.mutate()}
                    disabled={mutation.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                    {mutation.isPending ? 'Saving...' : 'Continue'}
                    <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
            </div>
        </div>
    );
};

export default Step5OrganizationScope;
