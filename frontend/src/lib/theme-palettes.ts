/**
 * Aequitas Theme Palette System
 * 
 * This file defines color palettes with proper semantic mapping.
 * Each palette includes light and dark mode variations with guaranteed contrast ratios.
 */

export interface ColorShade {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string; // DEFAULT
    600: string;
    700: string;
    800: string;
    900: string;
    950: string;
}

export interface PaletteColors {
    primary: ColorShade;
    accent: ColorShade;
    neutral: ColorShade;
    success: ColorShade;
    warning: ColorShade;
    error: ColorShade;
}

export interface SemanticMapping {
    light: {
        background: string;
        foreground: string;
        card: string;
        cardForeground: string;
        primary: string;
        primaryForeground: string;
        secondary: string;
        secondaryForeground: string;
        muted: string;
        mutedForeground: string;
        accent: string;
        accentForeground: string;
        border: string;
        input: string;
        ring: string;
    };
    dark: {
        background: string;
        foreground: string;
        card: string;
        cardForeground: string;
        primary: string;
        primaryForeground: string;
        secondary: string;
        secondaryForeground: string;
        muted: string;
        mutedForeground: string;
        accent: string;
        accentForeground: string;
        border: string;
        input: string;
        ring: string;
    };
}

export interface ThemePalette {
    id: string;
    name: string;
    description: string;
    colors: PaletteColors;
    semantic: SemanticMapping;
}

// ============================================================================
// PRE-BUILT PALETTES
// ============================================================================

/**
 * Professional Classic - Navy & Gold
 * Traditional, trustworthy, professional
 */
export const PALETTE_PROFESSIONAL: ThemePalette = {
    id: 'professional',
    name: 'Professional Classic',
    description: 'Navy blue and gold - traditional, trustworthy, professional',
    colors: {
        primary: {
            50: '#eff6ff',
            100: '#dbeafe',
            200: '#bfdbfe',
            300: '#93c5fd',
            400: '#60a5fa',
            500: '#1e40af', // Navy
            600: '#1e3a8a',
            700: '#1e3a8a',
            800: '#1e3a8a',
            900: '#172554',
            950: '#0f172a',
        },
        accent: {
            50: '#fefce8',
            100: '#fef9c3',
            200: '#fef08a',
            300: '#fde047',
            400: '#facc15',
            500: '#eab308', // Gold
            600: '#ca8a04',
            700: '#a16207',
            800: '#854d0e',
            900: '#713f12',
            950: '#422006',
        },
        neutral: {
            50: '#f8fafc',
            100: '#f1f5f9',
            200: '#e2e8f0',
            300: '#cbd5e1',
            400: '#94a3b8',
            500: '#64748b',
            600: '#475569',
            700: '#334155',
            800: '#1e293b',
            900: '#0f172a',
            950: '#020617',
        },
        success: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#052e16',
        },
        warning: {
            50: '#fffbeb',
            100: '#fef3c7',
            200: '#fde68a',
            300: '#fcd34d',
            400: '#fbbf24',
            500: '#f59e0b',
            600: '#d97706',
            700: '#b45309',
            800: '#92400e',
            900: '#78350f',
            950: '#451a03',
        },
        error: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            950: '#450a0a',
        },
    },
    semantic: {
        light: {
            background: '#f8fafc', // neutral-50
            foreground: '#0f172a', // neutral-900
            card: '#ffffff',
            cardForeground: '#0f172a',
            primary: '#1e40af', // primary-500
            primaryForeground: '#ffffff',
            secondary: '#f1f5f9', // neutral-100
            secondaryForeground: '#0f172a',
            muted: '#f1f5f9',
            mutedForeground: '#64748b', // neutral-500
            accent: '#eab308', // accent-500
            accentForeground: '#0f172a',
            border: '#e2e8f0', // neutral-200
            input: '#e2e8f0',
            ring: '#1e40af',
        },
        dark: {
            background: '#020617', // neutral-950
            foreground: '#f8fafc', // neutral-50
            card: '#0f172a', // neutral-900
            cardForeground: '#f8fafc',
            primary: '#60a5fa', // primary-400 (lighter for dark)
            primaryForeground: '#020617',
            secondary: '#1e293b', // neutral-800
            secondaryForeground: '#f8fafc',
            muted: '#1e293b',
            mutedForeground: '#94a3b8', // neutral-400
            accent: '#fde047', // accent-300 (lighter for dark)
            accentForeground: '#020617',
            border: '#334155', // neutral-700
            input: '#334155',
            ring: '#60a5fa',
        },
    },
};

