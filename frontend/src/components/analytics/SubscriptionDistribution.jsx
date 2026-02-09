'use client';
import { Box, Flex, Text, Badge, SimpleGrid, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';
import BarChart from '@/components/charts/BarChart';

/**
 * Reusable Subscription Distribution Component
 * @param {Object} data - Subscription analytics data
 * @param {boolean} isMockData - Flag to show mock data badge
 */
export default function SubscriptionDistribution({ data, isMockData }) {
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('secondaryGray.600', 'white');

  if (!data || !data.plans) return null;

  const chartData = [{
    name: "Users",
    data: data.user_counts || []
  }];

  const chartOptions = {
    chart: {
      type: 'bar',
      toolbar: { show: false }
    },
    plotOptions: {
      bar: {
        borderRadius: 10,
        columnWidth: '50%'
      }
    },
    dataLabels: {
      enabled: false
    },
    xaxis: {
      categories: (data.plans || []).map(p => {
        const planStr = typeof p === 'string' ? p : (p?.name || String(p));
        return planStr.charAt(0).toUpperCase() + planStr.slice(1);
      }),
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
          fontWeight: '500'
        }
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
          fontWeight: '500'
        }
      }
    },
    grid: {
      borderColor: 'rgba(163, 174, 208, 0.3)',
      strokeDashArray: 5
    },
    colors: ['#1e40af'],
    tooltip: {
      theme: 'dark'
    }
  };

  return (
    <Card p="20px">
      <Flex justify="space-between" align="center" mb="20px">
        <Text fontSize="lg" fontWeight="700" color={textColor}>
          Subscription Plans Distribution
        </Text>
        {isMockData && (
          <Badge colorScheme="orange" fontSize="xs">
            MOCK DATA
          </Badge>
        )}
      </Flex>
      <Box h="350px">
        <BarChart chartData={chartData} chartOptions={chartOptions} />
      </Box>
      <SimpleGrid columns={{ base: 2, md: 4 }} gap="20px" mt="20px">
        {data.plans.map((plan, idx) => (
          <Box key={plan}>
            <Text fontSize="sm" color={textColorSecondary} fontWeight="500" textTransform="capitalize">
              {plan}
            </Text>
            <Text fontSize="xl" fontWeight="700" color={textColor}>
              {data.user_counts[idx]}
            </Text>
          </Box>
        ))}
      </SimpleGrid>
    </Card>
  );
}
