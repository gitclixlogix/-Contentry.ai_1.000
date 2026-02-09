'use client';
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
import {
  Box,
  SimpleGrid,
  Text,
  useColorModeValue,
  Flex,
  Badge,
  Spinner,
  VStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Progress,
  HStack,
  Heading,
  useDisclosure,
} from '@chakra-ui/react';
import Card from '@/components/card/Card';
import MiniStatistics from '@/components/card/MiniStatistics';
import IconBox from '@/components/icons/IconBox';
import { FaDollarSign, FaCreditCard, FaReceipt, FaChartBar } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import DrilldownModal from '@/components/drilldown/DrilldownModal';

export default function FinancialAnalytics() {
  const [cardAnalytics, setCardAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Drilldown modal state
  const [drilldownMetric, setDrilldownMetric] = useState(null);
  const { isOpen: isDrilldownOpen, onOpen: onDrilldownOpen, onClose: onDrilldownClose } = useDisclosure();

  const textColor = useColorModeValue('secondaryGray.900', 'white');
  const textColorSecondary = useColorModeValue('secondaryGray.600', 'white');
  const brandColor = useColorModeValue('brand.500', 'white');
  const boxBg = useColorModeValue('secondaryGray.300', 'whiteAlpha.100');
  const cardBorderColor = useColorModeValue('gray.200', 'whiteAlpha.200');

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

  useEffect(() => {
    loadCardAnalytics();
  }, []);

  const loadCardAnalytics = async () => {
    try {
      setLoading(true);
      const API = getApiUrl();
      const response = await axios.get(`${API}/admin/analytics/card-distribution`);
      setCardAnalytics(response.data);
    } catch (error) {
      console.error('Failed to load card analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
        <Flex justify="center" align="center" h="400px">
          <Spinner size="xl" color={brandColor} />
        </Flex>
      </Box>
    );
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Flex mb="20px" justify="space-between" align="center">
        <Box>
          <Heading size="lg" color={textColor} mb="4px">
            Financial Analytics
          </Heading>
          <Text color={textColorSecondary} fontSize="md">
            Credit card transaction analytics and revenue breakdown
          </Text>
        </Box>
      </Flex>

      {cardAnalytics && (
        <VStack spacing="20px" align="stretch">
          {/* Summary Cards */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap="20px">
            <MiniStatistics
              startContent={
                <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #1e40af 0%, #60a5fa 100%)" icon={<FaReceipt color="white" size="24px" />} />
              }
              name="Total Transactions"
              value={cardAnalytics.total_transactions}
              isClickable={true}
              onClick={() => handleDrilldown('total_transactions')}
            />
            <MiniStatistics
              startContent={
                <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #05CD99 0%, #00B574 100%)" icon={<FaDollarSign color="white" size="24px" />} />
              }
              name="Total Revenue"
              value={`$${cardAnalytics.total_revenue.toLocaleString()}`}
              isClickable={true}
              onClick={() => handleDrilldown('total_revenue')}
            />
            <MiniStatistics
              startContent={
                <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #39B8FF 0%, #4481EB 100%)" icon={<FaCreditCard color="white" size="24px" />} />
              }
              name="Top Card Type"
              value={cardAnalytics.top_card ? cardAnalytics.top_card.charAt(0).toUpperCase() + cardAnalytics.top_card.slice(1) : 'N/A'}
              isClickable={true}
              onClick={() => handleDrilldown('card_distribution')}
            />
            <MiniStatistics
              startContent={
                <IconBox w="56px" h="56px" bg="linear-gradient(90deg, #FFB547 0%, #FF6B00 100%)" icon={<FaChartBar color="white" size="24px" />} />
              }
              name="Avg Transaction"
              value={`$${(Object.values(cardAnalytics.avg_transaction_value).reduce((a, b) => a + b, 0) / Object.keys(cardAnalytics.avg_transaction_value).length).toFixed(2)}`}
              isClickable={true}
              onClick={() => handleDrilldown('transactions')}
            />
          </SimpleGrid>

          {/* Card Type Distribution */}
          <Card p="20px">
            <Text fontSize="xl" fontWeight="700" mb="20px">
              Credit Card Type Distribution
            </Text>
            {cardAnalytics.is_mock_data && (
              <Badge colorScheme="orange" mb="4">Mock Data</Badge>
            )}
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Card Type</Th>
                  <Th isNumeric>Transactions</Th>
                  <Th isNumeric>Revenue</Th>
                  <Th isNumeric>Percentage</Th>
                  <Th isNumeric>Avg Value</Th>
                  <Th>Distribution</Th>
                </Tr>
              </Thead>
              <Tbody>
                {Object.entries(cardAnalytics.card_types).map(([cardType, data]) => (
                  <Tr key={cardType}>
                    <Td>
                      <HStack>
                        <Badge 
                          colorScheme={
                            cardType === 'visa' ? 'blue' :
                            cardType === 'mastercard' ? 'orange' :
                            cardType === 'amex' ? 'green' :
                            cardType === 'discover' ? 'blue' : 'gray'
                          }
                          fontSize="sm"
                          px={3}
                          py={1}
                          textTransform="capitalize"
                        >
                          {cardType}
                        </Badge>
                      </HStack>
                    </Td>
                    <Td isNumeric fontWeight="600">{data.count}</Td>
                    <Td isNumeric fontWeight="600">${data.revenue.toLocaleString()}</Td>
                    <Td isNumeric>{data.percentage}%</Td>
                    <Td isNumeric>${cardAnalytics.avg_transaction_value[cardType].toFixed(2)}</Td>
                    <Td>
                      <Progress 
                        value={data.percentage} 
                        size="sm" 
                        colorScheme={
                          cardType === 'visa' ? 'blue' :
                          cardType === 'mastercard' ? 'orange' :
                          cardType === 'amex' ? 'green' :
                          cardType === 'discover' ? 'blue' : 'gray'
                        }
                        borderRadius="full"
                      />
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Card>

          {/* Revenue by Card Type */}
          <Card p="20px">
            <Text fontSize="xl" fontWeight="700" mb="20px">
              Revenue Breakdown by Card Type
            </Text>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap="20px">
              {Object.entries(cardAnalytics.card_types).map(([cardType, data]) => (
                <Box 
                  key={cardType}
                  p="20px" 
                  bg={boxBg} 
                  borderRadius="md"
                  borderWidth="1px"
                  borderColor={cardBorderColor}
                >
                  <HStack justify="space-between" mb="10px">
                    <Text fontSize="md" fontWeight="600" textTransform="capitalize">
                      {cardType}
                    </Text>
                    <Badge 
                      colorScheme={
                        cardType === 'visa' ? 'blue' :
                        cardType === 'mastercard' ? 'orange' :
                        cardType === 'amex' ? 'green' :
                        cardType === 'discover' ? 'blue' : 'gray'
                      }
                    >
                      {data.percentage}%
                    </Badge>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="700" mb="8px">
                    ${data.revenue.toLocaleString()}
                  </Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    {data.count} transactions • ${cardAnalytics.avg_transaction_value[cardType].toFixed(2)} avg
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </Card>
        </VStack>
      )}

      {/* Drilldown Modal */}
      <DrilldownModal
        isOpen={isDrilldownOpen}
        onClose={handleDrilldownClose}
        metricType={drilldownMetric}
        dashboardType="financial"
      />
    </Box>
  );
}
