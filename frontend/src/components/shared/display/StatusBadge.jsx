/**
 * StatusBadge - Reusable component for displaying status indicators
 * 
 * Displays a status with appropriate color coding.
 * Common statuses: active, inactive, pending, approved, rejected, etc.
 * 
 * Props:
 * - status (string, required): The status value
 * - customColors (object): Override default color mappings
 * - size (string): Badge size - 'sm', 'md', 'lg' (default: 'md')
 * - variant (string): 'solid', 'subtle', 'outline' (default: 'subtle')
 * - showDot (boolean): Show status dot indicator (default: false)
 */

import React from 'react';
import { Badge, HStack, Box } from '@chakra-ui/react';

// Default status color mappings
const DEFAULT_STATUS_COLORS = {
  // Positive statuses
  active: 'green',
  approved: 'green',
  published: 'green',
  completed: 'green',
  success: 'green',
  verified: 'green',
  connected: 'green',
  
  // Warning statuses
  pending: 'yellow',
  draft: 'yellow',
  review: 'yellow',
  processing: 'yellow',
  scheduled: 'yellow',
  
  // Negative statuses
  inactive: 'gray',
  rejected: 'red',
  failed: 'red',
  error: 'red',
  expired: 'red',
  disconnected: 'red',
  cancelled: 'red',
  
  // Info statuses
  new: 'blue',
  info: 'blue',
  
  // Default
  default: 'gray'
};

// Format status text for display
function formatStatus(status) {
  if (!status) return '';
  return status
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function StatusBadge({ 
  status, 
  customColors = {},
  size = 'md',
  variant = 'subtle',
  showDot = false,
  label
}) {
  const normalizedStatus = status?.toLowerCase() || 'default';
  const colorScheme = customColors[normalizedStatus] 
    || DEFAULT_STATUS_COLORS[normalizedStatus] 
    || DEFAULT_STATUS_COLORS.default;

  const displayText = label || formatStatus(status);
  
  const fontSize = size === 'sm' ? 'xs' : size === 'lg' ? 'md' : 'sm';
  const px = size === 'sm' ? 2 : size === 'lg' ? 4 : 3;
  const py = size === 'sm' ? 0.5 : size === 'lg' ? 1.5 : 1;
  const dotSize = size === 'sm' ? '6px' : size === 'lg' ? '10px' : '8px';

  const dotColors = {
    green: 'green.500',
    yellow: 'yellow.500',
    red: 'red.500',
    blue: 'blue.500',
    gray: 'gray.500'
  };

  if (showDot) {
    return (
      <HStack spacing={2}>
        <Box 
          w={dotSize} 
          h={dotSize} 
          borderRadius="full" 
          bg={dotColors[colorScheme] || 'gray.500'}
        />
        <Badge 
          colorScheme={colorScheme}
          variant={variant}
          px={px}
          py={py}
          borderRadius="md"
          fontSize={fontSize}
        >
          {displayText}
        </Badge>
      </HStack>
    );
  }

  return (
    <Badge 
      colorScheme={colorScheme}
      variant={variant}
      px={px}
      py={py}
      borderRadius="md"
      fontSize={fontSize}
    >
      {displayText}
    </Badge>
  );
}

export default StatusBadge;
