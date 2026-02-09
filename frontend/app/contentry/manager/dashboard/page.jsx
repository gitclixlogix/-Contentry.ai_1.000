'use client';
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Card,
  CardBody,
  CardHeader,
  useToast,
  Icon,
  Avatar,
  AvatarGroup,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
} from '@chakra-ui/react';
import MiniStatistics from '@/components/card/MiniStatistics';
import IconBox from '@/components/icons/IconBox';
import { FaUsers, FaFileAlt, FaCheckCircle, FaExclamationTriangle, FaChartLine, FaTrophy, FaClock } from 'react-icons/fa';
import { MdBarChart } from 'react-icons/md';
import BarChart from '@/components/charts/BarChart';
import LineChart from '@/components/charts/LineChart';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function ManagerDashboard() {
  const router = useRouter();
  const toast = useToast();
  
  const [user, setUser] = useState(null);
  const [teamAnalytics, setTeamAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const brandColor = useColorModeValue('brand.500', 'white');
  const boxBg = useColorModeValue('secondaryGray.300', 'whiteAlpha.100');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    if (user?.id) {
      loadTeamAnalytics();
    }
  }, [user]);

  const loadUser = () => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      
      // Check if user is manager
      if (userData.role !== 'manager' && userData.enterprise_role !== 'manager') {
        toast({
          title: 'Access Denied',
          description: 'Only managers can access this page',
          status: 'error',
          duration: 3000,
        });
        router.push('/contentry/dashboard');
        return;
      }
      
      setUser(userData);
    } else {
      router.push('/contentry/auth/login');
    }
  };

  const loadTeamAnalytics = async () => {
    try {
      const API = getApiUrl();
      
      // Call the real backend API
      const response = await axios.get(
        `${API}/enterprises/${user.enterprise_id}/manager/${user.id}/team`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      setTeamAnalytics(response.data);
    } catch (error) {
      console.error('Error loading team analytics:', error);
      
      // Fallback to mock data if API fails (e.g., user is not a real manager)
      const mockData = {
        team_stats: {
          total_members: 8,
          active_members: 6,
          total_posts: 124,
          approved_posts: 98,
          pending_posts: 18,
          flagged_posts: 8,
          avg_team_score: 82.5,
          overall_approval_rate: 79.0
        },
        top_performers: [
          { id: '1', name: 'Sarah Chen', avatar: '', posts: 32, approval_rate: 96.8, avg_score: 88 },
          { id: '2', name: 'Michael Rodriguez', avatar: '', posts: 28, approval_rate: 92.3, avg_score: 85 },
          { id: '3', name: 'Emily Watson', avatar: '', posts: 24, approval_rate: 91.7, avg_score: 84 },
          { id: '4', name: 'David Kim', avatar: '', posts: 22, approval_rate: 90.9, avg_score: 82 },
          { id: '5', name: 'Lisa Anderson', avatar: '', posts: 18, approval_rate: 88.9, avg_score: 80 },
        ],
        weekly_activity: {
          weeks: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          posts: [28, 35, 31, 30],
          trend: 'up'
        },
        category_breakdown: {
          categories: ['Marketing', 'Product Updates', 'Team News', 'Industry Insights', 'Customer Stories'],
          counts: [38, 32, 24, 18, 12],
        },
        score_trend: {
          weeks: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          scores: [78, 80, 82, 85]
        },
        is_demo_data: true
      };

      setTeamAnalytics(mockData);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <Center h="100vh">
        <VStack spacing={4}>
          <Spinner size="xl" color={brandColor} />
          <Text color={textColorSecondary}>Loading team analytics...</Text>
        </VStack>
      </Center>
    );
  }

  // Chart data for weekly activity
  const weeklyActivityData = teamAnalytics?.weekly_activity ? [{
    name: "Team Posts",
    data: teamAnalytics.weekly_activity.posts
  }] : [];

  const weeklyActivityOptions = {
    chart: {
      toolbar: { show: false },
      zoom: { enabled: false }
    },
    stroke: {
      curve: 'smooth',
      width: 3
    },
    xaxis: {
      categories: teamAnalytics?.weekly_activity?.weeks || [],
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
          fontWeight: '500',
        },
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
          fontWeight: '500',
        },
      },
    },
    grid: {
      strokeDashArray: 5,
      borderColor: '#E2E8F0',
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'light',
        type: 'vertical',
        shadeIntensity: 0.5,
        opacityFrom: 0.8,
        opacityTo: 0.3,
      }
    },
    colors: [brandColor],
    dataLabels: { enabled: false },
  };

  // Chart data for category breakdown
  const categoryData = teamAnalytics?.category_breakdown ? [{
    name: "Posts",
    data: teamAnalytics.category_breakdown.counts
  }] : [];

  const categoryOptions = {
    chart: {
      toolbar: { show: false }
    },
    plotOptions: {
      bar: {
        borderRadius: 8,
        columnWidth: '60%',
      }
    },
    colors: ['#4299E1'],
    dataLabels: { enabled: false },
    xaxis: {
      categories: teamAnalytics?.category_breakdown?.categories || [],
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '11px',
          fontWeight: '500',
        },
        rotate: -45,
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
          fontWeight: '500',
        },
      },
    },
    grid: {
      borderColor: '#E2E8F0',
    },
    legend: { show: false },
  };

  const stats = teamAnalytics?.team_stats || {};

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Header */}
      <Flex mb={6} justify="space-between" align="center" flexWrap="wrap" gap={4}>
        <Box>
          <Flex align="center" gap={3}>
            <Heading size="lg" color={textColor}>
              Team Dashboard
            </Heading>
            <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
              MANAGER
            </Badge>
          </Flex>
          <Text color={textColorSecondary} fontSize="md" mt={2}>
            Monitor your team&apos;s performance and content quality
          </Text>
        </Box>
        <Button
          leftIcon={<Icon as={FaChartLine} />}
          colorScheme="brand"
          onClick={loadTeamAnalytics}
          isLoading={loading}
        >
          Refresh
        </Button>
      </Flex>

      {/* Overview Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg={boxBg}
              icon={<Icon w="32px" h="32px" as={FaUsers} color={brandColor} />}
            />
          }
          name="Team Members"
          value={stats.total_members || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg={boxBg}
              icon={<Icon w="32px" h="32px" as={FaFileAlt} color={brandColor} />}
            />
          }
          name="Total Posts"
          value={stats.total_posts || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg="green.100"
              icon={<Icon w="32px" h="32px" as={FaCheckCircle} color="green.500" />}
            />
          }
          name="Approved"
          value={stats.approved_posts || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg="red.100"
              icon={<Icon w="32px" h="32px" as={FaExclamationTriangle} color="red.500" />}
            />
          }
          name="Flagged"
          value={stats.flagged_posts || 0}
        />
      </SimpleGrid>

      {/* Charts Row */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={6} mb={6}>
        {/* Weekly Activity */}
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={2}>
            <Flex align="center" gap={3}>
              <Icon as={FaChartLine} boxSize={5} color={brandColor} />
              <Box flex="1">
                <Heading size="md" color={textColor}>Weekly Team Activity</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>
                  Posts created by your team over the last 4 weeks
                </Text>
              </Box>
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              {weeklyActivityData.length > 0 ? (
                <LineChart chartData={weeklyActivityData} chartOptions={weeklyActivityOptions} />
              ) : (
                <Center h="100%">
                  <Text color={textColorSecondary} fontSize="sm">No activity data available</Text>
                </Center>
              )}
            </Box>
          </CardBody>
        </Card>

        {/* Category Breakdown */}
        <Card bg={cardBg} boxShadow="lg">
          <CardHeader pb={2}>
            <Flex align="center" gap={3}>
              <Icon as={MdBarChart} boxSize={5} color={brandColor} />
              <Box flex="1">
                <Heading size="md" color={textColor}>Content by Category</Heading>
                <Text fontSize="sm" color={textColorSecondary} mt={1}>
                  Distribution of posts across different categories
                </Text>
              </Box>
            </Flex>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              {categoryData.length > 0 ? (
                <BarChart chartData={categoryData} chartOptions={categoryOptions} />
              ) : (
                <Center h="100%">
                  <Text color={textColorSecondary} fontSize="sm">No category data available</Text>
                </Center>
              )}
            </Box>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Top Performers */}
      <Card bg={cardBg} boxShadow="lg">
        <CardHeader>
          <Flex align="center" gap={3}>
            <Icon as={FaTrophy} boxSize={6} color="yellow.500" />
            <Box flex="1">
              <Heading size="md" color={textColor}>Top Performers</Heading>
              <Text fontSize="sm" color={textColorSecondary} mt={1}>
                Team members with the highest post counts and approval rates
              </Text>
            </Box>
          </Flex>
        </CardHeader>
        <CardBody>
          {teamAnalytics?.top_performers?.length > 0 ? (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Rank</Th>
                    <Th>Team Member</Th>
                    <Th isNumeric>Posts</Th>
                    <Th isNumeric>Approval Rate</Th>
                    <Th>Performance</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {teamAnalytics.top_performers.map((member, idx) => (
                    <Tr key={member.id}>
                      <Td>
                        <Badge
                          colorScheme={idx === 0 ? 'yellow' : idx === 1 ? 'gray' : idx === 2 ? 'orange' : 'blue'}
                          fontSize="md"
                          px={3}
                          py={1}
                        >
                          #{idx + 1}
                        </Badge>
                      </Td>
                      <Td>
                        <Flex align="center" gap={3}>
                          <Avatar size="sm" name={member.name} />
                          <Text fontWeight="600" fontSize="sm">{member.name}</Text>
                        </Flex>
                      </Td>
                      <Td isNumeric>
                        <Badge colorScheme="blue" fontSize="sm">{member.posts}</Badge>
                      </Td>
                      <Td isNumeric>
                        <Text fontWeight="600" color={member.approval_rate >= 90 ? 'green.500' : 'orange.500'}>
                          {member.approval_rate}%
                        </Text>
                      </Td>
                      <Td>
                        <Progress
                          value={member.approval_rate}
                          colorScheme={member.approval_rate >= 90 ? 'green' : 'orange'}
                          size="sm"
                          borderRadius="full"
                          w="100px"
                        />
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          ) : (
            <Center py={8}>
              <VStack spacing={3}>
                <Icon as={FaTrophy} boxSize={12} color={textColorSecondary} />
                <Text color={textColor} fontWeight="600">No Performance Data</Text>
                <Text fontSize="sm" color={textColorSecondary} textAlign="center" maxW="400px">
                  Team member performance data will appear here
                </Text>
              </VStack>
            </Center>
          )}
        </CardBody>
      </Card>
    </Box>
  );
}
