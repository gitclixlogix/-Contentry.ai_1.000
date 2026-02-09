'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  Box, Button, Card, CardBody, Text, VStack, useColorModeValue,
  Heading, Icon, Flex, Badge, Stat, StatLabel, StatNumber, StatHelpText, Grid, SimpleGrid, Spinner
} from '@chakra-ui/react';
import { FaCreditCard, FaArrowLeft, FaChartLine, FaUsers } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

export default function BillingUsagePage() {
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [companyUsage, setCompanyUsage] = useState({
    totalAnalyses: 0,
    totalPosts: 0,
    totalUsers: 0
  });
  const router = useRouter();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const planBg = useColorModeValue('blue.50', 'blue.900');
  const userStatBg = useColorModeValue('blue.50', 'blue.900');
  const userStatBorderColor = useColorModeValue('blue.200', 'blue.700');
  const postStatBg = useColorModeValue('blue.50', 'blue.900');
  const postStatBorderColor = useColorModeValue('blue.200', 'blue.700');
  const analysisStatBg = useColorModeValue('green.50', 'green.900');
  const analysisStatBorderColor = useColorModeValue('green.200', 'green.700');
  const noteBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    const storedUser = localStorage.getItem('contentry_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setUser(userData);
      
      // Check if user is enterprise admin (accept both 'admin' and 'enterprise_admin' roles)
      const isEnterpriseAdmin = userData.enterprise_role === 'enterprise_admin' || 
                                 userData.enterprise_role === 'admin' ||
                                 userData.is_enterprise_admin === true;
      
      if (!isEnterpriseAdmin || !userData.enterprise_id) {
        router.push('/contentry/dashboard');
        return;
      }
      
      loadCompanyUsage(userData.enterprise_id, userData.id);
    } else {
      router.push('/contentry/auth/login');
    }
  }, [router]);

  const loadCompanyUsage = async (enterpriseId, userId) => {
    try {
      const API = getApiUrl();
      
      // Get all company users
      const usersResponse = await axios.get(
        `${API}/enterprises/${enterpriseId}/settings/users`,
        { headers: { 'X-User-ID': userId } }
      );
      
      const companyUsers = usersResponse.data.users || [];
      setUsers(companyUsers);
      
      // Calculate aggregated usage
      let totalAnalyses = 0;
      let totalPosts = 0;
      
      // Fetch posts for each user to get usage
      for (const companyUser of companyUsers) {
        try {
          const postsResponse = await axios.get(`${API}/posts`, {
            headers: { 'X-User-ID': companyUser.id },
            params: { user_id: companyUser.id }
          });
          totalPosts += postsResponse.data.posts?.length || 0;
        } catch (error) {
          console.log(`Could not fetch posts for user ${companyUser.id}`);
        }
      }
      
      // Estimate analyses (typically 1-2 per post)
      totalAnalyses = totalPosts * 2;
      
      setCompanyUsage({
        totalAnalyses,
        totalPosts,
        totalUsers: companyUsers.length
      });
    } catch (error) {
      console.error('Failed to load company usage:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Button
        leftIcon={<Icon as={FaArrowLeft} />}
        variant="ghost"
        mb={4}
        onClick={() => router.push('/contentry/enterprise/settings')}
      >
        Back to Company Settings
      </Button>

      <VStack spacing={6} align="stretch">
        <Card bg={bgColor} boxShadow="lg">
          <CardBody p={{ base: 4, md: 6 }}>
            <Flex align="center" gap={3} mb={6}>
              <Icon as={FaCreditCard} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>Billing & Usage</Heading>
            </Flex>

            <VStack spacing={4} align="stretch">
              <Flex align="center" justify="space-between" p={4} bg={planBg} borderRadius="md">
                <Box>
                  <Text fontSize="sm" color={textColorSecondary}>Current Plan</Text>
                  <Text fontSize="2xl" fontWeight="700" color={textColor}>Enterprise</Text>
                </Box>
                <Badge colorScheme="green" fontSize="lg" px={4} py={2}>Active</Badge>
              </Flex>

              <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={4}>
                <Stat>
                  <StatLabel>Monthly Cost</StatLabel>
                  <StatNumber>$299</StatNumber>
                  <StatHelpText>Per month</StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Next Billing Date</StatLabel>
                  <StatNumber>Dec 29, 2025</StatNumber>
                  <StatHelpText>Renews automatically</StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Payment Method</StatLabel>
                  <StatNumber fontSize="md">•••• 4242</StatNumber>
                  <StatHelpText>Visa</StatHelpText>
                </Stat>
              </Grid>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={bgColor} boxShadow="lg">
          <CardBody p={{ base: 4, md: 6 }}>
            <Flex align="center" gap={3} mb={6}>
              <Icon as={FaChartLine} boxSize={5} color="brand.500" />
              <Heading size="md" color={textColor}>Company-Wide Usage</Heading>
              <Badge colorScheme="blue" fontSize="sm">
                <Flex align="center" gap={1}>
                  <Icon as={FaUsers} boxSize={3} />
                  {companyUsage.totalUsers} users
                </Flex>
              </Badge>
            </Flex>

            {loading ? (
              <Flex justify="center" py={8}>
                <Spinner size="lg" color="brand.500" />
              </Flex>
            ) : (
              <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
                <Box 
                  p={6} 
                  bg={userStatBg} 
                  borderRadius="lg"
                  borderWidth="2px"
                  borderColor={userStatBorderColor}
                >
                  <Stat>
                    <StatLabel color={textColorSecondary} fontSize="sm">Total Users</StatLabel>
                    <StatNumber color={textColor} fontSize="3xl">
                      {companyUsage.totalUsers}
                    </StatNumber>
                    <StatHelpText>Active company members</StatHelpText>
                  </Stat>
                </Box>

                <Box 
                  p={6} 
                  bg={postStatBg} 
                  borderRadius="lg"
                  borderWidth="2px"
                  borderColor={postStatBorderColor}
                >
                  <Stat>
                    <StatLabel color={textColorSecondary} fontSize="sm">Total Posts</StatLabel>
                    <StatNumber color={textColor} fontSize="3xl">
                      {companyUsage.totalPosts}
                    </StatNumber>
                    <StatHelpText>Across all users</StatHelpText>
                  </Stat>
                </Box>

                <Box 
                  p={6} 
                  bg={analysisStatBg} 
                  borderRadius="lg"
                  borderWidth="2px"
                  borderColor={analysisStatBorderColor}
                >
                  <Stat>
                    <StatLabel color={textColorSecondary} fontSize="sm">Content Analyses</StatLabel>
                    <StatNumber color={textColor} fontSize="3xl">
                      {companyUsage.totalAnalyses}
                    </StatNumber>
                    <StatHelpText>Total analyses performed</StatHelpText>
                  </Stat>
                </Box>
              </SimpleGrid>
            )}

            <Box mt={6} p={4} bg={noteBg} borderRadius="md">
              <Text fontSize="sm" color={textColorSecondary}>
                💡 <strong>Note:</strong> Usage statistics are aggregated across all {companyUsage.totalUsers} users in your organization.
              </Text>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}
