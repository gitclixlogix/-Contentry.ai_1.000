import { Flex, Image, Box, useColorModeValue } from '@chakra-ui/react';

/**
 * Reusable Contentry.ai Logo Component
 * Used across authentication pages and other branding locations
 * Updated to official brand logos from BrandBook (December 2025)
 * 
 * Logo files have TRANSPARENT backgrounds:
 * - logo-light.png: Blue shield + Dark text (for light backgrounds)
 * - logo-dark.png: Blue shield + White text (for dark backgrounds)
 */
export default function ContentryLogo({ showText = false, size = 'md', variant = 'auto' }) {
  // Responsive logo sizes - scales with screen size
  const logoSizes = {
    xs: { base: '24px', sm: '28px', md: '32px' },
    sm: { base: '28px', sm: '32px', md: '36px' },
    md: { base: '32px', sm: '36px', md: '40px' },
    lg: { base: '40px', sm: '48px', md: '56px' }
  };

  const currentSize = logoSizes[size] || logoSizes.md;

  // Select logo based on color mode
  // Light mode: Use logo with dark text
  // Dark mode: Use logo with white text
  const autoLogo = useColorModeValue('/logo-light.png', '/logo-dark.png');
  
  // Allow forcing a specific variant
  const logoSrc = variant === 'light' 
    ? '/logo-light.png' 
    : variant === 'dark' 
      ? '/logo-dark.png' 
      : autoLogo;

  return (
    <Flex 
      align="center" 
      justify="center"
      w="full"
      maxW="100%"
    >
      <Image 
        src={logoSrc}
        alt="Contentry.ai Logo"
        h={currentSize}
        objectFit="contain"
        flexShrink={0}
      />
    </Flex>
  );
}
