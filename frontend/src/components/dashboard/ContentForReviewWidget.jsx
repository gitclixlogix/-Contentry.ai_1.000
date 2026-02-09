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
  Badge,
  Button,
  Flex,
  Icon,
  Spinner,
  Center,
  useColorModeValue,
  Divider,
  Avatar,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Textarea,
  useDisclosure,
} from '@chakra-ui/react';
import { FaCheckCircle, FaEdit, FaExclamationTriangle, FaClock, FaUser, FaArrowRight } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

export default function ContentForReviewWidget({ userId, userPermissions }) {
  const [pendingPosts, setPendingPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [selectedPost, setSelectedPost] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const router = useRouter();
  const toast = useToast();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const previewBg = useColorModeValue('gray.50', 'gray.700');

  // Only show widget if user can approve others
  const canApprove = userPermissions?.can_approve_others;

  const loadPendingContent = async () => {
    if (!userId || !canApprove) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/approval/pending');
      setPendingPosts(response.data.posts || []);
    } catch (error) {
      console.error('Failed to load pending content:', error);
      setPendingPosts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPendingContent();
  }, [userId, canApprove]);

  const handleApprove = async (postId) => {
    setActionLoading(postId);
    try {
      await api.post(`/approval/${postId}/approve`, {});
      
      toast({
        title: 'Content Approved!',
        description: 'The content has been approved and can now be published.',
        status: 'success',
        duration: 4000,
      });
      
      // Remove from list
      setPendingPosts(prev => prev.filter(p => p.id !== postId));
    } catch (error) {
      toast({
        title: 'Failed to approve',
        description: error.response?.data?.detail || 'An error occurred',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRequestChanges = (post) => {
    setSelectedPost(post);
    setRejectReason('');
    onOpen();
  };

  const handleSubmitChangesRequest = async () => {
    if (!selectedPost || !rejectReason.trim()) {
      toast({
        title: 'Please provide feedback',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setActionLoading(selectedPost.id);
    try {
      await api.post(`/approval/${selectedPost.id}/reject`, {
        reason: rejectReason
      });
      
      toast({
        title: 'Changes Requested',
        description: 'The creator has been notified and will revise the content.',
        status: 'info',
        duration: 4000,
      });
      
      // Remove from list
      setPendingPosts(prev => prev.filter(p => p.id !== selectedPost.id));
      onClose();
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
      setActionLoading(null);
    }
  };

  const navigateToPost = (postId) => {
    router.push(`/contentry/content-moderation?tab=posts&view=${postId}`);
  };

  // Don't render if user can't approve others
  if (!canApprove) {
    return null;
  }

  return (
    <>
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" shadow="sm">
        <CardHeader pb={2}>
          <Flex justify="space-between" align="center">
            <HStack>
              <Icon as={FaExclamationTriangle} color="orange.500" />
              <Heading size="sm">Content for Review</Heading>
              {pendingPosts.length > 0 && (
                <Badge colorScheme="orange" borderRadius="full" px={2}>
                  {pendingPosts.length}
                </Badge>
              )}
            </HStack>
            {pendingPosts.length > 3 && (
              <Button 
                size="xs" 
                variant="ghost" 
                rightIcon={<FaArrowRight />}
                onClick={() => router.push('/contentry/content-moderation?tab=posts&filter=pending_approval')}
              >
                View All
              </Button>
            )}
          </Flex>
        </CardHeader>
        <CardBody pt={0}>
          {loading ? (
            <Center py={6}>
              <Spinner size="md" color="orange.500" />
            </Center>
          ) : pendingPosts.length === 0 ? (
            <Box textAlign="center" py={6}>
              <Icon as={FaCheckCircle} boxSize={8} color="green.400" mb={2} />
              <Text color={textColor} fontSize="sm">
                No content pending review
              </Text>
              <Text color={textColor} fontSize="xs" mt={1}>
                You&apos;re all caught up! 🎉
              </Text>
            </Box>
          ) : (
            <VStack spacing={3} align="stretch">
              {pendingPosts.slice(0, 5).map((post, index) => (
                <Box key={post.id}>
                  {index > 0 && <Divider mb={3} />}
                  <Box
                    p={3}
                    borderRadius="md"
                    _hover={{ bg: hoverBg }}
                    transition="background 0.2s"
                  >
                    <Flex justify="space-between" align="start" gap={3}>
                      <Box flex={1} minW={0}>
                        <HStack mb={1} spacing={2}>
                          <Avatar size="xs" name={post.author_name || 'User'} />
                          <Text fontSize="xs" color={textColor}>
                            {post.author_name || 'Unknown'}
                          </Text>
                          <Badge size="sm" colorScheme="yellow">
                            Pending
                          </Badge>
                        </HStack>
                        <Text 
                          fontSize="sm" 
                          fontWeight="medium" 
                          noOfLines={2}
                          cursor="pointer"
                          onClick={() => navigateToPost(post.id)}
                          _hover={{ color: 'brand.500' }}
                        >
                          {post.content?.substring(0, 100) || post.title || 'Untitled content'}
                          {(post.content?.length > 100) && '...'}
                        </Text>
                        <HStack mt={2} spacing={2}>
                          <Icon as={FaClock} boxSize={3} color={textColor} />
                          <Text fontSize="xs" color={textColor}>
                            {post.submitted_at 
                              ? new Date(post.submitted_at).toLocaleDateString() 
                              : 'Recently submitted'}
                          </Text>
                          {post.project_name && (
                            <>
                              <Text fontSize="xs" color={textColor}>•</Text>
                              <Text fontSize="xs" color="brand.500">
                                {post.project_name}
                              </Text>
                            </>
                          )}
                        </HStack>
                      </Box>
                      <VStack spacing={1}>
                        <Button
                          size="xs"
                          colorScheme="green"
                          leftIcon={<FaCheckCircle />}
                          onClick={() => handleApprove(post.id)}
                          isLoading={actionLoading === post.id}
                          loadingText="..."
                        >
                          Approve
                        </Button>
                        <Button
                          size="xs"
                          colorScheme="orange"
                          variant="outline"
                          leftIcon={<FaEdit />}
                          onClick={() => handleRequestChanges(post)}
                          isDisabled={actionLoading === post.id}
                        >
                          Changes
                        </Button>
                      </VStack>
                    </Flex>
                  </Box>
                </Box>
              ))}
            </VStack>
          )}
        </CardBody>
      </Card>

      {/* Request Changes Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Request Changes</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text fontSize="sm" mb={3} color={textColor}>
              Provide feedback for the content creator. They will be notified and can revise their content.
            </Text>
            <Text fontSize="sm" fontWeight="medium" mb={2}>
              Content preview:
            </Text>
            <Box 
              p={3} 
              bg={previewBg} 
              borderRadius="md" 
              mb={4}
              fontSize="sm"
            >
              {selectedPost?.content?.substring(0, 200) || selectedPost?.title}
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
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="orange" 
              onClick={handleSubmitChangesRequest}
              isLoading={actionLoading === selectedPost?.id}
              isDisabled={!rejectReason.trim()}
            >
              Request Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
