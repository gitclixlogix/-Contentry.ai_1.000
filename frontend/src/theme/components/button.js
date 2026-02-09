import { mode } from '@chakra-ui/theme-tools';
import { borders, shadows, transitions } from '../designConfig';

// ============================================
// BUTTON STYLES - OKLCH Blue Design System
// ============================================
// Light Mode Primary: #1e40af (Royal Blue)
// Dark Mode Primary: #3b82f6 (Bright Blue)
// Accent: #0284c7 / #38bdf8 (Electric/Vibrant Blue)
// ============================================

export const buttonStyles = {
  components: {
    Button: {
      baseStyle: {
        borderRadius: borders.radius.lg,
        fontWeight: '500',
        transition: `all ${transitions.duration.normal} ${transitions.easing.default}`,
        boxSizing: 'border-box',
        _focus: {
          boxShadow: 'none',
          outline: '2px solid',
          outlineColor: 'brand.400',
          outlineOffset: '2px',
        },
        _active: {
          transform: 'scale(0.98)',
        },
      },
      variants: {
        transparent: (props) => ({
          bg: 'transparent',
          color: mode('#172554', '#f0f9ff')(props),
          boxShadow: 'none',
          _focus: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _active: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.2)')(props),
          },
          _hover: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
        }),
        a: (props) => ({
          bg: 'transparent',
          color: mode('#1e40af', '#3b82f6')(props),
          padding: 0,
          _focus: {
            bg: 'transparent',
          },
          _active: {
            bg: 'transparent',
          },
          _hover: {
            textDecoration: 'underline',
            bg: 'transparent',
          },
        }),
        // Primary action button - Royal Blue gradient
        primary: (props) => ({
          bg: mode(
            'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
            'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
          )(props),
          color: 'white',
          boxShadow: shadows.md,
          _focus: {
            bg: mode(
              'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
              'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
            )(props),
          },
          _active: {
            bg: mode(
              'linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)',
              'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)'
            )(props),
          },
          _hover: {
            boxShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.4)',
            transform: 'translateY(-1px)',
            bg: mode(
              'linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)',
              'linear-gradient(135deg, #60a5fa 0%, #93c5fd 100%)'
            )(props),
            _disabled: {
              bg: mode(
                'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
                'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
              )(props),
              transform: 'none',
            },
          },
          _disabled: {
            opacity: 0.6,
            cursor: 'not-allowed',
          },
        }),
        // Secondary/outline button
        secondary: (props) => ({
          bg: 'transparent',
          color: mode('#1e40af', '#60a5fa')(props),
          border: '1px solid',
          borderColor: mode('#1e40af', '#60a5fa')(props),
          _focus: {
            bg: mode('#eff6ff', 'rgba(59, 130, 246, 0.1)')(props),
          },
          _active: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.2)')(props),
          },
          _hover: {
            bg: mode('#eff6ff', 'rgba(59, 130, 246, 0.1)')(props),
          },
        }),
        // Ghost/subtle button
        ghost: (props) => ({
          bg: 'transparent',
          color: mode('#475569', '#94a3b8')(props),
          _focus: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _active: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.2)')(props),
          },
          _hover: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
        }),
        red: (props) => ({
          bg: mode('#fef2f2', 'rgba(239, 68, 68, 0.1)')(props),
          color: mode('#dc2626', '#f87171')(props),
          boxShadow: 'none',
          _focus: {
            bg: mode('#fee2e2', 'rgba(239, 68, 68, 0.15)')(props),
          },
          _active: {
            bg: mode('#fee2e2', 'rgba(239, 68, 68, 0.2)')(props),
          },
          _hover: {
            bg: mode('#fee2e2', 'rgba(239, 68, 68, 0.2)')(props),
          },
        }),
        // Cyan accent button
        chakraLinear: (props) => ({
          bg: mode(
            'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
            'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
          )(props),
          color: 'white',
          boxShadow: shadows.md,
          _focus: {
            bg: mode(
              'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
              'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
            )(props),
          },
          _active: {
            bg: mode(
              'linear-gradient(135deg, #0369a1 0%, #0284c7 100%)',
              'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)'
            )(props),
          },
          _hover: {
            boxShadow: '0 10px 20px -5px rgba(2, 132, 199, 0.4)',
            transform: 'translateY(-1px)',
            bg: mode(
              'linear-gradient(135deg, #0ea5e9 0%, #7dd3fc 100%)',
              'linear-gradient(135deg, #7dd3fc 0%, #bae6fd 100%)'
            )(props),
          },
        }),
        outline: (props) => ({
          borderRadius: borders.radius.lg,
          border: '1px solid',
          borderColor: mode('#e2e8f0', '#334155')(props),
          color: mode('#172554', '#f0f9ff')(props),
          _hover: {
            bg: mode('#f8fafc', 'rgba(255,255,255,0.05)')(props),
          },
        }),
        api: (props) => ({
          bg: mode('#1e293b', 'rgba(255,255,255,0.1)')(props),
          color: 'white',
          boxShadow: shadows.sm,
          _focus: {
            bg: mode('#1e293b', 'rgba(255,255,255,0.1)')(props),
          },
          _active: {
            bg: mode('#0f172a', 'rgba(255,255,255,0.15)')(props),
          },
          _hover: {
            bg: mode('#0f172a', 'rgba(255,255,255,0.15)')(props),
            transform: 'translateY(-1px)',
          },
        }),
        // Brand button - Royal Blue
        brand: (props) => ({
          bg: mode('#1e40af', '#3b82f6')(props),
          color: 'white',
          boxShadow: shadows.sm,
          _focus: {
            bg: mode('#2563eb', '#60a5fa')(props),
          },
          _active: {
            bg: mode('#2563eb', '#60a5fa')(props),
          },
          _hover: {
            bg: mode('#2563eb', '#60a5fa')(props),
            boxShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.35)',
            transform: 'translateY(-1px)',
          },
        }),
        darkBrand: (props) => ({
          bg: mode('#1e3a8a', '#2563eb')(props),
          color: 'white',
          _focus: {
            bg: mode('#172554', '#3b82f6')(props),
          },
          _active: {
            bg: mode('#172554', '#3b82f6')(props),
          },
          _hover: {
            bg: mode('#172554', '#3b82f6')(props),
          },
        }),
        lightBrand: (props) => ({
          bg: mode('#eff6ff', 'rgba(59, 130, 246, 0.1)')(props),
          color: mode('#1e40af', '#60a5fa')(props),
          _focus: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.15)')(props),
          },
          _active: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.2)')(props),
          },
          _hover: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.2)')(props),
          },
        }),
        light: (props) => ({
          bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          color: mode('#172554', '#f0f9ff')(props),
          _focus: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.15)')(props),
          },
          _active: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.2)')(props),
          },
          _hover: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.2)')(props),
          },
        }),
        action: (props) => ({
          fontWeight: '500',
          borderRadius: borders.radius.full,
          bg: mode('#eff6ff', '#3b82f6')(props),
          color: mode('#1e40af', 'white')(props),
          _focus: {
            bg: mode('#dbeafe', '#2563eb')(props),
          },
          _active: {
            bg: mode('#dbeafe', '#2563eb')(props),
          },
          _hover: {
            bg: mode('#dbeafe', '#2563eb')(props),
          },
        }),
        setup: (props) => ({
          fontWeight: '500',
          borderRadius: borders.radius.full,
          bg: 'transparent',
          border: '1px solid',
          borderColor: mode('#e2e8f0', '#334155')(props),
          color: mode('#172554', '#f0f9ff')(props),
          _focus: {
            bg: mode('#f8fafc', 'rgba(255,255,255,0.05)')(props),
          },
          _active: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _hover: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
        }),
        // AI action button - Accent Blue gradient
        ai: (props) => ({
          bg: mode(
            'linear-gradient(135deg, #1e40af 0%, #0284c7 50%, #38bdf8 100%)',
            'linear-gradient(135deg, #3b82f6 0%, #38bdf8 50%, #7dd3fc 100%)'
          )(props),
          color: 'white',
          boxShadow: shadows.md,
          position: 'relative',
          overflow: 'hidden',
          _before: {
            content: '""',
            position: 'absolute',
            top: 0,
            left: '-100%',
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
            transition: 'left 0.5s ease',
          },
          _hover: {
            boxShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.5)',
            transform: 'translateY(-1px)',
            _before: {
              left: '100%',
            },
          },
          _active: {
            transform: 'scale(0.98)',
          },
        }),
      },
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
    },
    MenuButton: {
      baseStyle: {
        borderRadius: borders.radius.lg,
        transition: `all ${transitions.duration.normal} ${transitions.easing.default}`,
        boxSizing: 'border-box',
        _focus: {
          boxShadow: 'none',
        },
        _active: {
          boxShadow: 'none',
        },
      },
      variants: {
        transparent: (props) => ({
          bg: 'transparent',
          color: mode('#172554', '#f0f9ff')(props),
          boxShadow: 'none',
          _focus: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _active: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _hover: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.05)')(props),
          },
        }),
        primary: (props) => ({
          bg: mode(
            'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
            'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
          )(props),
          color: 'white',
          boxShadow: shadows.sm,
          _focus: {
            bg: mode(
              'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
              'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
            )(props),
          },
          _active: {
            bg: mode(
              'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
              'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
            )(props),
          },
          _hover: {
            boxShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.4)',
            bg: mode(
              'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
              'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
            )(props),
            _disabled: {
              bg: mode(
                'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
                'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
              )(props),
            },
          },
        }),
        chakraLinear: (props) => ({
          bg: mode(
            'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
            'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
          )(props),
          color: 'white',
          boxShadow: shadows.sm,
          _focus: {
            bg: mode(
              'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
              'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
            )(props),
          },
          _active: {
            bg: mode(
              'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
              'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
            )(props),
          },
          _hover: {
            boxShadow: '0 10px 20px -5px rgba(2, 132, 199, 0.4)',
            bg: mode(
              'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
              'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)'
            )(props),
          },
        }),
        outline: () => ({
          borderRadius: borders.radius.lg,
        }),
        api: (props) => ({
          bg: mode('#1e293b', '#f0f9ff')(props),
          color: mode('white', '#172554')(props),
          _focus: {
            bg: mode('#1e293b', '#f0f9ff')(props),
          },
          _active: {
            bg: mode('#1e293b', '#f0f9ff')(props),
          },
          _hover: {
            bg: mode('#0f172a', '#e0f2fe')(props),
          },
        }),
        brand: (props) => ({
          bg: mode('#1e40af', '#3b82f6')(props),
          color: 'white',
          _focus: {
            bg: mode('#1e40af', '#3b82f6')(props),
          },
          _active: {
            bg: mode('#1e40af', '#3b82f6')(props),
          },
          _hover: {
            bg: mode('#2563eb', '#60a5fa')(props),
            boxShadow: '0 10px 20px -5px rgba(30, 64, 175, 0.35)',
          },
        }),
        darkBrand: (props) => ({
          bg: mode('#1e3a8a', '#2563eb')(props),
          color: 'white',
          _focus: {
            bg: mode('#172554', '#3b82f6')(props),
          },
          _active: {
            bg: mode('#172554', '#3b82f6')(props),
          },
          _hover: {
            bg: mode('#172554', '#3b82f6')(props),
          },
        }),
        lightBrand: (props) => ({
          bg: mode('#eff6ff', 'rgba(59, 130, 246, 0.1)')(props),
          color: mode('#1e40af', '#60a5fa')(props),
          _focus: {
            bg: mode('#eff6ff', 'rgba(59, 130, 246, 0.1)')(props),
          },
          _active: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.15)')(props),
          },
          _hover: {
            bg: mode('#dbeafe', 'rgba(59, 130, 246, 0.2)')(props),
          },
        }),
        light: (props) => ({
          bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          color: mode('#172554', '#f0f9ff')(props),
          _focus: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _active: {
            bg: mode('#f1f5f9', 'rgba(255,255,255,0.1)')(props),
          },
          _hover: {
            bg: mode('#e2e8f0', 'rgba(255,255,255,0.2)')(props),
          },
        }),
        action: (props) => ({
          fontWeight: '500',
          borderRadius: borders.radius.full,
          bg: mode('#eff6ff', '#3b82f6')(props),
          color: mode('#1e40af', 'white')(props),
          _focus: {
            bg: mode('#eff6ff', '#3b82f6')(props),
          },
          _active: {
            bg: mode('#eff6ff', '#3b82f6')(props),
          },
          _hover: {
            bg: mode('#dbeafe', '#2563eb')(props),
          },
        }),
        setup: (props) => ({
          fontWeight: '500',
          borderRadius: borders.radius.full,
          bg: 'transparent',
          border: '1px solid',
          borderColor: mode('#e2e8f0', 'transparent')(props),
          color: mode('#172554', '#f0f9ff')(props),
          _focus: {
            bg: 'transparent',
          },
          _active: {
            bg: 'transparent',
          },
          _hover: {
            bg: mode('#f1f5f9', '#3b82f6')(props),
          },
        }),
      },
    },
  },
};
