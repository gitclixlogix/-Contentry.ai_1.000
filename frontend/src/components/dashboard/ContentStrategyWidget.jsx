'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Flex,
  VStack,
  HStack,
  useColorModeValue,
  Spinner,
  Icon,
  SimpleGrid,
} from '@chakra-ui/react';
import { FaChartPie, FaExternalLinkAlt } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { getApiUrl, createAuthenticatedAxios } from '@/lib/api';
import ExportButton from './ExportButton';

const PieChart = dynamic(() => import('@/components/charts/PieChart'), { ssr: false });

export default function ContentStrategyWidget({ userId, dateRange, customStart, customEnd }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');

  useEffect(() => {
    fetchContentStrategy();
  }, [userId, dateRange, customStart, customEnd]);

  const fetchContentStrategy = async () => {
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      let url = `/dashboard/content-strategy?date_range=${dateRange || 'last_30_days'}`;
      
      if (customStart && customEnd) {
        url += `&custom_start=${customStart}&custom_end=${customEnd}`;
      }

      const response = await api.get(url, {
        headers: {
          'x-user-id': userId,
        },
      });

      // Axios returns data directly in response.data
      setData(response.data);
    } catch (err) {
      console.error('Content strategy error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Platform colors mapping
  const platformColors = {
    twitter: '#1DA1F2',
    facebook: '#4267B2',
    linkedin: '#0A66C2',
    instagram: '#E4405F',
    tiktok: '#000000',
    pinterest: '#E60023',
    youtube: '#FF0000',
    threads: '#000000',
    unspecified: '#718096',
  };

  // Chart configurations for platforms
  const platformChartData = data?.posts_by_platform?.chart?.data || [];
  const platformChartOptions = {
    chart: { type: 'pie' },
    labels: data?.posts_by_platform?.chart?.labels || [],
    colors: (data?.posts_by_platform?.chart?.labels || []).map(
      label => platformColors[label.toLowerCase()] || '#4318FF'
    ),
    legend: {
      position: 'bottom',
      fontSize: '12px',
    },
    dataLabels: {
      enabled: true,
      formatter: (val, opts) => {
        const name = opts.w.globals.labels[opts.seriesIndex];
        return `${Math.round(val)}%`;
      },
    },
    tooltip: {
      y: {
        formatter: (val) => `${val} posts`,
      },
    },
  };

  // Chart configurations for profiles
  const profileChartData = data?.posts_by_profile?.chart?.data || [];
  const profileChartOptions = {
    chart: { type: 'pie' },
    labels: data?.posts_by_profile?.chart?.labels || [],
    colors: ['#4318FF', '#01B574', '#FFB547', '#FF6B6B', '#845EF7', '#22D3EE'],
    legend: {
      position: 'bottom',
      fontSize: '12px',
    },
    dataLabels: {
      enabled: true,
      formatter: (val) => `${Math.round(val)}%`,
    },
    tooltip: {
      y: {
        formatter: (val) => `${val} posts`,
      },
    },
  };

  const handleItemClick = (drillDownUrl) => {
    if (drillDownUrl) {
      router.push(drillDownUrl);
    }
  };

  return (
    <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaChartPie} boxSize={5} color={brandColor} />
            <Box>
              <Heading size="md" color={textColor}>
                {t('dashboard.contentStrategy.title', 'Content Strategy Insights')}
              </Heading>
              <Text fontSize="sm" color={textColorSecondary}>
                {t('dashboard.contentStrategy.description', 'Posts distribution by platform and strategic profile')}
              </Text>
            </Box>
          </HStack>
          <ExportButton 
            widgetType="content-strategy" 
            dateRange={dateRange}
            customStart={customStart}
            customEnd={customEnd}
          />
        </Flex>
      </CardHeader>
      <CardBody>
        {loading ? (
          <Flex justify="center" py={10}>
            <Spinner size="lg" color="brand.500" />
          </Flex>
        ) : error ? (
          <Text color="red.500" textAlign="center" py={4}>{error}</Text>
        ) : (
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* Posts by Platform */}
            <Box>
              <Text fontSize="sm" fontWeight="600" color={textColor} mb={3} textAlign="center">
                {t('dashboard.contentStrategy.postsByPlatform', 'Posts by Platform')}
              </Text>
              <Box h="250px">
                {platformChartData.length > 0 ? (
                  <PieChart chartData={platformChartData} chartOptions={platformChartOptions} />
                ) : (
                  <Flex align="center" justify="center" h="100%" color={textColorSecondary}>
                    {t('dashboard.contentStrategy.noPlatformData', 'No platform data available')}
                  </Flex>
                )}
              </Box>
              {/* Platform list with click-through */}
              <VStack spacing={1} mt={3} align="stretch">
                {(data?.posts_by_platform?.data || []).slice(0, 5).map((item) => (
                  <Flex
                    key={item.platform}
                    justify="space-between"
                    align="center"
                    px={3}
                    py={1}
                    borderRadius="md"
                    cursor="pointer"
                    _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
                    onClick={() => handleItemClick(item.drill_down_url)}
                  >
                    <HStack>
                      <Box
                        w={3}
                        h={3}
                        borderRadius="full"
                        bg={platformColors[item.platform.toLowerCase()] || '#4318FF'}
                      />
                      <Text fontSize="sm">{item.platform}</Text>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="600">{item.count}</Text>
                      <Icon as={FaExternalLinkAlt} boxSize={2} color="gray.400" />
                    </HStack>
                  </Flex>
                ))}
              </VStack>
            </Box>

            {/* Posts by Strategic Profile */}
            <Box>
              <Text fontSize="sm" fontWeight="600" color={textColor} mb={3} textAlign="center">
                {t('dashboard.contentStrategy.postsByProfile', 'Posts by Strategic Profile')}
              </Text>
              <Box h="250px">
                {profileChartData.length > 0 ? (
                  <PieChart chartData={profileChartData} chartOptions={profileChartOptions} />
                ) : (
                  <Flex align="center" justify="center" h="100%" color={textColorSecondary}>
                    {t('dashboard.contentStrategy.noProfileData', 'No profile data available')}
                  </Flex>
                )}
              </Box>
              {/* Profile list with click-through */}
              <VStack spacing={1} mt={3} align="stretch">
                {(data?.posts_by_profile?.data || []).slice(0, 5).map((item, idx) => (
                  <Flex
                    key={item.profile}
                    justify="space-between"
                    align="center"
                    px={3}
                    py={1}
                    borderRadius="md"
                    cursor="pointer"
                    _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
                    onClick={() => handleItemClick(item.drill_down_url)}
                  >
                    <HStack>
                      <Box
                        w={3}
                        h={3}
                        borderRadius="full"
                        bg={['#4318FF', '#01B574', '#FFB547', '#FF6B6B', '#845EF7'][idx % 5]}
                      />
                      <Text fontSize="sm" isTruncated maxW="150px">{item.profile}</Text>
                    </HStack>
                    <HStack>
                      <Text fontSize="sm" fontWeight="600">{item.count}</Text>
                      <Icon as={FaExternalLinkAlt} boxSize={2} color="gray.400" />
                    </HStack>
                  </Flex>
                ))}
              </VStack>
            </Box>
          </SimpleGrid>
        )}
      </CardBody>
    </Card>
  );
}
