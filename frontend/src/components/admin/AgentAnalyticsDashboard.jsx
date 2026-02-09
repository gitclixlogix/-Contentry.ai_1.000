'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Flex,
  VStack,
  HStack,
  Badge,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Select,
  useColorModeValue,
  Icon,
  Spinner,
  Center,
  useToast,
  Divider,
  Tooltip,
} from '@chakra-ui/react';
import { 
  FaRobot, 
  FaBrain, 
  FaBolt, 
  FaCoins, 
  FaChartLine, 
  FaClock,
  FaCheckCircle,
  FaLightbulb,
  FaRecycle,
  FaMagic
} from 'react-icons/fa';
import api from '@/lib/api';

const tierColors = {
  top_tier: { bg: 'blue.600', light: 'blue.200', text: 'Top Tier', icon: FaBrain },
  balanced: { bg: 'blue.500', light: 'blue.100', text: 'Balanced', icon: FaBolt },
  fast: { bg: 'green.500', light: 'green.100', text: 'Fast', icon: FaCheckCircle },
};

const operationIcons = {
  content_generation: FaMagic,
  content_rewrite: FaRecycle,
  content_analysis: FaChartLine,
  content_ideation: FaLightbulb,
  content_repurpose: FaRecycle,
  content_optimization: FaCheckCircle,
};

