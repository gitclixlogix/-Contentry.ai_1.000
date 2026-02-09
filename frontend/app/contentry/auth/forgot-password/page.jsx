'use client';
import { useState } from 'react';
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
  useColorModeValue,
  useToast,
  Link as ChakraLink,
  Icon,
} from '@chakra-ui/react';
import { FaArrowLeft, FaCheckCircle } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import LanguageSelector from '@/components/LanguageSelector';
import ContentryLogo from '@/components/branding/ContentryLogo';

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const textColor = useColorModeValue('gray.800', 'white');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Helper function to extract error message from response
  const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
    const detail = error?.response?.data?.detail;
    if (!detail) return defaultMessage;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(err => err.msg || JSON.stringify(err)).join(', ');
    }
    if (typeof detail === 'object') {
      return detail.error || detail.msg || detail.message || defaultMessage;
    }
    return defaultMessage;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email) {
      toast({
        title: t('auth.forgotPassword.email') + ' required',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/auth/forgot-password`, { email });
      
      setSent(true);
      toast({
        title: t('auth.forgotPassword.toasts.resetLinkSent'),
        description: t('auth.forgotPassword.toasts.checkEmail'),
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: t('auth.forgotPassword.toasts.sendFailed'),
        description: getErrorMessage(error, 'Failed to send reset link'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex minH="100vh" align="center" justify="center" bg={useColorModeValue('gray.50', 'gray.900')} position="relative">
      {/* Language Selector - Top Right Corner */}
      <Box position="absolute" top={4} right={4} zIndex={10}>
        <LanguageSelector />
      </Box>
      
      <Box
        maxW="400px"
        w="full"
        bg={bgColor}
        boxShadow="xl"
        rounded="lg"
        p={8}
        borderWidth="1px"
        borderColor={borderColor}
      >
        {!sent ? (
          <VStack spacing={6} align="stretch">
            <VStack spacing={2}>
              <ContentryLogo size="sm" />
              <Heading size="lg" color={textColor} textAlign="center">
                {t('auth.forgotPassword.title')}
              </Heading>
              <Text fontSize="sm" color="gray.500" textAlign="center">
                {t('auth.forgotPassword.subtitle')}
              </Text>
            </VStack>

            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel fontSize="sm" color={textColor}>{t('auth.forgotPassword.email')}</FormLabel>
                  <Input
                    type="email"
                    placeholder={t('auth.forgotPassword.emailPlaceholder')}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    size="lg"
                    borderColor={borderColor}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="brand"
                  size="lg"
                  w="full"
                  isLoading={loading}
                  loadingText={t('auth.forgotPassword.sending')}
                >
                  {t('auth.forgotPassword.sendResetLink')}
                </Button>

                <Button
                  variant="ghost"
                  size="lg"
                  w="full"
                  leftIcon={<Icon as={FaArrowLeft} />}
                  onClick={() => router.push('/contentry/auth/login')}
                >
                  {t('auth.forgotPassword.backToLogin')}
                </Button>
              </VStack>
            </form>
          </VStack>
        ) : (
          <VStack spacing={6} align="center">
            <Icon as={FaCheckCircle} boxSize={16} color="green.500" />
            <Heading size="lg" color={textColor} textAlign="center">
              {t('auth.forgotPassword.toasts.checkEmail')}
            </Heading>
            <Text fontSize="sm" color="gray.500" textAlign="center">
              We&apos;ve sent a password reset link to <strong>{email}</strong>
            </Text>
            <Text fontSize="sm" color="gray.500" textAlign="center">
              The link will expire in 1 hour for security reasons.
            </Text>
            <Button
              colorScheme="brand"
              size="lg"
              w="full"
              onClick={() => router.push('/contentry/auth/login')}
            >
              {t('auth.forgotPassword.backToLogin')}
            </Button>
            <Text fontSize="xs" color="gray.500" textAlign="center">
              Didn&apos;t receive the email?{' '}
              <ChakraLink color="brand.500" onClick={() => setSent(false)}>
                Try again
              </ChakraLink>
            </Text>
          </VStack>
        )}
      </Box>
    </Flex>
  );
}
