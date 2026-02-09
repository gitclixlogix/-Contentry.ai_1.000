'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Badge,
  Icon,
  useToast,
  useColorModeValue,
  Divider,
  Image,
  Input,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Alert,
  AlertIcon,
  AlertDescription,
  SimpleGrid,
  Code,
  Spinner,
  Center,
  Switch,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';
import { FaShieldAlt, FaKey, FaMobile, FaCheckCircle, FaTimesCircle, FaCopy, FaTrash, FaLock } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function SecuritySettingsPage() {
  const { user } = useAuth();
  const toast = useToast();
  const { isOpen: isSetupOpen, onOpen: onSetupOpen, onClose: onSetupClose } = useDisclosure();
  const { isOpen: isDisableOpen, onOpen: onDisableOpen, onClose: onDisableClose } = useDisclosure();
  const { isOpen: isBackupOpen, onOpen: onBackupOpen, onClose: onBackupClose } = useDisclosure();

  const [loading, setLoading] = useState(true);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaEnabledAt, setMfaEnabledAt] = useState(null);
  
  // MFA Setup state
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [backupCodes, setBackupCodes] = useState([]);
  const [disableCode, setDisableCode] = useState('');
  const [disabling, setDisabling] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const codeBg = useColorModeValue('gray.100', 'gray.700');

  useEffect(() => {
    if (user?.id) {
      loadSecurityStatus();
    }
  }, [user]);

  const loadSecurityStatus = async () => {
    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/auth/security/mfa/status`, {
        headers: { 'X-User-ID': user.id }
      });
      setMfaEnabled(response.data.mfa_enabled || false);
      setMfaEnabledAt(response.data.mfa_enabled_at || null);
    } catch (error) {
      console.error('Failed to load security status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetupMFA = async () => {
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/auth/security/mfa/setup`, {}, {
        headers: { 'X-User-ID': user.id }
      });
      setSetupData(response.data);
      setBackupCodes(response.data.backup_codes || []);
      onSetupOpen();
    } catch (error) {
      toast({
        title: 'Failed to start MFA setup',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleVerifyMFA = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      toast({
        title: 'Invalid code',
        description: 'Please enter a 6-digit code from your authenticator app',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setVerifying(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/auth/security/mfa/verify-setup`, {
        code: verificationCode
      }, {
        headers: { 'X-User-ID': user.id }
      });

      toast({
        title: '2FA Enabled!',
        description: 'Two-factor authentication is now active on your account',
        status: 'success',
        duration: 5000,
      });

      setMfaEnabled(true);
      setMfaEnabledAt(new Date().toISOString());
      onSetupClose();
      onBackupOpen(); // Show backup codes
      setVerificationCode('');
      setSetupData(null);
    } catch (error) {
      toast({
        title: 'Verification failed',
        description: 'Invalid code. Please try again.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleDisableMFA = async () => {
    if (!disableCode || disableCode.length < 6) {
      toast({
        title: 'Invalid code',
        description: 'Please enter a code from your authenticator app or a backup code',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setDisabling(true);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/auth/security/mfa/disable`, {
        code: disableCode
      }, {
        headers: { 'X-User-ID': user.id }
      });

      toast({
        title: '2FA Disabled',
        description: 'Two-factor authentication has been disabled on your account',
        status: 'info',
        duration: 5000,
      });

      setMfaEnabled(false);
      setMfaEnabledAt(null);
      onDisableClose();
      setDisableCode('');
    } catch (error) {
      toast({
        title: 'Failed to disable 2FA',
        description: 'Invalid code. Please try again.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDisabling(false);
    }
  };

  const copyBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    toast({
      title: 'Copied!',
      description: 'Backup codes copied to clipboard',
      status: 'success',
      duration: 2000,
    });
  };

  if (loading) {
    return (
      <Center minH="400px">
        <Spinner size="lg" color="brand.500" />
      </Center>
    );
  }

  return (
    <Box p={{ base: 4, md: 6 }} maxW="800px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>Security Settings</Heading>
          <Text color={textColor}>
            Manage your account security and two-factor authentication
          </Text>
        </Box>

        {/* 2FA Card */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <HStack justify="space-between">
              <HStack>
                <Icon as={FaShieldAlt} color="brand.500" boxSize={5} />
                <Heading size="md">Two-Factor Authentication (2FA)</Heading>
              </HStack>
              <Badge colorScheme={mfaEnabled ? 'green' : 'gray'}>
                {mfaEnabled ? 'Enabled' : 'Disabled'}
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor} fontSize="sm">
                Add an extra layer of security to your account by requiring a verification code 
                from an authenticator app (like Google Authenticator or Authy) when you sign in 
                from an unrecognized device.
              </Text>

              {mfaEnabled ? (
                <>
                  <Alert status="success" borderRadius="md">
                    <AlertIcon />
                    <AlertDescription>
                      2FA has been enabled since {mfaEnabledAt ? new Date(mfaEnabledAt).toLocaleDateString() : 'recently'}.
                      Your account is protected with an additional layer of security.
                    </AlertDescription>
                  </Alert>
                  <HStack>
                    <Button 
                      colorScheme="red" 
                      variant="outline" 
                      leftIcon={<FaTimesCircle />}
                      onClick={onDisableOpen}
                      size="sm"
                    >
                      Disable 2FA
                    </Button>
                    <Button 
                      variant="outline" 
                      leftIcon={<FaKey />}
                      onClick={handleSetupMFA}
                      size="sm"
                    >
                      View New Backup Codes
                    </Button>
                  </HStack>
                </>
              ) : (
                <>
                  <Alert status="warning" borderRadius="md">
                    <AlertIcon />
                    <AlertDescription>
                      Your account is not protected by 2FA. We strongly recommend enabling it for better security.
                    </AlertDescription>
                  </Alert>
                  <Button 
                    colorScheme="brand" 
                    leftIcon={<FaMobile />}
                    onClick={handleSetupMFA}
                    size="md"
                  >
                    Enable Two-Factor Authentication
                  </Button>
                </>
              )}
            </VStack>
          </CardBody>
        </Card>

        {/* Password Security Card */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <HStack>
              <Icon as={FaLock} color="brand.500" boxSize={5} />
              <Heading size="md">Password Security</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={4}>
              <Text color={textColor} fontSize="sm">
                Keep your account secure by using a strong password and changing it regularly.
              </Text>
              <Button 
                variant="outline" 
                colorScheme="brand"
                onClick={() => window.location.href = '/contentry/auth/forgot-password'}
                size="sm"
                maxW="200px"
              >
                Change Password
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </VStack>

      {/* MFA Setup Modal */}
      <Modal isOpen={isSetupOpen} onClose={onSetupClose} size="lg" closeOnOverlayClick={false}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Set Up Two-Factor Authentication</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color={textColor}>
                Scan the QR code below with your authenticator app (Google Authenticator, Authy, etc.):
              </Text>

              {setupData?.qr_code && (
                <Center>
                  <Box p={4} bg="white" borderRadius="md">
                    <Image src={setupData.qr_code} alt="MFA QR Code" boxSize="200px" />
                  </Box>
                </Center>
              )}

              <Text fontSize="xs" color={textColor} textAlign="center">
                Or enter this secret key manually:
              </Text>
              <Code p={2} textAlign="center" bg={codeBg} borderRadius="md" fontSize="sm">
                {setupData?.secret}
              </Code>

              <Divider />

              <FormControl>
                <FormLabel fontSize="sm">Enter the 6-digit code from your app:</FormLabel>
                <Input
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  maxLength={6}
                  textAlign="center"
                  fontSize="xl"
                  letterSpacing="0.5em"
                  fontFamily="mono"
                />
              </FormControl>

              <Alert status="info" borderRadius="md" fontSize="sm">
                <AlertIcon />
                <AlertDescription>
                  After enabling 2FA, you&apos;ll receive backup codes. Save them in a secure place - 
                  they&apos;re the only way to access your account if you lose your phone.
                </AlertDescription>
              </Alert>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onSetupClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleVerifyMFA}
              isLoading={verifying}
              isDisabled={verificationCode.length !== 6}
            >
              Verify & Enable 2FA
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Backup Codes Modal */}
      <Modal isOpen={isBackupOpen} onClose={onBackupClose} size="md" closeOnOverlayClick={false}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <HStack>
              <Icon as={FaKey} color="orange.500" />
              <Text>Your Backup Codes</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert status="warning" borderRadius="md">
                <AlertIcon />
                <AlertDescription fontSize="sm">
                  <strong>Save these codes now!</strong> They won&apos;t be shown again. 
                  Use them to access your account if you lose your authenticator device.
                </AlertDescription>
              </Alert>

              <Box bg={codeBg} p={4} borderRadius="md">
                <SimpleGrid columns={2} spacing={2}>
                  {backupCodes.map((code, idx) => (
                    <Code key={idx} p={2} textAlign="center" bg="transparent" fontSize="sm">
                      {code}
                    </Code>
                  ))}
                </SimpleGrid>
              </Box>

              <Button 
                leftIcon={<FaCopy />} 
                onClick={copyBackupCodes}
                variant="outline"
                size="sm"
              >
                Copy All Codes
              </Button>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="brand" onClick={onBackupClose}>
              I&apos;ve Saved My Codes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Disable 2FA Modal */}
      <Modal isOpen={isDisableOpen} onClose={onDisableClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader color="red.500">Disable Two-Factor Authentication</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                <AlertDescription fontSize="sm">
                  Disabling 2FA will make your account less secure. 
                  Are you sure you want to continue?
                </AlertDescription>
              </Alert>

              <FormControl>
                <FormLabel fontSize="sm">
                  Enter a code from your authenticator app (or a backup code) to confirm:
                </FormLabel>
                <Input
                  placeholder="Enter code"
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value.toUpperCase())}
                  textAlign="center"
                  fontSize="lg"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onDisableClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="red" 
              onClick={handleDisableMFA}
              isLoading={disabling}
              isDisabled={!disableCode}
            >
              Disable 2FA
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
