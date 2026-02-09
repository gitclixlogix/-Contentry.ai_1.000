'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Button,
  Spinner,
  Center,
  useColorModeValue,
  Avatar,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Divider,
  IconButton,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
} from '@chakra-ui/react';
import {
  FaArrowLeft,
  FaBuilding,
  FaUsers,
  FaDollarSign,
  FaCalendar,
  FaGlobe,
  FaEnvelope,
} from 'react-icons/fa';
import Link from 'next/link';
import { getApiUrl } from '@/lib/api';

export default function CompanyDetailPage() {
  const { companyId } = useParams();
  const router = useRouter();
  const [company, setCompany] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  useEffect(() => {
    fetchCompanyDetails();
  }, [companyId]);
  
  const fetchCompanyDetails = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      
      const response = await fetch(`${getApiUrl()}/superadmin/customers/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-user-id': userId,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCompany(data.company);
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('Error fetching company details:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };
  
  const getPlanBadge = (plan) => {
    const planConfig = {
      enterprise: { color: 'purple', label: 'Enterprise' },
      pro: { color: 'blue', label: 'Pro' },
      starter: { color: 'green', label: 'Starter' },
      free: { color: 'gray', label: 'Free' },
    };
    const config = planConfig[plan?.toLowerCase()] || planConfig.free;
    return <Badge colorScheme={config.color} fontSize="md" px={3} py={1}>{config.label}</Badge>;
  };
  
  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { color: 'green', label: 'Active' },
      inactive: { color: 'gray', label: 'Inactive' },
      invited: { color: 'blue', label: 'Invited' },
      deactivated: { color: 'red', label: 'Deactivated' },
    };
    const config = statusConfig[status?.toLowerCase()] || statusConfig.inactive;
    return <Badge colorScheme={config.color}>{config.label}</Badge>;
  };
  
  if (loading) {
    return (
      <Center h="400px">
        <Spinner size="xl" color="red.500" />
      </Center>
    );
  }
  
  if (!company) {
    return (
      <Center h="400px">
        <VStack>
          <FaBuilding size={50} color="gray" />
          <Text color={mutedColor}>Company not found</Text>
          <Button onClick={() => router.push('/superadmin/users')} leftIcon={<FaArrowLeft />}>
            Back to Customers
          </Button>
        </VStack>
      </Center>
    );
  }
  
  return (
    <Box>
      {/* Breadcrumb */}
      <Breadcrumb mb={4} fontSize="sm">
        <BreadcrumbItem>
          <BreadcrumbLink as={Link} href="/superadmin/users" color="red.500">
            Users & Customers
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>
          <BreadcrumbLink color={mutedColor}>{company.name}</BreadcrumbLink>
        </BreadcrumbItem>
      </Breadcrumb>
      
      {/* Header */}
      <HStack justify="space-between" mb={6}>
        <HStack spacing={4}>
          <Avatar size="lg" name={company.name} bg="red.500" icon={<FaBuilding />} />
          <VStack align="start" spacing={0}>
            <Heading size="lg" color={textColor}>{company.name}</Heading>
            <HStack>
              {getPlanBadge(company.subscription_plan)}
              {getStatusBadge(company.status)}
            </HStack>
          </VStack>
        </HStack>
        <Button leftIcon={<FaArrowLeft />} variant="outline" onClick={() => router.push('/superadmin/users')}>
          Back
        </Button>
      </HStack>
      
      {/* Company Stats */}
      <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={6}>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box as={FaDollarSign} color="green.500" />
                <StatLabel color={mutedColor}>MRR</StatLabel>
              </HStack>
              <StatNumber color={textColor}>{formatCurrency(company.mrr)}</StatNumber>
              <StatHelpText>Monthly revenue</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box as={FaUsers} color="blue.500" />
                <StatLabel color={mutedColor}>Users</StatLabel>
              </HStack>
              <StatNumber color={textColor}>{users.length}</StatNumber>
              <StatHelpText>Team members</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box as={FaCalendar} color="purple.500" />
                <StatLabel color={mutedColor}>Customer Since</StatLabel>
              </HStack>
              <StatNumber fontSize="lg" color={textColor}>{formatDate(company.created_at)}</StatNumber>
              <StatHelpText>Sign-up date</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <HStack>
                <Box as={FaGlobe} color="teal.500" />
                <StatLabel color={mutedColor}>Domain</StatLabel>
              </HStack>
              <StatNumber fontSize="lg" color={textColor}>{company.domain || 'N/A'}</StatNumber>
              <StatHelpText>Company domain</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Users Table */}
      <Card bg={cardBg}>
        <CardHeader>
          <HStack>
            <FaUsers />
            <Heading size="md">Team Members ({users.length})</Heading>
          </HStack>
        </CardHeader>
        <CardBody p={0}>
          {users.length === 0 ? (
            <Center py={10}>
              <VStack>
                <FaUsers size={40} color="gray" />
                <Text color={mutedColor}>No users in this organization</Text>
              </VStack>
            </Center>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>User</Th>
                  <Th>Email</Th>
                  <Th>Role</Th>
                  <Th>Last Login</Th>
                  <Th>Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {users.map((user) => (
                  <Tr key={user.id}>
                    <Td>
                      <HStack>
                        <Avatar size="sm" name={user.full_name} src={user.profile_picture} />
                        <Text fontWeight="500">{user.full_name || 'Unknown'}</Text>
                      </HStack>
                    </Td>
                    <Td color={mutedColor}>{user.email}</Td>
                    <Td>
                      <Badge colorScheme={user.enterprise_role === 'enterprise_admin' ? 'purple' : 'gray'}>
                        {user.enterprise_role || user.role || 'member'}
                      </Badge>
                    </Td>
                    <Td>{formatDate(user.last_login)}</Td>
                    <Td>{getStatusBadge(user.status || (user.email_verified ? 'active' : 'invited'))}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>
    </Box>
  );
}
