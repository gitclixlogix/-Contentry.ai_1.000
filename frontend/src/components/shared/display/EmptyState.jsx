/**
 * EmptyState - Reusable component for displaying empty data states
 * 
 * Shows a centered message when there's no data to display.
 * Includes optional icon, title, description, and action button.
 * 
 * Props:
 * - icon (IconType): Icon from react-icons to display
 * - title (string): Main heading text
 * - description (string): Secondary description text
 * - action (ReactNode): Optional action button or element
 * - size (string): 'sm', 'md', 'lg' (default: 'md')
 */

import React from 'react';
import { VStack, Icon, Text, Box } from '@chakra-ui/react';
import { FiInbox } from 'react-icons/fi';

export function EmptyState({ 
  icon = FiInbox,
  title = 'No data',
  description,
  action,
  size = 'md',
  py = 12
}) {
  const iconSize = size === 'sm' ? 8 : size === 'lg' ? 16 : 12;
  const titleSize = size === 'sm' ? 'md' : size === 'lg' ? 'xl' : 'lg';
  const descSize = size === 'sm' ? 'sm' : 'md';

  return (
    <VStack 
      spacing={4} 
      py={py} 
      px={6}
      textAlign="center"
    >
      <Box 
        p={4} 
        borderRadius="full" 
        bg="gray.100"
      >
        <Icon 
          as={icon} 
          boxSize={iconSize} 
          color="gray.400"
        />
      </Box>
      <VStack spacing={2}>
        <Text 
          fontSize={titleSize} 
          fontWeight="600" 
          color="gray.700"
        >
          {title}
        </Text>
        {description && (
          <Text 
            fontSize={descSize} 
            color="gray.500"
            maxW="sm"
          >
            {description}
          </Text>
        )}
      </VStack>
      {action && (
        <Box mt={4}>
          {action}
        </Box>
      )}
    </VStack>
  );
}

export default EmptyState;
