'use client';

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
  useColorModeValue,
  VStack,
  HStack,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Badge,
  InputGroup,
  InputRightElement,
  IconButton,
  Card,
  CardBody,
  Divider,
} from '@chakra-ui/react';
import { FaEye, FaEyeSlash, FaUserPlus, FaBuilding, FaEnvelope, FaUser, FaLock } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import ContentryLogo from '@/components/branding/ContentryLogo';

function AcceptInviteContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const { login } = useAuth();
  
  const token = searchParams.get('token');
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [invitation, setInvitation] = useState(null);
  
  // Form fields
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // Colors - all hooks must be called before any conditional returns
  const bgColor = useColorModeValue('white', 'gray.800');
  const pageBgColor = useColorModeValue('gray.50', 'gray.900');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const cardBg = useColorModeValue('gray.50', 'gray.700');
  const inputBg = useColorModeValue('white', 'gray.700');
  const messageBg = useColorModeValue('blue.50', 'blue.900');
  
  // Fetch invitation details
  useEffect(() => {
    const fetchInvitation = async () => {
      if (!token) {
        setError('No invitation token provided');
        setLoading(false);
        return;
      }
      
      try {
        const API = getApiUrl();
        const response = await axios.get(`${API}/team-management/invitation/${token}`);
        setInvitation(response.data);
        setError(null);
      } catch (err) {
        const errorMessage = err.response?.data?.detail || 'Failed to load invitation';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };
    
    fetchInvitation();
  }, [token]);
  
  // Handle form submission
  const handleAcceptInvitation = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!fullName.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter your full name',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    if (password.length < 8) {
      toast({
        title: 'Password too short',
        description: 'Password must be at least 8 characters',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    if (password !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure your passwords match',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setSubmitting(true);
    
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/team-management/invitation/${token}/accept`, {
        full_name: fullName.trim(),
        password: password,
      });
      
      toast({
        title: 'Welcome to the team!',
        description: 'Your account has been created successfully',
        status: 'success',
        duration: 5000,
      });
      
      // Auto-login the user
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: invitation.email,
        password: password,
      }, { withCredentials: true });
      
      if (loginResponse.data.success) {
        login(loginResponse.data.user);
        router.push('/contentry/dashboard');
      } else {
        // If auto-login fails, redirect to login page
        router.push('/contentry/auth/login');
      }
      
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to accept invitation';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSubmitting(false);
    }
  };
  
  // Get role badge color
  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'red';
      case 'manager': return 'blue';
      case 'creator': return 'blue';
      default: return 'gray';
    }
  };
  
  // Loading state
  if (loading) {
    return (
      <Flex minH="100vh" justify="center" align="center" bg={pageBgColor}>
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" thickness="4px" />
          <Text color={textColorSecondary}>Loading invitation...</Text>
        </VStack>
      </Flex>
    );
  }
  
  // Error state
  if (error) {
    return (
      <Flex minH="100vh" justify="center" align="center" bg={pageBgColor} p={4}>
        <Card maxW="md" w="full" bg={bgColor}>
          <CardBody>
            <VStack spacing={4} align="center">
              <ContentryLogo h="40px" />
              <Alert status="error" borderRadius="md" flexDirection="column" textAlign="center" py={6}>
                <AlertIcon boxSize="40px" mr={0} mb={4} />
                <AlertTitle fontSize="lg">Invitation Error</AlertTitle>
                <AlertDescription mt={2}>{error}</AlertDescription>
              </Alert>
              <Button
                colorScheme="brand"
                onClick={() => router.push('/contentry/auth/login')}
              >
                Go to Login
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Flex>
    );
  }
  
  // Invitation form
  return (
    <Flex minH="100vh" justify="center" align="center" bg={pageBgColor} p={4}>
      <Card maxW="md" w="full" bg={bgColor} shadow="xl">
        <CardBody>
          <VStack spacing={6}>
            {/* Logo */}
            <ContentryLogo h="40px" />
            
            {/* Invitation Info Card */}
            <Box w="full" p={4} bg={cardBg} borderRadius="lg" borderWidth="1px" borderColor={borderColor}>
              <VStack spacing={3} align="start">
                <HStack justify="space-between" w="full">
                  <HStack>
                    <FaBuilding color="gray" />
                    <Text fontSize="sm" color={textColorSecondary}>Team Invitation</Text>
                  </HStack>
                  <Badge colorScheme={getRoleBadgeColor(invitation.role)} fontSize="sm">
                    {invitation.role?.charAt(0).toUpperCase() + invitation.role?.slice(1)}
                  </Badge>
                </HStack>
                
                <Divider />
                
                <VStack align="start" spacing={2} w="full">
                  <Text fontSize="sm" color={textColorSecondary}>
                    <strong>{invitation.inviter_name}</strong> has invited you to join their team
                  </Text>
                  
                  <HStack>
                    <FaEnvelope color="gray" />
                    <Text fontSize="sm" color={textColor}>{invitation.email}</Text>
                  </HStack>
                  
                  {invitation.message && (
                    <Box mt={2} p={3} bg={messageBg} borderRadius="md" w="full">
                      <Text fontSize="sm" fontStyle="italic" color={textColor}>
                        &ldquo;{invitation.message}&rdquo;
                      </Text>
                    </Box>
                  )}
                </VStack>
              </VStack>
            </Box>
            
            {/* Signup Form */}
            <Box w="full">
              <Heading size="md" mb={4} textAlign="center" color={textColor}>
                Create Your Account
              </Heading>
              
              <form onSubmit={handleAcceptInvitation}>
                <VStack spacing={4}>
                  <FormControl isRequired>
                    <FormLabel fontSize="sm">Full Name</FormLabel>
                    <InputGroup>
                      <Input
                        type="text"
                        placeholder="Enter your full name"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        bg={inputBg}
                      />
                    </InputGroup>
                  </FormControl>
                  
                  <FormControl isRequired>
                    <FormLabel fontSize="sm">Password</FormLabel>
                    <InputGroup>
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Create a password (min 8 characters)"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        bg={inputBg}
                      />
                      <InputRightElement>
                        <IconButton
                          variant="ghost"
                          size="sm"
                          icon={showPassword ? <FaEyeSlash /> : <FaEye />}
                          onClick={() => setShowPassword(!showPassword)}
                          aria-label={showPassword ? 'Hide password' : 'Show password'}
                        />
                      </InputRightElement>
                    </InputGroup>
                  </FormControl>
                  
                  <FormControl isRequired>
                    <FormLabel fontSize="sm">Confirm Password</FormLabel>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Confirm your password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      bg={inputBg}
                    />
                  </FormControl>
                  
                  <Button
                    type="submit"
                    colorScheme="brand"
                    size="lg"
                    w="full"
                    leftIcon={<FaUserPlus />}
                    isLoading={submitting}
                    loadingText="Creating Account..."
                  >
                    Accept Invitation & Join Team
                  </Button>
                </VStack>
              </form>
            </Box>
            
            {/* Footer */}
            <Text fontSize="xs" color={textColorSecondary} textAlign="center">
              By accepting this invitation, you agree to our Terms of Service and Privacy Policy.
            </Text>
          </VStack>
        </CardBody>
      </Card>
    </Flex>
  );
}

// Wrap in Suspense for useSearchParams
export default function AcceptInvitePage() {
  return (
    <Suspense fallback={
      <Flex minH="100vh" justify="center" align="center">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    }>
      <AcceptInviteContent />
    </Suspense>
  );
}
