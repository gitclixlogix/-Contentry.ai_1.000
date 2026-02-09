'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  Icon,
  InputGroup,
  InputRightElement,
  IconButton,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { FaCheckCircle, FaEye, FaEyeSlash, FaCheck, FaTimes } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);

  const textColor = useColorModeValue('gray.800', 'white');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const pageBgColor = useColorModeValue('gray.50', 'gray.900');

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

  useEffect(() => {
    const resetToken = searchParams.get('token');
    if (resetToken) {
      setToken(resetToken);
      validateToken(resetToken);
    } else {
      setValidating(false);
      toast({
        title: 'Invalid reset link',
        description: 'No token found in URL',
        status: 'error',
        duration: 5000,
      });
    }
  }, [searchParams]);

  const validateToken = async (resetToken) => {
    try {
      const API = getApiUrl();
      await axios.post(`${API}/auth/validate-reset-token`, { token: resetToken });
      setTokenValid(true);
    } catch (error) {
      toast({
        title: 'Invalid or expired link',
        description: 'This password reset link has expired or is invalid',
        status: 'error',
        duration: 5000,
      });
      setTokenValid(false);
    } finally {
      setValidating(false);
    }
  };

  const passwordRequirements = [
    { label: 'At least 8 characters', test: (pwd) => pwd.length >= 8 },
    { label: 'Contains uppercase letter', test: (pwd) => /[A-Z]/.test(pwd) },
    { label: 'Contains lowercase letter', test: (pwd) => /[a-z]/.test(pwd) },
    { label: 'Contains number', test: (pwd) => /[0-9]/.test(pwd) },
  ];

  const isPasswordValid = passwordRequirements.every(req => req.test(newPassword));
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isPasswordValid) {
      toast({
        title: 'Password requirements not met',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!passwordsMatch) {
      toast({
        title: 'Passwords do not match',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: newPassword
      });
      
      setSuccess(true);
      toast({
        title: 'Password reset successful!',
        description: 'You can now log in with your new password',
        status: 'success',
        duration: 5000,
      });
      
      setTimeout(() => {
        router.push('/contentry/auth/login');
      }, 2000);
    } catch (error) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to reset password'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  if (validating) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={pageBgColor}>
        <Text>Validating reset link...</Text>
      </Flex>
    );
  }

  if (!tokenValid) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={pageBgColor}>
        <Box
          maxW="400px"
          w="full"
          bg={bgColor}
          boxShadow="xl"
          rounded="lg"
          p={8}
          borderWidth="1px"
          borderColor={borderColor}
          textAlign="center"
        >
          <VStack spacing={4}>
            <Icon as={FaTimes} boxSize={16} color="red.500" />
            <Heading size="lg" color={textColor}>Invalid Reset Link</Heading>
            <Text color="gray.500">
              This password reset link has expired or is invalid.
            </Text>
            <Button
              colorScheme="brand"
              onClick={() => router.push('/contentry/auth/forgot-password')}
            >
              Request New Link
            </Button>
          </VStack>
        </Box>
      </Flex>
    );
  }

  return (
    <Flex minH="100vh" align="center" justify="center" bg={pageBgColor}>
      <Box
        maxW="450px"
        w="full"
        bg={bgColor}
        boxShadow="xl"
        rounded="lg"
        p={8}
        borderWidth="1px"
        borderColor={borderColor}
      >
        {!success ? (
          <VStack spacing={6} align="stretch">
            <VStack spacing={2}>
              <Heading size="lg" color={textColor} textAlign="center">
                Set New Password
              </Heading>
              <Text fontSize="sm" color="gray.500" textAlign="center">
                Choose a strong password for your account
              </Text>
            </VStack>

            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel fontSize="sm" color={textColor}>New Password</FormLabel>
                  <InputGroup>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter new password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      size="lg"
                      borderColor={borderColor}
                    />
                    <InputRightElement h="full">
                      <IconButton
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                        icon={showPassword ? <FaEyeSlash /> : <FaEye />}
                        onClick={() => setShowPassword(!showPassword)}
                        variant="ghost"
                      />
                    </InputRightElement>
                  </InputGroup>
                </FormControl>

                <FormControl isRequired>
                  <FormLabel fontSize="sm" color={textColor}>Confirm Password</FormLabel>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    size="lg"
                    borderColor={borderColor}
                  />
                </FormControl>

                {/* Password Requirements */}
                <Box w="full" p={3} bg="gray.50" borderRadius="md">
                  <Text fontSize="xs" fontWeight="600" mb={2}>Password Requirements:</Text>
                  <List spacing={1}>
                    {passwordRequirements.map((req, idx) => (
                      <ListItem key={idx} fontSize="xs">
                        <ListIcon
                          as={req.test(newPassword) ? FaCheck : FaTimes}
                          color={req.test(newPassword) ? 'green.500' : 'gray.400'}
                        />
                        {req.label}
                      </ListItem>
                    ))}
                    <ListItem fontSize="xs">
                      <ListIcon
                        as={passwordsMatch ? FaCheck : FaTimes}
                        color={passwordsMatch ? 'green.500' : 'gray.400'}
                      />
                      Passwords match
                    </ListItem>
                  </List>
                </Box>

                <Button
                  type="submit"
                  colorScheme="brand"
                  size="lg"
                  w="full"
                  isLoading={loading}
                  isDisabled={!isPasswordValid || !passwordsMatch}
                >
                  Reset Password
                </Button>
              </VStack>
            </form>
          </VStack>
        ) : (
          <VStack spacing={6} align="center">
            <Icon as={FaCheckCircle} boxSize={16} color="green.500" />
            <Heading size="lg" color={textColor} textAlign="center">
              Password Reset Complete!
            </Heading>
            <Text fontSize="sm" color="gray.500" textAlign="center">
              Redirecting to login...
            </Text>
          </VStack>
        )}
      </Box>
    </Flex>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<Flex minH="100vh" align="center" justify="center"><Text>Loading...</Text></Flex>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
