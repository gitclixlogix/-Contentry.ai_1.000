import { mode } from '@chakra-ui/theme-tools';
import { typography, colors as designColors, borders, shadows } from './designConfig';

// ============================================
// OFFICIAL BRAND COLOR PALETTE (December 2025)
// OKLCH-Based High Contrast Design System
// ============================================
// 
// LIGHT MODE (High Contrast):
// - Primary (Royal Blue): oklch(0.45 0.18 250) → #1e40af
// - Secondary (Light Cyan): oklch(0.95 0.05 230) → #e0f2fe
// - Accent (Electric Blue): oklch(0.5 0.15 220) → #0284c7
// - Background (Pure White): oklch(0.99 0 0) → #fafafa
// - Foreground (Deep Navy): oklch(0.15 0.04 260) → #172554
//
// DARK MODE (Deep Blue / Glassmorphism):
// - Primary (Bright Blue): oklch(0.6 0.18 250) → #3b82f6
// - Secondary (Soft Cyan): oklch(0.85 0.1 230) → #bae6fd
// - Accent (Vibrant Blue): oklch(0.7 0.15 220) → #38bdf8
// - Background (Deep Navy): oklch(0.12 0.04 260) → #0c1222
// - Foreground (Off-White): oklch(0.95 0.02 240) → #f0f9ff
// - Card Background: oklch(0.18 0.04 260 / 0.6) → rgba(23, 37, 84, 0.6)
// ============================================

