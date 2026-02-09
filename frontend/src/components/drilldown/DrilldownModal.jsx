'use client';

import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  VStack,
  HStack,
  Text,
  Badge,
  Avatar,
  Progress,
  Spinner,
  Center,
  Icon,
  useColorModeValue,
  Box,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { FaSearch, FaUsers, FaFileAlt, FaDollarSign, FaExclamationTriangle, FaCheckCircle, FaEnvelope, FaBriefcase, FaCalendar } from 'react-icons/fa';
import api from '@/lib/api';

const metricConfigs = {
  // Admin Dashboard Metrics
  total_users: {
    title: 'Total Users',
    description: 'All registered users on the platform',
    icon: FaUsers,
    color: 'blue.500',
    columns: ['user', 'email', 'role', 'status', 'joined'],
  },
  total_posts: {
    title: 'Total Posts',
    description: 'All content created on the platform',
    icon: FaFileAlt,
    color: 'blue.600',
    columns: ['user', 'posts', 'approved', 'flagged', 'avg_score'],
  },
  total_revenue: {
    title: 'Total Revenue',
    description: 'Revenue breakdown by user',
    icon: FaDollarSign,
    color: 'green.500',
    columns: ['user', 'plan', 'amount', 'transactions', 'last_payment'],
  },
  flagged_content: {
    title: 'Flagged Content',
    description: 'Content flagged for policy violations',
    icon: FaExclamationTriangle,
    color: 'red.500',
    columns: ['user', 'content_preview', 'flag_reason', 'flagged_at', 'status'],
  },
  approved_content: {
    title: 'Approved Content',
    description: 'Content that passed moderation',
    icon: FaCheckCircle,
    color: 'green.500',
    columns: ['user', 'posts', 'approval_rate', 'avg_score'],
  },
  active_subscriptions: {
    title: 'Active Subscriptions',
    description: 'Users with active subscription plans',
    icon: FaDollarSign,
    color: 'teal.500',
    columns: ['user', 'plan', 'started', 'expires', 'amount'],
  },
  // Enterprise Dashboard Metrics (already implemented)
  enterprise_users: {
    title: 'Enterprise Users',
    description: 'Users in this enterprise',
    icon: FaUsers,
    color: 'blue.600',
    columns: ['user', 'role', 'posts', 'score'],
  },
  // Financial Dashboard Metrics
  transactions: {
    title: 'Transactions',
    description: 'Payment transaction details',
    icon: FaDollarSign,
    color: 'green.500',
    columns: ['user', 'amount', 'type', 'status', 'date'],
  },
  revenue_by_plan: {
    title: 'Revenue by Plan',
    description: 'Revenue breakdown by subscription plan',
    icon: FaDollarSign,
    color: 'blue.500',
    columns: ['plan', 'users', 'revenue', 'percentage'],
  },
  // Analytics Dashboard Metrics
  content_by_platform: {
    title: 'Content by Platform',
    description: 'Content distribution across platforms',
    icon: FaFileAlt,
    color: 'blue.500',
    columns: ['user', 'platform', 'posts', 'engagement'],
  },
  users_by_country: {
    title: 'Users by Country',
    description: 'User distribution by country',
    icon: FaUsers,
    color: 'teal.500',
    columns: ['country', 'users', 'posts', 'revenue'],
  },
};

