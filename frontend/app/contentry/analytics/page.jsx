'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  SimpleGrid,
  Text,
  useColorModeValue,
  Flex,
  Badge,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Spinner,
  Icon,
  HStack,
  VStack,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Divider,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useDisclosure,
} from '@chakra-ui/react';
import { FaFileAlt, FaDollarSign, FaClock, FaUsers, FaChartLine, FaGlobe, FaCheckCircle, FaExclamationTriangle, FaShieldAlt } from 'react-icons/fa';
import { MdBarChart, MdTrendingUp } from 'react-icons/md';
import MiniStatistics from '@/components/card/MiniStatistics';
import IconBox from '@/components/icons/IconBox';
import BarChart from '@/components/charts/BarChart';
import LineChart from '@/components/charts/LineChart';
import WorldMap from '@/components/charts/WorldMap';
import { useRouter } from 'next/navigation';
import useAdminAnalytics from '@/hooks/useAdminAnalytics';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import DrilldownModal from '@/components/drilldown/DrilldownModal';

export default function AnalyticsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [costMetrics, setCostMetrics] = useState(null);
  const [demographics, setDemographics] = useState(null);
  const [subscriptions, setSubscriptions] = useState(null);
  const [adminStats, setAdminStats] = useState(null);
  
  // Drilldown modal state
  const [drilldownMetric, setDrilldownMetric] = useState(null);
  const { isOpen: isDrilldownOpen, onOpen: onDrilldownOpen, onClose: onDrilldownClose } = useDisclosure();

  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const boxBg = useColorModeValue('secondaryGray.300', 'whiteAlpha.100');
  const cardBg = useColorModeValue('white', 'navy.800');
  const textColor = useColorModeValue('secondaryGray.900', 'white');
  const textColorSecondary = useColorModeValue('secondaryGray.600', 'gray.400');

  // Handle drilldown click
  const handleDrilldown = (metricType) => {
    setDrilldownMetric(metricType);
    onDrilldownOpen();
  };

  // Handle drilldown close with cleanup
  const handleDrilldownClose = () => {
    onDrilldownClose();
    setTimeout(() => {
      setDrilldownMetric(null);
    }, 200);
  };

  // Load user from localStorage on client side only
  useEffect(() => {
    const loadUser = () => {
      if (typeof window !== 'undefined') {
        const savedUser = localStorage.getItem('contentry_user');
        if (savedUser) {
          setUser(JSON.parse(savedUser));
        } else {
          router.push('/contentry/auth/login');
        }
      }
    };
    loadUser();
  }, [router]);

  // Use reusable analytics hook
  const { data, loading } = useAdminAnalytics({
    autoLoad: !!user,
    includeUserDemographics: true,
    includePostingPatterns: true,
    includeContentQuality: true,
    includeLanguageDistribution: true,
    includeUsersByCountry: true,
    includeCostMetrics: false,
  });

  useEffect(() => {
    if (!user) return;
    
    if (user.role !== 'admin') {
      router.push('/contentry/dashboard');
      return;
    }
    
    // Load additional data
    const loadAdditionalData = async () => {
      try {
        const API = getApiUrl();
        const [costRes, demographicsRes, subsRes, statsRes] = await Promise.all([
          axios.get(`${API}/admin/analytics/cost-metrics`),
          axios.get(`${API}/admin/analytics/user-demographics`),
          axios.get(`${API}/admin/analytics/subscriptions`),
          axios.get(`${API}/admin/stats`),
        ]);

        setCostMetrics(costRes.data);
        setDemographics(demographicsRes.data);
        setSubscriptions(subsRes.data);
        setAdminStats(statsRes.data);
      } catch (error) {
        console.error('Error loading analytics:', error);
      }
    };
    loadAdditionalData();
  }, [user, router]);

  if (loading) {
    return (
      <Box pt={{ base: '10px', md: '10px', xl: '10px' }}>
        <Flex justify="center" align="center" minH="400px">
          <Spinner size="xl" color={brandColor} thickness="4px" />
        </Flex>
      </Box>
    );
  }

  // Chart configurations for Horizon AI style
  const lineChartOptions = {
    chart: { toolbar: { show: false }, dropShadow: { enabled: true, top: 13, left: 0, blur: 10, opacity: 0.1, color: '#1e40af' } },
    stroke: { curve: 'smooth', width: 3 },
    colors: ['#1e40af', '#39B8FF'],
    markers: { size: 0 },
    xaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } } },
    grid: { strokeDashArray: 5, borderColor: '#56577A' },
    fill: { type: 'gradient', gradient: { shade: 'light', type: 'vertical', shadeIntensity: 0.5, opacityFrom: 0.8, opacityTo: 0.3 } },
    dataLabels: { enabled: false },
    tooltip: { theme: 'dark' },
  };

  const barChartOptions = {
    chart: { toolbar: { show: false } },
    plotOptions: { bar: { borderRadius: 10, columnWidth: '40px' } },
    colors: ['#1e40af'],
    dataLabels: { enabled: false },
    xaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } } },
    fill: { type: 'gradient', gradient: { type: 'vertical', colorStops: [[ { offset: 0, color: '#1e40af', opacity: 1 }, { offset: 100, color: '#60a5fa', opacity: 0.5 } ]] } },
    grid: { strokeDashArray: 5, borderColor: '#56577A' },
    tooltip: { theme: 'dark' },
  };

  // Prepare chart data
  const postingTrendData = [{
    name: 'Posts',
    data: data.postingPatterns?.hourly_distribution?.map(h => h.count) || Array(24).fill(0)
  }];

  const postingTrendOptions = {
    ...lineChartOptions,
    xaxis: { ...lineChartOptions.xaxis, categories: Array.from({ length: 24 }, (_, i) => `${i}:00`) }
  };

  const ageGroupData = [{
    name: 'Users',
    data: demographics?.age_groups?.map(a => a.count) || []
  }];

  const ageGroupOptions = {
    ...barChartOptions,
    xaxis: { ...barChartOptions.xaxis, categories: demographics?.age_groups?.map(a => a.range) || [] }
  };

  const genderData = [{
    name: 'Users',
    data: demographics?.gender_distribution?.map(g => g.count) || []
  }];

  const genderOptions = {
    ...barChartOptions,
    colors: ['#39B8FF'],
    fill: { type: 'gradient', gradient: { type: 'vertical', colorStops: [[ { offset: 0, color: '#39B8FF', opacity: 1 }, { offset: 100, color: '#4481EB', opacity: 0.5 } ]] } },
    xaxis: { ...barChartOptions.xaxis, categories: demographics?.gender_distribution?.map(g => g.gender) || [] }
  };

  const subscriptionData = [{
    name: 'Users',
    data: subscriptions?.user_counts || []
  }];

  const subscriptionOptions = {
    ...barChartOptions,
    colors: ['#05CD99'],
    fill: { type: 'gradient', gradient: { type: 'vertical', colorStops: [[ { offset: 0, color: '#05CD99', opacity: 1 }, { offset: 100, color: '#00B574', opacity: 0.5 } ]] } },
    xaxis: { ...barChartOptions.xaxis, categories: subscriptions?.plans || [] }
  };

  const languageData = [{
    name: 'Posts',
    data: data.languages?.languages?.slice(0, 8).map(l => l.count) || []
  }];

  const languageOptions = {
    ...barChartOptions,
    plotOptions: { bar: { borderRadius: 8, horizontal: true, distributed: true } },
    colors: ['#1e40af', '#39B8FF', '#05CD99', '#FFB547', '#E31A1A', '#868CFF', '#F158C0', '#6E49F5'],
    xaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } } },
    yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } }, categories: data.languages?.languages?.slice(0, 8).map(l => l.language) || [] }
  };

  const contentQualityData = [{
    name: 'Score',
    data: [
      data.contentQuality?.average_scores?.overall || 0,
      data.contentQuality?.average_scores?.accuracy || 0,
      data.contentQuality?.average_scores?.compliance || 0,
      data.contentQuality?.average_scores?.cultural_sensitivity || 0
    ]
  }];

  const contentQualityOptions = {
    ...barChartOptions,
    xaxis: { ...barChartOptions.xaxis, categories: ['Overall', 'Accuracy', 'Compliance', 'Cultural'] },
    yaxis: { ...barChartOptions.yaxis, max: 100 }
  };

  // Score Trend Data (mock monthly trend)
  const scoreTrendData = [
    {
      name: 'Overall',
      data: [72, 75, 78, 80, 82, 85]
    },
    {
      name: 'Compliance',
      data: [68, 70, 74, 78, 80, 82]
    },
    {
      name: 'Cultural',
      data: [75, 77, 79, 82, 84, 86]
    }
  ];

  const scoreTrendOptions = {
    chart: { 
      toolbar: { show: false },
      dropShadow: { enabled: true, top: 13, left: 0, blur: 10, opacity: 0.1, color: '#1e40af' }
    },
    stroke: { curve: 'smooth', width: 3 },
    colors: ['#1e40af', '#05CD99', '#39B8FF'],
    markers: { size: 4, colors: ['#1e40af', '#05CD99', '#39B8FF'], strokeColors: '#fff', strokeWidth: 2 },
    xaxis: {
      categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: { 
      min: 0, 
      max: 100,
      labels: { style: { colors: '#A3AED0', fontSize: '12px', fontWeight: '500' } }
    },
    grid: { strokeDashArray: 5, borderColor: '#56577A' },
    legend: { 
      show: true, 
      position: 'top',
      labels: { colors: '#A3AED0' }
    },
    dataLabels: { enabled: false },
    tooltip: { theme: 'dark' },
  };

  return (
    <Box pt={{ base: '10px', md: '10px', xl: '10px' }}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb="20px">
        <Box>
          <Text color={textColor} fontSize="2xl" fontWeight="700">
            {t('analytics.pageTitle')}
          </Text>
          <Text color={textColorSecondary} fontSize="sm" mt={2}>
            {t('analytics.pageDescription')}
          </Text>
        </Box>
        <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
          {t('analytics.adminAccess')}
        </Badge>
      </Flex>

      {/* Overview Stats Row */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4, '2xl': 6 }} gap="20px" mb="20px">
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #1e40af 0%, #60a5fa 100%)" icon={<Icon as={FaUsers} w="28px" h="28px" color="white" />} />
          }
          name={t('analytics.totalUsers')}
          value={adminStats?.users?.total || 0}
          growth={`+${adminStats?.users?.recent_signups_30d || 0} ${t('analytics.thisMonth')}`}
          isClickable={true}
          onClick={() => handleDrilldown('total_users')}
        />
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #39B8FF 0%, #4481EB 100%)" icon={<Icon as={FaFileAlt} w="28px" h="28px" color="white" />} />
          }
          name={t('analytics.totalPosts')}
          value={adminStats?.posts?.total || 0}
          isClickable={true}
          onClick={() => handleDrilldown('total_posts')}
        />
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #05CD99 0%, #00B574 100%)" icon={<Icon as={FaCheckCircle} w="28px" h="28px" color="white" />} />
          }
          name={t('analytics.complianceRate')}
          value={`${adminStats?.posts?.compliance_rate || 0}%`}
          isClickable={true}
          onClick={() => handleDrilldown('compliance_rate')}
        />
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #E31A1A 0%, #FF6B6B 100%)" icon={<Icon as={FaExclamationTriangle} w="28px" h="28px" color="white" />} />
          }
          name={t('analytics.flaggedPosts')}
          value={adminStats?.posts?.flagged || 0}
          isClickable={true}
          onClick={() => handleDrilldown('flagged_content')}
        />
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #FFB547 0%, #FF6B00 100%)" icon={<Icon as={FaDollarSign} w="28px" h="28px" color="white" />} />
          }
          name={t('analytics.totalMrr')}
          value={`$${subscriptions?.total_mrr || 0}`}
          isClickable={true}
          onClick={() => handleDrilldown('total_mrr')}
        />
        <MiniStatistics
          startContent={
            <IconBox w="56px" h="56px" bg={boxBg} icon={<Icon as={FaGlobe} w="28px" h="28px" color={brandColor} />} />
          }
          name={t('analytics.enterprises')}
          value={adminStats?.enterprises?.total || 0}
        />
      </SimpleGrid>

      {/* Main Charts Row 1 - Posting Activity & Content Quality */}
      <SimpleGrid columns={{ base: 1, xl: 2 }} gap="20px" mb="20px">
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.postingActivity')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.postingActivityDesc')}</Text>
              </Box>
              <Icon as={MdTrendingUp} boxSize={6} color={brandColor} />
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              <LineChart chartData={postingTrendData} chartOptions={postingTrendOptions} />
            </Box>
          </CardBody>
        </Card>

        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.contentQualityScores')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.contentQualityDesc')}</Text>
              </Box>
              <Icon as={FaShieldAlt} boxSize={6} color={brandColor} />
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              <BarChart chartData={contentQualityData} chartOptions={contentQualityOptions} />
            </Box>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Score Trends - Full Width */}
      <Card bg={cardBg} boxShadow="lg" mb="20px">
        <CardHeader pb={0}>
          <Flex justify="space-between" align="center">
            <Box>
              <Heading size="md" color={textColor}>{t('analytics.scoreTrends')}</Heading>
              <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.scoreTrendsDesc')}</Text>
            </Box>
            <Badge colorScheme="blue">{t('analytics.trendAnalysis')}</Badge>
          </Flex>
        </CardHeader>
        <CardBody>
          <Box h="350px">
            <LineChart chartData={scoreTrendData} chartOptions={scoreTrendOptions} />
          </Box>
        </CardBody>
      </Card>

      {/* Main Charts Row 2 - Demographics */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} gap="20px" mb="20px">
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.ageDistribution')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.ageDistributionDesc')}</Text>
              </Box>
              {demographics?.is_mock_data && <Badge colorScheme="orange" fontSize="xs">{t('analytics.sampleData')}</Badge>}
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="280px">
              <BarChart chartData={ageGroupData} chartOptions={ageGroupOptions} />
            </Box>
          </CardBody>
        </Card>

        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.genderDistribution')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.genderDistributionDesc')}</Text>
              </Box>
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="280px">
              <BarChart chartData={genderData} chartOptions={genderOptions} />
            </Box>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Geographic Distribution - Full Width */}
      <Card bg={cardBg} boxShadow="lg" mb="20px">
        <CardHeader pb={0}>
          <Flex justify="space-between" align="center">
            <Box>
              <Heading size="md" color={textColor}>{t('analytics.geographicDistribution')}</Heading>
              <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.geographicDistributionDesc')}</Text>
            </Box>
            <HStack>
              <Badge colorScheme="blue">{data.geoData ? Object.keys(data.geoData).length : 0} {t('analytics.countries')}</Badge>
              {data.geoData && <Badge colorScheme="orange" fontSize="xs">{t('analytics.mockData')}</Badge>}
            </HStack>
          </Flex>
        </CardHeader>
        <CardBody>
          <WorldMap 
            data={data.geoData || {}} 
            countryDetails={data.geoCountryDetails || {}}
            height="450px"
          />
        </CardBody>
      </Card>

      {/* Main Charts Row 3 - Subscriptions & Languages */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} gap="20px" mb="20px">
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.subscriptionPlans')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.subscriptionPlansDesc')}</Text>
              </Box>
              <HStack>
                <Badge colorScheme="green">MRR: ${subscriptions?.total_mrr || 0}</Badge>
              </HStack>
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="280px">
              <BarChart chartData={subscriptionData} chartOptions={subscriptionOptions} />
            </Box>
          </CardBody>
        </Card>

        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={0}>
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="md" color={textColor}>{t('analytics.languageDistribution')}</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.languageDistributionDesc')}</Text>
              </Box>
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="280px">
              <BarChart chartData={languageData} chartOptions={languageOptions} />
            </Box>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Flagged Content Breakdown */}
      <Card bg={cardBg} boxShadow="lg" mb="20px">
        <CardHeader>
          <Flex justify="space-between" align="center">
            <Box>
              <Heading size="md" color={textColor}>{t('analytics.flaggedContentBreakdown')}</Heading>
              <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.flaggedContentDesc')}</Text>
            </Box>
          </Flex>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
            <VStack p={4} bg={boxBg} borderRadius="xl" align="center">
              <Icon as={FaCheckCircle} boxSize={8} color="green.500" />
              <Text fontSize="2xl" fontWeight="700" color={textColor}>{adminStats?.flagged_stats?.good_coverage || 0}</Text>
              <Text fontSize="sm" color={textColorSecondary}>{t('analytics.goodCoverage')}</Text>
            </VStack>
            <VStack p={4} bg={boxBg} borderRadius="xl" align="center">
              <Icon as={FaExclamationTriangle} boxSize={8} color="red.500" />
              <Text fontSize="2xl" fontWeight="700" color={textColor}>{adminStats?.flagged_stats?.rude_and_abusive || 0}</Text>
              <Text fontSize="sm" color={textColorSecondary}>{t('analytics.rudeAbusive')}</Text>
            </VStack>
            <VStack p={4} bg={boxBg} borderRadius="xl" align="center">
              <Icon as={FaExclamationTriangle} boxSize={8} color="orange.500" />
              <Text fontSize="2xl" fontWeight="700" color={textColor}>{adminStats?.flagged_stats?.contain_harassment || 0}</Text>
              <Text fontSize="sm" color={textColorSecondary}>{t('analytics.harassment')}</Text>
            </VStack>
            <VStack p={4} bg={boxBg} borderRadius="xl" align="center">
              <Icon as={FaShieldAlt} boxSize={8} color="blue.500" />
              <Text fontSize="2xl" fontWeight="700" color={textColor}>{adminStats?.flagged_stats?.policy_violation || 0}</Text>
              <Text fontSize="sm" color={textColorSecondary}>{t('analytics.policyViolation')}</Text>
            </VStack>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Score Distribution Table */}
      {data.contentQuality?.score_distribution && (
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader>
            <Heading size="md" color={textColor}>{t('analytics.contentScoreDistribution', 'Content Score Distribution')}</Heading>
            <Text fontSize="sm" color={textColorSecondary} mt={1}>{t('analytics.contentScoreDistributionDesc', 'Breakdown of content scores')}</Text>
          </CardHeader>
          <CardBody>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>{t('analytics.scoreRange', 'Score Range')}</Th>
                  <Th isNumeric>{t('analytics.count', 'Count')}</Th>
                  <Th>{t('analytics.distribution', 'Distribution')}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {Object.entries(data.contentQuality.score_distribution).map(([range, count]) => {
                  const total = Object.values(data.contentQuality.score_distribution).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
                  const colorScheme = range === '90-100' ? 'green' : range === '80-89' ? 'blue' : range === '70-79' ? 'yellow' : range === '60-69' ? 'orange' : 'red';
                  return (
                    <Tr key={range}>
                      <Td>
                        <Badge colorScheme={colorScheme}>{range}</Badge>
                      </Td>
                      <Td isNumeric fontWeight="600">{count}</Td>
                      <Td>
                        <HStack spacing={3}>
                          <Progress value={percentage} w="150px" colorScheme={colorScheme} size="sm" borderRadius="full" />
                          <Text fontSize="sm" color={textColorSecondary}>{percentage}%</Text>
                        </HStack>
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      )}

      {/* Drilldown Modal */}
      <DrilldownModal
        isOpen={isDrilldownOpen}
        onClose={handleDrilldownClose}
        metricType={drilldownMetric}
        dashboardType="analytics"
      />
    </Box>
  );
}
