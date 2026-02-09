'use client';
import { Box, Flex, Text, Badge, SimpleGrid, useColorModeValue } from '@chakra-ui/react';
import Card from '@/components/card/Card';
import LineChart from '@/components/charts/LineChart';

/**
 * Reusable Revenue Over Time Component
 * @param {Object} data - Payment analytics data with revenue_over_time
 * @param {boolean} isMockData - Flag to show mock data badge
 */
export default function RevenueOverTime({ data, isMockData }) {
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('secondaryGray.600', 'white');

  if (!data || !data.revenue_over_time) return null;

  const chartData = [{
    name: "Revenue",
    data: data.revenue_over_time.data
  }];

  const chartOptions = {
    chart: {
      type: 'line',
      height: 350,
      toolbar: { show: false },
      zoom: { enabled: false }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    colors: ['#1e40af'],
    markers: {
      size: 5,
      colors: ['#1e40af'],
      strokeColors: '#fff',
      strokeWidth: 2
    },
    dataLabels: {
      enabled: false
    },
    xaxis: {
      categories: data.revenue_over_time.labels,
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
        },
        formatter: (value) => `$${value.toLocaleString()}`
      }
    },
    grid: {
      borderColor: 'rgba(163, 174, 208, 0.3)',
      strokeDashArray: 5
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: (value) => `$${value.toLocaleString()}`
      }
    }
  };

  return (
    <Card p="20px">
      <Flex justify="space-between" align="center" mb="20px">
        <Text fontSize="lg" fontWeight="700" color={textColor}>
          Revenue Over Time
        </Text>
        {isMockData && (
          <Badge colorScheme="orange" fontSize="xs">
            MOCK DATA
          </Badge>
        )}
      </Flex>
      <Box h="350px">
        <LineChart chartData={chartData} chartOptions={chartOptions} />
      </Box>
      <SimpleGrid columns={{ base: 1, md: 3 }} gap="20px" mt="20px">
        <Box>
          <Text fontSize="sm" color={textColorSecondary} fontWeight="500">
            Total Revenue
          </Text>
          <Text fontSize="xl" fontWeight="700" color={textColor}>
            ${data.total_revenue.toLocaleString()}
          </Text>
        </Box>
        <Box>
          <Text fontSize="sm" color={textColorSecondary} fontWeight="500">
            Avg Monthly Revenue
          </Text>
          <Text fontSize="xl" fontWeight="700" color={textColor}>
            ${data.avg_monthly_revenue.toLocaleString()}
          </Text>
        </Box>
        <Box>
          <Text fontSize="sm" color={textColorSecondary} fontWeight="500">
            Growth Rate
          </Text>
          <Text fontSize="xl" fontWeight="700" color={data.growth_rate > 0 ? 'green.500' : 'red.500'}>
            {data.growth_rate > 0 ? '+' : ''}{data.growth_rate.toFixed(1)}%
          </Text>
        </Box>
      </SimpleGrid>
    </Card>
  );
}
