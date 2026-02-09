'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Flex,
  Text,
  Box,
  Checkbox,
  Icon,
  Input,
  Grid,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  useToast,
  Link,
} from '@chakra-ui/react';
import {
  FaFacebookF,
  FaInstagram,
  FaLinkedinIn,
  FaYoutube,
  FaTwitter,
  FaTiktok,
  FaPinterest,
  FaCalendarAlt,
  FaClock,
  FaCheckCircle,
  FaExclamationCircle,
  FaExternalLinkAlt,
} from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import api from '@/lib/api';
import NextLink from 'next/link';

// Platform configuration
const PLATFORM_CONFIG = {
  facebook: { label: 'Facebook', icon: FaFacebookF, color: '#1877F2' },
  instagram: { label: 'Instagram', icon: FaInstagram, color: '#E4405F' },
  linkedin: { label: 'LinkedIn', icon: FaLinkedinIn, color: '#0A66C2' },
  youtube: { label: 'YouTube', icon: FaYoutube, color: '#FF0000' },
  twitter: { label: 'Twitter/X', icon: FaTwitter, color: '#1DA1F2' },
  tiktok: { label: 'TikTok', icon: FaTiktok, color: '#000000' },
  pinterest: { label: 'Pinterest', icon: FaPinterest, color: '#E60023' },
  threads: { label: 'Threads', icon: SiThreads, color: '#000000' },
};

// Platforms to show in the modal
const DISPLAY_PLATFORMS = ['facebook', 'instagram', 'linkedin', 'youtube', 'twitter', 'tiktok', 'pinterest', 'threads'];

