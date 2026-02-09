'use client';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  SimpleGrid,
  Text,
  useColorModeValue,
  Flex,
  Heading,
  Button,
  Spinner,
  Center,
  VStack,
  HStack,
  Icon,
  Progress,
  Badge,
  Card as ChakraCard,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Divider,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Tooltip,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import IconBox from '@/components/icons/IconBox';
import { 
  FileText, CheckCircle, AlertTriangle, LineChart as LineChartIcon, 
  Shield, Globe, Brain, Trophy, ArrowUp, ArrowDown,
  Eye, Pencil, TrendingUp, TrendingDown, ExternalLink, Building2, User
} from 'lucide-react';
import { FaExternalLinkAlt } from 'react-icons/fa';
import LineChart from '@/components/charts/LineChart';
import BarChart from '@/components/charts/BarChart';
import axios from 'axios';
import { getApiUrl, createAuthenticatedAxios } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useWorkspace } from '@/context/WorkspaceContext';
import { useRouter } from 'next/navigation';

// New Dashboard Components
import DateRangeFilter from '@/components/dashboard/DateRangeFilter';
import ExportButton from '@/components/dashboard/ExportButton';
import ContentForReviewWidget from '@/components/dashboard/ContentForReviewWidget';
import TeamPerformanceWidget from '@/components/dashboard/TeamPerformanceWidget';
import ContentStrategyWidget from '@/components/dashboard/ContentStrategyWidget';
import ApprovalKPIsWidget from '@/components/dashboard/ApprovalKPIsWidget';
import MyPerformanceWidget from '@/components/dashboard/MyPerformanceWidget';
import MyActionItemsWidget from '@/components/dashboard/MyActionItemsWidget';

