/**
 * UserInfoCell - Reusable component for displaying user information
 * 
 * Displays user avatar, name, email/subtitle with optional badge.
 * Use this component in tables, lists, and detail views for consistent user display.
 * 
 * Props:
 * - name (string, required): User's display name
 * - email (string): User's email address
 * - avatar (string): URL to user's avatar image
 * - subtitle (string): Alternative to email for non-user entities
 * - badge (ReactNode): Optional badge element (e.g., role badge)
 * - size (string): Avatar size - 'xs', 'sm', 'md', 'lg' (default: 'sm')
 * - showEmail (boolean): Whether to show email (default: true)
 */

import React from 'react';
import { HStack, VStack, Box, Avatar, Text, Tooltip } from '@chakra-ui/react';

export function UserInfoCell({ 
  name, 
  email, 
  avatar, 
  subtitle, 
  badge,
  size = 'sm',
  showEmail = true,
  onClick,
  isClickable = false
}) {
  const displayText = email || subtitle;
  
  const content = (
    <HStack 
      spacing={3} 
      cursor={isClickable ? 'pointer' : 'default'}
      onClick={onClick}
      _hover={isClickable ? { bg: 'gray.50' } : {}}
      borderRadius="md"
      p={isClickable ? 1 : 0}
    >
      <Avatar 
        size={size} 
        name={name} 
        src={avatar}
        bg="blue.600"
        color="white"
      />
      <Box minW={0} flex={1}>
        <HStack spacing={2} flexWrap="wrap">
          <Text 
            fontWeight="500" 
            fontSize={size === 'xs' ? 'sm' : 'md'}
            noOfLines={1}
          >
            {name}
          </Text>
          {badge}
        </HStack>
        {showEmail && displayText && (
          <Tooltip label={displayText} placement="bottom-start" hasArrow>
            <Text 
              fontSize="sm" 
              color="gray.500" 
              noOfLines={1}
            >
              {displayText}
            </Text>
          </Tooltip>
        )}
      </Box>
    </HStack>
  );

  return content;
}

export default UserInfoCell;
