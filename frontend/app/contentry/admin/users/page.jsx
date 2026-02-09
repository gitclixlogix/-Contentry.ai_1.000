'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Input,
  Select,
  HStack,
  VStack,
  IconButton,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Avatar,
  Spinner,
} from '@chakra-ui/react';
import { FaSearch, FaUserCircle, FaBan, FaCheckCircle, FaEye, FaTrash, FaUserMinus, FaExclamationTriangle } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import Card from '@/components/card/Card';
// Import shared reusable components
import { UserInfoCell, DeleteConfirmationModal, InfoRow } from '@/components/shared';

export default function AdminUsersPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [filterSubscription, setFilterSubscription] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [deletingUser, setDeletingUser] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [stats, setStats] = useState({
    total: 0,
    active_subscriptions: 0,
    free_users: 0,
    revenue: 0
  });

  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isCancelSubOpen, onOpen: onCancelSubOpen, onClose: onCancelSubClose } = useDisclosure();
  const [cancellingSubscription, setCancellingSubscription] = useState(false);

  const textColor = useColorModeValue('navy.700', 'white');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.100');
  const cardBg = useColorModeValue('white', 'navy.800');

  useEffect(() => {
    const user = localStorage.getItem('contentry_user');
    if (!user) {
      router.push('/contentry/auth/login');
      return;
    }

    const userData = JSON.parse(user);
    if (userData.role !== 'admin') {
      router.push('/contentry/dashboard');
      return;
    }

    loadUsers();
  }, [router]);

  useEffect(() => {
    filterUsers();
  }, [searchQuery, filterRole, filterSubscription, users]);

  const loadUsers = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/admin/analytics/user-table`, {
        params: { limit: 1000 }
      });

      const usersData = response.data.users || [];
      setUsers(usersData);

      // Calculate stats
      const activeSubscriptions = usersData.filter(
        u => u.subscription?.status === 'active' || u.subscription?.status === 'trialing'
      ).length;
      const freeUsers = usersData.filter(
        u => u.subscription?.plan === 'free' || !u.subscription?.plan
      ).length;

      setStats({
        total: usersData.length,
        active_subscriptions: activeSubscriptions,
        free_users: freeUsers,
        revenue: activeSubscriptions * 29.99 // Rough estimate
      });
    } catch (error) {
      console.error('Failed to load users:', error);
      toast({
        title: t('documentation.adminUsersPage.toasts.loadFailed'),
        description: error.response?.data?.detail || t('common.pleaseTryAgain'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const filterUsers = () => {
    let filtered = [...users];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(user =>
        user.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Role filter
    if (filterRole !== 'all') {
      filtered = filtered.filter(user => user.role === filterRole);
    }

    // Subscription filter
    if (filterSubscription !== 'all') {
      filtered = filtered.filter(user => {
        if (filterSubscription === 'active') {
          return user.subscription?.status === 'active' || user.subscription?.status === 'trialing';
        } else if (filterSubscription === 'inactive') {
          return !user.subscription?.status || user.subscription?.status === 'inactive' || user.subscription?.status === 'cancelled';
        } else if (filterSubscription === 'free') {
          return user.subscription?.plan === 'free' || !user.subscription?.plan;
        }
        return true;
      });
    }

    setFilteredUsers(filtered);
  };

  const handleViewUser = (user) => {
    setSelectedUser(user);
    onOpen();
  };

  const handleDeleteUser = async (userId, email) => {
    setDeletingUser(true);
    try {
      const API = getApiUrl();
      const response = await axios.delete(`${API}/admin/users/${userId}`);
      
      toast({
        title: t('documentation.adminUsersPage.toasts.deleteSuccess'),
        description: `${email}`,
        status: 'success',
        duration: 3000,
      });

      loadUsers();
      onDeleteClose();
      onClose();
    } catch (error) {
      toast({
        title: t('documentation.adminUsersPage.toasts.deleteFailed'),
        description: error.response?.data?.detail || t('common.pleaseTryAgain'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeletingUser(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedUsers.length === 0) {
      toast({
        title: t('common.noData'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setDeletingUser(true);
    try {
      const API = getApiUrl();
      const response = await axios.delete(`${API}/admin/users/bulk`, {
        data: selectedUsers
      });
      
      toast({
        title: t('documentation.adminUsersPage.toasts.deleteSuccess'),
        description: `${response.data.deleted?.length || 0} users`,
        status: 'success',
        duration: 3000,
      });

      setSelectedUsers([]);
      loadUsers();
    } catch (error) {
      toast({
        title: t('documentation.adminUsersPage.toasts.deleteFailed'),
        description: error.response?.data?.detail || t('common.pleaseTryAgain'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeletingUser(false);
    }
  };

  const toggleUserSelection = (userId) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedUsers.length === filteredUsers.filter(u => u.role !== 'admin').length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(filteredUsers.filter(u => u.role !== 'admin').map(u => u.id));
    }
  };

  const confirmDeleteUser = (user) => {
    setSelectedUser(user);
    onDeleteOpen();
  };

  const openCancelSubscriptionModal = () => {
    onCancelSubOpen();
  };

  const handleCancelSubscription = async () => {
    if (!selectedUser) return;
    
    setCancellingSubscription(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/subscriptions/cancel/${selectedUser.id}`);
      
      toast({
        title: t('admin.users.subscriptionCancelled'),
        status: 'success',
        duration: 3000,
      });

      loadUsers();
      onCancelSubClose();
      onClose();
    } catch (error) {
      toast({
        title: t('admin.users.errorCancellingSubscription'),
        description: error.response?.data?.detail || t('admin.users.pleaseRetryError'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setCancellingSubscription(false);
    }
  };

  const getSubscriptionBadge = (subscription) => {
    if (!subscription || !subscription.status) {
      return <Badge colorScheme="gray">{t('admin.users.noSubscriptionBadge')}</Badge>;
    }

    const status = subscription.status;
    const plan = subscription.plan || 'free';

    if (status === 'active') {
      return <Badge colorScheme="green">{plan.toUpperCase()} - {t('admin.users.active')}</Badge>;
    } else if (status === 'trialing') {
      return <Badge colorScheme="blue">{plan.toUpperCase()} - {t('admin.users.trial')}</Badge>;
    } else if (status === 'cancelled') {
      return <Badge colorScheme="red">{plan.toUpperCase()} - {t('admin.users.cancelled')}</Badge>;
    } else {
      return <Badge colorScheme="gray">{plan.toUpperCase()} - {t('admin.users.inactive')}</Badge>;
    }
  };

  if (loading) {
    return (
      <Flex minH="100vh" align="center" justify="center">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <VStack spacing={6} align="stretch">
        {/* Stats Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="20px" mb="20px">
          <Card>
            <Stat>
              <StatLabel color={textColor}>{t('admin.users.totalUsers')}</StatLabel>
              <StatNumber color={textColor}>{stats.total}</StatNumber>
              <StatHelpText>{t('admin.users.allRegisteredUsers')}</StatHelpText>
            </Stat>
          </Card>
          <Card>
            <Stat>
              <StatLabel color={textColor}>{t('admin.users.activeSubscriptions')}</StatLabel>
              <StatNumber color="green.500">{stats.active_subscriptions}</StatNumber>
              <StatHelpText>{t('admin.users.payingCustomers')}</StatHelpText>
            </Stat>
          </Card>
          <Card>
            <Stat>
              <StatLabel color={textColor}>{t('admin.users.freeUsers')}</StatLabel>
              <StatNumber color="orange.500">{stats.free_users}</StatNumber>
              <StatHelpText>{t('admin.users.noSubscription')}</StatHelpText>
            </Stat>
          </Card>
          <Card>
            <Stat>
              <StatLabel color={textColor}>{t('admin.users.estMonthlyRevenue')}</StatLabel>
              <StatNumber color={textColor}>${stats.revenue.toFixed(2)}</StatNumber>
              <StatHelpText>{t('admin.users.approximateMrr')}</StatHelpText>
            </Stat>
          </Card>
        </SimpleGrid>

        {/* User Management Table */}
        <Card p="20px">
          <VStack spacing={4} align="stretch">
            <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
              <Heading size="md" color={textColor}>
                {t('admin.users.title')}
              </Heading>
            </Flex>

            {/* Filters */}
            <HStack spacing={4} wrap="wrap">
              <Input
                placeholder={t('admin.users.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                maxW="300px"
                leftIcon={<FaSearch />}
              />
              <Select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                maxW="200px"
              >
                <option value="all">{t('admin.users.allRoles')}</option>
                <option value="user">{t('admin.users.user')}</option>
                <option value="admin">{t('enterprise.admin')}</option>
                <option value="enterprise_user">{t('admin.users.enterpriseUser')}</option>
                <option value="enterprise_admin">{t('admin.users.enterpriseAdmin')}</option>
              </Select>
              <Select
                value={filterSubscription}
                onChange={(e) => setFilterSubscription(e.target.value)}
                maxW="200px"
              >
                <option value="all">{t('admin.users.allSubscriptions')}</option>
                <option value="active">{t('admin.users.active')}</option>
                <option value="inactive">{t('admin.users.inactive')}</option>
                <option value="free">{t('admin.users.free')}</option>
              </Select>
              {selectedUsers.length > 0 && (
                <Button
                  colorScheme="red"
                  size="sm"
                  leftIcon={<FaTrash />}
                  onClick={handleBulkDelete}
                  isLoading={deletingUser}
                >
                  {t('admin.users.deleteSelected')} ({selectedUsers.length})
                </Button>
              )}
            </HStack>

            {/* Users Table */}
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th borderColor={borderColor} w="40px">
                      <input 
                        type="checkbox" 
                        checked={selectedUsers.length === filteredUsers.filter(u => u.role !== 'admin').length && filteredUsers.length > 0}
                        onChange={toggleSelectAll}
                      />
                    </Th>
                    <Th borderColor={borderColor}>{t('admin.users.user')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.email')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.role')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.subscription')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.oauth')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.lastLogin')}</Th>
                    <Th borderColor={borderColor}>{t('admin.users.actions')}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredUsers
                    .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                    .map((user) => (
                    <Tr key={user.id} bg={selectedUsers.includes(user.id) ? 'blue.50' : undefined}>
                      <Td borderColor={borderColor}>
                        {user.role !== 'admin' && (
                          <input 
                            type="checkbox" 
                            checked={selectedUsers.includes(user.id)}
                            onChange={() => toggleUserSelection(user.id)}
                          />
                        )}
                      </Td>
                      <Td borderColor={borderColor}>
                        <UserInfoCell
                          name={user.full_name || 'N/A'}
                          email={user.email}
                          avatar={user.oauth_picture}
                          showEmail={false}
                          size="sm"
                        />
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">{user.email}</Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <Badge colorScheme={user.role === 'admin' ? 'blue' : 'blue'}>
                          {user.role}
                        </Badge>
                      </Td>
                      <Td borderColor={borderColor}>
                        {getSubscriptionBadge(user.subscription)}
                      </Td>
                      <Td borderColor={borderColor}>
                        {user.oauth_provider ? (
                          <Badge colorScheme="green">{user.oauth_provider}</Badge>
                        ) : (
                          <Badge>{t('admin.users.emailPassword')}</Badge>
                        )}
                      </Td>
                      <Td borderColor={borderColor}>
                        <Text fontSize="sm">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleDateString()
                            : t('admin.users.never')}
                        </Text>
                      </Td>
                      <Td borderColor={borderColor}>
                        <HStack spacing={1}>
                          <IconButton
                            icon={<FaEye />}
                            size="sm"
                            onClick={() => handleViewUser(user)}
                            aria-label="View user"
                          />
                          {user.role !== 'admin' && (
                            <IconButton
                              icon={<FaTrash />}
                              size="sm"
                              colorScheme="red"
                              variant="ghost"
                              onClick={() => confirmDeleteUser(user)}
                              aria-label="Delete user"
                            />
                          )}
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>

              {filteredUsers.length === 0 && (
                <Flex justify="center" py={10}>
                  <Text color="gray.500">{t('admin.users.noUsersFound')}</Text>
                </Flex>
              )}
              
              {/* Pagination Controls */}
              {filteredUsers.length > 0 && (
                <Flex justify="space-between" align="center" mt={4} px={4}>
                  <HStack spacing={2}>
                    <Text fontSize="sm" color="gray.600">
                      Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredUsers.length)} of {filteredUsers.length} users
                    </Text>
                  </HStack>
                  <HStack spacing={2}>
                    <Select 
                      size="sm" 
                      w="80px" 
                      value={pageSize} 
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                    >
                      <option value={5}>5</option>
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </Select>
                    <Button 
                      size="sm" 
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
                      isDisabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Text fontSize="sm" px={2}>
                      Page {currentPage} of {Math.ceil(filteredUsers.length / pageSize)}
                    </Text>
                    <Button 
                      size="sm" 
                      onClick={() => setCurrentPage(p => Math.min(Math.ceil(filteredUsers.length / pageSize), p + 1))} 
                      isDisabled={currentPage >= Math.ceil(filteredUsers.length / pageSize)}
                    >
                      Next
                    </Button>
                  </HStack>
                </Flex>
              )}
            </Box>
          </VStack>
        </Card>
      </VStack>

      {/* User Details Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{t('admin.users.userDetails')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedUser && (
              <VStack spacing={4} align="stretch">
                <UserInfoCell
                  name={selectedUser.full_name || 'N/A'}
                  email={selectedUser.email}
                  avatar={selectedUser.oauth_picture}
                  size="lg"
                />

                <Box p={4} bg={cardBg} borderRadius="md" borderWidth="1px">
                  <VStack align="stretch" spacing={2}>
                    <InfoRow label={t('admin.users.userId')} value={selectedUser.id} />
                    <HStack justify="space-between">
                      <Text fontWeight="600">{t('admin.users.role')}:</Text>
                      <Badge>{selectedUser.role}</Badge>
                    </HStack>
                    <InfoRow label={t('admin.users.oauthProvider')} value={selectedUser.oauth_provider || t('common.none')} />
                    <HStack justify="space-between">
                      <Text fontWeight="600">{t('admin.users.emailVerified')}:</Text>
                      <Badge colorScheme={selectedUser.email_verified ? 'green' : 'red'}>
                        {selectedUser.email_verified ? t('common.yes') : t('common.no')}
                      </Badge>
                    </HStack>
                    <InfoRow 
                      label={t('admin.users.created')} 
                      value={selectedUser.created_at
                        ? new Date(selectedUser.created_at).toLocaleDateString()
                        : t('admin.users.unknown')} 
                    />
                  </VStack>
                </Box>

                {selectedUser.subscription && (
                  <Box p={4} bg={cardBg} borderRadius="md" borderWidth="1px">
                    <VStack align="stretch" spacing={2}>
                      <Heading size="sm">{t('admin.users.subscriptionDetails')}</Heading>
                      <HStack justify="space-between">
                        <Text fontWeight="600">{t('admin.users.plan')}:</Text>
                        <Badge colorScheme="blue">
                          {selectedUser.subscription.plan || 'free'}
                        </Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontWeight="600">{t('admin.users.status')}:</Text>
                        {getSubscriptionBadge(selectedUser.subscription)}
                      </HStack>
                      {selectedUser.subscription.stripe_customer_id && (
                        <HStack justify="space-between">
                          <Text fontWeight="600">{t('admin.users.stripeCustomer')}:</Text>
                          <Text fontSize="xs">{selectedUser.subscription.stripe_customer_id}</Text>
                        </HStack>
                      )}
                    </VStack>
                  </Box>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            {selectedUser?.role !== 'admin' && (
              <Button
                colorScheme="red"
                size="sm"
                mr={3}
                onClick={() => confirmDeleteUser(selectedUser)}
                leftIcon={<FaTrash />}
              >
                {t('admin.users.deleteUser')}
              </Button>
            )}
            {selectedUser?.subscription?.status === 'active' && (
              <Button
                colorScheme="orange"
                size="sm"
                mr={3}
                onClick={openCancelSubscriptionModal}
                leftIcon={<FaBan />}
              >
                {t('admin.users.cancelSubscription')}
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              {t('common.close')}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Cancel Subscription Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={isCancelSubOpen}
        onClose={onCancelSubClose}
        onConfirm={handleCancelSubscription}
        itemName={`subscription for ${selectedUser?.full_name || selectedUser?.email || 'this user'}`}
        isLoading={cancellingSubscription}
        title={t('admin.confirmCancelSubscription.title')}
        confirmText={t('admin.users.cancelSubscription')}
        confirmColorScheme="orange"
      />

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader color="red.500">{t('admin.users.deleteUser')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Text>
                {t('admin.confirmDelete.userMessage').replace('this user', '')}
                <Text as="span" fontWeight="bold">{selectedUser?.full_name || selectedUser?.email}</Text>?
              </Text>
              <Box p={4} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.200">
                <Text fontSize="sm" color="red.700">
                  ⚠️ This action is permanent and cannot be undone. All user data including:
                </Text>
                <VStack align="start" mt={2} spacing={1}>
                  <Text fontSize="sm" color="red.700">• User account</Text>
                  <Text fontSize="sm" color="red.700">• All posts and content</Text>
                  <Text fontSize="sm" color="red.700">• Content analyses</Text>
                  <Text fontSize="sm" color="red.700">• Scheduled posts</Text>
                  <Text fontSize="sm" color="red.700">• Notifications</Text>
                </VStack>
              </Box>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onDeleteClose}>
              {t('common.cancel')}
            </Button>
            <Button
              colorScheme="red"
              onClick={() => handleDeleteUser(selectedUser?.id, selectedUser?.email)}
              isLoading={deletingUser}
            >
              {t('common.delete')}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
