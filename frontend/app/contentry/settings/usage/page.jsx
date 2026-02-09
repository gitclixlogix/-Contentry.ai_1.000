'use client';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Heading,
  SimpleGrid,
  Card,
  CardBody,
  Text,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Flex,
  Icon,
  useColorModeValue,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  HStack,
  VStack,
  Spinner,
  Center,
  Select,
} from '@chakra-ui/react';
import { FaChartLine, FaCoins, FaCalendarAlt, FaArrowUp, FaShoppingCart, FaHistory } from 'react-icons/fa';
import api from '@/lib/api';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';

// Dynamically import chart components
const LineChart = dynamic(
  () => import('@/components/charts/LineChart'),
  { ssr: false }
);

const BarChart = dynamic(
  () => import('@/components/charts/BarChart'),
  { ssr: false }
);

// Action display names
const ACTION_NAMES = {
  content_analysis: 'Content Analysis',
  quick_analysis: 'Quick Analysis',
  content_generation: 'Content Generation',
  ai_rewrite: 'AI Rewrite',
  iterative_rewrite: 'Iterative Rewrite',
  image_generation: 'Image Generation',
  image_analysis: 'Image Analysis',
  image_regeneration: 'Image Regeneration',
  voice_dictation: 'Voice Dictation',
  voice_commands: 'Voice Commands',
  ai_voice_assistant: 'Olivia AI',
  voice_content_generation: 'Voice Content',
  url_sentiment_analysis: 'URL Sentiment',
  brand_mention_tracking: 'Brand Tracking',
  competitor_analysis: 'Competitor Analysis',
  direct_publish: 'Direct Publish',
  scheduled_post: 'Scheduled Post',
  pre_publish_reanalysis: 'Pre-Publish Check',
  knowledge_base_upload: 'Knowledge Upload',
  strategic_profile_creation: 'Profile Creation',
  export_to_pdf: 'PDF Export',
  credit_purchase: 'Credit Purchase',
  plan_change: 'Plan Change',
};

// Action colors for badges
const ACTION_COLORS = {
  content_analysis: 'blue',
  quick_analysis: 'cyan',
  content_generation: 'purple',
  ai_rewrite: 'orange',
  iterative_rewrite: 'red',
  image_generation: 'pink',
  direct_publish: 'green',
  scheduled_post: 'teal',
  credit_purchase: 'yellow',
};

