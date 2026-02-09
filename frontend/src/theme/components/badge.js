import { mode } from '@chakra-ui/theme-tools';
import { borders, transitions } from '../designConfig';

export const badgeStyles = {
  components: {
    Badge: {
      baseStyle: {
        borderRadius: borders.radius.full, // Pill shape
        lineHeight: '100%',
        padding: '6px',
        paddingLeft: '10px',
        paddingRight: '10px',
        fontWeight: '500',
        fontSize: '0.75rem',
        textTransform: 'none',
        transition: `all ${transitions.duration.fast} ${transitions.easing.default}`,
      },
      variants: {
        outline: (props) => ({
          borderRadius: borders.radius.full,
          border: '1px solid',
          bg: 'transparent',
        }),
        brand: (props) => ({
          bg: mode('brand.500', 'brand.400')(props),
          color: 'white',
          _focus: {
            bg: mode('brand.600', 'brand.500')(props),
          },
          _active: {
            bg: mode('brand.600', 'brand.500')(props),
          },
          _hover: {
            bg: mode('brand.600', 'brand.500')(props),
          },
        }),
        subtle: (props) => ({
          bg: mode('brand.50', 'brand.900')(props),
          color: mode('brand.700', 'brand.200')(props),
        }),
        success: (props) => ({
          bg: mode('green.50', 'green.900')(props),
          color: mode('green.700', 'green.200')(props),
        }),
        warning: (props) => ({
          bg: mode('orange.50', 'orange.900')(props),
          color: mode('orange.700', 'orange.200')(props),
        }),
        error: (props) => ({
          bg: mode('red.50', 'red.900')(props),
          color: mode('red.700', 'red.200')(props),
        }),
        info: (props) => ({
          bg: mode('blue.50', 'blue.900')(props),
          color: mode('blue.700', 'blue.200')(props),
        }),
        // AI-themed badge with subtle gradient
        ai: (props) => ({
          bg: mode(
            'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)',
            'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%)'
          )(props),
          color: mode('brand.700', 'brand.200')(props),
          fontWeight: '600',
        }),
      },
    },
  },
};
