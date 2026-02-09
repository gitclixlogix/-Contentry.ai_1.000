'use client';

import { Box, Text, Heading, VStack, useColorModeValue, Icon, Tooltip } from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { FaExternalLinkAlt } from 'react-icons/fa';

/**
 * ClickableStat - A clickable statistic component for drill-down navigation
 * 
 * @param {string} label - The stat label
 * @param {number|string} value - The stat value to display
 * @param {string} drillDownUrl - URL to navigate to on click
 * @param {string} colorScheme - Color scheme for the value
 * @param {React.Component} icon - Optional icon component
 * @param {string} helpText - Optional help text below the value
 * @param {string} size - Size variant: 'sm', 'md', 'lg'
 */
export default function ClickableStat({
  label,
  value,
  drillDownUrl,
  colorScheme = 'brand',
  icon: IconComponent,
  helpText,
  size = 'md',
  isClickable = true,
}) {
  const router = useRouter();
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const sizeStyles = {
    sm: {
      value: '2xl',
      label: 'xs',
      padding: 3,
    },
    md: {
      value: '3xl',
      label: 'sm',
      padding: 4,
    },
    lg: {
      value: '4xl',
      label: 'md',
      padding: 5,
    },
  };

  const currentSize = sizeStyles[size];

  const handleClick = () => {
    if (drillDownUrl && isClickable) {
      router.push(drillDownUrl);
    }
  };

  const colorMap = {
    brand: 'brand.500',
    green: 'green.500',
    red: 'red.500',
    yellow: 'yellow.500',
    orange: 'orange.500',
    blue: 'blue.500',
    purple: 'purple.500',
    gray: 'gray.500',
  };

  const valueColor = colorMap[colorScheme] || colorMap.brand;

  return (
    <Tooltip
      label={isClickable && drillDownUrl ? 'Click to view details' : ''}
      isDisabled={!isClickable || !drillDownUrl}
      hasArrow
      placement="top"
    >
      <VStack
        spacing={1}
        align="center"
        p={currentSize.padding}
        cursor={isClickable && drillDownUrl ? 'pointer' : 'default'}
        borderRadius="lg"
        transition="all 0.2s"
        _hover={
          isClickable && drillDownUrl
            ? {
                bg: hoverBg,
                transform: 'translateY(-2px)',
              }
            : {}
        }
        onClick={handleClick}
        role={isClickable && drillDownUrl ? 'button' : undefined}
        tabIndex={isClickable && drillDownUrl ? 0 : undefined}
        onKeyPress={(e) => {
          if (e.key === 'Enter' && isClickable && drillDownUrl) {
            handleClick();
          }
        }}
        position="relative"
      >
        {IconComponent && (
          <Icon as={IconComponent} boxSize={6} color={valueColor} mb={1} />
        )}
        <Text fontSize={currentSize.label} color={textColorSecondary} fontWeight="600">
          {label}
        </Text>
        <Heading size={currentSize.value} color={valueColor} display="flex" alignItems="center" gap={2}>
          {value}
          {isClickable && drillDownUrl && (
            <Icon as={FaExternalLinkAlt} boxSize={3} opacity={0.5} />
          )}
        </Heading>
        {helpText && (
          <Text fontSize="xs" color={textColorSecondary}>
            {helpText}
          </Text>
        )}
      </VStack>
    </Tooltip>
  );
}
