'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Flex,
  Text,
  VStack,
  HStack,
  Icon,
  Badge,
  useToast,
  useColorModeValue,
  Spinner,
  Alert,
  AlertIcon,
  Tooltip,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FaFacebookF,
  FaInstagram,
  FaLinkedinIn,
  FaYoutube,
  FaTwitter,
  FaCheck,
  FaLink,
  FaExternalLinkAlt,
  FaTiktok,
  FaPinterest,
} from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import Card from '@/components/card/Card';
import api from '@/lib/api';
import Link from 'next/link';

/**
 * Social Media Connections Component
 * Shows connected Ayrshare social accounts and allows linking new ones
 */
export default function SocialConnections({ compact = false, onConnectionChange }) {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [linking, setLinking] = useState(false);
  const toast = useToast();

  const textColorPrimary = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');
  const connectedBg = useColorModeValue('green.50', 'green.900');
  const connectedBorder = useColorModeValue('green.300', 'green.600');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const platforms = [
    { name: 'Twitter', apiName: 'twitter', icon: FaTwitter, color: '#1da1f2' },
    { name: 'LinkedIn', apiName: 'linkedin', icon: FaLinkedinIn, color: '#0a66c2' },
    { name: 'Facebook', apiName: 'facebook', icon: FaFacebookF, color: '#1877f2' },
    { name: 'Instagram', apiName: 'instagram', icon: FaInstagram, color: '#e4405f' },
    { name: 'YouTube', apiName: 'youtube', icon: FaYoutube, color: '#ff0000' },
    { name: 'TikTok', apiName: 'tiktok', icon: FaTiktok, color: '#000000' },
    { name: 'Pinterest', apiName: 'pinterest', icon: FaPinterest, color: '#E60023' },
    { name: 'Threads', apiName: 'threads', icon: SiThreads, color: '#000000' },
  ];

  const loadProfiles = useCallback(async () => {
    try {
      const userStr = localStorage.getItem('contentry_user');
      if (!userStr) return;
      
      const response = await api.get('/social/profiles');
      
      setProfiles(response.data.profiles || []);
      
      if (onConnectionChange) {
        const connectedPlatforms = {};
        response.data.profiles?.forEach(p => {
          p.linked_networks?.forEach(network => {
            connectedPlatforms[network] = true;
          });
        });
        onConnectionChange(connectedPlatforms);
      }
    } catch (error) {
      console.error('Failed to load social profiles:', error);
    } finally {
      setLoading(false);
    }
  }, [onConnectionChange]);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  const openLinkingPage = async (profileId) => {
    try {
      setLinking(true);
      const userStr = localStorage.getItem('contentry_user');
      if (!userStr) return;
      
      const response = await api.post(
        `/social/profiles/${profileId}/generate-link`,
        {}
      );
      
      const { url, type, message } = response.data;
      
      if (type === 'dashboard') {
        toast({
          title: 'Link Social Accounts',
          description: message,
          status: 'info',
          duration: 5000,
        });
      }
      
      window.open(url, '_blank', 'width=800,height=600');
    } catch (error) {
      toast({
        title: 'Failed to open linking page',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLinking(false);
    }
  };

  // Get all connected platforms across all profiles
  const getConnectedPlatforms = () => {
    const connected = new Set();
    profiles.forEach(p => {
      p.linked_networks?.forEach(network => connected.add(network));
    });
    return connected;
  };

  const connectedPlatforms = getConnectedPlatforms();
  const connectedCount = connectedPlatforms.size;

  if (loading) {
    return (
      <Card p={6}>
        <Flex justify="center" align="center" h="150px">
          <Spinner size="lg" color="brand.500" />
        </Flex>
      </Card>
    );
  }

  return (
    <Card p={compact ? 4 : 6} bg={cardBg}>
      <VStack spacing={compact ? 3 : 5} align="stretch">
        {/* Header */}
        <Flex justify="space-between" align="center">
          <Box>
            <Text fontSize={compact ? 'md' : 'xl'} color={textColorPrimary} fontWeight="bold">
              Social Accounts
            </Text>
            {!compact && (
              <Text fontSize="sm" color={textColorSecondary}>
                Connect via Ayrshare to publish content directly
              </Text>
            )}
          </Box>
          <Badge colorScheme={connectedCount > 0 ? 'green' : 'gray'} fontSize="xs">
            {connectedCount} Connected
          </Badge>
        </Flex>

        {/* Platform Status Grid */}
        <SimpleGrid columns={compact ? 4 : 4} spacing={2}>
          {platforms.map(platform => {
            const isConnected = connectedPlatforms.has(platform.apiName);
            return (
              <Tooltip key={platform.apiName} label={isConnected ? 'Connected' : 'Not connected'}>
                <HStack
                  p={2}
                  borderRadius="md"
                  bg={isConnected ? connectedBg : 'transparent'}
                  border="1px solid"
                  borderColor={isConnected ? connectedBorder : borderColor}
                  opacity={isConnected ? 1 : 0.5}
                  justify="center"
                >
                  <Icon as={platform.icon} color={platform.color} boxSize={compact ? 4 : 5} />
                  {!compact && (
                    <Text fontSize="xs" color={textColorPrimary} display={{ base: 'none', md: 'block' }}>
                      {platform.name}
                    </Text>
                  )}
                  {isConnected && <Icon as={FaCheck} color="green.500" boxSize={3} />}
                </HStack>
              </Tooltip>
            );
          })}
        </SimpleGrid>

        {/* Action Buttons */}
        {profiles.length > 0 ? (
          <VStack spacing={2}>
            {profiles.map(profile => (
              <Button
                key={profile.id}
                size="sm"
                w="full"
                leftIcon={<FaLink />}
                onClick={() => openLinkingPage(profile.id)}
                isLoading={linking}
                variant="outline"
                colorScheme="brand"
              >
                Link Accounts ({profile.title})
              </Button>
            ))}
          </VStack>
        ) : (
          <Alert status="info" borderRadius="md" fontSize="sm">
            <AlertIcon />
            <Box>
              <Text fontWeight="600">No social profiles yet</Text>
              <Text fontSize="xs">
                Create a social profile in{' '}
                <Link href="/contentry/settings/social" style={{ color: 'var(--chakra-colors-brand-500)', textDecoration: 'underline' }}>
                  Social Settings
                </Link>
              </Text>
            </Box>
          </Alert>
        )}

        {/* Manage Link */}
        <Button
          as={Link}
          href="/contentry/settings/social"
          size="sm"
          variant="ghost"
          rightIcon={<FaExternalLinkAlt />}
          colorScheme="brand"
        >
          Manage Social Accounts
        </Button>
      </VStack>
    </Card>
  );
}

