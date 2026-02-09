'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Icon,
  SimpleGrid,
  useColorModeValue,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  Divider,
  Avatar,
  IconButton,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Tooltip,
} from '@chakra-ui/react';
import {
  Twitter,
  Facebook,
  Instagram,
  Linkedin,
  Plus,
  Link as LinkIcon,
  Unlink,
  ExternalLink,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Globe,
} from 'lucide-react';
import { FaTiktok, FaPinterest, FaYoutube } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

// Platform configurations
const PLATFORMS = {
  linkedin: {
    name: 'LinkedIn',
    icon: Linkedin,
    color: 'linkedin',
    description: 'Professional networking',
  },
  twitter: {
    name: 'X (Twitter)',
    icon: Twitter,
    color: 'twitter',
    description: 'Microblogging platform',
  },
  facebook: {
    name: 'Facebook',
    icon: Facebook,
    color: 'facebook',
    description: 'Social networking',
  },
  instagram: {
    name: 'Instagram',
    icon: Instagram,
    color: 'pink',
    description: 'Photo and video sharing',
  },
  tiktok: {
    name: 'TikTok',
    icon: FaTiktok,
    color: 'gray',
    description: 'Short-form video',
  },
  youtube: {
    name: 'YouTube',
    icon: FaYoutube,
    color: 'red',
    description: 'Video platform',
  },
  pinterest: {
    name: 'Pinterest',
    icon: FaPinterest,
    color: 'red',
    description: 'Visual discovery',
  },
  threads: {
    name: 'Threads',
    icon: SiThreads,
    color: 'gray',
    description: 'Text-based conversations',
  },
};

