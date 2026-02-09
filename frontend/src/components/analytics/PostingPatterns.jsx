'use client';
import { Box, Flex, Text, Badge, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';
import LineChart from '@/components/charts/LineChart';

/**
 * Reusable Posting Patterns Component
 * @param {Object} data - Posting patterns data with hourly_distribution
 * @param {boolean} isMockData - Flag to show mock data badge
 */
export default function PostingPatterns({ data, isMockData }) {
  const textColor = useColorModeValue('navy.700', 'white');

  if (!data || !data.hourly_distribution) return null;

  return (
    <Card p="20px">
      <Flex justify="space-between" align="center" mb="20px">
        <Text fontSize="lg" fontWeight="700" color={textColor}>
          Posting Activity by Time of Day
        </Text>
        {isMockData && (
          <Badge colorScheme="orange" fontSize="xs">
            MOCK DATA
          </Badge>
        )}
      </Flex>
      <Box h="350px">
        <LineChart 
          chartData={[{
            name: "Posts",
            data: data.hourly_distribution.post_counts
          }]}
          chartOptions={{
            chart: { toolbar: { show: false } },
            xaxis: {
              categories: data.hourly_distribution.labels,
              labels: { style: { colors: '#A3AED0', fontSize: '10px' } }
            },
            yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } } },
            stroke: { curve: 'smooth', width: 3 },
            colors: ['#1e40af'],
            markers: { size: 4, colors: '#1e40af' },
            dataLabels: { enabled: false }
          }}
        />
      </Box>
    </Card>
  );
}
