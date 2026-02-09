'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  Text,
  Avatar,
  useColorModeValue,
  Collapse,
  IconButton,
  HStack,
  CircularProgress,
  CircularProgressLabel,
  Badge,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
// Note: axios import removed - using mock data until API endpoint is ready

export default function ComplianceGauge({ user }) {
  const [reputationData, setReputationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const scoreBreakdownBg = useColorModeValue('gray.50', 'gray.700');
  const trackColor = useColorModeValue('gray.100', 'gray.700');
  const descriptionBg = useColorModeValue('blue.50', 'blue.900');
  const descriptionBorder = useColorModeValue('blue.200', 'blue.700');
  const descriptionText = useColorModeValue('blue.800', 'blue.100');
  const flaggedBg = useColorModeValue('red.50', 'red.900');
  const flaggedText = useColorModeValue('red.700', 'red.200');

  useEffect(() => {
    if (user) {
      loadReputationScore();
    }
  }, [user]);

  const loadReputationScore = async () => {
    // TODO: Replace with actual API call when endpoint is ready
    // For now, using mock data to avoid 404 errors
    setReputationData({
      compliance_score: null,
      total_analyzed_posts: 0,
    });
    setLoading(false);
  };

  const getComplianceLevel = (score) => {
    if (score >= 85) return { level: 'EXCELLENT', color: '#2ecc71' };
    if (score >= 75) return { level: 'GOOD', color: '#95d44d' };
    if (score >= 60) return { level: 'AVERAGE', color: '#f9e04c' };
    if (score >= 40) return { level: 'POOR', color: '#f39c12' };
    return { level: 'VERY POOR', color: '#e74c3c' };
  };

  if (loading) {
    return (
      <Box bg={cardBg} p={6} borderRadius="lg" borderWidth="1px" borderColor={borderColor}>
        <Text>Loading compliance assessment...</Text>
      </Box>
    );
  }

  // Check if user has any analyzed posts
  const hasAnalyzedPosts = reputationData?.total_analyzed_posts > 0;
  
  // Start with 100/100 score when no posts, then use actual scores
  const complianceScore = hasAnalyzedPosts ? (reputationData?.compliance_score ?? 100) : 100;
  const complianceInfo = getComplianceLevel(complianceScore);

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
            Compliance Assessment
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
            value={complianceScore}
            size="180px"
            thickness="12px"
            color={complianceInfo.color}
            trackColor={trackColor}
          >
            <CircularProgressLabel>
              <VStack spacing={0}>
                <Text fontSize="4xl" fontWeight="bold" color={complianceInfo.color}>
                  {complianceScore}
                </Text>
                <Text fontSize="xs" color="gray.500">out of 100</Text>
              </VStack>
            </CircularProgressLabel>
          </CircularProgress>
        </VStack>

        {/* Compliance Level Badge */}
        <Badge 
          colorScheme={
            complianceScore >= 85 ? 'green' :
            complianceScore >= 75 ? 'blue' :
            complianceScore >= 60 ? 'yellow' :
            complianceScore >= 40 ? 'orange' : 'red'
          }
          fontSize="md" 
          px={4} 
          py={2} 
          borderRadius="full"
        >
          🔒 {complianceInfo.level}
        </Badge>
        {!hasAnalyzedPosts && (
          <Text fontSize="xs" color="gray.400" textAlign="center">
            (No posts analyzed yet)
          </Text>
        )}

        <Collapse in={isExpanded} animateOpacity>
          <VStack spacing={3} width="100%" mt={2}>
            {/* Compliance Description */}
            <Box 
              bg={descriptionBg} 
              p={3} 
              borderRadius="md"
              borderWidth="1px"
              borderColor={descriptionBorder}
              width="100%"
            >
              <Text fontSize="xs" color={descriptionText} textAlign="center">
                Policy compliance based on severity of violations detected in analyzed posts.
              </Text>
            </Box>

            {/* Flagged Content Stats */}
            {reputationData && reputationData.flagged_posts > 0 && (
              <Box 
                bg={flaggedBg} 
                p={3} 
                borderRadius="md"
                width="100%"
              >
                <HStack justify="center" spacing={2}>
                  <Text fontSize="sm" fontWeight="600" color="red.600">⚠️</Text>
                  <Text fontSize="xs" color={flaggedText}>
                    {reputationData.flagged_posts} policy violation{reputationData.flagged_posts !== 1 ? 's' : ''}
                  </Text>
                </HStack>
              </Box>
            )}

            {/* Compliance Scale Legend */}
            <VStack spacing={2} width="100%" fontSize="xs">
              <Text fontWeight="600" color="gray.500" mb={1}>COMPLIANCE ASSESSMENT SCALE</Text>
              <VStack spacing={1} width="100%" fontSize="xs">
                <HStack justify="space-between" width="100%">
                  <Text color="#2ecc71" fontWeight="600">85-100</Text>
                  <Text color="gray.600">EXCELLENT</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#95d44d" fontWeight="600">75-84</Text>
                  <Text color="gray.600">GOOD</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#f9e04c" fontWeight="600">60-74</Text>
                  <Text color="gray.600">AVERAGE</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#f39c12" fontWeight="600">40-59</Text>
                  <Text color="gray.600">POOR</Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="#e74c3c" fontWeight="600">0-39</Text>
                  <Text color="gray.600">VERY POOR</Text>
                </HStack>
              </VStack>
            </VStack>

            {/* Stats */}
            {reputationData && (
              <Box 
                width="100%" 
                pt={3} 
                borderTopWidth="1px" 
                borderColor={borderColor}
              >
                <Text fontSize="xs" color="gray.500" textAlign="center">
                  Based on {reputationData.total_analyzed_posts} analyzed post{reputationData.total_analyzed_posts !== 1 ? 's' : ''}
                </Text>
                {reputationData.flagged_posts > 0 && (
                  <Text fontSize="xs" color="red.600" textAlign="center" mt={1}>
                    ⚠️ {reputationData.flagged_posts} policy violation{reputationData.flagged_posts !== 1 ? 's' : ''}
                  </Text>
                )}
              </Box>
            )}
          </VStack>
        </Collapse>
      </VStack>
    </Box>
  );
}
