import { useState, useEffect } from 'react';
import { Check, Palette } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { AVAILABLE_PALETTES, type ThemePalette } from '@/lib/theme-palettes';
import { applyPalette, getCurrentPaletteId } from '@/lib/theme-utils';
import { useTheme } from '@/contexts/ThemeContext';

export default function ThemeSettingsPage() {
    const [selectedPalette, setSelectedPalette] = useState<string>('professional');
    const { theme } = useTheme(); // 'light' or 'dark'

    useEffect(() => {
        // Load saved palette on mount
        const saved = getCurrentPaletteId();
        if (saved) {
            setSelectedPalette(saved);
        }
    }, []);

    const handlePaletteChange = (paletteId: string) => {
        setSelectedPalette(paletteId);
        const palette = AVAILABLE_PALETTES.find(p => p.id === paletteId);
        if (palette) {
            applyPalette(palette, theme as 'light' | 'dark');
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Theme Settings</h1>
                <p className="text-muted-foreground mt-2">
                    Choose a color palette that fits your style
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Palette className="h-5 w-5" />
                        Color Palette
                    </CardTitle>
                    <CardDescription>
                        Select from professionally designed color palettes with proper contrast and accessibility
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <RadioGroup value={selectedPalette} onValueChange={handlePaletteChange}>
                        <div className="grid md:grid-cols-2 gap-4">
                            {AVAILABLE_PALETTES.map((palette) => (
                                <PaletteCard
                                    key={palette.id}
                                    palette={palette}
                                    selected={selectedPalette === palette.id}
                                    onClick={() => handlePaletteChange(palette.id)}
                                />
                            ))}
                        </div>
                    </RadioGroup>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Custom Palette</CardTitle>
                    <CardDescription>
                        Create your own custom color palette (coming soon)
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button variant="outline" disabled>
                        <Palette className="h-4 w-4 mr-2" />
                        Create Custom Palette
                    </Button>
                    <p className="text-xs text-muted-foreground mt-2">
                        This feature will allow you to define custom colors with automatic contrast checking
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}

interface PaletteCardProps {
    palette: ThemePalette;
    selected: boolean;
    onClick: () => void;
}

function PaletteCard({ palette, selected, onClick }: PaletteCardProps) {
    return (
        <div
            className={`relative cursor-pointer rounded-lg border-2 transition-all ${selected ? 'border-primary ring-2 ring-primary/20' : 'border-border hover:border-primary/50'
                }`}
            onClick={onClick}
        >
            <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                        <h3 className="font-semibold text-base">{palette.name}</h3>
                        <p className="text-sm text-muted-foreground mt-1">{palette.description}</p>
                    </div>
                    {selected && (
                        <div className="bg-primary text-primary-foreground rounded-full p-1">
                            <Check className="h-4 w-4" />
                        </div>
                    )}
                </div>

                {/* Color Preview */}
                <div className="space-y-2">
                    <div className="flex gap-2">
                        <div
                            className="h-12 flex-1 rounded-md border"
                            style={{ backgroundColor: palette.colors.primary[500] }}
                            title="Primary"
                        />
                        <div
                            className="h-12 flex-1 rounded-md border"
                            style={{ backgroundColor: palette.colors.accent[500] }}
                            title="Accent"
                        />
                    </div>
                    <div className="flex gap-1">
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.neutral[100] }}
                            title="Background"
                        />
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.neutral[300] }}
                            title="Muted"
                        />
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.neutral[700] }}
                            title="Foreground"
                        />
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.success[500] }}
                            title="Success"
                        />
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.warning[500] }}
                            title="Warning"
                        />
                        <div
                            className="h-8 flex-1 rounded border"
                            style={{ backgroundColor: palette.colors.error[500] }}
                            title="Error"
                        />
                    </div>
                </div>
            </div>

            <RadioGroupItem
                value={palette.id}
                id={palette.id}
                className="sr-only"
            />
        </div>
    );
}
