'use client';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Flex,
  Heading,
  Text,
  Spinner,
  VStack,
  Icon,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

function VerifyEmailContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');
  
  const token = searchParams.get('token');
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const bgGradient = 'linear(to-br, brand.500, blue.600)';

  // Helper function to extract error message from response
  const getErrorMessage = (error, defaultMessage) => {
    const detail = error?.response?.data?.detail;
    if (!detail) return defaultMessage || t('errors.somethingWentWrong');
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(err => err.msg || JSON.stringify(err)).join(', ');
    }
    if (typeof detail === 'object') {
      return detail.error || detail.msg || detail.message || defaultMessage;
    }
    return defaultMessage;
  };

  const verifyEmail = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/auth/verify-email`, { token });
      
      setStatus('success');
      setMessage(t('auth.emailVerified'));
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/contentry/auth/login');
      }, 3000);
    } catch (error) {
      setStatus('error');
      setMessage(getErrorMessage(error, t('auth.verificationFailed')));
    }
  };

  useEffect(() => {
    if (token) {
      verifyEmail();
    } else {
      setStatus('error');
      setMessage(t('auth.noToken'));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <Flex
      minH="100vh"
      align="center"
      justify="center"
      bgGradient={bgGradient}
      p={8}
    >
      <Box
        maxW="500px"
        w="full"
        bg={cardBg}
        borderRadius="2xl"
        p={12}
        boxShadow="2xl"
        textAlign="center"
      >
        <VStack spacing={6}>
          {status === 'verifying' && (
            <>
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Heading size="lg">{t('common.verifyingEmail')}</Heading>
              <Text color="gray.600">{t('common.pleaseWait')}</Text>
            </>
          )}

          {status === 'success' && (
            <>
              <Icon as={FaCheckCircle} boxSize={20} color="green.500" />
              <Heading size="lg" color="green.600">{t('auth.emailVerifiedTitle')}</Heading>
              <Text color="gray.600">{message}</Text>
              <Text fontSize="sm" color="gray.500">{t('auth.redirectingToLogin')}</Text>
            </>
          )}

          {status === 'error' && (
            <>
              <Icon as={FaTimesCircle} boxSize={20} color="red.500" />
              <Heading size="lg" color="red.600">{t('auth.verificationFailed')}</Heading>
              <Text color="gray.600">{message}</Text>
              <Button
                colorScheme="brand"
                onClick={() => router.push('/contentry/auth/login')}
                mt={4}
              >
                {t('auth.goToLogin')}
              </Button>
            </>
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <Flex minH="100vh" align="center" justify="center" bg="gray.50">
        <Spinner size="xl" />
      </Flex>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
