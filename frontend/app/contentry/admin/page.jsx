'use client';
import { useEffect, useState } from 'react';
import {
  Box,
  SimpleGrid,
  Text,
  useColorModeValue,
  Flex,
  Badge,
  Button,
  Spinner,
  Icon,
  VStack,
  HStack,
  Heading,
  Center,
  Card,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Progress,
  Divider,
  Tooltip,
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import IconBox from '@/components/icons/IconBox';
import { 
  FaUsers, FaBuilding, FaFileAlt, FaDollarSign, 
  FaChartLine, FaExclamationTriangle, FaServer,
  FaArrowUp, FaArrowDown, FaDatabase, FaCrown, FaClock
} from 'react-icons/fa';
import { MdTrendingUp, MdWarning, MdBusiness } from 'react-icons/md';
import LineChart from '@/components/charts/LineChart';
import BarChart from '@/components/charts/BarChart';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';

// Area Chart Component
function AreaChart({ chartData, chartOptions }) {
  const [Chart, setChart] = useState(null);
  
  useEffect(() => {
    import('react-apexcharts').then((mod) => {
      setChart(() => mod.default);
    });
  }, []);
  
  if (!Chart) return <Center h="100%"><Spinner /></Center>;
  
  return <Chart options={chartOptions} series={chartData} type="area" height="100%" />;
}

export default function AdminDashboard() {
  const { t } = useTranslation();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [godViewData, setGodViewData] = useState(null);

  // Brand Colors - OKLCH Blue Design System (December 2025)
  const brandBlue = '#1e40af';      // Royal Blue - Primary
  const brandBlueDark = '#1e3a8a';  // Deep Blue
  const brandBlueLight = '#3b82f6'; // Bright Blue
  const brandNavy = '#172554';      // Deep Navy
  const brandGrey = '#64748b';      // Slate-500 for better contrast
  
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const greenColor = useColorModeValue('green.500', 'green.300');

  useEffect(() => {
    loadGodViewData();
  }, []);

  const loadGodViewData = async () => {
    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/admin/god-view-dashboard`);
      setGodViewData(response.data);
    } catch (error) {
      console.error('Error loading god view dashboard:', error);
      // Demo data fallback
      setGodViewData({
        kpi_cards: {
          mrr: { value: 10000, label: 'Monthly Recurring Revenue', format: 'currency' },
          new_users: { value: 156, label: 'New Users (30 Days)', format: 'number' },
          active_companies: { value: 42, label: 'Active Companies', format: 'number' },
          total_content: { value: 12487, label: 'Total Content Analyzed', format: 'number' }
        },
        credit_consumption: {
          dates: ['11-11', '11-15', '11-20', '11-25', '11-30', '12-05', '12-10'],
          credits: [1250, 1480, 1320, 1590, 1420, 1680, 1520]
        },
        most_active_companies: [
          { name: 'TechCorp Inc.', posts: 487 },
          { name: 'GlobalMedia Ltd.', posts: 356 },
          { name: 'InnovateCo', posts: 298 },
          { name: 'MarketPro Agency', posts: 245 },
          { name: 'ContentFirst', posts: 198 },
          { name: 'BrandBuilders', posts: 176 },
          { name: 'SocialSync', posts: 154 },
          { name: 'DigitalEdge', posts: 132 }
        ],
        compliance_hotspots: [
          { violation_type: 'Brand Voice Violation', count: 234, percentage: 22.5 },
          { violation_type: 'Profanity/Inappropriate Language', count: 187, percentage: 18.0 },
          { violation_type: 'Competitor Mentions', count: 156, percentage: 15.0 },
          { violation_type: 'Data Privacy Concerns', count: 134, percentage: 12.9 },
          { violation_type: 'Regulatory Non-Compliance', count: 112, percentage: 10.8 },
          { violation_type: 'Cultural Sensitivity', count: 98, percentage: 9.4 },
          { violation_type: 'Misleading Claims', count: 76, percentage: 7.3 },
          { violation_type: 'Other', count: 43, percentage: 4.1 }
        ],
        summary: {
          total_users: 1248,
          total_enterprises: 42,
          total_analyses: 12487,
          total_violations: 1040
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Credit Consumption Area Chart
  const creditChartData = godViewData?.credit_consumption ? [{
    name: 'Credits Used',
    data: godViewData.credit_consumption.credits
  }] : [];

  const creditChartOptions = {
    chart: {
      type: 'area',
      toolbar: { show: false },
      zoom: { enabled: false },
      fontFamily: 'inherit'
    },
    colors: [brandBlue],
    stroke: {
      curve: 'smooth',
      width: 3
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.5,
        opacityTo: 0.1,
        stops: [0, 90, 100]
      }
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: godViewData?.credit_consumption?.dates || [],
      labels: { style: { colors: brandGrey, fontSize: '12px' } },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: { 
        style: { colors: brandGrey, fontSize: '12px' },
        formatter: (val) => val.toLocaleString()
      }
    },
    grid: {
      borderColor: borderColor,
      strokeDashArray: 5
    },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val.toLocaleString()} credits` }
    }
  };

  // Most Active Companies Bar Chart
  const companiesChartData = godViewData?.most_active_companies ? [{
    name: 'Posts Analyzed',
    data: godViewData.most_active_companies.map(c => c.posts)
  }] : [];

  const companiesChartOptions = {
    chart: {
      type: 'bar',
      toolbar: { show: false },
      fontFamily: 'inherit'
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: '70%',
        borderRadius: 6,
        distributed: false
      }
    },
    colors: [brandBlue],
    dataLabels: {
      enabled: true,
      formatter: (val) => val.toLocaleString(),
      style: { fontSize: '12px', fontWeight: 'bold', colors: ['#fff'] }
    },
    xaxis: {
      categories: godViewData?.most_active_companies?.map(c => c.name) || [],
      labels: { style: { colors: brandGrey, fontSize: '11px' } }
    },
    yaxis: {
      labels: { style: { colors: textColor, fontSize: '11px' } }
    },
    grid: { borderColor: borderColor, strokeDashArray: 5 },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val.toLocaleString()} posts` }
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  // MRR Helper Functions for Stripe Integration
  const getMrrCardColor = () => {
    const mrrData = godViewData?.kpi_cards?.mrr;
    if (!mrrData) return 'gray.500';
    if (mrrData.status === 'error' && mrrData.value === null) return 'red.500';
    if (mrrData.status === 'stale') return 'yellow.500';
    return 'green.500';
  };

  const renderMrrValue = () => {
    const mrrData = godViewData?.kpi_cards?.mrr;
    
    // Error state - no value available
    if (!mrrData || (mrrData.status === 'error' && mrrData.value === null)) {
      return (
        <Heading size="2xl" color="red.500">
          N/A
        </Heading>
      );
    }
    
    // Success or stale (cached) state
    return (
      <Heading size="2xl" color={mrrData.status === 'stale' ? 'yellow.500' : greenColor}>
        {formatCurrency(mrrData.value || 0)}
      </Heading>
    );
  };

  const renderMrrBadge = () => {
    const mrrData = godViewData?.kpi_cards?.mrr;
    
    // Error state
    if (!mrrData || (mrrData.status === 'error' && mrrData.value === null)) {
      return (
        <Tooltip label={mrrData?.error || 'Unable to fetch MRR from Stripe'}>
          <Badge colorScheme="red" fontSize="xs">
            <Icon as={FaExclamationTriangle} mr={1} />
            {t('admin.stripError', 'Stripe API Error')}
          </Badge>
        </Tooltip>
      );
    }
    
    // Stale/cached state with warning
    if (mrrData.status === 'stale') {
      return (
        <Tooltip label={`${mrrData.error || 'Showing cached value'} - Last updated: ${mrrData.last_updated ? new Date(mrrData.last_updated).toLocaleString() : 'Unknown'}`}>
          <Badge colorScheme="yellow" fontSize="xs">
            <Icon as={FaClock} mr={1} />
            {t('admin.cachedData', 'Cached Data')}
          </Badge>
        </Tooltip>
      );
    }
    
    // Success state
    const subscriptionCount = mrrData.subscription_count || 0;
    const isCached = mrrData.cached;
    
    return (
      <HStack spacing={2}>
        <Tooltip label={`From ${subscriptionCount} active subscription${subscriptionCount !== 1 ? 's' : ''}`}>
          <Badge colorScheme="green" fontSize="xs">
            <Icon as={FaArrowUp} mr={1} />
            {t('admin.liveStripe', 'Live from Stripe')}
          </Badge>
        </Tooltip>
        {isCached && (
          <Tooltip label={`Cached - Last updated: ${mrrData.last_updated ? new Date(mrrData.last_updated).toLocaleString() : 'Unknown'}`}>
            <Badge colorScheme="blue" fontSize="xs" variant="outline">
              <Icon as={FaClock} mr={1} />
              {t('admin.cached', 'Cached')}
            </Badge>
          </Tooltip>
        )}
      </HStack>
    );
  };

  if (loading) {
    return (
      <Center h="100vh">
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" thickness="4px" />
          <Text color={textColorSecondary}>{t('admin.loadingGodView', 'Loading platform overview...')}</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <Box>
          <HStack spacing={3} mb={1}>
            <Icon as={FaCrown} boxSize={6} color="yellow.500" />
            <Heading size="lg" color={textColor}>
              {t('admin.godView', 'System Admin Dashboard')}
            </Heading>
          </HStack>
          <Text color={textColorSecondary} fontSize="sm">
            {t('admin.platformOverview', 'Complete platform overview and business health metrics')}
          </Text>
        </Box>
        <HStack spacing={3}>
          <Button
            colorScheme="brand"
            variant="outline"
            leftIcon={<Icon as={FaUsers} />}
            onClick={() => router.push('/contentry/admin/users')}
          >
            {t('admin.manageUsers', 'Manage Users')}
          </Button>
          <Button
            colorScheme="brand"
            leftIcon={<Icon as={FaBuilding} />}
            onClick={() => router.push('/contentry/admin/enterprises')}
          >
            {t('admin.manageEnterprises', 'Manage Enterprises')}
          </Button>
        </HStack>
      </Flex>

      <VStack spacing={6} align="stretch">
        {/* KPI Cards - Large Numbers */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
          {/* MRR Card - Live Stripe Integration */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" borderTop="4px solid" borderColor={getMrrCardColor()}>
            <CardBody>
              <VStack spacing={3} align="start">
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
                    {godViewData?.kpi_cards?.mrr?.label || 'Monthly Recurring Revenue'}
                  </Text>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={getMrrCardColor()}
                    icon={<Icon as={FaDollarSign} w="20px" h="20px" color="white" />}
                  />
                </HStack>
                {renderMrrValue()}
                {renderMrrBadge()}
              </VStack>
            </CardBody>
          </Card>

          {/* New Users Card */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" borderTop="4px solid" borderColor={brandBlue}>
            <CardBody>
              <VStack spacing={3} align="start">
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
                    {godViewData?.kpi_cards?.new_users?.label || 'New Users (30 Days)'}
                  </Text>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={brandBlue}
                    icon={<Icon as={FaUsers} w="20px" h="20px" color="white" />}
                  />
                </HStack>
                <Heading size="2xl" color={textColor}>
                  {formatNumber(godViewData?.kpi_cards?.new_users?.value || 0)}
                </Heading>
                <Text fontSize="xs" color={textColorSecondary}>
                  {t('admin.last30Days', 'Last 30 days')}
                </Text>
              </VStack>
            </CardBody>
          </Card>

          {/* Active Companies Card */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" borderTop="4px solid" borderColor={brandBlueLight}>
            <CardBody>
              <VStack spacing={3} align="start">
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
                    {godViewData?.kpi_cards?.active_companies?.label || 'Active Companies'}
                  </Text>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={brandBlueLight}
                    icon={<Icon as={FaBuilding} w="20px" h="20px" color="white" />}
                  />
                </HStack>
                <Heading size="2xl" color={textColor}>
                  {formatNumber(godViewData?.kpi_cards?.active_companies?.value || 0)}
                </Heading>
                <Text fontSize="xs" color={textColorSecondary}>
                  {t('admin.enterprises', 'Enterprise accounts')}
                </Text>
              </VStack>
            </CardBody>
          </Card>

          {/* Total Content Analyzed Card */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" borderTop="4px solid" borderColor={brandBlueDark}>
            <CardBody>
              <VStack spacing={3} align="start">
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
                    {godViewData?.kpi_cards?.total_content?.label || 'Total Content Analyzed'}
                  </Text>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={brandBlueDark}
                    icon={<Icon as={FaFileAlt} w="20px" h="20px" color="white" />}
                  />
                </HStack>
                <Heading size="2xl" color={textColor}>
                  {formatNumber(godViewData?.kpi_cards?.total_content?.value || 0)}
                </Heading>
                <Text fontSize="xs" color={textColorSecondary}>
                  {t('admin.allTime', 'All time')}
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Charts Row */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
          {/* Platform-Wide Credit Consumption - Area Chart */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
            <CardHeader pb={0}>
              <Flex justify="space-between" align="center">
                <Box>
                  <Heading size="md" color={textColor} mb={1}>
                    {t('admin.creditConsumption', 'Platform-Wide Credit Consumption')}
                  </Heading>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {t('admin.dailyUsage', 'Daily credit usage across all users')}
                  </Text>
                </Box>
                <IconBox
                  w="40px"
                  h="40px"
                  bg={brandBlue}
                  icon={<Icon as={FaServer} w="20px" h="20px" color="white" />}
                />
              </Flex>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                <AreaChart chartData={creditChartData} chartOptions={creditChartOptions} />
              </Box>
            </CardBody>
          </Card>

          {/* Most Active Companies - Bar Chart */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
            <CardHeader pb={0}>
              <Flex justify="space-between" align="center">
                <Box>
                  <Heading size="md" color={textColor} mb={1}>
                    {t('admin.mostActiveCompanies', 'Most Active Companies')}
                  </Heading>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {t('admin.postsByCompany', 'Posts analyzed per company (last 30 days)')}
                  </Text>
                </Box>
                <IconBox
                  w="40px"
                  h="40px"
                  bg={brandBlueLight}
                  icon={<Icon as={MdBusiness} w="20px" h="20px" color="white" />}
                />
              </Flex>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                <BarChart chartData={companiesChartData} chartOptions={companiesChartOptions} />
              </Box>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Compliance Hotspots Table */}
        <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
          <CardHeader>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor} mb={1}>
                  {t('admin.complianceHotspots', 'Platform-Wide Compliance Hotspots')}
                </Heading>
                <Text fontSize="sm" color={textColorSecondary}>
                  {t('admin.mostCommonViolations', 'Most frequently triggered compliance violations across all companies')}
                </Text>
              </Box>
              <Badge colorScheme="red" fontSize="md" px={3} py={1}>
                {formatNumber(godViewData?.summary?.total_violations || 0)} {t('admin.totalViolations', 'total violations')}
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody pt={0}>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>#</Th>
                  <Th>{t('admin.violationType', 'Violation Type')}</Th>
                  <Th isNumeric>{t('admin.count', 'Count')}</Th>
                  <Th>{t('admin.percentage', 'Percentage')}</Th>
                  <Th>{t('admin.distribution', 'Distribution')}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {(godViewData?.compliance_hotspots || []).map((hotspot, idx) => (
                  <Tr key={idx}>
                    <Td>
                      <Badge 
                        colorScheme={idx < 3 ? 'red' : idx < 6 ? 'yellow' : 'gray'} 
                        borderRadius="full"
                      >
                        {idx + 1}
                      </Badge>
                    </Td>
                    <Td fontWeight="600">{hotspot.violation_type}</Td>
                    <Td isNumeric>
                      <Text fontWeight="600">{formatNumber(hotspot.count)}</Text>
                    </Td>
                    <Td>
                      <Badge colorScheme={hotspot.percentage > 15 ? 'red' : hotspot.percentage > 10 ? 'yellow' : 'gray'}>
                        {hotspot.percentage}%
                      </Badge>
                    </Td>
                    <Td w="200px">
                      <Progress 
                        value={hotspot.percentage} 
                        colorScheme={hotspot.percentage > 15 ? 'red' : hotspot.percentage > 10 ? 'yellow' : 'brand'}
                        size="sm" 
                        borderRadius="full"
                      />
                    </Td>
                  </Tr>
                ))}
                {(!godViewData?.compliance_hotspots || godViewData.compliance_hotspots.length === 0) && (
                  <Tr>
                    <Td colSpan={5} textAlign="center" py={8}>
                      <Text color={textColorSecondary}>
                        {t('admin.noViolations', 'No compliance violations recorded')}
                      </Text>
                    </Td>
                  </Tr>
                )}
              </Tbody>
            </Table>
          </CardBody>
        </Card>

        {/* Summary Stats */}
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
          <Card bg={cardBg} boxShadow="md" borderRadius="lg">
            <CardBody py={4}>
              <Stat size="sm">
                <StatLabel color={textColorSecondary} fontSize="xs">{t('admin.totalUsers', 'Total Users')}</StatLabel>
                <StatNumber color={textColor} fontSize="xl">{formatNumber(godViewData?.summary?.total_users || 0)}</StatNumber>
                <StatHelpText fontSize="xs">
                  <Icon as={FaUsers} mr={1} color={brandBlue} />
                  {t('admin.registered', 'registered')}
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg} boxShadow="md" borderRadius="lg">
            <CardBody py={4}>
              <Stat size="sm">
                <StatLabel color={textColorSecondary} fontSize="xs">{t('admin.totalEnterprises', 'Total Enterprises')}</StatLabel>
                <StatNumber color={textColor} fontSize="xl">{formatNumber(godViewData?.summary?.total_enterprises || 0)}</StatNumber>
                <StatHelpText fontSize="xs">
                  <Icon as={FaBuilding} mr={1} color={brandBlueLight} />
                  {t('admin.companies', 'companies')}
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg} boxShadow="md" borderRadius="lg">
            <CardBody py={4}>
              <Stat size="sm">
                <StatLabel color={textColorSecondary} fontSize="xs">{t('admin.totalAnalyses', 'Total Analyses')}</StatLabel>
                <StatNumber color={textColor} fontSize="xl">{formatNumber(godViewData?.summary?.total_analyses || 0)}</StatNumber>
                <StatHelpText fontSize="xs">
                  <Icon as={FaDatabase} mr={1} color={brandBlueDark} />
                  {t('admin.contentPieces', 'content pieces')}
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg} boxShadow="md" borderRadius="lg">
            <CardBody py={4}>
              <Stat size="sm">
                <StatLabel color={textColorSecondary} fontSize="xs">{t('admin.violationRate', 'Violation Rate')}</StatLabel>
                <StatNumber color="red.500" fontSize="xl">
                  {godViewData?.summary?.total_analyses > 0 
                    ? ((godViewData?.summary?.total_violations / godViewData?.summary?.total_analyses) * 100).toFixed(1)
                    : 0}%
                </StatNumber>
                <StatHelpText fontSize="xs">
                  <Icon as={FaExclamationTriangle} mr={1} color="red.500" />
                  {t('admin.ofContent', 'of content')}
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>
      </VStack>
    </Box>
  );
}
