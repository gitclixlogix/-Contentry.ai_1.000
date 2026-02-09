/**
 * Global Design Configuration
 * ==============================
 * This file centralizes all design tokens for easy customization.
 * Change values here to update the entire application's look and feel.
 */

// =============================================================================
// TYPOGRAPHY
// =============================================================================
export const typography = {
  // Primary font family - Used for all body text, headings, and UI elements
  // Options: 'Satoshi', 'Inter', 'Plus Jakarta Sans', etc.
  fontFamily: "'Satoshi', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  
  // Font weights mapping
  fontWeights: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    black: 900,
  },

  // Font sizes following the text size hierarchy
  fontSizes: {
    // H1 (Main Heading): text-4xl sm:text-5xl lg:text-6xl
    h1: { base: '2.25rem', sm: '3rem', lg: '3.75rem' }, // 36px, 48px, 60px
    // H2 (Subheading): text-base md:text-lg
    h2: { base: '1rem', md: '1.125rem' }, // 16px, 18px
    // H3 (Section Title)
    h3: { base: '1.125rem', md: '1.25rem' }, // 18px, 20px
    // Body text
    body: { base: '0.875rem', md: '1rem' }, // 14px, 16px
    // Small/Accent text
    small: '0.875rem', // 14px
    xs: '0.75rem', // 12px
  },

  // Line heights
  lineHeights: {
    tight: 1.2,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
};

// =============================================================================
// COLORS - OKLCH-Based Blue Design System (December 2025)
// =============================================================================
export const colors = {
  // Brand colors - Royal Blue palette (OKLCH-based)
  // Light Mode Primary: oklch(0.45 0.18 250) → #1e40af
  // Dark Mode Primary: oklch(0.6 0.18 250) → #3b82f6
  brand: {
    50: '#eff6ff',   // Very light blue
    100: '#dbeafe',  // Light blue
    200: '#bfdbfe',  // Soft blue
    300: '#93c5fd',  // Medium light blue
    400: '#60a5fa',  // Medium blue
    500: '#1e40af',  // PRIMARY - Royal Blue (Light mode)
    600: '#3b82f6',  // Bright Blue (Dark mode primary)
    700: '#1d4ed8',  // Deep blue
    800: '#1e3a8a',  // Darker blue
    900: '#172554',  // Deep Navy
  },

  // AI accent colors - Electric/Vibrant Blue
  aiAccent: {
    primary: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
    secondary: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
    glow: 'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)',
  },

  // Background gradients for cards and sections
  gradients: {
    aiCard: 'linear-gradient(135deg, rgba(30, 64, 175, 0.05) 0%, rgba(59, 130, 246, 0.08) 100%)',
    aiCardDark: 'linear-gradient(135deg, rgba(30, 64, 175, 0.15) 0%, rgba(59, 130, 246, 0.2) 100%)',
    primary: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
    subtle: 'linear-gradient(135deg, rgba(30, 64, 175, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%)',
  },
};

// =============================================================================
// SPACING
// =============================================================================
export const spacing = {
  // Base spacing unit (4px)
  unit: 4,
  
  // Spacing scale
  scale: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },

  // Section padding
  section: {
    x: { base: '16px', md: '24px', lg: '32px' },
    y: { base: '24px', md: '32px', lg: '48px' },
  },

  // Card padding
  card: {
    base: '16px',
    md: '20px',
    lg: '24px',
  },
};

// =============================================================================
// BORDERS & SHADOWS
// =============================================================================
export const borders = {
  // Border radius - Softer, more modern feel
  radius: {
    none: '0',
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '18px',
    '2xl': '24px',
    full: '9999px',
  },

  // Border widths
  width: {
    thin: '1px',
    medium: '2px',
    thick: '3px',
  },
};

export const shadows = {
  // Shadows - Subtle, modern depth
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
  
  // Special AI-themed shadows - Blue glow
  aiGlow: '0 0 20px rgba(30, 64, 175, 0.3)',
  aiGlowHover: '0 0 30px rgba(30, 64, 175, 0.5)',
  
  // Card shadows
  card: '0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
  cardHover: '0 10px 20px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
};

// =============================================================================
// TRANSITIONS & ANIMATIONS
// =============================================================================
export const transitions = {
  // Durations
  duration: {
    fast: '150ms',
    normal: '250ms',
    slow: '350ms',
  },

  // Easing functions
  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },

  // Common transition strings
  all: 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)',
  colors: 'color 250ms, background-color 250ms, border-color 250ms',
  transform: 'transform 250ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// =============================================================================
// BUTTON STYLES
// =============================================================================
export const buttons = {
  // Default border radius for buttons
  borderRadius: borders.radius.lg, // 14px - softer than before
  
  // Size variants
  sizes: {
    sm: {
      h: '32px',
      px: '12px',
      fontSize: '0.875rem',
    },
    md: {
      h: '40px',
      px: '16px',
      fontSize: '0.875rem',
    },
    lg: {
      h: '48px',
      px: '24px',
      fontSize: '1rem',
    },
  },

  // Primary button gradient - Royal Blue
  primaryGradient: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
  primaryHoverShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.4)',
};

// =============================================================================
// COMPONENT-SPECIFIC CONFIGS
// =============================================================================
export const components = {
  // Card component
  card: {
    borderRadius: borders.radius.xl,
    shadow: shadows.card,
    hoverShadow: shadows.cardHover,
    padding: spacing.card,
  },

  // Input component
  input: {
    borderRadius: borders.radius.md,
    height: '44px',
  },

  // Badge component
  badge: {
    borderRadius: borders.radius.full,
  },

  // Modal component
  modal: {
    borderRadius: borders.radius['2xl'],
  },
};

// =============================================================================
// EXPORT COMPLETE CONFIG
// =============================================================================
export const designConfig = {
  typography,
  colors,
  spacing,
  borders,
  shadows,
  transitions,
  buttons,
  components,
};

export default designConfig;
