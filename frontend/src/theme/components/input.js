import { mode } from '@chakra-ui/theme-tools';
import { borders, transitions } from '../designConfig';

export const inputStyles = {
  components: {
    Input: {
      baseStyle: {
        field: {
          fontWeight: 400,
          borderRadius: borders.radius.md, // Softer: 10px
          transition: `all ${transitions.duration.fast} ${transitions.easing.default}`,
        },
      },
      variants: {
        main: (props) => ({
          field: {
            bg: mode('transparent', 'navy.800')(props),
            border: '1px solid',
            color: mode('gray.700', 'white')(props),
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            fontSize: 'sm',
            p: '20px',
            _placeholder: { color: 'gray.400' },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.300')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
        }),
        auth: (props) => ({
          field: {
            fontWeight: '500',
            color: mode('gray.700', 'white')(props),
            bg: mode('transparent', 'transparent')(props),
            border: '1px solid',
            borderColor: mode('gray.200', 'rgba(135, 140, 189, 0.3)')(props),
            borderRadius: borders.radius.md,
            _placeholder: {
              color: 'gray.400',
              fontWeight: '400',
            },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.400')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
        }),
        authSecondary: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.300')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
        }),
        search: (props) => ({
          field: {
            border: 'none',
            py: '11px',
            borderRadius: 'inherit',
            _placeholder: { color: 'gray.400' },
          },
        }),
      },
    },
    NumberInput: {
      baseStyle: {
        field: {
          fontWeight: 400,
          borderRadius: borders.radius.md,
        },
      },
      variants: {
        main: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.300')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
        }),
        auth: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
          },
        }),
        authSecondary: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
          },
        }),
        search: () => ({
          field: {
            border: 'none',
            py: '11px',
            borderRadius: 'inherit',
            _placeholder: { color: 'gray.400' },
          },
        }),
      },
    },
    Select: {
      baseStyle: {
        field: {
          fontWeight: 500,
          borderRadius: borders.radius.md,
        },
      },
      variants: {
        main: (props) => ({
          field: {
            bg: mode('transparent', 'navy.800')(props),
            border: '1px solid',
            color: mode('gray.600', 'gray.300')(props),
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.300')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
          icon: {
            color: 'gray.400',
          },
        }),
        mini: (props) => ({
          field: {
            bg: mode('transparent', 'navy.800')(props),
            border: '0px solid transparent',
            fontSize: '0px',
            p: '10px',
            _placeholder: { color: 'gray.400' },
          },
          icon: {
            color: 'gray.400',
          },
        }),
        subtle: () => ({
          box: {
            width: 'unset',
          },
          field: {
            bg: 'transparent',
            border: '0px solid',
            color: 'gray.500',
            borderColor: 'transparent',
            width: 'max-content',
            _placeholder: { color: 'gray.400' },
          },
          icon: {
            color: 'gray.400',
          },
        }),
        transparent: (props) => ({
          field: {
            bg: 'transparent',
            border: '0px solid',
            width: 'min-content',
            color: mode('gray.600', 'gray.400')(props),
            borderColor: 'transparent',
            padding: '0px',
            paddingLeft: '8px',
            paddingRight: '20px',
            fontWeight: '600',
            fontSize: '14px',
            _placeholder: { color: 'gray.400' },
          },
          icon: {
            transform: 'none !important',
            position: 'unset !important',
            width: 'unset',
            color: 'gray.400',
            right: '0px',
          },
        }),
        auth: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
            _hover: {
              borderColor: mode('gray.300', 'whiteAlpha.300')(props),
            },
            _focus: {
              borderColor: 'brand.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
            },
          },
        }),
        authSecondary: (props) => ({
          field: {
            bg: 'transparent',
            border: '1px solid',
            borderColor: mode('gray.200', 'whiteAlpha.200')(props),
            borderRadius: borders.radius.md,
            _placeholder: { color: 'gray.400' },
          },
        }),
        search: () => ({
          field: {
            border: 'none',
            py: '11px',
            borderRadius: 'inherit',
            _placeholder: { color: 'gray.400' },
          },
        }),
      },
    },
    Textarea: {
      baseStyle: {
        borderRadius: borders.radius.md,
        transition: `all ${transitions.duration.fast} ${transitions.easing.default}`,
      },
      variants: {
        main: (props) => ({
          bg: mode('transparent', 'navy.800')(props),
          border: '1px solid',
          borderColor: mode('gray.200', 'whiteAlpha.200')(props),
          borderRadius: borders.radius.md,
          _placeholder: { color: 'gray.400' },
          _hover: {
            borderColor: mode('gray.300', 'whiteAlpha.300')(props),
          },
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
        }),
      },
    },
  },
};
