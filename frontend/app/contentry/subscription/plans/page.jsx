'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  useColorModeValue,
  Container,
  SimpleGrid,
  List,
  ListItem,
  ListIcon,
  Badge,
  useToast,
} from '@chakra-ui/react';
import { FaCheck, FaStar } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

export default function SubscriptionPlansPage() {
  const router = useRouter();
  const toast = useToast();
  const [packages, setPackages] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [user, setUser] = useState(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    loadPackages();
    
    // Get user from pending_user or contentry_user
    const pendingUser = localStorage.getItem('pending_user');
    const existingUser = localStorage.getItem('contentry_user');
    
    if (pendingUser) {
      setUser(JSON.parse(pendingUser));
    } else if (existingUser) {
      setUser(JSON.parse(existingUser));
    }
  }, []);

  const loadPackages = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/subscriptions/packages`);
      setPackages(response.data.packages);
    } catch (error) {
      console.error('Failed to load packages:', error);
      toast({
        title: 'Error loading plans',
        description: 'Please refresh the page',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (packageId) => {
    if (!user) {
      toast({
        title: 'Please login first',
        status: 'warning',
        duration: 3000,
      });
      router.push('/contentry/auth/login');
      return;
    }

    setSelectedPlan(packageId);

    try {
      const API = getApiUrl();
      const originUrl = window.location.origin;
      
      const response = await axios.post(`${API}/subscriptions/checkout`, {
        package_id: packageId,
        origin_url: originUrl,
        user_id: user.id
      });

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast({
        title: 'Checkout failed',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
      setSelectedPlan(null);
    }
  };

  if (loading) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={bgColor}>
        <Text>Loading plans...</Text>
      </Flex>
    );
  }

  return (
    <Box minH="100vh" bg={bgColor} py={20}>
      <Container maxW="1200px">
        <VStack spacing={10}>
          {/* Header */}
          <VStack spacing={4} textAlign="center">
            <Heading size="2xl" color={textColor}>
              Choose Your Plan
            </Heading>
            <Text fontSize="xl" color="gray.500">
              Unlock the full power of content analysis and moderation
            </Text>
          </VStack>

          {/* Pricing Cards */}
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={8} w="full">
            {packages && Object.entries(packages).map(([key, pkg]) => {
              const isPopular = key === 'pro';
              
              return (
                <Box
                  key={key}
                  bg={cardBg}
                  borderWidth="2px"
                  borderColor={isPopular ? 'brand.500' : borderColor}
                  borderRadius="xl"
                  p={8}
                  position="relative"
                  boxShadow={isPopular ? 'xl' : 'md'}
                  transform={isPopular ? 'scale(1.05)' : 'scale(1)'}
                  transition="all 0.3s"
                >
                  {isPopular && (
                    <Badge
                      position="absolute"
                      top="-3"
                      right="4"
                      colorScheme="brand"
                      fontSize="sm"
                      px={3}
                      py={1}
                      borderRadius="full"
                    >
                      <HStack spacing={1}>
                        <FaStar size={10} />
                        <Text>Most Popular</Text>
                      </HStack>
                    </Badge>
                  )}

                  <VStack spacing={6} align="stretch">
                    <VStack spacing={2} align="start">
                      <Heading size="md" color={textColor}>
                        {pkg.name}
                      </Heading>
                      <HStack align="baseline">
                        <Heading size="2xl" color={textColor}>
                          ${pkg.price}
                        </Heading>
                        <Text color="gray.500">/month</Text>
                      </HStack>
                    </VStack>

                    <List spacing={3}>
                      {pkg.features.map((feature, idx) => (
                        <ListItem key={idx}>
                          <HStack align="start">
                            <ListIcon as={FaCheck} color="green.500" mt={1} />
                            <Text fontSize="sm">{feature}</Text>
                          </HStack>
                        </ListItem>
                      ))}
                    </List>

                    <Button
                      colorScheme={isPopular ? 'brand' : 'gray'}
                      size="lg"
                      w="full"
                      onClick={() => handleSubscribe(key)}
                      isLoading={selectedPlan === key}
                      loadingText="Redirecting..."
                    >
                      {isPopular ? 'Get Started' : 'Subscribe'}
                    </Button>
                  </VStack>
                </Box>
              );
            })}
          </SimpleGrid>

          {/* FAQ or Additional Info */}
          <Box
            bg={cardBg}
            p={8}
            borderRadius="xl"
            borderWidth="1px"
            borderColor={borderColor}
            w="full"
          >
            <VStack spacing={4} align="start">
              <Heading size="md" color={textColor}>
                What&apos;s included in all plans:
              </Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} w="full">
                <HStack>
                  <FaCheck color="green" />
                  <Text>AI-Powered Content Analysis</Text>
                </HStack>
                <HStack>
                  <FaCheck color="green" />
                  <Text>Real-time Compliance Checking</Text>
                </HStack>
                <HStack>
                  <FaCheck color="green" />
                  <Text>Multi-language Support</Text>
                </HStack>
                <HStack>
                  <FaCheck color="green" />
                  <Text>Secure & Private</Text>
                </HStack>
              </SimpleGrid>
            </VStack>
          </Box>

          {/* Back Button */}
          <Button
            variant="ghost"
            onClick={() => router.push('/contentry/auth/login')}
          >
            Back to Login
          </Button>
        </VStack>
      </Container>
    </Box>
  );
}
