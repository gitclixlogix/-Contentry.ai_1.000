'use client';
import { Box, SimpleGrid, Text, Badge, Flex, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';
import BarChart from '@/components/charts/BarChart';

/**
 * Reusable Content Quality Component
 * @param {Object} data - Content quality data
 * @param {boolean} isMockData - Flag to show mock data badge
 */
export default function ContentQuality({ data, isMockData }) {
  const textColor = useColorModeValue('navy.700', 'white');

  if (!data) return null;

  return (
    <SimpleGrid columns={{ base: 1, md: 2, xl: 2 }} gap="20px">
      <Card p="20px">
        <Flex justify="space-between" align="center" mb="20px">
          <Text fontSize="lg" fontWeight="700" color={textColor}>
            Content Quality Overview
          </Text>
          {isMockData && (
            <Badge colorScheme="orange" fontSize="xs">
              MOCK DATA
            </Badge>
          )}
        </Flex>
        <Box h="300px">
          <BarChart 
            chartData={[{
              name: "Quality Score",
              data: [
                data.avg_compliance_score || 0,
                data.avg_accuracy_score || 0,
                data.avg_cultural_score || 0
              ]
            }]}
            chartOptions={{
              chart: { toolbar: { show: false } },
              xaxis: {
                categories: ['Compliance', 'Accuracy', 'Cultural'],
                labels: { style: { colors: '#A3AED0', fontSize: '12px' } }
              },
              yaxis: { 
                max: 100,
                labels: { style: { colors: '#A3AED0', fontSize: '12px' } }
              },
              plotOptions: {
                bar: { borderRadius: 8, columnWidth: '40%' }
              },
              colors: ['#1e40af'],
              dataLabels: { enabled: false }
            }}
          />
        </Box>
      </Card>

      <Card p="20px">
        <Flex justify="space-between" align="center" mb="20px">
          <Text fontSize="lg" fontWeight="700" color={textColor}>
            Flagged Content
          </Text>
          {isMockData && (
            <Badge colorScheme="orange" fontSize="xs">
              MOCK DATA
            </Badge>
          )}
        </Flex>
        <Box h="300px">
          <BarChart 
            chartData={[{
              name: "Count",
              data: data.flagged_breakdown ? [
                data.flagged_breakdown.high || 0,
                data.flagged_breakdown.medium || 0,
                data.flagged_breakdown.low || 0
              ] : [0, 0, 0]
            }]}
            chartOptions={{
              chart: { toolbar: { show: false } },
              xaxis: {
                categories: ['High Risk', 'Medium Risk', 'Low Risk'],
                labels: { style: { colors: '#A3AED0', fontSize: '12px' } }
              },
              yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } } },
              plotOptions: {
                bar: { borderRadius: 8, columnWidth: '40%' }
              },
              colors: ['#FF5733'],
              dataLabels: { enabled: false }
            }}
          />
        </Box>
      </Card>
    </SimpleGrid>
  );
}
