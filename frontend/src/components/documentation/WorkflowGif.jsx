/**
 * WorkflowGif - Component for displaying animated workflow GIFs in documentation
 * 
 * Fetches and displays pre-recorded workflow GIFs from the documentation API.
 * Shows a loading state while fetching and handles errors gracefully.
 * 
 * Props:
 * - workflowId (string, required): ID of the workflow to display
 * - caption (string): Optional caption for the GIF
 * - className (string): Additional CSS classes
 */

'use client';
import React, { useState, useEffect } from 'react';
import {
  Box,
  Skeleton,
  Text,
  VStack,
  HStack,
  Badge,
  Icon,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaPlay, FaRedo, FaClock } from 'react-icons/fa';
import { getApiUrl } from '@/lib/api';

export function WorkflowGif({ workflowId, caption, className = '' }) {
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);

  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const captionColor = useColorModeValue('gray.600', 'gray.400');

  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        setLoading(true);
        const API = getApiUrl();
        const response = await fetch(`${API}/documentation/workflows/${workflowId}`);
        
        if (!response.ok) {
          throw new Error('Workflow not found');
        }
        
        const data = await response.json();
        setWorkflow(data);
      } catch (err) {
        console.error('Error fetching workflow:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (workflowId) {
      fetchWorkflow();
    }
  }, [workflowId]);

  if (loading) {
    return (
      <Box className={className} my={4}>
        <Skeleton height="300px" borderRadius="md" />
        {caption && <Skeleton height="20px" mt={2} width="60%" />}
      </Box>
    );
  }

  if (error || !workflow || workflow.status === 'not_recorded') {
    return (
      <Box
        className={className}
        my={4}
        p={6}
        bg={bgColor}
        borderRadius="md"
        borderWidth="1px"
        borderColor={borderColor}
        textAlign="center"
      >
        <Icon as={FaPlay} boxSize={8} color="gray.400" mb={2} />
        <Text color="gray.500" fontSize="sm">
          {workflow?.message || 'Workflow GIF not yet recorded'}
        </Text>
        <Text color="gray.400" fontSize="xs" mt={1}>
          {workflow?.name || workflowId}
        </Text>
      </Box>
    );
  }

  return (
    <VStack className={className} spacing={2} align="stretch" my={4}>
      {/* GIF Container */}
      <Box
        position="relative"
        borderRadius="md"
        overflow="hidden"
        borderWidth="1px"
        borderColor={borderColor}
        bg={bgColor}
      >
        {/* GIF Image */}
        <Box
          as="img"
          src={`data:image/gif;base64,${workflow.gif_data}`}
          alt={workflow.name || caption}
          width="100%"
          height="auto"
          display="block"
          opacity={isPlaying ? 1 : 0.7}
        />
        
        {/* Overlay Controls */}
        <HStack
          position="absolute"
          bottom={2}
          right={2}
          spacing={2}
        >
          <Badge
            bg="blackAlpha.700"
            color="white"
            px={2}
            py={1}
            borderRadius="md"
            fontSize="xs"
          >
            <HStack spacing={1}>
              <Icon as={FaClock} boxSize={3} />
              <Text>{workflow.duration_seconds?.toFixed(1)}s</Text>
            </HStack>
          </Badge>
          
          {workflow.frame_count && (
            <Badge
              bg="blackAlpha.700"
              color="white"
              px={2}
              py={1}
              borderRadius="md"
              fontSize="xs"
            >
              {workflow.frame_count} frames
            </Badge>
          )}
        </HStack>
      </Box>

      {/* Caption and Info */}
      <HStack justify="space-between" align="center">
        <VStack align="start" spacing={0}>
          <Text fontSize="sm" color={captionColor} fontStyle="italic">
            {caption || workflow.description || workflow.name}
          </Text>
          {workflow.captured_at && (
            <Text fontSize="xs" color="gray.400">
              Recorded: {new Date(workflow.captured_at).toLocaleDateString()}
            </Text>
          )}
        </VStack>
      </HStack>
    </VStack>
  );
}

/**
 * WorkflowGifGallery - Displays all available workflow GIFs
 */
export function WorkflowGifGallery({ guide = 'all' }) {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const API = getApiUrl();
        const response = await fetch(`${API}/documentation/workflows`);
        const data = await response.json();
        
        let filtered = data.workflows || [];
        if (guide !== 'all') {
          filtered = filtered.filter(w => w.guide === guide);
        }
        
        setWorkflows(filtered);
      } catch (err) {
        console.error('Error fetching workflows:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, [guide]);

  if (loading) {
    return (
      <VStack spacing={4}>
        <Skeleton height="200px" width="100%" />
        <Skeleton height="200px" width="100%" />
      </VStack>
    );
  }

  if (workflows.length === 0) {
    return (
      <Text color="gray.500" fontSize="sm">
        No workflow GIFs available for this guide.
      </Text>
    );
  }

  return (
    <VStack spacing={6} align="stretch">
      {workflows.map((workflow) => (
        <WorkflowGif
          key={workflow.id}
          workflowId={workflow.id}
          caption={workflow.description}
        />
      ))}
    </VStack>
  );
}

export default WorkflowGif;
