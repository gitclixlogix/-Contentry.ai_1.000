'use client';
import { useTranslation } from 'react-i18next';
import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Spinner,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

function PaymentSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('checking');
  const [message, setMessage] = useState('Verifying your payment...');
  const [attempts, setAttempts] = useState(0);

  const textColor = useColorModeValue('navy.700', 'white');
  const cardBg = useColorModeValue('white', 'gray.800');

  const pollPaymentStatus = async (sessionId, attemptCount = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attemptCount >= maxAttempts) {
      setStatus('timeout');
      setMessage('Payment verification timed out. Please check your email for confirmation or contact support.');
      return;
    }

    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/payments/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid') {
        setStatus('success');
        setMessage('Payment successful! Your subscription is now active.');
        return;
      } else if (response.data.status === 'expired') {
        setStatus('error');
        setMessage('Payment session expired. Please try again.');
        return;
      }

      // Continue polling
      setAttempts(attemptCount + 1);
      setTimeout(() => pollPaymentStatus(sessionId, attemptCount + 1), pollInterval);
      
    } catch (error) {
      console.error('Error checking payment status:', error);
      setStatus('error');
      setMessage('Error verifying payment. Please contact support.');
    }
  };

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (!sessionId) {
      setStatus('error');
      setMessage('No payment session found');
      return;
    }

    pollPaymentStatus(sessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Box
        maxW="600px"
        mx="auto"
        bg={cardBg}
        p={8}
        borderRadius="lg"
        boxShadow="xl"
      >
        <VStack spacing={6} align="center">
          {status === 'checking' && (
            <>
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Heading size="lg" color={textColor}>
                Processing Payment
              </Heading>
              <Text color="gray.600" textAlign="center">
                {message}
              </Text>
              <Text fontSize="sm" color="gray.500">
                Attempt {attempts + 1} of 5...
              </Text>
            </>
          )}

          {status === 'success' && (
            <>
              <Icon as={FaCheckCircle} fontSize="6xl" color="green.500" />
              <Heading size="lg" color={textColor}>
                Payment Successful!
              </Heading>
              <Text color="gray.600" textAlign="center">
                {message}
              </Text>
              <Button
                colorScheme="brand"
                size="sm"
                onClick={() => router.push('/contentry/dashboard')}
              >
                Go to Dashboard
              </Button>
            </>
          )}

          {(status === 'error' || status === 'timeout') && (
            <>
              <Icon as={FaTimesCircle} fontSize="6xl" color="red.500" />
              <Heading size="lg" color={textColor}>
                Payment {status === 'timeout' ? 'Verification Timeout' : 'Failed'}
              </Heading>
              <Text color="gray.600" textAlign="center">
                {message}
              </Text>
              <Button
                colorScheme="brand"
                size="sm"
                onClick={() => router.push('/contentry/subscription')}
              >
                Return to Subscriptions
              </Button>
            </>
          )}
        </VStack>
      </Box>
    </Box>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
        <Box maxW="600px" mx="auto" p={8}>
          <VStack spacing={6} align="center">
            <Spinner size="xl" color="brand.500" thickness="4px" />
            <Text>Loading...</Text>
          </VStack>
        </Box>
      </Box>
    }>
      <PaymentSuccessContent />
    </Suspense>
  );
}
