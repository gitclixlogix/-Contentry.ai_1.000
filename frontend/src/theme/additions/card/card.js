import { mode } from '@chakra-ui/theme-tools';
import { borders, shadows, transitions } from '../../designConfig';

const Card = {
  baseStyle: (props) => ({
    p: '20px',
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    position: 'relative',
    borderRadius: borders.radius.xl, // Softer: 18px
    minWidth: '0px',
    wordWrap: 'break-word',
    bg: mode('#ffffff', 'navy.800')(props),
    boxShadow: mode(shadows.card, 'none')(props),
    backgroundClip: 'border-box',
    transition: `all ${transitions.duration.normal} ${transitions.easing.default}`,
    border: '1px solid',
    borderColor: mode('gray.100', 'whiteAlpha.100')(props),
  }),
  variants: {
    // Elevated card with hover effect
    elevated: (props) => ({
      boxShadow: mode(shadows.md, shadows.lg)(props),
      _hover: {
        transform: 'translateY(-2px)',
        boxShadow: mode(shadows.cardHover, shadows.xl)(props),
      },
    }),
    // AI-themed card with subtle gradient
    ai: (props) => ({
      background: mode(
        'linear-gradient(135deg, rgba(139, 92, 246, 0.03) 0%, rgba(124, 58, 237, 0.05) 100%)',
        'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.15) 100%)'
      )(props),
      borderColor: mode('brand.100', 'brand.800')(props),
      _hover: {
        borderColor: mode('brand.200', 'brand.700')(props),
        boxShadow: mode(
          '0 0 20px rgba(139, 92, 246, 0.15)',
          '0 0 20px rgba(139, 92, 246, 0.25)'
        )(props),
      },
    }),
    // Outline card
    outline: (props) => ({
      bg: 'transparent',
      boxShadow: 'none',
      border: '1px solid',
      borderColor: mode('gray.200', 'whiteAlpha.200')(props),
      _hover: {
        borderColor: mode('gray.300', 'whiteAlpha.300')(props),
      },
    }),
    // Filled card with subtle background
    filled: (props) => ({
      bg: mode('gray.50', 'whiteAlpha.50')(props),
      boxShadow: 'none',
      borderColor: 'transparent',
    }),
  },
};

export const CardComponent = {
  components: {
    Card,
  },
};
