'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  useDisclosure,
  VStack,
  Select,
  Tooltip,
  useToast,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  AlertDescription,
  Tabs,
  TabList,
  Tab,
  ModalFooter,
  Textarea,
} from '@chakra-ui/react';
import { FaFacebookF, FaInstagram, FaLinkedinIn, FaYoutube, FaTwitter, FaTrash, FaEye, FaSync, FaRedo, FaEdit, FaFileAlt, FaHeart, FaComment, FaShare, FaChartLine, FaPaperPlane, FaExclamationTriangle, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import { FolderKanban, Unlink } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { getApiUrl, createAuthenticatedAxios } from '@/lib/api';
import axios from 'axios';
// Import shared components
import { StatusBadge, ScoreBadge, EmptyState, DeleteConfirmationModal } from '@/components/shared';
// Import workspace context
import { useWorkspace } from '@/context/WorkspaceContext';

export default function AllPostsTab({ user, updatePostCounts }) {
  const { t } = useTranslation();
  const { currentWorkspace, isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  const [posts, setPosts] = useState([]);
  const [filteredPosts, setFilteredPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all'); // New status filter
  const [projectFilter, setProjectFilter] = useState('all'); // Project filter
  const [reanalyzeLoading, setReanalyzeLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [engagementData, setEngagementData] = useState({});
  const [engagementLoading, setEngagementLoading] = useState(false);
  const [hasConnections, setHasConnections] = useState(false);
  const [userPermissions, setUserPermissions] = useState(null);
  const [rejectedPosts, setRejectedPosts] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]); // Posts pending Manager approval
  const [approvedPosts, setApprovedPosts] = useState([]); // Approved posts ready to publish
  const [submittingPostId, setSubmittingPostId] = useState(null);
  const [deletePostId, setDeletePostId] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [projects, setProjects] = useState([]); // Available projects
  const [assigningPostId, setAssigningPostId] = useState(null); // Post being assigned
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isAssignOpen, onOpen: onAssignOpen, onClose: onAssignClose } = useDisclosure();
  const { isOpen: isChangesOpen, onOpen: onChangesOpen, onClose: onChangesClose } = useDisclosure();
  const { isOpen: isRejectOpen, onOpen: onRejectOpen, onClose: onRejectClose } = useDisclosure();
  const [selectedAssignProjectId, setSelectedAssignProjectId] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [approvalLoading, setApprovalLoading] = useState(null);
  const [rejectingPost, setRejectingPost] = useState(null);
  const router = useRouter();
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const secondaryTextColor = useColorModeValue('gray.600', 'gray.400');
  const modalContentBg = useColorModeValue('gray.50', 'gray.700');
  const iconColor = useColorModeValue('gray.600', 'gray.400');
  const rejectedBg = useColorModeValue('red.50', 'red.900');
  const pendingBg = useColorModeValue('orange.50', 'orange.900');
  const approvedBg = useColorModeValue('green.50', 'green.900');

  useEffect(() => {
    if (user?.id) {
      loadPosts(user.id);
      loadUserPermissions();
      loadRejectedPosts();
      loadProjects(); // Load projects
    }
  }, [user, currentWorkspace]); // Reload when workspace changes

  // Load pending approvals and approved posts when permissions are available
  useEffect(() => {
    if (user?.id && userPermissions?.can_view_pending) {
      loadPendingApprovals();
      loadApprovedPosts();
    }
  }, [user, userPermissions]);

  // Load pending approvals for Managers
  const loadPendingApprovals = async () => {
    if (!user?.id || !userPermissions?.can_view_pending) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/approval/pending`, {
        headers: { 'X-User-ID': user.id }
      });
      setPendingApprovals(response.data.posts || []);
    } catch (error) {
      console.error('Failed to load pending approvals:', error);
    }
  };

  // Load approved posts for Managers
  const loadApprovedPosts = async () => {
    if (!user?.id || !userPermissions?.can_view_pending) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/approval/approved`, {
        headers: { 'X-User-ID': user.id }
      });
      setApprovedPosts(response.data.posts || []);
    } catch (error) {
      console.error('Failed to load approved posts:', error);
    }
  };

  // Open reject modal for Manager approval workflow
  const openRejectModal = (post) => {
    setRejectingPost(post);
    setRejectReason('');
    onRejectOpen();
  };

  // Load available projects
  const loadProjects = async () => {
    if (!user?.id) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/projects`, {
        headers: { 'X-User-ID': user.id }
      });
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  // Assign post to project
  const handleAssignToProject = async () => {
    if (!assigningPostId || !selectedAssignProjectId) return;
    
    try {
      const API = getApiUrl();
      await axios.post(
        `${API}/projects/${selectedAssignProjectId}/content`,
        {
          content_id: assigningPostId,
          content_type: 'post'
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Success',
        description: 'Post assigned to project',
        status: 'success',
        duration: 3000,
      });
      
      onAssignClose();
      setAssigningPostId(null);
      setSelectedAssignProjectId('');
      loadPosts(user.id); // Reload to show updated project
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to assign post',
        status: 'error',
        duration: 3000,
      });
    }
  };

  // Remove post from project
  const handleRemoveFromProject = async (postId, projectId) => {
    try {
      const API = getApiUrl();
      await axios.delete(
        `${API}/projects/${projectId}/content/${postId}?content_type=post`,
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Success',
        description: 'Post removed from project',
        status: 'success',
        duration: 3000,
      });
      
      loadPosts(user.id);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to remove post from project',
        status: 'error',
        duration: 3000,
      });
    }
  };

  useEffect(() => {
    let filtered = posts;
    
    // Apply source filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(post => post.source === sourceFilter);
    }
    
    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(post => post.status === statusFilter);
    }
    
    // Apply project filter
    if (projectFilter !== 'all') {
      if (projectFilter === 'unassigned') {
        filtered = filtered.filter(post => !post.project_id);
      } else {
        filtered = filtered.filter(post => post.project_id === projectFilter);
      }
    }
    
    setFilteredPosts(filtered);
  }, [posts, sourceFilter, statusFilter, projectFilter]);

  // Load user permissions for approval workflow
  const loadUserPermissions = async () => {
    if (!user?.id) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/approval/user-permissions`, {
        headers: { 'X-User-ID': user.id }
      });
      setUserPermissions(response.data.permissions);
    } catch (error) {
      console.error('Failed to load user permissions:', error);
    }
  };

  // Load rejected posts for Creator users
  const loadRejectedPosts = async () => {
    if (!user?.id) return;
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/approval/rejected`, {
        headers: { 'X-User-ID': user.id }
      });
      setRejectedPosts(response.data.posts || []);
    } catch (error) {
      console.error('Failed to load rejected posts:', error);
    }
  };

  // Submit post for re-approval (after revision)
  const handleResubmit = async (postId) => {
    setSubmittingPostId(postId);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/approval/submit/${postId}`, {}, {
        headers: { 'X-User-ID': user?.id }
      });
      
      toast({
        title: t('allPosts.toasts.resubmitted'),
        description: t('allPosts.toasts.resubmittedDesc'),
        status: 'success',
        duration: 5000,
      });
      
      loadRejectedPosts();
      loadPosts(user.id);
    } catch (error) {
      toast({
        title: t('allPosts.toasts.resubmitFailed'),
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSubmittingPostId(null);
    }
  };

  // Approve a post (for managers/admins)
  const handleApprove = async (postId) => {
    setApprovalLoading(postId);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/approval/${postId}/approve`, {}, {
        headers: { 'X-User-ID': user?.id }
      });
      
      toast({
        title: 'Content Approved!',
        description: 'The content has been approved and can now be published.',
        status: 'success',
        duration: 4000,
      });
      
      // Refresh posts and pending approvals
      loadPosts(user.id);
      loadPendingApprovals();
      loadApprovedPosts();
    } catch (error) {
      toast({
        title: 'Failed to approve',
        description: error.response?.data?.detail || 'An error occurred',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setApprovalLoading(null);
    }
  };

  // Reject a post from Manager approval workflow
  const handleRejectPost = async () => {
    if (!rejectingPost || !rejectReason.trim()) {
      toast({
        title: 'Please provide feedback',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setApprovalLoading(rejectingPost.id);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/approval/${rejectingPost.id}/reject`, {
        reason: rejectReason
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      toast({
        title: 'Post Rejected',
        description: 'The creator has been notified with your feedback.',
        status: 'info',
        duration: 4000,
      });
      
      onRejectClose();
      setRejectingPost(null);
      setRejectReason('');
      
      // Refresh posts and pending approvals
      loadPosts(user.id);
      loadPendingApprovals();
    } catch (error) {
      toast({
        title: 'Failed to reject',
        description: error.response?.data?.detail || 'An error occurred',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setApprovalLoading(null);
    }
  };

  // Open Request Changes modal
  const openRequestChangesModal = (post) => {
    setSelectedPost(post);
    setRejectReason('');
    onChangesOpen();
  };

  // Submit Request Changes
  const handleRequestChanges = async () => {
    if (!selectedPost || !rejectReason.trim()) {
      toast({
        title: 'Please provide feedback',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setApprovalLoading(selectedPost.id);
    try {
      const API = getApiUrl();
      await axios.post(`${API}/approval/${selectedPost.id}/reject`, {
        reason: rejectReason
      }, {
        headers: { 'X-User-ID': user?.id }
      });
      
      toast({
        title: 'Changes Requested',
        description: 'The creator has been notified and will revise the content.',
        status: 'info',
        duration: 4000,
      });
      
      // Refresh posts and close modal
      loadPosts(user.id);
      onChangesClose();
      setSelectedPost(null);
      setRejectReason('');
    } catch (error) {
      toast({
        title: 'Failed to request changes',
        description: error.response?.data?.detail || 'An error occurred',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setApprovalLoading(null);
    }
  };

  const loadPosts = async (userId) => {
    setLoading(true);
    try {
      const axiosInstance = createAuthenticatedAxios();
      // Build query params based on workspace context
      const params = new URLSearchParams();
      params.append('workspace', isEnterpriseWorkspace ? 'enterprise' : 'personal');
      if (isEnterpriseWorkspace && enterpriseInfo?.id) {
        params.append('enterprise_id', enterpriseInfo.id);
      }
      
      const response = await axiosInstance.get(`/posts?${params.toString()}`);
      setPosts(response.data);
      if (updatePostCounts) {
        updatePostCounts(prev => ({ ...prev, all: response.data.length }));
      }
      // Load engagement data
      loadEngagementData();
    } catch (error) {
      console.error('Failed to load posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEngagementData = async () => {
    try {
      const axiosInstance = createAuthenticatedAxios();
      const response = await axiosInstance.get('/social-media/engagement/bulk');
      const engagementMap = {};
      response.data.posts?.forEach(item => {
        engagementMap[item.post_id] = item.engagement;
      });
      setEngagementData(engagementMap);
      setHasConnections(response.data.has_connections);
    } catch (error) {
      console.error('Failed to load engagement data:', error);
    }
  };

  const syncEngagement = async () => {
    setEngagementLoading(true);
    try {
      const axiosInstance = createAuthenticatedAxios();
      const response = await axiosInstance.post('/social-media/engagement/sync');
      
      if (response.data.status === 'no_connections') {
        toast({
          title: t('allPosts.toasts.noAccountsConnected'),
          description: t('allPosts.toasts.connectSocialAccountsDesc'),
          status: 'info',
          duration: 5000,
        });
      } else {
        toast({
          title: t('allPosts.toasts.engagementSynced'),
          description: response.data.message,
          status: 'success',
          duration: 3000,
        });
        loadEngagementData();
      }
    } catch (error) {
      toast({
        title: t('allPosts.toasts.syncFailed'),
        description: error.response?.data?.detail || t('allPosts.toasts.failedToSync'),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setEngagementLoading(false);
    }
  };

  const reanalyzeAllPosts = async () => {
    if (!user) return;
    if (!confirm(t('allPosts.confirmReanalyze'))) return;
    
    setReanalyzeLoading(true);
    try {
      const axiosInstance = createAuthenticatedAxios();
      const response = await axiosInstance.post('/posts/reanalyze-all');
      toast({
        title: t('allPosts.toasts.reanalysisComplete'),
        description: response.data.message,
        status: 'success',
        duration: 5000,
      });
      loadPosts(user.id);
    } catch (error) {
      toast({
        title: t('allPosts.toasts.reanalysisFailed'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setReanalyzeLoading(false);
    }
  };

  const reanalyzeSinglePost = async (postId) => {
    try {
      const axiosInstance = createAuthenticatedAxios();
      await axiosInstance.post(`/posts/${postId}/reanalyze`);
      toast({ title: t('allPosts.toasts.postReanalyzed'), status: 'success', duration: 2000 });
      loadPosts(user.id);
    } catch (error) {
      toast({ title: t('allPosts.toasts.reanalysisFailed'), status: 'error', duration: 3000 });
    }
  };

  const deletePost = async (postId) => {
    setDeleteLoading(true);
    try {
      const axiosInstance = createAuthenticatedAxios();
      await axiosInstance.delete(`/posts/${postId}`);
      toast({ title: t('allPosts.toasts.postDeleted'), status: 'success', duration: 2000 });
      if (user) loadPosts(user.id);
      onDeleteClose();
    } catch (error) {
      toast({ title: t('allPosts.toasts.deleteFailed'), status: 'error', duration: 3000 });
    } finally {
      setDeleteLoading(false);
      setDeletePostId(null);
    }
  };

  const openDeleteModal = (postId) => {
    setDeletePostId(postId);
    onDeleteOpen();
  };

  const handleRewritePost = (post) => {
    const rewriteData = {
      post_id: post.id,
      original_content: post.content,
      is_update: true,
      platform: post.platform || 'general',
      post_status: post.status,
      created_at: post.created_at
    };
    localStorage.setItem('rewrite_post_data', JSON.stringify(rewriteData));
    router.push('/contentry/content-moderation?tab=analyze');
  };

  const getFlagColor = (status) => {
    const colors = {
      good_coverage: 'green',
      rude_and_abusive: 'red',
      contain_harassment: 'red',
      policy_violation: 'orange',
      pending: 'gray'
    };
    return colors[status] || 'gray';
  };

  // Get color for approval status
  const getApprovalStatusColor = (status) => {
    const colors = {
      draft: 'gray',
      pending_approval: 'orange',
      approved: 'green',
      rejected: 'red',
      scheduled: 'blue',
      published: 'blue'
    };
    return colors[status] || 'gray';
  };

  // Get label for approval status
  const getApprovalStatusLabel = (status) => {
    const key = `allPosts.approvalStatus.${status}`;
    const translated = t(key);
    // If translation key doesn't exist, return formatted status
    return translated !== key ? translated : (status || t('allPosts.approvalStatus.unknown'));
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      facebook: FaFacebookF,
      instagram: FaInstagram,
      linkedin: FaLinkedinIn,
      youtube: FaYoutube,
      twitter: FaTwitter
    };
    return icons[platform?.toLowerCase()] || FaFacebookF;
  };

  if (loading) {
    return (
      <Center py={12}>
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" />
          <Text color={textColor}>{t('allPosts.loadingPosts')}</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      {/* Needs Revision Alert for Creator Role */}
      {userPermissions?.needs_approval && rejectedPosts.length > 0 && (
        <Alert status="warning" mb={4} borderRadius="md">
          <AlertIcon as={FaExclamationTriangle} />
          <Box flex={1}>
            <AlertDescription>
              <strong>{rejectedPosts.length} {t('allPosts.needsRevisionAlert')}</strong> {t('allPosts.managerRequestedChanges')}
            </AlertDescription>
          </Box>
          <Button
            size="sm"
            colorScheme="orange"
            onClick={() => setStatusFilter('rejected')}
          >
            {t('allPosts.viewAll')}
          </Button>
        </Alert>
      )}

      {/* Action Buttons */}
      <Flex gap={3} mb={4} flexWrap="wrap">
        <Button
          leftIcon={<FaSync />}
          colorScheme="blue"
          variant="outline"
          onClick={reanalyzeAllPosts}
          isLoading={reanalyzeLoading}
          size="sm"
        >
          {t('allPosts.reanalyzeAll')}
        </Button>
        <Button
          leftIcon={<FaChartLine />}
          colorScheme="teal"
          variant="outline"
          onClick={syncEngagement}
          isLoading={engagementLoading}
          size="sm"
        >
          {t('allPosts.syncEngagement')}
        </Button>
      </Flex>

      {/* Status Filter Tabs (for Creator approval workflow) */}
      {userPermissions?.needs_approval && (
        <Tabs 
          variant="soft-rounded" 
          colorScheme="brand" 
          mb={4}
          index={['all', 'draft', 'pending_approval', 'rejected', 'approved'].indexOf(statusFilter)}
          onChange={(idx) => setStatusFilter(['all', 'draft', 'pending_approval', 'rejected', 'approved'][idx])}
        >
          <TabList flexWrap="wrap" gap={1}>
            <Tab fontSize="xs">{t('allPosts.all')}</Tab>
            <Tab fontSize="xs">{t('allPosts.drafts')}</Tab>
            <Tab fontSize="xs">{t('allPosts.pending')}</Tab>
            <Tab fontSize="xs">
              {t('allPosts.needsRevision')}
              {rejectedPosts.length > 0 && (
                <Badge ml={1} colorScheme="red" fontSize="2xs">{rejectedPosts.length}</Badge>
              )}
            </Tab>
            <Tab fontSize="xs">{t('allPosts.approved')}</Tab>
          </TabList>
        </Tabs>
      )}

      {/* Status Filter Tabs (for Manager/Admin approval workflow) */}
      {userPermissions?.can_view_pending && !userPermissions?.needs_approval && (
        <Tabs 
          variant="soft-rounded" 
          colorScheme="brand" 
          mb={4}
          index={['all', 'pending_review', 'approved_ready', 'published'].indexOf(statusFilter)}
          onChange={(idx) => setStatusFilter(['all', 'pending_review', 'approved_ready', 'published'][idx])}
        >
          <TabList flexWrap="wrap" gap={1}>
            <Tab fontSize="xs">{t('allPosts.all')}</Tab>
            <Tab fontSize="xs">
              Pending Review
              {pendingApprovals.length > 0 && (
                <Badge ml={1} colorScheme="orange" fontSize="2xs">{pendingApprovals.length}</Badge>
              )}
            </Tab>
            <Tab fontSize="xs">
              Ready to Publish
              {approvedPosts.length > 0 && (
                <Badge ml={1} colorScheme="green" fontSize="2xs">{approvedPosts.length}</Badge>
              )}
            </Tab>
            <Tab fontSize="xs">Published</Tab>
          </TabList>
        </Tabs>
      )}

      {/* Pending Approvals Section (for Managers viewing pending_review filter) */}
      {userPermissions?.can_view_pending && statusFilter === 'pending_review' && pendingApprovals.length > 0 && (
        <Card bg={pendingBg} mb={4} borderWidth="2px" borderColor="orange.300">
          <CardBody p={4}>
            <HStack mb={4} spacing={2}>
              <Icon as={FaExclamationTriangle} color="orange.500" />
              <Text fontSize="lg" fontWeight="600" color={textColor}>
                Posts Pending Approval ({pendingApprovals.length})
              </Text>
              <Badge colorScheme="orange">Action Required</Badge>
            </HStack>
            <Text fontSize="sm" color={secondaryTextColor} mb={4}>
              Review and approve content submitted by team members before it can be published.
            </Text>
            
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Content</Th>
                    <Th>Submitted By</Th>
                    <Th>Submitted At</Th>
                    <Th width="200px">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {pendingApprovals.map((post) => (
                    <Tr key={post.id}>
                      <Td maxW="300px">
                        <Text noOfLines={2} fontSize="sm">{post.content}</Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm">{post.submitter?.full_name || 'Unknown'}</Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm" color={secondaryTextColor}>
                          {post.submitted_at ? new Date(post.submitted_at).toLocaleDateString() : '-'}
                        </Text>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          <Button
                            size="xs"
                            colorScheme="green"
                            leftIcon={<FaCheckCircle />}
                            onClick={() => handleApprove(post.id)}
                            isLoading={approvalLoading === post.id}
                          >
                            Approve
                          </Button>
                          <Button
                            size="xs"
                            colorScheme="red"
                            leftIcon={<FaTimesCircle />}
                            onClick={() => openRejectModal(post)}
                          >
                            Reject
                          </Button>
                          <Tooltip label="View Details">
                            <Button
                              size="xs"
                              variant="ghost"
                              onClick={() => { setSelectedPost(post); onOpen(); }}
                            >
                              <FaEye />
                            </Button>
                          </Tooltip>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          </CardBody>
        </Card>
      )}

      {/* Approved Posts Section (for Managers viewing approved_ready filter) */}
      {userPermissions?.can_view_pending && statusFilter === 'approved_ready' && approvedPosts.length > 0 && (
        <Card bg={approvedBg} mb={4} borderWidth="2px" borderColor="green.300">
          <CardBody p={4}>
            <HStack mb={4} spacing={2}>
              <Icon as={FaCheckCircle} color="green.500" />
              <Text fontSize="lg" fontWeight="600" color={textColor}>
                Approved & Ready to Publish ({approvedPosts.length})
              </Text>
              <Badge colorScheme="green">Ready</Badge>
            </HStack>
            <Text fontSize="sm" color={secondaryTextColor} mb={4}>
              These posts have been approved and are ready to be scheduled or published.
            </Text>
            
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Content</Th>
                    <Th>Created By</Th>
                    <Th>Approved At</Th>
                    <Th width="150px">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {approvedPosts.map((post) => (
                    <Tr key={post.id}>
                      <Td maxW="300px">
                        <Text noOfLines={2} fontSize="sm">{post.content}</Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm">{post.submitter?.full_name || 'Unknown'}</Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm" color={secondaryTextColor}>
                          {post.approved_at ? new Date(post.approved_at).toLocaleDateString() : '-'}
                        </Text>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          <Tooltip label="View Details">
                            <Button
                              size="xs"
                              variant="ghost"
                              onClick={() => { setSelectedPost(post); onOpen(); }}
                            >
                              <FaEye />
                            </Button>
                          </Tooltip>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          </CardBody>
        </Card>
      )}

      {/* Filter */}
      <Card bg={cardBg} mb={4}>
        <CardBody p={4}>
          <Flex gap={4} align="center" flexWrap="wrap">
            <Text fontWeight="600" fontSize="sm" color={textColor}>{t('allPosts.source')}:</Text>
            <Select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              w="200px"
              size="sm"
            >
              <option value="all">{t('allPosts.all')} ({posts.length})</option>
              <option value="contentry">{t('allPosts.contentry')} ({posts.filter(p => p.source === 'contentry').length})</option>
              <option value="imported">{t('allPosts.imported')} ({posts.filter(p => p.source === 'imported').length})</option>
            </Select>
            
            {/* Project Filter */}
            {projects.length > 0 && (
              <>
                <Text fontWeight="600" fontSize="sm" color={textColor}>Project:</Text>
                <Select
                  value={projectFilter}
                  onChange={(e) => setProjectFilter(e.target.value)}
                  w="200px"
                  size="sm"
                >
                  <option value="all">All Projects</option>
                  <option value="unassigned">Unassigned ({posts.filter(p => !p.project_id).length})</option>
                  {projects.map(project => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.name} ({posts.filter(p => p.project_id === project.project_id).length})
                    </option>
                  ))}
                </Select>
              </>
            )}
          </Flex>

          {/* Rejection Details Card (shows when filtered to rejected) */}
          {statusFilter === 'rejected' && rejectedPosts.length > 0 && (
            <Box mt={4}>
              <Text fontWeight="600" fontSize="sm" color={textColor} mb={2}>
                {t('allPosts.postsNeedingRevision')}
              </Text>
              <VStack spacing={3} align="stretch">
                {rejectedPosts.map((post) => (
                  <Card key={post.id} bg={rejectedBg} size="sm">
                    <CardBody p={3}>
                      <Flex justify="space-between" align="start" gap={3}>
                        <Box flex={1}>
                          <Text fontSize="sm" noOfLines={2} fontWeight="500">{post.content}</Text>
                          <Box mt={2} p={2} bg="white" _dark={{ bg: 'gray.700' }} borderRadius="md" borderLeft="3px solid" borderLeftColor="red.500">
                            <Text fontSize="xs" color="red.600" _dark={{ color: 'red.300' }} fontWeight="600">
                              {t('allPosts.managerFeedback')}
                            </Text>
                            <Text fontSize="xs" color={secondaryTextColor}>
                              {post.rejection_reason || t('allPosts.noFeedbackProvided')}
                            </Text>
                            {post.rejector?.full_name && (
                              <Text fontSize="xs" color={secondaryTextColor} mt={1}>
                                — {post.rejector.full_name}
                              </Text>
                            )}
                          </Box>
                        </Box>
                        <VStack spacing={1}>
                          <Tooltip label={t('allPosts.editAndRevise')}>
                            <Button size="xs" colorScheme="blue" leftIcon={<FaEdit />} onClick={() => handleRewritePost(post)}>
                              {t('allPosts.revise')}
                            </Button>
                          </Tooltip>
                          <Tooltip label={t('allPosts.resubmitForApproval')}>
                            <Button 
                              size="xs" 
                              colorScheme="orange" 
                              leftIcon={<FaPaperPlane />}
                              onClick={() => handleResubmit(post.id)}
                              isLoading={submittingPostId === post.id}
                            >
                              {t('allPosts.resubmit')}
                            </Button>
                          </Tooltip>
                        </VStack>
                      </Flex>
                    </CardBody>
                  </Card>
                ))}
              </VStack>
            </Box>
          )}

          {/* Posts Table */}
          {statusFilter !== 'rejected' && (
          <Box overflowX="auto" mt={4}>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>{t('allPosts.source')}</Th>
                  <Th>{t('allPosts.post')}</Th>
                  <Th>{t('allPosts.analysis')}</Th>
                  {userPermissions?.needs_approval && <Th>{t('allPosts.approval')}</Th>}
                  <Th display={{ base: 'none', lg: 'table-cell' }}>{t('allPosts.scores')}</Th>
                  <Th display={{ base: 'none', xl: 'table-cell' }}>
                    <Tooltip label={hasConnections ? t('allPosts.engagementMetrics') : t('allPosts.connectSocialToView')}>
                      <HStack spacing={1} cursor="help">
                        <Icon as={FaHeart} color="pink.400" boxSize={3} />
                        <Icon as={FaComment} color="blue.400" boxSize={3} />
                        <Icon as={FaShare} color="green.400" boxSize={3} />
                      </HStack>
                    </Tooltip>
                  </Th>
                  <Th display={{ base: 'none', md: 'table-cell' }}>{t('allPosts.platform')}</Th>
                  <Th display={{ base: 'none', sm: 'table-cell' }}>{t('allPosts.date')}</Th>
                  <Th>{t('allPosts.actions')}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredPosts.map((post) => {
                  const engagement = engagementData[post.id] || {};
                  return (
                  <Tr key={post.id} bg={post.status === 'rejected' ? rejectedBg : 'transparent'}>
                    <Td>
                      <VStack spacing={1} align="start">
                        <Badge colorScheme={post.source === 'contentry' ? 'blue' : 'cyan'} fontSize="xs">
                          {post.source === 'contentry' ? 'Contentry' : 'Imported'}
                        </Badge>
                        {/* Workspace indicator */}
                        {post.enterprise_id && (
                          <Tooltip label="Company Post">
                            <Badge colorScheme="purple" fontSize="2xs" variant="subtle">
                              Company
                            </Badge>
                          </Tooltip>
                        )}
                      </VStack>
                    </Td>
                    <Td maxW="200px">
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" noOfLines={2}>{post.content}</Text>
                        {post.project_id && (
                          <Tooltip label={`Assigned to: ${projects.find(p => p.project_id === post.project_id)?.name || 'Project'}`}>
                            <Badge colorScheme="teal" fontSize="2xs" variant="subtle">
                              <HStack spacing={1}>
                                <FolderKanban size={10} />
                                <Text>{projects.find(p => p.project_id === post.project_id)?.name?.slice(0, 15) || 'Project'}...</Text>
                              </HStack>
                            </Badge>
                          </Tooltip>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Badge colorScheme={getFlagColor(post.flagged_status)} fontSize="xs">
                        {(post.flagged_status || 'pending').replace(/_/g, ' ')}
                      </Badge>
                    </Td>
                    {userPermissions?.needs_approval && (
                      <Td>
                        <Badge colorScheme={getApprovalStatusColor(post.status)} fontSize="xs">
                          {getApprovalStatusLabel(post.status)}
                        </Badge>
                      </Td>
                    )}
                    <Td display={{ base: 'none', lg: 'table-cell' }}>
                      <HStack spacing={1} flexWrap="wrap">
                        <Tooltip label={t('allPosts.overallScore')}>
                          <Badge colorScheme={post.overall_score >= 75 ? 'green' : post.overall_score >= 50 ? 'yellow' : 'red'} fontSize="2xs">
                            O:{post.overall_score || '—'}
                          </Badge>
                        </Tooltip>
                        <Tooltip label={t('allPosts.accuracyScore')}>
                          <Badge colorScheme={post.accuracy_score >= 75 ? 'blue' : post.accuracy_score >= 50 ? 'yellow' : 'red'} fontSize="2xs" variant="outline">
                            A:{post.accuracy_score || '—'}
                          </Badge>
                        </Tooltip>
                        <Tooltip label={t('allPosts.complianceScore')}>
                          <Badge colorScheme={post.compliance_score >= 75 ? 'green' : post.compliance_score >= 50 ? 'yellow' : 'red'} fontSize="2xs" variant="outline">
                            C:{post.compliance_score || '—'}
                          </Badge>
                        </Tooltip>
                        <Tooltip label={t('allPosts.culturalSensitivityScore')}>
                          <Badge colorScheme={post.cultural_sensitivity_score >= 75 ? 'blue' : post.cultural_sensitivity_score >= 50 ? 'yellow' : 'red'} fontSize="2xs" variant="outline">
                            Cu:{post.cultural_sensitivity_score || '—'}
                          </Badge>
                        </Tooltip>
                      </HStack>
                    </Td>
                    <Td display={{ base: 'none', xl: 'table-cell' }}>
                      <HStack spacing={2}>
                        <Tooltip label={t('allPosts.likes')}>
                          <HStack spacing={1}>
                            <Icon as={FaHeart} color="pink.400" boxSize={3} />
                            <Text fontSize="xs" color={secondaryTextColor}>
                              {engagement.likes !== null && engagement.likes !== undefined ? engagement.likes : '—'}
                            </Text>
                          </HStack>
                        </Tooltip>
                        <Tooltip label={t('allPosts.comments')}>
                          <HStack spacing={1}>
                            <Icon as={FaComment} color="blue.400" boxSize={3} />
                            <Text fontSize="xs" color={secondaryTextColor}>
                              {engagement.comments !== null && engagement.comments !== undefined ? engagement.comments : '—'}
                            </Text>
                          </HStack>
                        </Tooltip>
                        <Tooltip label={t('allPosts.shares')}>
                          <HStack spacing={1}>
                            <Icon as={FaShare} color="green.400" boxSize={3} />
                            <Text fontSize="xs" color={secondaryTextColor}>
                              {engagement.shares !== null && engagement.shares !== undefined ? engagement.shares : '—'}
                            </Text>
                          </HStack>
                        </Tooltip>
                      </HStack>
                    </Td>
                    <Td display={{ base: 'none', md: 'table-cell' }}>
                      <HStack>
                        {(post.platforms || []).slice(0, 3).map(platform => {
                          const IconComp = getPlatformIcon(platform);
                          return <Icon key={platform} as={IconComp} color={iconColor} boxSize={4} />;
                        })}
                      </HStack>
                    </Td>
                    <Td display={{ base: 'none', sm: 'table-cell' }}>
                      <Text fontSize="xs" color={secondaryTextColor}>
                        {new Date(post.created_at).toLocaleDateString()}
                      </Text>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        <Tooltip label={t('allPosts.view')}>
                          <Button size="xs" colorScheme="blue" onClick={() => { setSelectedPost(post); onOpen(); }}>
                            <FaEye />
                          </Button>
                        </Tooltip>
                        <Tooltip label={t('allPosts.rewrite')}>
                          <Button size="xs" colorScheme="green" variant="outline" onClick={() => handleRewritePost(post)}>
                            <FaEdit />
                          </Button>
                        </Tooltip>
                        <Tooltip label={t('allPosts.reanalyze')}>
                          <Button size="xs" colorScheme="blue" variant="outline" onClick={() => reanalyzeSinglePost(post.id)}>
                            <FaRedo />
                          </Button>
                        </Tooltip>
                        {/* Assign/Remove from Project */}
                        {post.project_id ? (
                          <Tooltip label="Remove from project">
                            <Button 
                              size="xs" 
                              colorScheme="orange" 
                              variant="outline" 
                              onClick={() => handleRemoveFromProject(post.id, post.project_id)}
                            >
                              <Unlink size={12} />
                            </Button>
                          </Tooltip>
                        ) : projects.length > 0 && (
                          <Tooltip label="Assign to project">
                            <Button 
                              size="xs" 
                              colorScheme="teal" 
                              variant="outline" 
                              onClick={() => {
                                setAssigningPostId(post.id);
                                onAssignOpen();
                              }}
                            >
                              <FolderKanban size={12} />
                            </Button>
                          </Tooltip>
                        )}
                        {/* Approval Actions - Only for managers on pending_approval posts */}
                        {userPermissions?.can_approve_others && post.status === 'pending_approval' && (
                          <>
                            <Tooltip label="Approve">
                              <Button 
                                size="xs" 
                                colorScheme="green" 
                                onClick={() => handleApprove(post.id)}
                                isLoading={approvalLoading === post.id}
                              >
                                <FaCheckCircle />
                              </Button>
                            </Tooltip>
                            <Tooltip label="Request Changes">
                              <Button 
                                size="xs" 
                                colorScheme="orange" 
                                variant="outline"
                                onClick={() => openRequestChangesModal(post)}
                                isDisabled={approvalLoading === post.id}
                              >
                                <FaTimesCircle />
                              </Button>
                            </Tooltip>
                          </>
                        )}
                        <Tooltip label={t('allPosts.delete')}>
                          <Button size="xs" colorScheme="red" variant="ghost" onClick={() => openDeleteModal(post.id)}>
                            <FaTrash />
                          </Button>
                        </Tooltip>
                      </HStack>
                    </Td>
                  </Tr>
                  );
                })}
              </Tbody>
            </Table>

            {filteredPosts.length === 0 && (
              <Box textAlign="center" py={12} color={secondaryTextColor}>
                <Text fontSize="lg" fontWeight="600" mb={2}>{t('allPosts.noPostsFound')}</Text>
                <Text fontSize="sm">
                  {statusFilter !== 'all' 
                    ? `${t('allPosts.noPostsWithStatus')} "${getApprovalStatusLabel(statusFilter)}"`
                    : t('allPosts.createFirstPost')}
                </Text>
              </Box>
            )}
          </Box>
          )}
        </CardBody>
      </Card>

      {/* Post Detail Modal */}
      {selectedPost && (
        <Modal isOpen={isOpen} onClose={onClose} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>{t('allPosts.postDetails')}</ModalHeader>
            <ModalCloseButton />
            <ModalBody pb={6}>
              <VStack align="stretch" spacing={4}>
                <Box>
                  <Text fontSize="sm" color={secondaryTextColor} mb={1}>{t('allPosts.status')}</Text>
                  <Badge colorScheme={getFlagColor(selectedPost.flagged_status)}>
                    {(selectedPost.flagged_status || 'pending').replace(/_/g, ' ')}
                  </Badge>
                </Box>
                <Box>
                  <Text fontSize="sm" color={secondaryTextColor} mb={1}>{t('allPosts.content')}</Text>
                  <Box p={4} bg={modalContentBg} borderRadius="md" whiteSpace="pre-wrap">
                    {selectedPost.content}
                  </Box>
                </Box>
                {selectedPost.moderation_summary && (
                  <Box>
                    <Text fontSize="sm" color={secondaryTextColor} mb={1}>{t('allPosts.summary')}</Text>
                    <Box p={4} bg={modalContentBg} borderRadius="md">
                      {selectedPost.moderation_summary}
                    </Box>
                  </Box>
                )}
                <HStack>
                  <Button flex={1} size="sm" onClick={onClose}>{t('allPosts.close')}</Button>
                  <Button flex={1} size="sm" colorScheme="red" onClick={() => { onClose(); openDeleteModal(selectedPost.id); }}>{t('allPosts.delete')}</Button>
                </HStack>
              </VStack>
            </ModalBody>
          </ModalContent>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={isDeleteOpen}
        onClose={() => { onDeleteClose(); setDeletePostId(null); }}
        onConfirm={() => deletePost(deletePostId)}
        itemName={t('allPosts.thisPost', 'this post')}
        isLoading={deleteLoading}
      />

      {/* Assign to Project Modal */}
      <Modal isOpen={isAssignOpen} onClose={() => { onAssignClose(); setAssigningPostId(null); setSelectedAssignProjectId(''); }}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Assign to Project</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color={secondaryTextColor}>
                Select a project to assign this content to:
              </Text>
              <Select
                placeholder="Select a project"
                value={selectedAssignProjectId}
                onChange={(e) => setSelectedAssignProjectId(e.target.value)}
              >
                {projects.map(project => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </Select>
              <HStack spacing={3}>
                <Button flex={1} variant="outline" onClick={() => { onAssignClose(); setAssigningPostId(null); setSelectedAssignProjectId(''); }}>
                  Cancel
                </Button>
                <Button 
                  flex={1} 
                  colorScheme="brand" 
                  onClick={handleAssignToProject}
                  isDisabled={!selectedAssignProjectId}
                >
                  Assign
                </Button>
              </HStack>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Request Changes Modal */}
      <Modal isOpen={isChangesOpen} onClose={onChangesClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Request Changes</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text fontSize="sm" mb={3} color={secondaryTextColor}>
              Provide feedback for the content creator. They will be notified and can revise their content.
            </Text>
            <Text fontSize="sm" fontWeight="medium" mb={2}>
              Content preview:
            </Text>
            <Box 
              p={3} 
              bg={modalContentBg} 
              borderRadius="md" 
              mb={4}
              fontSize="sm"
            >
              {selectedPost?.content?.substring(0, 200)}
              {(selectedPost?.content?.length > 200) && '...'}
            </Box>
            <Text fontSize="sm" fontWeight="medium" mb={2}>
              Your feedback: <Text as="span" color="red.500">*</Text>
            </Text>
            <Textarea
              placeholder="Please explain what changes are needed..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onChangesClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="orange" 
              onClick={handleRequestChanges}
              isLoading={approvalLoading === selectedPost?.id}
              isDisabled={!rejectReason.trim()}
            >
              Request Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Reject Post Modal (for Manager approval workflow) */}
      <Modal isOpen={isRejectOpen} onClose={() => { onRejectClose(); setRejectingPost(null); setRejectReason(''); }} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Reject Post</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text mb={3} fontSize="sm" color={secondaryTextColor}>
              Please provide feedback for the content creator explaining why this post needs revision.
            </Text>
            <Textarea
              placeholder="Enter rejection reason or feedback for the creator..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              minH="120px"
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => { onRejectClose(); setRejectingPost(null); setRejectReason(''); }}>
              Cancel
            </Button>
            <Button 
              colorScheme="red" 
              onClick={handleRejectPost}
              isLoading={approvalLoading === rejectingPost?.id}
              isDisabled={!rejectReason.trim()}
            >
              Reject Post
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
