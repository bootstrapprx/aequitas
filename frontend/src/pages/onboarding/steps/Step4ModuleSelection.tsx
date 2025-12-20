
import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Check, Package, Calculator, FileText, Briefcase, Truck, Users, ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils'; // Assuming standard cn utility exists

interface Step4Props {
    companyId: string;
    onNext: () => void;
    onBack: () => void;
    status: any;
}

const MODULES = [
    {
        id: 'ACCOUNTING',
        name: 'Accounting',
        description: 'Core general ledger, journal entries, and financial reporting.',
        icon: Calculator,
        required: true
    },
    {
        id: 'FISCAL',
        name: 'Fiscal Management',
        description: 'Tax calculation, fiscal periods, and compliance reporting.',
        icon: FileText,
        required: false
    },
    {
        id: 'INVOICING',
        name: 'Invoicing',
        description: 'Create and send invoices, track payments, and manage receivables.',
        icon: FileText, // Reusing icon for now
        required: false
    },
    {
        id: 'CONTRACTS',
        name: 'Contracts',
        description: 'Manage vendor and customer contracts, recurring billing, and terms.',
        icon: Briefcase,
        required: false
    },
    {
        id: 'INVENTORY',
        name: 'Inventory',
        description: 'Track stock levels, product movement, and valuation.',
        icon: Truck,
        required: false
    },
    {
        id: 'PAYROLL',
        name: 'Payroll',
        description: 'Employee compensation, benefits, and payroll taxes.',
        icon: Users,
        required: false
    },
];

const Step4ModuleSelection: React.FC<Step4Props> = ({ companyId, onNext, onBack, status }) => {
    const [selectedModules, setSelectedModules] = useState<string[]>(['ACCOUNTING']);

    // Hydrate logic could go here if we had an endpoint to fetch current modules

    const toggleModule = (id: string, required: boolean) => {
        if (required) return;
        if (selectedModules.includes(id)) {
            setSelectedModules(selectedModules.filter(m => m !== id));
        } else {
            setSelectedModules([...selectedModules, id]);
        }
    };

    const mutation = useMutation({
        mutationFn: async () => {
            await api.post(`/onboarding/${companyId}/step-4`, {
                modules: selectedModules
            });
        },
        onSuccess: () => {
            onNext();
        }
    });

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-semibold tracking-tight">Select Modules</h2>
                <p className="text-muted-foreground">
                    Choose the functional areas you need. Accounting is included by default.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {MODULES.map((module) => {
                    const isSelected = selectedModules.includes(module.id);
                    const Icon = module.icon;

                    return (
                        <Card
                            key={module.id}
                            className={cn(
                                "cursor-pointer transition-all duration-200 border-2 hover:border-emerald-500/50",
                                isSelected ? "border-emerald-600 bg-emerald-50" : "border-transparent bg-stone-50"
                            )}
                            onClick={() => toggleModule(module.id, module.required)}
                        >
                            <CardContent className="p-6 space-y-4">
                                <div className="flex justify-between items-start">
                                    <div className={cn(
                                        "p-3 rounded-lg",
                                        isSelected ? "bg-emerald-100 text-emerald-700" : "bg-stone-200 text-stone-500"
                                    )}>
                                        <Icon className="h-6 w-6" />
                                    </div>
                                    {isSelected && (
                                        <div className="bg-emerald-600 text-white rounded-full p-1">
                                            <Check className="h-4 w-4" />
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">{module.name}</h3>
                                    <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                                        {module.description}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
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

export default Step4ModuleSelection;
