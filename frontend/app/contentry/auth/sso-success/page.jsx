'use client';
import { useTranslation } from 'react-i18next';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Flex,
  VStack,
  Text,
  Spinner,
  useColorModeValue,
  useToast,
  Center,
} from '@chakra-ui/react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import ContentryLogo from '@/components/branding/ContentryLogo';

// Loading fallback
const PageLoadingFallback = () => (
  <Center minH="100vh">
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Center>
);

function SSOSuccessPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Completing authentication...');

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');

  useEffect(() => {
    const processSSO = async () => {
      const userId = searchParams.get('user_id');
      const email = searchParams.get('email');
      const error = searchParams.get('error');

      if (error) {
        setStatus('error');
        setMessage(decodeURIComponent(error));
        toast({
          title: 'Authentication Failed',
          description: decodeURIComponent(error),
          status: 'error',
          duration: 5000,
        });
        setTimeout(() => router.push('/contentry/auth/login'), 3000);
        return;
      }

      if (!userId || !email) {
        setStatus('error');
        setMessage('Invalid authentication response');
        toast({
          title: 'Authentication Failed',
          description: 'Invalid authentication response from SSO provider',
          status: 'error',
          duration: 5000,
        });
        setTimeout(() => router.push('/contentry/auth/login'), 3000);
        return;
      }

      try {
        setMessage('Verifying your account...');
        
        // Fetch the full user data from the backend
        const API = getApiUrl();
        const response = await axios.get(`${API}/users/${userId}`, {
          headers: {
            'X-User-ID': userId
          }
        });

        if (response.data) {
          const userData = {
            id: response.data.id,
            email: response.data.email,
            full_name: response.data.full_name,
            role: response.data.role || 'user',
            enterprise_id: response.data.enterprise_id,
            enterprise_role: response.data.enterprise_role,
            subscription_status: response.data.subscription_status || 'active',
            subscription_plan: response.data.subscription_plan,
            email_verified: true,
            sso_provider: response.data.sso_provider,
          };

          // Store user in localStorage
          localStorage.setItem('contentry_user', JSON.stringify(userData));

          setStatus('success');
          setMessage('Login successful! Redirecting...');

          toast({
            title: 'Welcome!',
            description: `Logged in as ${userData.email}`,
            status: 'success',
            duration: 3000,
          });

          // Determine where to redirect based on user role
          let redirectPath = '/contentry/dashboard';
          if (userData.role === 'admin') {
            redirectPath = '/contentry/admin';
          } else if (userData.enterprise_role === 'enterprise_admin') {
            redirectPath = '/contentry/enterprise/dashboard';
          } else if (userData.enterprise_role === 'manager') {
            redirectPath = '/contentry/manager/dashboard';
          }

          setTimeout(() => router.push(redirectPath), 1500);
        }
      } catch (error) {
        console.error('SSO verification error:', error);
        
        // If user fetch fails, create a basic user object from URL params
        const basicUserData = {
          id: userId,
          email: email,
          full_name: email.split('@')[0],
          role: 'user',
          subscription_status: 'active',
          email_verified: true,
          sso_provider: 'microsoft',
        };

        localStorage.setItem('contentry_user', JSON.stringify(basicUserData));

        setStatus('success');
        setMessage('Login successful! Redirecting...');

        toast({
          title: 'Welcome!',
          description: `Logged in as ${email}`,
          status: 'success',
          duration: 3000,
        });

        setTimeout(() => router.push('/contentry/dashboard'), 1500);
      }
    };

    processSSO();
  }, [searchParams, router, toast]);

  return (
    <Flex minH="100vh" align="center" justify="center" bg={bgColor}>
      <Box
        maxW="400px"
        w="full"
        bg={cardBg}
        boxShadow="xl"
        rounded="lg"
        p={8}
        textAlign="center"
      >
        <VStack spacing={6}>
          <ContentryLogo size="sm" />
          
          {status === 'processing' && (
            <>
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text fontSize="lg" color={textColor} fontWeight="500">
                {message}
              </Text>
              <Text fontSize="sm" color={textColorSecondary}>
                Please wait while we complete your sign-in...
              </Text>
            </>
          )}

          {status === 'success' && (
            <>
              <Box fontSize="4xl">✅</Box>
              <Text fontSize="lg" color={textColor} fontWeight="500">
                {message}
              </Text>
            </>
          )}

          {status === 'error' && (
            <>
              <Box fontSize="4xl">❌</Box>
              <Text fontSize="lg" color="red.500" fontWeight="500">
                Authentication Failed
              </Text>
              <Text fontSize="sm" color={textColorSecondary}>
                {message}
              </Text>
              <Text fontSize="xs" color={textColorSecondary}>
                Redirecting to login page...
              </Text>
            </>
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

// Export with Suspense wrapper
export default function SSOSuccessPage() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <SSOSuccessPageContent />
    </Suspense>
  );
}
