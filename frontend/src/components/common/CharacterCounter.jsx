'use client';
import { HStack, Text, Progress, Box } from '@chakra-ui/react';
import { useColorModeValue } from '@chakra-ui/react';

/**
 * Real-time character counter with visual progress indicator
 * 
 * @param {number} current - Current character count
 * @param {number} limit - Maximum character limit (null for no limit)
 * @param {boolean} showProgress - Show progress bar
 * @param {string} size - 'sm', 'md', or 'lg'
 */
export default function CharacterCounter({ 
  current = 0, 
  limit = null, 
  showProgress = true,
  size = 'sm'
}) {
  const isOverLimit = limit && current > limit;
  const isNearLimit = limit && current > limit * 0.9;
  const percentage = limit ? Math.min((current / limit) * 100, 100) : 0;
  
  // Colors
  const normalColor = useColorModeValue('gray.500', 'gray.400');
  const warningColor = useColorModeValue('orange.500', 'orange.400');
  const errorColor = useColorModeValue('red.500', 'red.400');
  const successColor = useColorModeValue('green.500', 'green.400');
  
  const getColor = () => {
    if (isOverLimit) return errorColor;
    if (isNearLimit) return warningColor;
    if (current > 0) return successColor;
    return normalColor;
  };
  
  const getProgressColor = () => {
    if (isOverLimit) return 'red';
    if (isNearLimit) return 'orange';
    return 'blue';
  };
  
  const fontSizeMap = {
    sm: 'xs',
    md: 'sm',
    lg: 'md'
  };
  
  const fontSize = fontSizeMap[size] || 'xs';

  if (!limit) {
    return (
      <Text fontSize={fontSize} color={normalColor}>
        {current.toLocaleString()} characters
      </Text>
    );
  }

  return (
    <Box w="full">
      <HStack justify="space-between" mb={showProgress ? 1 : 0}>
        <Text 
          fontSize={fontSize} 
          fontWeight={isOverLimit ? 'bold' : 'normal'}
          color={getColor()}
        >
          {current.toLocaleString()} / {limit.toLocaleString()}
          {isOverLimit && (
            <Text as="span" color={errorColor} ml={2}>
              ({(current - limit).toLocaleString()} over limit!)
            </Text>
          )}
        </Text>
        
        {!isOverLimit && limit && (
          <Text fontSize={fontSize} color={normalColor}>
            {(limit - current).toLocaleString()} remaining
          </Text>
        )}
      </HStack>
      
      {showProgress && (
        <Progress 
          value={percentage} 
          size="xs" 
          colorScheme={getProgressColor()}
          borderRadius="full"
          bg={useColorModeValue('gray.100', 'gray.700')}
        />
      )}
    </Box>
  );
}

/**
 * Inline character counter for compact spaces
 */
export function InlineCharacterCounter({ current = 0, limit = null }) {
  const isOverLimit = limit && current > limit;
  const isNearLimit = limit && current > limit * 0.9;
  
  const normalColor = useColorModeValue('gray.500', 'gray.400');
  const warningColor = useColorModeValue('orange.500', 'orange.400');
  const errorColor = useColorModeValue('red.500', 'red.400');
  
  const getColor = () => {
    if (isOverLimit) return errorColor;
    if (isNearLimit) return warningColor;
    return normalColor;
  };

  if (!limit) {
    return <Text fontSize="xs" color={normalColor}>{current}</Text>;
  }

  return (
    <Text 
      fontSize="xs" 
      fontWeight={isOverLimit ? 'bold' : 'normal'}
      color={getColor()}
    >
      {current} / {limit}
    </Text>
  );
}
