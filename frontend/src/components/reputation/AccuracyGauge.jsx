'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Avatar,
  CircularProgress,
  CircularProgressLabel,
  useColorModeValue,
  IconButton,
  Collapse,
  Badge,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
// Note: axios import removed - using mock data until API endpoint is ready

export default function AccuracyGauge({ user }) {
  const [reputationData, setReputationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const trackColor = useColorModeValue('gray.100', 'gray.700');

  useEffect(() => {
    if (user) {
      loadAccuracyScore();
    }
  }, [user]);

  const loadAccuracyScore = async () => {
    // TODO: Replace with actual API call when endpoint is ready
    // For now, using mock data to avoid 404 errors
    setReputationData({
      accuracy_score: null,
      total_analyzed_posts: 0,
    });
    setLoading(false);
  };

  const getAccuracyLevel = (score) => {
    if (score >= 90) return { level: 'HIGHLY ACCURATE', color: '#2ecc71' };
    if (score >= 80) return { level: 'VERY ACCURATE', color: '#95d44d' };
    if (score >= 70) return { level: 'ACCURATE', color: '#f9e04c' };
    if (score >= 60) return { level: 'MODERATELY ACCURATE', color: '#f39c12' };
    return { level: 'NEEDS REVIEW', color: '#e74c3c' };
  };

  if (loading) {
    return (
      <Box bg={cardBg} p={6} borderRadius="lg" borderWidth="1px" borderColor={borderColor}>
        <Text>Loading accuracy assessment...</Text>
      </Box>
    );
  }

  // Check if user has any analyzed posts
  const hasAnalyzedPosts = reputationData?.total_analyzed_posts > 0;
  
  // Start with 100/100 score when no posts, then use actual scores
  const accuracyScore = hasAnalyzedPosts ? (reputationData?.accuracy_score ?? 100) : 100;
  const accuracyInfo = getAccuracyLevel(accuracyScore);

  return (
    <Box 
      bg={cardBg} 
      p={6} 
      borderRadius="lg" 
      borderWidth="1px" 
      borderColor={borderColor}
      position="relative"
      maxW="400px"
      mx="auto"
    >
      <VStack spacing={4}>
        <HStack width="100%" justify="space-between">
          <Text fontSize="lg" fontWeight="700">
            Accuracy Assessment
          </Text>
          <IconButton
            icon={isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label="Toggle details"
          />
        </HStack>

        {/* Circular Progress */}
        <VStack spacing={1}>
          <CircularProgress
            value={accuracyScore}
            size="180px"
            thickness="12px"
            color={accuracyInfo.color}
            trackColor={trackColor}
          >
            <CircularProgressLabel>
              <VStack spacing={0}>
                <Text fontSize="4xl" fontWeight="bold" color={accuracyInfo.color}>
                  {accuracyScore}
                </Text>
                <Text fontSize="xs" color="gray.500">out of 100</Text>
              </VStack>
            </CircularProgressLabel>
          </CircularProgress>
        </VStack>

        {/* Accuracy Level Badge */}
        <Badge 
          colorScheme={
            accuracyScore >= 90 ? 'green' :
            accuracyScore >= 80 ? 'blue' :
            accuracyScore >= 70 ? 'yellow' :
            accuracyScore >= 60 ? 'orange' : 'red'
          }
          fontSize="md" 
          px={4} 
          py={2} 
          borderRadius="full"
        >
          ✓ {accuracyInfo.level}
        </Badge>
        {!hasAnalyzedPosts && (
          <Text fontSize="xs" color="gray.400" textAlign="center">
            (No posts analyzed yet)
          </Text>
        )}

        <Collapse in={isExpanded} animateOpacity>
          <VStack spacing={3} width="100%" mt={3}>
            <Box 
              bg="blue.50" 
              p={3} 
              borderRadius="md"
              borderWidth="1px"
              borderColor="blue.200"
              width="100%"
            >
              <Text fontSize="xs" color="blue.700" textAlign="center">
                Accuracy measures factual correctness and truthfulness of content based on verified sources and fact-checking.
              </Text>
            </Box>

            {/* Accuracy Scale */}
            <VStack spacing={2} width="100%" mt={2}>
              <Text fontSize="xs" fontWeight="600" color="gray.500">ACCURACY SCALE</Text>
              <VStack spacing={1} width="100%" fontSize="xs">
                <HStack justify="space-between" width="100%">
                  <Text color="#2ecc71" fontWeight="600">90-100</Text>
                  <Text color="gray.600">HIGHLY ACCURATE</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#95d44d" fontWeight="600">80-89</Text>
                  <Text color="gray.600">VERY ACCURATE</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#f9e04c" fontWeight="600">70-79</Text>
                  <Text color="gray.600">ACCURATE</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#f39c12" fontWeight="600">60-69</Text>
                  <Text color="gray.600">MODERATELY ACCURATE</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#e74c3c" fontWeight="600">0-59</Text>
                  <Text color="gray.600">NEEDS REVIEW</Text>
                </HStack>
              </VStack>
            </VStack>

            {hasAnalyzedPosts && (
              <Box 
                width="100%" 
                pt={3} 
                borderTopWidth="1px" 
                borderColor={borderColor}
              >
                <VStack spacing={1}>
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    Assessment based on {reputationData.total_analyzed_posts} post{reputationData.total_analyzed_posts !== 1 ? 's' : ''}
                  </Text>
                  <Text fontSize="xs" color="gray.400" textAlign="center" fontStyle="italic">
                    Purpose: Verify content accuracy and factual correctness
                  </Text>
                </VStack>
              </Box>
            )}
          </VStack>
        </Collapse>
      </VStack>
    </Box>
  );
}
