'use client';
import {
  Box,
  VStack,
  HStack,
  Text,
  Progress,
  SimpleGrid,
  useColorModeValue,
  Icon,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Tooltip,
} from '@chakra-ui/react';
import { FaCheckCircle, FaShieldAlt, FaGlobe, FaArrowUp, FaArrowDown, FaInfoCircle } from 'react-icons/fa';

const scoreTooltips = {
  accuracy: {
    title: "Accuracy Score",
    description: "Measures factual correctness and source reliability of content. Higher scores indicate verified facts, credible sources, and minimal misinformation risk.",
    breakdown: {
      factual_accuracy: "How well facts are verified against reliable sources",
      source_credibility: "Quality and trustworthiness of referenced sources", 
      claim_verification: "Extent to which claims are backed by evidence",
      context_accuracy: "Whether information is presented in proper context"
    }
  },
  compliance: {
    title: "Compliance Score",
    description: "Evaluates adherence to company policies, industry regulations, and legal requirements. Higher scores mean better alignment with organizational guidelines.",
    breakdown: {
      policy_adherence: "Alignment with internal company policies",
      regulatory_compliance: "Compliance with industry regulations",
      brand_guidelines: "Consistency with brand voice and messaging",
      legal_requirements: "Adherence to legal and disclosure requirements"
    }
  },
  cultural: {
    title: "Cultural Sensitivity Score",
    description: "Assesses content for cultural awareness and sensitivity across different regions and demographics. Higher scores indicate inclusive, respectful content.",
    breakdown: {
      cultural_awareness: "Understanding of cultural nuances and contexts",
      inclusive_language: "Use of inclusive and respectful terminology",
      regional_sensitivity: "Appropriateness for different geographic regions",
      demographic_consideration: "Consideration of diverse audience demographics"
    }
  }
};