export default function PostToSocialModal({
  isOpen,
  onClose,
  content,
  userId,
  onPostSuccess,
  mediaUrl = null,
  imageBase64 = null,  // NEW: Accept base64 image
  imageMimeType = 'image/png',  // NEW: MIME type for base64 image
  defaultSchedule = false,  // NEW: Open with schedule mode enabled
}) {
  const toast = useToast();
  
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [connectedPlatforms, setConnectedPlatforms] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState({});
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [isScheduled, setIsScheduled] = useState(defaultSchedule);
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);  // NEW: Track uploaded image URL
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');

  const cardBg = useColorModeValue('white', 'gray.800');
  const platformBg = useColorModeValue('gray.50', 'gray.700');
  const connectedBg = useColorModeValue('green.50', 'green.900');
  const connectedBorder = useColorModeValue('green.300', 'green.600');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');

  // Load user's social profiles and connected accounts
  const loadSocialData = useCallback(async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      
      // Get user's social profiles - use sync=false for faster cached reads
      // The Settings page will do the full sync with Ayrshare
      const profilesResponse = await api.get('/social/profiles', {
        params: { sync: false }  // Use cached data for faster loading
      });
      
      const profilesList = profilesResponse.data.profiles || [];
      setProfiles(profilesList);
      
      if (profilesList.length > 0) {
        // Use the first profile's data directly - no need for second API call
        // The profiles endpoint already returns linked_networks and linked_accounts_info
        const firstProfile = profilesList[0];
        setSelectedProfile(firstProfile);
        setConnectedPlatforms(firstProfile.linked_networks || []);
      }
    } catch (error) {
      console.error('Failed to load social data:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (isOpen) {
      loadSocialData();
      // Reset selections when modal opens, but respect defaultSchedule prop
      setSelectedPlatforms({});
      setIsScheduled(defaultSchedule);
      setScheduleDate('');
      setScheduleTime('');
    }
  }, [isOpen, loadSocialData, defaultSchedule]);

  const handlePlatformToggle = (platformId) => {
    if (!connectedPlatforms.includes(platformId)) {
      toast({
        title: 'Platform not connected',
        description: 'Please connect this platform in Settings → Social Accounts first.',
        status: 'warning',
        duration: 4000,
      });
      return;
    }
    
    setSelectedPlatforms(prev => ({
      ...prev,
      [platformId]: !prev[platformId]
    }));
  };

  const handlePost = async () => {
    const platformsToPost = Object.entries(selectedPlatforms)
      .filter(([_, selected]) => selected)
      .map(([platform]) => platform);
    
    if (platformsToPost.length === 0) {
      toast({
        title: 'No platforms selected',
        description: 'Please select at least one platform to post to.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!content?.trim()) {
      toast({
        title: 'No content to post',
        description: 'Please add some content before posting.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    // Validate schedule if scheduled
    let scheduleDateISO = null;
    if (isScheduled) {
      if (!scheduleDate || !scheduleTime) {
        toast({
          title: 'Schedule incomplete',
          description: 'Please select both date and time for scheduling.',
          status: 'warning',
          duration: 3000,
        });
        return;
      }
      
      const dateTime = new Date(`${scheduleDate}T${scheduleTime}`);
      if (dateTime <= new Date()) {
        toast({
          title: 'Invalid schedule time',
          description: 'Schedule time must be in the future.',
          status: 'warning',
          duration: 3000,
        });
        return;
      }
      scheduleDateISO = dateTime.toISOString();
    }

    setPosting(true);
    try {
      // Step 1: Upload base64 image if provided
      let finalMediaUrl = mediaUrl || uploadedImageUrl;
      
      if (imageBase64 && !finalMediaUrl) {
        try {
          toast({
            title: 'Uploading image...',
            status: 'info',
            duration: 2000,
          });
          
          const uploadResponse = await api.post(
            '/social/upload-image',
            {
              image_base64: imageBase64,
              mime_type: imageMimeType,
            }
          );
          
          if (uploadResponse.data.success) {
            finalMediaUrl = uploadResponse.data.url;
            setUploadedImageUrl(finalMediaUrl);
          }
        } catch (uploadError) {
          console.error('Image upload failed:', uploadError);
          toast({
            title: 'Image upload failed',
            description: 'Posting without image. ' + (uploadError.response?.data?.detail || uploadError.message),
            status: 'warning',
            duration: 4000,
          });
        }
      }
      
      // Step 2: Create the post
      const payload = {
        content: content.trim(),
        platforms: platformsToPost,
      };
      
      if (finalMediaUrl) {
        payload.media_urls = [finalMediaUrl];
      }
      
      if (scheduleDateISO) {
        payload.schedule_date = scheduleDateISO;
      }

      const response = await api.post(
        `/social/posts?profile_id=${selectedProfile.id}`,
        payload
      );

      const result = response.data;
      
      if (result.errors && result.errors.length > 0) {
        toast({
          title: 'Some platforms failed',
          description: result.errors.map(e => e.message || e).join(', '),
          status: 'warning',
          duration: 5000,
        });
      } else {
        toast({
          title: isScheduled ? 'Post Scheduled!' : 'Posted Successfully!',
          description: isScheduled 
            ? `Your post will be published on ${new Date(scheduleDateISO).toLocaleString()}`
            : `Posted to ${platformsToPost.join(', ')}`,
          status: 'success',
          duration: 5000,
        });
      }

      if (onPostSuccess) {
        onPostSuccess(result);
      }
      
      onClose();
      
    } catch (error) {
      console.error('Failed to post:', error);
      
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to post content';
      let errorStatus = 'error';
      
      if (typeof errorDetail === 'object') {
        if (errorDetail.action === 'upgrade_plan') {
          // Ayrshare plan upgrade required
          errorMessage = errorDetail.info || 'Ayrshare Premium Plan required to post';
          toast({
            title: 'Upgrade Required',
            description: (
              <>
                {errorMessage}
                <br />
                <a href={errorDetail.url || 'https://www.ayrshare.com/pricing'} target="_blank" rel="noopener noreferrer" style={{color: '#3182CE', textDecoration: 'underline'}}>
                  View Ayrshare Plans
                </a>
              </>
            ),
            status: 'warning',
            duration: 10000,
            isClosable: true,
          });
          return;
        } else if (errorDetail.not_linked) {
          errorMessage = `Platforms not linked: ${errorDetail.not_linked.join(', ')}`;
        } else if (errorDetail.message) {
          errorMessage = errorDetail.message;
        }
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      }
      
      toast({
        title: 'Post Failed',
        description: errorMessage,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setPosting(false);
    }
  };

  const getMinDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const selectedCount = Object.values(selectedPlatforms).filter(Boolean).length;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
      <ModalContent maxW="500px" maxH="85vh" bg={cardBg}>
        <ModalHeader pb={2}>Post to Social Media</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody py={2}>
          {loading ? (
            <VStack py={4}>
              <Spinner size="md" color="brand.500" />
              <Text fontSize="sm" color={textColorSecondary}>Loading accounts...</Text>
            </VStack>
          ) : profiles.length === 0 ? (
            <Alert status="warning" borderRadius="md" size="sm">
              <AlertIcon />
              <Box>
                <Text fontWeight="600" fontSize="sm">No Social Profiles Found</Text>
                <Link as={NextLink} href="/contentry/settings/social" color="brand.500" fontSize="sm">
                  Go to Social Settings <Icon as={FaExternalLinkAlt} boxSize={3} ml={1} />
                </Link>
              </Box>
            </Alert>
          ) : (
            <VStack align="stretch" spacing={2}>
              {/* Connection Status */}
              <HStack justify="space-between">
                <Text fontWeight="600" fontSize="sm" color={textColor}>Select Platforms:</Text>
                <Badge colorScheme={connectedPlatforms.length > 0 ? 'green' : 'gray'} fontSize="xs">
                  {connectedPlatforms.length} Connected
                </Badge>
              </HStack>

              {/* Platform List - Compact */}
              <VStack spacing={1} align="stretch">
                {DISPLAY_PLATFORMS.map((platformId) => {
                  const config = PLATFORM_CONFIG[platformId];
                  if (!config) return null;
                  
                  const isConnected = connectedPlatforms.includes(platformId);
                  const isSelected = selectedPlatforms[platformId] || false;
                  
                  return (
                    <Flex
                      key={platformId}
                      justify="space-between"
                      align="center"
                      p={2}
                      bg={isConnected ? (isSelected ? connectedBg : platformBg) : platformBg}
                      borderRadius="md"
                      borderWidth={isConnected && isSelected ? '1px' : '0'}
                      borderColor={connectedBorder}
                      opacity={isConnected ? 1 : 0.5}
                      cursor={isConnected ? 'pointer' : 'not-allowed'}
                      onClick={() => handlePlatformToggle(platformId)}
                      transition="all 0.15s"
                      _hover={isConnected ? { bg: isSelected ? connectedBg : 'gray.100' } : {}}
                    >
                      <HStack spacing={2}>
                        <Checkbox
                          isChecked={isSelected}
                          isDisabled={!isConnected}
                          onChange={() => {}}
                          pointerEvents="none"
                          size="sm"
                        />
                        <Icon as={config.icon} fontSize="md" color={config.color} />
                        <Text fontWeight="500" fontSize="sm" color={textColor}>{config.label}</Text>
                      </HStack>
                      
                      {isConnected ? (
                        <Icon as={FaCheckCircle} color="green.500" boxSize={3} />
                      ) : (
                        <Link
                          as={NextLink}
                          href="/contentry/settings/social"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Button size="xs" variant="outline" colorScheme="brand">
                            CONNECT
                          </Button>
                        </Link>
                      )}
                    </Flex>
                  );
                })}
              </VStack>

              {/* No Connected Platforms Warning - Compact */}
              {connectedPlatforms.length === 0 && (
                <Alert status="info" borderRadius="md" py={2}>
                  <AlertIcon boxSize={4} />
                  <Text fontSize="sm">
                    Connect accounts in{' '}
                    <Link as={NextLink} href="/contentry/settings/social" color="brand.500" fontWeight="600">
                      Settings → Social
                    </Link>
                  </Text>
                </Alert>
              )}

              {/* Image Preview - Show if image is available */}
              {(imageBase64 || mediaUrl) && (
                <Box 
                  p={2} 
                  borderWidth="1px" 
                  borderRadius="md" 
                  borderColor="green.300"
                  bg="green.50"
                  _dark={{ bg: 'green.900', borderColor: 'green.600' }}
                >
                  <HStack spacing={2} mb={2}>
                    <Icon as={FaCheckCircle} color="green.500" boxSize={3} />
                    <Text fontWeight="500" fontSize="sm" color="green.700" _dark={{ color: 'green.200' }}>
                      Image attached
                    </Text>
                  </HStack>
                  <Box borderRadius="md" overflow="hidden" maxH="120px">
                    <img 
                      src={imageBase64 ? `data:${imageMimeType};base64,${imageBase64}` : mediaUrl}
                      alt="Post image preview"
                      style={{ maxWidth: '100%', maxHeight: '120px', objectFit: 'contain' }}
                    />
                  </Box>
                </Box>
              )}

              {/* Schedule Option - Compact */}
              {connectedPlatforms.length > 0 && (
                <Box 
                  p={2} 
                  borderWidth="1px" 
                  borderRadius="md" 
                  borderColor={isScheduled ? "blue.400" : "gray.200"}
                  bg={isScheduled ? "blue.50" : platformBg}
                >
                  <Checkbox
                    isChecked={isScheduled}
                    onChange={(e) => setIsScheduled(e.target.checked)}
                    colorScheme="blue"
                    size="sm"
                  >
                    <HStack spacing={1}>
                      <Icon as={FaCalendarAlt} color={isScheduled ? "blue.600" : "gray.500"} boxSize={3} />
                      <Text fontWeight="500" fontSize="sm">Schedule for Later</Text>
                    </HStack>
                  </Checkbox>
                  
                  {isScheduled && (
                    <Grid templateColumns="1fr 1fr" gap={2} mt={2} pl={5}>
                      <Box>
                        <Text fontSize="xs" fontWeight="500" mb={1}>Date</Text>
                        <Input
                          type="date"
                          value={scheduleDate}
                          onChange={(e) => setScheduleDate(e.target.value)}
                          min={getMinDate()}
                          size="xs"
                        />
                      </Box>
                      <Box>
                        <Text fontSize="xs" fontWeight="500" mb={1}>Time</Text>
                        <Input
                          type="time"
                          value={scheduleTime}
                          onChange={(e) => setScheduleTime(e.target.value)}
                          size="xs"
                        />
                      </Box>
                    </Grid>
                  )}
                </Box>
              )}
            </VStack>
          )}
        </ModalBody>

        <ModalFooter pt={2}>
          <Button variant="ghost" mr={2} size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            colorScheme={isScheduled ? "blue" : "brand"}
            onClick={handlePost}
            isLoading={posting}
            loadingText={isScheduled ? 'Scheduling...' : 'Posting...'}
            isDisabled={selectedCount === 0 || loading || profiles.length === 0}
            leftIcon={isScheduled ? <FaClock /> : undefined}
            size="sm"
          >
            {isScheduled ? 'Schedule' : 'Post Now'}
            {selectedCount > 0 && ` (${selectedCount})`}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
