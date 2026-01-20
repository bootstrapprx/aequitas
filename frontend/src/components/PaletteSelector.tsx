import { Palette } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { AVAILABLE_PALETTES } from '@/lib/theme-palettes';
import { applyPalette, getCurrentPaletteId } from '@/lib/theme-utils';

export const PaletteSelector = () => {
    const [selectedPalette, setSelectedPalette] = useState<string>('professional');
    const { theme } = useTheme();
    const [open, setOpen] = useState(false);

    useEffect(() => {
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
            setOpen(false);
        }
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="relative h-9 w-9"
                    aria-label="Change color palette"
                >
                    <Palette className="h-[1.2rem] w-[1.2rem]" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-3" align="end">
                <div className="space-y-2">
                    <p className="text-sm font-semibold">Color Palette</p>
                    <div className="space-y-2">
                        {AVAILABLE_PALETTES.map((palette) => (
                            <button
                                key={palette.id}
                                onClick={() => handlePaletteChange(palette.id)}
                                className={`w-full text-left p-3 rounded-md border transition-all ${selectedPalette === palette.id
                                        ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                                    }`}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm truncate">{palette.name}</p>
                                        <p className="text-xs text-muted-foreground mt-0.5">{palette.description}</p>
                                    </div>
                                    {selectedPalette === palette.id && (
                                        <div className="bg-primary h-4 w-4 rounded-full flex-shrink-0 mt-0.5" />
                                    )}
                                </div>

                                {/* Color preview */}
                                <div className="flex gap-1 mt-2">
                                    <div
                                        className="h-5 flex-1 rounded border"
                                        style={{ backgroundColor: palette.colors.primary[500] }}
                                        title="Primary"
                                    />
                                    <div
                                        className="h-5 flex-1 rounded border"
                                        style={{ backgroundColor: palette.colors.accent[500] }}
                                        title="Accent"
                                    />
                                    <div
                                        className="h-5 flex-1 rounded border"
                                        style={{ backgroundColor: palette.colors.success[500] }}
                                        title="Success"
                                    />
                                    <div
                                        className="h-5 flex-1 rounded border"
                                        style={{ backgroundColor: palette.colors.warning[500] }}
                                        title="Warning"
                                    />
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    );
};
