'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  SimpleGrid,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Icon,
  Spinner,
  Center,
  useColorModeValue,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Select,
  Flex,
  Progress,
  Divider,
} from '@chakra-ui/react';
import {
  FaDollarSign,
  FaUsers,
  FaUserCheck,
  FaChartLine,
  FaRocket,
  FaExchangeAlt,
  FaRobot,
  FaCrown,
} from 'react-icons/fa';
import dynamic from 'next/dynamic';
import { getApiUrl } from '@/lib/api';

const LineChart = dynamic(() => import('@/components/charts/LineChart'), { ssr: false });
const BarChart = dynamic(() => import('@/components/charts/BarChart'), { ssr: false });
const PieChart = dynamic(() => import('@/components/charts/PieChart'), { ssr: false });

export default function SuperAdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [growthKpis, setGrowthKpis] = useState(null);
  const [mrrTrend, setMrrTrend] = useState(null);
  const [activeUsersTrend, setActiveUsersTrend] = useState(null);
  const [customerFunnel, setCustomerFunnel] = useState(null);
  const [trialConversion, setTrialConversion] = useState(null);
  const [aiCosts, setAiCosts] = useState(null);
  const [featureAdoption, setFeatureAdoption] = useState(null);
  const [mrrByPlan, setMrrByPlan] = useState(null);
  const [topCustomers, setTopCustomers] = useState(null);
  const [activeUsersView, setActiveUsersView] = useState('daily');

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const accentRed = useColorModeValue('red.600', 'red.400');

  useEffect(() => {
    fetchAllData();
  }, []);

  useEffect(() => {
    fetchActiveUsersTrend(activeUsersView);
  }, [activeUsersView]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    return {
      'Authorization': `Bearer ${token}`,
      'x-user-id': userId,
    };
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const headers = getAuthHeaders();
      const baseUrl = getApiUrl();

      // Fetch all data in parallel
      const [
        growthRes,
        mrrTrendRes,
        activeUsersRes,
        funnelRes,
        trialRes,
        aiCostsRes,
        featureRes,
        planRes,
        customersRes,
      ] = await Promise.all([
        fetch(`${baseUrl}/superadmin/kpis/growth`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/mrr-trend?months=12`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/active-users?view=daily&days=30`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/customer-funnel?months=12`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/trial-conversion`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/ai-costs?months=12`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/feature-adoption`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/mrr-by-plan`, { headers }),
        fetch(`${baseUrl}/superadmin/kpis/top-customers?limit=10`, { headers }),
      ]);

      if (growthRes.ok) setGrowthKpis(await growthRes.json());
      if (mrrTrendRes.ok) setMrrTrend(await mrrTrendRes.json());
      if (activeUsersRes.ok) setActiveUsersTrend(await activeUsersRes.json());
      if (funnelRes.ok) setCustomerFunnel(await funnelRes.json());
      if (trialRes.ok) setTrialConversion(await trialRes.json());
      if (aiCostsRes.ok) setAiCosts(await aiCostsRes.json());
      if (featureRes.ok) setFeatureAdoption(await featureRes.json());
      if (planRes.ok) setMrrByPlan(await planRes.json());
      if (customersRes.ok) setTopCustomers(await customersRes.json());

    } catch (error) {
      console.error('Failed to fetch super admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveUsersTrend = async (view) => {
    try {
      const headers = getAuthHeaders();
      const days = view === 'daily' ? 30 : view === 'weekly' ? 90 : 365;
      const response = await fetch(
        `${getApiUrl()}/superadmin/kpis/active-users?view=${view}&days=${days}`,
        { headers }
      );
      if (response.ok) {
        setActiveUsersTrend(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch active users trend:', error);
    }
  };

  // Chart configurations
  const mrrChartOptions = {
    chart: { type: 'area', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: ['#E53E3E'],
    stroke: { curve: 'smooth', width: 3 },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
        stops: [0, 100],
      },
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: mrrTrend?.chart?.labels || [],
      labels: { style: { colors: textColorSecondary } },
    },
    yaxis: {
      labels: {
        style: { colors: textColorSecondary },
        formatter: (val) => `$${(val / 1000).toFixed(0)}k`,
      },
    },
    tooltip: { y: { formatter: (val) => `$${val.toLocaleString()}` } },
    grid: { borderColor: useColorModeValue('#E2E8F0', '#4A5568') },
  };

  const mrrChartData = mrrTrend?.chart?.data ? [{ name: 'MRR', data: mrrTrend.chart.data }] : [];

  const activeUsersChartOptions = {
    chart: { type: 'line', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: ['#3182CE'],
    stroke: { curve: 'smooth', width: 3 },
    dataLabels: { enabled: false },
    xaxis: {
      categories: activeUsersTrend?.chart?.labels || [],
      labels: { style: { colors: textColorSecondary }, rotate: -45 },
    },
    yaxis: {
      labels: { style: { colors: textColorSecondary } },
    },
    tooltip: { y: { formatter: (val) => `${val} users` } },
    grid: { borderColor: useColorModeValue('#E2E8F0', '#4A5568') },
  };

  const activeUsersChartData = activeUsersTrend?.chart?.data 
    ? [{ name: activeUsersView === 'daily' ? 'DAU' : activeUsersView === 'weekly' ? 'WAU' : 'MAU', data: activeUsersTrend.chart.data }] 
    : [];

  const funnelChartOptions = {
    chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: ['#38A169', '#E53E3E'],
    plotOptions: { bar: { borderRadius: 4, columnWidth: '60%' } },
    dataLabels: { enabled: false },
    xaxis: {
      categories: customerFunnel?.chart?.labels || [],
      labels: { style: { colors: textColorSecondary }, rotate: -45 },
    },
    yaxis: { labels: { style: { colors: textColorSecondary } } },
    legend: { position: 'top' },
    grid: { borderColor: useColorModeValue('#E2E8F0', '#4A5568') },
  };

  const funnelChartData = customerFunnel?.chart 
    ? [
        { name: 'New Signups', data: customerFunnel.chart.new_signups },
        { name: 'Churned', data: customerFunnel.chart.churned },
      ] 
    : [];

  const aiCostsChartOptions = {
    chart: { type: 'area', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: ['#805AD5'],
    stroke: { curve: 'smooth', width: 3 },
    fill: {
      type: 'gradient',
      gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] },
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: aiCosts?.chart?.labels || [],
      labels: { style: { colors: textColorSecondary } },
    },
    yaxis: {
      labels: {
        style: { colors: textColorSecondary },
        formatter: (val) => `$${val.toFixed(0)}`,
      },
    },
    tooltip: { y: { formatter: (val) => `$${val.toFixed(2)}` } },
    grid: { borderColor: useColorModeValue('#E2E8F0', '#4A5568') },
  };

  const aiCostsChartData = aiCosts?.chart?.data ? [{ name: 'AI Costs', data: aiCosts.chart.data }] : [];

  const featureChartOptions = {
    chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'inherit' },
    colors: ['#DD6B20'],
    plotOptions: { bar: { borderRadius: 4, horizontal: true } },
    dataLabels: { enabled: true, formatter: (val) => `${val}%` },
    xaxis: {
      categories: featureAdoption?.chart?.labels || [],
      max: 100,
      labels: { style: { colors: textColorSecondary } },
    },
    yaxis: { labels: { style: { colors: textColor } } },
    grid: { borderColor: useColorModeValue('#E2E8F0', '#4A5568') },
  };

  const featureChartData = featureAdoption?.chart?.data 
    ? [{ name: 'Adoption %', data: featureAdoption.chart.data }] 
    : [];

  const planPieOptions = {
    chart: { type: 'pie' },
    labels: mrrByPlan?.chart?.labels || [],
    colors: ['#E53E3E', '#DD6B20', '#D69E2E', '#38A169', '#3182CE', '#805AD5'],
    legend: { position: 'bottom' },
    dataLabels: { enabled: true, formatter: (val) => `${val.toFixed(1)}%` },
  };

  const planPieData = mrrByPlan?.chart?.data || [];

  if (loading) {
    return (
      <Center h="80vh">
        <VStack spacing={4}>
          <Spinner size="xl" color="red.500" thickness="4px" />
          <Text color={textColorSecondary}>Loading business KPIs...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={1} mb={8}>
        <HStack>
          <Icon as={FaChartLine} boxSize={6} color={accentRed} />
          <Heading size="lg" color={textColor}>
            Business Intelligence Dashboard
          </Heading>
        </HStack>
        <Text color={textColorSecondary}>
          Internal KPIs and platform health metrics • Last updated: {new Date().toLocaleString()}
        </Text>
      </VStack>

      <VStack spacing={8} align="stretch">
        {/* P0: Core Growth KPIs */}
        <Box>
          <HStack mb={4}>
            <Badge colorScheme="red" fontSize="sm" px={2}>P0</Badge>
            <Text fontWeight="600" color={textColor}>Core Growth KPIs</Text>
          </HStack>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
            {/* MRR */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardBody>
                <Stat>
                  <StatLabel color={textColorSecondary}>
                    <HStack>
                      <Icon as={FaDollarSign} color="green.500" />
                      <Text>Monthly Recurring Revenue</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber fontSize="3xl" color={textColor}>
                    {growthKpis?.mrr?.formatted || '$0'}
                  </StatNumber>
                  <StatHelpText>
                    <StatArrow type={growthKpis?.mrr?.growth_percent >= 0 ? 'increase' : 'decrease'} />
                    {growthKpis?.mrr?.growth_percent || 0}% from last month
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            {/* Active Customers */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardBody>
                <Stat>
                  <StatLabel color={textColorSecondary}>
                    <HStack>
                      <Icon as={FaUsers} color="blue.500" />
                      <Text>Total Active Customers</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber fontSize="3xl" color={textColor}>
                    {growthKpis?.total_active_customers?.formatted || '0'}
                  </StatNumber>
                  <StatHelpText>Paying organizations</StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            {/* DAU */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardBody>
                <Stat>
                  <StatLabel color={textColorSecondary}>
                    <HStack>
                      <Icon as={FaUserCheck} color="purple.500" />
                      <Text>Daily Active Users (DAU)</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber fontSize="3xl" color={textColor}>
                    {growthKpis?.dau?.formatted || '0'}
                  </StatNumber>
                  <StatHelpText>Users logged in today</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* MRR Trend Chart */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" mt={6}>
            <CardHeader>
              <Heading size="md" color={textColor}>MRR Growth Trend (12 Months)</Heading>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                {mrrChartData.length > 0 ? (
                  <LineChart chartData={mrrChartData} chartOptions={mrrChartOptions} />
                ) : (
                  <Center h="100%">
                    <Text color={textColorSecondary}>No MRR data available</Text>
                  </Center>
                )}
              </Box>
            </CardBody>
          </Card>
        </Box>

        <Divider />

        {/* P1: User & Engagement Metrics */}
        <Box>
          <HStack mb={4}>
            <Badge colorScheme="orange" fontSize="sm" px={2}>P1</Badge>
            <Text fontWeight="600" color={textColor}>User & Engagement Metrics</Text>
          </HStack>

          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* Active Users Trend */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Flex justify="space-between" align="center">
                  <Heading size="md" color={textColor}>Active Users Trend</Heading>
                  <Select
                    size="sm"
                    w="120px"
                    value={activeUsersView}
                    onChange={(e) => setActiveUsersView(e.target.value)}
                  >
                    <option value="daily">Daily (DAU)</option>
                    <option value="weekly">Weekly (WAU)</option>
                    <option value="monthly">Monthly (MAU)</option>
                  </Select>
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  {activeUsersChartData.length > 0 ? (
                    <LineChart chartData={activeUsersChartData} chartOptions={activeUsersChartOptions} />
                  ) : (
                    <Center h="100%">
                      <Text color={textColorSecondary}>No data available</Text>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>

            {/* Customer Funnel */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Heading size="md" color={textColor}>Customer Funnel (Sign-ups vs Churn)</Heading>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  {funnelChartData.length > 0 ? (
                    <BarChart chartData={funnelChartData} chartOptions={funnelChartOptions} />
                  ) : (
                    <Center h="100%">
                      <Text color={textColorSecondary}>No data available</Text>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* Trial Conversion */}
          <Card bg={cardBg} boxShadow="lg" borderRadius="xl" mt={6}>
            <CardBody>
              <Stat>
                <StatLabel color={textColorSecondary}>
                  <HStack>
                    <Icon as={FaExchangeAlt} color="teal.500" />
                    <Text>Trial to Paid Conversion Rate (Last 30 Days)</Text>
                  </HStack>
                </StatLabel>
                <StatNumber fontSize="3xl" color={textColor}>
                  {trialConversion?.conversion_rate?.formatted || '0%'}
                </StatNumber>
                <StatHelpText>
                  {trialConversion?.trials_converted || 0} converted out of {trialConversion?.trials_started || 0} trials
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </Box>

        <Divider />

        {/* P2: Platform & Cost Metrics */}
        <Box>
          <HStack mb={4}>
            <Badge colorScheme="purple" fontSize="sm" px={2}>P2</Badge>
            <Text fontWeight="600" color={textColor}>Platform & Cost Metrics</Text>
          </HStack>

          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* AI Costs */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Flex justify="space-between" align="center">
                  <Heading size="md" color={textColor}>AI API Costs</Heading>
                  <VStack align="end" spacing={0}>
                    <Text fontSize="sm" color={textColorSecondary}>Avg per Customer</Text>
                    <Text fontWeight="bold" color="purple.500">
                      {aiCosts?.avg_cost_per_customer?.formatted || '$0'}
                    </Text>
                  </VStack>
                </Flex>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  {aiCostsChartData.length > 0 ? (
                    <LineChart chartData={aiCostsChartData} chartOptions={aiCostsChartOptions} />
                  ) : (
                    <Center h="100%">
                      <Text color={textColorSecondary}>No data available</Text>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>

            {/* Feature Adoption */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Heading size="md" color={textColor}>Feature Adoption (Top 5)</Heading>
              </CardHeader>
              <CardBody>
                <Box h="250px">
                  {featureChartData.length > 0 ? (
                    <BarChart chartData={featureChartData} chartOptions={featureChartOptions} />
                  ) : (
                    <Center h="100%">
                      <Text color={textColorSecondary}>No data available</Text>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>

        <Divider />

        {/* P3: Customer Segmentation */}
        <Box>
          <HStack mb={4}>
            <Badge colorScheme="blue" fontSize="sm" px={2}>P3</Badge>
            <Text fontWeight="600" color={textColor}>Customer Segmentation</Text>
          </HStack>

          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
            {/* MRR by Plan */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Heading size="md" color={textColor}>MRR by Subscription Plan</Heading>
              </CardHeader>
              <CardBody>
                <Box h="300px">
                  {planPieData.length > 0 ? (
                    <PieChart chartData={planPieData} chartOptions={planPieOptions} />
                  ) : (
                    <Center h="100%">
                      <Text color={textColorSecondary}>No data available</Text>
                    </Center>
                  )}
                </Box>
              </CardBody>
            </Card>

            {/* Top 10 Customers */}
            <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
              <CardHeader>
                <Heading size="md" color={textColor}>
                  <HStack>
                    <Icon as={FaCrown} color="yellow.500" />
                    <Text>Top 10 Customers by MRR</Text>
                  </HStack>
                </Heading>
              </CardHeader>
              <CardBody>
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>#</Th>
                      <Th>Customer</Th>
                      <Th isNumeric>MRR</Th>
                      <Th isNumeric>%</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {(topCustomers?.customers || []).map((customer) => (
                      <Tr key={customer.customer_id}>
                        <Td>
                          <Badge colorScheme={customer.rank <= 3 ? 'yellow' : 'gray'}>
                            {customer.rank}
                          </Badge>
                        </Td>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="500" fontSize="sm" isTruncated maxW="150px">
                              {customer.name}
                            </Text>
                            {customer.email && (
                              <Text fontSize="xs" color={textColorSecondary}>
                                {customer.email}
                              </Text>
                            )}
                          </VStack>
                        </Td>
                        <Td isNumeric fontWeight="600">{customer.formatted_mrr}</Td>
                        <Td isNumeric>
                          <Badge colorScheme="green">{customer.percentage}%</Badge>
                        </Td>
                      </Tr>
                    ))}
                    {(!topCustomers?.customers || topCustomers.customers.length === 0) && (
                      <Tr>
                        <Td colSpan={4} textAlign="center" py={4}>
                          <Text color={textColorSecondary}>No customer data available</Text>
                        </Td>
                      </Tr>
                    )}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>
      </VStack>
    </Box>
  );
}
