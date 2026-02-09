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
  FormControl,
  FormLabel,
  FormHelperText,
  Textarea,
  Input,
  Select,
  Checkbox,
  Text,
  Box,
  useColorModeValue,
  useToast,
  Icon,
  Alert,
  AlertIcon,
  Spinner,
  Divider,
  Progress,
} from '@chakra-ui/react';
import {
  FaPaperPlane,
  FaClock,
  FaImage,
} from 'react-icons/fa';
import api from '@/lib/api';
import PlatformSelector, { PLATFORM_CONFIG, getStrictestLimit } from '@/components/social/PlatformSelector';

export default function CreateSocialPostModal({ isOpen, onClose, onPostCreated, userId }) {
  const toast = useToast();
  
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [content, setContent] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [mediaUrl, setMediaUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingProfiles, setLoadingProfiles] = useState(true);
  const [isScheduled, setIsScheduled] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Load user's social profiles
  const loadProfiles = useCallback(async () => {
    if (!userId) return;
    
    try {
      setLoadingProfiles(true);
      const response = await api.get('/social/profiles');
      
      const profilesList = response.data.profiles || [];
      setProfiles(profilesList);
      
      // Auto-select first profile
      if (profilesList.length > 0) {
        setSelectedProfile(profilesList[0].id);
      }
    } catch (error) {
      console.error('Failed to load profiles:', error);
    } finally {
      setLoadingProfiles(false);
    }
  }, [userId]);

  useEffect(() => {
    if (isOpen) {
      loadProfiles();
    }
  }, [isOpen, loadProfiles]);

  // Get available platforms from selected profile
  const getAvailablePlatforms = () => {
    const profile = profiles.find(p => p.id === selectedProfile);
    return profile?.linked_networks || [];
  };

  const availablePlatforms = getAvailablePlatforms();

  // Calculate content length and warnings using PLATFORM_CONFIG
  const getContentWarnings = () => {
    const warnings = [];
    selectedPlatforms.forEach(platform => {
      const config = PLATFORM_CONFIG[platform];
      if (config && content.length > config.charLimit) {
        warnings.push(`${config.label}: ${content.length}/${config.charLimit} characters (over limit)`);
      }
    });
    return warnings;
  };

  const contentWarnings = getContentWarnings();

  // Get minimum max length for selected platforms using getStrictestLimit
  const getMinMaxLength = () => {
    const limit = getStrictestLimit(selectedPlatforms);
    return limit || 280;
  };

  const handleSubmit = async () => {
    if (!selectedProfile) {
      toast({
        title: 'Please select a social profile',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: 'Please select at least one platform',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!content.trim()) {
      toast({
        title: 'Please enter post content',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    // Build schedule date if scheduled
    let scheduleDateISO = null;
    if (isScheduled && scheduleDate && scheduleTime) {
      const dateTime = new Date(`${scheduleDate}T${scheduleTime}`);
      if (dateTime <= new Date()) {
        toast({
          title: 'Schedule time must be in the future',
          status: 'warning',
          duration: 3000,
        });
        return;
      }
      scheduleDateISO = dateTime.toISOString();
    }

    setLoading(true);
    try {
      const payload = {
        content: content.trim(),
        platforms: selectedPlatforms,
      };
      
      if (mediaUrl.trim()) {
        payload.media_urls = [mediaUrl.trim()];
      }
      
      if (scheduleDateISO) {
        payload.schedule_date = scheduleDateISO;
      }

      const response = await api.post(
        `/social/posts?profile_id=${selectedProfile}`,
        payload
      );

      const result = response.data;
      
      // Check for errors in the response
      if (result.errors && result.errors.length > 0) {
        toast({
          title: 'Some platforms failed',
          description: result.errors.map(e => e.message || e).join(', '),
          status: 'warning',
          duration: 5000,
        });
      } else {
        toast({
          title: isScheduled ? 'Post Scheduled!' : 'Post Published!',
          description: isScheduled 
            ? `Your post will be published on ${new Date(scheduleDateISO).toLocaleString()}`
            : 'Your post has been published to the selected platforms',
          status: 'success',
          duration: 5000,
        });
      }

      // Reset form
      setContent('');
      setSelectedPlatforms([]);
      setScheduleDate('');
      setScheduleTime('');
      setMediaUrl('');
      setIsScheduled(false);
      
      if (onPostCreated) {
        onPostCreated(result);
      }
      
      onClose();
      
    } catch (error) {
      console.error('Failed to create post:', error);
      
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to create post';
      
      if (typeof errorDetail === 'object') {
        if (errorDetail.not_linked) {
          errorMessage = `Platforms not linked: ${errorDetail.not_linked.join(', ')}. Please link your accounts in Settings → Social Accounts.`;
        } else if (errorDetail.message) {
          errorMessage = errorDetail.message;
        }
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      }
      
      toast({
        title: 'Failed to create post',
        description: errorMessage,
        status: 'error',
        duration: 7000,
      });
    } finally {
      setLoading(false);
    }
  };

  // Get minimum date for scheduling (now)
  const getMinDate = () => {
    const now = new Date();
    return now.toISOString().split('T')[0];
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
      <ModalContent bg={cardBg} maxH="90vh">
        <ModalHeader>
          <HStack spacing={3}>
            <Icon as={FaPaperPlane} color="brand.500" />
            <Text>Create Social Post</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {loadingProfiles ? (
            <VStack py={8}>
              <Spinner size="lg" color="brand.500" />
              <Text color={textColorSecondary}>Loading profiles...</Text>
            </VStack>
          ) : profiles.length === 0 ? (
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              <Box>
                <Text fontWeight="600">No Social Profiles Found</Text>
                <Text fontSize="sm">
                  Please create a social profile and link your accounts in Settings → Social Accounts first.
                </Text>
              </Box>
            </Alert>
          ) : (
            <VStack spacing={5} align="stretch">
              {/* Profile Selection */}
              <FormControl>
                <FormLabel>Social Profile</FormLabel>
                <Select
                  value={selectedProfile}
                  onChange={(e) => {
                    setSelectedProfile(e.target.value);
                    setSelectedPlatforms([]); // Reset platform selection
                  }}
                >
                  {profiles.map(profile => (
                    <option key={profile.id} value={profile.id}>
                      {profile.title} ({profile.linked_networks?.length || 0} platforms linked)
                    </option>
                  ))}
                </Select>
              </FormControl>

              {/* Platform Selection - Using PlatformSelector */}
              <FormControl>
                <FormLabel>Target Platforms</FormLabel>
                <PlatformSelector
                  connectedPlatforms={availablePlatforms}
                  selectedPlatforms={selectedPlatforms}
                  onChange={setSelectedPlatforms}
                  showAllPlatforms={false}
                  showCharLimits={true}
                  showConnectLink={true}
                  compact={false}
                />
              </FormControl>

              <Divider />

              {/* Post Content */}
              <FormControl>
                <FormLabel>Post Content</FormLabel>
                <Textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="What's on your mind?"
                  rows={5}
                  resize="vertical"
                />
                <HStack justify="space-between" mt={2}>
                  <Text fontSize="xs" color={textColorSecondary}>
                    {content.length} characters
                  </Text>
                  {selectedPlatforms.length > 0 && (
                    <Text fontSize="xs" color={textColorSecondary}>
                      Min limit: {getMinMaxLength()} chars
                    </Text>
                  )}
                </HStack>
                {content.length > 0 && selectedPlatforms.length > 0 && (
                  <Progress
                    value={(content.length / getMinMaxLength()) * 100}
                    size="xs"
                    colorScheme={content.length > getMinMaxLength() ? 'red' : 'green'}
                    mt={1}
                  />
                )}
                {contentWarnings.length > 0 && (
                  <Alert status="warning" borderRadius="md" mt={2} size="sm">
                    <AlertIcon />
                    <VStack align="start" spacing={0}>
                      {contentWarnings.map((warning, idx) => (
                        <Text key={idx} fontSize="xs">{warning}</Text>
                      ))}
                    </VStack>
                  </Alert>
                )}
              </FormControl>

              {/* Media URL (Optional) */}
              <FormControl>
                <FormLabel>
                  <HStack spacing={2}>
                    <Icon as={FaImage} />
                    <Text>Media URL (Optional)</Text>
                  </HStack>
                </FormLabel>
                <Input
                  value={mediaUrl}
                  onChange={(e) => setMediaUrl(e.target.value)}
                  placeholder="https://example.com/image.jpg"
                />
                <FormHelperText>
                  Add a direct URL to an image or video
                </FormHelperText>
              </FormControl>

              <Divider />

              {/* Schedule Options */}
              <FormControl>
                <Checkbox
                  isChecked={isScheduled}
                  onChange={(e) => setIsScheduled(e.target.checked)}
                >
                  <HStack spacing={2}>
                    <Icon as={FaClock} />
                    <Text>Schedule for later</Text>
                  </HStack>
                </Checkbox>
              </FormControl>

              {isScheduled && (
                <HStack spacing={4}>
                  <FormControl>
                    <FormLabel fontSize="sm">Date</FormLabel>
                    <Input
                      type="date"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      min={getMinDate()}
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel fontSize="sm">Time</FormLabel>
                    <Input
                      type="time"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                    />
                  </FormControl>
                </HStack>
              )}
            </VStack>
          )}
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button
            colorScheme="brand"
            onClick={handleSubmit}
            isLoading={loading}
            loadingText={isScheduled ? 'Scheduling...' : 'Publishing...'}
            isDisabled={
              !selectedProfile ||
              selectedPlatforms.length === 0 ||
              !content.trim() ||
              profiles.length === 0
            }
            leftIcon={isScheduled ? <FaClock /> : <FaPaperPlane />}
          >
            {isScheduled ? 'Schedule Post' : 'Publish Now'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
