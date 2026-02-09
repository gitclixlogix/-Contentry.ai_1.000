'use client';
// Chakra imports
import { Flex, Image, useColorModeValue } from '@chakra-ui/react';

import { HSeparator } from '@/components/separator/Separator';

export function SidebarBrand() {
  // Logo source based on color mode - from BrandBook guidelines
  const logoSrc = useColorModeValue('/logo-light.png', '/logo-dark.png');
  
  return (
    <Flex alignItems="center" flexDirection="column">
      <Image src={logoSrc} h="36px" w="auto" maxW="180px" my="24px" alt="Contentry.ai" />
      <HSeparator mb="20px" w="284px" />
    </Flex>
  );
}

export default SidebarBrand;
