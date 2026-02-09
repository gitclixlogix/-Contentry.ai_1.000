'use client';
import { useEffect, useState } from 'react';
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
  Badge,
  Card,
  CardBody,
  CardHeader,
  useToast,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Avatar,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Tooltip,
  Divider,
} from '@chakra-ui/react';
import IconBox from '@/components/icons/IconBox';
import { 
  FaUsers, FaFileAlt, FaCheckCircle, FaExclamationTriangle, 
  FaShieldAlt, FaGlobe, FaBuilding, FaEye, FaCheck, FaTimes,
  FaChartPie, FaUserShield, FaClock
} from 'react-icons/fa';
import { MdTrendingUp, MdWarning } from 'react-icons/md';
import BarChart from '@/components/charts/BarChart';
import PieChart from '@/components/charts/PieChart';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

// Radar Chart Component for Cultural Dimensions
function RadarChart({ data, options }) {
  const [Chart, setChart] = useState(null);
  
  useEffect(() => {
    import('react-apexcharts').then((mod) => {
      setChart(() => mod.default);
    });
  }, []);
  
  if (!Chart) return <Center h="100%"><Spinner /></Center>;
  
  return <Chart options={options} series={data} type="radar" height="100%" />;
}

export default function EnterpriseDashboard() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const { user, isLoading: authLoading, isHydrated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);

  // Brand Colors - Contentry Palette
  const brandBlue = '#2563eb';
  const brandBlueDark = '#1e40af';
  const brandBlueLight = '#60a5fa';
  const brandNavy = '#1B2559';
  const brandGrey = '#A3AED0';
  
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    if (isHydrated && !authLoading && user?.enterprise_id) {
      loadDashboardData();
    } else if (isHydrated && !authLoading && !user?.enterprise_id) {
      router.push('/contentry/dashboard');
    }
  }, [isHydrated, authLoading, user]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/dashboard-analytics`,
        { headers: { 'X-User-ID': user.id } }
      );
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading enterprise dashboard:', error);
      // Demo data fallback
      setDashboardData({
        enterprise_name: 'ACME Corporation',
        team_stats: {
          total_users: 24,
          total_posts: 487,
          approved_posts: 412,
          flagged_posts: 45,
          pending_review: 30,
          compliance_rate: 84.6
        },
        policy_violations: {
          total: 67,
          by_policy: {
            'Social Media Policy': 18,
            'Brand Voice Guide': 15,
            'Regulatory Compliance': 12,
            'Data Privacy': 10,
            'Competitor Mentions': 7,
            'Profanity Filter': 5
          }
        },
        cultural_risk_profile: {
          'Power Distance': 35,
          'Individualism': 28,
          'Masculinity': 42,
          'Uncertainty Avoidance': 55,
          'Long-term Orientation': 30,
          'Indulgence': 22
        },
        content_for_review: [
          { id: '1', content_preview: 'Excited to announce our Q4 results...', platform: 'LinkedIn', overall_score: 72, created_by: { name: 'John Smith', email: 'john@acme.com' }, created_at: '2024-12-10T14:30:00Z' },
          { id: '2', content_preview: 'Our team just closed a major deal with...', platform: 'Twitter', overall_score: 65, created_by: { name: 'Sarah Johnson', email: 'sarah@acme.com' }, created_at: '2024-12-10T12:15:00Z' },
          { id: '3', content_preview: 'Looking forward to the upcoming industry...', platform: 'LinkedIn', overall_score: 58, created_by: { name: 'Mike Chen', email: 'mike@acme.com' }, created_at: '2024-12-10T09:45:00Z' },
          { id: '4', content_preview: 'Great insights from our latest webinar...', platform: 'Facebook', overall_score: 81, created_by: { name: 'Emily Davis', email: 'emily@acme.com' }, created_at: '2024-12-09T16:20:00Z' },
          { id: '5', content_preview: 'We are hiring! Join our growing team...', platform: 'LinkedIn', overall_score: 77, created_by: { name: 'Alex Turner', email: 'alex@acme.com' }, created_at: '2024-12-09T11:30:00Z' }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApproveContent = async (contentId) => {
    try {
      const API = getApiUrl();
      await axios.post(`${API}/posts/${contentId}/approve`, {}, {
        headers: { 'X-User-ID': user.id }
      });
      toast({ title: 'Content approved', status: 'success', duration: 3000 });
      loadDashboardData();
    } catch (error) {
      toast({ title: 'Failed to approve content', status: 'error', duration: 3000 });
    }
  };

  const handleRejectContent = async (contentId) => {
    try {
      const API = getApiUrl();
      await axios.post(`${API}/posts/${contentId}/reject`, {}, {
        headers: { 'X-User-ID': user.id }
      });
      toast({ title: 'Content rejected', status: 'success', duration: 3000 });
      loadDashboardData();
    } catch (error) {
      toast({ title: 'Failed to reject content', status: 'error', duration: 3000 });
    }
  };

  // Policy Violations Donut Chart
  const policyViolationsData = dashboardData?.policy_violations?.by_policy 
    ? Object.values(dashboardData.policy_violations.by_policy)
    : [];
  
  const policyViolationsOptions = {
    chart: { type: 'donut', fontFamily: 'inherit' },
    labels: dashboardData?.policy_violations?.by_policy 
      ? Object.keys(dashboardData.policy_violations.by_policy)
      : [],
    colors: [brandBlue, brandBlueDark, brandBlueLight, '#9F7AEA', '#B794F4', '#D6BCFA'],
    legend: {
      position: 'bottom',
      labels: { colors: textColor }
    },
    dataLabels: {
      enabled: true,
      formatter: (val) => `${val.toFixed(0)}%`
    },
    plotOptions: {
      pie: {
        donut: {
          size: '65%',
          labels: {
            show: true,
            total: {
              show: true,
              label: 'Total Violations',
              fontSize: '14px',
              color: textColor
            }
          }
        }
      }
    },
    tooltip: { theme: 'dark' }
  };

  // Cultural Dimension Radar Chart
  const culturalDimensions = dashboardData?.cultural_risk_profile || {};
  const culturalRadarData = [{
    name: 'Risk Level',
    data: Object.values(culturalDimensions)
  }];
  
  const culturalRadarOptions = {
    chart: { type: 'radar', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: [brandBlue],
    xaxis: {
      categories: Object.keys(culturalDimensions),
      labels: { 
        style: { colors: Array(6).fill(textColor), fontSize: '11px' }
      }
    },
    yaxis: {
      show: false,
      max: 100
    },
    fill: {
      opacity: 0.3,
      colors: [brandBlue]
    },
    stroke: {
      width: 2,
      colors: [brandBlue]
    },
    markers: {
      size: 4,
      colors: [brandBlue],
      strokeColors: '#fff',
      strokeWidth: 2
    },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `${val}% risk` }
    },
    plotOptions: {
      radar: {
        polygons: {
          strokeColors: borderColor,
          connectorColors: borderColor,
          fill: { colors: ['transparent'] }
        }
      }
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  if (!isHydrated || authLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (!user?.enterprise_id) {
    return null;
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <Box>
          <Heading size="lg" color={textColor} mb={1}>
            {t('enterprise.commandCenter', 'Enterprise Command Center')}
          </Heading>
          <Text color={textColorSecondary} fontSize="sm">
            {dashboardData?.enterprise_name || 'Enterprise'} - {t('enterprise.teamCompliance', 'Team Compliance & Quality Control')}
          </Text>
        </Box>
        <Button
          colorScheme="brand"
          leftIcon={<Icon as={FaUsers} />}
          onClick={() => router.push('/contentry/enterprise/team')}
        >
          {t('enterprise.manageTeam', 'Manage Team')}
        </Button>
      </Flex>

      {loading ? (
        <Center py={20}>
          <VStack spacing={4}>
            <Spinner size="xl" color="brand.500" thickness="4px" />
            <Text color={textColorSecondary}>{t('enterprise.loadingData', 'Loading enterprise data...')}</Text>
          </VStack>
        </Center>
      ) : (
        <VStack spacing={6} align="stretch">
          {/* Team Stats KPIs */}
          <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={4}>
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.teamMembers', 'Team Members')}</StatLabel>
                  <StatNumber color={textColor} fontSize="2xl">{dashboardData?.team_stats?.total_users || 0}</StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaUsers} mr={1} color={brandBlue} />{t('enterprise.active', 'active')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.totalPosts', 'Total Posts')}</StatLabel>
                  <StatNumber color={textColor} fontSize="2xl">{dashboardData?.team_stats?.total_posts || 0}</StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaFileAlt} mr={1} color={brandBlue} />{t('enterprise.analyzed', 'analyzed')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.approved', 'Approved')}</StatLabel>
                  <StatNumber color="green.500" fontSize="2xl">{dashboardData?.team_stats?.approved_posts || 0}</StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaCheckCircle} mr={1} color="green.500" />{t('enterprise.goodToGo', 'good')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.flagged', 'Flagged')}</StatLabel>
                  <StatNumber color="red.500" fontSize="2xl">{dashboardData?.team_stats?.flagged_posts || 0}</StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaExclamationTriangle} mr={1} color="red.500" />{t('enterprise.issues', 'issues')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.pendingReview', 'Pending Review')}</StatLabel>
                  <StatNumber color="yellow.500" fontSize="2xl">{dashboardData?.team_stats?.pending_review || 0}</StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaClock} mr={1} color="yellow.500" />{t('enterprise.awaiting', 'awaiting')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            
            <Card bg={cardBg} boxShadow="md" borderRadius="lg">
              <CardBody py={4}>
                <Stat size="sm">
                  <StatLabel color={textColorSecondary} fontSize="xs">{t('enterprise.complianceRate', 'Compliance Rate')}</StatLabel>
                  <StatNumber color={dashboardData?.team_stats?.compliance_rate >= 80 ? 'green.500' : 'yellow.500'} fontSize="2xl">
                    {dashboardData?.team_stats?.compliance_rate || 0}%
                  </StatNumber>
                  <StatHelpText fontSize="xs"><Icon as={FaShieldAlt} mr={1} color={brandBlue} />{t('enterprise.teamAvg', 'team avg')}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* Charts Row */}
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* Compliance Violations by Policy - Donut Chart */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader pb={0}>
                <Flex justify="space-between" align="center">
                  <Box>
                    <Heading size="md" color={textColor} mb={1}>
                      {t('enterprise.complianceViolations', 'Team-Wide Compliance Violations by Policy')}
                    </Heading>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {t('enterprise.identifyTrainingNeeds', 'Identify which policies need more team training')}
                    </Text>
                  </Box>
                  <Badge colorScheme="red" fontSize="md" px={3} py={1}>
                    {dashboardData?.policy_violations?.total || 0} {t('enterprise.total', 'total')}
                  </Badge>
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="320px">
                  {policyViolationsData.length > 0 ? (
                    <PieChart chartData={policyViolationsData} chartOptions={policyViolationsOptions} />
                  ) : (
                    <Center h="100%">
                      <VStack spacing={3}>
                        <Icon as={FaCheckCircle} boxSize={12} color="green.500" />
                        <Text color={textColorSecondary}>{t('enterprise.noViolations', 'No violations detected!')}</Text>
                      </VStack>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>

            {/* Cultural Dimension Risk - Radar Chart */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader pb={0}>
                <Flex justify="space-between" align="center">
                  <Box>
                    <Heading size="md" color={textColor} mb={1}>
                      {t('enterprise.culturalRisk', 'Team-Wide Cultural Dimension Risk')}
                    </Heading>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {t('enterprise.culturalDimensionsDesc', 'Cultural dimension analysis across all team content')}
                    </Text>
                  </Box>
                  <IconBox
                    w="40px"
                    h="40px"
                    bg={brandBlueLight}
                    icon={<Icon as={FaGlobe} w="20px" h="20px" color="white" />}
                  />
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="320px">
                  <RadarChart data={culturalRadarData} options={culturalRadarOptions} />
                </Box>
                <Text fontSize="xs" color={textColorSecondary} textAlign="center" mt={2}>
                  {t('enterprise.higherRisk', 'Higher values indicate areas where your team may have cultural blind spots')}
                </Text>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* Content for Review Queue */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
            <CardHeader>
              <Flex justify="space-between" align="center">
                <Box>
                  <Heading size="md" color={textColor} mb={1}>
                    {t('enterprise.contentForReview', 'Content for Review')}
                  </Heading>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {t('enterprise.pendingApproval', 'Content submitted by creators awaiting manager approval')}
                  </Text>
                </Box>
                <HStack spacing={3}>
                  <Badge colorScheme="yellow" fontSize="md" px={3} py={1}>
                    {dashboardData?.content_for_review?.length || 0} {t('enterprise.pending', 'pending')}
                  </Badge>
                  <Button size="sm" colorScheme="brand" variant="outline" onClick={() => router.push('/contentry/enterprise/approvals')}>
                    {t('enterprise.viewAll', 'View All')}
                  </Button>
                </HStack>
              </Flex>
            </CardHeader>
            <CardBody pt={0}>
              {(dashboardData?.content_for_review?.length || 0) > 0 ? (
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>{t('enterprise.creator', 'Creator')}</Th>
                      <Th>{t('enterprise.contentPreview', 'Content Preview')}</Th>
                      <Th>{t('enterprise.platform', 'Platform')}</Th>
                      <Th isNumeric>{t('enterprise.score', 'Score')}</Th>
                      <Th>{t('enterprise.submitted', 'Submitted')}</Th>
                      <Th>{t('enterprise.actions', 'Actions')}</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {dashboardData?.content_for_review?.map((item) => (
                      <Tr key={item.id}>
                        <Td>
                          <HStack spacing={2}>
                            <Avatar size="sm" name={item.created_by?.name} />
                            <Box>
                              <Text fontWeight="600" fontSize="sm">{item.created_by?.name}</Text>
                              <Text fontSize="xs" color={textColorSecondary}>{item.created_by?.email}</Text>
                            </Box>
                          </HStack>
                        </Td>
                        <Td maxW="300px">
                          <Text isTruncated fontSize="sm">{item.content_preview}</Text>
                        </Td>
                        <Td>
                          <Badge colorScheme="brand">{item.platform}</Badge>
                        </Td>
                        <Td isNumeric>
                          <Badge colorScheme={getScoreColor(item.overall_score)} fontSize="sm" px={2}>
                            {item.overall_score}
                          </Badge>
                        </Td>
                        <Td>
                          <Text fontSize="xs" color={textColorSecondary}>
                            {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                          </Text>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            <Tooltip label={t('enterprise.viewDetails', 'View Details')}>
                              <Button size="xs" variant="ghost" colorScheme="brand">
                                <Icon as={FaEye} />
                              </Button>
                            </Tooltip>
                            <Tooltip label={t('enterprise.approve', 'Approve')}>
                              <Button 
                                size="xs" 
                                colorScheme="green" 
                                variant="ghost"
                                onClick={() => handleApproveContent(item.id)}
                              >
                                <Icon as={FaCheck} />
                              </Button>
                            </Tooltip>
                            <Tooltip label={t('enterprise.reject', 'Reject')}>
                              <Button 
                                size="xs" 
                                colorScheme="red" 
                                variant="ghost"
                                onClick={() => handleRejectContent(item.id)}
                              >
                                <Icon as={FaTimes} />
                              </Button>
                            </Tooltip>
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              ) : (
                <Center py={10}>
                  <VStack spacing={3}>
                    <Icon as={FaCheckCircle} boxSize={12} color="green.500" />
                    <Text color={textColorSecondary} fontWeight="500">
                      {t('enterprise.allCaughtUp', 'All caught up! No content pending review.')}
                    </Text>
                  </VStack>
                </Center>
              )}
            </CardBody>
          </Card>
        </VStack>
      )}
    </Box>
  );
}
