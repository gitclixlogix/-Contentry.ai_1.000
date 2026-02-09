'use client';
import { Box, Flex, Text, Badge, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';
import WorldMap from '@/components/charts/WorldMap';

/**
 * Reusable Geographic Distribution Map Component
 * @param {Object} data - Country data object { countryCode: count }
 * @param {Object} countryDetails - Optional detailed country information
 * @param {boolean} isMockData - Flag to show mock data badge
 * @param {string} height - Map height (default: 450px)
 */
export default function GeographicMap({ data, countryDetails, isMockData, height = '450px' }) {
  const textColor = useColorModeValue('navy.700', 'white');

  return (
    <Card p="20px">
      <Flex justify="space-between" align="center" mb="20px">
        <Text fontSize="lg" fontWeight="700" color={textColor}>
          Geographic Distribution (Interactive)
        </Text>
        {isMockData && (
          <Badge colorScheme="orange" fontSize="xs">
            MOCK DATA
          </Badge>
        )}
      </Flex>
      <Box>
        <WorldMap 
          data={data}
          countryDetails={countryDetails || {}}
          height={height}
        />
      </Box>
    </Card>
  );
}
