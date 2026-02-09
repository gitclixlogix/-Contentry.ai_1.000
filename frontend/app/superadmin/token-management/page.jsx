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
  Switch,
  FormControl,
  FormLabel,
  Input,
  Button,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  IconButton,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import {
  FaRobot,
  FaDollarSign,
  FaChartLine,
  FaBell,
  FaCog,
  FaExclamationTriangle,
  FaCheckCircle,
  FaSync,
  FaLightbulb,
  FaDatabase,
  FaClock,
  FaUsers,
} from 'react-icons/fa';
import dynamic from 'next/dynamic';
import { getApiUrl } from '@/lib/api';

const LineChart = dynamic(() => import('@/components/charts/LineChart'), { ssr: false });
const BarChart = dynamic(() => import('@/components/charts/BarChart'), { ssr: false });
const PieChart = dynamic(() => import('@/components/charts/PieChart'), { ssr: false });

export default function TokenManagementPage() {
  const [loading, setLoading] = useState(true);
  const [realtimeStats, setRealtimeStats] = useState(null);
  const [usageSummary, setUsageSummary] = useState(null);
  const [agentBreakdown, setAgentBreakdown] = useState([]);
  const [modelBreakdown, setModelBreakdown] = useState([]);
  const [topUsers, setTopUsers] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [alertConfig, setAlertConfig] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [costComparison, setCostComparison] = useState(null);
  const [daysFilter, setDaysFilter] = useState(30);
  const [refreshing, setRefreshing] = useState(false);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const accentRed = useColorModeValue('red.600', 'red.400');
  const accentGreen = useColorModeValue('green.500', 'green.400');
  const accentBlue = useColorModeValue('blue.500', 'blue.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getAuthHeaders = () => {
    const userId = localStorage.getItem('userId');
    const userStr = localStorage.getItem('contentry_user');
    let actualUserId = userId;
    if (userStr) {
      try {
        const userData = JSON.parse(userStr);
        actualUserId = userData.id || userId;
      } catch (e) {}
    }
    return {
      'x-user-id': actualUserId,
      'Content-Type': 'application/json',
    };
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const headers = getAuthHeaders();
      const baseUrl = getApiUrl();

      const [
        realtimeRes,
        summaryRes,
        agentRes,
        modelRes,
        topUsersRes,
        alertsRes,
        configRes,
        recommendationsRes,
        costRes,
      ] = await Promise.all([
        fetch(`${baseUrl}/superadmin/tokens/realtime`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/usage/summary?days=${daysFilter}`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/usage/by-agent?days=${daysFilter}`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/usage/by-model?days=${daysFilter}`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/usage/top-users?days=${daysFilter}&limit=10`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/alerts?limit=20`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/alerts/config`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/recommendations`, { headers, credentials: 'include' }),
        fetch(`${baseUrl}/superadmin/tokens/cost/comparison?days=${daysFilter}`, { headers, credentials: 'include' }),
      ]);

      const [realtime, summary, agent, model, users, alertsData, config, recs, cost] = await Promise.all([
        realtimeRes.json(),
        summaryRes.json(),
        agentRes.json(),
        modelRes.json(),
        topUsersRes.json(),
        alertsRes.json(),
        configRes.json(),
        recommendationsRes.json(),
        costRes.json(),
      ]);

      if (realtime.success) setRealtimeStats(realtime.data);
      if (summary.success) setUsageSummary(summary.data);
      if (agent.success) setAgentBreakdown(agent.data);
      if (model.success) setModelBreakdown(model.data);
      if (users.success) setTopUsers(users.data);
      if (alertsData.success) setAlerts(alertsData.data);
      if (config.success) setAlertConfig(config.data);
      if (recs.success) setRecommendations(recs.data);
      if (cost.success) setCostComparison(cost.data);
    } catch (error) {
      console.error('Error fetching token data:', error);
      toast({
        title: 'Error loading data',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [daysFilter]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAllData();
    setRefreshing(false);
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      const headers = getAuthHeaders();
      const baseUrl = getApiUrl();
      
      const res = await fetch(`${baseUrl}/superadmin/tokens/alerts/acknowledge`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ alert_id: alertId }),
      });
      
      if (res.ok) {
        setAlerts(alerts.filter(a => a.id !== alertId));
        toast({
          title: 'Alert acknowledged',
          status: 'success',
          duration: 2000,
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to acknowledge alert',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleUpdateConfig = async () => {
    try {
      const headers = getAuthHeaders();
      const baseUrl = getApiUrl();
      
      const res = await fetch(`${baseUrl}/superadmin/tokens/alerts/config`, {
        method: 'PUT',
        headers,
        credentials: 'include',
        body: JSON.stringify(alertConfig),
      });
      
      if (res.ok) {
        toast({
          title: 'Configuration saved',
          status: 'success',
          duration: 2000,
        });
        onClose();
      }
    } catch (error) {
      toast({
        title: 'Failed to save configuration',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toLocaleString() || '0';
  };

  const formatCost = (cost) => `$${cost?.toFixed(2) || '0.00'}`;

  if (loading) {
    return (
      <Center minH="60vh">
        <VStack spacing={4}>
          <Spinner size="xl" color={accentRed} thickness="4px" />
          <Text color={textColorSecondary}>Loading token analytics...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" color={textColor}>
            <Icon as={FaRobot} mr={2} color={accentRed} />
            AI Token Management
          </Heading>
          <Text color={textColorSecondary} fontSize="sm">
            Monitor and optimize AI token usage across all agents
          </Text>
        </VStack>
        <HStack spacing={3}>
          <Select 
            value={daysFilter} 
            onChange={(e) => setDaysFilter(Number(e.target.value))}
            w="150px"
            size="sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Select>
          <Tooltip label="Configure Alerts">
            <IconButton
              icon={<FaCog />}
              onClick={onOpen}
              variant="outline"
              size="sm"
            />
          </Tooltip>
          <Tooltip label="Refresh Data">
            <IconButton
              icon={<FaSync />}
              onClick={handleRefresh}
              isLoading={refreshing}
              variant="outline"
              size="sm"
            />
          </Tooltip>
        </HStack>
      </Flex>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Box mb={6}>
          {alerts.slice(0, 3).map((alert) => (
            <Alert
              key={alert.id}
              status={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
              variant="left-accent"
              mb={2}
              borderRadius="md"
            >
              <AlertIcon />
              <Box flex="1">
                <AlertTitle fontSize="sm">{alert.title}</AlertTitle>
                <AlertDescription fontSize="xs">{alert.message}</AlertDescription>
              </Box>
              <Button size="xs" onClick={() => handleAcknowledgeAlert(alert.id)}>
                Dismiss
              </Button>
            </Alert>
          ))}
        </Box>
      )}

      {/* Real-time Stats Cards */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <Icon as={FaDatabase} mr={2} />
                Today's Tokens
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {formatNumber(realtimeStats?.today?.total_tokens || 0)}
              </StatNumber>
              <StatHelpText>
                <Text as="span" color={accentBlue}>
                  {realtimeStats?.tokens_per_minute?.toFixed(1) || 0}/min
                </Text>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <Icon as={FaDollarSign} mr={2} />
                Today's API Cost
              </StatLabel>
              <StatNumber color={accentRed} fontSize="2xl">
                {formatCost(realtimeStats?.today?.api_cost_usd)}
              </StatNumber>
              <StatHelpText>
                Projected: {formatCost(realtimeStats?.projection?.projected_cost_usd)}/mo
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <Icon as={FaChartLine} mr={2} />
                API Requests
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {formatNumber(realtimeStats?.today?.request_count || 0)}
              </StatNumber>
              <StatHelpText>
                {realtimeStats?.requests_per_minute?.toFixed(2) || 0} req/min
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <Icon as={FaClock} mr={2} />
                MTD Spend
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {formatCost(realtimeStats?.projection?.current_cost_usd)}
              </StatNumber>
              <StatHelpText>
                Day {realtimeStats?.projection?.days_elapsed || 0} of month
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Cost Comparison Banner */}
      {costComparison && (
        <Card bg={cardBg} mb={6}>
          <CardBody>
            <Flex justify="space-between" align="center" flexWrap="wrap" gap={4}>
              <VStack align="start" spacing={0}>
                <Text fontSize="sm" color={textColorSecondary}>API Cost ({daysFilter}d)</Text>
                <Text fontSize="xl" fontWeight="bold" color={accentRed}>
                  {formatCost(costComparison.totals?.api_cost_usd)}
                </Text>
              </VStack>
              <VStack align="center" spacing={0}>
                <Text fontSize="sm" color={textColorSecondary}>Credits Consumed</Text>
                <Text fontSize="xl" fontWeight="bold" color={textColor}>
                  {formatNumber(costComparison.totals?.credit_cost || 0)}
                </Text>
              </VStack>
              <VStack align="center" spacing={0}>
                <Text fontSize="sm" color={textColorSecondary}>Credit Revenue</Text>
                <Text fontSize="xl" fontWeight="bold" color={accentGreen}>
                  {formatCost(costComparison.totals?.credit_revenue_usd)}
                </Text>
              </VStack>
              <VStack align="end" spacing={0}>
                <Text fontSize="sm" color={textColorSecondary}>Margin</Text>
                <Text 
                  fontSize="xl" 
                  fontWeight="bold" 
                  color={costComparison.totals?.margin_usd >= 0 ? accentGreen : accentRed}
                >
                  {formatCost(costComparison.totals?.margin_usd)} ({costComparison.totals?.margin_percent?.toFixed(1)}%)
                </Text>
              </VStack>
            </Flex>
          </CardBody>
        </Card>
      )}

      {/* Tabs for Detailed Views */}
      <Tabs colorScheme="red" variant="enclosed">
        <TabList>
          <Tab><Icon as={FaRobot} mr={2} /> By Agent</Tab>
          <Tab><Icon as={FaDatabase} mr={2} /> By Model</Tab>
          <Tab><Icon as={FaUsers} mr={2} /> Top Users</Tab>
          <Tab><Icon as={FaLightbulb} mr={2} /> Recommendations</Tab>
        </TabList>

        <TabPanels>
          {/* By Agent Tab */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <CardBody>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Agent Type</Th>
                      <Th isNumeric>Total Tokens</Th>
                      <Th isNumeric>Requests</Th>
                      <Th isNumeric>Avg Tokens/Req</Th>
                      <Th isNumeric>API Cost</Th>
                      <Th isNumeric>Credits Used</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {agentBreakdown.map((agent, idx) => (
                      <Tr key={idx}>
                        <Td>
                          <Badge colorScheme="purple" variant="subtle">
                            {agent.agent_type?.replace(/_/g, ' ').toUpperCase()}
                          </Badge>
                        </Td>
                        <Td isNumeric fontWeight="medium">{formatNumber(agent.total_tokens)}</Td>
                        <Td isNumeric>{formatNumber(agent.request_count)}</Td>
                        <Td isNumeric>{agent.avg_tokens_per_request?.toFixed(0)}</Td>
                        <Td isNumeric color={accentRed}>{formatCost(agent.api_cost_usd)}</Td>
                        <Td isNumeric>{formatNumber(agent.credit_cost)}</Td>
                      </Tr>
                    ))}
                    {agentBreakdown.length === 0 && (
                      <Tr>
                        <Td colSpan={6} textAlign="center" color={textColorSecondary}>
                          No token usage data yet. Data will appear after AI agents are used.
                        </Td>
                      </Tr>
                    )}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>

          {/* By Model Tab */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <CardBody>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Model</Th>
                      <Th>Provider</Th>
                      <Th isNumeric>Total Tokens</Th>
                      <Th isNumeric>Input Tokens</Th>
                      <Th isNumeric>Output Tokens</Th>
                      <Th isNumeric>Requests</Th>
                      <Th isNumeric>API Cost</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {modelBreakdown.map((model, idx) => (
                      <Tr key={idx}>
                        <Td>
                          <Badge 
                            colorScheme={model.provider === 'openai' ? 'green' : model.provider === 'gemini' ? 'blue' : 'purple'}
                            variant="subtle"
                          >
                            {model.model}
                          </Badge>
                        </Td>
                        <Td textTransform="capitalize">{model.provider}</Td>
                        <Td isNumeric fontWeight="medium">{formatNumber(model.total_tokens)}</Td>
                        <Td isNumeric>{formatNumber(model.input_tokens)}</Td>
                        <Td isNumeric>{formatNumber(model.output_tokens)}</Td>
                        <Td isNumeric>{formatNumber(model.request_count)}</Td>
                        <Td isNumeric color={accentRed}>{formatCost(model.api_cost_usd)}</Td>
                      </Tr>
                    ))}
                    {modelBreakdown.length === 0 && (
                      <Tr>
                        <Td colSpan={7} textAlign="center" color={textColorSecondary}>
                          No model usage data yet.
                        </Td>
                      </Tr>
                    )}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Top Users Tab */}
          <TabPanel px={0}>
            <Card bg={cardBg}>
              <CardBody>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>User</Th>
                      <Th>Plan</Th>
                      <Th isNumeric>Total Tokens</Th>
                      <Th isNumeric>Requests</Th>
                      <Th isNumeric>API Cost</Th>
                      <Th isNumeric>Credits Used</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {topUsers.map((user, idx) => (
                      <Tr key={idx}>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="medium">{user.name || 'Unknown'}</Text>
                            <Text fontSize="xs" color={textColorSecondary}>{user.email}</Text>
                          </VStack>
                        </Td>
                        <Td>
                          <Badge 
                            colorScheme={
                              user.plan === 'business' ? 'purple' : 
                              user.plan === 'pro' ? 'blue' : 
                              user.plan === 'creator' ? 'green' : 'gray'
                            }
                          >
                            {user.plan?.toUpperCase()}
                          </Badge>
                        </Td>
                        <Td isNumeric fontWeight="medium">{formatNumber(user.total_tokens)}</Td>
                        <Td isNumeric>{formatNumber(user.request_count)}</Td>
                        <Td isNumeric color={accentRed}>{formatCost(user.api_cost_usd)}</Td>
                        <Td isNumeric>{formatNumber(user.credit_cost)}</Td>
                      </Tr>
                    ))}
                    {topUsers.length === 0 && (
                      <Tr>
                        <Td colSpan={6} textAlign="center" color={textColorSecondary}>
                          No user token data yet.
                        </Td>
                      </Tr>
                    )}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Recommendations Tab */}
          <TabPanel px={0}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              {recommendations.map((rec, idx) => (
                <Card key={idx} bg={cardBg} borderLeft="4px solid" borderLeftColor={
                  rec.priority === 'high' ? 'red.500' : 
                  rec.priority === 'medium' ? 'orange.500' : 'blue.500'
                }>
                  <CardBody>
                    <VStack align="start" spacing={2}>
                      <HStack>
                        <Badge colorScheme={
                          rec.priority === 'high' ? 'red' : 
                          rec.priority === 'medium' ? 'orange' : 'blue'
                        }>
                          {rec.priority?.toUpperCase()}
                        </Badge>
                        <Badge variant="outline">{rec.type?.replace(/_/g, ' ')}</Badge>
                      </HStack>
                      <Text fontWeight="bold" color={textColor}>{rec.title}</Text>
                      <Text fontSize="sm" color={textColorSecondary}>{rec.description}</Text>
                      {rec.potential_savings_usd && (
                        <Text fontSize="sm" color={accentGreen} fontWeight="medium">
                          💰 Potential savings: {formatCost(rec.potential_savings_usd)}
                        </Text>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Alert Configuration Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent bg={cardBg}>
          <ModalHeader>Alert Configuration</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {alertConfig && (
              <VStack spacing={4} align="stretch">
                <FormControl display="flex" alignItems="center">
                  <FormLabel mb={0}>Enable Alerts</FormLabel>
                  <Switch 
                    isChecked={alertConfig.enabled}
                    onChange={(e) => setAlertConfig({...alertConfig, enabled: e.target.checked})}
                    colorScheme="red"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center">
                  <FormLabel mb={0}>Email Notifications</FormLabel>
                  <Switch 
                    isChecked={alertConfig.email_notifications}
                    onChange={(e) => setAlertConfig({...alertConfig, email_notifications: e.target.checked})}
                    colorScheme="red"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Email Recipient</FormLabel>
                  <Input 
                    value={alertConfig.email_recipient || ''}
                    onChange={(e) => setAlertConfig({...alertConfig, email_recipient: e.target.value})}
                    placeholder="contact@contentry.ai"
                  />
                </FormControl>

                <Divider />

                <Text fontWeight="bold">Thresholds</Text>

                <SimpleGrid columns={2} spacing={4}>
                  <FormControl>
                    <FormLabel fontSize="sm">Daily Token Limit</FormLabel>
                    <Input 
                      type="number"
                      value={alertConfig.thresholds?.daily_tokens || 100000}
                      onChange={(e) => setAlertConfig({
                        ...alertConfig, 
                        thresholds: {...alertConfig.thresholds, daily_tokens: parseInt(e.target.value)}
                      })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontSize="sm">Daily Cost Limit ($)</FormLabel>
                    <Input 
                      type="number"
                      step="0.01"
                      value={alertConfig.thresholds?.daily_cost_usd || 10}
                      onChange={(e) => setAlertConfig({
                        ...alertConfig, 
                        thresholds: {...alertConfig.thresholds, daily_cost_usd: parseFloat(e.target.value)}
                      })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontSize="sm">Monthly Budget ($)</FormLabel>
                    <Input 
                      type="number"
                      step="1"
                      value={alertConfig.thresholds?.monthly_budget_usd || 500}
                      onChange={(e) => setAlertConfig({
                        ...alertConfig, 
                        thresholds: {...alertConfig.thresholds, monthly_budget_usd: parseFloat(e.target.value)}
                      })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontSize="sm">Warning at (%)</FormLabel>
                    <Input 
                      type="number"
                      value={alertConfig.thresholds?.warning_percent || 80}
                      onChange={(e) => setAlertConfig({
                        ...alertConfig, 
                        thresholds: {...alertConfig.thresholds, warning_percent: parseInt(e.target.value)}
                      })}
                    />
                  </FormControl>
                </SimpleGrid>

                <FormControl>
                  <FormLabel fontSize="sm">Notification Cooldown (minutes)</FormLabel>
                  <Input 
                    type="number"
                    value={alertConfig.notification_cooldown_minutes || 60}
                    onChange={(e) => setAlertConfig({
                      ...alertConfig, 
                      notification_cooldown_minutes: parseInt(e.target.value)
                    })}
                  />
                </FormControl>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
            <Button colorScheme="red" onClick={handleUpdateConfig}>Save Configuration</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
