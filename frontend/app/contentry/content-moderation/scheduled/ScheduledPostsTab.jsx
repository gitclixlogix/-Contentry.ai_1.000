'use client';
import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import {
  Box,
  Button,
  Card,
  CardBody,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  HStack,
  Flex,
  Icon,
  useColorModeValue,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useDisclosure,
  VStack,
  Tooltip,
  useToast,
  Spinner,
  Center,
  IconButton,
  Input,
  Textarea,
  FormControl,
  FormLabel,
  Grid,
  Checkbox,
  Avatar,
} from '@chakra-ui/react';
import { FaFacebookF, FaInstagram, FaLinkedinIn, FaYoutube, FaTwitter, FaTrash, FaSync, FaClock, FaCalendarAlt, FaPlay, FaList, FaMagic, FaToggleOn, FaToggleOff, FaEdit, FaSearchPlus, FaTiktok, FaPinterest, FaExclamationTriangle, FaCheckCircle, FaTimes, FaPaperPlane, FaUserCheck } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import api from '@/lib/api';
import { getErrorMessage } from '@/lib/errorUtils';
import PlatformSelector, { PLATFORM_CONFIG } from '@/components/social/PlatformSelector';
import useContentAnalyzer from '@/hooks/useContentAnalyzer';
import AnalysisResults from '../components/AnalysisResults';
// Import workspace context
import { useWorkspace } from '@/context/WorkspaceContext';

// Lazy load heavy components
const CalendarView = dynamic(() => import('@/components/scheduler/CalendarView'), {
  ssr: false,
  loading: () => <Center py={4}><Spinner size="md" /></Center>,
});

const PostToSocialModal = dynamic(() => import('@/components/social/PostToSocialModal'), {
  ssr: false,
  loading: () => null,
});