/**
 * Modern Tech - Indigo & Cyan
 * Clean, modern, tech-forward
 */
export const PALETTE_MODERN: ThemePalette = {
    id: 'modern',
    name: 'Modern Tech',
    description: 'Indigo and cyan - clean, modern, tech-forward',
    colors: {
        primary: {
            50: '#eef2ff',
            100: '#e0e7ff',
            200: '#c7d2fe',
            300: '#a5b4fc',
            400: '#818cf8',
            500: '#6366f1', // Indigo
            600: '#4f46e5',
            700: '#4338ca',
            800: '#3730a3',
            900: '#312e81',
            950: '#1e1b4b',
        },
        accent: {
            50: '#ecfeff',
            100: '#cffafe',
            200: '#a5f3fc',
            300: '#67e8f9',
            400: '#22d3ee',
            500: '#06b6d4', // Cyan
            600: '#0891b2',
            700: '#0e7490',
            800: '#155e75',
            900: '#164e63',
            950: '#083344',
        },
        neutral: {
            50: '#fafafa',
            100: '#f4f4f5',
            200: '#e4e4e7',
            300: '#d4d4d8',
            400: '#a1a1aa',
            500: '#71717a',
            600: '#52525b',
            700: '#3f3f46',
            800: '#27272a',
            900: '#18181b',
            950: '#09090b',
        },
        success: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#052e16',
        },
        warning: {
            50: '#fefce8',
            100: '#fef9c3',
            200: '#fef08a',
            300: '#fde047',
            400: '#facc15',
            500: '#eab308',
            600: '#ca8a04',
            700: '#a16207',
            800: '#854d0e',
            900: '#713f12',
            950: '#422006',
        },
        error: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            950: '#450a0a',
        },
    },
    semantic: {
        light: {
            background: '#fafafa',
            foreground: '#18181b',
            card: '#ffffff',
            cardForeground: '#18181b',
            primary: '#6366f1',
            primaryForeground: '#ffffff',
            secondary: '#f4f4f5',
            secondaryForeground: '#18181b',
            muted: '#f4f4f5',
            mutedForeground: '#71717a',
            accent: '#06b6d4',
            accentForeground: '#ffffff',
            border: '#e4e4e7',
            input: '#e4e4e7',
            ring: '#6366f1',
        },
        dark: {
            background: '#09090b',
            foreground: '#fafafa',
            card: '#18181b',
            cardForeground: '#fafafa',
            primary: '#818cf8',
            primaryForeground: '#09090b',
            secondary: '#27272a',
            secondaryForeground: '#fafafa',
            muted: '#27272a',
            mutedForeground: '#a1a1aa',
            accent: '#22d3ee',
            accentForeground: '#09090b',
            border: '#3f3f46',
            input: '#3f3f46',
            ring: '#818cf8',
        },
    },
};

/**
 * Earthy Natural - Sage & Terra Cotta
 * Organic, warm, approachable
 */
export const PALETTE_EARTHY: ThemePalette = {
    id: 'earthy',
    name: 'Earthy Natural',
    description: 'Sage green and terra cotta - organic, warm, approachable',
    colors: {
        primary: {
            50: '#f4f6f3',
            100: '#e6ebe3',
            200: '#cdd8c9',
            300: '#a9bda2',
            400: '#829e77',
            500: '#5f7f55', // Sage
            600: '#4a6543',
            700: '#3b5136',
            800: '#31422d',
            900: '#293727',
            950: '#131c13',
        },
        accent: {
            50: '#fdf5f3',
            100: '#fbe8e4',
            200: '#f8d5cd',
            300: '#f2b7a8',
            400: '#e98e76',
            500: '#d4704f', // Terra cotta
            600: '#c25739',
            700: '#a2472f',
            800: '#863d2b',
            900: '#6f3729',
            950: '#3c1a12',
        },
        neutral: {
            50: '#f9faf8',
            100: '#f2f4f0',
            200: '#e5e9e0',
            300: '#d0d7c9',
            400: '#b3bdaa',
            500: '#93a187',
            600: '#79876d',
            700: '#636f5a',
            800: '#525b4b',
            900: '#444c3f',
            950: '#232720',
        },
        success: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#052e16',
        },
        warning: {
            50: '#fefce8',
            100: '#fef9c3',
            200: '#fef08a',
            300: '#fde047',
            400: '#facc15',
            500: '#eab308',
            600: '#ca8a04',
            700: '#a16207',
            800: '#854d0e',
            900: '#713f12',
            950: '#422006',
        },
        error: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            950: '#450a0a',
        },
    },
    semantic: {
        light: {
            background: '#f9faf8',
            foreground: '#232720',
            card: '#ffffff',
            cardForeground: '#232720',
            primary: '#5f7f55',
            primaryForeground: '#ffffff',
            secondary: '#f2f4f0',
            secondaryForeground: '#232720',
            muted: '#e5e9e0',
            mutedForeground: '#636f5a',
            accent: '#d4704f',
            accentForeground: '#ffffff',
            border: '#d0d7c9',
            input: '#e5e9e0',
            ring: '#5f7f55',
        },
        dark: {
            background: '#232720',
            foreground: '#f9faf8',
            card: '#444c3f',
            cardForeground: '#f9faf8',
            primary: '#a9bda2',
            primaryForeground: '#232720',
            secondary: '#525b4b',
            secondaryForeground: '#f9faf8',
            muted: '#636f5a',
            mutedForeground: '#b3bdaa',
            accent: '#f2b7a8',
            accentForeground: '#232720',
            border: '#636f5a',
            input: '#636f5a',
            ring: '#a9bda2',
        },
    },
};

