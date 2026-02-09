'use client';
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  Text,
  VStack,
  HStack,
  Grid,
  Badge,
  Icon,
  useColorModeValue,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { FaCheck } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';


export default function Subscription() {
  const [plans, setPlans] = useState([]);
  const [currentSub, setCurrentSub] = useState(null);
  const [user, setUser] = useState(null);

  const cardBg = useColorModeValue('white', 'gray.800');

  const loadPlans = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/subscriptions/plans`);
      setPlans(response.data);
    } catch (error) {
      alert('Failed to load plans');
    }
  };

  const loadCurrentSubscription = async (userId) => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/subscriptions/current`, { params: { user_id: userId } });
      setCurrentSub(response.data);
    } catch (error) {
      console.error('Failed to load subscription');
    }
  };

  const checkPaymentStatus = () => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    if (sessionId) {
      pollPaymentStatus(sessionId);
    }
  };

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    if (attempts >= 5) {
      alert('Payment verification timed out');
      return;
    }

    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/payments/checkout/status/${sessionId}`);
      if (response.data.payment_status === 'paid') {
        alert('Payment successful! Your subscription has been activated.');
        if (user) loadCurrentSubscription(user.id);
        if (typeof window !== 'undefined') {
          window.history.replaceState({}, '', window.location.pathname);
        }
      } else if (response.data.status === 'expired') {
        alert('Payment session expired. Please try again.');
      } else {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
      }
    } catch (error) {
      alert('Failed to verify payment');
    }
  };

  const handleUpgrade = async (planId) => {
    if (!user) return;
    
    // Handle free plan directly without Stripe
    if (planId === 'free') {
      try {
        const API = getApiUrl();
        const originUrl = typeof window !== 'undefined' ? window.location.origin : '';
        const response = await axios.post(
          `${API}/payments/checkout/session?package_id=${planId}&user_id=${user.id}`,
          { origin_url: originUrl }
        );
        
        if (response.data.message) {
          alert(response.data.message);
          loadCurrentSubscription(user.id);
        }
      } catch (error) {
        alert('Failed to activate free plan');
      }
      return;
    }
    
    try {
      const API = getApiUrl();
      const originUrl = typeof window !== 'undefined' ? window.location.origin : '';
      const response = await axios.post(
        `${API}/payments/checkout/session?package_id=${planId}&user_id=${user.id}`,
        { origin_url: originUrl }
      );
      
      if (response.data.url && typeof window !== 'undefined') {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert(error.response?.data?.detail || 'Checkout failed');
    }
  };

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      loadPlans();
      loadCurrentSubscription(userData.id);
      checkPaymentStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  return (
    <Box>
      <Heading size="lg" mb={6}>Subscription & Billing</Heading>

      {currentSub && (
        <Card mb={6} bgGradient="linear(to-br, brand.500, blue.600)" color="white">
          <CardBody p={8}>
            <Heading size="md" mb={2}>Current {currentSub.plan} Plan</Heading>
            <Text fontSize="4xl" fontWeight="700" mb={2}>${currentSub.price.toFixed(2)}</Text>
            <Text opacity={0.9} mb={6}>{currentSub.credits.toLocaleString()} Credits Remaining</Text>
            <HStack>
              <Button bg="white" color="brand.500" _hover={{ bg: 'gray.100' }}>ADD TOKENS</Button>
              <Button variant="outline" borderColor="white" color="white" _hover={{ bg: 'whiteAlpha.200' }}>CANCEL SUBSCRIPTION</Button>
            </HStack>
          </CardBody>
        </Card>
      )}

      <Heading size="md" mb={6}>Choose Your Perfect Plan</Heading>

      <Grid templateColumns="repeat(auto-fit, minmax(280px, 1fr))" gap={6}>
        {plans.map((plan) => (
          <Card
            key={plan.id}
            bg={cardBg}
            border={currentSub?.plan === plan.id ? '3px solid' : '1px solid'}
            borderColor={currentSub?.plan === plan.id ? 'brand.500' : 'gray.200'}
            position="relative"
          >
            <CardBody>
              {currentSub?.plan === plan.id && (
                <Badge
                  position="absolute"
                  top={4}
                  right={4}
                  colorScheme="blue"
                >
                  CURRENT
                </Badge>
              )}
              <Heading size="md" mb={2}>{plan.name}</Heading>
              <HStack mb={2}>
                <Text fontSize="2xl" fontWeight="700">${plan.price.toFixed(2)}</Text>
                <Text fontSize="md" color="gray.600">/month</Text>
              </HStack>
              <Text fontSize="sm" color="gray.600" mb={6}>{plan.credits.toLocaleString()} Credits</Text>
              
              <Box mb={6}>
                <Text fontSize="sm" fontWeight="600" mb={3}>What&apos;s Included:</Text>
                <List spacing={2}>
                  {plan.features.map((feature, i) => (
                    <ListItem key={i} fontSize="sm" color="gray.600">
                      <ListIcon as={FaCheck} color="green.500" />
                      {feature}
                    </ListItem>
                  ))}
                </List>
              </Box>

              <Button
                w="full"
                colorScheme="brand"
                onClick={() => handleUpgrade(plan.id)}
                isDisabled={currentSub?.plan === plan.id}
              >
                {currentSub?.plan === plan.id ? 'CURRENT PLAN' : 'BUY NOW'}
              </Button>
            </CardBody>
          </Card>
        ))}
      </Grid>
    </Box>
  );
}