export default function ConnectedSocialAccounts({ 
  workspaceType = 'personal', // 'personal' or 'company'
  enterpriseId = null,
  onAccountsChange = () => {},
}) {
  const { user } = useAuth();
  const toast = useToast();
  
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectingPlatform, setConnectingPlatform] = useState(null);
  const [error, setError] = useState(null);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedProfile, setSelectedProfile] = useState(null);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  const connectedBg = useColorModeValue('green.50', 'green.900');
  const disconnectedBg = useColorModeValue('gray.50', 'gray.700');

  // Fetch social profiles with linked accounts
  const fetchProfiles = async (sync = false) => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    
    try {
      setError(null);
      const API = getApiUrl();
      const response = await axios.get(`${API}/social/profiles`, {
        params: { 
          user_id: user?.id,
          sync: sync,
        },
        headers: { 'X-User-ID': user?.id },
      });
      
      if (response.data) {
        // Handle both array and object with profiles property
        const profilesData = Array.isArray(response.data) 
          ? response.data 
          : (response.data.profiles || []);
        
        // Filter by workspace type if needed
        let filtered;
        if (workspaceType === 'company') {
          // For company workspace, show company profiles (is_enterprise=true)
          filtered = profilesData.filter(p => p.is_enterprise === true || p.enterprise_id);
        } else {
          // For personal workspace, show profiles without enterprise_id and is_enterprise
          filtered = profilesData.filter(p => !p.enterprise_id && p.is_enterprise !== true);
        }
        
        setProfiles(filtered);
        onAccountsChange(filtered);
      }
    } catch (error) {
      console.error('Error fetching social profiles:', error);
      setError(error.message || 'Failed to fetch connected accounts');
      // Don't show error toast on initial load - might just not have profiles yet
      if (!loading) {
        toast({
          title: 'Error loading social accounts',
          description: error.response?.data?.detail || 'Failed to fetch connected accounts',
          status: 'error',
          duration: 3000,
        });
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchProfiles(true); // Sync on initial load
    } else {
      setLoading(false);
    }
  }, [user?.id, workspaceType, enterpriseId]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchProfiles(true);
    toast({
      title: 'Accounts refreshed',
      status: 'success',
      duration: 2000,
    });
  };

  const handleConnectAccount = async (profileId) => {
    try {
      setConnectingPlatform(profileId);
      const API = getApiUrl();
      
      const response = await axios.post(
        `${API}/social/profiles/${profileId}/generate-link`,
        {},
        { headers: { 'X-User-ID': user?.id } }
      );
      
      if (response.data?.url) {
        // Open the linking URL in a new window
        window.open(response.data.url, '_blank', 'width=600,height=700');
        
        toast({
          title: 'Connect your accounts',
          description: response.data.message || 'A new window has opened for you to connect your social accounts.',
          status: 'info',
          duration: 8000,
        });
        
        // Refresh profiles after a delay to get updated linked accounts
        setTimeout(() => {
          fetchProfiles(true);
        }, 5000);
      }
    } catch (error) {
      console.error('Error generating link:', error);
      toast({
        title: 'Connection failed',
        description: error.response?.data?.detail || 'Failed to generate connection link',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setConnectingPlatform(null);
    }
  };

  const createNewProfile = async () => {
    try {
      const API = getApiUrl();
      const profileName = workspaceType === 'company' 
        ? `${enterpriseId || 'Company'} Social Profile` 
        : `${user?.full_name || user?.email}'s Profile`;
      
      const response = await axios.post(
        `${API}/social/profiles`,
        { 
          title: profileName,
          enterprise_id: workspaceType === 'company' ? enterpriseId : null,
          is_enterprise: workspaceType === 'company',
        },
        { headers: { 'X-User-ID': user?.id } }
      );
      
      if (response.data) {
        toast({
          title: 'Profile created',
          description: 'Now connect your social accounts to this profile.',
          status: 'success',
          duration: 3000,
        });
        
        // Refresh and then open connect dialog
        await fetchProfiles(true);
        if (response.data.id) {
          handleConnectAccount(response.data.id);
        }
      }
    } catch (error) {
      console.error('Error creating profile:', error);
      toast({
        title: 'Error creating profile',
        description: error.response?.data?.detail || 'Failed to create social profile',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getLinkedPlatforms = (profile) => {
    return profile.linked_networks || [];
  };

  const getAccountInfo = (profile, platform) => {
    const info = profile.linked_accounts_info?.[platform];
    return info || null;
  };

  if (loading) {
    return (
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardBody>
          <HStack justify="center" py={8}>
            <Spinner size="lg" color="blue.500" />
            <Text color={mutedColor}>Loading connected accounts...</Text>
          </HStack>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
      <CardHeader pb={2}>
        <HStack justify="space-between" wrap="wrap" gap={2}>
          <VStack align="start" spacing={0}>
            <Heading size="md" color={textColor}>
              {workspaceType === 'company' ? 'Company Social Accounts' : 'My Social Accounts'}
            </Heading>
            <Text fontSize="sm" color={mutedColor}>
              {workspaceType === 'company' 
                ? 'Connect your company\'s official social media accounts'
                : 'Connect your personal social media accounts for content publishing'}
            </Text>
          </VStack>
          
          <HStack>
            <Tooltip label="Refresh accounts">
              <IconButton
                icon={<RefreshCw size={18} />}
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                isLoading={refreshing}
                aria-label="Refresh"
              />
            </Tooltip>
          </HStack>
        </HStack>
      </CardHeader>
      
      <CardBody>
        {profiles.length === 0 ? (
          <Box textAlign="center" py={8}>
            <Icon as={Globe} boxSize={12} color={mutedColor} mb={4} />
            <Heading size="sm" mb={2} color={textColor}>
              No Social Accounts Connected
            </Heading>
            <Text color={mutedColor} mb={4}>
              {workspaceType === 'company'
                ? 'Connect your company\'s social media accounts to start publishing content.'
                : 'Connect your social media accounts to start publishing content.'}
            </Text>
            <Button
              leftIcon={<LinkIcon size={18} />}
              colorScheme="blue"
              onClick={createNewProfile}
            >
              Connect Social Accounts
            </Button>
          </Box>
        ) : (
          <VStack spacing={4} align="stretch">
            {profiles.map((profile) => {
              const linkedPlatforms = getLinkedPlatforms(profile);
              
              return (
                <Box
                  key={profile.id}
                  p={4}
                  borderWidth="1px"
                  borderColor={borderColor}
                  borderRadius="lg"
                >
                  <HStack justify="space-between" mb={3}>
                    <VStack align="start" spacing={0}>
                      <HStack>
                        <Text fontWeight="600" color={textColor}>{profile.title}</Text>
                        {profile.is_primary && (
                          <Badge colorScheme="purple" size="sm">Primary</Badge>
                        )}
                      </HStack>
                      <Text fontSize="xs" color={mutedColor}>
                        {linkedPlatforms.length} platform(s) connected
                      </Text>
                    </VStack>
                    
                    <Button
                      leftIcon={<LinkIcon size={16} />}
                      size="sm"
                      variant="outline"
                      colorScheme="blue"
                      onClick={() => handleConnectAccount(profile.id)}
                      isLoading={connectingPlatform === profile.id}
                    >
                      Manage Connections
                    </Button>
                  </HStack>
                  
                  <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={3}>
                    {Object.entries(PLATFORMS).map(([key, platform]) => {
                      const isConnected = linkedPlatforms.includes(key);
                      const accountInfo = getAccountInfo(profile, key);
                      const PlatformIcon = platform.icon;
                      
                      return (
                        <Box
                          key={key}
                          p={3}
                          borderRadius="md"
                          bg={isConnected ? connectedBg : disconnectedBg}
                          borderWidth="1px"
                          borderColor={isConnected ? 'green.200' : borderColor}
                          opacity={isConnected ? 1 : 0.6}
                        >
                          <VStack spacing={2}>
                            <HStack>
                              <Icon 
                                as={PlatformIcon} 
                                boxSize={5} 
                                color={isConnected ? `${platform.color}.500` : mutedColor}
                              />
                              {isConnected && (
                                <Icon as={CheckCircle} boxSize={4} color="green.500" />
                              )}
                            </HStack>
                            <Text fontSize="xs" fontWeight="500" color={textColor}>
                              {platform.name}
                            </Text>
                            {isConnected && accountInfo?.username && (
                              <Text fontSize="xs" color={mutedColor} noOfLines={1}>
                                @{accountInfo.username}
                              </Text>
                            )}
                            {!isConnected && (
                              <Text fontSize="xs" color={mutedColor}>
                                Not connected
                              </Text>
                            )}
                          </VStack>
                        </Box>
                      );
                    })}
                  </SimpleGrid>
                </Box>
              );
            })}
          </VStack>
        )}
        
        <Divider my={4} />
        
        <Alert status="info" variant="subtle" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontSize="sm" fontWeight="500">
              How to connect accounts
            </Text>
            <Text fontSize="xs" color={mutedColor}>
              Click "Manage Connections" to open the social account linking page. 
              You'll be able to authorize each platform securely. 
              After connecting, refresh this page to see your linked accounts.
            </Text>
          </Box>
        </Alert>
      </CardBody>
    </Card>
  );
}