export default function AgentAnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const toast = useToast();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const secondaryText = useColorModeValue('gray.600', 'gray.400');
  
  useEffect(() => {
    fetchData();
  }, [timeRange]);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, modelInfoRes] = await Promise.all([
        api.get(`/agent/usage-analytics?days=${timeRange}`),
        api.get('/agent/model-info')
      ]);
      
      setAnalytics(analyticsRes.data);
      setModelInfo(modelInfoRes.data);
    } catch (error) {
      console.error('Error fetching agent analytics:', error);
      toast({
        title: 'Error loading analytics',
        description: error.response?.data?.detail || 'Failed to load data',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <Center h="400px">
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.500" />
          <Text color={secondaryText}>Loading AI Agent Analytics...</Text>
        </VStack>
      </Center>
    );
  }
  
  if (!analytics) {
    return (
      <Center h="400px">
        <Text color={secondaryText}>No analytics data available</Text>
      </Center>
    );
  }
  
  return (
    <Box>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <HStack spacing={3}>
          <Icon as={FaRobot} boxSize={8} color="blue.500" />
          <VStack align="start" spacing={0}>
            <Heading size="lg" color={textColor}>AI Content Agent Analytics</Heading>
            <Text color={secondaryText} fontSize="sm">
              Monitor intelligent model selection and cost optimization
            </Text>
          </VStack>
        </HStack>
        <Select 
          value={timeRange} 
          onChange={(e) => setTimeRange(Number(e.target.value))}
          w="150px"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </Select>
      </Flex>
      
      {/* Summary Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            <Stat>
              <StatLabel color={secondaryText}>Total Requests</StatLabel>
              <StatNumber color={textColor}>{analytics.totals.requests.toLocaleString()}</StatNumber>
              <StatHelpText>
                <HStack>
                  <Icon as={FaChartLine} color="green.500" />
                  <Text>Agent-powered operations</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            <Stat>
              <StatLabel color={secondaryText}>Total Tokens</StatLabel>
              <StatNumber color={textColor}>{analytics.totals.tokens.toLocaleString()}</StatNumber>
              <StatHelpText>
                <HStack>
                  <Icon as={FaBrain} color="blue.600" />
                  <Text>Avg: {Math.round(analytics.averages.tokens_per_request)} per request</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            <Stat>
              <StatLabel color={secondaryText}>Total Cost</StatLabel>
              <StatNumber color={textColor}>${analytics.totals.cost.toFixed(4)}</StatNumber>
              <StatHelpText>
                <HStack>
                  <Icon as={FaCoins} color="yellow.500" />
                  <Text>${analytics.averages.cost_per_request.toFixed(6)} per request</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            <Stat>
              <StatLabel color={secondaryText}>Avg Response Time</StatLabel>
              <StatNumber color={textColor}>{Math.round(analytics.averages.duration_ms)}ms</StatNumber>
              <StatHelpText>
                <HStack>
                  <Icon as={FaClock} color="blue.500" />
                  <Text>Across all models</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Cost Savings Card */}
      <Card bg="green.50" borderWidth="2px" borderColor="green.200" mb={6}>
        <CardBody>
          <Flex align="center" justify="space-between">
            <HStack spacing={4}>
              <Icon as={FaCoins} boxSize={10} color="green.500" />
              <VStack align="start" spacing={0}>
                <Text fontWeight="bold" color="green.800" fontSize="lg">
                  Intelligent Model Selection Savings
                </Text>
                <Text color="green.600" fontSize="sm">
                  Estimated savings from using optimal models vs. always using top-tier
                </Text>
              </VStack>
            </HStack>
            <VStack align="end" spacing={0}>
              <Text fontSize="3xl" fontWeight="bold" color="green.600">
                ${analytics.cost_savings_estimate.savings.toFixed(4)}
              </Text>
              <Badge colorScheme="green" fontSize="sm">
                {analytics.cost_savings_estimate.savings > 0 
                  ? `${((1 - analytics.totals.cost / analytics.cost_savings_estimate.potential_top_tier_cost) * 100).toFixed(1)}% saved`
                  : 'Optimizing...'}
              </Badge>
            </VStack>
          </Flex>
        </CardBody>
      </Card>
      
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {/* Usage by Model Tier */}
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardHeader pb={2}>
            <Heading size="md" color={textColor}>Usage by Model Tier</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {Object.entries(analytics.by_tier).map(([tier, data]) => {
                const tierInfo = tierColors[tier] || tierColors.fast;
                const percentage = analytics.totals.requests > 0 
                  ? (data.requests / analytics.totals.requests * 100)
                  : 0;
                
                return (
                  <Box key={tier}>
                    <Flex justify="space-between" mb={1}>
                      <HStack>
                        <Icon as={tierInfo.icon} color={tierInfo.bg} />
                        <Text fontWeight="600" color={textColor}>{tierInfo.text}</Text>
                      </HStack>
                      <Badge colorScheme={tier === 'top_tier' ? 'blue' : tier === 'balanced' ? 'blue' : 'green'}>
                        {data.requests} requests
                      </Badge>
                    </Flex>
                    <Progress 
                      value={percentage} 
                      colorScheme={tier === 'top_tier' ? 'blue' : tier === 'balanced' ? 'blue' : 'green'}
                      borderRadius="full"
                      size="sm"
                    />
                    <Flex justify="space-between" mt={1}>
                      <Text fontSize="xs" color={secondaryText}>
                        {data.tokens.toLocaleString()} tokens
                      </Text>
                      <Text fontSize="xs" color={secondaryText}>
                        ${data.cost.toFixed(4)}
                      </Text>
                    </Flex>
                  </Box>
                );
              })}
            </VStack>
          </CardBody>
        </Card>
        
        {/* Usage by Operation */}
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardHeader pb={2}>
            <Heading size="md" color={textColor}>Usage by Operation</Heading>
          </CardHeader>
          <CardBody>
            <Table size="sm" variant="simple">
              <Thead>
                <Tr>
                  <Th color={secondaryText}>Operation</Th>
                  <Th isNumeric color={secondaryText}>Requests</Th>
                  <Th isNumeric color={secondaryText}>Tokens</Th>
                  <Th isNumeric color={secondaryText}>Cost</Th>
                </Tr>
              </Thead>
              <Tbody>
                {Object.entries(analytics.by_operation).map(([op, data]) => {
                  const OpIcon = operationIcons[op] || FaRobot;
                  return (
                    <Tr key={op}>
                      <Td>
                        <HStack>
                          <Icon as={OpIcon} color="blue.500" boxSize={4} />
                          <Text color={textColor} fontSize="sm">
                            {op.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </Text>
                        </HStack>
                      </Td>
                      <Td isNumeric color={textColor}>{data.requests}</Td>
                      <Td isNumeric color={textColor}>{data.tokens.toLocaleString()}</Td>
                      <Td isNumeric color={textColor}>${data.cost.toFixed(4)}</Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Model Information */}
      {modelInfo && (
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} mt={6}>
          <CardHeader>
            <Heading size="md" color={textColor}>Available Model Tiers</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              {Object.entries(modelInfo.tiers).map(([tier, info]) => {
                const tierInfo = tierColors[tier] || tierColors.fast;
                const lightBg = tier === 'top_tier' ? 'blue.50' : tier === 'balanced' ? 'blue.50' : 'green.50';
                return (
                  <Box 
                    key={tier}
                    p={4}
                    borderWidth="1px"
                    borderColor={borderColor}
                    borderRadius="lg"
                    bg={lightBg}
                    _dark={{ bg: 'gray.700' }}
                  >
                    <HStack mb={2}>
                      <Icon as={tierInfo.icon} color={tierInfo.bg} boxSize={5} />
                      <Text fontWeight="bold" color={textColor}>{info.name}</Text>
                    </HStack>
                    <Text fontSize="sm" color={secondaryText} mb={2}>
                      {info.model} ({info.provider})
                    </Text>
                    <Text fontSize="xs" color={secondaryText} mb={2}>
                      {info.description}
                    </Text>
                    <Divider my={2} />
                    <VStack align="start" spacing={1}>
                      <Text fontSize="xs" fontWeight="600" color={textColor}>Strengths:</Text>
                      <Flex wrap="wrap" gap={1}>
                        {info.strengths.map((s, i) => (
                          <Badge key={i} size="sm" colorScheme="gray" fontSize="xs">
                            {s}
                          </Badge>
                        ))}
                      </Flex>
                    </VStack>
                  </Box>
                );
              })}
            </SimpleGrid>
          </CardBody>
        </Card>
      )}
    </Box>
  );
}
