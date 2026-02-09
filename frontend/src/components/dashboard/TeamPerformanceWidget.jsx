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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Progress,
  Tooltip,
} from '@chakra-ui/react';
import { FaUsers, FaChartBar, FaExternalLinkAlt } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { createAuthenticatedAxios } from '@/lib/api';
import ExportButton from './ExportButton';

const BarChart = dynamic(() => import('@/components/charts/BarChart'), { ssr: false });

export default function TeamPerformanceWidget({ userId, dateRange, customStart, customEnd }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    fetchTeamPerformance();
  }, [userId, dateRange, customStart, customEnd]);

  const fetchTeamPerformance = async () => {
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      let url = `/dashboard/team-performance?date_range=${dateRange || 'last_30_days'}`;
      
      if (customStart && customEnd) {
        url += `&custom_start=${customStart}&custom_end=${customEnd}`;
      }

      const response = await api.get(url, {
        headers: {
          'x-user-id': userId,
        },
      });

      setData(response.data);
    } catch (err) {
      if (err.response?.status === 403) {
        // User doesn't have permission - hide widget
        setData(null);
        setLoading(false);
        return;
      }
      console.error('Team performance error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // If no permission or no data, don't render
  if (!loading && !data) return null;

  // Chart configurations
  const volumeChartData = data?.charts?.content_volume ? [{
    name: 'Content Volume',
    data: data.charts.content_volume.data,
  }] : [];

  const volumeChartOptions = {
    chart: { type: 'bar', toolbar: { show: false } },
    plotOptions: { bar: { borderRadius: 4, horizontal: true } },
    colors: ['#4318FF'],
    xaxis: { categories: data?.charts?.content_volume?.labels || [] },
    dataLabels: { enabled: true },
  };

  const scoreChartData = data?.charts?.compliance_scores ? [{
    name: 'Avg Score',
    data: data.charts.compliance_scores.data,
  }] : [];

  const scoreChartOptions = {
    chart: { type: 'bar', toolbar: { show: false } },
    plotOptions: { bar: { borderRadius: 4, horizontal: true } },
    colors: ['#01B574'],
    xaxis: { categories: data?.charts?.compliance_scores?.labels || [], max: 100 },
    dataLabels: { enabled: true, formatter: (val) => `${val}%` },
  };

  const handleMemberClick = (drillDownUrl) => {
    if (drillDownUrl) {
      router.push(drillDownUrl);
    }
  };

  return (
    <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaUsers} boxSize={5} color={brandColor} />
            <Box>
              <Heading size="md" color={textColor}>
                {t('dashboard.teamPerformance.title', 'Team Performance')}
              </Heading>
              <Text fontSize="sm" color={textColorSecondary}>
                {t('dashboard.teamPerformance.description', 'Content volume and compliance by team member')}
              </Text>
            </Box>
          </HStack>
          <ExportButton 
            widgetType="team-performance" 
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
          <VStack spacing={6} align="stretch">
            {/* Charts Row */}
            <Flex direction={{ base: 'column', lg: 'row' }} gap={6}>
              {/* Content Volume Chart */}
              <Box flex={1}>
                <Text fontSize="sm" fontWeight="600" color={textColor} mb={3}>
                  {t('dashboard.teamPerformance.contentVolumeByMember', 'Content Volume by Team Member')}
                </Text>
                <Box h="200px">
                  {volumeChartData.length > 0 && volumeChartData[0].data.length > 0 ? (
                    <BarChart chartData={volumeChartData} chartOptions={volumeChartOptions} />
                  ) : (
                    <Flex align="center" justify="center" h="100%" color={textColorSecondary}>
                      {t('dashboard.teamPerformance.noDataAvailable', 'No data available')}
                    </Flex>
                  )}
                </Box>
              </Box>

              {/* Compliance Score Chart */}
              <Box flex={1}>
                <Text fontSize="sm" fontWeight="600" color={textColor} mb={3}>
                  {t('dashboard.teamPerformance.avgComplianceByMember', 'Average Compliance Score by Team Member')}
                </Text>
                <Box h="200px">
                  {scoreChartData.length > 0 && scoreChartData[0].data.length > 0 ? (
                    <BarChart chartData={scoreChartData} chartOptions={scoreChartOptions} />
                  ) : (
                    <Flex align="center" justify="center" h="100%" color={textColorSecondary}>
                      {t('dashboard.teamPerformance.noDataAvailable', 'No data available')}
                    </Flex>
                  )}
                </Box>
              </Box>
            </Flex>

            {/* Team Member Table */}
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>{t('dashboard.teamPerformance.teamMember', 'Team Member')}</Th>
                    <Th isNumeric>{t('dashboard.teamPerformance.contentVolume', 'Content Volume')}</Th>
                    <Th isNumeric>{t('dashboard.teamPerformance.avgCompliance', 'Avg Compliance')}</Th>
                    <Th>{t('dashboard.teamPerformance.performance', 'Performance')}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {(data?.team_performance || []).slice(0, 10).map((member, idx) => (
                    <Tr
                      key={member.user_id}
                      cursor="pointer"
                      _hover={{ bg: hoverBg }}
                      onClick={() => handleMemberClick(member.drill_down_url)}
                    >
                      <Td>
                        <HStack>
                          <Text fontWeight="500">{member.name}</Text>
                          <Icon as={FaExternalLinkAlt} boxSize={2.5} color="gray.400" />
                        </HStack>
                      </Td>
                      <Td isNumeric>
                        <Badge colorScheme="brand">{member.content_volume}</Badge>
                      </Td>
                      <Td isNumeric>
                        <Badge colorScheme={member.avg_compliance_score >= 80 ? 'green' : member.avg_compliance_score >= 60 ? 'yellow' : 'red'}>
                          {member.avg_compliance_score}%
                        </Badge>
                      </Td>
                      <Td>
                        <Progress 
                          value={member.avg_compliance_score} 
                          size="sm" 
                          colorScheme={member.avg_compliance_score >= 80 ? 'green' : member.avg_compliance_score >= 60 ? 'yellow' : 'red'}
                          borderRadius="full"
                          maxW="100px"
                        />
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          </VStack>
        )}
      </CardBody>
    </Card>
  );
}
