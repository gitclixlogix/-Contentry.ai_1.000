/**
 * InfoRow - Reusable component for displaying label-value pairs
 * 
 * Creates a horizontal layout with label on the left and value on the right.
 * Commonly used in detail views, summaries, and settings pages.
 * 
 * Props:
 * - label (string, required): The label text
 * - value (ReactNode, required): The value to display (can be text or component)
 * - icon (IconType): Optional icon from react-icons to display before label
 * - valueColor (string): Color for the value text
 * - labelColor (string): Color for the label text (default: gray.500)
 * - py (number): Vertical padding (default: 1)
 * - divider (boolean): Show bottom divider (default: false)
 */

import React from 'react';
import { HStack, Text, Icon, Divider, VStack } from '@chakra-ui/react';

export function InfoRow({ 
  label, 
  value, 
  icon, 
  valueColor,
  labelColor = 'gray.500',
  py = 1,
  divider = false,
  fontSize = 'sm'
}) {
  const row = (
    <HStack justify="space-between" py={py} w="100%">
      <HStack color={labelColor} spacing={2}>
        {icon && <Icon as={icon} boxSize={4} />}
        <Text fontSize={fontSize}>{label}</Text>
      </HStack>
      {typeof value === 'string' || typeof value === 'number' ? (
        <Text fontWeight="500" color={valueColor} fontSize={fontSize}>
          {value}
        </Text>
      ) : (
        value
      )}
    </HStack>
  );

  if (divider) {
    return (
      <VStack spacing={0} w="100%" align="stretch">
        {row}
        <Divider />
      </VStack>
    );
  }

  return row;
}

export default InfoRow;
