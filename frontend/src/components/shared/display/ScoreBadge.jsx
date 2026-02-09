/**
 * ScoreBadge - Reusable component for displaying scores with color coding
 * 
 * Displays a score value with automatic color coding based on thresholds.
 * Green for good, yellow for warning, red for low scores.
 * 
 * Props:
 * - score (number, required): The score value to display
 * - max (number): Maximum score value (default: 100)
 * - thresholds (object): Custom thresholds { good: 70, warning: 50 }
 * - showMax (boolean): Whether to show "/max" suffix (default: true)
 * - size (string): Badge size - 'sm', 'md', 'lg' (default: 'md')
 * - variant (string): 'solid' or 'subtle' (default: 'subtle')
 */

import React from 'react';
import { Badge, Text, HStack, Box } from '@chakra-ui/react';

export function ScoreBadge({ 
  score, 
  max = 100, 
  thresholds = { good: 70, warning: 50 },
  showMax = true,
  size = 'md',
  variant = 'subtle',
  label
}) {
  const colorScheme = score >= thresholds.good 
    ? 'green' 
    : score >= thresholds.warning 
    ? 'yellow' 
    : 'red';

  const fontSize = size === 'sm' ? 'xs' : size === 'lg' ? 'md' : 'sm';
  const px = size === 'sm' ? 2 : size === 'lg' ? 4 : 3;
  const py = size === 'sm' ? 0.5 : size === 'lg' ? 1.5 : 1;

  return (
    <HStack spacing={2}>
      {label && (
        <Text fontSize={fontSize} color="gray.500">
          {label}
        </Text>
      )}
      <Badge 
        colorScheme={colorScheme} 
        variant={variant}
        px={px}
        py={py}
        borderRadius="md"
        fontSize={fontSize}
        fontWeight="600"
      >
        {Math.round(score)}{showMax && `/${max}`}
      </Badge>
    </HStack>
  );
}

// Variant that shows a progress-like indicator
export function ScoreIndicator({ 
  score, 
  max = 100, 
  thresholds = { good: 70, warning: 50 },
  size = 'md',
  showLabel = true
}) {
  const colorScheme = score >= thresholds.good 
    ? 'green' 
    : score >= thresholds.warning 
    ? 'yellow' 
    : 'red';
  
  const colors = {
    green: { bg: 'green.100', fill: 'green.500' },
    yellow: { bg: 'yellow.100', fill: 'yellow.500' },
    red: { bg: 'red.100', fill: 'red.500' }
  };

  const width = size === 'sm' ? '60px' : size === 'lg' ? '120px' : '80px';
  const height = size === 'sm' ? '6px' : size === 'lg' ? '10px' : '8px';

  return (
    <HStack spacing={2}>
      <Box 
        w={width} 
        h={height} 
        bg={colors[colorScheme].bg} 
        borderRadius="full"
        overflow="hidden"
      >
        <Box 
          w={`${(score / max) * 100}%`} 
          h="100%" 
          bg={colors[colorScheme].fill}
          borderRadius="full"
        />
      </Box>
      {showLabel && (
        <Text fontSize="sm" fontWeight="500" color={colors[colorScheme].fill}>
          {Math.round(score)}
        </Text>
      )}
    </HStack>
  );
}

export default ScoreBadge;
