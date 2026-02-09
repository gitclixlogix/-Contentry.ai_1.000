'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  SimpleGrid,
  Text,
  useColorModeValue,
  Flex,
  Heading,
  Button,
  Spinner,
  Center,
  VStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Card,
  CardBody,
  CardHeader,
  useToast,
  Icon,
  HStack,
  Tooltip,
  IconButton,
  Progress,
  useDisclosure,
} from '@chakra-ui/react';
import MiniStatistics from '@/components/card/MiniStatistics';
import IconBox from '@/components/icons/IconBox';
import { FaClock, FaCheckCircle, FaPlay, FaSyncAlt, FaChartLine, FaRedo, FaFacebookF, FaInstagram, FaLinkedinIn, FaTwitter, FaList, FaCalendarAlt, FaPlus, FaTiktok, FaPinterest, FaYoutube } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import { MdSchedule } from 'react-icons/md';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useRouter } from 'next/navigation';
import CalendarView from '@/components/scheduler/CalendarView';
import CreateSocialPostModal from '@/components/scheduler/CreateSocialPostModal';
import { useAuth } from '@/context/AuthContext';

export default function SchedulerPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const { user, isLoading: authLoading, isHydrated } = useAuth();
  
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [socialPosts, setSocialPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingPost, setProcessingPost] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  
  // Modal state
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();

  const brandColor = useColorModeValue('brand.500', 'white');
  const boxBg = useColorModeValue('secondaryGray.300', 'whiteAlpha.100');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('white', 'gray.800');
  const platformIconBg = useColorModeValue('gray.100', 'gray.700');

  useEffect(() => {
    if (isHydrated && !authLoading && user?.id) {
      loadData();
    }
  }, [isHydrated, authLoading, user]);

  const loadData = async () => {
    if (!user?.id) return;
    
    try {
      const API = getApiUrl();
      
      // Load scheduler status
      const statusResponse = await axios.get(`${API}/scheduler/status`);
      setSchedulerStatus(statusResponse.data);

      // Load user's scheduled posts
      const postsResponse = await axios.get(`${API}/scheduler/posts/scheduled`, {
        headers: { 'X-User-ID': user.id }
      });
      setScheduledPosts(postsResponse.data.scheduled_posts || []);
      
      // Load social posts
      try {
        const socialResponse = await axios.get(`${API}/social/posts`, {
          headers: { 'X-User-ID': user.id }
        });
        setSocialPosts(socialResponse.data.posts || []);
      } catch (e) {
        console.log('Social posts not available');
      }

    } catch (error) {
      console.error('Error loading data:', error);
      toast({
        title: 'Failed to load scheduler data',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerPost = async (postId) => {
    try {
      setProcessingPost(postId);
      const API = getApiUrl();
      
      const response = await axios.post(
        `${API}/scheduler/trigger/${postId}`,
        {},
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Post Published!',
        description: 'Your post has been published successfully.',
        status: 'success',
        duration: 5000,
      });
      
      // Reload data
      await loadData();
      
    } catch (error) {
      console.error('Error triggering post:', error);
      toast({
        title: 'Failed to publish post',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setProcessingPost(null);
    }
  };

  const handleReanalyze = async (postId) => {
    try {
      setProcessingPost(postId);
      const API = getApiUrl();
      
      const response = await axios.post(
        `${API}/scheduler/reanalyze/${postId}`,
        {},
        { headers: { 'X-User-ID': user.id } }
      );
      
      const reanalysis = response.data.reanalysis;
      const safeToPost = reanalysis.safe_to_post;
      
      toast({
        title: safeToPost ? 'Content Approved' : 'Content Flagged',
        description: safeToPost 
          ? 'Your content is still safe to publish.' 
          : 'Content was flagged during reanalysis. Please review.',
        status: safeToPost ? 'success' : 'warning',
        duration: 5000,
      });
      
      await loadData();
      
    } catch (error) {
      console.error('Error reanalyzing post:', error);
      toast({
        title: 'Failed to reanalyze post',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setProcessingPost(null);
    }
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      facebook: FaFacebookF,
      instagram: FaInstagram,
      linkedin: FaLinkedinIn,
      twitter: FaTwitter,
      tiktok: FaTiktok,
      pinterest: FaPinterest,
      youtube: FaYoutube,
      threads: SiThreads,
    };
    return icons[platform.toLowerCase()] || MdSchedule;
  };

  const getPlatformColor = (platform) => {
    const colors = {
      facebook: '#4267B2',
      instagram: '#E4405F',
      linkedin: '#0A66C2',
      twitter: '#1DA1F2',
      tiktok: '#000000',
      pinterest: '#E60023',
      youtube: '#FF0000',
      threads: '#000000',
    };
    return colors[platform.toLowerCase()] || brandColor;
  };

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeRemaining = (isoString) => {
    const now = new Date();
    const postTime = new Date(isoString);
    const diffMs = postTime - now;
    
    if (diffMs < 0) return 'Due now';
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `in ${diffDays}d ${diffHours % 24}h`;
    if (diffHours > 0) return `in ${diffHours}h ${diffMins % 60}m`;
    return `in ${diffMins}m`;
  };

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <Center h="100vh">
        <VStack spacing={4}>
          <Spinner size="xl" color={brandColor} />
          <Text color={textColorSecondary}>Loading scheduler...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Header */}
      <Flex mb={6} justify="space-between" align="center" flexWrap="wrap" gap={4}>
        <Box>
          <Flex align="center" gap={3}>
            <Heading size="lg" color={textColor}>
              Post Scheduler
            </Heading>
            <Badge colorScheme={schedulerStatus?.scheduler_active ? 'green' : 'red'} fontSize="md" px={3} py={1}>
              {schedulerStatus?.scheduler_active ? 'ACTIVE' : 'INACTIVE'}
            </Badge>
          </Flex>
          <Text color={textColorSecondary} fontSize="md" mt={2}>
            Automated posting with pre-publish reanalysis
          </Text>
        </Box>
        <HStack spacing={3}>
          <Button
            leftIcon={<Icon as={FaPlus} />}
            colorScheme="brand"
            onClick={onCreateOpen}
          >
            Create Post
          </Button>
          <Button
            leftIcon={<Icon as={FaSyncAlt} />}
            variant="outline"
            size="sm"
            onClick={loadData}
            isLoading={loading}
          >
            Refresh
          </Button>
        </HStack>
      </Flex>

      {/* Overview Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg="orange.100"
              icon={<Icon w="32px" h="32px" as={MdSchedule} color="orange.500" />}
            />
          }
          name="Total Scheduled"
          value={schedulerStatus?.total_scheduled_posts || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg="red.100"
              icon={<Icon w="32px" h="32px" as={FaClock} color="red.500" />}
            />
          }
          name="Due Now"
          value={schedulerStatus?.due_posts || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg="green.100"
              icon={<Icon w="32px" h="32px" as={FaCheckCircle} color="green.500" />}
            />
          }
          name="Published (24h)"
          value={schedulerStatus?.recently_published || 0}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w="56px"
              h="56px"
              bg={boxBg}
              icon={<Icon w="32px" h="32px" as={FaChartLine} color={brandColor} />}
            />
          }
          name="Check Interval"
          value={schedulerStatus?.check_interval || 'N/A'}
        />
      </SimpleGrid>

      {/* Features Card */}
      <Card bg={cardBg} mb={6} boxShadow="lg">
        <CardHeader>
          <Heading size="md" color={textColor}>Scheduler Features</Heading>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            <HStack spacing={3}>
              <Icon as={FaSyncAlt} color="green.500" boxSize={6} />
              <Box>
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  Pre-Publish Reanalysis
                </Text>
                <Text fontSize="xs" color={textColorSecondary}>
                  Content is re-checked before posting
                </Text>
              </Box>
            </HStack>
            <HStack spacing={3}>
              <Icon as={FaPlay} color="blue.500" boxSize={6} />
              <Box>
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  Auto-Posting
                </Text>
                <Text fontSize="xs" color={textColorSecondary}>
                  Automatic publishing to platforms
                </Text>
              </Box>
            </HStack>
            <HStack spacing={3}>
              <Icon as={FaChartLine} color="blue.500" boxSize={6} />
              <Box>
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  Multi-Platform
                </Text>
                <Text fontSize="xs" color={textColorSecondary}>
                  Post to multiple platforms at once
                </Text>
              </Box>
            </HStack>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Scheduled Posts */}
      <Card bg={cardBg} boxShadow="lg">
        <CardHeader>
          <Flex align="center" justify="space-between" flexWrap="wrap" gap={3}>
            <Box>
              <Heading size="md" color={textColor}>Your Scheduled Posts</Heading>
              <Text fontSize="sm" color={textColorSecondary} mt={1}>
                Posts will be automatically published at their scheduled time
              </Text>
            </Box>
            <HStack spacing={3}>
              {/* View Toggle */}
              <HStack spacing={1} bg={boxBg} p={1} borderRadius="lg">
                <Tooltip label="List View">
                  <IconButton
                    icon={<FaList />}
                    size="sm"
                    variant={viewMode === 'list' ? 'solid' : 'ghost'}
                    colorScheme={viewMode === 'list' ? 'brand' : 'gray'}
                    onClick={() => setViewMode('list')}
                    aria-label="List view"
                  />
                </Tooltip>
                <Tooltip label="Calendar View">
                  <IconButton
                    icon={<FaCalendarAlt />}
                    size="sm"
                    variant={viewMode === 'calendar' ? 'solid' : 'ghost'}
                    colorScheme={viewMode === 'calendar' ? 'brand' : 'gray'}
                    onClick={() => setViewMode('calendar')}
                    aria-label="Calendar view"
                  />
                </Tooltip>
              </HStack>
              <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
                {scheduledPosts.length} posts
              </Badge>
            </HStack>
          </Flex>
        </CardHeader>
        <CardBody>
          {viewMode === 'calendar' ? (
            <CalendarView 
              scheduledPosts={scheduledPosts} 
              onPostClick={(post) => {
                toast({
                  title: post.title,
                  description: `Scheduled for ${new Date(post.scheduled_time).toLocaleString()}`,
                  status: 'info',
                  duration: 3000,
                });
              }}
            />
          ) : scheduledPosts.length > 0 ? (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Post Title</Th>
                    <Th>Platforms</Th>
                    <Th>Scheduled Time</Th>
                    <Th>Time Remaining</Th>
                    <Th>Status</Th>
                    <Th>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {scheduledPosts.map((post) => (
                    <Tr key={post.id}>
                      <Td>
                        <VStack align="start" spacing={1}>
                          <Text fontWeight="600" fontSize="sm">{post.title}</Text>
                          <Text fontSize="xs" color={textColorSecondary} noOfLines={1}>
                            {post.content}
                          </Text>
                        </VStack>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          {post.platforms?.map((platform) => (
                            <Tooltip key={platform} label={platform}>
                              <Box
                                p={2}
                                borderRadius="md"
                                bg={platformIconBg}
                              >
                                <Icon as={getPlatformIcon(platform)} color={brandColor} />
                              </Box>
                            </Tooltip>
                          ))}
                        </HStack>
                      </Td>
                      <Td>
                        <Text fontSize="sm" fontWeight="500">
                          {formatDateTime(post.post_time)}
                        </Text>
                      </Td>
                      <Td>
                        <Badge colorScheme="blue">
                          {getTimeRemaining(post.post_time)}
                        </Badge>
                      </Td>
                      <Td>
                        <Badge
                          colorScheme={
                            post.flagged_status === 'good_coverage' ? 'green' :
                            post.flagged_status === 'needs_attention' ? 'yellow' :
                            'red'
                          }
                        >
                          {post.flagged_status || 'pending'}
                        </Badge>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          <Tooltip label="Publish now">
                            <IconButton
                              icon={<Icon as={FaPlay} />}
                              size="sm"
                              colorScheme="green"
                              variant="outline"
                              onClick={() => handleTriggerPost(post.id)}
                              isLoading={processingPost === post.id}
                              aria-label="Publish now"
                            />
                          </Tooltip>
                          <Tooltip label="Reanalyze content">
                            <IconButton
                              icon={<Icon as={FaRedo} />}
                              size="sm"
                              colorScheme="blue"
                              variant="outline"
                              onClick={() => handleReanalyze(post.id)}
                              isLoading={processingPost === post.id}
                              aria-label="Reanalyze"
                            />
                          </Tooltip>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          ) : (
            <Center py={8}>
              <VStack spacing={3}>
                <Icon as={MdSchedule} boxSize={12} color={textColorSecondary} />
                <Text color={textColor} fontWeight="600">No Scheduled Posts</Text>
                <Text fontSize="sm" color={textColorSecondary} textAlign="center" maxW="400px">
                  Schedule posts from the Content Intelligence page to see them here
                </Text>
                <Button
                  colorScheme="brand"
                  size="sm"
                  mt={4}
                  onClick={onCreateOpen}
                  leftIcon={<Icon as={FaPlus} />}
                >
                  Create Post
                </Button>
              </VStack>
            </Center>
          )}
        </CardBody>
      </Card>
      
      {/* Create Social Post Modal */}
      <CreateSocialPostModal
        isOpen={isCreateOpen}
        onClose={onCreateClose}
        userId={user?.id}
        onPostCreated={() => {
          loadData();
        }}
      />
    </Box>
  );
}
