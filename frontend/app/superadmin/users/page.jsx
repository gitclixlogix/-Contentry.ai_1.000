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
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Button,
  IconButton,
  Spinner,
  Center,
  useColorModeValue,
  Flex,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FaSearch,
  FaBuilding,
  FaUsers,
  FaChevronLeft,
  FaChevronRight,
  FaSort,
  FaSortUp,
  FaSortDown,
  FaEllipsisV,
  FaEye,
  FaEnvelope,
  FaDollarSign,
  FaUserCheck,
  FaUserTimes,
} from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { getApiUrl } from '@/lib/api';

export default function UsersAndCustomersPage() {
  const router = useRouter();
  const toast = useToast();
  
  // State for customers tab
  const [customers, setCustomers] = useState([]);
  const [customersLoading, setCustomersLoading] = useState(true);
  const [customerSearch, setCustomerSearch] = useState('');
  const [customerSort, setCustomerSort] = useState({ field: 'created_at', direction: 'desc' });
  const [customerPage, setCustomerPage] = useState(1);
  const [customerTotalPages, setCustomerTotalPages] = useState(1);
  const [customerStats, setCustomerStats] = useState({ total: 0, active: 0, mrr: 0 });
  
  // State for users tab
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [userSearch, setUserSearch] = useState('');
  const [userSort, setUserSort] = useState({ field: 'created_at', direction: 'desc' });
  const [userPage, setUserPage] = useState(1);
  const [userTotalPages, setUserTotalPages] = useState(1);
  const [userStats, setUserStats] = useState({ total: 0, active: 0, invited: 0 });
  
  const [activeTab, setActiveTab] = useState(0);
  
  // Colors
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  
  const pageSize = 10;
  
  // Fetch customers
  const fetchCustomers = useCallback(async () => {
    setCustomersLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      
      const params = new URLSearchParams({
        page: customerPage.toString(),
        limit: pageSize.toString(),
        search: customerSearch,
        sort_by: customerSort.field,
        sort_dir: customerSort.direction,
      });
      
      const response = await fetch(`${getApiUrl()}/superadmin/customers?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-user-id': userId,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
        setCustomerTotalPages(data.total_pages || 1);
        setCustomerStats({
          total: data.total || 0,
          active: data.active_count || 0,
          mrr: data.total_mrr || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching customers:', error);
      toast({ title: 'Error loading customers', status: 'error', duration: 3000 });
    } finally {
      setCustomersLoading(false);
    }
  }, [customerPage, customerSearch, customerSort, toast]);
  
  // Fetch users
  const fetchUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      
      const params = new URLSearchParams({
        page: userPage.toString(),
        limit: pageSize.toString(),
        search: userSearch,
        sort_by: userSort.field,
        sort_dir: userSort.direction,
      });
      
      const response = await fetch(`${getApiUrl()}/superadmin/users?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-user-id': userId,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setUserTotalPages(data.total_pages || 1);
        setUserStats({
          total: data.total || 0,
          active: data.active_count || 0,
          invited: data.invited_count || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      toast({ title: 'Error loading users', status: 'error', duration: 3000 });
    } finally {
      setUsersLoading(false);
    }
  }, [userPage, userSearch, userSort, toast]);
  
  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);
  
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);
  
  // Sort handler
  const handleSort = (field, isCustomer) => {
    if (isCustomer) {
      setCustomerSort(prev => ({
        field,
        direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
      }));
      setCustomerPage(1);
    } else {
      setUserSort(prev => ({
        field,
        direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
      }));
      setUserPage(1);
    }
  };
  
  // Get sort icon
  const getSortIcon = (field, sortState) => {
    if (sortState.field !== field) return FaSort;
    return sortState.direction === 'asc' ? FaSortUp : FaSortDown;
  };
  
  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };
  
  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };
  
  // Get status badge
  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { color: 'green', label: 'Active' },
      inactive: { color: 'gray', label: 'Inactive' },
      invited: { color: 'blue', label: 'Invited' },
      deactivated: { color: 'red', label: 'Deactivated' },
      trial: { color: 'orange', label: 'Trial' },
    };
    const config = statusConfig[status?.toLowerCase()] || statusConfig.inactive;
    return <Badge colorScheme={config.color}>{config.label}</Badge>;
  };
  
  // Get plan badge
  const getPlanBadge = (plan) => {
    const planConfig = {
      enterprise: { color: 'purple', label: 'Enterprise' },
      pro: { color: 'blue', label: 'Pro' },
      starter: { color: 'green', label: 'Starter' },
      free: { color: 'gray', label: 'Free' },
      trial: { color: 'orange', label: 'Trial' },
    };
    const config = planConfig[plan?.toLowerCase()] || planConfig.free;
    return <Badge colorScheme={config.color}>{config.label}</Badge>;
  };
  
  return (
    <Box>
      {/* Page Header */}
      <VStack align="stretch" spacing={1} mb={6}>
        <HStack>
          <Box as={FaUsers} boxSize={6} color="red.500" />
          <Heading size="lg" color={textColor}>Users & Customers</Heading>
        </HStack>
        <Text color={mutedColor}>Manage customer organizations and individual user accounts</Text>
      </VStack>
      
      {/* Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab} colorScheme="red" variant="enclosed">
        <TabList>
          <Tab>
            <HStack spacing={2}>
              <FaBuilding />
              <Text>Customer Organizations</Text>
              <Badge colorScheme="red" borderRadius="full">{customerStats.total}</Badge>
            </HStack>
          </Tab>
          <Tab>
            <HStack spacing={2}>
              <FaUsers />
              <Text>Individual Users</Text>
              <Badge colorScheme="red" borderRadius="full">{userStats.total}</Badge>
            </HStack>
          </Tab>
        </TabList>
        
        <TabPanels>
          {/* Customers Tab */}
          <TabPanel px={0} pt={6}>
            {/* Customer Stats */}
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Total Organizations</StatLabel>
                    <StatNumber color={textColor}>{customerStats.total}</StatNumber>
                    <StatHelpText>Registered companies</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Active Customers</StatLabel>
                    <StatNumber color="green.500">{customerStats.active}</StatNumber>
                    <StatHelpText>Paying organizations</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Total MRR</StatLabel>
                    <StatNumber color="blue.500">{formatCurrency(customerStats.mrr)}</StatNumber>
                    <StatHelpText>Monthly recurring revenue</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            {/* Search and Filters */}
            <Card bg={cardBg} mb={4}>
              <CardBody>
                <HStack spacing={4}>
                  <InputGroup maxW="400px">
                    <InputLeftElement pointerEvents="none">
                      <FaSearch color="gray.400" />
                    </InputLeftElement>
                    <Input
                      placeholder="Search by company name..."
                      value={customerSearch}
                      onChange={(e) => { setCustomerSearch(e.target.value); setCustomerPage(1); }}
                    />
                  </InputGroup>
                  <Select maxW="200px" defaultValue="all">
                    <option value="all">All Plans</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="pro">Pro</option>
                    <option value="starter">Starter</option>
                    <option value="free">Free</option>
                  </Select>
                </HStack>
              </CardBody>
            </Card>
            
            {/* Customers Table */}
            <Card bg={cardBg}>
              <CardBody p={0}>
                {customersLoading ? (
                  <Center py={10}>
                    <Spinner size="lg" color="red.500" />
                  </Center>
                ) : customers.length === 0 ? (
                  <Center py={10}>
                    <VStack>
                      <FaBuilding size={40} color="gray" />
                      <Text color={mutedColor}>No customers found</Text>
                    </VStack>
                  </Center>
                ) : (
                  <Box overflowX="auto">
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th cursor="pointer" onClick={() => handleSort('name', true)}>
                            <HStack>
                              <Text>Company Name</Text>
                              <Box as={getSortIcon('name', customerSort)} />
                            </HStack>
                          </Th>
                          <Th cursor="pointer" onClick={() => handleSort('subscription_plan', true)}>
                            <HStack>
                              <Text>Plan</Text>
                              <Box as={getSortIcon('subscription_plan', customerSort)} />
                            </HStack>
                          </Th>
                          <Th cursor="pointer" onClick={() => handleSort('mrr', true)} isNumeric>
                            <HStack justify="flex-end">
                              <Text>MRR</Text>
                              <Box as={getSortIcon('mrr', customerSort)} />
                            </HStack>
                          </Th>
                          <Th cursor="pointer" onClick={() => handleSort('user_count', true)} isNumeric>
                            <HStack justify="flex-end">
                              <Text>Users</Text>
                              <Box as={getSortIcon('user_count', customerSort)} />
                            </HStack>
                          </Th>
                          <Th cursor="pointer" onClick={() => handleSort('created_at', true)}>
                            <HStack>
                              <Text>Sign-up Date</Text>
                              <Box as={getSortIcon('created_at', customerSort)} />
                            </HStack>
                          </Th>
                          <Th>Status</Th>
                          <Th></Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {customers.map((customer) => (
                          <Tr 
                            key={customer.id} 
                            _hover={{ bg: hoverBg }}
                            cursor="pointer"
                            onClick={() => router.push(`/superadmin/users/${customer.id}`)}
                          >
                            <Td>
                              <HStack>
                                <Avatar size="sm" name={customer.name} bg="red.500" />
                                <VStack align="start" spacing={0}>
                                  <Text fontWeight="600" color={textColor}>{customer.name}</Text>
                                  <Text fontSize="xs" color={mutedColor}>{customer.domain || 'No domain'}</Text>
                                </VStack>
                              </HStack>
                            </Td>
                            <Td>{getPlanBadge(customer.subscription_plan)}</Td>
                            <Td isNumeric fontWeight="600">{formatCurrency(customer.mrr)}</Td>
                            <Td isNumeric>{customer.user_count || 0}</Td>
                            <Td>{formatDate(customer.created_at)}</Td>
                            <Td>{getStatusBadge(customer.status)}</Td>
                            <Td>
                              <Menu>
                                <MenuButton
                                  as={IconButton}
                                  icon={<FaEllipsisV />}
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => e.stopPropagation()}
                                />
                                <MenuList>
                                  <MenuItem icon={<FaEye />} onClick={(e) => { e.stopPropagation(); router.push(`/superadmin/users/${customer.id}`); }}>
                                    View Details
                                  </MenuItem>
                                  <MenuItem icon={<FaEnvelope />} onClick={(e) => e.stopPropagation()}>
                                    Contact Admin
                                  </MenuItem>
                                </MenuList>
                              </Menu>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
                
                {/* Pagination */}
                {customers.length > 0 && (
                  <Flex justify="space-between" align="center" p={4} borderTop="1px" borderColor={borderColor}>
                    <Text fontSize="sm" color={mutedColor}>
                      Page {customerPage} of {customerTotalPages}
                    </Text>
                    <HStack>
                      <IconButton
                        icon={<FaChevronLeft />}
                        size="sm"
                        onClick={() => setCustomerPage(p => Math.max(1, p - 1))}
                        isDisabled={customerPage === 1}
                      />
                      <IconButton
                        icon={<FaChevronRight />}
                        size="sm"
                        onClick={() => setCustomerPage(p => Math.min(customerTotalPages, p + 1))}
                        isDisabled={customerPage === customerTotalPages}
                      />
                    </HStack>
                  </Flex>
                )}
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Users Tab */}
          <TabPanel px={0} pt={6}>
            {/* User Stats */}
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4} mb={6}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Total Users</StatLabel>
                    <StatNumber color={textColor}>{userStats.total}</StatNumber>
                    <StatHelpText>All registered users</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Active Users</StatLabel>
                    <StatNumber color="green.500">{userStats.active}</StatNumber>
                    <StatHelpText>Logged in recently</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel color={mutedColor}>Pending Invites</StatLabel>
                    <StatNumber color="blue.500">{userStats.invited}</StatNumber>
                    <StatHelpText>Awaiting activation</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            {/* Search and Filters */}
            <Card bg={cardBg} mb={4}>
              <CardBody>
                <HStack spacing={4}>
                  <InputGroup maxW="400px">
                    <InputLeftElement pointerEvents="none">
                      <FaSearch color="gray.400" />
                    </InputLeftElement>
                    <Input
                      placeholder="Search by name or email..."
                      value={userSearch}
                      onChange={(e) => { setUserSearch(e.target.value); setUserPage(1); }}
                    />
                  </InputGroup>
                  <Select maxW="200px" defaultValue="all">
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="invited">Invited</option>
                    <option value="deactivated">Deactivated</option>
                  </Select>
                </HStack>
              </CardBody>
            </Card>
            
            {/* Users Table */}
            <Card bg={cardBg}>
              <CardBody p={0}>
                {usersLoading ? (
                  <Center py={10}>
                    <Spinner size="lg" color="red.500" />
                  </Center>
                ) : users.length === 0 ? (
                  <Center py={10}>
                    <VStack>
                      <FaUsers size={40} color="gray" />
                      <Text color={mutedColor}>No users found</Text>
                    </VStack>
                  </Center>
                ) : (
                  <Box overflowX="auto">
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th cursor="pointer" onClick={() => handleSort('full_name', false)}>
                            <HStack>
                              <Text>User</Text>
                              <Box as={getSortIcon('full_name', userSort)} />
                            </HStack>
                          </Th>
                          <Th cursor="pointer" onClick={() => handleSort('email', false)}>
                            <HStack>
                              <Text>Email</Text>
                              <Box as={getSortIcon('email', userSort)} />
                            </HStack>
                          </Th>
                          <Th>Company</Th>
                          <Th cursor="pointer" onClick={() => handleSort('last_login', false)}>
                            <HStack>
                              <Text>Last Login</Text>
                              <Box as={getSortIcon('last_login', userSort)} />
                            </HStack>
                          </Th>
                          <Th>Role</Th>
                          <Th>Status</Th>
                          <Th></Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {users.map((user) => (
                          <Tr key={user.id} _hover={{ bg: hoverBg }}>
                            <Td>
                              <HStack>
                                <Avatar size="sm" name={user.full_name} src={user.profile_picture} />
                                <Text fontWeight="500" color={textColor}>{user.full_name || 'Unknown'}</Text>
                              </HStack>
                            </Td>
                            <Td>
                              <Text color={mutedColor}>{user.email}</Text>
                            </Td>
                            <Td>
                              <Text color={mutedColor}>{user.company_name || user.enterprise_name || '-'}</Text>
                            </Td>
                            <Td>{formatDate(user.last_login)}</Td>
                            <Td>
                              <Badge colorScheme={user.role === 'admin' ? 'purple' : user.role === 'super_admin' ? 'red' : 'gray'}>
                                {user.role || 'user'}
                              </Badge>
                            </Td>
                            <Td>{getStatusBadge(user.status || (user.email_verified ? 'active' : 'invited'))}</Td>
                            <Td>
                              <Menu>
                                <MenuButton
                                  as={IconButton}
                                  icon={<FaEllipsisV />}
                                  variant="ghost"
                                  size="sm"
                                />
                                <MenuList>
                                  <MenuItem icon={<FaEye />}>View Profile</MenuItem>
                                  <MenuItem icon={<FaEnvelope />}>Send Email</MenuItem>
                                  <MenuItem icon={<FaUserTimes />} color="red.500">Deactivate</MenuItem>
                                </MenuList>
                              </Menu>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
                
                {/* Pagination */}
                {users.length > 0 && (
                  <Flex justify="space-between" align="center" p={4} borderTop="1px" borderColor={borderColor}>
                    <Text fontSize="sm" color={mutedColor}>
                      Page {userPage} of {userTotalPages}
                    </Text>
                    <HStack>
                      <IconButton
                        icon={<FaChevronLeft />}
                        size="sm"
                        onClick={() => setUserPage(p => Math.max(1, p - 1))}
                        isDisabled={userPage === 1}
                      />
                      <IconButton
                        icon={<FaChevronRight />}
                        size="sm"
                        onClick={() => setUserPage(p => Math.min(userTotalPages, p + 1))}
                        isDisabled={userPage === userTotalPages}
                      />
                    </HStack>
                  </Flex>
                )}
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
}
