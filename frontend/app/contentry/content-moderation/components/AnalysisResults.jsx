'use client';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Badge,
  VStack,
  HStack,
  Icon,
  Grid,
  Text,
  Heading,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Progress,
  Divider,
} from '@chakra-ui/react';
import { FaCheckCircle, FaGlobe } from 'react-icons/fa';

/**
 * Reusable component for displaying content analysis results
 * @param {Object} analysis - The analysis object containing compliance, accuracy, and cultural analysis
 * @param {string} title - Optional title for the analysis section (default: "Overall Analysis Summary")
 * @param {boolean} compact - If true, hides the overall summary box and only shows detailed scores
 */
export default function AnalysisResults({ analysis, title = "Overall Analysis Summary", compact = false }) {
  // ALL color mode values MUST be declared at the top before any conditional returns
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const culturalDimBg = useColorModeValue('gray.50', 'gray.700');
  const culturalDimBorder = useColorModeValue('gray.200', 'gray.600');
  const culturalDimTextColor = useColorModeValue('gray.800', 'white');
  const culturalRiskColor = useColorModeValue('orange.700', 'orange.300');
  const culturalRecColor = useColorModeValue('green.700', 'green.300');
  
  // Summary box colors
  const summaryBg = useColorModeValue('blue.50', 'blue.900');
  const summaryBorderColor = useColorModeValue('blue.300', 'blue.600');
  
  // Compliance accordion colors - Changed to blue to match other sections
  const complianceBorderColor = useColorModeValue('blue.200', 'blue.600');
  const complianceBg = useColorModeValue('blue.50', 'blue.900');
  const complianceHoverBg = useColorModeValue('blue.100', 'blue.800');
  const complianceExpandedBg = useColorModeValue('blue.100', 'blue.800');
  const compliancePanelBg = useColorModeValue('gray.50', 'gray.700');
  const complianceDetailBg = useColorModeValue('white', 'gray.800');
  
  // Accuracy accordion colors
  const accuracyBorderColor = useColorModeValue('blue.200', 'blue.600');
  const accuracyBg = useColorModeValue('blue.50', 'blue.900');
  const accuracyHoverBg = useColorModeValue('blue.100', 'blue.800');
  const accuracyExpandedBg = useColorModeValue('blue.100', 'blue.800');
  
  // Cultural accordion colors
  const culturalBorderColor = useColorModeValue('blue.200', 'blue.600');
  const culturalBg = useColorModeValue('blue.50', 'blue.900');
  const culturalHoverBg = useColorModeValue('blue.100', 'blue.800');
  const culturalExpandedBg = useColorModeValue('blue.100', 'blue.800');

  // Early return AFTER all hooks are declared
  if (!analysis) {
    return null;
  }

  // Calculate scores - use backend-calculated scores when available, fallback to derived values
  // Priority: backend score > analysis sub-object score > fallback
  const complianceScore = analysis.compliance_score ?? (
    analysis.compliance_analysis?.severity === 'none' ? 100 : 
    analysis.compliance_analysis?.severity === 'low' ? 70 :
    analysis.compliance_analysis?.severity === 'medium' ? 50 : 30
  );
  
  // Accuracy score: use top-level, then from accuracy_analysis object
  const accuracyScore = analysis.accuracy_score ?? analysis.accuracy_analysis?.accuracy_score ?? 85;
  
  // For cultural score, calculate from dimensions if overall_score is not provided
  const calculateCulturalFromDimensions = () => {
    const dims = analysis.cultural_analysis?.dimensions;
    if (dims && dims.length > 0) {
      const totalScore = dims.reduce((sum, dim) => sum + (dim.score ?? 75), 0);
      return Math.round(totalScore / dims.length);
    }
    return 75;
  };
  
  // Cultural score: UNIFIED source - use the same value everywhere
  // Priority: top-level cultural_score > cultural_analysis.overall_score > calculated from dimensions
  const culturalScore = analysis.cultural_score ?? 
                        analysis.cultural_analysis?.overall_score ?? 
                        calculateCulturalFromDimensions();
  
  // Overall score: Use backend-calculated overall_score if available
  // Otherwise recalculate using weighted formula matching backend scoring service
  const calculateOverallScore = () => {
    // Apply weighted formula: Compliance(40%) + Cultural(30%) + Accuracy(30%)
    // With adjustments for risk scenarios
    if (complianceScore <= 40) {
      // Critical compliance - cap at 40
      return Math.min(40, Math.round((complianceScore * 0.5) + (culturalScore * 0.3) + (accuracyScore * 0.2)));
    } else if (complianceScore <= 60) {
      // High risk - increased compliance weight
      return Math.round((complianceScore * 0.5) + (culturalScore * 0.3) + (accuracyScore * 0.2));
    } else if (culturalScore <= 50) {
      // Reputation risk - increased cultural weight
      return Math.round((complianceScore * 0.4) + (culturalScore * 0.4) + (accuracyScore * 0.2));
    } else {
      // Standard weighting
      return Math.round((complianceScore * 0.4) + (culturalScore * 0.3) + (accuracyScore * 0.3));
    }
  };
  
  const avgScore = analysis.overall_score ?? calculateOverallScore();
  
  let overallStatus = avgScore >= 80 ? '✅ Excellent' : avgScore >= 60 ? '⚠️ Good with Minor Concerns' : '❌ Needs Improvement';
  
  const overallSummary = `${overallStatus}: This content scores ${avgScore}/100 overall. ${
    complianceScore >= 80 ? 'It complies with policies.' : 'Policy violations detected.'
  } ${
    accuracyScore >= 80 ? 'Information is accurate.' : 'Accuracy needs verification.'
  } ${
    culturalScore >= 80 ? 'Culturally appropriate for global audiences.' : 'May need cultural sensitivity adjustments.'
  }`;

  // Helper function to get score color - red if below 80
  const getScoreColor = (score) => score >= 80 ? 'green' : 'red';

  return (
    <VStack align="stretch" spacing={4}>
      {/* Overall Summary Section - Hidden in compact mode or if title is empty */}
      {!compact && (
        <Box>
          {title && (
            <HStack mb={3}>
              <Icon as={FaCheckCircle} color="blue.500" boxSize={4} />
              <Heading size="sm" color={textColor}>{title}</Heading>
            </HStack>
          )}
          
          <Box 
            bg={summaryBg} 
            p={4} 
            borderRadius="md" 
            borderWidth="1px"
            borderColor={summaryBorderColor}
          >
            <Text fontSize="sm" lineHeight="1.7" fontWeight="500" color={textColor}>
              {overallSummary}
            </Text>
            
            {/* Score Indicators - All 4 Scores */}
            <Grid templateColumns="repeat(4, 1fr)" gap={3} mt={4}>
              <Box textAlign="center">
                <Text fontSize="xs" color={textColorSecondary} mb={1} fontWeight="600">Overall</Text>
                <Badge 
                  colorScheme={getScoreColor(avgScore)}
                  fontSize="sm"
                  px={2}
                  py={0.5}
                >
                  <Text color={avgScore < 80 ? 'red.600' : undefined}>{avgScore}/100</Text>
                </Badge>
              </Box>
              <Box textAlign="center">
                <Text fontSize="xs" color={textColorSecondary} mb={1} fontWeight="600">Compliance</Text>
                <Badge 
                  colorScheme={getScoreColor(complianceScore)}
                  fontSize="sm"
                  px={2}
                  py={0.5}
                >
                  <Text color={complianceScore < 80 ? 'red.600' : undefined}>{complianceScore}/100</Text>
                </Badge>
              </Box>
              <Box textAlign="center">
                <Text fontSize="xs" color={textColorSecondary} mb={1} fontWeight="600">Accuracy</Text>
                <Badge 
                  colorScheme={getScoreColor(accuracyScore)}
                  fontSize="sm"
                  px={2}
                  py={0.5}
                >
                  <Text color={accuracyScore < 80 ? 'red.600' : undefined}>{accuracyScore}/100</Text>
                </Badge>
              </Box>
              <Box textAlign="center">
                <Text fontSize="xs" color={textColorSecondary} mb={1} fontWeight="600">Cultural</Text>
                <Badge 
                  colorScheme={getScoreColor(culturalScore)}
                  fontSize="sm"
                  px={2}
                  py={0.5}
                >
                  <Text color={culturalScore < 80 ? 'red.600' : undefined}>{culturalScore}/100</Text>
                </Badge>
              </Box>
            </Grid>
          </Box>
        </Box>
      )}

      {/* Expandable Sections */}
      <Accordion allowMultiple>
        {/* 1. Compliance Analysis */}
        <AccordionItem 
          border="1px solid"
          borderColor={complianceBorderColor}
          borderRadius="md"
          mb={3}
        >
          <AccordionButton 
            bg={complianceBg}
            _hover={{ bg: complianceHoverBg }}
            _expanded={{ bg: complianceExpandedBg }}
            borderRadius="md"
            p={3}
          >
            <Box flex="1" textAlign="left">
              <HStack spacing={2}>
                <Icon as={FaCheckCircle} color="blue.500" boxSize={4} />
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  Compliance Analysis
                </Text>
                <Badge 
                  colorScheme={getScoreColor(complianceScore)}
                  fontSize="xs"
                >
                  <Text color={complianceScore < 80 ? 'red.600' : undefined}>{complianceScore}/100</Text>
                </Badge>
              </HStack>
              <Text fontSize="xs" color={textColorSecondary} mt={0.5} ml={6}>
                Policy compliance and violation check
              </Text>
            </Box>
            <AccordionIcon color={textColor} boxSize={5} />
          </AccordionButton>
          <AccordionPanel pb={3} pt={3}>
            {/* Only show summary if it's not raw JSON */}
            {analysis.summary && !analysis.summary.trim().startsWith('{') && !analysis.summary.trim().startsWith('"flagged') && (
              <Box 
                bg={compliancePanelBg} 
                p={4} 
                borderRadius="md" 
                mb={3}
              >
                <Text fontSize="sm" lineHeight="1.6" whiteSpace="pre-wrap" color={textColor}>
                  {analysis.summary}
                </Text>
              </Box>
            )}

            {analysis.issues && analysis.issues.length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>Issues Found:</Text>
                <VStack align="stretch" pl={4}>
                  {analysis.issues.map((issue, idx) => (
                    <Text key={idx} fontSize="sm" color="red.500">• {issue}</Text>
                  ))}
                </VStack>
              </Box>
            )}
            
            {analysis.compliance_analysis && (
              <Box mt={3} p={3} bg={complianceDetailBg} borderRadius="md" borderWidth="1px">
                {/* Severity Badge */}
                <HStack mb={3}>
                  <Text fontSize="sm" fontWeight="600" color={textColor}>Severity:</Text>
                  <Badge 
                    colorScheme={
                      analysis.compliance_analysis.severity === 'critical' || analysis.compliance_analysis.severity === 'severe' ? 'red' :
                      analysis.compliance_analysis.severity === 'high' ? 'orange' :
                      analysis.compliance_analysis.severity === 'moderate' ? 'yellow' : 'green'
                    }
                    fontSize="xs"
                    textTransform="capitalize"
                  >
                    {analysis.compliance_analysis.severity || 'None'}
                  </Badge>
                </HStack>
                
                {/* Explanation */}
                {analysis.compliance_analysis.explanation && (
                  <Box mb={3} p={2} bg={summaryBg} borderRadius="md">
                    <Text fontSize="sm" color={textColor} lineHeight="1.6">
                      {analysis.compliance_analysis.explanation}
                    </Text>
                  </Box>
                )}
                
                {/* Employment Law Violations Section */}
                {analysis.compliance_analysis.employment_law_check?.violations_found && (
                  <Box mb={3}>
                    <HStack mb={2}>
                      <Text fontSize="sm" fontWeight="600" color="red.600">⚠️ Employment Law Violations Detected</Text>
                      <Badge colorScheme="red" fontSize="xs">
                        {analysis.compliance_analysis.employment_law_check.violation_count} issues
                      </Badge>
                    </HStack>
                    
                    {/* Violation Types */}
                    {analysis.compliance_analysis.employment_law_check.violation_types?.length > 0 && (
                      <Box mb={2}>
                        <Text fontSize="xs" fontWeight="600" color={textColorSecondary} mb={1}>Violation Types:</Text>
                        <HStack spacing={2} flexWrap="wrap">
                          {analysis.compliance_analysis.employment_law_check.violation_types.map((type, idx) => (
                            <Badge key={idx} colorScheme="red" variant="subtle" fontSize="xs" textTransform="capitalize">
                              {type.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </HStack>
                      </Box>
                    )}
                    
                    {/* Specific Issues */}
                    {analysis.compliance_analysis.employment_law_check.specific_issues?.length > 0 && (
                      <Box mb={3} p={2} bg="red.50" _dark={{ bg: 'red.900' }} borderRadius="md">
                        <Text fontSize="xs" fontWeight="600" color="red.700" _dark={{ color: 'red.200' }} mb={1}>
                          Specific Issues Found:
                        </Text>
                        <VStack align="stretch" spacing={1}>
                          {analysis.compliance_analysis.employment_law_check.specific_issues.map((issue, idx) => (
                            <HStack key={idx} align="start" spacing={2}>
                              <Text color="red.500" fontSize="sm">•</Text>
                              <Text fontSize="sm" color="red.700" _dark={{ color: 'red.200' }}>{issue}</Text>
                            </HStack>
                          ))}
                        </VStack>
                      </Box>
                    )}
                    
                    {/* Recommendations */}
                    {analysis.compliance_analysis.employment_law_check.recommendations?.length > 0 && (
                      <Box p={2} bg="green.50" _dark={{ bg: 'green.900' }} borderRadius="md">
                        <Text fontSize="xs" fontWeight="600" color="green.700" _dark={{ color: 'green.200' }} mb={1}>
                          💡 Recommendations:
                        </Text>
                        <VStack align="stretch" spacing={1}>
                          {analysis.compliance_analysis.employment_law_check.recommendations.slice(0, 5).map((rec, idx) => (
                            <HStack key={idx} align="start" spacing={2}>
                              <Text color="green.500" fontSize="sm">✓</Text>
                              <Text fontSize="sm" color="green.700" _dark={{ color: 'green.200' }}>{rec}</Text>
                            </HStack>
                          ))}
                        </VStack>
                      </Box>
                    )}
                    
                    {/* Analysis Method Badge */}
                    {analysis.compliance_analysis.employment_law_check.models_used && (
                      <HStack mt={2} spacing={2}>
                        <Text fontSize="xs" color={textColorSecondary}>Analyzed by:</Text>
                        {analysis.compliance_analysis.employment_law_check.models_used.map((model, idx) => (
                          <Badge key={idx} colorScheme="purple" variant="outline" fontSize="xs">
                            {model}
                          </Badge>
                        ))}
                      </HStack>
                    )}
                  </Box>
                )}
                
                {/* General Violations (non-employment law) */}
                {analysis.compliance_analysis.violations?.length > 0 && !analysis.compliance_analysis.employment_law_check?.violations_found && (
                  <Box mb={3}>
                    <Text fontSize="sm" fontWeight="600" color="red.600" mb={2}>Violations Found:</Text>
                    <VStack align="stretch" spacing={2}>
                      {analysis.compliance_analysis.violations.map((violation, idx) => (
                        <Box key={idx} p={2} bg="red.50" _dark={{ bg: 'red.900' }} borderRadius="md">
                          <HStack mb={1}>
                            <Badge colorScheme={violation.severity === 'high' ? 'red' : 'orange'} fontSize="xs">
                              {violation.severity}
                            </Badge>
                            <Text fontSize="sm" fontWeight="600" color="red.700" _dark={{ color: 'red.200' }} textTransform="capitalize">
                              {violation.type?.replace(/_/g, ' ')}
                            </Text>
                          </HStack>
                          <Text fontSize="sm" color="red.600" _dark={{ color: 'red.300' }}>
                            {violation.description}
                          </Text>
                          {violation.recommendation && (
                            <Text fontSize="xs" color="green.600" _dark={{ color: 'green.300' }} mt={1}>
                              💡 {violation.recommendation}
                            </Text>
                          )}
                        </Box>
                      ))}
                    </VStack>
                  </Box>
                )}
                
                {/* Legacy violation type display */}
                {analysis.compliance_analysis.violation_type && analysis.compliance_analysis.violation_type !== 'none' && !analysis.compliance_analysis.violations?.length && (
                  <Text fontSize="sm" mb={1} color={textColor}>
                    <strong>Violation Type:</strong> {analysis.compliance_analysis.violation_type}
                  </Text>
                )}
              </Box>
            )}
          </AccordionPanel>
        </AccordionItem>

        {/* 2. Factual Accuracy Analysis */}
        {analysis.accuracy_analysis && (
          <AccordionItem 
            border="1px solid"
            borderColor={accuracyBorderColor}
            borderRadius="md"
            mb={3}
          >
            <AccordionButton 
              bg={accuracyBg}
              _hover={{ bg: accuracyHoverBg }}
              _expanded={{ bg: accuracyExpandedBg }}
              borderRadius="md"
              p={3}
            >
              <Box flex="1" textAlign="left">
                <HStack spacing={2}>
                  <Icon as={FaCheckCircle} color={analysis.accuracy_analysis.is_accurate ? "green.500" : "orange.500"} boxSize={4} />
                  <Text fontWeight="600" fontSize="sm" color={textColor}>
                    Factual Accuracy Analysis
                  </Text>
                  <Badge 
                    colorScheme={getScoreColor(analysis.accuracy_analysis.accuracy_score)}
                    fontSize="xs"
                  >
                    <Text color={analysis.accuracy_analysis.accuracy_score < 80 ? 'red.600' : undefined}>{analysis.accuracy_analysis.accuracy_score}/100</Text>
                  </Badge>
                </HStack>
                <Text fontSize="xs" color={textColorSecondary} mt={0.5} ml={6}>
                  {analysis.accuracy_analysis.is_accurate ? 'Content is factually accurate' : 'Content needs verification'}
                </Text>
              </Box>
              <AccordionIcon color={textColor} boxSize={5} />
            </AccordionButton>
            <AccordionPanel pb={3} pt={3}>
              {analysis.accuracy_analysis.inaccuracies && analysis.accuracy_analysis.inaccuracies.length > 0 && (
                <Box mb={2} p={2} bg="orange.100" borderRadius="md">
                  <Text fontSize="sm" fontWeight="600" color="orange.700" mb={1}>
                    ⚠️ Inaccuracies Found:
                  </Text>
                  <VStack align="stretch" pl={2}>
                    {analysis.accuracy_analysis.inaccuracies.map((item, idx) => (
                      <Text key={idx} fontSize="sm" color="orange.800">• {item}</Text>
                    ))}
                  </VStack>
                </Box>
              )}
              
              {analysis.accuracy_analysis.verified_facts && analysis.accuracy_analysis.verified_facts.length > 0 && (
                <Box mb={2} p={2} bg="green.100" borderRadius="md">
                  <Text fontSize="sm" fontWeight="600" color="green.700" mb={1}>
                    ✓ Verified Facts:
                  </Text>
                  <VStack align="stretch" pl={2}>
                    {analysis.accuracy_analysis.verified_facts.map((item, idx) => (
                      <Text key={idx} fontSize="sm" color="green.800">✓ {item}</Text>
                    ))}
                  </VStack>
                </Box>
              )}
              
              {analysis.accuracy_analysis.recommendations && (
                <Text fontSize="sm" color={textColor} fontStyle="italic" mt={2}>
                  💡 {analysis.accuracy_analysis.recommendations}
                </Text>
              )}
            </AccordionPanel>
          </AccordionItem>
        )}

        {/* 3. Global Cultural Sensitivity */}
        {analysis.cultural_analysis && (
          <AccordionItem 
            border="1px solid"
            borderColor={culturalBorderColor}
            borderRadius="md"
            mb={3}
          >
            <AccordionButton 
              bg={culturalBg}
              _hover={{ bg: culturalHoverBg }}
              _expanded={{ bg: culturalExpandedBg }}
              borderRadius="md"
              p={3}
            >
              <Box flex="1" textAlign="left">
                <HStack spacing={2}>
                  <Icon as={FaGlobe} color="blue.500" boxSize={4} />
                  <Text fontWeight="600" fontSize="sm" color={textColor}>
                    Global Cultural Sensitivity
                  </Text>
                  <Badge 
                    colorScheme={getScoreColor(culturalScore)}
                    fontSize="xs"
                  >
                    <Text color={culturalScore < 80 ? 'red.600' : undefined}>{culturalScore}/100</Text>
                  </Badge>
                </HStack>
                <Text fontSize="xs" color={textColorSecondary} mt={0.5} ml={6}>
                  Cultural appropriateness for global audiences
                </Text>
              </Box>
              <AccordionIcon color={textColor} boxSize={5} />
            </AccordionButton>
            <AccordionPanel pb={3} pt={3}>
              <Text fontSize="sm" fontWeight="500" color={textColorSecondary} mb={3}>
                {analysis.cultural_analysis.summary}
              </Text>

              {/* Target vs Appropriate Cultures Section */}
              {(analysis.profile_target_region || analysis.cultural_analysis.appropriate_cultures || analysis.cultural_analysis.risk_regions) && (
                <Box mb={4} p={3} bg={culturalDimBg} borderRadius="md" borderWidth="1px" borderColor={culturalDimBorder}>
                  <Text fontWeight="600" fontSize="sm" color={textColor} mb={2}>
                    🎯 Cultural Fit Analysis
                  </Text>
                  
                  {/* Profile Target Region/Audience */}
                  {analysis.profile_target_region && (
                    <Box mb={2}>
                      <Text fontSize="sm" color={textColor}>
                        <strong>Profile Target Region:</strong> {analysis.profile_target_region}
                      </Text>
                    </Box>
                  )}
                  {analysis.profile_target_audience && (
                    <Box mb={2}>
                      <Text fontSize="sm" color={textColor}>
                        <strong>Target Audience:</strong> {analysis.profile_target_audience}
                      </Text>
                    </Box>
                  )}
                  
                  {/* Cultures content is appropriate for */}
                  {analysis.cultural_analysis.appropriate_cultures && analysis.cultural_analysis.appropriate_cultures.length > 0 && (
                    <Box mb={2} p={2} bg="green.50" borderRadius="md">
                      <Text fontSize="sm" color="green.700">
                        <strong>✓ Content is well-suited for:</strong>
                      </Text>
                      <Text fontSize="sm" color="green.600" ml={2}>
                        {analysis.cultural_analysis.appropriate_cultures.join(', ')}
                      </Text>
                    </Box>
                  )}
                  
                  {/* Cultures that may need adjustment */}
                  {analysis.cultural_analysis.risk_regions && analysis.cultural_analysis.risk_regions.length > 0 && (
                    <Box mb={2} p={2} bg="orange.50" borderRadius="md">
                      <Text fontSize="sm" color="orange.700">
                        <strong>⚠️ May need adjustments for:</strong>
                      </Text>
                      <Text fontSize="sm" color="orange.600" ml={2}>
                        {analysis.cultural_analysis.risk_regions.join(', ')}
                      </Text>
                    </Box>
                  )}
                  
                  {/* Match status with target */}
                  {analysis.profile_target_region && (
                    <Box mt={2} p={2} borderRadius="md" bg={
                      analysis.cultural_analysis.target_match_status === 'good' ? 'green.50' :
                      analysis.cultural_analysis.target_match_status === 'caution' ? 'yellow.50' : 'gray.50'
                    }>
                      <Text fontSize="sm" fontWeight="600" color={
                        analysis.cultural_analysis.target_match_status === 'good' ? 'green.700' :
                        analysis.cultural_analysis.target_match_status === 'caution' ? 'yellow.700' : textColor
                      }>
                        {analysis.cultural_analysis.target_match_status === 'good' 
                          ? '✓ Content aligns well with your target region' 
                          : analysis.cultural_analysis.target_match_status === 'caution'
                          ? '⚠️ Review recommended for your target region'
                          : 'Cultural fit assessment based on profile target'}
                      </Text>
                      {analysis.cultural_analysis.target_match_explanation && (
                        <Text fontSize="xs" color={textColorSecondary} mt={1}>
                          {analysis.cultural_analysis.target_match_explanation}
                        </Text>
                      )}
                    </Box>
                  )}
                </Box>
              )}

              {/* Detailed Cultural Dimensions */}
              {analysis.cultural_analysis.dimensions && analysis.cultural_analysis.dimensions.length > 0 && (
                <>
                  <Divider my={3} />
                  <Text fontWeight="600" fontSize="sm" color={textColor} mb={2}>
                    Cultural Dimensions ({analysis.cultural_analysis.dimensions.length})
                  </Text>
                  <VStack spacing={3} align="stretch">
                    {analysis.cultural_analysis.dimensions.map((dim, idx) => {
                      // Handle both old and new API response formats
                      const dimensionName = dim.dimension || dim.name || `Dimension ${idx + 1}`;
                      const dimensionScore = dim.score ?? 75;
                      const assessment = dim.feedback || dim.assessment || dim.description || 
                        (dimensionScore >= 70 ? 'Content performs well in this dimension' :
                         dimensionScore >= 50 ? 'Content is moderate in this dimension' :
                         'Content may need adjustment in this dimension');
                      
                      // Handle cultures_affected as risk_regions (backward compatibility)
                      const riskRegions = dim.risk_regions || dim.cultures_affected || [];
                      const appropriateFor = dim.appropriate_for || [];
                      
                      return (
                        <Box 
                          key={idx} 
                          p={3} 
                          bg={culturalDimBg}
                          borderRadius="md" 
                          borderWidth="1px"
                          borderColor={culturalDimBorder}
                        >
                          <HStack justify="space-between" mb={1}>
                            <Text fontWeight="600" fontSize="sm" color={culturalDimTextColor}>
                              {dimensionName}
                            </Text>
                            <Badge 
                              colorScheme={getScoreColor(dimensionScore)}
                              fontSize="xs"
                            >
                              <Text color={dimensionScore < 80 ? 'red.600' : undefined}>{dimensionScore}/100</Text>
                            </Badge>
                          </HStack>
                          <Progress 
                            value={dimensionScore} 
                            size="xs" 
                            colorScheme={getScoreColor(dimensionScore)}
                            mb={2}
                            borderRadius="full"
                          />
                          <Text fontSize="sm" mb={1} color={textColor}>
                            <strong>Assessment:</strong> {assessment}
                          </Text>
                          
                          {/* Cultures appropriate for this dimension */}
                          {appropriateFor.length > 0 && (
                            <Text fontSize="sm" mb={1} color="green.600">
                              <strong>✓ Works well in:</strong> {appropriateFor.join(', ')}
                            </Text>
                          )}
                          
                          {riskRegions.length > 0 && (
                            <Text fontSize="sm" mb={1} color={culturalRiskColor}>
                              <strong>⚠️ May need adjustment for:</strong> {riskRegions.join(', ')}
                            </Text>
                          )}
                          {dim.recommendations && (
                            <Text fontSize="sm" color={culturalRecColor} fontWeight="500">
                              💡 {dim.recommendations}
                            </Text>
                          )}
                        </Box>
                      );
                    })}
                  </VStack>
                </>
              )}
            </AccordionPanel>
          </AccordionItem>
        )}
      </Accordion>
    </VStack>
  );
}
