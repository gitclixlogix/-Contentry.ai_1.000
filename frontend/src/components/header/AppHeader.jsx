'use client';
import {
  Box,
  Flex,
  Image,
  useColorModeValue,
  HStack,
} from '@chakra-ui/react';
import NavbarLinksAdmin from '@/components/navbar/NavbarLinksAdmin';
import { SidebarResponsive } from '@/components/sidebar/Sidebar';
import WorkspaceSwitcher from '@/components/workspace/WorkspaceSwitcher';

/**
 * Fixed Full-Width App Header Component
 * Spans the entire viewport width with logo on the far left
 * Includes Workspace Switcher for unified experience
 * Uses Contentry.ai Brand Colors from BrandBook
 */
export default function AppHeader({ routes, user }) {
  // Brand color mode values
  const headerBg = useColorModeValue('white', 'rgba(15, 23, 42, 0.9)'); // Dark Slate with transparency
  const borderColor = useColorModeValue('#e2e8f0', '#334155');
  const shadowColor = useColorModeValue(
    '0px 2px 8px rgba(0, 0, 0, 0.06)',
    '0px 2px 8px rgba(0, 0, 0, 0.3)'
  );
  
  // Logo source based on color mode - from BrandBook guidelines
  // Light mode: Blue Shield + Dark Slate Text
  // Dark mode: Blue Shield + White Text
  const logoSrc = useColorModeValue('/logo-light.png', '/logo-dark.png');

  return (
    <Box
      as="header"
      position="fixed"
      top="0"
      left="0"
      right="0"
      zIndex="1200"
      bg={headerBg}
      borderBottom="1px solid"
      borderColor={borderColor}
      boxShadow={shadowColor}
      px={{ base: 4, md: 6 }}
      py={2}
      backdropFilter="blur(10px)"
    >
      <Flex justify="space-between" align="center" h="56px">
        {/* Left Side: Mobile Menu + Logo */}
        <HStack spacing={4}>
          {/* Mobile Sidebar Toggle */}
          <Box display={{ base: 'block', xl: 'none' }}>
            {user && routes && (
              <SidebarResponsive 
                key={`${user.role}-${user.enterprise_role || 'none'}`} 
                routes={routes} 
              />
            )}
          </Box>

          {/* Logo - Contentry.ai brand logo with color mode switching */}
          <Image
            src={logoSrc}
            alt="Contentry.ai"
            h={{ base: '32px', md: '40px' }}
            objectFit="contain"
          />
        </HStack>

        {/* Right Side: Workspace Switcher + Navigation Links */}
        <HStack spacing={4}>
          {/* Workspace Switcher - Only shows for users with enterprise access */}
          <WorkspaceSwitcher />
          
          {/* User Menu and other navigation */}
          <NavbarLinksAdmin />
        </HStack>
      </Flex>
    </Box>
  );
}