export const globalStyles = {
  colors: {
    // =============================================
    // CONTENTRY.AI OFFICIAL BRAND COLORS (Dec 2025)
    // From BrandBook.pdf
    // =============================================
    // PRIMARY: Blue 600 #2563eb
    // ACCENT: Cyan 500 #06b6d4
    // DARK: Dark Slate #0f172a
    // SECONDARY: White #ffffff, Slate 400 #94a3b8
    // =============================================
    
    // Primary Brand Colors (Blue 600 based)
    brand: {
      50: '#eff6ff',   // Very light blue
      100: '#dbeafe',  // Light blue
      200: '#bfdbfe',  // Soft blue
      300: '#93c5fd',  // Medium light blue
      400: '#60a5fa',  // Medium blue
      500: '#2563eb',  // PRIMARY - Blue 600 (from BrandBook)
      600: '#2563eb',  // Blue 600 (consistent)
      700: '#1d4ed8',  // Deep blue
      800: '#1e40af',  // Darker blue
      900: '#0f172a',  // Dark Slate (from BrandBook)
    },
    brandScheme: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#2563eb',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#0f172a',
    },
    brandTabs: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#2563eb',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#0f172a',
    },
    // Accent Colors (Cyan 500 based from BrandBook)
    cyan: {
      50: '#ecfeff',
      100: '#cffafe',
      200: '#a5f3fc',
      300: '#67e8f9',
      400: '#22d3ee',
      500: '#06b6d4',  // Cyan 500 (from BrandBook)
      600: '#0891b2',
      700: '#0e7490',
      800: '#155e75',
      900: '#164e63',
    },
    // Secondary Colors (Light Cyan / Soft Cyan)
    secondary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#06b6d4',   // Cyan 500 accent
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
    // Accent Colors
    accent: {
      light: '#06b6d4',  // Cyan 500
      dark: '#22d3ee',   // Cyan 400
    },
    // UI Colors
    textPrimary: {
      light: '#172554',  // Deep Navy oklch(0.15 0.04 260)
      dark: '#f0f9ff',   // Off-White oklch(0.95 0.02 240)
    },
    textSecondary: {
      light: '#475569',  // Slate-600
      dark: '#94a3b8',   // Slate-400
    },
    borderColor: {
      light: '#e2e8f0',  // Slate-200
      dark: '#334155',   // Slate-700
    },
    background: {
      light: '#fafafa',  // Pure White oklch(0.99 0 0)
      dark: '#0c1222',   // Deep Navy oklch(0.12 0.04 260)
    },
    card: {
      light: '#ffffff',
      dark: 'rgba(23, 37, 84, 0.6)',  // Glassmorphism oklch(0.18 0.04 260 / 0.6)
    },
    secondaryGray: {
      100: '#f8fafc',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
    },
    red: {
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
    },
    blue: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    orange: {
      50: '#fff7ed',
      100: '#ffedd5',
      200: '#fed7aa',
      300: '#fdba74',
      400: '#fb923c',
      500: '#f97316',
      600: '#ea580c',
      700: '#c2410c',
      800: '#9a3412',
      900: '#7c2d12',
    },
    green: {
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
    },
    purple: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7e22ce',
      800: '#6b21a8',
      900: '#581c87',
    },
    white: {
      50: '#ffffff',
      100: '#ffffff',
      200: '#ffffff',
      300: '#ffffff',
      400: '#ffffff',
      500: '#ffffff',
      600: '#ffffff',
      700: '#ffffff',
      800: '#ffffff',
      900: '#ffffff',
    },
    navy: {
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
      950: '#0c1222',  // Deep Navy background
    },
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  styles: {
    global: (props) => ({
      // CSS Custom Properties for OKLCH colors
      ':root': {
        '--color-primary-light': 'oklch(0.45 0.18 250)',
        '--color-primary-dark': 'oklch(0.6 0.18 250)',
        '--color-secondary-light': 'oklch(0.95 0.05 230)',
        '--color-secondary-dark': 'oklch(0.85 0.1 230)',
        '--color-accent-light': 'oklch(0.5 0.15 220)',
        '--color-accent-dark': 'oklch(0.7 0.15 220)',
        '--color-bg-light': 'oklch(0.99 0 0)',
        '--color-bg-dark': 'oklch(0.12 0.04 260)',
        '--color-fg-light': 'oklch(0.15 0.04 260)',
        '--color-fg-dark': 'oklch(0.95 0.02 240)',
        '--color-card-dark': 'oklch(0.18 0.04 260 / 0.6)',
      },
      body: {
        overflowX: 'hidden',
        bg: mode('#fafafa', '#0c1222')(props), // oklch backgrounds
        fontFamily: typography.fontFamily,
        fontSize: '16px',
        lineHeight: '1.5',
        color: mode('#172554', '#f0f9ff')(props), // Deep Navy / Off-White
        WebkitFontSmoothing: 'antialiased',
        MozOsxFontSmoothing: 'grayscale',
        // Gradient background for dark mode
        _dark: {
          backgroundImage: `
            radial-gradient(circle at 15% 50%, rgba(30, 64, 175, 0.15), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(14, 165, 233, 0.1), transparent 25%)
          `,
          backgroundAttachment: 'fixed',
        },
      },
      html: {
        fontFamily: typography.fontFamily,
      },
      input: {
        color: mode('#172554', '#f0f9ff')(props),
        fontFamily: typography.fontFamily,
      },
      textarea: {
        fontFamily: typography.fontFamily,
      },
      select: {
        fontFamily: typography.fontFamily,
      },
      // Heading styles with proper hierarchy
      h1: {
        fontFamily: typography.fontFamily,
        fontWeight: typography.fontWeights.bold,
        lineHeight: '1.2',
        color: mode('#172554', '#f0f9ff')(props),
      },
      h2: {
        fontFamily: typography.fontFamily,
        fontWeight: typography.fontWeights.semibold,
        lineHeight: '1.25',
        color: mode('#172554', '#f0f9ff')(props),
      },
      h3: {
        fontFamily: typography.fontFamily,
        fontWeight: typography.fontWeights.semibold,
        lineHeight: '1.3',
      },
      h4: {
        fontFamily: typography.fontFamily,
        fontWeight: typography.fontWeights.medium,
        lineHeight: '1.35',
      },
      // Focus ring styling with brand color
      '*:focus-visible': {
        outline: '2px solid',
        outlineColor: mode('#1e40af', '#3b82f6')(props),
        outlineOffset: '2px',
      },
      // Scrollbar styling
      '*::-webkit-scrollbar': {
        width: '8px',
        height: '8px',
      },
      '*::-webkit-scrollbar-track': {
        background: mode('#f1f5f9', '#1e293b')(props),
        borderRadius: '4px',
      },
      '*::-webkit-scrollbar-thumb': {
        background: mode('#cbd5e1', '#475569')(props),
        borderRadius: '4px',
        '&:hover': {
          background: mode('#94a3b8', '#64748b')(props),
        },
      },
    }),
  },
};
