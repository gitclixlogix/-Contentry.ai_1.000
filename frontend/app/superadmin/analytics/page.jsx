'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Spinner,
  Center,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Progress,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Select,
  Flex,
  Avatar,
} from '@chakra-ui/react';
import {
  FaChartBar,
  FaGlobe,
  FaLanguage,
  FaHeartbeat,
  FaDollarSign,
  FaUsers,
  FaTrophy,
  FaMapMarkerAlt,
} from 'react-icons/fa';
import dynamic from 'next/dynamic';
import { getApiUrl } from '@/lib/api';

// Dynamic imports for charts
const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  
  // Analytics data state
  const [geoData, setGeoData] = useState({ countries: [], total_users: 0, total_mrr: 0 });
  const [languageData, setLanguageData] = useState({ languages: [], total_users: 0 });
  const [healthData, setHealthData] = useState({ stickiness: 0, dau: 0, mau: 0, power_users: [] });
  const [revenueData, setRevenueData] = useState({ arpu: 0, arpu_trend: [], mrr_movement: {} });
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  
  // Fetch all analytics data
  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'x-user-id': userId,
      };
      
      const [geoRes, langRes, healthRes, revenueRes] = await Promise.all([
        fetch(`${getApiUrl()}/superadmin/analytics/geographic`, { headers }),
        fetch(`${getApiUrl()}/superadmin/analytics/languages`, { headers }),
        fetch(`${getApiUrl()}/superadmin/analytics/health`, { headers }),
        fetch(`${getApiUrl()}/superadmin/analytics/revenue`, { headers }),
      ]);
      
      if (geoRes.ok) setGeoData(await geoRes.json());
      if (langRes.ok) setLanguageData(await langRes.json());
      if (healthRes.ok) setHealthData(await healthRes.json());
      if (revenueRes.ok) setRevenueData(await revenueRes.json());
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };
  
  const formatPercent = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };
  
  // Chart configurations
  const languageChartOptions = {
    chart: { type: 'bar', toolbar: { show: false } },
    plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
    colors: ['#E53E3E'],
    xaxis: { categories: languageData.languages?.slice(0, 10).map(l => l.name) || [] },
    dataLabels: { enabled: false },
  };
  
  const languageChartSeries = [{
    name: 'Users',
    data: languageData.languages?.slice(0, 10).map(l => l.count) || [],
  }];
  
  const arpuChartOptions = {
    chart: { type: 'line', toolbar: { show: false } },
    stroke: { curve: 'smooth', width: 3 },
    colors: ['#38A169'],
    xaxis: { categories: revenueData.arpu_trend?.map(d => d.month) || [] },
    yaxis: { labels: { formatter: (val) => `$${val.toFixed(2)}` } },
  };
  
  const arpuChartSeries = [{
    name: 'ARPU',
    data: revenueData.arpu_trend?.map(d => d.arpu) || [],
  }];
  
  const mrrMovementOptions = {
    chart: { type: 'bar', stacked: true, toolbar: { show: false } },
    plotOptions: { bar: { horizontal: false, borderRadius: 4 } },
    colors: ['#38A169', '#E53E3E', '#3182CE', '#805AD5'],
    xaxis: { categories: ['MRR Movement'] },
    legend: { position: 'bottom' },
  };
  
  const mrrMovementSeries = [
    { name: 'New', data: [revenueData.mrr_movement?.new || 0] },
    { name: 'Churned', data: [-(revenueData.mrr_movement?.churned || 0)] },
    { name: 'Expansion', data: [revenueData.mrr_movement?.expansion || 0] },
    { name: 'Contraction', data: [-(revenueData.mrr_movement?.contraction || 0)] },
  ];
  
  if (loading) {
    return (
      <Center h="400px">
        <Spinner size="xl" color="red.500" />
      </Center>
    );
  }
  
  return (
    <Box>
      {/* Page Header */}
      <VStack align="stretch" spacing={1} mb={6}>
        <HStack>
          <Box as={FaChartBar} boxSize={6} color="red.500" />
          <Heading size="lg" color={textColor}>Analytics & Reports</Heading>
        </HStack>
        <Text color={mutedColor}>Deep insights and segmented analytics for strategic decision-making</Text>
      </VStack>
      
      <Tabs index={activeTab} onChange={setActiveTab} colorScheme="red" variant="enclosed">
        <TabList>
          <Tab><HStack><FaGlobe /><Text>Geographic</Text></HStack></Tab>
          <Tab><HStack><FaLanguage /><Text>Languages</Text></HStack></Tab>
          <Tab><HStack><FaHeartbeat /><Text>Customer Health</Text></HStack></Tab>
          <Tab><HStack><FaDollarSign /><Text>Revenue</Text></HStack></Tab>
        </TabList>
        
        <TabPanels>
          {/* Geographic Distribution */}
          <TabPanel px={0} pt={6}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Countries Reached</StatLabel>
                    <StatNumber color={textColor}>{geoData.countries?.length || 0}</StatNumber>
                    <StatHelpText>Global presence</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>International MRR</StatLabel>
                    <StatNumber color="green.500">{formatCurrency(geoData.total_mrr)}</StatNumber>
                    <StatHelpText>From all regions</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            <Card bg={cardBg}>
              <CardHeader>
                <HStack>
                  <FaMapMarkerAlt />
                  <Heading size="md">Users by Country</Heading>
                </HStack>
              </CardHeader>
              <CardBody>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Rank</Th>
                      <Th>Country</Th>
                      <Th isNumeric>Users</Th>
                      <Th isNumeric>MRR</Th>
                      <Th>Share</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {geoData.countries?.slice(0, 15).map((country, idx) => (
                      <Tr key={country.code}>
                        <Td fontWeight="bold">#{idx + 1}</Td>
                        <Td>
                          <HStack>
                            <Text fontSize="xl">{country.flag || '🌍'}</Text>
                            <Text>{country.name}</Text>
                          </HStack>
                        </Td>
                        <Td isNumeric>{country.user_count}</Td>
                        <Td isNumeric>{formatCurrency(country.mrr)}</Td>
                        <Td>
                          <Progress 
                            value={(country.user_count / (geoData.total_users || 1)) * 100} 
                            colorScheme="red" 
                            size="sm" 
                            borderRadius="full"
                          />
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Language Usage */}
          <TabPanel px={0} pt={6}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Languages Used</StatLabel>
                    <StatNumber color={textColor}>{languageData.languages?.length || 0}</StatNumber>
                    <StatHelpText>UI language preferences</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Top Language</StatLabel>
                    <StatNumber color="blue.500">{languageData.languages?.[0]?.name || 'English'}</StatNumber>
                    <StatHelpText>{languageData.languages?.[0]?.count || 0} users</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            <Card bg={cardBg}>
              <CardHeader>
                <HStack>
                  <FaLanguage />
                  <Heading size="md">Language Distribution</Heading>
                </HStack>
              </CardHeader>
              <CardBody>
                {typeof window !== 'undefined' && (
                  <Chart
                    options={languageChartOptions}
                    series={languageChartSeries}
                    type="bar"
                    height={350}
                  />
                )}
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Customer Health */}
          <TabPanel px={0} pt={6}>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Stickiness Ratio (DAU/MAU)</StatLabel>
                    <StatNumber color={healthData.stickiness > 0.2 ? 'green.500' : 'orange.500'}>
                      {formatPercent(healthData.stickiness)}
                    </StatNumber>
                    <StatHelpText>{healthData.stickiness > 0.2 ? 'Healthy' : 'Needs improvement'}</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Daily Active Users</StatLabel>
                    <StatNumber color={textColor}>{healthData.dau}</StatNumber>
                    <StatHelpText>Today</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Monthly Active Users</StatLabel>
                    <StatNumber color={textColor}>{healthData.mau}</StatNumber>
                    <StatHelpText>Last 30 days</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            <Card bg={cardBg}>
              <CardHeader>
                <HStack>
                  <FaTrophy color="gold" />
                  <Heading size="md">Power Users (Top 10%)</Heading>
                </HStack>
              </CardHeader>
              <CardBody>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Rank</Th>
                      <Th>User</Th>
                      <Th>Company</Th>
                      <Th isNumeric>Sessions (30d)</Th>
                      <Th isNumeric>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {healthData.power_users?.slice(0, 10).map((user, idx) => (
                      <Tr key={user.id}>
                        <Td>
                          <Badge colorScheme={idx < 3 ? 'gold' : 'gray'}>#{idx + 1}</Badge>
                        </Td>
                        <Td>
                          <HStack>
                            <Avatar size="sm" name={user.full_name} />
                            <VStack align="start" spacing={0}>
                              <Text fontWeight="500">{user.full_name}</Text>
                              <Text fontSize="xs" color={mutedColor}>{user.email}</Text>
                            </VStack>
                          </HStack>
                        </Td>
                        <Td>{user.company_name || '-'}</Td>
                        <Td isNumeric fontWeight="bold">{user.session_count}</Td>
                        <Td isNumeric>{user.action_count}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Revenue Analytics */}
          <TabPanel px={0} pt={6}>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Average Revenue Per User</StatLabel>
                    <StatNumber color="green.500">{formatCurrency(revenueData.arpu)}</StatNumber>
                    <StatHelpText>Current ARPU</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Net MRR Change</StatLabel>
                    <StatNumber color={(revenueData.mrr_movement?.net || 0) >= 0 ? 'green.500' : 'red.500'}>
                      {formatCurrency(revenueData.mrr_movement?.net || 0)}
                    </StatNumber>
                    <StatHelpText>This month</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Expansion Revenue</StatLabel>
                    <StatNumber color="blue.500">{formatCurrency(revenueData.mrr_movement?.expansion || 0)}</StatNumber>
                    <StatHelpText>Upgrades this month</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">ARPU Trend (12 Months)</Heading>
                </CardHeader>
                <CardBody>
                  {typeof window !== 'undefined' && (
                    <Chart
                      options={arpuChartOptions}
                      series={arpuChartSeries}
                      type="line"
                      height={300}
                    />
                  )}
                </CardBody>
              </Card>
              
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">MRR Movement (Waterfall)</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <HStack justify="space-between">
                      <Text color={mutedColor}>New MRR</Text>
                      <Text fontWeight="bold" color="green.500">+{formatCurrency(revenueData.mrr_movement?.new || 0)}</Text>
                    </HStack>
                    <HStack justify="space-between">
                      <Text color={mutedColor}>Churned MRR</Text>
                      <Text fontWeight="bold" color="red.500">-{formatCurrency(revenueData.mrr_movement?.churned || 0)}</Text>
                    </HStack>
                    <HStack justify="space-between">
                      <Text color={mutedColor}>Expansion MRR</Text>
                      <Text fontWeight="bold" color="blue.500">+{formatCurrency(revenueData.mrr_movement?.expansion || 0)}</Text>
                    </HStack>
                    <HStack justify="space-between">
                      <Text color={mutedColor}>Contraction MRR</Text>
                      <Text fontWeight="bold" color="orange.500">-{formatCurrency(revenueData.mrr_movement?.contraction || 0)}</Text>
                    </HStack>
                    <Box borderTop="2px" borderColor={mutedColor} pt={2}>
                      <HStack justify="space-between">
                        <Text fontWeight="bold">Net MRR Change</Text>
                        <Text fontWeight="bold" fontSize="lg" color={(revenueData.mrr_movement?.net || 0) >= 0 ? 'green.500' : 'red.500'}>
                          {(revenueData.mrr_movement?.net || 0) >= 0 ? '+' : ''}{formatCurrency(revenueData.mrr_movement?.net || 0)}
                        </Text>
                      </HStack>
                    </Box>
                  </VStack>
                </CardBody>
              </Card>
            </SimpleGrid>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}