export default function DrilldownModal({ 
  isOpen, 
  onClose, 
  metricType, 
  dashboardType = 'admin',
  enterpriseId = null,
  userId = null 
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('');
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  
  const config = metricConfigs[metricType] || {
    title: 'Details',
    description: 'Metric details',
    icon: FaFileAlt,
    color: 'blue.500',
    columns: [],
  };
  
  useEffect(() => {
    if (isOpen && metricType) {
      fetchDrilldownData();
    }
  }, [isOpen, metricType]);
  
  const fetchDrilldownData = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      
      // Determine endpoint based on dashboard type
      switch (dashboardType) {
        case 'admin':
          endpoint = `/admin/drilldown/${metricType}`;
          break;
        case 'enterprise':
          endpoint = `/enterprises/${enterpriseId}/analytics/drilldown/${metricType}`;
          break;
        case 'financial':
          endpoint = `/admin/financial/drilldown/${metricType}`;
          break;
        case 'analytics':
          endpoint = `/admin/analytics/drilldown/${metricType}`;
          break;
        default:
          endpoint = `/admin/drilldown/${metricType}`;
      }
      
      const response = await api.get(endpoint);
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch drilldown data:', error);
      setData({ items: [], error: error.message });
    } finally {
      setLoading(false);
    }
  };
  
  const filteredData = data?.items?.filter(item => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      item.name?.toLowerCase().includes(searchLower) ||
      item.email?.toLowerCase().includes(searchLower) ||
      item.plan?.toLowerCase().includes(searchLower) ||
      item.country?.toLowerCase().includes(searchLower)
    );
  }) || [];
  
  const renderTableContent = () => {
    if (!data?.items || data.items.length === 0) {
      return (
        <Center py={12}>
          <VStack spacing={4}>
            <Icon as={config.icon} boxSize={12} color={textColorSecondary} />
            <Text color={textColorSecondary}>No data available</Text>
          </VStack>
        </Center>
      );
    }
    
    // Render based on metric type
    switch (metricType) {
      case 'total_users':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>User</Th>
                <Th>Role</Th>
                <Th>Status</Th>
                <Th>Joined</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={item.name} src={item.avatar} />
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="600" fontSize="sm">{item.name}</Text>
                        <Text fontSize="xs" color={textColorSecondary}>{item.email}</Text>
                      </VStack>
                    </HStack>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.role === 'admin' ? 'blue' : 'gray'}>
                      {item.role}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.status === 'active' ? 'green' : 'red'}>
                      {item.status}
                    </Badge>
                  </Td>
                  <Td fontSize="sm">{item.joined_at}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      case 'total_posts':
      case 'approved_content':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>User</Th>
                <Th isNumeric>Posts</Th>
                <Th isNumeric>Approved</Th>
                <Th isNumeric>Flagged</Th>
                <Th>Avg Score</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={item.name} />
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="600" fontSize="sm">{item.name}</Text>
                        <Text fontSize="xs" color={textColorSecondary}>{item.email}</Text>
                      </VStack>
                    </HStack>
                  </Td>
                  <Td isNumeric>
                    <Badge colorScheme="blue">{item.post_count}</Badge>
                  </Td>
                  <Td isNumeric>
                    <Badge colorScheme="green">{item.approved_count}</Badge>
                  </Td>
                  <Td isNumeric>
                    <Badge colorScheme="red">{item.flagged_count}</Badge>
                  </Td>
                  <Td>
                    <HStack spacing={2}>
                      <Progress
                        value={item.avg_score}
                        size="sm"
                        w="60px"
                        colorScheme={item.avg_score >= 80 ? 'green' : item.avg_score >= 60 ? 'yellow' : 'red'}
                        borderRadius="full"
                      />
                      <Text fontSize="sm" fontWeight="600">{item.avg_score}</Text>
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      case 'total_revenue':
      case 'active_subscriptions':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>User</Th>
                <Th>Plan</Th>
                <Th isNumeric>Amount</Th>
                <Th isNumeric>Transactions</Th>
                <Th>Last Payment</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={item.name} />
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="600" fontSize="sm">{item.name}</Text>
                        <Text fontSize="xs" color={textColorSecondary}>{item.email}</Text>
                      </VStack>
                    </HStack>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.plan === 'enterprise' ? 'blue' : item.plan === 'professional' ? 'blue' : 'gray'}>
                      {item.plan}
                    </Badge>
                  </Td>
                  <Td isNumeric fontWeight="600" color="green.500">
                    ${item.total_amount?.toLocaleString()}
                  </Td>
                  <Td isNumeric>{item.transaction_count}</Td>
                  <Td fontSize="sm">{item.last_payment}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      case 'flagged_content':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>User</Th>
                <Th>Content Preview</Th>
                <Th>Flag Reason</Th>
                <Th>Status</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={item.user_name} />
                      <Text fontWeight="600" fontSize="sm">{item.user_name}</Text>
                    </HStack>
                  </Td>
                  <Td>
                    <Text fontSize="sm" noOfLines={2} maxW="300px">
                      {item.content_preview}
                    </Text>
                  </Td>
                  <Td>
                    <Badge colorScheme="red">{item.flag_reason}</Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.status === 'resolved' ? 'green' : 'orange'}>
                      {item.status}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      case 'transactions':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>User</Th>
                <Th isNumeric>Amount</Th>
                <Th>Type</Th>
                <Th>Status</Th>
                <Th>Date</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={item.user_name} />
                      <Text fontWeight="600" fontSize="sm">{item.user_name}</Text>
                    </HStack>
                  </Td>
                  <Td isNumeric fontWeight="600" color="green.500">
                    ${item.amount?.toFixed(2)}
                  </Td>
                  <Td>
                    <Badge colorScheme="blue">{item.type}</Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.status === 'completed' ? 'green' : 'yellow'}>
                      {item.status}
                    </Badge>
                  </Td>
                  <Td fontSize="sm">{item.date}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      case 'users_by_country':
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>Country</Th>
                <Th isNumeric>Users</Th>
                <Th isNumeric>Posts</Th>
                <Th isNumeric>Revenue</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <HStack spacing={2}>
                      <Text fontSize="lg">{item.flag}</Text>
                      <Text fontWeight="600">{item.country}</Text>
                    </HStack>
                  </Td>
                  <Td isNumeric>
                    <Badge colorScheme="blue">{item.user_count}</Badge>
                  </Td>
                  <Td isNumeric>{item.post_count}</Td>
                  <Td isNumeric fontWeight="600" color="green.500">
                    ${item.revenue?.toLocaleString()}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
        
      default:
        // Generic table for unknown metric types
        return (
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>Item</Th>
                <Th>Details</Th>
                <Th isNumeric>Value</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredData.map((item, idx) => (
                <Tr key={idx} _hover={{ bg: hoverBg }}>
                  <Td>
                    <Text fontWeight="600" fontSize="sm">
                      {item.name || item.label || `Item ${idx + 1}`}
                    </Text>
                  </Td>
                  <Td>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {item.description || item.details || '-'}
                    </Text>
                  </Td>
                  <Td isNumeric fontWeight="600">
                    {item.value || item.count || 0}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        );
    }
  };
  
  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      size="5xl" 
      scrollBehavior="inside"
      closeOnOverlayClick={true}
      closeOnEsc={true}
      isCentered
      blockScrollOnMount={false}
    >
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
      <ModalContent bg={cardBg} maxH="85vh">
        <ModalHeader borderBottomWidth="1px" borderColor={borderColor}>
          <VStack align="start" spacing={1}>
            <Flex align="center" gap={2}>
              <Icon as={config.icon} color={config.color} boxSize={5} />
              <Text fontSize="xl" fontWeight="bold">{data?.title || config.title}</Text>
            </Flex>
            <Text fontSize="sm" fontWeight="normal" color={textColorSecondary}>
              {data?.description || config.description}
            </Text>
          </VStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody py={4}>
          {/* Search and Sort */}
          <Flex mb={4} gap={4} flexWrap="wrap">
            <InputGroup maxW="300px">
              <InputLeftElement>
                <Icon as={FaSearch} color={textColorSecondary} />
              </InputLeftElement>
              <Input
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            
            {data?.total && (
              <Badge colorScheme="blue" fontSize="md" px={3} py={1} alignSelf="center">
                {filteredData.length} of {data.total} items
              </Badge>
            )}
          </Flex>
          
          {loading ? (
            <Center py={12}>
              <VStack spacing={4}>
                <Spinner size="xl" color={config.color} />
                <Text color={textColorSecondary}>Loading details...</Text>
              </VStack>
            </Center>
          ) : (
            <Box overflowX="auto">
              {renderTableContent()}
            </Box>
          )}
          
          {data?.is_demo_data && (
            <Badge colorScheme="orange" mt={4}>Demo Data</Badge>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