export default function Usage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [creditBalance, setCreditBalance] = useState(null);
  const [usageSummary, setUsageSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [creditCosts, setCreditCosts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodDays, setPeriodDays] = useState(30);

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const boxBg = useColorModeValue('gray.50', 'gray.700');
  const tableBg = useColorModeValue('gray.50', 'gray.700');

  const loadCreditBalance = useCallback(async () => {
    try {
      const response = await api.get('/credits/balance');
      if (response.data?.data) {
        setCreditBalance(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load credit balance:', error);
    }
  }, []);

  const loadUsageSummary = useCallback(async () => {
    try {
      const response = await api.get(`/credits/usage?days=${periodDays}`);
      if (response.data?.data) {
        setUsageSummary(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load usage summary:', error);
    }
  }, [periodDays]);

  const loadTransactions = useCallback(async () => {
    try {
      const response = await api.get('/credits/history?limit=20');
      if (response.data?.data?.transactions) {
        setTransactions(response.data.data.transactions);
      }
    } catch (error) {
      console.error('Failed to load transactions:', error);
    }
  }, []);

  const loadCreditCosts = useCallback(async () => {
    try {
      const response = await api.get('/credits/costs');
      if (response.data?.data) {
        setCreditCosts(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load credit costs:', error);
    }
  }, []);

  useEffect(() => {
    Promise.all([
      loadCreditBalance(),
      loadUsageSummary(),
      loadTransactions(),
      loadCreditCosts(),
    ]).finally(() => setLoading(false));
  }, [loadCreditBalance, loadUsageSummary, loadTransactions, loadCreditCosts]);

  useEffect(() => {
    loadUsageSummary();
  }, [periodDays, loadUsageSummary]);

  const getUsagePercent = () => {
    if (!creditBalance) return 0;
    const { credits_used_this_month, monthly_allowance } = creditBalance;
    if (monthly_allowance <= 0) return 0;
    return Math.min(100, (credits_used_this_month / monthly_allowance) * 100);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Center minH="50vh" pt="80px">
        <Spinner size="xl" color="brand.500" thickness="4px" />
      </Center>
    );
  }

  return (
    <Box px={{ base: 2, md: 4 }} pt={{ base: '80px', md: '80px' }}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size={{ base: 'md', md: 'lg' }}>
          Credit Usage & Analytics
        </Heading>
        <Button 
          colorScheme="brand" 
          size="sm" 
          leftIcon={<FaShoppingCart />}
          onClick={() => router.push('/contentry/settings/billing')}
        >
          Buy Credits
        </Button>
      </Flex>

      {/* Summary Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={8}>
        {/* Current Balance */}
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <HStack>
                  <Icon as={FaCoins} color={brandColor} />
                  <Text>Available Credits</Text>
                </HStack>
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {creditBalance?.credits_balance?.toLocaleString() || 0}
              </StatNumber>
              <StatHelpText>
                Plan: {creditBalance?.plan_name || 'Free'}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        {/* Used This Month */}
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <HStack>
                  <Icon as={FaChartLine} color="orange.500" />
                  <Text>Used This Month</Text>
                </HStack>
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {creditBalance?.credits_used_this_month?.toLocaleString() || 0}
              </StatNumber>
              <StatHelpText>
                of {creditBalance?.monthly_allowance?.toLocaleString() || 0} allowance
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        {/* Usage Period */}
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <HStack>
                  <Icon as={FaCalendarAlt} color="green.500" />
                  <Text>Period Usage ({periodDays}d)</Text>
                </HStack>
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {usageSummary?.total_credits_used?.toLocaleString() || 0}
              </StatNumber>
              <StatHelpText>
                {usageSummary?.total_transactions || 0} transactions
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        {/* Usage Percentage */}
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel color={textColorSecondary}>
                <HStack>
                  <Icon as={FaArrowUp} color="purple.500" />
                  <Text>Monthly Usage</Text>
                </HStack>
              </StatLabel>
              <StatNumber color={textColor} fontSize="2xl">
                {getUsagePercent().toFixed(1)}%
              </StatNumber>
              <Progress 
                value={getUsagePercent()} 
                colorScheme={getUsagePercent() > 80 ? 'red' : getUsagePercent() > 60 ? 'orange' : 'green'} 
                size="sm" 
                borderRadius="full"
                mt={2}
              />
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Usage By Action */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
        {/* Usage Breakdown */}
        <Card bg={cardBg}>
          <CardBody>
            <Flex justify="space-between" align="center" mb={4}>
              <Heading size="sm" color={textColor}>Usage by Feature</Heading>
              <Select 
                size="sm" 
                w="120px" 
                value={periodDays}
                onChange={(e) => setPeriodDays(Number(e.target.value))}
              >
                <option value={7}>7 days</option>
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
              </Select>
            </Flex>
            
            <VStack spacing={3} align="stretch">
              {usageSummary?.usage_by_action?.slice(0, 8).map((item, idx) => (
                <Box key={idx}>
                  <Flex justify="space-between" mb={1}>
                    <HStack>
                      <Badge colorScheme={ACTION_COLORS[item.action] || 'gray'} fontSize="xs">
                        {ACTION_NAMES[item.action] || item.action}
                      </Badge>
                      <Text fontSize="xs" color={textColorSecondary}>
                        ({item.count} times)
                      </Text>
                    </HStack>
                    <Text fontWeight="bold" color={textColor}>
                      {item.credits?.toLocaleString()}
                    </Text>
                  </Flex>
                  <Progress 
                    value={(item.credits / (usageSummary?.total_credits_used || 1)) * 100}
                    colorScheme={ACTION_COLORS[item.action] || 'gray'}
                    size="xs"
                    borderRadius="full"
                  />
                </Box>
              ))}
              
              {(!usageSummary?.usage_by_action || usageSummary.usage_by_action.length === 0) && (
                <Text color={textColorSecondary} textAlign="center" py={4}>
                  No usage data for this period
                </Text>
              )}
            </VStack>
          </CardBody>
        </Card>

        {/* Credit Costs Reference */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="sm" color={textColor} mb={4}>Credit Costs Reference</Heading>
            
            <VStack spacing={4} align="stretch">
              {creditCosts?.categorized && Object.entries(creditCosts.categorized).slice(0, 3).map(([category, actions]) => (
                <Box key={category}>
                  <Text fontWeight="bold" color={textColor} fontSize="sm" mb={2} textTransform="capitalize">
                    {category.replace(/_/g, ' ')}
                  </Text>
                  <SimpleGrid columns={2} spacing={2}>
                    {Object.entries(actions).map(([action, info]) => (
                      <HStack key={action} justify="space-between" bg={boxBg} p={2} borderRadius="md">
                        <Text fontSize="xs" color={textColorSecondary}>
                          {ACTION_NAMES[action] || action.replace(/_/g, ' ')}
                        </Text>
                        <Badge colorScheme="brand">{info.cost}</Badge>
                      </HStack>
                    ))}
                  </SimpleGrid>
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Recent Transactions */}
      <Card bg={cardBg} mb={8}>
        <CardBody>
          <Flex justify="space-between" align="center" mb={4}>
            <HStack>
              <Icon as={FaHistory} color={brandColor} />
              <Heading size="sm" color={textColor}>Recent Transactions</Heading>
            </HStack>
            <Button size="xs" variant="ghost" onClick={loadTransactions}>
              Refresh
            </Button>
          </Flex>
          
          <Box overflowX="auto">
            <Table size="sm">
              <Thead>
                <Tr bg={tableBg}>
                  <Th>Date</Th>
                  <Th>Action</Th>
                  <Th isNumeric>Credits</Th>
                  <Th isNumeric>Balance After</Th>
                </Tr>
              </Thead>
              <Tbody>
                {transactions.map((tx, idx) => (
                  <Tr key={idx}>
                    <Td fontSize="sm" color={textColorSecondary}>
                      {formatDate(tx.created_at)}
                    </Td>
                    <Td>
                      <Badge colorScheme={ACTION_COLORS[tx.action] || 'gray'}>
                        {ACTION_NAMES[tx.action] || tx.action}
                      </Badge>
                    </Td>
                    <Td isNumeric fontWeight="bold" color={tx.credits_consumed ? 'red.500' : 'green.500'}>
                      {tx.credits_consumed ? `-${tx.credits_consumed}` : `+${tx.credits_added || 0}`}
                    </Td>
                    <Td isNumeric color={textColor}>
                      {tx.balance_after?.toLocaleString()}
                    </Td>
                  </Tr>
                ))}
                
                {transactions.length === 0 && (
                  <Tr>
                    <Td colSpan={4} textAlign="center" color={textColorSecondary} py={8}>
                      No transactions yet
                    </Td>
                  </Tr>
                )}
              </Tbody>
            </Table>
          </Box>
        </CardBody>
      </Card>
    </Box>
  );
}
