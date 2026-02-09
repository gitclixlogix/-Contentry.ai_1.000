'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Avatar,
  useColorModeValue,
  Collapse,
  IconButton,
  CircularProgress,
  CircularProgressLabel,
  Badge,
  Flex,
  Icon,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { FaChartBar, FaClock } from 'react-icons/fa';
import { getImageUrl } from '@/lib/api';
// Note: axios import removed - using mock data until API endpoint is ready

// Helper function to create SVG arc paths
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
  const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  };
}

function describeArc(x, y, radius, startAngle, endAngle) {
  const start = polarToCartesian(x, y, radius, endAngle);
  const end = polarToCartesian(x, y, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return [
    "M", start.x, start.y,
    "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
  ].join(" ");
}

export default function RiskGauge({ user }) {
  const [reputationData, setReputationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const scoreBreakdownBg = useColorModeValue('gray.50', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const trackColor = useColorModeValue('gray.100', 'gray.700');

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
      cultural_sensitivity_score: null,
      compliance_score: null,
      total_analyzed_posts: 0,
    });
    setLoading(false);
  };

  const getRiskLevel = (score) => {
    if (score >= 85) return { level: 'EXCELLENT', color: '#2ecc71' };
    if (score >= 75) return { level: 'GOOD', color: '#95d44d' };
    if (score >= 60) return { level: 'AVERAGE', color: '#f9e04c' };
    if (score >= 40) return { level: 'POOR', color: '#f39c12' };
    return { level: 'VERY POOR', color: '#e74c3c' };
  };

  if (loading) {
    return (
      <Box bg={cardBg} p={6} borderRadius="lg" borderWidth="1px" borderColor={borderColor}>
        <Text>Loading risk assessment...</Text>
      </Box>
    );
  }

  // Check if user has any analyzed posts
  const hasAnalyzedPosts = reputationData?.total_analyzed_posts > 0;
  
  // Start with 100/100 score when no posts, then use actual scores
  const overallScore = hasAnalyzedPosts ? (reputationData?.reputation_score ?? 100) : 100;
  const culturalScore = hasAnalyzedPosts ? (reputationData?.cultural_sensitivity_score ?? 100) : 100;
  const complianceScore = hasAnalyzedPosts ? (reputationData?.compliance_score ?? 100) : 100;
  
  const riskInfo = getRiskLevel(overallScore);
  
  // Calculate indicator position on the gauge
  // The gauge goes from -180° (VERY POOR) to +36° (EXCELLENT)
  // Score 0 = -180°, Score 100 = +36°
  const totalAngleRange = 216; // From -180 to +36
  const scoreRange = 100;
  const angle = -180 + (overallScore / scoreRange) * totalAngleRange;
  
  // Convert angle to x,y coordinates for the indicator
  const indicatorCoords = polarToCartesian(100, 110, 80, angle);
  const indicatorX = indicatorCoords.x;
  const indicatorY = indicatorCoords.y;

  return (
    <Box 
      bg={cardBg} 
      p={8} 
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
            Overall Risk Assessment
          </Text>
          <IconButton
            icon={isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label="Toggle details"
          />
        </HStack>

        <Box position="relative" width="100%" height="220px">
          {/* Semi-circular gauge background with thicker bars */}
          <svg
            viewBox="0 0 200 120"
            style={{
              width: '100%',
              height: '100%',
              position: 'absolute',
              top: 0,
              left: 0,
            }}
          >
            {/* Background arc segments - THICKER (strokeWidth=16) */}
            <path
              d={describeArc(100, 110, 80, -180, -108)}
              fill="none"
              stroke="#e74c3c"
              strokeWidth="16"
              opacity="0.3"
            />
            <path
              d={describeArc(100, 110, 80, -108, -72)}
              fill="none"
              stroke="#f39c12"
              strokeWidth="16"
              opacity="0.3"
            />
            <path
              d={describeArc(100, 110, 80, -72, -36)}
              fill="none"
              stroke="#f9e04c"
              strokeWidth="16"
              opacity="0.3"
            />
            <path
              d={describeArc(100, 110, 80, -36, 0)}
              fill="none"
              stroke="#95d44d"
              strokeWidth="16"
              opacity="0.3"
            />
            <path
              d={describeArc(100, 110, 80, 0, 36)}
              fill="none"
              stroke="#2ecc71"
              strokeWidth="16"
              opacity="0.3"
            />

            {/* Active indicator - WHITE TRIANGLE */}
            <polygon
              points={`${indicatorX},${indicatorY - 10} ${indicatorX - 8},${indicatorY + 10} ${indicatorX + 8},${indicatorY + 10}`}
              fill="white"
              stroke={riskInfo.color}
              strokeWidth="2"
            />
          </svg>

          {/* Risk level labels */}
          <Text
            position="absolute"
            left="10px"
            bottom="10px"
            fontSize="xs"
            color="#e74c3c"
            fontWeight="600"
          >
            VERY POOR
          </Text>
          <Text
            position="absolute"
            right="10px"
            bottom="10px"
            fontSize="xs"
            color="#2ecc71"
            fontWeight="600"
          >
            EXCELLENT
          </Text>

          {/* User Avatar in center */}
          <Box
            position="absolute"
            top="118px"
            left="50%"
            transform="translateX(-50%)"
          >
            <Avatar
              size="lg"
              name={user?.full_name}
              src={getImageUrl(user?.profile_picture)}
              border="3px solid"
              borderColor="white"
            />
          </Box>
        </Box>

        {/* Risk Level Badge */}
        <Badge
          colorScheme={
            overallScore >= 85 ? 'green' :
            overallScore >= 75 ? 'blue' :
            overallScore >= 60 ? 'yellow' :
            overallScore >= 40 ? 'orange' : 'red'
          }
          fontSize="md"
          px={4}
          py={2}
          borderRadius="full"
        >
          {riskInfo.level}
        </Badge>

        <Box textAlign="center" mt={4}>
          {/* Score Display */}
          <Text fontSize="3xl" fontWeight="bold" color={riskInfo.color} textAlign="center">
            {overallScore}/100
          </Text>
          <Text fontSize="xs" color="gray.500" textAlign="center" fontWeight="600">
            OVERALL RISK SCORE
          </Text>
          {!hasAnalyzedPosts && (
            <Text fontSize="xs" color="gray.400" textAlign="center" mt={1}>
              (No posts analyzed yet)
            </Text>
          )}
        </Box>
          
        <Collapse in={isExpanded} animateOpacity>
          <VStack spacing={3} width="100%" mt={2}>
            {/* Score Breakdown */}
            <Box width="100%" p={3} bg={scoreBreakdownBg} borderRadius="md">
              <VStack spacing={1} fontSize="xs">
                <HStack justify="space-between" width="100%">
                  <Text color="gray.600">Compliance:</Text>
                  <Text fontWeight="600" color={complianceScore === 100 ? 'green.500' : 'red.500'}>
                    {complianceScore}/100
                  </Text>
                </HStack>
                <HStack justify="space-between" width="100%">
                  <Text color="gray.600">Cultural Sensitivity:</Text>
                  <Text fontWeight="600">{culturalScore}/100</Text>
                </HStack>
              </VStack>
            </Box>

            {/* Risk Scale Legend */}
            <VStack spacing={1} width="100%" fontSize="xs">
              <Text fontWeight="600" color="gray.500" mb={1}>RISK LEVEL BREAKDOWN</Text>
              <Box display="flex" justifyContent="space-between" width="100%">
                <Text color="#e74c3c" fontWeight="600">0-39: VERY POOR</Text>
              </Box>
              <Box display="flex" justifyContent="space-between" width="100%">
                <Text color="#f39c12" fontWeight="600">40-59: POOR</Text>
              </Box>
              <Box display="flex" justifyContent="space-between" width="100%">
                <Text color="#f9e04c" fontWeight="600">60-74: AVERAGE</Text>
              </Box>
              <Box display="flex" justifyContent="space-between" width="100%">
                <Text color="#95d44d" fontWeight="600">75-84: GOOD</Text>
              </Box>
              <Box display="flex" justifyContent="space-between" width="100%">
                <Text color="#2ecc71" fontWeight="600">85-100: EXCELLENT</Text>
              </Box>
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
                    ⚠️ {reputationData.flagged_posts} flagged post{reputationData.flagged_posts !== 1 ? 's' : ''}
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