function ScoreBreakdownCard({ title, icon, iconColor, average, breakdown, trend, onClick, tooltipKey }) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const progressTrackColor = useColorModeValue('gray.100', 'gray.700');
  const tooltipBg = useColorModeValue('gray.800', 'gray.700');

  const tooltip = scoreTooltips[tooltipKey];

  const getScoreColor = (score) => {
    if (score >= 85) return 'green';
    if (score >= 75) return 'blue';
    if (score >= 60) return 'yellow';
    if (score >= 40) return 'orange';
    return 'red';
  };

  const scoreColor = getScoreColor(average);

  const getBreakdownTooltip = (key) => {
    if (tooltip?.breakdown && tooltip.breakdown[key]) {
      return tooltip.breakdown[key];
    }
    return null;
  };

  return (
    <Card 
      bg={cardBg} 
      borderWidth="1px" 
      borderColor={borderColor} 
      cursor={onClick ? 'pointer' : 'default'}
      onClick={onClick}
      transition="all 0.2s"
      _hover={onClick ? { shadow: 'md', borderColor: iconColor } : {}}
    >
      <CardHeader pb={2}>
        <HStack justify="space-between">
          <HStack spacing={2}>
            <Icon as={icon} color={iconColor} boxSize={{ base: 4, md: 5 }} />
            <Heading size={{ base: 'xs', md: 'sm' }} color={textColor}>{title}</Heading>
            {tooltip && (
              <Tooltip 
                label={tooltip.description} 
                placement="top" 
                hasArrow 
                bg={tooltipBg}
                color="white"
                fontSize="xs"
                px={3}
                py={2}
                borderRadius="md"
                maxW="250px"
              >
                <Box as="span" cursor="help">
                  <Icon as={FaInfoCircle} color={textColorSecondary} boxSize={3} />
                </Box>
              </Tooltip>
            )}
          </HStack>
          <Box>
            <Text fontSize={{ base: 'xl', md: '2xl' }} fontWeight="bold" color={`${scoreColor}.500`}>
              {average}
            </Text>
          </Box>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack spacing={3} align="stretch">
          {breakdown && Object.entries(breakdown).map(([key, value]) => (
            <Box key={key}>
              <HStack justify="space-between" mb={1}>
                <HStack spacing={1}>
                  <Text fontSize={{ base: 'xs', md: 'sm' }} color={textColorSecondary} textTransform="capitalize">
                    {key.replace(/_/g, ' ')}
                  </Text>
                  {getBreakdownTooltip(key) && (
                    <Tooltip 
                      label={getBreakdownTooltip(key)} 
                      placement="top" 
                      hasArrow
                      bg={tooltipBg}
                      color="white"
                      fontSize="xs"
                      px={2}
                      py={1}
                      borderRadius="md"
                      maxW="200px"
                    >
                      <Box as="span" cursor="help">
                        <Icon as={FaInfoCircle} color={textColorSecondary} boxSize={2.5} opacity={0.6} />
                      </Box>
                    </Tooltip>
                  )}
                </HStack>
                <Text fontSize={{ base: 'xs', md: 'sm' }} fontWeight="600" color={textColor}>
                  {typeof value === 'number' ? value.toFixed(1) : value}
                </Text>
              </HStack>
              <Progress 
                value={typeof value === 'number' ? value : 0} 
                max={100}
                size="sm" 
                colorScheme={getScoreColor(value)}
                bg={progressTrackColor}
                borderRadius="full"
              />
            </Box>
          ))}
          
          {trend && trend.length > 0 && (
            <HStack justify="space-between" pt={2} borderTopWidth="1px" borderColor={borderColor}>
              <Text fontSize="xs" color={textColorSecondary}>6-month trend</Text>
              <HStack spacing={1}>
                {trend.length >= 2 && (
                  <>
                    <Icon 
                      as={trend[trend.length - 1] >= trend[0] ? FaArrowUp : FaArrowDown} 
                      color={trend[trend.length - 1] >= trend[0] ? 'green.500' : 'red.500'}
                      boxSize={3}
                    />
                    <Text fontSize="xs" color={trend[trend.length - 1] >= trend[0] ? 'green.500' : 'red.500'}>
                      {Math.abs(trend[trend.length - 1] - trend[0]).toFixed(1)} pts
                    </Text>
                  </>
                )}
              </HStack>
            </HStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

export default function AssessmentScoreDetails({ scoreDetails, onCardClick }) {
  const textColor = useColorModeValue('gray.800', 'white');
  
  if (!scoreDetails) {
    return (
      <Box p={4} textAlign="center">
        <Text color={textColor}>No score data available</Text>
      </Box>
    );
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={{ base: 3, md: 4 }}>
      <ScoreBreakdownCard
        title="Accuracy"
        icon={FaCheckCircle}
        iconColor="#3B82F6"
        average={scoreDetails.accuracy?.average || 0}
        breakdown={scoreDetails.accuracy?.breakdown}
        trend={scoreDetails.accuracy?.trend}
        onClick={onCardClick ? () => onCardClick('accuracy') : undefined}
        tooltipKey="accuracy"
      />
      <ScoreBreakdownCard
        title="Compliance"
        icon={FaShieldAlt}
        iconColor="#10B981"
        average={scoreDetails.compliance?.average || 0}
        breakdown={scoreDetails.compliance?.breakdown}
        trend={scoreDetails.compliance?.trend}
        onClick={onCardClick ? () => onCardClick('compliance') : undefined}
        tooltipKey="compliance"
      />
      <ScoreBreakdownCard
        title="Cultural"
        icon={FaGlobe}
        iconColor="#3b82f6"
        average={scoreDetails.cultural?.average || 0}
        breakdown={scoreDetails.cultural?.breakdown}
        trend={scoreDetails.cultural?.trend}
        onClick={onCardClick ? () => onCardClick('cultural') : undefined}
        tooltipKey="cultural"
      />
    </SimpleGrid>
  );
}