export default function Dashboard() {
  const { t } = useTranslation();
  const { user, loading: authLoading, hasPermission } = useAuth();
  const { currentWorkspace, isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  const router = useRouter();

  const [scoreAnalytics, setScoreAnalytics] = useState(null);
  const [basicStats, setBasicStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  // Date range filter state
  const [dateRange, setDateRange] = useState('last_30_days');
  const [customStart, setCustomStart] = useState(null);
  const [customEnd, setCustomEnd] = useState(null);

  // Check if user is manager/admin
  const isManager = user?.role?.toLowerCase() === 'admin' || 
                    user?.role?.toLowerCase() === 'manager' ||
                    user?.enterprise_role?.toLowerCase() === 'admin' ||
                    user?.enterprise_role?.toLowerCase() === 'manager';

  // User permissions for widgets
  const userPermissions = {
    canApprove: hasPermission?.('approve_content') || isManager,
    canViewTeam: isManager,
    canManage: isManager,
  };

  // Brand colors
  const brandPrimary = '#4318FF';
  const brandPrimaryLight = '#7551FF';
  const brandAccent = '#01B574';
  const brandBlue = '#4318FF';
  const brandBlueLight = '#7551FF';
  const brandBlueDark = '#2B3674';
  const brandGrey = '#A3AED0';

  // Color mode values
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const fetchDashboardData = useCallback(async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();

      // Build query params
      let queryParams = `date_range=${dateRange}`;
      if (dateRange === 'custom' && customStart && customEnd) {
        queryParams += `&custom_start=${customStart}&custom_end=${customEnd}`;
      }

      // Fetch score analytics
      const [scoreResponse, statsResponse] = await Promise.all([
        api.get(`/users/${user.id}/score-analytics`),
        api.get(`/users/${user.id}/dashboard-analytics`),
      ]);

      setScoreAnalytics(scoreResponse.data);
      setBasicStats(statsResponse.data);
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, [user?.id, dateRange, customStart, customEnd]);

  useEffect(() => {
    if (user?.id) {
      fetchDashboardData();
    }
  }, [user?.id, fetchDashboardData]);

  // Handle date range change
  const handleDateRangeChange = (newRange) => {
    setDateRange(newRange.range);
    if (newRange.range === 'custom') {
      setCustomStart(newRange.customStart);
      setCustomEnd(newRange.customEnd);
    } else {
      setCustomStart(null);
      setCustomEnd(null);
    }
  };

  // Score trend chart configuration
  const scoreTrendChartData = scoreAnalytics?.score_trend?.scores ? [{
    name: 'Content Score',
    data: scoreAnalytics.score_trend.scores
  }] : [];

  const scoreTrendChartOptions = {
    chart: {
      type: 'area',
      toolbar: { show: false },
      zoom: { enabled: false },
      fontFamily: 'inherit',
      events: {
        dataPointSelection: (event, chartContext, config) => {
          // Navigate to posts filtered by date
          const dateIndex = config.dataPointIndex;
          const date = scoreAnalytics?.score_trend?.dates?.[dateIndex];
          if (date) {
            router.push(`/contentry/content-moderation?tab=posts&date=${date}`);
          }
        },
      },
      dropShadow: {
        enabled: true,
        top: 3,
        left: 0,
        blur: 4,
        opacity: 0.2,
        color: brandPrimary
      }
    },
    colors: [brandPrimary],
    stroke: {
      curve: 'smooth',
      width: 4
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.5,
        opacityTo: 0.1,
        stops: [0, 90, 100],
        colorStops: [
          { offset: 0, color: brandPrimaryLight, opacity: 0.4 },
          { offset: 100, color: brandPrimaryLight, opacity: 0.05 }
        ]
      }
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: scoreAnalytics?.score_trend?.dates || [],
      labels: { 
        style: { colors: brandGrey, fontSize: '12px', fontWeight: 500 },
        rotate: -45,
        rotateAlways: false
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      min: 0,
      max: 100,
      labels: { 
        style: { colors: brandGrey, fontSize: '12px', fontWeight: 500 },
        formatter: (val) => `${Math.round(val)}`
      }
    },
    grid: {
      borderColor: borderColor,
      strokeDashArray: 5,
      padding: { left: 10, right: 10 }
    },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val}/100` },
      marker: { show: true }
    },
    markers: {
      size: 6,
      colors: [brandPrimary],
      strokeColors: '#fff',
      strokeWidth: 3,
      hover: { size: 9 }
    }
  };

  // Pillar breakdown chart configuration (horizontal bar)
  const pillarChartData = scoreAnalytics?.pillar_breakdown ? [{
    name: 'Score',
    data: [
      scoreAnalytics.pillar_breakdown.compliance || 0,
      scoreAnalytics.pillar_breakdown.cultural || 0,
      scoreAnalytics.pillar_breakdown.accuracy || 0
    ]
  }] : [];

  const pillarChartOptions = {
    chart: {
      type: 'bar',
      toolbar: { show: false },
      fontFamily: 'inherit',
      events: {
        dataPointSelection: (event, chartContext, config) => {
          const pillars = ['compliance', 'cultural', 'accuracy'];
          const pillar = pillars[config.dataPointIndex];
          if (pillar) {
            router.push(`/contentry/analytics?view=${pillar}`);
          }
        },
      },
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: '65%',
        borderRadius: 8,
        distributed: true
      }
    },
    colors: [brandPrimary, brandPrimaryLight, brandAccent],
    dataLabels: {
      enabled: true,
      formatter: (val) => `${val}%`,
      style: { fontSize: '14px', fontWeight: 'bold', colors: ['#fff'] },
      offsetX: -10
    },
    xaxis: {
      categories: ['Compliance', 'Cultural Sensitivity', 'Accuracy'],
      max: 100,
      labels: { style: { colors: brandGrey, fontSize: '12px', fontWeight: 500 } }
    },
    yaxis: {
      labels: { style: { colors: textColor, fontSize: '13px', fontWeight: 600 } }
    },
    grid: { borderColor: borderColor, strokeDashArray: 5 },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val}/100` }
    },
    legend: { show: false }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  const getScoreBadge = (score) => {
    if (score >= 90) return { label: 'Excellent', color: 'green' };
    if (score >= 80) return { label: 'Good', color: 'teal' };
    if (score >= 70) return { label: 'Fair', color: 'yellow' };
    if (score >= 60) return { label: 'Needs Work', color: 'orange' };
    return { label: 'Poor', color: 'red' };
  };

  // Clickable stat card component
  const ClickableStatCard = ({ icon, iconColor, label, value, helpText, helpIcon, colorScheme, drillDownUrl }) => (
    <ChakraCard 
      bg={cardBg} 
      boxShadow="md" 
      borderRadius="lg"
      cursor={drillDownUrl ? 'pointer' : 'default'}
      _hover={drillDownUrl ? { transform: 'translateY(-2px)', boxShadow: 'lg' } : {}}
      transition="all 0.2s"
      onClick={() => drillDownUrl && router.push(drillDownUrl)}
    >
      <CardBody py={4}>
        <Stat>
          <Flex justify="space-between" align="center">
            <Box>
              <StatLabel color={textColorSecondary} fontSize="xs">{label}</StatLabel>
              <StatNumber color={colorScheme ? `${colorScheme}.500` : textColor} fontSize="2xl">
                {value}
              </StatNumber>
              <StatHelpText fontSize="xs">
                <Icon as={helpIcon} mr={1} color={colorScheme ? `${colorScheme}.500` : brandBlue} />
                {helpText}
              </StatHelpText>
            </Box>
            {drillDownUrl && (
              <Icon as={FaExternalLinkAlt} boxSize={3} color="gray.400" />
            )}
          </Flex>
        </Stat>
      </CardBody>
    </ChakraCard>
  );

  // Clickable score card component
  const ClickableScoreCard = ({ icon, iconColor, label, score, drillDownUrl }) => (
    <ChakraCard 
      bg={cardBg} 
      boxShadow="lg" 
      borderRadius="xl"
      cursor={drillDownUrl ? 'pointer' : 'default'}
      _hover={drillDownUrl ? { transform: 'translateY(-2px)', boxShadow: 'xl' } : {}}
      transition="all 0.2s"
      onClick={() => drillDownUrl && router.push(drillDownUrl)}
    >
      <CardBody>
        <VStack spacing={3} align="center" py={2}>
          <Icon as={icon} boxSize={8} color={iconColor} />
          <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
            {label}
          </Text>
          <HStack>
            <Heading size="2xl" color={textColor}>
              {score}
            </Heading>
            {drillDownUrl && (
              <Icon as={FaExternalLinkAlt} boxSize={3} color="gray.400" />
            )}
          </HStack>
          <Progress 
            value={score} 
            colorScheme={getScoreColor(score)}
            size="sm" 
            w="80%" 
            borderRadius="full"
          />
        </VStack>
      </CardBody>
    </ChakraCard>
  );

  if (!isHydrated || authLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (!user) {
    router.push('/contentry/auth/login');
    return null;
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Workspace indicator banner */}
      {isEnterpriseWorkspace && (
        <Alert status="info" mb={4} borderRadius="md" bg="purple.50" _dark={{ bg: 'purple.900' }}>
          <AlertIcon as={Building2} color="purple.500" />
          <Text fontSize="sm" fontWeight="500">
            You are viewing <Badge colorScheme="purple" mx={1}>{enterpriseInfo?.name || 'Company'}</Badge> dashboard. Analytics show company-wide performance.
          </Text>
        </Alert>
      )}
      
      {/* Header with Date Range Filter */}
      <Flex justify="space-between" align="center" mb={6} flexWrap="wrap" gap={4}>
        <Box>
          <HStack spacing={2} mb={1}>
            <Heading size="lg" color={textColor}>
              {isEnterpriseWorkspace 
                ? t('dashboard.companyIntelligence', 'Company Intelligence')
                : t('dashboard.contentIntelligence', 'Content Intelligence')}
            </Heading>
            {isEnterpriseWorkspace && (
              <Badge colorScheme="purple" fontSize="xs">
                <HStack spacing={1}>
                  <Building2 size={12} />
                  <Text>Company</Text>
                </HStack>
              </Badge>
            )}
          </HStack>
          <Text color={textColorSecondary} fontSize="sm">
            {t('dashboard.welcomeBack', 'Welcome back')}, {user?.full_name || user?.email?.split('@')[0]}! {isEnterpriseWorkspace 
              ? t('dashboard.companyOverview', "Here's your company's performance overview.")
              : t('dashboard.hereIsOverview', "Here's your performance overview.")}
          </Text>
        </Box>
        <HStack spacing={4} flexWrap="wrap">
          {/* P1: Global Date Range Filter */}
          <DateRangeFilter 
            value={dateRange}
            onChange={handleDateRangeChange}
          />
          <Button
            colorScheme="brand"
            leftIcon={<Icon as={Pencil} />}
            onClick={() => router.push('/contentry/create')}
          >
            {t('dashboard.createPost', 'Create Post')}
          </Button>
        </HStack>
      </Flex>

      {loading ? (
        <Center py={20}>
          <VStack spacing={4}>
            <Spinner size="xl" color="brand.500" thickness="4px" />
            <Text color={textColorSecondary}>{t('dashboard.loadingInsights', 'Loading your insights...')}</Text>
          </VStack>
        </Center>
      ) : (
        <VStack spacing={6} align="stretch">
          {/* P0: Overall Score Cards with Drill-Down */}
          <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6}>
            {/* Main Score - Clickable */}
            <ChakraCard 
              bg={cardBg} 
              boxShadow="lg" 
              borderRadius="xl"
              cursor="pointer"
              _hover={{ transform: 'translateY(-2px)', boxShadow: 'xl' }}
              transition="all 0.2s"
              onClick={() => router.push('/contentry/analytics?view=overall')}
            >
              <CardBody>
                <VStack spacing={3} align="center" py={2}>
                  <Icon as={Trophy} boxSize={8} color={brandBlue} />
                  <Text fontSize="sm" color={textColorSecondary} fontWeight="600">
                    {t('dashboard.overallScore', 'Overall Score')}
                  </Text>
                  <HStack>
                    <Heading size="2xl" color={textColor}>
                      {scoreAnalytics?.overall_average || 0}
                    </Heading>
                    <Icon as={FaExternalLinkAlt} boxSize={3} color="gray.400" />
                  </HStack>
                  <Badge colorScheme={getScoreBadge(scoreAnalytics?.overall_average || 0).color} fontSize="sm" px={3} py={1} borderRadius="full">
                    {getScoreBadge(scoreAnalytics?.overall_average || 0).label}
                  </Badge>
                </VStack>
              </CardBody>
            </ChakraCard>

            {/* Compliance Score - Clickable */}
            <ClickableScoreCard
              icon={Shield}
              iconColor={brandBlue}
              label={t('dashboard.compliance', 'Compliance')}
              score={scoreAnalytics?.pillar_breakdown?.compliance || 0}
              drillDownUrl="/contentry/analytics?view=compliance"
            />

            {/* Cultural Score - Clickable */}
            <ClickableScoreCard
              icon={Globe}
              iconColor={brandBlueLight}
              label={t('dashboard.culturalSensitivity', 'Cultural Sensitivity')}
              score={scoreAnalytics?.pillar_breakdown?.cultural || 0}
              drillDownUrl="/contentry/analytics?view=cultural"
            />

            {/* Accuracy Score - Clickable */}
            <ClickableScoreCard
              icon={Brain}
              iconColor={brandBlueDark}
              label={t('dashboard.accuracy', 'Accuracy')}
              score={scoreAnalytics?.pillar_breakdown?.accuracy || 0}
              drillDownUrl="/contentry/analytics?view=accuracy"
            />
          </SimpleGrid>

          {/* P2: Creator Role Widgets */}
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            <MyPerformanceWidget userId={user?.id} />
            <MyActionItemsWidget userId={user?.id} />
          </SimpleGrid>

          {/* P1: Content for Review Widget - Manager/Admin Only */}
          <ContentForReviewWidget userId={user?.id} userPermissions={userPermissions} />

          {/* P1: Manager/Admin Widgets */}
          {isManager && (
            <>
              {/* Team Performance Widget */}
              <TeamPerformanceWidget 
                userId={user?.id}
                dateRange={dateRange}
                customStart={customStart}
                customEnd={customEnd}
              />

              {/* Content Strategy & Approval KPIs Row */}
              <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={6}>
                <ContentStrategyWidget 
                  userId={user?.id}
                  dateRange={dateRange}
                  customStart={customStart}
                  customEnd={customEnd}
                />
                <ApprovalKPIsWidget 
                  userId={user?.id}
                  dateRange={dateRange}
                  customStart={customStart}
                  customEnd={customEnd}
                />
              </SimpleGrid>
            </>
          )}

          {/* Charts Row */}
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* Average Content Score Over Time */}
            <ChakraCard bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader pb={0}>
                <Flex justify="space-between" align="center">
                  <Box>
                    <Heading size="md" color={textColor} mb={1}>
                      {t('dashboard.scoreOverTime', 'Average Content Score Over Time')}
                    </Heading>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {t('dashboard.clickToViewPosts', 'Click data points to view posts')}
                    </Text>
                  </Box>
                  <HStack>
                    <ExportButton widgetType="overview" dateRange={dateRange} />
                    <IconBox
                      w="40px"
                      h="40px"
                      bg={brandBlue}
                      icon={<Icon as={TrendingUp} w="20px" h="20px" color="white" />}
                    />
                  </HStack>
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  <LineChart chartData={scoreTrendChartData} chartOptions={scoreTrendChartOptions} />
                </Box>
              </CardBody>
            </ChakraCard>

            {/* Score Breakdown by Pillar */}
            <ChakraCard bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader pb={0}>
                <Flex justify="space-between" align="center">
                  <Box>
                    <Heading size="md" color={textColor} mb={1}>
                      {t('dashboard.scoreByPillar', 'Score Breakdown by Pillar')}
                    </Heading>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {t('dashboard.clickToViewDetails', 'Click bars to view detailed analytics')}
                    </Text>
                  </Box>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={brandBlueLight}
                    icon={<Icon as={LineChartIcon} w="20px" h="20px" color="white" />}
                  />
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  <BarChart chartData={pillarChartData} chartOptions={pillarChartOptions} />
                </Box>
              </CardBody>
            </ChakraCard>
          </SimpleGrid>

          {/* Top & Bottom Performing Posts with Drill-Down */}
          <ChakraCard bg={cardBg} boxShadow="lg" borderRadius="xl">
            <CardHeader>
              <Flex justify="space-between" align="center">
                <Box>
                  <Heading size="md" color={textColor} mb={1}>
                    {t('dashboard.postPerformance', 'Top & Bottom Performing Posts')}
                  </Heading>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {t('dashboard.clickRowToView', 'Click any row to view post details')}
                  </Text>
                </Box>
                <HStack spacing={2}>
                  <Badge colorScheme="green" px={3} py={1}><Icon as={ArrowUp} mr={1} /> {t('dashboard.topPerformers', 'Top Performers')}</Badge>
                  <Badge colorScheme="red" px={3} py={1}><Icon as={ArrowDown} mr={1} /> {t('dashboard.needsImprovement', 'Needs Improvement')}</Badge>
                  <ExportButton widgetType="top-posts" />
                </HStack>
              </Flex>
            </CardHeader>
            <CardBody pt={0}>
              <Tabs variant="soft-rounded" colorScheme="brand">
                <TabList mb={4}>
                  <Tab>
                    <Icon as={Trophy} mr={2} color="green.500" />
                    {t('dashboard.top5', 'Top 5')}
                  </Tab>
                  <Tab>
                    <Icon as={AlertTriangle} mr={2} color="red.500" />
                    {t('dashboard.bottom5', 'Bottom 5')}
                  </Tab>
                </TabList>
                <TabPanels>
                  {/* Top Posts */}
                  <TabPanel px={0}>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>#</Th>
                          <Th>{t('dashboard.content', 'Content Preview')}</Th>
                          <Th isNumeric>{t('dashboard.score', 'Score')}</Th>
                          <Th>{t('dashboard.actions', 'Actions')}</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {(scoreAnalytics?.top_posts || []).map((post, idx) => (
                          <Tr 
                            key={post.id}
                            cursor="pointer"
                            _hover={{ bg: hoverBg }}
                            onClick={() => router.push(`/contentry/content-moderation?tab=posts&post_id=${post.id}`)}
                          >
                            <Td>
                              <Badge colorScheme="green" borderRadius="full">{idx + 1}</Badge>
                            </Td>
                            <Td maxW="400px" isTruncated fontWeight="500">
                              {post.content}
                            </Td>
                            <Td isNumeric>
                              <Badge colorScheme="green" fontSize="md" px={3} py={1}>
                                {post.overall_score}
                              </Badge>
                            </Td>
                            <Td>
                              <Tooltip label={t('dashboard.viewDetails', 'View Details')}>
                                <Button size="xs" variant="ghost" colorScheme="brand">
                                  <Icon as={Eye} />
                                  <Icon as={FaExternalLinkAlt} ml={1} boxSize={2} />
                                </Button>
                              </Tooltip>
                            </Td>
                          </Tr>
                        ))}
                        {(!scoreAnalytics?.top_posts || scoreAnalytics.top_posts.length === 0) && (
                          <Tr>
                            <Td colSpan={4} textAlign="center" py={8}>
                              <Text color={textColorSecondary}>
                                {t('dashboard.noTopPosts', 'No posts analyzed yet. Create your first post!')}
                              </Text>
                            </Td>
                          </Tr>
                        )}
                      </Tbody>
                    </Table>
                  </TabPanel>

                  {/* Bottom Posts */}
                  <TabPanel px={0}>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>#</Th>
                          <Th>{t('dashboard.content', 'Content Preview')}</Th>
                          <Th isNumeric>{t('dashboard.score', 'Score')}</Th>
                          <Th>{t('dashboard.actions', 'Actions')}</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {(scoreAnalytics?.bottom_posts || []).map((post, idx) => (
                          <Tr 
                            key={post.id}
                            cursor="pointer"
                            _hover={{ bg: hoverBg }}
                            onClick={() => router.push(`/contentry/content-moderation?tab=posts&post_id=${post.id}`)}
                          >
                            <Td>
                              <Badge colorScheme="red" borderRadius="full">{idx + 1}</Badge>
                            </Td>
                            <Td maxW="400px" isTruncated fontWeight="500">
                              {post.content}
                            </Td>
                            <Td isNumeric>
                              <Badge colorScheme={post.overall_score >= 60 ? 'yellow' : 'red'} fontSize="md" px={3} py={1}>
                                {post.overall_score}
                              </Badge>
                            </Td>
                            <Td>
                              <Tooltip label={t('dashboard.viewDetails', 'View Details')}>
                                <Button size="xs" variant="ghost" colorScheme="brand">
                                  <Icon as={Eye} />
                                  <Icon as={FaExternalLinkAlt} ml={1} boxSize={2} />
                                </Button>
                              </Tooltip>
                            </Td>
                          </Tr>
                        ))}
                        {(!scoreAnalytics?.bottom_posts || scoreAnalytics.bottom_posts.length === 0) && (
                          <Tr>
                            <Td colSpan={4} textAlign="center" py={8}>
                              <Text color={textColorSecondary}>
                                {t('dashboard.noBottomPosts', 'No posts analyzed yet. Create your first post!')}
                              </Text>
                            </Td>
                          </Tr>
                        )}
                      </Tbody>
                    </Table>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </CardBody>
          </ChakraCard>

          {/* P0: Quick Stats with Drill-Down */}
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <ClickableStatCard
              label={t('dashboard.totalAnalyzed', 'Total Analyzed')}
              value={scoreAnalytics?.total_analyses || basicStats?.stats?.total_posts || 0}
              helpText={t('dashboard.posts', 'posts')}
              helpIcon={FileText}
              drillDownUrl="/contentry/content-moderation?tab=posts"
            />
            
            <ClickableStatCard
              label={t('dashboard.approved', 'Approved')}
              value={basicStats?.stats?.approved || 0}
              helpText={t('dashboard.goodToGo', 'good to go')}
              helpIcon={CheckCircle}
              colorScheme="green"
              drillDownUrl="/contentry/content-moderation?tab=posts&status=published"
            />
            
            <ClickableStatCard
              label={t('dashboard.pending', 'Pending Review')}
              value={basicStats?.stats?.pending || 0}
              helpText={t('dashboard.awaitingReview', 'awaiting')}
              helpIcon={AlertTriangle}
              colorScheme="yellow"
              drillDownUrl="/contentry/content-moderation?tab=posts&status=pending_approval"
            />
            
            <ClickableStatCard
              label={t('dashboard.flagged', 'Flagged')}
              value={basicStats?.stats?.flagged || 0}
              helpText={t('dashboard.needsAttention', 'needs attention')}
              helpIcon={AlertTriangle}
              colorScheme="red"
              drillDownUrl="/contentry/content-moderation?tab=posts&status=flagged"
            />
          </SimpleGrid>
        </VStack>
      )}
    </Box>
  );
}
