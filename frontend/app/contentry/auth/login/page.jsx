'use client';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  useColorModeValue,
  VStack,
  HStack,
  useToast,
  Spinner,
  Checkbox,
  Link as ChakraLink,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Center,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Icon,
  InputGroup,
  InputLeftElement,
  Divider,
} from '@chakra-ui/react';
import { FaBuilding, FaEnvelope } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import GoogleLogo from '@/components/icons/GoogleLogo';
import MicrosoftLogo from '@/components/icons/MicrosoftLogo';
import AppleLogo from '@/components/icons/AppleLogo';
import SlackLogo from '@/components/icons/SlackLogo';
import ContentryLogo from '@/components/branding/ContentryLogo';
import LanguageSelector from '@/components/LanguageSelector';

// Loading fallback
const PageLoadingFallback = () => (
  <Center minH="100vh">
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Center>
);

function LoginPageContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const { login } = useAuth();  // Get login function from AuthContext
  const [loginMethod, setLoginMethod] = useState('email'); // 'email' or 'phone'
  const [phoneLoginMode, setPhoneLoginMode] = useState('password'); // 'password' or 'otp'
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [processingOAuth, setProcessingOAuth] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [mounted, setMounted] = useState(false);
  
  // Enterprise SSO state
  const [showSsoModal, setShowSsoModal] = useState(false);
  const [ssoEmail, setSsoEmail] = useState('');
  const [ssoLoading, setSsoLoading] = useState(false);

  // All useColorModeValue hooks must be called at the top level, before any conditional returns
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.300');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.500');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const inputBg = useColorModeValue('white', 'gray.700');
  const placeholderColor = useColorModeValue('gray.400', 'gray.400');
  const linkColor = useColorModeValue('brand.500', 'brand.300');
  const tabUnselectedColor = useColorModeValue('gray.600', 'gray.300');
  
  // Additional color mode values used in JSX (moved from inline to prevent conditional hooks)
  const pageBg = useColorModeValue('gray.50', 'gray.900');
  const oauthBtnBg = useColorModeValue('white', 'gray.700');
  const oauthBtnColor = useColorModeValue('#3c4043', 'white');
  const oauthBtnHoverBorderColor = useColorModeValue('gray.400', 'gray.500');
  const ssoBorderColor = useColorModeValue('blue.200', 'blue.600');
  const ssoBgColor = useColorModeValue('blue.50', 'blue.900');
  const ssoTitleColor = useColorModeValue('blue.700', 'blue.200');
  const ssoTextColor = useColorModeValue('blue.600', 'blue.300');
  const appleIconColor = useColorModeValue('#000000', 'white');

  // Helper function to extract error message from response
  const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
    const detail = error?.response?.data?.detail;
    if (!detail) return defaultMessage;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && detail.error) return detail.error;
    return defaultMessage;
  };

  // Handle hydration mismatch caused by browser extensions
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    checkExistingSession();
  }, []);

  useEffect(() => {
    const hash = window.location.hash;
    if (hash.includes('session_id=')) {
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      handleOAuthCallback(sessionId);
    }
  }, []);

  const checkExistingSession = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/oauth/validate-session`, {
        withCredentials: true
      });
      
      if (response.data.valid) {
        login(response.data.user);
        router.push('/contentry/dashboard');
      }
    } catch (error) {
      console.log('No existing session');
    }
  };

  const handleOAuthCallback = async (sessionId) => {
    setProcessingOAuth(true);
    
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/oauth/session`,
        {},
        {
          headers: { 'X-Session-ID': sessionId },
          withCredentials: true
        }
      );

      window.history.replaceState({}, document.title, window.location.pathname);

      if (response.data.success) {
        login(response.data.user);
        
        toast({
          title: t('auth.login.toasts.welcomeBack'),
          description: `${t('auth.login.toasts.loggedInAs')} ${response.data.user.email}`,
          status: 'success',
          duration: 3000,
        });
        
        router.push('/contentry/dashboard');
      } else if (response.data.error === 'subscription_required') {
        localStorage.setItem('pending_user', JSON.stringify(response.data.user));
        router.push('/contentry/subscription/required');
      }
    } catch (error) {
      console.error('OAuth callback error:', error);
      toast({
        title: t('auth.login.toasts.authFailed'),
        description: getErrorMessage(error, 'Please try again'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setProcessingOAuth(false);
    }
  };

  const handleSendOtp = async () => {
    if (!emailOrPhone) {
      toast({
        title: t('auth.login.toasts.phoneRequired'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/auth/phone/send-otp`, {
        phone: emailOrPhone
      });

      if (response.data.success) {
        setOtpSent(true);
        toast({
          title: t('auth.login.toasts.otpSent'),
          description: t('auth.login.toasts.checkPhone'),
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: t('auth.login.toasts.otpFailed'),
        description: getErrorMessage(error, 'Please try again'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    
    if (!emailOrPhone || !otp) {
      toast({
        title: t('auth.login.toasts.phoneRequired'),
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/auth/phone/verify-otp`, {
        phone: emailOrPhone,
        otp: otp
      });

      if (response.data.success) {
        login(response.data.user);
        
        toast({
          title: t('auth.login.toasts.welcomeBack'),
          status: 'success',
          duration: 2000,
        });
        
        router.push('/contentry/dashboard');
      }
    } catch (error) {
      toast({
        title: t('auth.login.toasts.authFailed'),
        description: getErrorMessage(error, 'Invalid or expired OTP'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    // If phone with OTP mode, use OTP verification
    if (loginMethod === 'phone' && phoneLoginMode === 'otp') {
      return handleVerifyOtp(e);
    }
    
    if (!emailOrPhone || !password) {
      toast({
        title: `${loginMethod === 'email' ? t('auth.login.email') : t('auth.login.phoneNumber')} and ${t('auth.login.password').toLowerCase()} required`,
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(
        `${API}/auth/login`,
        {
          [loginMethod]: emailOrPhone,
          password: password
        },
        { withCredentials: true }
      );

      if (response.data.success) {
        // HttpOnly cookie is automatically set by backend (ARCH-022)
        // We only store non-sensitive user data locally for UI purposes
        // JWT token is securely stored in HttpOnly cookie, not accessible via JS
        
        if (response.data.user?.id) {
          localStorage.setItem('userId', response.data.user.id);
        }
        
        login(response.data.user);
        
        toast({
          title: t('auth.login.toasts.welcomeBack'),
          status: 'success',
          duration: 2000,
        });
        
        router.push('/contentry/dashboard');
      } else if (response.data.must_change_password) {
        // User needs to change their temporary password
        toast({
          title: 'Password Change Required',
          description: response.data.message || 'Please set a new password to continue.',
          status: 'info',
          duration: 4000,
        });
        
        // Redirect to set-password page with user info
        const params = new URLSearchParams({
          email: response.data.email || emailOrPhone,
          name: response.data.full_name || '',
        });
        router.push(`/contentry/auth/set-password?${params.toString()}`);
      } else if (response.data.error === 'subscription_required') {
        localStorage.setItem('pending_user', JSON.stringify(response.data.user));
        router.push('/contentry/subscription/required');
      }
    } catch (error) {
      toast({
        title: t('auth.login.toasts.loginFailed'),
        description: getErrorMessage(error, t('auth.login.toasts.invalidCredentials')),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthLogin = (provider) => {
    const API = getApiUrl();
    
    if (provider === 'google') {
      const redirectUrl = `${window.location.origin}/contentry/auth/login`;
      window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    } else if (provider === 'microsoft' || provider === 'microsoft-sso') {
      // Redirect to Microsoft SSO login
      window.location.href = `${API}/sso/microsoft/login`;
    } else if (provider === 'okta') {
      // Redirect to Okta SSO login
      window.location.href = `${API}/sso/okta/login`;
    } else {
      toast({
        title: `${provider} OAuth`,
        description: `${provider} ${t('auth.login.toasts.comingSoon')}`,
        status: 'info',
        duration: 5000,
      });
    }
  };

  // Handle Enterprise SSO with smart domain lookup
  const handleEnterpriseSso = async () => {
    if (!ssoEmail || !ssoEmail.includes('@')) {
      toast({
        title: 'Invalid Email',
        description: 'Please enter a valid work email address',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setSsoLoading(true);
    try {
      const API = getApiUrl();
      const domain = ssoEmail.split('@')[1].toLowerCase();
      
      // Look up SSO provider for this domain
      const response = await axios.post(`${API}/sso/lookup-domain`, {
        email: ssoEmail,
        domain: domain
      });

      const ssoProvider = response.data.provider;
      const ssoUrl = response.data.login_url;

      if (ssoUrl) {
        // Redirect to the company's SSO provider
        window.location.href = ssoUrl;
      } else if (ssoProvider === 'microsoft' || ssoProvider === 'azure-ad') {
        window.location.href = `${API}/sso/microsoft/login?email=${encodeURIComponent(ssoEmail)}`;
      } else if (ssoProvider === 'okta') {
        window.location.href = `${API}/sso/okta/login?email=${encodeURIComponent(ssoEmail)}`;
      } else if (ssoProvider === 'google-workspace') {
        window.location.href = `${API}/sso/google-workspace/login?email=${encodeURIComponent(ssoEmail)}`;
      } else {
        // No SSO configured for this domain
        toast({
          title: 'SSO Not Configured',
          description: `Enterprise SSO is not set up for ${domain}. Please contact your IT administrator or use another login method.`,
          status: 'info',
          duration: 6000,
        });
      }
    } catch (error) {
      // If domain lookup fails, show helpful message
      const domain = ssoEmail.split('@')[1];
      toast({
        title: 'SSO Lookup Failed',
        description: `Could not find SSO configuration for ${domain}. Your organization may not have SSO enabled yet.`,
        status: 'warning',
        duration: 5000,
      });
    } finally {
      setSsoLoading(false);
    }
  };

  const handleDemoLogin = async (role) => {
    // Demo users configuration matching database
    const DEMO_CONFIGS = {
      // Individual plans (Personal workspace only)
      'free': {
        id: 'free-user',
        email: 'free@demo.com',
        full_name: 'Free User',
        role: 'user',
        subscription: { plan: 'free', status: 'active' },
        password: 'DemoUser!123'
      },
      'starter': {
        id: 'starter-user',
        email: 'starter@demo.com',
        full_name: 'Starter User',
        role: 'user',
        subscription: { plan: 'starter', status: 'active' },
        password: 'DemoUser!123'
      },
      'creator_plan': {
        id: 'creator-user',
        email: 'creator@demo.com',
        full_name: 'Creator User',
        role: 'user',
        subscription: { plan: 'creator', status: 'active' },
        password: 'DemoUser!123'
      },
      'pro': {
        id: 'pro-user',
        email: 'pro@demo.com',
        full_name: 'Pro User',
        role: 'user',
        subscription: { plan: 'pro', status: 'active' },
        password: 'DemoUser!123'
      },
      // Team plan users
      'team_admin': {
        id: 'team-admin',
        email: 'admin@team-demo.com',
        full_name: 'Team Admin',
        role: 'admin',
        enterprise_role: 'admin',
        enterprise_id: 'team-demo-company',
        enterprise_name: 'Team Demo Company',
        subscription: { plan: 'team', status: 'active' },
        password: 'DemoAdmin!123'
      },
      'team_manager': {
        id: 'team-manager',
        email: 'manager@team-demo.com',
        full_name: 'Team Manager',
        role: 'manager',
        enterprise_role: 'manager',
        enterprise_id: 'team-demo-company',
        enterprise_name: 'Team Demo Company',
        subscription: { plan: 'team', status: 'active' },
        password: 'DemoManager!123'
      },
      'team_creator': {
        id: 'team-creator',
        email: 'creator@team-demo.com',
        full_name: 'Team Creator',
        role: 'creator',
        enterprise_role: 'creator',
        enterprise_id: 'team-demo-company',
        enterprise_name: 'Team Demo Company',
        subscription: { plan: 'team', status: 'active' },
        password: 'DemoCreator!123'
      },
      'team_reviewer': {
        id: 'team-reviewer',
        email: 'reviewer@team-demo.com',
        full_name: 'Team Reviewer',
        role: 'reviewer',
        enterprise_role: 'reviewer',
        enterprise_id: 'team-demo-company',
        enterprise_name: 'Team Demo Company',
        subscription: { plan: 'team', status: 'active' },
        password: 'DemoReviewer!123'
      },
      // Business plan users
      'business_admin': {
        id: 'business-admin',
        email: 'admin@business-demo.com',
        full_name: 'Business Admin',
        role: 'admin',
        enterprise_role: 'admin',
        enterprise_id: 'business-demo-company',
        enterprise_name: 'Business Demo Company',
        subscription: { plan: 'business', status: 'active' },
        password: 'DemoAdmin!123'
      },
      'business_manager': {
        id: 'business-manager',
        email: 'manager@business-demo.com',
        full_name: 'Business Manager',
        role: 'manager',
        enterprise_role: 'manager',
        enterprise_id: 'business-demo-company',
        enterprise_name: 'Business Demo Company',
        subscription: { plan: 'business', status: 'active' },
        password: 'DemoManager!123'
      },
      'business_creator': {
        id: 'business-creator',
        email: 'creator@business-demo.com',
        full_name: 'Business Creator',
        role: 'creator',
        enterprise_role: 'creator',
        enterprise_id: 'business-demo-company',
        enterprise_name: 'Business Demo Company',
        subscription: { plan: 'business', status: 'active' },
        password: 'DemoCreator!123'
      },
      'business_reviewer': {
        id: 'business-reviewer',
        email: 'reviewer@business-demo.com',
        full_name: 'Business Reviewer',
        role: 'reviewer',
        enterprise_role: 'reviewer',
        enterprise_id: 'business-demo-company',
        enterprise_name: 'Business Demo Company',
        subscription: { plan: 'business', status: 'active' },
        password: 'DemoReviewer!123'
      },
      // Enterprise plan users
      'enterprise_admin': {
        id: 'enterprise-admin',
        email: 'admin@enterprise-demo.com',
        full_name: 'Enterprise Admin',
        role: 'admin',
        enterprise_role: 'admin',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoAdmin!123'
      },
      'enterprise_manager': {
        id: 'enterprise-manager',
        email: 'manager@enterprise-demo.com',
        full_name: 'Enterprise Manager',
        role: 'manager',
        enterprise_role: 'manager',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoManager!123'
      },
      'enterprise_creator': {
        id: 'enterprise-creator',
        email: 'creator@enterprise-demo.com',
        full_name: 'Enterprise Creator',
        role: 'creator',
        enterprise_role: 'creator',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoCreator!123'
      },
      'enterprise_reviewer': {
        id: 'enterprise-reviewer',
        email: 'reviewer@enterprise-demo.com',
        full_name: 'Enterprise Reviewer',
        role: 'reviewer',
        enterprise_role: 'reviewer',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoReviewer!123'
      },
      // Legacy roles for backward compatibility
      'user': {
        id: 'pro-user',
        email: 'pro@demo.com',
        full_name: 'Pro User',
        role: 'user',
        subscription: { plan: 'pro', status: 'active' },
        password: 'DemoUser!123'
      },
      'admin': {
        id: 'enterprise-admin',
        email: 'admin@enterprise-demo.com',
        full_name: 'Enterprise Admin',
        role: 'admin',
        enterprise_role: 'admin',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoAdmin!123'
      },
      'enterprise': {
        id: 'enterprise-admin',
        email: 'admin@enterprise-demo.com',
        full_name: 'Enterprise Admin',
        role: 'admin',
        enterprise_role: 'admin',
        enterprise_id: 'enterprise-demo-company',
        enterprise_name: 'Enterprise Demo Company',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoAdmin!123'
      },
      'super_admin': {
        id: 'security-test-user-001',
        email: 'test@security.com',
        full_name: 'Super Administrator',
        role: 'super_admin',
        subscription: { plan: 'enterprise', status: 'active' },
        password: 'DemoSuper_admin!123'
      }
    };

    const config = DEMO_CONFIGS[role];
    if (!config) {
      toast({
        title: 'Invalid Demo Role',
        description: `Unknown role: ${role}`,
        status: 'error',
        duration: 3000,
      });
      return;
    }

    const userData = {
      id: config.id,
      full_name: config.full_name,
      email: config.email,
      role: config.role,
      subscription: config.subscription,
      subscription_status: 'active',
      default_homepage: '/contentry/dashboard',
      email_verified: true,
      ...(config.enterprise_id && {
        enterprise_id: config.enterprise_id,
        enterprise_name: config.enterprise_name,
        enterprise_role: config.enterprise_role,
      })
    };
    const demoPassword = config.password;

    try {
      const API = getApiUrl();
      
      // Ensure demo user exists in database with proper password hash
      const createResponse = await axios.post(`${API}/auth/create-demo-user`, userData);
      
      // Get the demo password from response if available
      if (createResponse.data.demo_password) {
        demoPassword = createResponse.data.demo_password;
      }
      
      // Use the full user data from database
      if (createResponse.data.user) {
        userData = {
          ...userData,
          ...createResponse.data.user,
          role: userData.role,
          subscription: userData.subscription,
          subscription_status: createResponse.data.user.subscription_status || userData.subscription?.status || 'active',
          subscription_plan: createResponse.data.user.subscription_plan || userData.subscription?.plan
        };
      }
      
      // Now perform actual login with proper authentication
      try {
        const loginResponse = await axios.post(`${API}/auth/login`, {
          email: userData.email,
          password: demoPassword
        }, { withCredentials: true }); // Enable HttpOnly cookie
        
        if (loginResponse.data.success) {
          // HttpOnly cookie is automatically set by backend (ARCH-022)
          // We only store non-sensitive user data locally
          localStorage.setItem('userId', userData.id);
          
          // Use AuthContext login function
          login(loginResponse.data.user || userData);
          
          // Navigate based on role - use proper routes
          if (role === 'super_admin') {
            window.location.href = '/superadmin/dashboard';
          } else {
            // Get homepage from user data, ensuring it has proper /contentry prefix
            let homepage = userData.default_homepage || '/contentry/content-moderation';
            if (!homepage.startsWith('/contentry') && !homepage.startsWith('/superadmin')) {
              homepage = `/contentry${homepage.startsWith('/') ? '' : '/'}${homepage}`;
            }
            router.push(homepage);
          }
          return;
        }
      } catch (loginError) {
        console.log('Demo login with credentials failed:', loginError.message);
        // ISS-051 FIX: Do not use fallback - require proper authentication
        toast({
          title: 'Demo Login Failed',
          description: 'Unable to authenticate demo user. Please try again or contact support.',
          status: 'error',
          duration: 5000,
        });
        return;
      }
    } catch (error) {
      console.log('Demo user creation failed:', error.message);
      // ISS-051 FIX: Do not use fallback - require proper authentication
      toast({
        title: 'Demo Setup Failed',
        description: 'Unable to create demo user. Please try again.',
        status: 'error',
        duration: 5000,
      });
      return;
    }
  };

  // TechCorp Demo Login - For Right Management demo
  // Password format: Demo{Role}!123 (matches create-demo-user endpoint)
  const handleTechCorpDemoLogin = async (role) => {
    const DEMO_USERS = {
      admin: {
        id: 'sarah-chen',
        email: 'sarah.chen@techcorp-demo.com',
        full_name: 'Sarah Chen',
        password: 'DemoAdmin!123',
        homepage: '/contentry/dashboard',
        enterprise_id: 'techcorp-international',
        enterprise_name: 'TechCorp International',
        enterprise_role: 'admin'
      },
      manager: {
        id: 'michael-rodriguez',
        email: 'michael.rodriguez@techcorp-demo.com',
        full_name: 'Michael Rodriguez',
        password: 'DemoManager!123',
        homepage: '/contentry/content-moderation?tab=scheduled',
        enterprise_id: 'techcorp-international',
        enterprise_name: 'TechCorp International',
        enterprise_role: 'manager'
      },
      creator: {
        id: 'alex-martinez',
        email: 'alex.martinez@techcorp-demo.com',
        full_name: 'Alex Martinez',
        password: 'DemoCreator!123',
        homepage: '/contentry/content-moderation?tab=generate',
        enterprise_id: 'techcorp-international',
        enterprise_name: 'TechCorp International',
        enterprise_role: 'creator'
      },
      reviewer: {
        id: 'robert-kim',
        email: 'robert.kim@techcorp-demo.com',
        full_name: 'Robert Kim',
        password: 'DemoReviewer!123',
        homepage: '/contentry/content-moderation?tab=scheduled',
        enterprise_id: 'techcorp-international',
        enterprise_name: 'TechCorp International',
        enterprise_role: 'reviewer'
      }
    };

    const demoUser = DEMO_USERS[role];
    if (!demoUser) {
      toast({
        title: 'Invalid Demo Role',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      
      // First, ensure the demo user exists with correct password and enterprise data
      // This also resets the password if it was changed and unlocks the account
      try {
        await axios.post(`${API}/auth/create-demo-user`, {
          id: demoUser.id,
          email: demoUser.email,
          full_name: demoUser.full_name,
          role: role,
          enterprise_id: demoUser.enterprise_id,
          enterprise_name: demoUser.enterprise_name,
          enterprise_role: demoUser.enterprise_role,
          subscription: { plan: 'enterprise', status: 'active' }
        });
      } catch (setupError) {
        console.log('Demo user setup (non-blocking):', setupError.message);
        // Continue anyway - user might already exist with correct password
      }
      
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: demoUser.email,
        password: demoUser.password
      }, { withCredentials: true });

      if (loginResponse.data.success) {
        localStorage.setItem('userId', loginResponse.data.user.id);
        login(loginResponse.data.user);
        
        toast({
          title: `Welcome, ${loginResponse.data.user.full_name}!`,
          description: `Logged in as ${role.charAt(0).toUpperCase() + role.slice(1)}`,
          status: 'success',
          duration: 2000,
        });
        
        router.push(demoUser.homepage);
      } else if (loginResponse.data.must_change_password) {
        // User needs to change their temporary password
        toast({
          title: 'Password Change Required',
          description: loginResponse.data.message || 'Please set a new password to continue.',
          status: 'info',
          duration: 4000,
        });
        
        // Redirect to set-password page with user info
        const params = new URLSearchParams({
          email: loginResponse.data.email || demoUser.email,
          name: loginResponse.data.full_name || '',
        });
        router.push(`/contentry/auth/set-password?${params.toString()}`);
      }
    } catch (error) {
      toast({
        title: 'Demo Login Failed',
        description: getErrorMessage(error, 'Unable to login with demo account'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  if (processingOAuth) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={pageBg}>
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" thickness="4px" />
          <Text fontSize="lg" color={textColor}>{t('auth.login.completingAuth')}</Text>
        </VStack>
      </Flex>
    );
  }

  // Show loading state until client is mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={pageBg}>
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.500" thickness="4px" />
          <Text color={textColorSecondary}>{t('auth.login.loading')}</Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <Flex minH="100vh" align="center" justify="center" bg={pageBg} py={{ base: 4, md: 6 }} position="relative">
      {/* Language Selector - Top Right Corner */}
      <Box position="absolute" top={4} right={4} zIndex={10}>
        <LanguageSelector />
      </Box>
      
      <Box
        maxW="420px"
        w="full"
        bg={bgColor}
        boxShadow="xl"
        rounded="lg"
        p={{ base: 6, md: 7 }}
        borderWidth="1px"
        borderColor={borderColor}
        my="auto"
      >
        <VStack spacing={{ base: 4, md: 5 }} align="stretch">
          {/* Logo & Title - No background, logo adapts to color mode */}
          <VStack spacing={2}>
            <ContentryLogo size="sm" />
            <Text fontSize="xs" color={textColorSecondary} textAlign="center">
              {t('auth.login.title')}
            </Text>
          </VStack>

          {/* Login Form */}
          <form onSubmit={handleLogin}>
            <VStack spacing={3}>
              {/* Email/Phone Tabs */}
              <Tabs
                variant="soft-rounded"
                colorScheme="brand"
                w="full"
                onChange={(index) => setLoginMethod(index === 0 ? 'email' : 'phone')}
                suppressHydrationWarning
              >
                <TabList mb={3} suppressHydrationWarning>
                  <Tab flex={1} fontSize="sm" py={2} color={tabUnselectedColor} _selected={{ color: 'white', bg: 'brand.500' }}>{t('auth.login.emailTab')}</Tab>
                  <Tab flex={1} fontSize="sm" py={2} color={tabUnselectedColor} _selected={{ color: 'white', bg: 'brand.500' }}>{t('auth.login.phoneTab')}</Tab>
                </TabList>
              </Tabs>

              <FormControl isRequired suppressHydrationWarning>
                <FormLabel fontSize="xs" color={textColor} fontWeight="600">
                  {loginMethod === 'email' ? t('auth.login.email') : t('auth.login.phoneNumber')}
                </FormLabel>
                <Input
                  type={loginMethod === 'email' ? 'email' : 'tel'}
                  placeholder={loginMethod === 'email' ? t('auth.login.emailPlaceholder') : t('auth.login.phonePlaceholder')}
                  value={emailOrPhone}
                  onChange={(e) => setEmailOrPhone(e.target.value)}
                  size="md"
                  bg={inputBg}
                  borderColor={borderColor}
                  _placeholder={{ color: placeholderColor }}
                  color={textColor}
                  suppressHydrationWarning
                />
              </FormControl>

              {/* Password or OTP Input */}
              {loginMethod === 'phone' && !otpSent ? (
                <VStack spacing={1.5} w="full" align="stretch">
                  <Text fontSize="xs" color={textColor} fontWeight="600">{t('auth.login.loginWith')}</Text>
                  <HStack spacing={2}>
                    <Button
                      flex={1}
                      size="sm"
                      variant={phoneLoginMode === 'password' ? 'solid' : 'outline'}
                      colorScheme="brand"
                      onClick={() => setPhoneLoginMode('password')}
                    >
                      {t('auth.login.password')}
                    </Button>
                    <Button
                      flex={1}
                      size="sm"
                      variant={phoneLoginMode === 'otp' ? 'solid' : 'outline'}
                      colorScheme="brand"
                      onClick={() => setPhoneLoginMode('otp')}
                    >
                      {t('auth.login.otp')}
                    </Button>
                  </HStack>
                </VStack>
              ) : null}

              {loginMethod === 'phone' && phoneLoginMode === 'otp' && !otpSent ? (
                <Button
                  w="full"
                  colorScheme="brand"
                  size="md"
                  onClick={handleSendOtp}
                  isLoading={loading}
                >
                  {t('auth.login.sendOtp')}
                </Button>
              ) : loginMethod === 'phone' && phoneLoginMode === 'otp' && otpSent ? (
                <FormControl isRequired suppressHydrationWarning>
                  <FormLabel fontSize="xs" color={textColor} fontWeight="600">{t('auth.login.enterOtp')}</FormLabel>
                  <Input
                    type="text"
                    placeholder={t('auth.login.otpPlaceholder')}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    size="md"
                    bg={inputBg}
                    borderColor={borderColor}
                    _placeholder={{ color: placeholderColor }}
                    color={textColor}
                    maxLength={6}
                    suppressHydrationWarning
                  />
                  <Text fontSize="2xs" color={textColorSecondary} mt={1}>
                    {t('auth.login.didntReceive')} <ChakraLink color={linkColor} onClick={() => { setOtpSent(false); handleSendOtp(); }}>{t('auth.login.resendOtp')}</ChakraLink>
                  </Text>
                </FormControl>
              ) : (
                <FormControl isRequired suppressHydrationWarning>
                  <FormLabel fontSize="xs" color={textColor} fontWeight="600">{t('auth.login.password')}</FormLabel>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={t('auth.login.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    suppressHydrationWarning
                    size="md"
                    bg={inputBg}
                    borderColor={borderColor}
                    _placeholder={{ color: placeholderColor }}
                    color={textColor}
                  />
                </FormControl>
              )}

              <VStack spacing={2.5} w="full" align="stretch">
                <Flex w="full" justify="space-between" align="center">
                  <Checkbox
                    isChecked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    colorScheme="brand"
                    size="sm"
                  >
                    <Text fontSize="xs" color={textColor}>{t('auth.login.rememberMe')}</Text>
                  </Checkbox>
                  <ChakraLink
                    href="/contentry/auth/forgot-password"
                    color={linkColor}
                    fontSize="xs"
                    fontWeight="500"
                  >
                    {t('auth.login.forgotPassword')}
                  </ChakraLink>
                </Flex>
                
                <Text fontSize="xs" color={textColorSecondary} textAlign="center">
                  {t('auth.login.dontHaveAccount')}{' '}
                  <ChakraLink
                    href="/contentry/auth/signup"
                    color={linkColor}
                    fontWeight="600"
                  >
                    {t('auth.login.signUp')}
                  </ChakraLink>
                </Text>
              </VStack>

              <Button
                type="submit"
                colorScheme="brand"
                size="md"
                w="full"
                isLoading={loading}
              >
                {t('auth.login.logIn')}
              </Button>
            </VStack>
          </form>

          {/* Enterprise SSO Section - OLD REMOVED */}
          
          {/* Divider */}
          <HStack spacing={3} pt={1}>
            <Box h="1px" flex={1} bg={borderColor} />
            <Text fontSize="xs" color={textColorSecondary} whiteSpace="nowrap">
              {t('auth.login.orContinueWith')}
            </Text>
            <Box h="1px" flex={1} bg={borderColor} />
          </HStack>

          {/* Social Logins - The Big Three */}
          <VStack spacing={2}>
            <Button
              w="full"
              bg={oauthBtnBg}
              color={oauthBtnColor}
              border="1px solid"
              borderColor={borderColor}
              leftIcon={<GoogleLogo size={18} />}
              onClick={() => handleOAuthLogin('google')}
              size="md"
              fontWeight="500"
              _hover={{ bg: hoverBg, borderColor: oauthBtnHoverBorderColor }}
            >
              {t('auth.login.continueWithGoogle')}
            </Button>
            
            <Button
              w="full"
              bg={oauthBtnBg}
              color={oauthBtnColor}
              border="1px solid"
              borderColor={borderColor}
              leftIcon={<Box color={appleIconColor}><AppleLogo size={18} /></Box>}
              onClick={() => handleOAuthLogin('apple')}
              size="md"
              fontWeight="500"
              _hover={{ bg: hoverBg, borderColor: oauthBtnHoverBorderColor }}
            >
              {t('auth.login.continueWithApple')}
            </Button>
            
            <Button
              w="full"
              bg={oauthBtnBg}
              color={oauthBtnColor}
              border="1px solid"
              borderColor={borderColor}
              leftIcon={<MicrosoftLogo size={18} />}
              onClick={() => handleOAuthLogin('microsoft')}
              size="md"
              fontWeight="500"
              _hover={{ bg: hoverBg, borderColor: oauthBtnHoverBorderColor }}
            >
              {t('auth.login.continueWithMicrosoft')}
            </Button>
            
            <Button
              w="full"
              bg={oauthBtnBg}
              color={oauthBtnColor}
              border="1px solid"
              borderColor={borderColor}
              leftIcon={<SlackLogo size={18} />}
              onClick={() => handleOAuthLogin('slack')}
              size="md"
              fontWeight="500"
              _hover={{ bg: hoverBg, borderColor: oauthBtnHoverBorderColor }}
            >
              {t('auth.login.continueWithSlack')}
            </Button>
          </VStack>

          {/* Organizational Login - Work or School Account */}
          <VStack spacing={2} pt={2}>
            <HStack spacing={3} w="full">
              <Box h="1px" flex={1} bg={borderColor} />
              <Text fontSize="xs" color={textColorSecondary} whiteSpace="nowrap">
                {t('common.or', 'OR')}
              </Text>
              <Box h="1px" flex={1} bg={borderColor} />
            </HStack>
            <Button
              w="full"
              variant="outline"
              colorScheme="blue"
              leftIcon={<Icon as={FaBuilding} />}
              onClick={() => setShowSsoModal(true)}
              size="md"
              fontWeight="500"
            >
              {t('auth.login.continueWithWorkAccount', 'Continue with Work or School Account')}
            </Button>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center">
              {t('auth.login.ssoDescription', 'For organizations, universities, and schools using SSO')}
            </Text>
          </VStack>

          {/* ============ DEMO LOGIN SECTION ============ */}
          {/* Individual Plans Demo */}
          <VStack spacing={2} pt={3} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" fontWeight="600">
              Individual Plans (Personal Workspace):
            </Text>
            <HStack spacing={2} w="full" flexWrap="wrap" justify="center">
              <Button size="xs" variant="outline" colorScheme="gray" onClick={() => handleDemoLogin('free')}>
                Free
              </Button>
              <Button size="xs" variant="outline" colorScheme="green" onClick={() => handleDemoLogin('starter')}>
                Starter
              </Button>
              <Button size="xs" variant="outline" colorScheme="blue" onClick={() => handleDemoLogin('creator_plan')}>
                Creator
              </Button>
              <Button size="xs" variant="outline" colorScheme="purple" onClick={() => handleDemoLogin('pro')}>
                Pro
              </Button>
            </HStack>
          </VStack>

          {/* Team Plan Demo */}
          <VStack spacing={2} pt={2} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" fontWeight="600">
              Team Plan (Personal + Company Workspace):
            </Text>
            <HStack spacing={2} w="full" flexWrap="wrap" justify="center">
              <Button size="xs" variant="outline" colorScheme="teal" onClick={() => handleDemoLogin('team_admin')}>
                Admin
              </Button>
              <Button size="xs" variant="outline" colorScheme="teal" onClick={() => handleDemoLogin('team_manager')}>
                Manager
              </Button>
              <Button size="xs" variant="outline" colorScheme="teal" onClick={() => handleDemoLogin('team_creator')}>
                Creator
              </Button>
              <Button size="xs" variant="outline" colorScheme="teal" onClick={() => handleDemoLogin('team_reviewer')}>
                Reviewer
              </Button>
            </HStack>
          </VStack>

          {/* Business Plan Demo */}
          <VStack spacing={2} pt={2} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" fontWeight="600">
              Business Plan (Personal + Company Workspace):
            </Text>
            <HStack spacing={2} w="full" flexWrap="wrap" justify="center">
              <Button size="xs" variant="outline" colorScheme="cyan" onClick={() => handleDemoLogin('business_admin')}>
                Admin
              </Button>
              <Button size="xs" variant="outline" colorScheme="cyan" onClick={() => handleDemoLogin('business_manager')}>
                Manager
              </Button>
              <Button size="xs" variant="outline" colorScheme="cyan" onClick={() => handleDemoLogin('business_creator')}>
                Creator
              </Button>
              <Button size="xs" variant="outline" colorScheme="cyan" onClick={() => handleDemoLogin('business_reviewer')}>
                Reviewer
              </Button>
            </HStack>
          </VStack>

          {/* Enterprise Plan Demo */}
          <VStack spacing={2} pt={2} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" fontWeight="600">
              Enterprise Plan (Personal + Company Workspace):
            </Text>
            <HStack spacing={2} w="full" flexWrap="wrap" justify="center">
              <Button size="xs" variant="outline" colorScheme="purple" onClick={() => handleDemoLogin('enterprise_admin')}>
                Admin
              </Button>
              <Button size="xs" variant="outline" colorScheme="purple" onClick={() => handleDemoLogin('enterprise_manager')}>
                Manager
              </Button>
              <Button size="xs" variant="outline" colorScheme="purple" onClick={() => handleDemoLogin('enterprise_creator')}>
                Creator
              </Button>
              <Button size="xs" variant="outline" colorScheme="purple" onClick={() => handleDemoLogin('enterprise_reviewer')}>
                Reviewer
              </Button>
            </HStack>
          </VStack>

          {/* Super Admin Access */}
          <VStack spacing={2} pt={2} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" fontWeight="600">
              Platform Admin:
            </Text>
            <Button size="xs" variant="outline" colorScheme="red" onClick={() => handleDemoLogin('super_admin')}>
              Super Admin
            </Button>
          </VStack>

          {/* Footer Links */}
          <VStack spacing={1} pt={2}>
            <Text fontSize="2xs" color={textColorSecondary} textAlign="center" pt={2}>
              {t('auth.login.oneAccountForAll')}
            </Text>
            
            <HStack spacing={3} fontSize="2xs" color={textColorSecondary}>
              <ChakraLink href="/contentry/privacy" color={linkColor}>{t('auth.signup.privacyPolicy')}</ChakraLink>
              <Text>•</Text>
              <ChakraLink href="/contentry/terms" color={linkColor}>{t('auth.signup.termsOfService')}</ChakraLink>
            </HStack>
          </VStack>
        </VStack>
      </Box>

      {/* Work or School Account Modal - Smart Domain Lookup */}
      <Modal isOpen={showSsoModal} onClose={() => setShowSsoModal(false)} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <HStack>
              <Icon as={FaBuilding} color="brand.500" />
              <Text>{t('auth.login.signInWithOrganization')}</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color={textColorSecondary}>
                {t('auth.login.enterWorkEmailDescription', "Enter your work or school email address. We'll automatically redirect you to your organization's login page.")}
              </Text>
              
              <FormControl>
                <FormLabel fontSize="sm">{t('auth.login.workSchoolEmail', 'Work or School Email')}</FormLabel>
                <InputGroup>
                  <InputLeftElement pointerEvents="none">
                    <Icon as={FaEnvelope} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    type="email"
                    placeholder={t('auth.login.workEmailPlaceholder', 'you@organization.com')}
                    value={ssoEmail}
                    onChange={(e) => setSsoEmail(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleEnterpriseSso()}
                  />
                </InputGroup>
              </FormControl>

              <Text fontSize="xs" color={textColorSecondary}>
                {t('auth.login.ssoProvidersInfo', 'Works with Microsoft Azure AD, Okta, Google Workspace, and other identity providers used by companies, universities, and schools.')}
              </Text>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setShowSsoModal(false)}>
              {t('common.cancel')}
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleEnterpriseSso}
              isLoading={ssoLoading}
              isDisabled={!ssoEmail || !ssoEmail.includes('@')}
            >
              {t('common.continue')}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Flex>
  );
}

// Export with Suspense wrapper
export default function LoginPage() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <LoginPageContent />
    </Suspense>
  );
}
