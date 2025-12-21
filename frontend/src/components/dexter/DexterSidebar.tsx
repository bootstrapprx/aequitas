import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Sparkles, Info, AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDexter } from '@/contexts/DexterContext';

// Types covering Canon §5
type SuggestionType = 'correction' | 'warning' | 'info';

interface DexterSidebarProps {
    step: string;
    currentField?: string;
    context?: any;
}

export function DexterSidebar({ step }: DexterSidebarProps) {
    const { suggestion, isAnalyzing } = useDexter();

    return (
        <div className="w-80 border-l bg-muted/10 h-full flex flex-col hidden lg:flex">
            <div className="p-4 border-b bg-background/50 backdrop-blur-sm">
                <div className="flex items-center gap-2 text-primary font-semibold">
                    <Sparkles className="h-4 w-4" />
                    <span>Dexter</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                    Accounting Intelligence Layer
                </p>
            </div>

            <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {/* Analyzing State */}
                {isAnalyzing && (
                    <div className="flex items-center justify-center py-4 text-muted-foreground gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-xs">Analyzing...</span>
                    </div>
                )}

                {/* Default "Presence" State (CANON §3.2 - Silence is allowed) */}
                {!suggestion && !isAnalyzing && (
                    <div className="text-sm text-muted-foreground italic text-center py-8 opacity-50">
                        Dexter is observing...
                    </div>
                )}

                {/* Suggestion Card */}
                {suggestion && (
                    <Card className={cn("border-l-4 shadow-sm",
                        suggestion.type === 'correction' ? "border-l-blue-500" :
                            suggestion.type === 'warning' ? "border-l-yellow-500" : "border-l-gray-300"
                    )}>
                        <CardHeader className="pb-2 pt-4">
                            <div className="flex items-center gap-2 text-sm font-medium">
                                {suggestion.type === 'warning' ? <AlertTriangle className="h-4 w-4 text-yellow-500" /> : <Info className="h-4 w-4 text-blue-500" />}
                                {suggestion.type === 'correction' ? 'Standardization' :
                                    suggestion.type === 'warning' ? 'Attention' : 'Insight'}
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm">
                            <p>{suggestion.message}</p>
                            {suggestion.details && (
                                <p className="mt-2 text-xs text-muted-foreground bg-muted p-2 rounded">
                                    {suggestion.details}
                                </p>
                            )}
                        </CardContent>
                    </Card>
                )}
            </div>

            <div className="p-4 border-t bg-background/50 text-[10px] text-muted-foreground text-center">
                DEXTER v1.1 • AUTHORITATIVE
            </div>
        </div>
    );
}
