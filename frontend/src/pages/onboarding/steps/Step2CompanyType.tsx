
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Briefcase, Building2, CheckCircle, ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Step2Props {
    companyId: string;
    onNext: () => void;
    onBack: () => void;
    status: any;
}

const LEGAL_NATURE_OPTIONS = [
    'LLC', 'Corporation', 'Sole Proprietorship', 'Partnership', 'Non-Profit'
];

const ECONOMIC_ACTIVITY_OPTIONS = [
    'Technology', 'Retail', 'Healthcare', 'Finance', 'Manufacturing', 'Services', 'Real Estate', 'Other'
];

const Step2CompanyType: React.FC<Step2Props> = ({ companyId, onNext, onBack, status }) => {
    const [legalNature, setLegalNature] = useState('');
    const [economicActivity, setEconomicActivity] = useState('');

    // Hydrate from existing data if available
    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const response = await api.get<any>(`/companies/${companyId}`);
                if (response.legal_nature) setLegalNature(response.legal_nature);
                if (response.economic_activity) setEconomicActivity(response.economic_activity);
            } catch (error) {
                console.error("Failed to fetch company details", error);
            }
        };
        fetchDetails();
    }, [companyId]);

    const mutation = useMutation({
        mutationFn: async () => {
            await api.post(`/onboarding/${companyId}/step-2`, {
                legal_nature: legalNature,
                economic_activity: economicActivity
            });
        },
        onSuccess: () => {
            onNext();
        }
    });

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-semibold tracking-tight">Company Type & Activity</h2>
                <p className="text-muted-foreground">
                    Tell us more about your business structure and industry.
                </p>
            </div>

            <div className="grid gap-6 max-w-md mx-auto">
                <div className="grid gap-2">
                    <Label htmlFor="legal_nature">Legal Nature</Label>
                    <Select value={legalNature} onValueChange={setLegalNature}>
                        <SelectTrigger id="legal_nature">
                            <SelectValue placeholder="Select legal structure" />
                        </SelectTrigger>
                        <SelectContent>
                            {LEGAL_NATURE_OPTIONS.map((opt) => (
                                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="grid gap-2">
                    <Label htmlFor="economic_activity">Economic Activity</Label>
                    <Select value={economicActivity} onValueChange={setEconomicActivity}>
                        <SelectTrigger id="economic_activity">
                            <SelectValue placeholder="Select primary industry" />
                        </SelectTrigger>
                        <SelectContent>
                            {ECONOMIC_ACTIVITY_OPTIONS.map((opt) => (
                                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="flex justify-between pt-8 border-t">
                <Button variant="outline" onClick={onBack}>
                    Back
                </Button>
                <Button
                    onClick={() => mutation.mutate()}
                    disabled={!legalNature || !economicActivity || mutation.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                    {mutation.isPending ? 'Saving...' : 'Continue'}
                    <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
            </div>
        </div>
    );
};

export default Step2CompanyType;
