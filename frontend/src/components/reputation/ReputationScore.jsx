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
  Flex,
  Badge,
  Tooltip,
  Collapse,
  IconButton,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
// Note: axios import removed - using mock data until API endpoint is ready

export default function ReputationScore({ user }) {
  const [reputationData, setReputationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const trackColor = useColorModeValue('gray.100', 'gray.700');
  const riskBg = useColorModeValue('orange.50', 'orange.900');
  const riskBorder = useColorModeValue('orange.200', 'orange.700');
  const riskText = useColorModeValue('orange.800', 'orange.100');
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
      reputation_score: null,
      risk_level: 'UNKNOWN',
      risk_description: 'No data available',
      flagged_posts: 0,
      total_analyzed_posts: 0,
    });
    setLoading(false);
  };

  const getScoreColor = (score) => {
    if (score >= 85) return '#2ecc71'; // EXCELLENT - green
    if (score >= 75) return '#95d44d'; // GOOD - light green
    if (score >= 60) return '#f9e04c'; // AVERAGE - yellow
    if (score >= 40) return '#f39c12'; // POOR - orange
    return '#e74c3c'; // VERY POOR - red
  };

  const getRiskColor = (riskLevel) => {
    const colors = {
      'MINIMAL RISK': 'green',
      'LOW RISK': 'blue',
      'MODERATE RISK': 'yellow',
      'ELEVATED RISK': 'orange',
      'HIGH RISK': 'red',
      'UNKNOWN': 'gray'
    };
    return colors[riskLevel] || 'gray';
  };

  if (loading) {
    return (
      <Box bg={cardBg} p={6} borderRadius="lg" borderWidth="1px" borderColor={borderColor}>
        <Text>Loading reputation score...</Text>
      </Box>
    );
  }

  if (!reputationData || reputationData.reputation_score === null) {
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
              Cultural Sensitivity Assessment
            </Text>
            <IconButton
              icon={isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
              size="sm"
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label="Toggle details"
            />
          </HStack>

          <VStack spacing={1}>
            <CircularProgress
              value={100}
              size="180px"
              thickness="12px"
              color="#2ecc71"
              trackColor={trackColor}
            >
              <CircularProgressLabel>
                <VStack spacing={0}>
                  <Text fontSize="4xl" fontWeight="bold" color="#2ecc71">
                    100
                  </Text>
                  <Text fontSize="xs" color="gray.500">out of 100</Text>
                </VStack>
              </CircularProgressLabel>
            </CircularProgress>
          </VStack>

          <Badge colorScheme="green" fontSize="md" px={4} py={2} borderRadius="full">
            EXCELLENT
          </Badge>
          
          <Text fontSize="xs" color="gray.400" textAlign="center">
            (No posts analyzed yet)
          </Text>
        </VStack>
      </Box>
    );
  }

  const score = reputationData.reputation_score;
  const riskLevel = reputationData.risk_level;
  const riskDescription = reputationData.risk_description;

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
        {/* Header with Toggle */}
        <HStack width="100%" justify="space-between">
          <Text fontSize="lg" fontWeight="700">
            Cultural Sensitivity Assessment
          </Text>
          <IconButton
            icon={isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label="Toggle details"
          />
        </HStack>

        {/* Risk Assessment Gauge */}
        <VStack spacing={1}>
          <CircularProgress
            value={score}
            size="180px"
            thickness="12px"
            color={getScoreColor(score)}
            trackColor={trackColor}
          >
            <CircularProgressLabel>
              <VStack spacing={0}>
                <Text fontSize="4xl" fontWeight="bold" color={getScoreColor(score)}>
                  {score}
                </Text>
                <Text fontSize="xs" color="gray.500">out of 100</Text>
              </VStack>
            </CircularProgressLabel>
          </CircularProgress>
        </VStack>

        {/* Risk Level Badge */}
        <Badge 
          colorScheme={getRiskColor(riskLevel)} 
          fontSize="md" 
          px={4} 
          py={2} 
          borderRadius="full"
        >
          🔒 {riskLevel}
        </Badge>

        <Collapse in={isExpanded} animateOpacity>
          <VStack spacing={3} width="100%">
            {/* Risk Description */}
            <Box 
              bg={riskBg} 
              p={3} 
              borderRadius="md"
              borderWidth="1px"
              borderColor={riskBorder}
              width="100%"
            >
              <Text fontSize="xs" color={riskText} textAlign="center">
                {riskDescription}
              </Text>
            </Box>

            {/* Flagged Content Stats */}
            {reputationData.flagged_posts > 0 && (
              <Box 
                bg={flaggedBg} 
                p={3} 
                borderRadius="md"
                width="100%"
              >
                <HStack justify="center" spacing={2}>
                  <Text fontSize="sm" fontWeight="600" color="red.600">⚠️</Text>
                  <Text fontSize="xs" color={flaggedText}>
                    {reputationData.flagged_posts} flagged post{reputationData.flagged_posts !== 1 ? 's' : ''} 
                    ({reputationData.flagged_percentage}%)
                  </Text>
                </HStack>
              </Box>
            )}

            {/* Risk Scale */}
            <VStack spacing={2} width="100%" mt={2}>
              <Text fontSize="xs" fontWeight="600" color="gray.500">CULTURAL SENSITIVITY SCALE</Text>
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

            {/* Assessment Stats */}
            <Box 
              width="100%" 
              pt={3} 
              borderTopWidth="1px" 
              borderColor={borderColor}
            >
              <VStack spacing={1}>
                <Tooltip label="Risk assessment based on cultural sensitivity, policy violations, and content appropriateness">
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    Assessment based on {reputationData.total_analyzed_posts} post{reputationData.total_analyzed_posts !== 1 ? 's' : ''}
                  </Text>
                </Tooltip>
                <Text fontSize="xs" color="gray.400" textAlign="center" fontStyle="italic">
                  Purpose: Identify potential risks to organization
                </Text>
              </VStack>
            </Box>
          </VStack>
        </Collapse>
      </VStack>
    </Box>
  );
}
