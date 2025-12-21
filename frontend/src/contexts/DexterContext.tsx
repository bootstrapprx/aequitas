import React, { createContext, useContext, useState, ReactNode } from 'react';
import { api } from '@/lib/api';

// Types from our API
interface OnboardingPreprocessResponse {
    suggested_value: string;
    confidence: number;
    correction_type?: string;
    explanation?: string;
    requires_confirmation: boolean;
}

interface Suggestion {
    type: 'correction' | 'warning' | 'info';
    message: string;
    details?: string;
    suggestedValue?: string; // For auto-fix application
    field?: string;
}

interface DexterContextType {
    suggestion: Suggestion | null;
    isAnalyzing: boolean;
    analyzeInput: (companyId: string, step: string, field: string, value: string, context?: any) => Promise<void>;
    clearSuggestion: () => void;
    acceptSuggestion: () => void; // Placeholder for accepting the fix
}

const DexterContext = createContext<DexterContextType | undefined>(undefined);

export function DexterProvider({ children }: { children: ReactNode }) {
    const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const analyzeInput = async (companyId: string, step: string, field: string, value: string, extraContext?: any) => {
        // Basic debounce or check could go here, but validation usually happens onBlur
        if (!value || value.trim().length < 2) {
            setSuggestion(null);
            return;
        }

        setIsAnalyzing(true);
        try {
            // Call Dexter Preprocess API
            // Note: api wrapper might need type adjustment or generic
            const response = await api.post(`/onboarding/${companyId}/dexter/preprocess`, {
                step,
                field,
                user_input: value,
                context: extraContext
            }) as unknown as OnboardingPreprocessResponse;

            if (response.requires_confirmation && response.suggested_value !== value) {
                // Map API response to UI Suggestion
                setSuggestion({
                    type: response.correction_type === 'warning' ? 'warning' : 'correction',
                    message: response.explanation || 'I have a suggestion for this field.',
                    suggestedValue: response.suggested_value,
                    field: field,
                    details: `Suggested: ${response.suggested_value}`
                });
            } else {
                setSuggestion(null);
            }
        } catch (err) {
            console.error("Dexter analysis failed", err);
            // Fail silently in UI
            setSuggestion(null);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const clearSuggestion = () => setSuggestion(null);
    const acceptSuggestion = () => {
        // Logic to update the form would need to be handled by the consuming component 
        // passing a callback or exposing the setFieldValue method contextually.
        // For now, we just clear.
        setSuggestion(null);
    };

    return (
        <DexterContext.Provider value={{ suggestion, isAnalyzing, analyzeInput, clearSuggestion, acceptSuggestion }}>
            {children}
        </DexterContext.Provider>
    );
}

export function useDexter() {
    const context = useContext(DexterContext);
    if (context === undefined) {
        throw new Error('useDexter must be used within a DexterProvider');
    }
    return context;
}
