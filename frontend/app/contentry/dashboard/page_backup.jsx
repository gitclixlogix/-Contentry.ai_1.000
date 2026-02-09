'use client';
import { useEffect, useState } from 'react';
import {
  Box,
  SimpleGrid,
  Flex,
  Text,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Button,
  Icon,
  HStack,
  VStack,
  Card,
  CardBody,
  Select,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Heading,
  Spinner,
} from '@chakra-ui/react';
import MiniStatistics from '@/components/card/MiniStatistics';
import IconBox from '@/components/icons/IconBox';
import ReputationScore from '@/components/reputation/ReputationScore';
import RiskGauge from '@/components/reputation/RiskGauge';
import ComplianceGauge from '@/components/reputation/ComplianceGauge';
import AccuracyGauge from '@/components/reputation/AccuracyGauge';
import { FaFileAlt, FaCheckCircle, FaClock, FaExclamationTriangle, FaTrash, FaFacebookF, FaInstagram, FaLinkedinIn, FaYoutube, FaTwitter, FaEye, FaSync, FaDownload, FaRedo } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_posts: 0,
    approved: 0,
    pending: 0,
    flagged: 0,
  });
  const [posts, setPosts] = useState([]);
  const [filteredPosts, setFilteredPosts] = useState([]);
  const [user, setUser] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('all'); // all, contentry, imported
  const [statusFilter, setStatusFilter] = useState('all'); // all, approved, pending, flagged
  const [selectedPost, setSelectedPost] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [reanalyzeLoading, setReanalyzeLoading] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const boxBg = useColorModeValue('secondaryGray.300', 'whiteAlpha.100');
  const cardBg = useColorModeValue('white', 'navy.800');
  const textColor = useColorModeValue('secondaryGray.900', 'white');
  const textColorSecondary = useColorModeValue('secondaryGray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.100');

  useEffect(() => {
    // Force a fresh read of user data on every mount
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      console.log('Dashboard: Loading user data', userData);
      console.log('Dashboard: User profile picture:', userData.profile_picture);
      setUser(userData);
      loadDashboardData(userData.id);
    }
  }, []);

  useEffect(() => {
    // Filter posts based on both source and status filters
    let filtered = posts;
    
    // Apply source filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(post => post.source === sourceFilter);
    }
    
    // Apply status filter
    if (statusFilter === 'approved') {
      filtered = filtered.filter(post => post.flagged_status === 'good_coverage');
    } else if (statusFilter === 'pending') {
      filtered = filtered.filter(post => post.status === 'scheduled');
    } else if (statusFilter === 'flagged') {
      filtered = filtered.filter(post => 
        post.flagged_status === 'policy_violation' || 
        post.flagged_status === 'rude_and_abusive' || 
        post.flagged_status === 'contain_harassment'
      );
    }
    
    setFilteredPosts(filtered);
  }, [posts, sourceFilter, statusFilter]);

  const loadDashboardData = async (userId) => {
    try {
      const API = getApiUrl();
      const postsRes = await axios.get(`${API}/posts`, { 
        headers: { 'X-User-ID': userId }
      });

      const postsData = postsRes.data;
      setPosts(postsData);
      setFilteredPosts(postsData);
      
      setStats({
        total_posts: postsData.length,
        approved: postsData.filter(p => p.flagged_status === 'good_coverage').length,
        pending: postsData.filter(p => p.flagged_status === 'pending').length,
        flagged: postsData.filter(p => ['rude_and_abusive', 'contain_harassment', 'policy_violation'].includes(p.flagged_status)).length,
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const importSocialMediaPosts = async () => {
    if (!user) return;
    
    setImportLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/social-media/import-posts`, {
        user_id: user.id,
        platform: 'all',
        limit: 50
      });
      
      alert(response.data.message + `\n\nNote: ${response.data.note}`);
      loadDashboardData(user.id);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to import posts');
    } finally {
      setImportLoading(false);
    }
  };

  const reanalyzeAllPosts = async () => {
    if (!user) return;
    
    if (!confirm('This will reanalyze all your posts to check if they still meet content standards. Continue?')) {
      return;
    }
    
    setReanalyzeLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/posts/reanalyze-all`, {
        user_id: user.id
      });
      
      alert(response.data.message);
      loadDashboardData(user.id);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to reanalyze posts');
    } finally {
      setReanalyzeLoading(false);
    }
  };

  const deletePost = async (postId) => {
    if (!confirm('Are you sure you want to delete this post? This will also remove it from connected social media platforms.')) {
      return;
    }
    try {
      const API = getApiUrl();
      await axios.delete(`${API}/posts/${postId}`);
      if (user) loadDashboardData(user.id);
    } catch (error) {
      alert('Failed to delete post');
    }
  };

  const viewPostDetails = (post) => {
    setSelectedPost(post);
    onOpen();
  };

  const reanalyzePost = async (postId) => {
    try {
      const API = getApiUrl();
      await axios.post(`${API}/posts/${postId}/reanalyze`);
      alert('Post re-analyzed successfully');
      if (user) loadDashboardData(user.id);
    } catch (error) {
      alert('Failed to re-analyze post');
    }
  };

  const getFlagColor = (status) => {
    const colors = {
      'good_coverage': 'green',
      'pending': 'yellow',
      'rude_and_abusive': 'red',
      'contain_harassment': 'red',
      'policy_violation': 'orange',
    };
    return colors[status] || 'gray';
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      'Facebook': FaFacebookF,
      'Instagram': FaInstagram,
      'LinkedIn': FaLinkedinIn,
      'YouTube': FaYoutube,
      'Twitter': FaTwitter,
      'X': FaTwitter,
    };
    return icons[platform] || FaFileAlt;
  };

  return (
    <Box pt={{ base: '80px', md: '80px', xl: '80px' }} px={{ base: 2, md: 4 }}>
      <Text
        mb={{ base: "16px", md: "20px" }}
        color={textColor}
        fontSize={{ base: "xl", md: "2xl" }}
        fontWeight="700"
        lineHeight="100%"
      >
        Dashboard
      </Text>

      {/* Risk Assessment Gauges */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={{ base: "20px", md: "24px" }} mb={{ base: "16px", md: "20px" }}>
        <RiskGauge user={user} />
        <ComplianceGauge user={user} />
        <AccuracyGauge user={user} />
        <ReputationScore user={user} />
      </SimpleGrid>

      {/* Statistics - Clickable Filter Buttons */}
      <Flex 
        gap={{ base: 2, md: 3 }} 
        mb={{ base: "16px", md: "20px" }} 
        flexWrap="wrap"
        direction={{ base: "column", sm: "row" }}
      >
        <Button
          leftIcon={<FaFileAlt />}
          colorScheme={statusFilter === 'all' ? 'purple' : 'gray'}
          variant={statusFilter === 'all' ? 'solid' : 'outline'}
          onClick={() => setStatusFilter('all')}
          size={{ base: "sm", md: "md" }}
          fontSize={{ base: "xs", md: "sm" }}
          w={{ base: "full", sm: "auto" }}
        >
          Total: {stats.total_posts}
        </Button>

        <Button
          leftIcon={<FaCheckCircle />}
          colorScheme={statusFilter === 'approved' ? 'green' : 'gray'}
          variant={statusFilter === 'approved' ? 'solid' : 'outline'}
          onClick={() => setStatusFilter('approved')}
          size={{ base: "sm", md: "md" }}
          fontSize={{ base: "xs", md: "sm" }}
          w={{ base: "full", sm: "auto" }}
        >
          Approved: {stats.approved}
        </Button>

        <Button
          leftIcon={<FaClock />}
          colorScheme={statusFilter === 'pending' ? 'orange' : 'gray'}
          variant={statusFilter === 'pending' ? 'solid' : 'outline'}
          onClick={() => setStatusFilter('pending')}
          size={{ base: "sm", md: "md" }}
          fontSize={{ base: "xs", md: "sm" }}
          w={{ base: "full", sm: "auto" }}
        >
          Pending: {stats.pending}
        </Button>

        <Button
          leftIcon={<FaExclamationTriangle />}
          colorScheme={statusFilter === 'flagged' ? 'red' : 'gray'}
          variant={statusFilter === 'flagged' ? 'solid' : 'outline'}
          onClick={() => setStatusFilter('flagged')}
          size={{ base: "sm", md: "md" }}
          fontSize={{ base: "xs", md: "sm" }}
          w={{ base: "full", sm: "auto" }}
        >
          Flagged: {stats.flagged}
        </Button>
      </Flex>

      {/* Post Listings - Exact same as Post Listings page */}
      <Flex 
        justify="space-between" 
        mb={4} 
        direction={{ base: "column", md: "row" }}
        gap={{ base: 3, md: 0 }}
      >
        <Heading size={{ base: "sm", md: "md" }} color={textColor}>Your Posts</Heading>
        <Flex gap={2} direction={{ base: "column", sm: "row" }} w={{ base: "full", md: "auto" }}>
          <Button
            leftIcon={<FaSync />}
            colorScheme="blue"
            onClick={importSocialMediaPosts}
            isLoading={importLoading}
            loadingText="Importing..."
            size="sm"
            fontSize={{ base: "xs", md: "sm" }}
            w={{ base: "full", sm: "auto" }}
          >
            Import Posts
          </Button>
          <Button
            leftIcon={<FaRedo />}
            colorScheme="blue"
            onClick={reanalyzeAllPosts}
            isLoading={reanalyzeLoading}
            loadingText="Analyzing..."
            size="sm"
            fontSize={{ base: "xs", md: "sm" }}
            w={{ base: "full", sm: "auto" }}
          >
            Reanalyze All
          </Button>
          <Button
            leftIcon={<FaDownload />}
            colorScheme="green"
            onClick={() => {
              if (user) {
                window.open(`/contentry/report?user_id=${user.id}`, '_blank');
              }
            }}
            size="sm"
            fontSize={{ base: "xs", md: "sm" }}
            w={{ base: "full", sm: "auto" }}
          >
            Report
          </Button>
        </Flex>
      </Flex>

      <Card bg={cardBg} mb={4}>
        <CardBody p={{ base: 3, md: 4 }}>
          <Flex 
            gap={{ base: 2, md: 4 }} 
            mb={4}
            direction={{ base: "column", sm: "row" }}
            align={{ base: "stretch", sm: "center" }}
          >
            <Text fontWeight="600" fontSize={{ base: "xs", md: "sm" }} color={textColor}>Filter by Source:</Text>
            <Select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              w={{ base: "full", sm: "200px" }}
              size="sm"
              fontSize={{ base: "xs", md: "sm" }}
            >
              <option value="all">All ({posts.length})</option>
              <option value="contentry">Contentry ({posts.filter(p => p.source === 'contentry').length})</option>
              <option value="imported">Imported ({posts.filter(p => p.source === 'imported').length})</option>
            </Select>
          </Flex>

          <Box overflowX="auto">
            <Table variant="simple" size={{ base: "sm", md: "sm" }}>
              <Thead>
                <Tr>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", md: "table-cell" }}>Source</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }}>Post</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }}>Status</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", lg: "table-cell" }}>Overall</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", lg: "table-cell" }}>Compliance</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", lg: "table-cell" }}>Cultural</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", md: "table-cell" }}>Platform</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", xl: "table-cell" }}>Engagement</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }} display={{ base: "none", sm: "table-cell" }}>Date</Th>
                  <Th fontSize={{ base: "10px", md: "xs" }}>Action</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredPosts.map((post, idx) => (
                  <Tr key={post.id}>
                    <Td>
                      <Badge colorScheme={post.source === 'contentry' ? 'blue' : 'purple'} fontSize="xs">
                        {post.source === 'contentry' ? 'Contentry' : 'Imported'}
                      </Badge>
                    </Td>
                    <Td maxW="200px">
                      <Text fontSize="xs" noOfLines={2}>
                        {post.content}
                      </Text>
                    </Td>
                    <Td>
                      <Badge colorScheme={getFlagColor(post.flagged_status)} fontSize="xs">
                        {post.flagged_status.replace(/_/g, ' ').substring(0, 15)}
                      </Badge>
                    </Td>
                    <Td>
                      <Tooltip label={`Overall: ${post.overall_score || '—'}/100`}>
                        {post.overall_score ? (
                          <Text fontWeight="600" fontSize="md" color={
                            post.overall_score >= 85 ? 'green.500' : 
                            post.overall_score >= 75 ? 'blue.500' : 
                            post.overall_score >= 60 ? 'yellow.600' : 
                            post.overall_score >= 40 ? 'orange.500' : 'red.500'
                          }>
                            {post.overall_score}
                          </Text>
                        ) : (
                          <Text fontSize="xs" color="gray.400">—</Text>
                        )}
                      </Tooltip>
                    </Td>
                    <Td>
                      <Tooltip label={
                        post.violation_severity && post.violation_severity !== 'none' 
                          ? `${post.violation_severity} - ${post.violation_type} - ${post.potential_consequences}` 
                          : 'Compliant'
                      }>
                        {post.compliance_score ? (
                          <Badge colorScheme={
                            post.compliance_score >= 81 ? 'green' :
                            post.compliance_score >= 61 ? 'blue' :
                            post.compliance_score >= 41 ? 'yellow' :
                            post.compliance_score >= 21 ? 'orange' : 'red'
                          } fontSize="xs">
                            {post.compliance_score}
                          </Badge>
                        ) : (
                          <Text fontSize="xs" color="gray.400">—</Text>
                        )}
                      </Tooltip>
                    </Td>
                    <Td>
                      {post.cultural_sensitivity_score ? (
                        <Text fontWeight="600" fontSize="md" color={
                          post.cultural_sensitivity_score >= 75 ? 'green.500' : 
                          post.cultural_sensitivity_score >= 60 ? 'blue.500' : 
                          post.cultural_sensitivity_score >= 40 ? 'orange.500' : 'red.500'
                        }>
                          {post.cultural_sensitivity_score}
                        </Text>
                      ) : (
                        <Text fontSize="xs" color="gray.400">—</Text>
                      )}
                    </Td>
                    <Td>
                      <HStack>
                        {post.platforms.slice(0, 3).map(platform => {
                          const IconComponent = getPlatformIcon(platform);
                          return <Icon key={platform} as={IconComponent} color="gray.600" />;
                        })}
                      </HStack>
                    </Td>
                    <Td>
                      {post.engagement_metrics && Object.keys(post.engagement_metrics).length > 0 ? (
                        <VStack align="start" spacing={0}>
                          <Text fontSize="xs">❤️ {post.engagement_metrics.likes || 0}</Text>
                          <Text fontSize="xs">💬 {post.engagement_metrics.comments || 0}</Text>
                          <Text fontSize="xs">🔄 {post.engagement_metrics.shares || 0}</Text>
                        </VStack>
                      ) : (
                        <Text fontSize="xs" color="gray.400">—</Text>
                      )}
                    </Td>
                    <Td>
                      <Text fontSize="xs">{new Date(post.created_at).toLocaleDateString()}</Text>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        <Tooltip label="View Details">
                          <Button size="xs" variant="ghost" onClick={() => viewPostDetails(post)}>
                            <FaEye />
                          </Button>
                        </Tooltip>
                        <Tooltip label="Re-analyze">
                          <Button size="xs" variant="ghost" colorScheme="blue" onClick={() => reanalyzePost(post.id)}>
                            <FaSync />
                          </Button>
                        </Tooltip>
                        <Tooltip label="Delete">
                          <Button size="xs" variant="ghost" colorScheme="red" onClick={() => deletePost(post.id)}>
                            <FaTrash />
                          </Button>
                        </Tooltip>
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>

          {filteredPosts.length === 0 && (
            <Text textAlign="center" py={8} color="gray.500">
              No posts found. {sourceFilter !== 'all' ? 'Try changing the filter.' : 'Create your first post!'}
            </Text>
          )}
        </CardBody>
      </Card>

      {/* Post Details Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent bg={cardBg}>
          <ModalHeader>Post Details</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedPost && (
              <VStack align="stretch" spacing={4}>
                <Box>
                  <Text fontWeight="600" mb={2}>Content:</Text>
                  <Text fontSize="sm" whiteSpace="pre-wrap">{selectedPost.content}</Text>
                </Box>
                
                <Box>
                  <Text fontWeight="600" mb={2}>Status:</Text>
                  <Badge colorScheme={getFlagColor(selectedPost.flagged_status)}>
                    {selectedPost.flagged_status.replace(/_/g, ' ')}
                  </Badge>
                </Box>

                {selectedPost.moderation_summary && (
                  <Box>
                    <Text fontWeight="600" mb={2}>Moderation Summary:</Text>
                    <Text fontSize="sm" color="gray.600">{selectedPost.moderation_summary}</Text>
                  </Box>
                )}

                <Box>
                  <Text fontWeight="600" mb={2}>Platforms:</Text>
                  <HStack>
                    {selectedPost.platforms.map(platform => (
                      <Badge key={platform} colorScheme="blue">{platform}</Badge>
                    ))}
                  </HStack>
                </Box>

                {selectedPost.engagement_metrics && Object.keys(selectedPost.engagement_metrics).length > 0 && (
                  <Box>
                    <Text fontWeight="600" mb={2}>Engagement:</Text>
                    <HStack spacing={4}>
                      <Text fontSize="sm">❤️ {selectedPost.engagement_metrics.likes || 0} likes</Text>
                      <Text fontSize="sm">💬 {selectedPost.engagement_metrics.comments || 0} comments</Text>
                      <Text fontSize="sm">🔄 {selectedPost.engagement_metrics.shares || 0} shares</Text>
                    </HStack>
                  </Box>
                )}

                <Box>
                  <Text fontWeight="600" mb={2}>Created:</Text>
                  <Text fontSize="sm">{new Date(selectedPost.created_at).toLocaleString()}</Text>
                </Box>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}
