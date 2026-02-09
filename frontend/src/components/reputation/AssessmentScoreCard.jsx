'use client';
import { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  useColorModeValue,
  Collapse,
  IconButton,
  Flex,
  Icon,
  Card,
  CardBody,
  Tooltip,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { FaShieldAlt, FaCheckCircle, FaGlobe, FaArrowUp, FaArrowDown, FaInfoCircle } from 'react-icons/fa';

// ============================================================
// EDITABLE CONFIGURATION - Adjust these values as needed
// ============================================================
const GAUGE_CONFIG = {
  // SVG dimensions
  viewBoxWidth: 260,
  viewBoxHeight: 230,
  
  // Arc center position
  centerX: 130,
  centerY: 120,
  
  // Arc properties
  arcRadius: 75,           // Radius of the colored arc
  arcStrokeWidth: 20,      // Thickness of the arc
  
  // Text markers position (distance from center)
  markerRadius: 118,       // How far the numbers (0, 40, 60, etc.) are from center
  markerFontSize: 12,      // Font size for the markers
  
  // Pointer/indicator properties
  pointerOuterRadius: 14,  // Outer circle of the score pointer
  pointerInnerRadius: 6,   // Inner circle of the score pointer
  pointerStrokeWidth: 4,   // Border width of pointer
  
  // Central score display position (percentage from top)
  scoreDisplayTop: '52%',  // Move down to create more space from arc
  scoreFontSize: '3xl',    // Size of the score number (78)
  labelFontSize: 'sm',     // Size of the label (Good/Excellent)
};

// Gradient colors - adjust percentages to control color distribution
// Red at 0%, Orange, Yellow, Green at 100%
const GRADIENT_STOPS = [
  { offset: '0%', color: '#FF1744' },    // Red
  { offset: '17%', color: '#FF5722' },   // Deep Orange
  { offset: '34%', color: '#FF9100' },   // Orange  
  { offset: '51%', color: '#FFC107' },   // Yellow
  { offset: '68%', color: '#CDDC39' },   // Lime
  { offset: '84%', color: '#8BC34A' },   // Light Green
  { offset: '100%', color: '#00C853' },  // Green
];

// Score thresholds and their colors
const SCORE_THRESHOLDS = [
  { min: 85, label: 'Excellent', color: '#00C853' },
  { min: 75, label: 'Good', color: '#8BC34A' },
  { min: 60, label: 'Average', color: '#FFC107' },
  { min: 40, label: 'Poor', color: '#FF9100' },
  { min: 0, label: 'Critical', color: '#FF1744' },
];

// Score markers to display around the arc (empty to hide numbers)
const SCORE_MARKERS = [];

// ============================================================
// END OF EDITABLE CONFIGURATION
// ============================================================

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

function getScoreInfo(score) {
  for (const threshold of SCORE_THRESHOLDS) {
    if (score >= threshold.min) {
      return { label: threshold.label, color: threshold.color };
    }
  }
  return SCORE_THRESHOLDS[SCORE_THRESHOLDS.length - 1];
}

// Score tooltips for the compact cards
const SCORE_TOOLTIPS = {
  Accuracy: "Measures factual correctness and source reliability. Higher scores mean verified facts and credible sources.",
  Compliance: "Evaluates adherence to company policies and regulations. Higher scores indicate better policy alignment.",
  Cultural: "Assesses cultural awareness and sensitivity. Higher scores mean more inclusive, respectful content.",
};

// Compact Score Card Component
function CompactScoreCard({ label, score, icon, iconColor, description, isExpanded, onToggle }) {
  const cardBg = useColorModeValue('white', 'gray.750');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const tooltipBg = useColorModeValue('gray.800', 'gray.700');
  const scoreInfo = getScoreInfo(score);

  return (
    <Box
      bg={cardBg}
      p={3}
      borderRadius="lg"
      borderWidth="1px"
      borderColor={borderColor}
      cursor="pointer"
      onClick={onToggle}
      transition="all 0.2s ease"
      _hover={{ borderColor: iconColor, shadow: 'sm' }}
    >
      <HStack justify="space-between" align="center">
        <HStack spacing={2} flex="1">
          <Icon as={icon} color={iconColor} boxSize={4} />
          <Text fontSize="xs" fontWeight="600" color={textColor}>{label}</Text>
          <Tooltip 
            label={SCORE_TOOLTIPS[label] || description} 
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
            <Box as="span" cursor="help" onClick={(e) => e.stopPropagation()}>
              <Icon as={FaInfoCircle} color={textColorSecondary} boxSize={3} opacity={0.7} />
            </Box>
          </Tooltip>
        </HStack>
        <HStack spacing={2}>
          <Text fontSize="lg" fontWeight="bold" color={scoreInfo.color}>{score}</Text>
          <IconButton
            icon={isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
            size="xs"
            variant="ghost"
            aria-label="Toggle details"
            color={textColorSecondary}
          />
        </HStack>
      </HStack>

      <Collapse in={isExpanded} animateOpacity>
        <Box pt={2} mt={2} borderTopWidth="1px" borderColor={borderColor}>
          <Text fontSize="xs" color={textColorSecondary}>
            {description}
          </Text>
        </Box>
      </Collapse>
    </Box>
  );
}

export default function AssessmentScoreCard({ user }) {
  const [expandedDetail, setExpandedDetail] = useState(null);
  
  // Demo data
  const [scores] = useState({
    overall: 78,
    accuracy: 85,
    compliance: 72,
    cultural: 76,
    change: +12,
  });

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const trackColor = useColorModeValue('#E8E8E8', '#3A3A3A');

  const scoreInfo = getScoreInfo(scores.overall);

  const toggleDetail = (detail) => {
    setExpandedDetail(expandedDetail === detail ? null : detail);
  };

  // Arc angles
  const startAngle = 225;  // Bottom left (score 0, RED)
  const endAngle = 495;    // Bottom right (score 100, GREEN)
  
  // Calculate pointer angle based on score
  const scoreAngle = startAngle + (scores.overall / 100) * 270;
  const pointerPos = polarToCartesian(
    GAUGE_CONFIG.centerX, 
    GAUGE_CONFIG.centerY, 
    GAUGE_CONFIG.arcRadius, 
    scoreAngle
  );

  // Generate marker positions
  const markerPositions = SCORE_MARKERS.map(value => ({
    value,
    angle: 225 + (value / 100) * 270
  }));

  const cfg = GAUGE_CONFIG;

  return (
    <Card bg={cardBg} boxShadow="sm" borderRadius="xl" borderWidth="1px" borderColor={borderColor} overflow="hidden">
      <CardBody p={4}>
        {/* Header */}
        <HStack spacing={2} mb={4}>
          <Icon as={FaShieldAlt} boxSize={4} color="blue.600" />
          <Text fontSize="sm" fontWeight="700" color={textColor}>
            Assessment Scores
          </Text>
          <Tooltip 
            label="Your overall content assessment score combines Accuracy, Compliance, and Cultural Sensitivity. Higher scores indicate better content quality and lower risk. Click on individual scores below for detailed breakdowns."
            placement="top" 
            hasArrow 
            bg={useColorModeValue('gray.800', 'gray.700')}
            color="white"
            fontSize="xs"
            px={3}
            py={2}
            borderRadius="md"
            maxW="280px"
          >
            <Box as="span" cursor="help">
              <Icon as={FaInfoCircle} color={textColorSecondary} boxSize={3.5} />
            </Box>
          </Tooltip>
        </HStack>

        {/* Main Content - Two Column Layout */}
        <Flex direction={{ base: 'column', md: 'row' }} gap={4}>
          {/* Left: Credit Score Style Gauge */}
          <Box flex="1" display="flex" justifyContent="center" alignItems="center" minH="220px">
            <Box position="relative" width={`${cfg.viewBoxWidth}px`} height={`${cfg.viewBoxHeight}px`}>
              <svg viewBox={`0 0 ${cfg.viewBoxWidth} ${cfg.viewBoxHeight}`} style={{ width: '100%', height: '100%' }}>
                {/* Gradient definition */}
                <defs>
                  <linearGradient id="gaugeGradientEditable" x1="0%" y1="0%" x2="100%" y2="0%">
                    {GRADIENT_STOPS.map((stop, idx) => (
                      <stop key={idx} offset={stop.offset} stopColor={stop.color} />
                    ))}
                  </linearGradient>
                </defs>
                
                {/* Background track */}
                <path 
                  d={describeArc(cfg.centerX, cfg.centerY, cfg.arcRadius, startAngle, endAngle)} 
                  fill="none" 
                  stroke={trackColor}
                  strokeWidth={cfg.arcStrokeWidth} 
                  strokeLinecap="round"
                />
                
                {/* Colored arc with gradient */}
                <path 
                  d={describeArc(cfg.centerX, cfg.centerY, cfg.arcRadius, startAngle, endAngle)} 
                  fill="none" 
                  stroke="url(#gaugeGradientEditable)" 
                  strokeWidth={cfg.arcStrokeWidth} 
                  strokeLinecap="round"
                />

                {/* Score pointer on the arc */}
                <circle
                  cx={pointerPos.x}
                  cy={pointerPos.y}
                  r={cfg.pointerOuterRadius}
                  fill="white"
                  stroke={scoreInfo.color}
                  strokeWidth={cfg.pointerStrokeWidth}
                />
                <circle
                  cx={pointerPos.x}
                  cy={pointerPos.y}
                  r={cfg.pointerInnerRadius}
                  fill={scoreInfo.color}
                />

                {/* Score markers outside the arc */}
                {markerPositions.map((marker) => {
                  const pos = polarToCartesian(cfg.centerX, cfg.centerY, cfg.markerRadius, marker.angle);
                  return (
                    <text
                      key={marker.value}
                      x={pos.x}
                      y={pos.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize={cfg.markerFontSize}
                      fill="#6B7280"
                      fontWeight="600"
                    >
                      {marker.value}
                    </text>
                  );
                })}
              </svg>

              {/* Central Score Display */}
              <Box
                position="absolute"
                top={cfg.scoreDisplayTop}
                left="50%"
                transform="translate(-50%, -50%)"
                textAlign="center"
              >
                <Text fontSize={cfg.scoreFontSize} fontWeight="800" color={scoreInfo.color} lineHeight="1">
                  {scores.overall}
                </Text>
                <Text fontSize={cfg.labelFontSize} fontWeight="600" color={scoreInfo.color} mt={1}>
                  {scoreInfo.label}
                </Text>
                <HStack justify="center" spacing={1} mt={2}>
                  <Icon 
                    as={scores.change >= 0 ? FaArrowUp : FaArrowDown} 
                    color={scores.change >= 0 ? '#00C853' : '#FF1744'} 
                    boxSize={3} 
                  />
                  <Text fontSize="xs" color={scores.change >= 0 ? '#00C853' : '#FF1744'} fontWeight="600">
                    {scores.change >= 0 ? '+' : ''}{scores.change} pts
                  </Text>
                </HStack>
                <Text fontSize="xs" color={textColorSecondary}>since last month</Text>
              </Box>
            </Box>
          </Box>

          {/* Right: Category Scores */}
          <VStack flex="1" spacing={2} align="stretch" justify="center">
            <CompactScoreCard
              label="Accuracy"
              score={scores.accuracy}
              icon={FaCheckCircle}
              iconColor="#3B82F6"
              description="Factual correctness and truthfulness of content."
              isExpanded={expandedDetail === 'accuracy'}
              onToggle={() => toggleDetail('accuracy')}
            />
            <CompactScoreCard
              label="Compliance"
              score={scores.compliance}
              icon={FaShieldAlt}
              iconColor="#10B981"
              description="Adherence to policies and guidelines."
              isExpanded={expandedDetail === 'compliance'}
              onToggle={() => toggleDetail('compliance')}
            />
            <CompactScoreCard
              label="Cultural"
              score={scores.cultural}
              icon={FaGlobe}
              iconColor="#3b82f6"
              description="Sensitivity across different cultural contexts."
              isExpanded={expandedDetail === 'cultural'}
              onToggle={() => toggleDetail('cultural')}
            />
          </VStack>
        </Flex>
      </CardBody>
    </Card>
  );
}
