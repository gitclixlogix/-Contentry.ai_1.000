'use client';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
  useColorModeValue,
  Icon,
  Container,
  Spinner,
  Progress,
} from '@chakra-ui/react';
import { FaCheckCircle } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

function SubscriptionSuccessContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('checking'); // checking, success, failed
  const [message, setMessage] = useState(t('common.verifyingPayment'));

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      verifyPayment(sessionId);
    } else {
      setStatus('failed');
      setMessage(t('errors.notFound'));
    }
  }, [searchParams, t]);

  const verifyPayment = async (sessionId) => {
    try {
      const API = getApiUrl();
      
      // Poll for payment status (max 10 attempts)
      let attempts = 0;
      const maxAttempts = 10;
      
      const checkStatus = async () => {
        attempts++;
        
        try {
          const response = await axios.get(
            `${API}/subscriptions/checkout/status/${sessionId}`
          );
          
          if (response.data.payment_status === 'paid') {
            setStatus('success');
            setMessage(t('subscription.success.subtitle'));
            
            // Wait 2 seconds then redirect
            setTimeout(() => {
              router.push('/contentry/auth/login');
            }, 2000);
          } else if (attempts < maxAttempts) {
            // Try again in 1 second
            setTimeout(checkStatus, 1000);
          } else {
            setStatus('failed');
            setMessage(t('errors.networkError'));
          }
        } catch (error) {
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 1000);
          } else {
            setStatus('failed');
            setMessage(t('errors.networkError'));
          }
        }
      };
      
      checkStatus();
    } catch (error) {
      console.error('Payment verification error:', error);
      setStatus('failed');
      setMessage(t('errors.somethingWentWrong'));
    }
  };

  return (
    <Flex minH="100vh" align="center" justify="center" bg={bgColor}>
      <Container maxW="600px">
        <Box
          bg={cardBg}
          boxShadow="xl"
          rounded="2xl"
          p={10}
          textAlign="center"
        >
          <VStack spacing={6}>
            {status === 'checking' && (
              <>
                <Spinner size="xl" color="brand.500" thickness="4px" />
                <Heading size="lg" color={textColor}>
                  {t('common.processing')}
                </Heading>
                <Text color="gray.500">{message}</Text>
                <Progress size="xs" isIndeterminate colorScheme="brand" w="full" />
              </>
            )}

            {status === 'success' && (
              <>
                <Icon as={FaCheckCircle} boxSize={20} color="green.500" />
                <Heading size="xl" color={textColor}>
                  {t('subscription.success.title')}
                </Heading>
                <Text fontSize="lg" color="gray.500">
                  {t('subscription.success.subtitle')}
                </Text>
                <Text fontSize="md" color={textColor}>
                  {message}
                </Text>
              </>
            )}

            {status === 'failed' && (
              <>
                <Icon as={FaCheckCircle} boxSize={20} color="red.500" />
                <Heading size="xl" color={textColor}>
                  {t('errors.somethingWentWrong')}
                </Heading>
                <Text fontSize="lg" color="gray.500">
                  {message}
                </Text>
                <VStack spacing={3} w="full" pt={4}>
                  <Button
                    colorScheme="brand"
                    size="lg"
                    w="full"
                    onClick={() => router.push('/contentry/subscription/plans')}
                  >
                    {t('errors.tryAgain')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="lg"
                    w="full"
                    onClick={() => router.push('/contentry/auth/login')}
                  >
                    {t('common.goBack')}
                  </Button>
                </VStack>
              </>
            )}
          </VStack>
        </Box>
      </Container>
    </Flex>
  );
}

export default function SubscriptionSuccessPage() {
  return (
    <Suspense fallback={
      <Flex minH="100vh" align="center" justify="center">
        <Spinner size="xl" />
      </Flex>
    }>
      <SubscriptionSuccessContent />
    </Suspense>
  );
}
