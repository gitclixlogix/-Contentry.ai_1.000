'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  VStack,
  Heading,
  Text,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputRightElement,
  Button,
  Icon,
  IconButton,
  useColorModeValue,
  useToast,
  Card,
  CardBody,
  Progress,
  HStack,
  List,
  ListItem,
  ListIcon,
  Spinner,
} from '@chakra-ui/react';
import { FaEye, FaEyeSlash, FaLock, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

// Loading fallback
const PageLoadingFallback = () => (
  <Flex minH="100vh" align="center" justify="center" bg="gray.50">
    <VStack spacing={4}>
      <Spinner size="xl" color="brand.500" thickness="4px" />
      <Text color="gray.600">Loading...</Text>
    </VStack>
  </Flex>
);

function SetPasswordForm({ email, fullName }) {
  const router = useRouter();
  const toast = useToast();

  const [temporaryPassword, setTemporaryPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showTempPassword, setShowTempPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Password requirements state
  const [passwordRequirements, setPasswordRequirements] = useState({
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSymbol: false,
  });

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const reqBg = useColorModeValue('gray.50', 'gray.700');

  // Check password requirements in real-time
  useEffect(() => {
    setPasswordRequirements({
      minLength: newPassword.length >= 8,
      hasUppercase: /[A-Z]/.test(newPassword),
      hasLowercase: /[a-z]/.test(newPassword),
      hasNumber: /\d/.test(newPassword),
      hasSymbol: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(newPassword),
    });
  }, [newPassword]);

  // Calculate password strength
  const getPasswordStrength = () => {
    const met = Object.values(passwordRequirements).filter(Boolean).length;
    if (met === 0) return { value: 0, color: 'gray', label: '' };
    if (met <= 2) return { value: 25, color: 'red', label: 'Weak' };
    if (met <= 3) return { value: 50, color: 'orange', label: 'Fair' };
    if (met <= 4) return { value: 75, color: 'yellow', label: 'Good' };
    return { value: 100, color: 'green', label: 'Strong' };
  };

  const passwordStrength = getPasswordStrength();
  const allRequirementsMet = Object.values(passwordRequirements).every(Boolean);
  const passwordsMatch = newPassword === confirmPassword && confirmPassword !== '';

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!temporaryPassword) {
      toast({
        title: 'Temporary password required',
        description: 'Please enter your temporary password.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!allRequirementsMet) {
      toast({
        title: 'Password requirements not met',
        description: 'Please ensure your new password meets all requirements.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!passwordsMatch) {
      toast({
        title: 'Passwords do not match',
        description: 'Please ensure both password fields match.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/auth/set-initial-password`, {
        email: email,
        temporary_password: temporaryPassword,
        new_password: newPassword,
      });

      if (response.data.success) {
        toast({
          title: 'Password set successfully!',
          description: 'You can now log in with your new password.',
          status: 'success',
          duration: 4000,
        });

        // Redirect to login page
        setTimeout(() => {
          router.push('/contentry/auth/login');
        }, 1500);
      }
    } catch (error) {
      console.error('Set password error:', error);
      const errorMessage =
        error.response?.data?.detail?.message ||
        error.response?.data?.detail ||
        error.message ||
        'Failed to set password. Please try again.';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex minH="100vh" align="center" justify="center" bg={bgColor} p={4}>
      <Card maxW="md" w="full" bg={cardBg} borderColor={borderColor} borderWidth="1px" shadow="lg">
        <CardBody p={8}>
          <VStack spacing={6} align="stretch">
            {/* Header */}
            <VStack spacing={2} textAlign="center">
              <Icon as={FaLock} boxSize={10} color="brand.500" />
              <Heading size="lg" color={textColor}>
                Set Your Password
              </Heading>
              <Text color={mutedColor} fontSize="sm">
                {fullName ? `Welcome, ${fullName}!` : 'Welcome!'} Please create a new password to secure your account.
              </Text>
              <Text color={mutedColor} fontSize="xs" fontWeight="medium" bg={reqBg} px={3} py={1} borderRadius="md">
                {email}
              </Text>
            </VStack>

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                {/* Temporary Password */}
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Temporary Password</FormLabel>
                  <InputGroup>
                    <Input
                      type={showTempPassword ? 'text' : 'password'}
                      placeholder="Enter your temporary password"
                      value={temporaryPassword}
                      onChange={(e) => setTemporaryPassword(e.target.value)}
                      data-testid="temp-password-input"
                    />
                    <InputRightElement>
                      <IconButton
                        variant="ghost"
                        size="sm"
                        icon={showTempPassword ? <FaEyeSlash /> : <FaEye />}
                        onClick={() => setShowTempPassword(!showTempPassword)}
                        aria-label={showTempPassword ? 'Hide password' : 'Show password'}
                      />
                    </InputRightElement>
                  </InputGroup>
                </FormControl>

                {/* New Password */}
                <FormControl isRequired>
                  <FormLabel fontSize="sm">New Password</FormLabel>
                  <InputGroup>
                    <Input
                      type={showNewPassword ? 'text' : 'password'}
                      placeholder="Create your new password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      data-testid="new-password-input"
                    />
                    <InputRightElement>
                      <IconButton
                        variant="ghost"
                        size="sm"
                        icon={showNewPassword ? <FaEyeSlash /> : <FaEye />}
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                      />
                    </InputRightElement>
                  </InputGroup>

                  {/* Password Strength Indicator */}
                  {newPassword && (
                    <Box mt={2}>
                      <HStack justify="space-between" mb={1}>
                        <Text fontSize="xs" color={mutedColor}>
                          Password Strength
                        </Text>
                        <Text fontSize="xs" color={`${passwordStrength.color}.500`}>
                          {passwordStrength.label}
                        </Text>
                      </HStack>
                      <Progress
                        value={passwordStrength.value}
                        colorScheme={passwordStrength.color}
                        size="xs"
                        borderRadius="full"
                      />
                    </Box>
                  )}
                </FormControl>

                {/* Confirm Password */}
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Confirm New Password</FormLabel>
                  <InputGroup>
                    <Input
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Confirm your new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      isInvalid={confirmPassword && !passwordsMatch}
                      data-testid="confirm-password-input"
                    />
                    <InputRightElement>
                      <IconButton
                        variant="ghost"
                        size="sm"
                        icon={showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      />
                    </InputRightElement>
                  </InputGroup>
                  {confirmPassword && !passwordsMatch && (
                    <Text fontSize="xs" color="red.500" mt={1}>
                      Passwords do not match
                    </Text>
                  )}
                </FormControl>

                {/* Password Requirements */}
                <Box w="full" p={3} bg={reqBg} borderRadius="md">
                  <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>
                    Password Requirements
                  </Text>
                  <List spacing={1}>
                    {[
                      { key: 'minLength', label: 'At least 8 characters' },
                      { key: 'hasUppercase', label: 'One uppercase letter' },
                      { key: 'hasLowercase', label: 'One lowercase letter' },
                      { key: 'hasNumber', label: 'One number' },
                      { key: 'hasSymbol', label: 'One special character (!@#$%...)' },
                    ].map((req) => (
                      <ListItem key={req.key} fontSize="xs" color={passwordRequirements[req.key] ? 'green.500' : mutedColor}>
                        <ListIcon
                          as={passwordRequirements[req.key] ? FaCheckCircle : FaTimesCircle}
                          color={passwordRequirements[req.key] ? 'green.500' : 'gray.400'}
                        />
                        {req.label}
                      </ListItem>
                    ))}
                  </List>
                </Box>

                {/* Submit Button */}
                <Button
                  type="submit"
                  colorScheme="brand"
                  w="full"
                  isLoading={loading}
                  isDisabled={!allRequirementsMet || !passwordsMatch || !temporaryPassword}
                  data-testid="set-password-btn"
                >
                  Set Password
                </Button>
              </VStack>
            </form>
          </VStack>
        </CardBody>
      </Card>
    </Flex>
  );
}

// Main content wrapper that handles searchParams
function SetPasswordPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [paramsLoaded, setParamsLoaded] = useState(false);

  useEffect(() => {
    // Only run on client side when searchParams is available
    if (typeof window !== 'undefined') {
      // Get params from URL using window.location as a fallback
      const urlParams = new URLSearchParams(window.location.search);
      const emailParam = searchParams?.get('email') || urlParams.get('email') || '';
      const nameParam = searchParams?.get('name') || urlParams.get('name') || '';
      
      setEmail(emailParam);
      setFullName(nameParam);
      setParamsLoaded(true);
    }
  }, [searchParams]);

  // Show loading until params are loaded
  if (!paramsLoaded) {
    return <PageLoadingFallback />;
  }

  // Redirect if no email after params are loaded
  if (!email) {
    // Use a separate effect for redirect to avoid SSR issues
    return (
      <Flex minH="100vh" align="center" justify="center" bg="gray.50">
        <VStack spacing={4}>
          <Text color="red.500">No email provided. Redirecting to login...</Text>
        </VStack>
      </Flex>
    );
  }

  return <SetPasswordForm email={email} fullName={fullName} />;
}

// Export with Suspense wrapper (required for useSearchParams in Next.js 13+)
export default function SetPasswordPage() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <SetPasswordPageContent />
    </Suspense>
  );
}
