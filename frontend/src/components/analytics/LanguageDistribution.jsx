'use client';
import { Flex, Text, Badge, VStack, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';

/**
 * Reusable Language Distribution Component
 * @param {Object} languages - Language data object { language: count }
 * @param {boolean} isMockData - Flag to show mock data badge
 * @param {string} maxHeight - Maximum height with scroll (default: 450px)
 */
export default function LanguageDistribution({ languages, isMockData, maxHeight = '450px' }) {
  const textColor = useColorModeValue('navy.700', 'white');
  const languageItemBg = useColorModeValue('gray.50', 'whiteAlpha.50');

  if (!languages) return null;

  // Handle both object format { "English": 10 } and array format [{ language: "English", count: 10 }]
  const languageData = Array.isArray(languages)
    ? languages
    : Object.entries(languages).map(([lang, count]) => ({
        language: lang,
        count: typeof count === 'object' ? count.count : count,
        percentage: typeof count === 'object' ? count.percentage : null
      }));

  return (
    <Card p="20px">
      <Flex justify="space-between" align="center" mb="20px">
        <Text fontSize="lg" fontWeight="700" color={textColor}>
          Language Distribution
        </Text>
        {isMockData && (
          <Badge colorScheme="orange" fontSize="xs">
            MOCK DATA
          </Badge>
        )}
      </Flex>
      <VStack align="stretch" spacing={3} maxH={maxHeight} overflowY="auto">
        {languageData.map((item, idx) => (
          <Flex key={item.language || idx} justify="space-between" p={3} bg={languageItemBg} borderRadius="md">
            <Text fontSize="sm" fontWeight="600" color={textColor}>{item.language}</Text>
            <Badge colorScheme="blue" fontSize="sm">{item.count} users</Badge>
          </Flex>
        ))}
      </VStack>
    </Card>
  );
}
