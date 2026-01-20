/**
 * Theme Palette Utility
 * 
 * Converts TypeScript palette definitions to CSS variables
 */

import type { ThemePalette } from './theme-palettes';

/**
 * Convert hex to HSL
 */
function hexToHSL(hex: string): string {
    // Remove # if present
    hex = hex.replace(/^#/, '');

    // Parse RGB
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;

    if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

        switch (max) {
            case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
            case g: h = ((b - r) / d + 2) / 6; break;
            case b: h = ((r - g) / d + 4) / 6; break;
        }
    }

    h = Math.round(h * 360);
    s = Math.round(s * 100);
    l = Math.round(l * 100);

    return `${h} ${s}% ${l}%`;
}

/**
 * Generate CSS variables for a palette
 */
export function generateCSSVariables(palette: ThemePalette, mode: 'light' | 'dark'): string {
    const semantic = palette.semantic[mode];

    let css = '';

    // Core semantic colors
    css += `    --background: ${hexToHSL(semantic.background)};\n`;
    css += `    --foreground: ${hexToHSL(semantic.foreground)};\n`;
    css += `    --card: ${hexToHSL(semantic.card)};\n`;
    css += `    --card-foreground: ${hexToHSL(semantic.cardForeground)};\n`;
    css += `    --primary: ${hexToHSL(semantic.primary)};\n`;
    css += `    --primary-foreground: ${hexToHSL(semantic.primaryForeground)};\n`;
    css += `    --secondary: ${hexToHSL(semantic.secondary)};\n`;
    css += `    --secondary-foreground: ${hexToHSL(semantic.secondaryForeground)};\n`;
    css += `    --muted: ${hexToHSL(semantic.muted)};\n`;
    css += `    --muted-foreground: ${hexToHSL(semantic.mutedForeground)};\n`;
    css += `    --accent: ${hexToHSL(semantic.accent)};\n`;
    css += `    --accent-foreground: ${hexToHSL(semantic.accentForeground)};\n`;
    css += `    --border: ${hexToHSL(semantic.border)};\n`;
    css += `    --input: ${hexToHSL(semantic.input)};\n`;
    css += `    --ring: ${hexToHSL(semantic.ring)};\n`;

    // Semantic feedback colors
    css += `    --success: ${hexToHSL(palette.colors.success[600])};\n`;
    css += `    --success-foreground: ${hexToHSL(mode === 'light' ? '#ffffff' : palette.colors.success[950])};\n`;
    css += `    --warning: ${hexToHSL(palette.colors.warning[500])};\n`;
    css += `    --warning-foreground: ${hexToHSL(mode === 'light' ? palette.colors.warning[950] : '#ffffff')};\n`;
    css += `    --info: ${hexToHSL(palette.colors.primary[600])};\n`;
    css += `    --info-foreground: ${hexToHSL(mode === 'light' ? '#ffffff' : palette.colors.primary[950])};\n`;

    return css;
}

/**
 * Apply palette to document
 */
export function applyPalette(palette: ThemePalette, mode: 'light' | 'dark' = 'light'): void {
    const root = document.documentElement;
    const semantic = palette.semantic[mode];

    // Apply semantic colors
    root.style.setProperty('--background', hexToHSL(semantic.background));
    root.style.setProperty('--foreground', hexToHSL(semantic.foreground));
    root.style.setProperty('--card', hexToHSL(semantic.card));
    root.style.setProperty('--card-foreground', hexToHSL(semantic.cardForeground));
    root.style.setProperty('--primary', hexToHSL(semantic.primary));
    root.style.setProperty('--primary-foreground', hexToHSL(semantic.primaryForeground));
    root.style.setProperty('--secondary', hexToHSL(semantic.secondary));
    root.style.setProperty('--secondary-foreground', hexToHSL(semantic.secondaryForeground));
    root.style.setProperty('--muted', hexToHSL(semantic.muted));
    root.style.setProperty('--muted-foreground', hexToHSL(semantic.mutedForeground));
    root.style.setProperty('--accent', hexToHSL(semantic.accent));
    root.style.setProperty('--accent-foreground', hexToHSL(semantic.accentForeground));
    root.style.setProperty('--border', hexToHSL(semantic.border));
    root.style.setProperty('--input', hexToHSL(semantic.input));
    root.style.setProperty('--ring', hexToHSL(semantic.ring));

    // Apply semantic feedback colors
    root.style.setProperty('--success', hexToHSL(palette.colors.success[600]));
    root.style.setProperty('--success-foreground', hexToHSL(mode === 'light' ? '#ffffff' : palette.colors.success[950]));
    root.style.setProperty('--warning', hexToHSL(palette.colors.warning[500]));
    root.style.setProperty('--warning-foreground', hexToHSL(mode === 'light' ? palette.colors.warning[950] : '#ffffff'));
    root.style.setProperty('--info', hexToHSL(palette.colors.primary[600]));
    root.style.setProperty('--info-foreground', hexToHSL(mode === 'light' ? '#ffffff' : palette.colors.primary[950]));

    // Store palette ID in localStorage
    localStorage.setItem('theme-palette', palette.id);
}

/**
 * Get current palette ID from localStorage
 */
export function getCurrentPaletteId(): string | null {
    return localStorage.getItem('theme-palette');
}
