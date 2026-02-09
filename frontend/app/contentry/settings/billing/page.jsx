'use client';
import { useState, useEffect, useCallback, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Heading,
  Card,
  CardBody,
  Text,
  Button,
  SimpleGrid,
  Badge,
  Flex,
  VStack,
  HStack,
  Icon,
  useColorModeValue,
  Divider,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  useToast,
  Alert,
  AlertIcon,
  List,
  ListItem,
  ListIcon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Spinner,
  Center,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';
import { 
  FaCoins, FaCreditCard, FaReceipt, FaDownload, FaPlus, FaCheck, 
  FaCrown, FaCheckCircle, FaRocket, FaUsers, FaBuilding, FaStar
} from 'react-icons/fa';
import api, { createAuthenticatedAxios } from '@/lib/api';
import { useSearchParams, useRouter } from 'next/navigation';

// Plan icons mapping
const PLAN_ICONS = {
  free: FaCoins,
  starter: FaRocket,
  creator: FaStar,
  pro: FaCrown,
  team: FaUsers,
  business: FaBuilding,
  enterprise: FaCrown,
};

// Helper function to get plan tagline
const getPlanTagline = (planId) => {
  const taglines = {
    free: '14-day free trial',
    starter: 'For hobbyists',
    creator: 'For individual creators',
    pro: 'For professionals',
    team: 'For small teams',
    business: 'For growing businesses',
    enterprise: 'Custom solutions',
  };
  return taglines[planId] || '';
};

// Helper function to get plan features
const getPlanFeatures = (planId, credits) => {
  const baseFeatures = {
    free: [
      `${credits} credits for 14 days`,
      'All features included',
      'Content analysis & generation',
      'AI rewrite & image generation',
      'Voice assistant',
      '1 strategic profile',
    ],
    starter: [
      `${credits} credits/month`,
      'All features included',
      '1 strategic profile',
      'Email support (72h)',
    ],
    creator: [
      `${credits} credits/month`,
      'All features included',
      '3 strategic profiles',
      'Priority email support (48h)',
    ],
    pro: [
      `${credits.toLocaleString()} credits/month`,
      'Everything in Creator',
      '10 strategic profiles',
      'Priority support (24h)',
      'Advanced analytics',
    ],
    team: [
      `${credits.toLocaleString()} credits/month`,
      'Everything in Pro',
      'Up to 10 team members',
      'Approval workflows',
      'Shared credit pool',
      'Priority support (4h)',
    ],
    business: [
      `${credits.toLocaleString()} credits/month`,
      'Everything in Team',
      'Unlimited team members',
      'SSO (SAML/OAuth)',
      'Custom roles',
      'Dedicated CSM',
      'Priority support (2h)',
    ],
  };
  return baseFeatures[planId] || [`${credits} credits/month`];
};

// Loading fallback
const PageLoadingFallback = () => (
  <Center minH="50vh">
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Center>
);

function BillingAndInvoicingContent() {
  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [creditBalance, setCreditBalance] = useState(null);
  const [creditPacks, setCreditPacks] = useState([]);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [selectedPack, setSelectedPack] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  
  // Auto-refill state
  const [autoRefillSettings, setAutoRefillSettings] = useState(null);
  const [autoRefillLoading, setAutoRefillLoading] = useState(false);
  const [savingAutoRefill, setSavingAutoRefill] = useState(false);
  
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const { isOpen: isPackOpen, onOpen: onPackOpen, onClose: onPackClose } = useDisclosure();
  const { isOpen: isPlanOpen, onOpen: onPlanOpen, onClose: onPlanClose } = useDisclosure();
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const highlightBg = useColorModeValue('brand.50', 'brand.900');
  const popularBorderColor = useColorModeValue('brand.500', 'brand.400');

  // Load credit balance from API
  const loadCreditBalance = useCallback(async () => {
    try {
      const response = await api.get('/credits/balance');
      if (response.data?.data) {
        setCreditBalance(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load credit balance:', error);
      // Set default values for demo
      setCreditBalance({
        credits_balance: 25,
        credits_used_this_month: 0,
        monthly_allowance: 25,
        plan: 'free',
        plan_name: 'Free',
      });
    }
  }, []);

  // Load credit packs from API
  const loadCreditPacks = useCallback(async () => {
    try {
      const response = await api.get('/credits/packs?currency=USD');
      if (response.data?.data?.packs) {
        setCreditPacks(response.data.data.packs);
      }
    } catch (error) {
      console.error('Failed to load credit packs:', error);
    }
  }, []);

  // Load subscription plans from API with location-based pricing
  const loadSubscriptionPlans = useCallback(async () => {
    try {
      // Try to get user's country for location-based pricing
      let countryCode = null;
      try {
        // Use browser's timezone to estimate country (basic approach)
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        // Map common timezones to country codes
        const tzCountryMap = {
          'Europe/London': 'GB', 'Europe/Oslo': 'NO', 'Europe/Berlin': 'DE',
          'Europe/Paris': 'FR', 'Europe/Amsterdam': 'NL', 'Europe/Brussels': 'BE',
          'Europe/Madrid': 'ES', 'Europe/Rome': 'IT', 'Europe/Vienna': 'AT',
          'America/New_York': 'US', 'America/Los_Angeles': 'US', 'America/Chicago': 'US',
          'Australia/Sydney': 'AU', 'Pacific/Auckland': 'NZ',
        };
        countryCode = tzCountryMap[timezone] || null;
      } catch (e) {
        console.log('Could not detect timezone for pricing');
      }
      
      // Use the location-based pricing endpoint
      const queryParams = countryCode ? `?country_code=${countryCode}` : '';
      const response = await api.get(`/payments/plans${queryParams}`);
      
      if (response.data?.plans) {
        // Map to expected format
        const plans = response.data.plans.map(plan => ({
          id: plan.id,
          name: plan.name,
          credits_monthly: plan.credits,
          price_monthly: plan.monthly_price,
          price_annual: plan.annual_price,
          currency: plan.currency,
          currency_symbol: plan.currency_symbol,
          // Add taglines and features based on plan id
          tagline: getPlanTagline(plan.id),
          features: getPlanFeatures(plan.id, plan.credits),
          popular: plan.id === 'creator',
        }));
        setSubscriptionPlans(plans);
      } else {
        // Fallback to old endpoint if new one fails
        const fallbackResponse = await api.get('/subscriptions/packages');
        if (fallbackResponse.data?.packages) {
          const plans = Object.entries(fallbackResponse.data.packages).map(([id, plan]) => ({
            id,
            ...plan,
          }));
          setSubscriptionPlans(plans);
        }
      }
    } catch (error) {
      console.error('Failed to load subscription plans:', error);
      // Try fallback endpoint
      try {
        const fallbackResponse = await api.get('/subscriptions/packages');
        if (fallbackResponse.data?.packages) {
          const plans = Object.entries(fallbackResponse.data.packages).map(([id, plan]) => ({
            id,
            ...plan,
          }));
          setSubscriptionPlans(plans);
        }
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
      }
    }
  }, []);

  // Poll payment status after returning from Stripe
  const pollPaymentStatus = useCallback(async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setCheckingPayment(false);
      setPaymentStatus('timeout');
      toast({
        title: 'Status Check Timeout',
        description: 'Payment status check timed out. Please check your email for confirmation.',
        status: 'warning',
        duration: 8000,
      });
      return;
    }

    try {
      const axiosInstance = createAuthenticatedAxios();
      const response = await axiosInstance.get(`/payments/checkout/status/${sessionId}`);
      const data = response.data;

      if (data.payment_status === 'paid') {
        setCheckingPayment(false);
        setPaymentStatus('success');
        toast({
          title: 'Payment Successful!',
          description: 'Your purchase has been completed.',
          status: 'success',
          duration: 5000,
        });
        loadCreditBalance();
        router.replace('/contentry/settings/billing');
        return;
      } else if (data.status === 'expired') {
        setCheckingPayment(false);
        setPaymentStatus('expired');
        router.replace('/contentry/settings/billing');
        return;
      }

      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
      } else {
        setCheckingPayment(false);
        setPaymentStatus('error');
      }
    }
  }, [toast, router, loadCreditBalance]);

  // Load auto-refill settings
  const loadAutoRefillSettings = useCallback(async () => {
    setAutoRefillLoading(true);
    try {
      const response = await api.get('/credits/auto-refill/settings');
      if (response.data?.data) {
        setAutoRefillSettings(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load auto-refill settings:', error);
      // Set default settings
      setAutoRefillSettings({
        enabled: false,
        threshold_credits: 100,
        refill_pack_id: 'standard',
        max_refills_per_month: 3,
        refills_this_month: 0,
      });
    } finally {
      setAutoRefillLoading(false);
    }
  }, []);

  // Save auto-refill settings
  const saveAutoRefillSettings = useCallback(async (newSettings) => {
    setSavingAutoRefill(true);
    try {
      const response = await api.put('/credits/auto-refill/settings', newSettings);
      if (response.data?.data) {
        setAutoRefillSettings(response.data.data);
        toast({
          title: newSettings.enabled ? 'Auto-Refill Enabled' : 'Auto-Refill Disabled',
          description: newSettings.enabled 
            ? `Your credits will automatically refill when balance drops below ${newSettings.threshold_credits}`
            : 'Auto-refill has been turned off',
          status: 'success',
          duration: 4000,
        });
      }
    } catch (error) {
      console.error('Failed to save auto-refill settings:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save auto-refill settings',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSavingAutoRefill(false);
    }
  }, [toast]);

  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    
    // Load all data
    Promise.all([
      loadCreditBalance(),
      loadCreditPacks(),
      loadSubscriptionPlans(),
      loadAutoRefillSettings(),
    ]).finally(() => setLoading(false));
    
    // Check if returning from Stripe checkout
    const sessionId = searchParams.get('session_id');
    const purchaseStatus = searchParams.get('purchase');
    
    if (purchaseStatus === 'success' && sessionId) {
      setCheckingPayment(true);
      setPaymentStatus('checking');
      pollPaymentStatus(sessionId);
    } else if (purchaseStatus === 'cancelled') {
      toast({
        title: 'Purchase Cancelled',
        description: 'Your purchase was cancelled.',
        status: 'info',
        duration: 3000,
      });
      router.replace('/contentry/settings/billing');
    }
  }, [searchParams, pollPaymentStatus, loadCreditBalance, loadCreditPacks, loadSubscriptionPlans, loadAutoRefillSettings, toast, router]);

  // Handle credit pack purchase
  const handleBuyCredits = (pack) => {
    setSelectedPack(pack);
    onPackOpen();
  };

  const handleConfirmCreditPurchase = async () => {
    if (!selectedPack) return;
    
    setPurchasing(true);
    try {
      const response = await api.post('/credits/purchase', {
        pack_id: selectedPack.id,
        origin_url: window.location.origin,
        currency: 'USD',
      });
      
      if (response.data?.data?.checkout_url) {
        window.location.href = response.data.data.checkout_url;
      }
    } catch (error) {
      toast({
        title: 'Purchase Failed',
        description: error.response?.data?.detail || 'Failed to create checkout session.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setPurchasing(false);
      onPackClose();
    }
  };

  // Handle subscription change
  const handleSelectPlan = (plan) => {
    if (plan.contact_sales) {
      window.open('mailto:sales@contentry.ai?subject=Enterprise Plan Inquiry', '_blank');
      return;
    }
    setSelectedPlan(plan);
    onPlanOpen();
  };

  const handleConfirmSubscription = async () => {
    // Log for debugging
    console.log('[Checkout] Button clicked');
    console.log('[Checkout] selectedPlan:', selectedPlan);
    console.log('[Checkout] billingCycle:', billingCycle);
    console.log('[Checkout] user:', user);
    
    if (!selectedPlan) {
      console.log('[Checkout] No selected plan, showing error toast');
      toast({
        title: 'Error',
        description: 'Please select a plan first.',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    // Show loading state immediately
    setPurchasing(true);
    console.log('[Checkout] Set purchasing to true');
    
    try {
      const requestPayload = {
        package_id: selectedPlan.id,
        billing_cycle: billingCycle,
        origin_url: window.location.origin,
        user_id: user?.id,
      };
      console.log('[Checkout] Making request with payload:', requestPayload);
      
      const response = await api.post('/subscriptions/checkout', requestPayload);
      
      console.log('[Checkout] Response received:', response.data);
      
      // Backend returns { url, session_id } directly
      const checkoutUrl = response.data?.url || response.data?.data?.checkout_url;
      
      console.log('[Checkout] Checkout URL:', checkoutUrl);
      
      if (checkoutUrl) {
        console.log('[Checkout] Redirecting to Stripe:', checkoutUrl);
        // Use window.location.assign for better cross-browser support
        window.location.assign(checkoutUrl);
      } else if (response.data?.success || response.data?.redirect || selectedPlan.id === 'free') {
        // Free plan activated
        console.log('[Checkout] Free plan activated or success response');
        toast({
          title: 'Plan Updated!',
          description: `You're now on the ${selectedPlan.name} plan.`,
          status: 'success',
          duration: 5000,
        });
        loadCreditBalance();
        onPlanClose();
      } else {
        // Unexpected response format
        console.error('[Checkout] Unexpected response:', response.data);
        toast({
          title: 'Checkout Error',
          description: 'Unexpected response from server. Please try again.',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      console.error('[Checkout] Error caught:', error);
      console.error('[Checkout] Error response:', error.response?.data);
      console.error('[Checkout] Error status:', error.response?.status);
      
      // Extract error message properly
      let errorMessage = 'Failed to process subscription.';
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (detail?.message) {
        errorMessage = detail.message;
      } else if (detail?.error) {
        errorMessage = detail.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Show specific message for auth errors
      if (error.response?.status === 401) {
        errorMessage = 'Please log in again to continue.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to perform this action.';
      }
      
      toast({
        title: 'Subscription Failed',
        description: errorMessage,
        status: 'error',
        duration: 5000,
      });
    } finally {
      console.log('[Checkout] Setting purchasing to false');
      setPurchasing(false);
    }
  };

  // Calculate usage percentage
  const getUsagePercent = () => {
    if (!creditBalance) return 0;
    const { credits_used_this_month, monthly_allowance } = creditBalance;
    if (monthly_allowance <= 0) return 0;
    return Math.min(100, (credits_used_this_month / monthly_allowance) * 100);
  };

  if (loading) {
    return <PageLoadingFallback />;
  }

  return (
    <Box px={{ base: 2, md: 4 }} pt={{ base: '80px', md: '80px' }}>
      {/* Payment Status Indicator */}
      {checkingPayment && (
        <Alert status="info" mb={6} borderRadius="md">
          <Spinner size="sm" mr={3} />
          <Box>
            <Text fontWeight="600">Processing Payment...</Text>
            <Text fontSize="sm">Please wait while we confirm your payment.</Text>
          </Box>
        </Alert>
      )}
      
      {paymentStatus === 'success' && (
        <Alert status="success" mb={6} borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="600">Payment Successful!</Text>
            <Text fontSize="sm">Your credits have been added to your account.</Text>
          </Box>
        </Alert>
      )}
      
      <Heading size={{ base: 'md', md: 'lg' }} mb={{ base: 4, md: 6 }}>
        Billing & Credits
      </Heading>

      {/* Current Balance & Plan Summary */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
        {/* Current Credits */}
        <Card bg={highlightBg} borderWidth="2px" borderColor="brand.500">
          <CardBody>
            <Flex justify="space-between" align="flex-start" direction={{ base: 'column', md: 'row' }} gap={4}>
              <Box flex="1">
                <HStack spacing={3} mb={3}>
                  <Icon as={FaCoins} boxSize={8} color="brand.500" />
                  <Box>
                    <Text fontSize="sm" color={textColorSecondary}>Available Credits</Text>
                    <Heading size="xl" color={textColor}>
                      {creditBalance?.credits_balance?.toLocaleString() || 0}
                    </Heading>
                  </Box>
                </HStack>
                
                {/* Usage Progress */}
                <Box mt={4}>
                  <Flex justify="space-between" mb={1}>
                    <Text fontSize="xs" color={textColorSecondary}>
                      Used this month: {creditBalance?.credits_used_this_month?.toLocaleString() || 0}
                    </Text>
                    <Text fontSize="xs" color={textColorSecondary}>
                      Allowance: {creditBalance?.monthly_allowance?.toLocaleString() || 0}
                    </Text>
                  </Flex>
                  <Progress 
                    value={getUsagePercent()} 
                    colorScheme={getUsagePercent() > 80 ? 'red' : 'brand'} 
                    size="sm" 
                    borderRadius="full"
                  />
                </Box>
              </Box>
              <Button colorScheme="brand" size="sm" leftIcon={<FaPlus />} onClick={() => document.getElementById('credits-section')?.scrollIntoView({ behavior: 'smooth' })}>
                Buy Credits
              </Button>
            </Flex>
          </CardBody>
        </Card>

        {/* Current Plan */}
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            <Flex justify="space-between" align="flex-start" direction={{ base: 'column', md: 'row' }} gap={4}>
              <HStack spacing={4}>
                <Icon as={PLAN_ICONS[creditBalance?.plan] || FaCoins} boxSize={10} color="blue.500" />
                <Box>
                  <Text fontSize="sm" color={textColorSecondary}>Current Plan</Text>
                  <Heading size="lg" color={textColor}>
                    {creditBalance?.plan_name || 'Free'}
                  </Heading>
                  <Text fontSize="xs" color={textColorSecondary}>
                    {creditBalance?.monthly_allowance?.toLocaleString() || 25} credits/month
                  </Text>
                  {creditBalance?.overage_credits > 0 && (
                    <Text fontSize="xs" color="green.500">
                      + {creditBalance.overage_credits.toLocaleString()} purchased credits
                    </Text>
                  )}
                </Box>
              </HStack>
              <Button variant="outline" colorScheme="brand" size="sm" onClick={() => document.getElementById('plans-section')?.scrollIntoView({ behavior: 'smooth' })}>
                Change Plan
              </Button>
            </Flex>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Credit Packs Section */}
      <Box id="credits-section" mb={10}>
        <Heading size="md" color={textColor} mb={2}>Buy Credit Packs</Heading>
        <Text fontSize="sm" color={textColorSecondary} mb={6}>
          Purchase additional credits when you need more. Credits never expire.
        </Text>
        
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          {creditPacks.map((pack) => (
            <Card 
              key={pack.id} 
              bg={cardBg} 
              borderWidth="2px" 
              borderColor={pack.savings_percent > 20 ? popularBorderColor : borderColor}
              position="relative"
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              transition="all 0.2s"
            >
              {pack.savings_percent > 20 && (
                <Badge 
                  position="absolute" 
                  top="-3" 
                  right="3" 
                  colorScheme="brand"
                  fontSize="xs"
                  px={2}
                  py={1}
                  borderRadius="full"
                >
                  Best Value
                </Badge>
              )}
              <CardBody>
                <VStack spacing={3} align="stretch">
                  <Text fontWeight="bold" fontSize="lg" color={textColor}>
                    {pack.name}
                  </Text>
                  <HStack justify="space-between">
                    <Text fontSize="2xl" fontWeight="bold" color="brand.500">
                      {pack.credits.toLocaleString()}
                    </Text>
                    <Text fontSize="sm" color={textColorSecondary}>credits</Text>
                  </HStack>
                  <Divider />
                  <HStack justify="space-between">
                    <Text fontSize="xl" fontWeight="bold" color={textColor}>
                      ${pack.price}
                    </Text>
                    <VStack spacing={0} align="end">
                      <Text fontSize="xs" color={textColorSecondary}>
                        ${pack.per_credit_rate}/credit
                      </Text>
                      {pack.savings_percent > 0 && (
                        <Badge colorScheme="green" fontSize="xs">
                          Save {pack.savings_percent}%
                        </Badge>
                      )}
                    </VStack>
                  </HStack>
                  <Button 
                    colorScheme="brand" 
                    size="sm" 
                    onClick={() => handleBuyCredits(pack)}
                    mt={2}
                  >
                    Buy Now
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>
      </Box>

      {/* Auto-Refill Section */}
      <Box id="auto-refill-section" mb={10}>
        <Heading size="md" color={textColor} mb={2}>Auto-Refill</Heading>
        <Text fontSize="sm" color={textColorSecondary} mb={6}>
          Never run out of credits. Automatically purchase more when your balance drops below a threshold.
        </Text>
        
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody>
            {autoRefillLoading ? (
              <Center py={6}>
                <Spinner size="md" color="brand.500" />
              </Center>
            ) : (
              <VStack spacing={6} align="stretch">
                {/* Enable/Disable Toggle */}
                <Flex justify="space-between" align="center">
                  <Box>
                    <Text fontWeight="semibold" color={textColor}>Enable Auto-Refill</Text>
                    <Text fontSize="sm" color={textColorSecondary}>
                      Automatically purchase credits when balance is low
                    </Text>
                  </Box>
                  <Button
                    colorScheme={autoRefillSettings?.enabled ? 'green' : 'gray'}
                    variant={autoRefillSettings?.enabled ? 'solid' : 'outline'}
                    size="sm"
                    onClick={() => {
                      const newEnabled = !autoRefillSettings?.enabled;
                      saveAutoRefillSettings({
                        ...autoRefillSettings,
                        enabled: newEnabled,
                      });
                    }}
                    isLoading={savingAutoRefill}
                    leftIcon={autoRefillSettings?.enabled ? <FaCheckCircle /> : null}
                  >
                    {autoRefillSettings?.enabled ? 'Enabled' : 'Disabled'}
                  </Button>
                </Flex>

                {autoRefillSettings?.enabled && (
                  <>
                    <Divider />
                    
                    {/* Threshold Setting */}
                    <Box>
                      <Text fontWeight="medium" color={textColor} mb={2}>Refill Threshold</Text>
                      <Text fontSize="sm" color={textColorSecondary} mb={3}>
                        Trigger auto-refill when credits drop below this amount
                      </Text>
                      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={2}>
                        {[50, 100, 200, 500].map((threshold) => (
                          <Button
                            key={threshold}
                            size="sm"
                            variant={autoRefillSettings?.threshold_credits === threshold ? 'solid' : 'outline'}
                            colorScheme={autoRefillSettings?.threshold_credits === threshold ? 'brand' : 'gray'}
                            onClick={() => {
                              saveAutoRefillSettings({
                                ...autoRefillSettings,
                                threshold_credits: threshold,
                              });
                            }}
                            isLoading={savingAutoRefill}
                          >
                            {threshold} credits
                          </Button>
                        ))}
                      </SimpleGrid>
                    </Box>

                    {/* Pack Selection */}
                    <Box>
                      <Text fontWeight="medium" color={textColor} mb={2}>Refill Pack</Text>
                      <Text fontSize="sm" color={textColorSecondary} mb={3}>
                        Choose which credit pack to purchase automatically
                      </Text>
                      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                        {creditPacks.map((pack) => (
                          <Card
                            key={pack.id}
                            size="sm"
                            cursor="pointer"
                            borderWidth="2px"
                            borderColor={autoRefillSettings?.refill_pack_id === pack.id ? 'brand.500' : borderColor}
                            bg={autoRefillSettings?.refill_pack_id === pack.id ? highlightBg : cardBg}
                            onClick={() => {
                              saveAutoRefillSettings({
                                ...autoRefillSettings,
                                refill_pack_id: pack.id,
                              });
                            }}
                            _hover={{ borderColor: 'brand.300' }}
                            transition="all 0.2s"
                          >
                            <CardBody py={3}>
                              <Flex justify="space-between" align="center">
                                <HStack spacing={3}>
                                  <Icon as={FaCoins} color="brand.500" />
                                  <Box>
                                    <Text fontWeight="medium" fontSize="sm">{pack.name}</Text>
                                    <Text fontSize="xs" color={textColorSecondary}>
                                      {pack.credits.toLocaleString()} credits
                                    </Text>
                                  </Box>
                                </HStack>
                                <VStack spacing={0} align="end">
                                  <Text fontWeight="bold" fontSize="sm">${pack.price}</Text>
                                  {pack.savings_percent > 0 && (
                                    <Badge colorScheme="green" fontSize="xs">
                                      Save {pack.savings_percent}%
                                    </Badge>
                                  )}
                                </VStack>
                              </Flex>
                            </CardBody>
                          </Card>
                        ))}
                      </SimpleGrid>
                    </Box>

                    {/* Monthly Limit */}
                    <Box>
                      <Text fontWeight="medium" color={textColor} mb={2}>Monthly Safety Limit</Text>
                      <Text fontSize="sm" color={textColorSecondary} mb={3}>
                        Maximum auto-refills per month (to prevent unexpected charges)
                      </Text>
                      <HStack spacing={2}>
                        {[1, 2, 3, 5, 10].map((limit) => (
                          <Button
                            key={limit}
                            size="sm"
                            variant={autoRefillSettings?.max_refills_per_month === limit ? 'solid' : 'outline'}
                            colorScheme={autoRefillSettings?.max_refills_per_month === limit ? 'brand' : 'gray'}
                            onClick={() => {
                              saveAutoRefillSettings({
                                ...autoRefillSettings,
                                max_refills_per_month: limit,
                              });
                            }}
                            isLoading={savingAutoRefill}
                          >
                            {limit}x
                          </Button>
                        ))}
                      </HStack>
                      <Text fontSize="xs" color={textColorSecondary} mt={2}>
                        Used this month: {autoRefillSettings?.refills_this_month || 0} / {autoRefillSettings?.max_refills_per_month || 3}
                      </Text>
                    </Box>

                    {/* Summary */}
                    <Alert status="info" borderRadius="md">
                      <AlertIcon />
                      <Box>
                        <Text fontWeight="medium" fontSize="sm">
                          Auto-refill Summary
                        </Text>
                        <Text fontSize="sm">
                          When your balance drops below <strong>{autoRefillSettings?.threshold_credits || 100} credits</strong>, 
                          we&apos;ll automatically purchase the{' '}
                          <strong>{autoRefillSettings?.pack_details?.name || 'Standard Pack'}</strong>{' '}
                          (${autoRefillSettings?.pack_details?.price_usd || '22.50'} for{' '}
                          {autoRefillSettings?.pack_details?.credits?.toLocaleString() || '500'} credits).
                        </Text>
                      </Box>
                    </Alert>
                  </>
                )}
              </VStack>
            )}
          </CardBody>
        </Card>
      </Box>

      {/* Subscription Plans Section */}
      <Box id="plans-section" mb={8}>
        <Flex justify="space-between" align="center" mb={6} direction={{ base: 'column', md: 'row' }} gap={4}>
          <Box>
            <Heading size="md" color={textColor}>Subscription Plans</Heading>
            <Text fontSize="sm" color={textColorSecondary}>
              Choose a plan that fits your needs. All plans include monthly credit allowance.
            </Text>
          </Box>
          <HStack>
            <Button
              size="sm"
              variant={billingCycle === 'monthly' ? 'solid' : 'outline'}
              colorScheme="brand"
              onClick={() => setBillingCycle('monthly')}
            >
              Monthly
            </Button>
            <Button
              size="sm"
              variant={billingCycle === 'annual' ? 'solid' : 'outline'}
              colorScheme="brand"
              onClick={() => setBillingCycle('annual')}
            >
              Annual (Save 20%)
            </Button>
          </HStack>
        </Flex>
        
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
          {subscriptionPlans.filter(p => p.id !== 'enterprise').map((plan) => {
            const isCurrentPlan = creditBalance?.plan === plan.id;
            const price = billingCycle === 'annual' ? plan.price_annual : plan.price_monthly;
            
            return (
              <Card 
                key={plan.id} 
                bg={cardBg} 
                borderWidth="2px" 
                borderColor={plan.popular ? popularBorderColor : isCurrentPlan ? 'green.500' : borderColor}
                position="relative"
              >
                {plan.popular && (
                  <Badge 
                    position="absolute" 
                    top="-3" 
                    left="50%"
                    transform="translateX(-50%)"
                    colorScheme="brand"
                    fontSize="xs"
                    px={3}
                    py={1}
                    borderRadius="full"
                  >
                    Most Popular
                  </Badge>
                )}
                {isCurrentPlan && (
                  <Badge 
                    position="absolute" 
                    top="-3" 
                    right="3"
                    colorScheme="green"
                    fontSize="xs"
                    px={2}
                    py={1}
                    borderRadius="full"
                  >
                    Current Plan
                  </Badge>
                )}
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Box textAlign="center">
                      <Icon as={PLAN_ICONS[plan.id] || FaCoins} boxSize={8} color="brand.500" mb={2} />
                      <Heading size="md" color={textColor}>{plan.name}</Heading>
                      <Text fontSize="sm" color={textColorSecondary}>{plan.tagline}</Text>
                    </Box>
                    
                    <Box textAlign="center">
                      <HStack justify="center" align="baseline">
                        <Text fontSize="3xl" fontWeight="bold" color={textColor}>
                          {price === 0 ? 'Free' : `${plan.currency_symbol || '$'}${price?.toFixed(2) || '0.00'}`}
                        </Text>
                        {price > 0 && (
                          <Text fontSize="sm" color={textColorSecondary}>
                            /{billingCycle === 'annual' ? 'year' : 'mo'}
                          </Text>
                        )}
                      </HStack>
                      <Text fontSize="sm" color="brand.500" fontWeight="600">
                        {plan.credits_monthly?.toLocaleString() || 0} credits/month
                      </Text>
                    </Box>
                    
                    <Divider />
                    
                    <List spacing={2} fontSize="sm">
                      {plan.features?.slice(0, 6).map((feature, idx) => (
                        <ListItem key={idx} display="flex" alignItems="flex-start">
                          <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
                          <Text color={textColorSecondary}>{feature}</Text>
                        </ListItem>
                      ))}
                    </List>
                    
                    <Button 
                      colorScheme={isCurrentPlan ? 'gray' : 'brand'}
                      variant={isCurrentPlan ? 'outline' : 'solid'}
                      size="md"
                      onClick={() => !isCurrentPlan && handleSelectPlan(plan)}
                      isDisabled={isCurrentPlan}
                      mt="auto"
                    >
                      {isCurrentPlan ? 'Current Plan' : plan.id === 'free' ? 'Downgrade' : 'Upgrade'}
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            );
          })}
          
          {/* Enterprise Card */}
          <Card bg={cardBg} borderWidth="2px" borderColor={borderColor}>
            <CardBody>
              <VStack spacing={4} align="stretch" h="full">
                <Box textAlign="center">
                  <Icon as={FaCrown} boxSize={8} color="purple.500" mb={2} />
                  <Heading size="md" color={textColor}>Enterprise</Heading>
                  <Text fontSize="sm" color={textColorSecondary}>Custom solutions</Text>
                </Box>
                
                <Box textAlign="center" flex="1">
                  <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                    Custom
                  </Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    Tailored to your needs
                  </Text>
                </Box>
                
                <Divider />
                
                <List spacing={2} fontSize="sm">
                  <ListItem display="flex" alignItems="flex-start">
                    <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
                    <Text color={textColorSecondary}>Custom credit allocation</Text>
                  </ListItem>
                  <ListItem display="flex" alignItems="flex-start">
                    <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
                    <Text color={textColorSecondary}>Dedicated support & SLA</Text>
                  </ListItem>
                  <ListItem display="flex" alignItems="flex-start">
                    <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
                    <Text color={textColorSecondary}>Custom integrations</Text>
                  </ListItem>
                  <ListItem display="flex" alignItems="flex-start">
                    <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
                    <Text color={textColorSecondary}>Volume discounts</Text>
                  </ListItem>
                </List>
                
                <Button 
                  colorScheme="purple"
                  variant="outline"
                  size="md"
                  onClick={() => window.open('mailto:sales@contentry.ai?subject=Enterprise Plan Inquiry', '_blank')}
                  mt="auto"
                >
                  Contact Sales
                </Button>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>
      </Box>

      {/* Credit Pack Purchase Modal */}
      <Modal isOpen={isPackOpen} onClose={onPackClose} isCentered>
        <ModalOverlay bg="blackAlpha.700" zIndex={99998} />
        <ModalContent zIndex={99999} bg={cardBg}>
          <ModalHeader>Purchase Credit Pack</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedPack && (
              <VStack spacing={4} align="stretch">
                <Card bg={highlightBg}>
                  <CardBody>
                    <HStack justify="space-between">
                      <Text fontWeight="bold">{selectedPack.name}</Text>
                      <Text fontWeight="bold" color="brand.500">
                        {selectedPack.credits.toLocaleString()} credits
                      </Text>
                    </HStack>
                  </CardBody>
                </Card>
                <Divider />
                <HStack justify="space-between">
                  <Text>Total:</Text>
                  <Text fontSize="xl" fontWeight="bold">${selectedPack.price}</Text>
                </HStack>
                <Text fontSize="sm" color={textColorSecondary}>
                  Credits will be added to your account immediately after payment.
                </Text>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPackClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleConfirmCreditPurchase}
              isLoading={purchasing}
            >
              Proceed to Checkout
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Plan Change Modal */}
      <Modal isOpen={isPlanOpen} onClose={onPlanClose} isCentered>
        <ModalOverlay bg="blackAlpha.700" zIndex={99998} />
        <ModalContent zIndex={99999} bg={cardBg}>
          <ModalHeader>Change Subscription Plan</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedPlan && (
              <VStack spacing={4} align="stretch">
                <Card bg={highlightBg}>
                  <CardBody>
                    <VStack spacing={2}>
                      <Text fontWeight="bold" fontSize="lg">{selectedPlan.name}</Text>
                      <Text color={textColorSecondary}>{selectedPlan.tagline}</Text>
                      <Text fontWeight="bold" color="brand.500">
                        {selectedPlan.credits_monthly?.toLocaleString() || 0} credits/month
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
                <Divider />
                
                {/* Billing Cycle Toggle in Modal */}
                {selectedPlan.id !== 'free' && (
                  <Box>
                    <Text mb={2} fontWeight="medium">Billing Cycle:</Text>
                    <HStack spacing={2}>
                      <Button
                        size="sm"
                        flex={1}
                        variant={billingCycle === 'monthly' ? 'solid' : 'outline'}
                        colorScheme="brand"
                        onClick={() => setBillingCycle('monthly')}
                      >
                        Monthly
                      </Button>
                      <Button
                        size="sm"
                        flex={1}
                        variant={billingCycle === 'annual' ? 'solid' : 'outline'}
                        colorScheme="brand"
                        onClick={() => setBillingCycle('annual')}
                      >
                        Annual (Save 20%)
                      </Button>
                    </HStack>
                  </Box>
                )}
                
                <HStack justify="space-between">
                  <Text>Price:</Text>
                  <Text fontSize="xl" fontWeight="bold">
                    {selectedPlan.id === 'free' ? 'Free' : (
                      <>
                        {selectedPlan.currency_symbol || '$'}
                        {billingCycle === 'annual' 
                          ? selectedPlan.price_annual?.toFixed(2) 
                          : selectedPlan.price_monthly?.toFixed(2)}
                        <Text as="span" fontSize="sm" fontWeight="normal">
                          /{billingCycle === 'annual' ? 'year' : 'mo'}
                        </Text>
                      </>
                    )}
                  </Text>
                </HStack>
                
                {billingCycle === 'annual' && selectedPlan.id !== 'free' && selectedPlan.price_monthly > 0 && (
                  <Alert status="success" size="sm">
                    <AlertIcon />
                    You save {selectedPlan.currency_symbol || '$'}
                    {((selectedPlan.price_monthly * 12) - selectedPlan.price_annual).toFixed(2)} per year with annual billing!
                  </Alert>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPlanClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleConfirmSubscription}
              isLoading={purchasing}
              data-testid="proceed-to-checkout-btn"
            >
              {selectedPlan?.id === 'free' ? 'Switch to Free' : 'Proceed to Checkout'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <BillingAndInvoicingContent />
    </Suspense>
  );
}