/**
 * Premium Dark - Charcoal & Amber
 * Sophisticated, luxurious, elegant
 */
export const PALETTE_PREMIUM: ThemePalette = {
    id: 'premium',
    name: 'Premium Dark',
    description: 'Charcoal and amber - sophisticated, luxurious, elegant',
    colors: {
        primary: {
            50: '#f6f6f6',
            100: '#e7e7e7',
            200: '#d1d1d1',
            300: '#b0b0b0',
            400: '#888888',
            500: '#6d6d6d', // Charcoal
            600: '#5d5d5d',
            700: '#4f4f4f',
            800: '#454545',
            900: '#3d3d3d',
            950: '#1a1a1a',
        },
        accent: {
            50: '#fffbeb',
            100: '#fef3c7',
            200: '#fde68a',
            300: '#fcd34d',
            400: '#fbbf24',
            500: '#f59e0b', // Amber
            600: '#d97706',
            700: '#b45309',
            800: '#92400e',
            900: '#78350f',
            950: '#451a03',
        },
        neutral: {
            50: '#fafafa',
            100: '#f5f5f5',
            200: '#e5e5e5',
            300: '#d4d4d4',
            400: '#a3a3a3',
            500: '#737373',
            600: '#525252',
            700: '#404040',
            800: '#262626',
            900: '#171717',
            950: '#0a0a0a',
        },
        success: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#052e16',
        },
        warning: {
            50: '#fffbeb',
            100: '#fef3c7',
            200: '#fde68a',
            300: '#fcd34d',
            400: '#fbbf24',
            500: '#f59e0b',
            600: '#d97706',
            700: '#b45309',
            800: '#92400e',
            900: '#78350f',
            950: '#451a03',
        },
        error: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            950: '#450a0a',
        },
    },
    semantic: {
        light: {
            background: '#fafafa',
            foreground: '#171717',
            card: '#ffffff',
            cardForeground: '#171717',
            primary: '#3d3d3d',
            primaryForeground: '#ffffff',
            secondary: '#f5f5f5',
            secondaryForeground: '#171717',
            muted: '#e5e5e5',
            mutedForeground: '#525252',
            accent: '#f59e0b',
            accentForeground: '#171717',
            border: '#d4d4d4',
            input: '#e5e5e5',
            ring: '#3d3d3d',
        },
        dark: {
            background: '#0a0a0a',
            foreground: '#fafafa',
            card: '#171717',
            cardForeground: '#fafafa',
            primary: '#d4d4d4',
            primaryForeground: '#0a0a0a',
            secondary: '#262626',
            secondaryForeground: '#fafafa',
            muted: '#404040',
            mutedForeground: '#a3a3a3',
            accent: '#fbbf24',
            accentForeground: '#0a0a0a',
            border: '#404040',
            input: '#404040',
            ring: '#d4d4d4',
        },
    },
};

// ============================================================================
// PALETTE REGISTRY
// ============================================================================

export const AVAILABLE_PALETTES: ThemePalette[] = [
    PALETTE_PROFESSIONAL,
    PALETTE_MODERN,
    PALETTE_EARTHY,
    PALETTE_PREMIUM,
];

export const getPaletteById = (id: string): ThemePalette | undefined => {
    return AVAILABLE_PALETTES.find((p) => p.id === id);
};

export const getDefaultPalette = (): ThemePalette => {
    return PALETTE_PROFESSIONAL;
};
