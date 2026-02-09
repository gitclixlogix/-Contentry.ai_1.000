'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  HStack,
  useColorModeValue,
  useToast,
  Checkbox,
  Link as ChakraLink,
  Tabs,
  TabList,
  Tab,
  InputGroup,
  InputRightElement,
  IconButton,
  List,
  ListItem,
  ListIcon,
  Divider,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { FaEye, FaEyeSlash, FaCheck, FaTimes, FaArrowLeft } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import GoogleLogo from '@/components/icons/GoogleLogo';
import MicrosoftLogo from '@/components/icons/MicrosoftLogo';
import AppleLogo from '@/components/icons/AppleLogo';
import SlackLogo from '@/components/icons/SlackLogo';
import ContentryLogo from '@/components/branding/ContentryLogo';
import LanguageSelector from '@/components/LanguageSelector';
import PasswordStrengthIndicator, { isPasswordValid as checkPasswordValid } from '@/components/auth/PasswordStrengthIndicator';

export default function SignupPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const [mounted, setMounted] = useState(false);
  const [registrationMethod, setRegistrationMethod] = useState('email'); // 'email' or 'phone'
  const [fullName, setFullName] = useState('');
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false);
  const [consentDataProcessing, setConsentDataProcessing] = useState(false);
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [loading, setLoading] = useState(false);

  const textColor = useColorModeValue('gray.800', 'white');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const pageBg = useColorModeValue('gray.50', 'gray.900');

  // Handle hydration mismatch caused by browser extensions (password managers, etc.)
  useEffect(() => {
    setMounted(true);
  }, []);

  // Helper function to extract error message from response
  const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
    const detail = error?.response?.data?.detail;
    if (!detail) return defaultMessage;
    
    // If detail is a string, return it directly
    if (typeof detail === 'string') return detail;
    
    // If detail is an array (Pydantic validation errors)
    if (Array.isArray(detail)) {
      const messages = detail.map(err => {
        if (typeof err === 'string') return err;
        if (err.msg) return err.msg;
        return JSON.stringify(err);
      });
      return messages.join(', ');
    }
    
    // If detail is an object with error key
    if (typeof detail === 'object') {
      if (detail.error) return detail.error;
      if (detail.msg) return detail.msg;
      if (detail.message) return detail.message;
    }
    
    return defaultMessage;
  };

  // Password validation now handled by PasswordStrengthIndicator
  const isPasswordValid = checkPasswordValid(password);
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;
  
  // Email/Phone validation
  const isEmailValid = registrationMethod === 'email' ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailOrPhone) : true;
  const isPhoneValid = registrationMethod === 'phone' ? /^\+?[1-9]\d{9,14}$/.test(emailOrPhone.replace(/\s/g, '')) : true;
  const isContactValid = registrationMethod === 'email' ? isEmailValid : isPhoneValid;
  
  const canSubmit = fullName.length >= 2 && emailOrPhone && isContactValid && isPasswordValid && passwordsMatch && acceptedTerms && acceptedPrivacy && consentDataProcessing;

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (!canSubmit) {
      toast({
        title: 'Please complete all required fields',
        description: 'Make sure you accept the terms and privacy policy',
        status: 'warning',
        duration: 5000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      const signupData = {
        full_name: fullName,
        [registrationMethod]: emailOrPhone,
        password: password,
        accepted_terms: true,
        accepted_privacy: true,
        consent_data_processing: true,
        marketing_consent: marketingConsent,
        registration_method: registrationMethod,
      };

      const response = await axios.post(`${API}/auth/signup`, signupData);

      if (response.data.success) {
        toast({
          title: 'Account created!',
          description: 'Please check your email to verify your account',
          status: 'success',
          duration: 5000,
        });
        
        // Redirect to subscription plans
        router.push('/contentry/subscription/plans');
      }
    } catch (error) {
      toast({
        title: 'Signup failed',
        description: getErrorMessage(error, 'Please try again'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthSignup = (provider) => {
    const API = getApiUrl();
    
    if (provider === 'google') {
      const redirectUrl = `${window.location.origin}/contentry/auth/login`;
      window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    } else if (provider === 'microsoft') {
      // Redirect to Microsoft SSO login (will create account if not exists)
      window.location.href = `${API}/sso/microsoft/login`;
    } else {
      toast({
        title: `${provider} OAuth`,
        description: 'Will be available soon',
        status: 'info',
        duration: 3000,
      });
    }
  };

  // Show loading state until client is mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={pageBg}>
        <Center>
          <VStack spacing={4}>
            <Spinner size="xl" color="blue.500" thickness="4px" />
            <Text color="gray.500">{t('auth.login.loading')}</Text>
          </VStack>
        </Center>
      </Flex>
    );
  }

  return (
    <Flex minH="100vh" align="center" justify="center" bg={pageBg} py={10} position="relative">
      {/* Language Selector - Top Right Corner */}
      <Box position="absolute" top={4} right={4} zIndex={10}>
        <LanguageSelector />
      </Box>
      
      <Box
        maxW="500px"
        w="full"
        bg={bgColor}
        boxShadow="xl"
        rounded="lg"
        p={8}
        borderWidth="1px"
        borderColor={borderColor}
      >
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <VStack spacing={2}>
            <ContentryLogo size="sm" />
            <Text fontSize="sm" color="gray.500" textAlign="center">
              {t('auth.signup.subtitle')}
            </Text>
          </VStack>

          {/* Signup Form */}
          <form onSubmit={handleSignup} suppressHydrationWarning>
            <VStack spacing={4}>
              {/* Full Name */}
              <FormControl isRequired isInvalid={fullName.length > 0 && fullName.length < 2}>
                <FormLabel fontSize="sm" color={textColor}>{t('auth.signup.fullName')}</FormLabel>
                <Input
                  placeholder={t('auth.signup.fullNamePlaceholder')}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  size="lg"
                  borderColor={fullName.length > 0 && fullName.length < 2 ? 'red.500' : borderColor}
                  autoComplete="name"
                />
                {fullName.length > 0 && fullName.length < 2 && (
                  <Text fontSize="xs" color="red.500" mt={1}>
                    Name must be at least 2 characters
                  </Text>
                )}
              </FormControl>

              {/* Email/Phone Tabs */}
              <FormControl isRequired isInvalid={emailOrPhone && registrationMethod === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailOrPhone)}>
                <FormLabel fontSize="sm" color={textColor}>
                  {registrationMethod === 'email' ? t('auth.signup.email') : t('auth.login.phoneNumber')}
                </FormLabel>
                <Tabs
                  variant="soft-rounded"
                  colorScheme="brand"
                  size="sm"
                  mb={2}
                  onChange={(index) => setRegistrationMethod(index === 0 ? 'email' : 'phone')}
                >
                  <TabList>
                    <Tab flex={1} fontSize="xs">{t('auth.login.emailTab')}</Tab>
                    <Tab flex={1} fontSize="xs">{t('auth.login.phoneTab')}</Tab>
                  </TabList>
                </Tabs>
                <Input
                  type={registrationMethod === 'email' ? 'email' : 'tel'}
                  placeholder={registrationMethod === 'email' ? t('auth.signup.emailPlaceholder') : '+1234567890'}
                  value={emailOrPhone}
                  onChange={(e) => setEmailOrPhone(e.target.value)}
                  size="lg"
                  borderColor={emailOrPhone && registrationMethod === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailOrPhone) ? 'red.500' : borderColor}
                  autoComplete={registrationMethod === 'email' ? 'email' : 'tel'}
                />
                {emailOrPhone && registrationMethod === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailOrPhone) && (
                  <Text fontSize="xs" color="red.500" mt={1}>
                    Please enter a valid email address
                  </Text>
                )}
                {emailOrPhone && registrationMethod === 'phone' && !/^\+?[1-9]\d{9,14}$/.test(emailOrPhone.replace(/\s/g, '')) && (
                  <Text fontSize="xs" color="red.500" mt={1}>
                    Please enter a valid phone number (e.g., +1234567890)
                  </Text>
                )}
              </FormControl>

              {/* Password */}
              <FormControl isRequired>
                <FormLabel fontSize="sm" color={textColor}>{t('auth.signup.password')}</FormLabel>
                <InputGroup>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={t('auth.signup.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    size="lg"
                    borderColor={borderColor}
                    autoComplete="new-password"
                  />
                  <InputRightElement h="full">
                    <IconButton
                      aria-label="Toggle password"
                      icon={showPassword ? <FaEyeSlash /> : <FaEye />}
                      onClick={() => setShowPassword(!showPassword)}
                      variant="ghost"
                      size="sm"
                    />
                  </InputRightElement>
                </InputGroup>
                {/* Password Strength Indicator */}
                <PasswordStrengthIndicator password={password} showRequirements={true} />
              </FormControl>

              {/* Confirm Password */}
              <FormControl isRequired>
                <FormLabel fontSize="sm" color={textColor}>{t('auth.signup.confirmPassword')}</FormLabel>
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder={t('auth.signup.confirmPasswordPlaceholder')}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  size="lg"
                  borderColor={borderColor}
                />
                {/* Password Match Indicator */}
                {confirmPassword && (
                  <HStack mt={2} spacing={2}>
                    <ListIcon
                      as={passwordsMatch ? FaCheck : FaTimes}
                      color={passwordsMatch ? 'green.500' : 'red.500'}
                    />
                    <Text fontSize="xs" color={passwordsMatch ? 'green.500' : 'red.500'}>
                      {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
                    </Text>
                  </HStack>
                )}
              </FormControl>

              {/* GDPR Compliance Checkboxes */}
              <VStack align="stretch" spacing={3} pt={2} w="full">
                <Checkbox
                  isChecked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  colorScheme="brand"
                  size="sm"
                >
                  <Text fontSize="xs">
                    {t('auth.signup.agreeToTerms')}{' '}
                    <ChakraLink href="/contentry/terms" color="brand.500" isExternal>
                      {t('auth.signup.termsOfService')}
                    </ChakraLink>
                    {' '}<Text as="span" color="red.500">{t('auth.gdpr.required')}</Text>
                  </Text>
                </Checkbox>

                <Checkbox
                  isChecked={acceptedPrivacy}
                  onChange={(e) => setAcceptedPrivacy(e.target.checked)}
                  colorScheme="brand"
                  size="sm"
                >
                  <Text fontSize="xs">
                    {t('auth.signup.agreeToTerms')}{' '}
                    <ChakraLink href="/contentry/privacy" color="brand.500" isExternal>
                      {t('auth.signup.privacyPolicy')}
                    </ChakraLink>
                    {' '}<Text as="span" color="red.500">{t('auth.gdpr.required')}</Text>
                  </Text>
                </Checkbox>

                <Checkbox
                  isChecked={consentDataProcessing}
                  onChange={(e) => setConsentDataProcessing(e.target.checked)}
                  colorScheme="brand"
                  size="sm"
                >
                  <Text fontSize="xs">
                    {t('auth.gdpr.consentDataProcessing')} <Text as="span" color="red.500">{t('auth.gdpr.required')}</Text>
                  </Text>
                </Checkbox>

                <Checkbox
                  isChecked={marketingConsent}
                  onChange={(e) => setMarketingConsent(e.target.checked)}
                  colorScheme="brand"
                  size="sm"
                >
                  <Text fontSize="xs">
                    {t('auth.gdpr.marketingConsent')}
                  </Text>
                </Checkbox>
              </VStack>

              <Button
                type="submit"
                colorScheme="brand"
                size="lg"
                w="full"
                isLoading={loading}
                isDisabled={!canSubmit}
              >
                {t('auth.signup.createAccount')}
              </Button>
            </VStack>
          </form>

          {/* Divider */}
          <HStack spacing={4}>
            <Divider />
            <Text fontSize="sm" color="gray.500" whiteSpace="nowrap">
              {t('auth.signup.orSignUpWith')}
            </Text>
            <Divider />
          </HStack>

          {/* OAuth Buttons */}
          <VStack spacing={2}>
            <Button
              w="full"
              bg="white"
              color="#3c4043"
              border="1px solid"
              borderColor="gray.300"
              leftIcon={<GoogleLogo size={18} />}
              onClick={() => handleOAuthSignup('google')}
              size="md"
              fontWeight="500"
              justifyContent="flex-start"
              pl={6}
              _hover={{ bg: 'gray.50', borderColor: 'gray.400' }}
            >
              <Text ml={4}>Google</Text>
            </Button>
            
            <Button
              w="full"
              bg="white"
              color="#3c4043"
              border="1px solid"
              borderColor="gray.300"
              leftIcon={<MicrosoftLogo size={21} />}
              onClick={() => handleOAuthSignup('microsoft')}
              size="md"
              fontWeight="500"
              justifyContent="flex-start"
              pl={6}
              _hover={{ bg: 'gray.50', borderColor: 'gray.400' }}
            >
              <Text ml={4}>Microsoft</Text>
            </Button>
            
            <Button
              w="full"
              bg="white"
              color="#3c4043"
              border="1px solid"
              borderColor="gray.300"
              leftIcon={<Box color="#000000"><AppleLogo size={18} /></Box>}
              onClick={() => handleOAuthSignup('apple')}
              size="md"
              fontWeight="500"
              justifyContent="flex-start"
              pl={6}
              _hover={{ bg: 'gray.50', borderColor: 'gray.400' }}
            >
              <Text ml={4}>Apple</Text>
            </Button>
            
            <Button
              w="full"
              bg="white"
              color="#3c4043"
              border="1px solid"
              borderColor="gray.300"
              leftIcon={<SlackLogo size={20} />}
              onClick={() => handleOAuthSignup('slack')}
              size="md"
              fontWeight="500"
              justifyContent="flex-start"
              pl={6}
              _hover={{ bg: 'gray.50', borderColor: 'gray.400' }}
            >
              <Text ml={4}>Slack</Text>
            </Button>
          </VStack>

          {/* Footer */}
          <VStack spacing={2}>
            <HStack fontSize="sm">
              <Text color="gray.500">{t('auth.signup.alreadyHaveAccount')}</Text>
              <ChakraLink color="brand.500" href="/contentry/auth/login">
                {t('auth.signup.logIn')}
              </ChakraLink>
            </HStack>
            
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<FaArrowLeft />}
              onClick={() => router.push('/contentry/auth/login')}
            >
              Back to Login
            </Button>
          </VStack>
        </VStack>
      </Box>
    </Flex>
  );
}