export default function ScheduledPostsTab({ user, updatePostCounts, onOpenInAnalyze }) {
  const { t } = useTranslation();
  const { currentWorkspace, isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [scheduledPrompts, setScheduledPrompts] = useState([]);
  const [editingPost, setEditingPost] = useState(null);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list');
  const [connectedPlatforms, setConnectedPlatforms] = useState([]);
  const [loadingPlatforms, setLoadingPlatforms] = useState(false);
  
  // Approval workflow is now handled in AllPostsTab
  // Only keep userPermissions for reference if needed
  const [userPermissions, setUserPermissions] = useState({});
  
  // Modal states
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isEditPostOpen, onOpen: onEditPostOpen, onClose: onEditPostClose } = useDisclosure();
  const { isOpen: isEditPromptOpen, onOpen: onEditPromptOpen, onClose: onEditPromptClose } = useDisclosure();
  const { isOpen: isPostSocialOpen, onOpen: onPostSocialOpen, onClose: onPostSocialClose } = useDisclosure();
  const { isOpen: isAnalysisOpen, onOpen: onAnalysisOpen, onClose: onAnalysisClose } = useDisclosure();
  const { isOpen: isErrorOpen, onOpen: onErrorOpen, onClose: onErrorClose } = useDisclosure();
  
  const toast = useToast();
  
  // Use shared content analyzer hook
  const { analyzing, analysis, analyzeContent, resetAnalysis } = useContentAnalyzer();
  const [postToPublish, setPostToPublish] = useState(null);
  const [postToAnalyze, setPostToAnalyze] = useState(null);
  const [selectedError, setSelectedError] = useState(null);

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const secondaryTextColor = useColorModeValue('gray.600', 'gray.400');
  const scheduledBg = useColorModeValue('blue.50', 'blue.900');
  const modalContentBg = useColorModeValue('gray.50', 'gray.700');
  const iconColor = useColorModeValue('gray.600', 'gray.400');
  const toggleBg = useColorModeValue('gray.100', 'gray.700');
  
  // Function to show error details
  const showErrorDetails = (post) => {
    setSelectedError({
      content: post.content,
      error: post.error_message || 'Unknown error',
      failedAt: post.failed_at,
      platforms: post.platforms
    });
    onErrorOpen();
  };

  // Load user's connected social accounts
  const loadConnectedPlatforms = useCallback(async () => {
    if (!user?.id) return;
    setLoadingPlatforms(true);
    try {
      const response = await api.get(`/social/profiles`, {
        headers: { 'X-User-ID': user.id },
        params: { sync: false }  // Use cached data for faster loading
      });
      const profiles = response.data.profiles || [];
      if (profiles.length > 0) {
        setConnectedPlatforms(profiles[0].linked_networks || []);
      }
    } catch (error) {
      console.error('Failed to load connected platforms:', error);
    } finally {
      setLoadingPlatforms(false);
    }
  }, [user?.id]);

  useEffect(() => {
    if (user?.id) {
      loadScheduledPosts(user.id);
      loadScheduledPrompts(user.id);
      loadConnectedPlatforms();
      loadUserPermissions(user.id);
    }
  }, [user, currentWorkspace, loadConnectedPlatforms]); // Reload when workspace changes

  // Note: Pending approval UI moved to AllPostsTab
  // loadPendingApprovals and loadApprovedPosts are now handled there

  const loadScheduledPosts = async (userId) => {
    setLoading(true);
    try {
      // Build query params based on workspace context
      const workspaceParams = new URLSearchParams();
      workspaceParams.append('workspace', isEnterpriseWorkspace ? 'enterprise' : 'personal');
      if (isEnterpriseWorkspace && enterpriseInfo?.id) {
        workspaceParams.append('enterprise_id', enterpriseInfo.id);
      }
      
      // Fetch from both sources: regular posts and social posts
      const [regularPostsRes, socialPostsRes] = await Promise.all([
        api.get(`/posts?${workspaceParams.toString()}`, {
          params: { user_id: userId, status: 'scheduled' }
        }).catch(() => ({ data: [] })),
        api.get(`/social/posts`, {
          headers: { 'X-User-ID': userId }
        }).catch(() => ({ data: { posts: [] } }))
      ]);
      
      // Filter regular posts to only include scheduled and failed (exclude pending_approval, draft, etc.)
      const allRegularPosts = regularPostsRes.data.posts || regularPostsRes.data || [];
      const regularPosts = allRegularPosts.filter(p => 
        p.status === 'scheduled' || p.status === 'failed'
      );
      // Include both scheduled and failed posts from social
      const socialPosts = (socialPostsRes.data.posts || []).filter(p => 
        p.status === 'scheduled' || p.status === 'failed'
      );
      
      // Mark social posts to distinguish them
      const markedSocialPosts = socialPosts.map(p => ({
        ...p,
        source: 'social',
        scheduled_date: p.schedule_date // Normalize field name
      }));
      
      // Combine and sort by scheduled date (failed posts at top)
      const allPosts = [...regularPosts, ...markedSocialPosts].sort((a, b) => {
        // Failed posts first
        if (a.status === 'failed' && b.status !== 'failed') return -1;
        if (b.status === 'failed' && a.status !== 'failed') return 1;
        const dateA = new Date(a.scheduled_date || a.schedule_date);
        const dateB = new Date(b.scheduled_date || b.schedule_date);
        return dateA - dateB;
      });
      
      setScheduledPosts(allPosts);
    } catch (error) {
      console.error('Error loading scheduled posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadScheduledPrompts = async (userId) => {
    try {
      // Use authenticated api instance instead of plain axios
      const response = await api.get(`/scheduler/scheduled-prompts`, {
        headers: { 'X-User-ID': userId }
      });
      setScheduledPrompts(response.data || []);
    } catch (error) {
      console.error('Error loading scheduled prompts:', error);
      // Don't show error toast for empty results, just log it
    }
  };

  // ========== APPROVAL WORKFLOW FUNCTIONS ==========
  
  // Load user permissions
  const loadUserPermissions = async (userId) => {
    try {
      const response = await api.get(`/approval/user-permissions`, {
        headers: { 'X-User-ID': userId }
      });
      setUserPermissions(response.data.permissions || {});
    } catch (error) {
      console.error('Error loading user permissions:', error);
    }
  };

  // Note: Approval functions (loadPendingApprovals, loadApprovedPosts, approvePost, rejectPost) 
  // have been moved to AllPostsTab.jsx for cleaner separation of concerns

  // ========== END - Approval functions moved to AllPostsTab ==========

  const cancelScheduledPost = async (postId, source) => {
    if (!window.confirm(t('scheduledPosts.confirmCancel'))) return;
    try {
      // Delete from appropriate endpoint based on source
      if (source === 'social') {
        await api.delete(`/social/posts/${postId}`, { headers: { 'X-User-ID': user?.id } });
      } else {
        await api.delete(`/posts/${postId}`, { headers: { 'X-User-ID': user?.id } });
      }
      
      toast({ title: t('scheduledPosts.toasts.scheduledPostCancelled'), status: 'success', duration: 2000 });
      loadScheduledPosts(user?.id);
      if (updatePostCounts) updatePostCounts();
    } catch (error) {
      toast({ title: t('scheduledPosts.toasts.failedToCancelPost'), description: getErrorMessage(error), status: 'error', duration: 3000 });
    }
  };

  // Open PostToSocialModal for publishing - reuses same component as Analyze/Generate tabs
  const handlePublishNow = (post) => {
    setPostToPublish(post);
    onPostSocialOpen();
  };

  // Analyze post using shared hook - same analysis as AnalyzeContentTab
  const handleAnalyzePost = async (post) => {
    setPostToAnalyze(post);
    resetAnalysis();
    onAnalysisOpen();
    
    await analyzeContent(post.content, {
      userId: user?.id,
      showProgress: true,
    });
  };

  const deleteScheduledPrompt = async (promptId) => {
    if (!window.confirm(t('scheduledPosts.confirmDeletePrompt'))) return;
    try {
      await api.delete(`/scheduler/scheduled-prompts/${promptId}`, { headers: { 'X-User-ID': user?.id } });
      toast({ title: t('scheduledPosts.toasts.promptDeleted'), status: 'success', duration: 2000 });
      loadScheduledPrompts(user?.id);
    } catch (error) {
      toast({ title: t('scheduledPosts.toasts.failedToDeletePrompt'), description: getErrorMessage(error), status: 'error', duration: 3000 });
    }
  };

  const toggleScheduledPrompt = async (promptId) => {
    try {
      const prompt = scheduledPrompts.find(p => p.id === promptId);
      const newStatus = prompt?.status === 'active' ? 'paused' : 'active';
      await api.put(`/scheduler/scheduled-prompts/${promptId}`, { status: newStatus }, { headers: { 'X-User-ID': user?.id } });
      toast({ title: t(`scheduledPosts.toasts.promptUpdated`), status: 'success', duration: 2000 });
      loadScheduledPrompts(user?.id);
    } catch (error) {
      toast({ title: t('scheduledPosts.toasts.failedToUpdatePrompt'), description: getErrorMessage(error), status: 'error', duration: 3000 });
    }
  };

  const openEditPost = (post) => {
    const postTime = post.post_time ? new Date(post.post_time) : new Date();
    setEditingPost({
      ...post,
      scheduleDate: postTime.toISOString().split('T')[0],
      scheduleTime: postTime.toTimeString().slice(0, 5)
    });
    onEditPostOpen();
  };

  const saveEditedPost = async () => {
    if (!editingPost || !user) return;
    try {
      const postTime = `${editingPost.scheduleDate}T${editingPost.scheduleTime}:00`;
      await api.put(`/posts/${editingPost.id}`, {
        content: editingPost.content,
        post_time: postTime,
        platforms: editingPost.platforms
      }, { headers: { 'X-User-ID': user.id } });
      toast({ title: t('scheduledPosts.toasts.scheduledPostUpdated'), status: 'success', duration: 2000 });
      onEditPostClose();
      setEditingPost(null);
      loadScheduledPosts(user.id);
    } catch (error) {
      toast({ title: t('scheduledPosts.toasts.failedToUpdatePost'), description: getErrorMessage(error), status: 'error', duration: 3000 });
    }
  };

  const openEditPrompt = (prompt) => {
    setEditingPrompt({ ...prompt, hashtag_count: prompt.hashtag_count || 3 });
    onEditPromptOpen();
  };

  const saveEditedPrompt = async () => {
    if (!editingPrompt || !user) return;
    try {
      await api.put(`/scheduler/scheduled-prompts/${editingPrompt.id}`, {
        prompt: editingPrompt.prompt,
        schedule_type: editingPrompt.schedule_type,
        schedule_time: editingPrompt.schedule_time,
        auto_post: editingPrompt.auto_post,
        platforms: editingPrompt.platforms,
        hashtag_count: editingPrompt.hashtag_count
      }, { headers: { 'X-User-ID': user.id } });
      toast({ title: t('scheduledPosts.toasts.promptUpdated'), status: 'success', duration: 2000 });
      onEditPromptClose();
      setEditingPrompt(null);
      loadScheduledPrompts(user.id);
    } catch (error) {
      toast({ title: t('scheduledPosts.toasts.failedToUpdatePrompt'), description: getErrorMessage(error), status: 'error', duration: 3000 });
    }
  };

  const getPlatformIcon = (platform) => {
    const config = PLATFORM_CONFIG[platform?.toLowerCase()];
    return config?.icon || FaFacebookF;
  };

  const handleOpenInAnalyze = (post) => {
    if (onOpenInAnalyze) onOpenInAnalyze(post.content);
  };

  if (loading) {
    return (
      <Center py={12}>
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" />
          <Text color={textColor}>{t('scheduledPosts.loadingScheduledPosts')}</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      {/* Action Buttons and View Toggle */}
      <Flex gap={3} mb={4} justify="space-between" align="center" flexWrap="wrap">
        <Button leftIcon={<FaSync />} colorScheme="brand" onClick={() => { if (user) { loadScheduledPosts(user.id); loadScheduledPrompts(user.id); loadConnectedPlatforms(); } }} isLoading={loading} size="sm">{t('scheduledPosts.refresh')}</Button>
        <HStack spacing={1} bg={toggleBg} p={1} borderRadius="lg">
          <Tooltip label={t('scheduledPosts.listView')}><IconButton icon={<FaList />} size="sm" variant={viewMode === 'list' ? 'solid' : 'ghost'} colorScheme={viewMode === 'list' ? 'brand' : 'gray'} onClick={() => setViewMode('list')} aria-label={t('scheduledPosts.listView')} /></Tooltip>
          <Tooltip label={t('scheduledPosts.calendarView')}><IconButton icon={<FaCalendarAlt />} size="sm" variant={viewMode === 'calendar' ? 'solid' : 'ghost'} colorScheme={viewMode === 'calendar' ? 'brand' : 'gray'} onClick={() => setViewMode('calendar')} aria-label={t('scheduledPosts.calendarView')} /></Tooltip>
        </HStack>
      </Flex>

      {viewMode === 'calendar' ? (
        <CalendarView scheduledPosts={scheduledPosts.map(post => ({ ...post, scheduled_time: post.post_time || post.scheduled_time, title: post.content?.substring(0, 50) + '...' }))} scheduledPrompts={scheduledPrompts} onPostClick={openEditPost} onPromptClick={openEditPrompt} />
      ) : (
        <>
          {/* ========== SCHEDULED POSTS SECTION ========== */}
          <Card bg={cardBg}>
            <CardBody p={4}>
              <HStack mb={4} spacing={2}>
                <Icon as={FaCalendarAlt} color="blue.500" />
                <Text fontSize="lg" fontWeight="600" color={textColor}>{t('scheduledPosts.scheduledPosts')} ({scheduledPosts.length})</Text>
              </HStack>
              <Text fontSize="sm" color={secondaryTextColor} mb={4}>{t('scheduledPosts.scheduledPostsDesc')}</Text>
            
            {scheduledPosts.length === 0 ? (
              <Box textAlign="center" py={8} bg={scheduledBg} borderRadius="md">
                <Icon as={FaCalendarAlt} boxSize={10} mb={3} color={secondaryTextColor} />
                <Text fontSize="md" fontWeight="600" mb={1} color={textColor}>{t('scheduledPosts.noScheduledPosts')}</Text>
                <Text fontSize="sm" color={secondaryTextColor}>{t('scheduledPosts.postsWillAppearHere')}</Text>
              </Box>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>{t('scheduledPosts.content')}</Th>
                      <Th>{t('scheduledPosts.scheduledTime')}</Th>
                      <Th>{t('scheduledPosts.platforms')}</Th>
                      <Th>{t('scheduledPosts.status')}</Th>
                      <Th width="140px">{t('scheduledPosts.actions')}</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {scheduledPosts.map((post) => (
                      <Tr key={post.id}>
                        <Td maxW="300px">
                          <VStack align="start" spacing={1}>
                            <Text fontSize="sm" noOfLines={2}>{post.content}</Text>
                            {/* Workspace indicator */}
                            {post.enterprise_id && (
                              <Badge colorScheme="purple" fontSize="2xs" variant="subtle">
                                Company
                              </Badge>
                            )}
                          </VStack>
                        </Td>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <HStack spacing={1}>
                              <Icon as={FaClock} color="blue.500" boxSize={3} />
                              <Text fontSize="sm" fontWeight="600">{(post.post_time || post.scheduled_date || post.schedule_date) ? new Date(post.post_time || post.scheduled_date || post.schedule_date).toLocaleString() : t('scheduledPosts.notSet')}</Text>
                            </HStack>
                            {post.reanalyze_before_post && <Badge colorScheme="blue" fontSize="xs" mt={1}>{t('scheduledPosts.prePublishCheck')}</Badge>}
                          </VStack>
                        </Td>
                        <Td>
                          <HStack spacing={1} flexWrap="wrap">
                            {(post.platforms || []).map((platform) => {
                              const IconComp = getPlatformIcon(platform);
                              return <Tooltip key={platform} label={platform}><span><Icon as={IconComp} color={iconColor} boxSize={4} /></span></Tooltip>;
                            })}
                          </HStack>
                        </Td>
                        <Td>
                          {post.status === 'failed' ? (
                            <Tooltip label={t('scheduledPosts.errorMessage')}>
                              <Badge 
                                colorScheme="red" 
                                cursor="pointer" 
                                onClick={() => showErrorDetails(post)}
                                _hover={{ opacity: 0.8 }}
                              >
                                <HStack spacing={1}>
                                  <Icon as={FaExclamationTriangle} boxSize={3} />
                                  <Text>{t('scheduledPosts.failed')}</Text>
                                </HStack>
                              </Badge>
                            </Tooltip>
                          ) : (
                            <Badge colorScheme="blue">
                              <HStack spacing={1}>
                                <Icon as={FaCalendarAlt} boxSize={3} />
                                <Text>{t('scheduledPosts.scheduled')}</Text>
                              </HStack>
                            </Badge>
                          )}
                        </Td>
                        <Td>
                          {/* Compact action buttons on one line */}
                          <HStack spacing={0}>
                            <Tooltip label={t('scheduledPosts.analyze')}><IconButton size="xs" icon={<FaSearchPlus />} onClick={() => handleAnalyzePost(post)} colorScheme="blue" variant="ghost" aria-label={t('scheduledPosts.analyze')} /></Tooltip>
                            <Tooltip label={t('scheduledPosts.edit')}><IconButton size="xs" icon={<FaEdit />} onClick={() => openEditPost(post)} colorScheme="blue" variant="ghost" aria-label={t('scheduledPosts.edit')} /></Tooltip>
                            <Tooltip label={t('scheduledPosts.publishNow')}><IconButton size="xs" icon={<FaPlay />} onClick={() => handlePublishNow(post)} colorScheme="green" aria-label={t('scheduledPosts.publishNow')} /></Tooltip>
                            <Tooltip label={t('scheduledPosts.delete')}><IconButton size="xs" icon={<FaTrash />} onClick={() => cancelScheduledPost(post.id, post.source)} colorScheme="red" variant="ghost" aria-label={t('scheduledPosts.delete')} /></Tooltip>
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
          </CardBody>
        </Card>

      {/* Scheduled Prompts Section */}
      <Card bg={cardBg} mt={6}>
        <CardBody p={4}>
          <HStack mb={4} spacing={2}>
            <Icon as={FaMagic} color="blue.500" />
            <Text fontSize="lg" fontWeight="600" color={textColor}>{t('scheduledPosts.scheduledPrompts')} ({scheduledPrompts.length})</Text>
          </HStack>
          <Text fontSize="sm" color={secondaryTextColor} mb={4}>{t('scheduledPosts.scheduledPromptsDesc')}</Text>
          
          {scheduledPrompts.length === 0 ? (
            <Box textAlign="center" py={8} bg={scheduledBg} borderRadius="md">
              <Icon as={FaMagic} boxSize={10} mb={3} color={secondaryTextColor} />
              <Text fontSize="md" fontWeight="600" mb={1} color={textColor}>{t('scheduledPosts.noScheduledPrompts')}</Text>
              <Text fontSize="sm" color={secondaryTextColor}>{t('scheduledPosts.schedulePromptsHint')}</Text>
            </Box>
          ) : (
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>{t('scheduledPosts.prompt')}</Th>
                    <Th>{t('scheduledPosts.schedule')}</Th>
                    <Th>{t('scheduledPosts.nextRun')}</Th>
                    <Th>{t('scheduledPosts.autoPost')}</Th>
                    <Th>{t('scheduledPosts.status')}</Th>
                    <Th width="100px">{t('scheduledPosts.actions')}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {scheduledPrompts.map((prompt) => (
                    <Tr key={prompt.id}>
                      <Td maxW="250px"><Text fontSize="sm" noOfLines={2}>{prompt.prompt}</Text></Td>
                      <Td>
                        <VStack align="start" spacing={0}>
                          <Badge colorScheme="blue" fontSize="xs">{prompt.schedule_type}</Badge>
                          <Text fontSize="xs" color={secondaryTextColor}>{t('scheduledPosts.time').toLowerCase()} {prompt.schedule_time}</Text>
                        </VStack>
                      </Td>
                      <Td><Text fontSize="sm">{prompt.next_run ? new Date(prompt.next_run).toLocaleString() : 'N/A'}</Text></Td>
                      <Td>{prompt.auto_post ? <Badge colorScheme="green" fontSize="xs">{t('scheduledPosts.autoPost')}</Badge> : <Badge colorScheme="gray" fontSize="xs">{t('scheduledPosts.manual')}</Badge>}</Td>
                      <Td><Badge colorScheme={prompt.status === 'active' ? 'green' : 'gray'} fontSize="xs">{prompt.status === 'active' ? t('scheduledPosts.active') : t('scheduledPosts.paused')}</Badge></Td>
                      <Td>
                        <HStack spacing={0}>
                          <Tooltip label={t('scheduledPosts.edit')}><IconButton size="xs" icon={<FaEdit />} onClick={() => openEditPrompt(prompt)} colorScheme="blue" variant="ghost" aria-label={t('scheduledPosts.edit')} /></Tooltip>
                          <Tooltip label={prompt.status === 'active' ? t('scheduledPosts.pause') : t('scheduledPosts.activate')}><IconButton size="xs" icon={prompt.status === 'active' ? <FaToggleOn /> : <FaToggleOff />} onClick={() => toggleScheduledPrompt(prompt.id)} colorScheme={prompt.status === 'active' ? 'green' : 'gray'} aria-label={prompt.status === 'active' ? t('scheduledPosts.pause') : t('scheduledPosts.activate')} /></Tooltip>
                          <Tooltip label={t('scheduledPosts.delete')}><IconButton size="xs" icon={<FaTrash />} onClick={() => deleteScheduledPrompt(prompt.id)} colorScheme="red" variant="ghost" aria-label={t('scheduledPosts.delete')} /></Tooltip>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}
        </CardBody>
      </Card>
        </>
      )}

      {/* Post to Social Modal - REUSED from PostToSocialModal component */}
      {postToPublish && (
        <PostToSocialModal
          isOpen={isPostSocialOpen}
          onClose={() => { onPostSocialClose(); setPostToPublish(null); }}
          content={postToPublish.content}
          userId={user?.id}
          imageBase64={postToPublish.image_base64}
          imageMimeType={postToPublish.image_mime_type || 'image/png'}
          onPostSuccess={() => {
            loadScheduledPosts(user?.id);
            if (updatePostCounts) updatePostCounts();
          }}
        />
      )}

      {/* Analysis Modal - REUSES useContentAnalyzer hook and AnalysisResults component */}
      <Modal isOpen={isAnalysisOpen} onClose={() => { onAnalysisClose(); setPostToAnalyze(null); resetAnalysis(); }} size="xl">
        <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
        <ModalContent bg={cardBg} maxW="800px">
          <ModalHeader>{t('scheduledPosts.contentAnalysis')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={4}>
            {postToAnalyze && (
              <VStack align="stretch" spacing={4}>
                <Box p={3} bg={modalContentBg} borderRadius="md">
                  <Text fontSize="sm" color={secondaryTextColor} mb={1}>{t('scheduledPosts.contentLabel')}</Text>
                  <Text fontSize="sm" whiteSpace="pre-wrap">{postToAnalyze.content}</Text>
                </Box>
                
                {analyzing ? (
                  <Center py={8}>
                    <VStack>
                      <Spinner size="lg" color="brand.500" />
                      <Text color={secondaryTextColor}>{t('scheduledPosts.analyzingContent')}</Text>
                    </VStack>
                  </Center>
                ) : analysis ? (
                  <AnalysisResults analysis={analysis} title={t('scheduledPosts.analysisResults')} compact={true} />
                ) : null}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => { onAnalysisClose(); setPostToAnalyze(null); resetAnalysis(); }}>{t('scheduledPosts.close')}</Button>
            {analysis && <Button colorScheme="blue" leftIcon={<FaSearchPlus />} onClick={() => { handleOpenInAnalyze(postToAnalyze); onAnalysisClose(); }}>{t('scheduledPosts.openInFullAnalyzer')}</Button>}
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Scheduled Post Modal - Uses PlatformSelector with connected accounts */}
      <Modal isOpen={isEditPostOpen} onClose={onEditPostClose} size="lg">
        <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
        <ModalContent bg={cardBg}>
          <ModalHeader>{t('scheduledPosts.editScheduledPost')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={4}>
            {editingPost && (
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>{t('scheduledPosts.content')}</FormLabel>
                  <Textarea value={editingPost.content} onChange={(e) => setEditingPost({...editingPost, content: e.target.value})} minH="120px" />
                </FormControl>
                <Grid templateColumns="1fr 1fr" gap={4}>
                  <FormControl>
                    <FormLabel>{t('scheduledPosts.scheduleDate')}</FormLabel>
                    <Input type="date" value={editingPost.scheduleDate} onChange={(e) => setEditingPost({...editingPost, scheduleDate: e.target.value})} min={new Date().toISOString().split('T')[0]} />
                  </FormControl>
                  <FormControl>
                    <FormLabel>{t('scheduledPosts.scheduleTime')}</FormLabel>
                    <Input type="time" value={editingPost.scheduleTime} onChange={(e) => setEditingPost({...editingPost, scheduleTime: e.target.value})} />
                  </FormControl>
                </Grid>
                <FormControl>
                  <FormLabel>{t('scheduledPosts.platformsConnectedOnly')}</FormLabel>
                  <PlatformSelector connectedPlatforms={connectedPlatforms} selectedPlatforms={editingPost.platforms} onChange={(platforms) => setEditingPost({...editingPost, platforms})} />
                </FormControl>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditPostClose}>{t('scheduledPosts.cancel')}</Button>
            <Button colorScheme="brand" onClick={saveEditedPost}>{t('scheduledPosts.saveChanges')}</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Scheduled Prompt Modal - Uses PlatformSelector with connected accounts */}
      <Modal isOpen={isEditPromptOpen} onClose={onEditPromptClose} size="lg">
        <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
        <ModalContent bg={cardBg}>
          <ModalHeader>{t('scheduledPosts.editScheduledPrompt')}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={4}>
            {editingPrompt && (
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>{t('scheduledPosts.prompt')}</FormLabel>
                  <Textarea value={editingPrompt.prompt} onChange={(e) => setEditingPrompt({...editingPrompt, prompt: e.target.value})} minH="100px" />
                </FormControl>
                <Grid templateColumns="1fr 1fr" gap={4}>
                  <FormControl>
                    <FormLabel>{t('scheduledPosts.scheduleType')}</FormLabel>
                    <Input value={editingPrompt.schedule_type} isReadOnly />
                  </FormControl>
                  <FormControl>
                    <FormLabel>{t('scheduledPosts.time')}</FormLabel>
                    <Input type="time" value={editingPrompt.schedule_time} onChange={(e) => setEditingPrompt({...editingPrompt, schedule_time: e.target.value})} />
                  </FormControl>
                </Grid>
                <Checkbox isChecked={editingPrompt.auto_post} onChange={(e) => setEditingPrompt({...editingPrompt, auto_post: e.target.checked, platforms: e.target.checked ? editingPrompt.platforms : []})}>{t('scheduledPosts.autoPostToSocial')}</Checkbox>
                {editingPrompt.auto_post && (
                  <FormControl>
                    <FormLabel>{t('scheduledPosts.selectPlatformsConnectedOnly')}</FormLabel>
                    <PlatformSelector connectedPlatforms={connectedPlatforms} selectedPlatforms={editingPrompt.platforms} onChange={(platforms) => setEditingPrompt({...editingPrompt, platforms})} />
                  </FormControl>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditPromptClose}>{t('scheduledPosts.cancel')}</Button>
            <Button colorScheme="brand" onClick={saveEditedPrompt}>{t('scheduledPosts.saveChanges')}</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Error Details Modal */}
      <Modal isOpen={isErrorOpen} onClose={onErrorClose} size="md">
        <ModalOverlay bg="blackAlpha.600" />
        <ModalContent bg={cardBg}>
          <ModalHeader color="red.500">
            <HStack>
              <Icon as={FaExclamationTriangle} />
              <Text>{t('scheduledPosts.postFailed')}</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={4}>
            {selectedError && (
              <VStack spacing={4} align="stretch">
                <Box>
                  <Text fontWeight="600" mb={1}>{t('scheduledPosts.errorMessage')}</Text>
                  <Box bg="red.50" _dark={{ bg: 'red.900' }} p={3} borderRadius="md" borderLeft="4px solid" borderColor="red.500">
                    <Text color="red.700" _dark={{ color: 'red.200' }}>{selectedError.error}</Text>
                  </Box>
                </Box>
                {selectedError.failedAt && (
                  <Box>
                    <Text fontWeight="600" mb={1}>{t('scheduledPosts.failedAt')}</Text>
                    <Text>{new Date(selectedError.failedAt).toLocaleString()}</Text>
                  </Box>
                )}
                {selectedError.platforms && selectedError.platforms.length > 0 && (
                  <Box>
                    <Text fontWeight="600" mb={1}>{t('scheduledPosts.targetPlatforms')}</Text>
                    <HStack>
                      {selectedError.platforms.map(p => (
                        <Badge key={p} colorScheme="gray">{p}</Badge>
                      ))}
                    </HStack>
                  </Box>
                )}
                <Box>
                  <Text fontWeight="600" mb={1}>{t('scheduledPosts.postContent')}</Text>
                  <Box bg="gray.50" _dark={{ bg: 'gray.700' }} p={3} borderRadius="md" maxH="150px" overflow="auto">
                    <Text fontSize="sm">{selectedError.content}</Text>
                  </Box>
                </Box>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={() => { onErrorClose(); /* Could add retry logic here */ }}>
              {t('scheduledPosts.tryAgain')}
            </Button>
            <Button variant="ghost" onClick={onErrorClose}>{t('scheduledPosts.close')}</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Note: Rejection Modal moved to AllPostsTab */}
    </Box>
  );
}
