'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect, useCallback, Suspense } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  SimpleGrid,
  Badge,
  Divider,
  Progress,
  Spinner,
  Center,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Flex,
  CircularProgress,
  CircularProgressLabel,
  Avatar,
  UnorderedList,
  ListItem,
} from '@chakra-ui/react';
import { FaDownload, FaShieldAlt, FaCheckCircle, FaExclamationTriangle, FaChartPie, FaLightbulb, FaArrowLeft, FaUser, FaClipboardList, FaSearch } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useSearchParams, useRouter } from 'next/navigation';

// Color scheme matching Contentry.ai brand
const colors = {
  bg: '#0f1419',
  cardBg: '#1a1f2e',
  cardBgLight: '#232a3b',
  accent: '#3b82f6',
  accentLight: '#A78BFA',
  accentGradient: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
  text: '#ffffff',
  textMuted: '#9CA3AF',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  border: '#374151',
};

// Helper function to render text with bold markdown (**text**)
const renderBoldText = (text) => {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <Text as="span" key={idx} fontWeight="700" color={colors.text}>{part.slice(2, -2)}</Text>;
    }
    return <Text as="span" key={idx}>{part}</Text>;
  });
};

// Markdown Text Component - renders markdown with bold and bullet points
const MarkdownText = ({ content, color = colors.textMuted }) => {
  if (!content) return null;
  
  // Split by newlines
  const lines = content.split('\n');
  const elements = [];
  let currentList = [];
  let listKey = 0;
  
  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <UnorderedList key={`list-${listKey++}`} spacing={2} ml={4} mb={3} styleType="none">
          {currentList.map((item, idx) => (
            <ListItem key={idx} display="flex" alignItems="flex-start">
              <Text as="span" color={colors.accent} mr={2} mt="2px">•</Text>
              <Text color={color} lineHeight="tall">{renderBoldText(item)}</Text>
            </ListItem>
          ))}
        </UnorderedList>
      );
      currentList = [];
    }
  };
  
  lines.forEach((line, idx) => {
    const trimmedLine = line.trim();
    
    // Check for headers (### or **)
    if (trimmedLine.startsWith('### ')) {
      flushList();
      elements.push(
        <Text key={`h-${idx}`} color={colors.accent} fontWeight="700" fontSize="md" mb={2} mt={idx > 0 ? 4 : 0}>
          {trimmedLine.replace(/^###\s+/, '')}
        </Text>
      );
    } else if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**') && !trimmedLine.includes(':** ')) {
      flushList();
      elements.push(
        <Text key={`h-${idx}`} color={colors.accent} fontWeight="700" fontSize="md" mb={2} mt={idx > 0 ? 4 : 0}>
          {trimmedLine.slice(2, -2)}
        </Text>
      );
    } else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
      // Bullet point
      const bulletContent = trimmedLine.replace(/^[-•]\s*/, '');
      currentList.push(bulletContent);
    } else if (trimmedLine === '') {
      flushList();
    } else {
      flushList();
      elements.push(
        <Text key={`p-${idx}`} color={color} lineHeight="tall" mb={2}>
          {renderBoldText(trimmedLine)}
        </Text>
      );
    }
  });
  
  flushList();
  
  return <Box>{elements}</Box>;
};

// Section Header Component
const SectionHeader = ({ icon, title }) => (
  <HStack spacing={3} mb={6}>
    <Box w="4px" h="28px" bgGradient={colors.accentGradient} borderRadius="full" />
    <Icon as={icon} boxSize={5} color={colors.accent} />
    <Heading size="md" color={colors.text} fontWeight="700">
      {title}
    </Heading>
  </HStack>
);

// Metric Card Component
const MetricCard = ({ label, value, gradient = false, size = 'md' }) => (
  <Box
    bg={gradient ? colors.accentGradient : colors.cardBgLight}
    p={4}
    borderRadius="xl"
    textAlign="center"
  >
    <Text fontSize="xs" color={colors.textMuted} mb={1} textTransform="uppercase" letterSpacing="wide">
      {label}
    </Text>
    <Text fontSize={size === 'lg' ? '3xl' : '2xl'} fontWeight="800" color={colors.text}>
      {value}
    </Text>
  </Box>
);

// Large Circular Metric
const CircularMetric = ({ value, label, color = colors.accent }) => (
  <VStack spacing={2}>
    <Box position="relative">
      <CircularProgress
        value={value}
        size="120px"
        thickness="8px"
        color={color}
        trackColor={colors.cardBgLight}
        capIsRound
      >
        <CircularProgressLabel fontSize="2xl" fontWeight="800" color={colors.text}>
          {value}
        </CircularProgressLabel>
      </CircularProgress>
    </Box>
    <Text fontSize="sm" color={colors.textMuted} textAlign="center">
      {label}
    </Text>
  </VStack>
);

// Loading fallback
const PageLoadingFallback = () => (
  <Center minH="100vh" bg={colors.bg}>
    <Spinner size="xl" color={colors.accent} thickness="4px" />
  </Center>
);

function ReportPageContent() {
  const [reportData, setReportData] = useState(null);
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const searchParams = useSearchParams();
  const router = useRouter();
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const urlUserId = searchParams.get('user_id');
    if (urlUserId) {
      setUserId(urlUserId);
    } else {
      const savedUser = localStorage.getItem('contentry_user');
      if (savedUser) {
        const data = JSON.parse(savedUser);
        setUserId(data.id);
        setUserData(data);
      }
    }
  }, [searchParams]);

  const loadReportData = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/admin/generate-comprehensive-report`, null, {
        params: { user_id: userId }
      });
      setReportData(response.data.report || response.data);
      
      // Also load user data if not already loaded
      if (!userData) {
        const savedUser = localStorage.getItem('contentry_user');
        if (savedUser) {
          setUserData(JSON.parse(savedUser));
        }
      }
    } catch (err) {
      console.error('Error loading report:', err);
      setError(err.response?.data?.detail || 'Failed to load report. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [userId, userData]);

  useEffect(() => {
    if (userId) {
      loadReportData();
    }
  }, [userId, loadReportData]);

  const downloadPDF = () => {
    const API = getApiUrl();
    window.open(`${API}/admin/download-pdf-report?user_id=${userId}`, '_blank');
  };

  if (loading) {
    return (
      <Box minH="100vh" bg={colors.bg} p={8}>
        <Center h="60vh">
          <VStack spacing={6}>
            <Spinner size="xl" color={colors.accent} thickness="4px" />
            <VStack spacing={2}>
              <Text fontSize="xl" color={colors.text} fontWeight="600">Generating Your Report</Text>
              <Text color={colors.textMuted}>Analyzing content and preparing insights...</Text>
            </VStack>
          </VStack>
        </Center>
      </Box>
    );
  }

  if (error) {
    return (
      <Box minH="100vh" bg={colors.bg} p={8}>
        <Center h="60vh">
          <VStack spacing={6}>
            <Icon as={FaExclamationTriangle} boxSize={12} color={colors.danger} />
            <Text fontSize="xl" color={colors.danger}>{error}</Text>
            <HStack spacing={4}>
              <Button colorScheme="blue" onClick={loadReportData}>Try Again</Button>
              <Button variant="outline" borderColor={colors.border} color={colors.text} onClick={() => router.back()}>
                Go Back
              </Button>
            </HStack>
          </VStack>
        </Center>
      </Box>
    );
  }

  if (!reportData) {
    return (
      <Box minH="100vh" bg={colors.bg} p={8}>
        <Center h="60vh">
          <VStack spacing={4}>
            <Text fontSize="xl" color={colors.textMuted}>No report data available</Text>
            <Button leftIcon={<FaArrowLeft />} onClick={() => router.back()} color={colors.text}>
              Go Back
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  const overview = reportData.overview || {};
  const quality = reportData.content_quality || {};
  const llmAnalysis = reportData.llm_analysis || {};
  const generatedAt = new Date(reportData.generated_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });

  // Calculate scores
  const overallScore = Math.round((quality.approval_rate || 100));
  const complianceScore = Math.round(100 - ((quality.policy_violations || 0) / Math.max(overview.total_posts || 1, 1)) * 100);
  const professionalFocus = Math.round(((overview.total_posts || 0) - (quality.flagged_posts || 0)) / Math.max(overview.total_posts || 1, 1) * 100);

  return (
    <Box minH="100vh" bg={colors.bg} py={8} px={4}>
      <VStack spacing={8} maxW="900px" mx="auto">
        
        {/* ============ HEADER ============ */}
        <Box w="100%" textAlign="center" py={8}>
          {/* Logo */}
          <HStack justify="center" spacing={3} mb={4}>
            <Box
              w="50px"
              h="50px"
              bgGradient={colors.accentGradient}
              borderRadius="xl"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Icon as={FaShieldAlt} boxSize={6} color="white" />
            </Box>
            <VStack align="start" spacing={0}>
              <Heading size="lg" color={colors.text} fontWeight="800">Contentry.ai</Heading>
              <Text fontSize="xs" color={colors.textMuted}>Your Reputation is Your Future. Protect it.</Text>
            </VStack>
          </HStack>
          
          {/* Report Title */}
          <Heading size="xl" color={colors.text} mt={6} mb={2}>
            Content Analysis Report
          </Heading>
          <Text color={colors.textMuted} fontSize="md">
            Social Media Content Audit & Reputation Analysis
          </Text>
          
          <HStack justify="center" spacing={4} mt={6}>
            <Button
              leftIcon={<FaDownload />}
              bgGradient={colors.accentGradient}
              color="white"
              size="lg"
              onClick={downloadPDF}
              _hover={{ opacity: 0.9 }}
            >
              Download PDF Report
            </Button>
            <Button
              leftIcon={<FaArrowLeft />}
              variant="outline"
              borderColor={colors.border}
              color={colors.text}
              onClick={() => router.back()}
              _hover={{ bg: colors.cardBgLight }}
            >
              Back
            </Button>
          </HStack>
        </Box>

        {/* ============ EXECUTIVE SUMMARY ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaClipboardList} title="Executive Summary" />
          <Box bg={colors.cardBgLight} p={5} borderRadius="lg">
            <Text color={colors.textMuted} lineHeight="tall">
              {llmAnalysis.executive_summary || 
                `This comprehensive analysis evaluates ${overview.total_posts || 0} posts to assess content quality, compliance adherence, and reputation risk factors. The report provides actionable insights for maintaining a strong digital presence and professional brand image across social media platforms.`
              }
            </Text>
          </Box>
        </Box>

        {/* ============ PROFILE OVERVIEW & METHODOLOGY ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaUser} title="Profile Overview & Methodology" />
          
          {/* Profile Info */}
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={6} mb={6}>
            <Box bg={colors.cardBgLight} p={5} borderRadius="lg">
              <HStack spacing={4} mb={4}>
                <Avatar 
                  size="lg" 
                  name={userData?.full_name} 
                  src={userData?.profile_picture}
                  bg={colors.accent}
                />
                <VStack align="start" spacing={1}>
                  <Text color={colors.text} fontWeight="700" fontSize="lg">
                    {userData?.full_name || 'User Profile'}
                  </Text>
                  <Text color={colors.textMuted} fontSize="sm">
                    {userData?.job_title || 'Content Creator'}
                  </Text>
                </VStack>
              </HStack>
              <SimpleGrid columns={2} gap={3}>
                <Box>
                  <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Company</Text>
                  <Text color={colors.text} fontSize="sm">{userData?.company_name || 'Not specified'}</Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Location</Text>
                  <Text color={colors.text} fontSize="sm">{userData?.country || 'Not specified'}</Text>
                </Box>
              </SimpleGrid>
            </Box>
            
            <Box bg={colors.cardBgLight} p={5} borderRadius="lg">
              <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase" mb={3}>Methodology</Text>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaCheckCircle} color={colors.success} boxSize={4} />
                  <Text color={colors.text} fontSize="sm">AI-Powered Content Analysis</Text>
                </HStack>
                <HStack>
                  <Icon as={FaCheckCircle} color={colors.success} boxSize={4} />
                  <Text color={colors.text} fontSize="sm">Policy Compliance Verification</Text>
                </HStack>
                <HStack>
                  <Icon as={FaCheckCircle} color={colors.success} boxSize={4} />
                  <Text color={colors.text} fontSize="sm">Cultural Sensitivity Assessment</Text>
                </HStack>
                <HStack>
                  <Icon as={FaCheckCircle} color={colors.success} boxSize={4} />
                  <Text color={colors.text} fontSize="sm">Reputation Risk Scoring</Text>
                </HStack>
              </VStack>
            </Box>
          </SimpleGrid>
          
          {/* Key Metrics */}
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
            <MetricCard label="Posts Analyzed" value={overview.total_posts || 0} gradient />
            <MetricCard label="Flagged Content" value={quality.flagged_posts || 0} />
            <MetricCard label="Policy Violations" value={quality.policy_violations || 0} />
            <MetricCard label="Professional Focus" value={`${professionalFocus}%`} gradient />
          </SimpleGrid>
        </Box>

        {/* ============ RISK ASSESSMENT & COMPLIANCE ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaShieldAlt} title="Risk Assessment & Compliance Analysis" />
          
          <Flex direction={{ base: 'column', md: 'row' }} gap={6}>
            {/* Main Score Circle */}
            <VStack 
              bg={colors.cardBgLight} 
              p={6} 
              borderRadius="xl" 
              flex="1"
              justify="center"
            >
              <CircularMetric 
                value={overallScore} 
                label="Overall Reputation Score" 
                color={overallScore >= 80 ? colors.success : overallScore >= 60 ? colors.warning : colors.danger}
              />
              <Badge 
                mt={2}
                px={4} 
                py={1} 
                borderRadius="full" 
                bg={overallScore >= 80 ? colors.success : overallScore >= 60 ? colors.warning : colors.danger}
                color="white"
                fontSize="sm"
                fontWeight="700"
              >
                {overallScore >= 80 ? 'EXCELLENT' : overallScore >= 60 ? 'GOOD' : 'NEEDS ATTENTION'}
              </Badge>
            </VStack>
            
            {/* Score Breakdown */}
            <VStack flex="1.5" spacing={4} align="stretch">
              {/* Compliance Score */}
              <Box bg={colors.cardBgLight} p={4} borderRadius="lg">
                <HStack justify="space-between" mb={2}>
                  <Text color={colors.text} fontWeight="600">Compliance Score</Text>
                  <Text color={complianceScore >= 80 ? colors.success : colors.warning} fontWeight="700">
                    {complianceScore}%
                  </Text>
                </HStack>
                <Progress 
                  value={complianceScore} 
                  colorScheme={complianceScore >= 80 ? 'green' : 'orange'}
                  size="sm" 
                  borderRadius="full" 
                  bg={colors.cardBg}
                />
              </Box>
              
              {/* Cultural Sensitivity */}
              <Box bg={colors.cardBgLight} p={4} borderRadius="lg">
                <HStack justify="space-between" mb={2}>
                  <Text color={colors.text} fontWeight="600">Cultural Sensitivity</Text>
                  <Text color={colors.success} fontWeight="700">
                    {100 - (quality.harassment_cases || 0)}%
                  </Text>
                </HStack>
                <Progress 
                  value={100 - (quality.harassment_cases || 0)} 
                  colorScheme="green"
                  size="sm" 
                  borderRadius="full" 
                  bg={colors.cardBg}
                />
              </Box>
              
              {/* Platform Health */}
              <Box bg={colors.cardBgLight} p={4} borderRadius="lg">
                <HStack justify="space-between">
                  <Text color={colors.text} fontWeight="600">Platform Health</Text>
                  <Badge 
                    colorScheme={overview.platform_health === 'Excellent' ? 'green' : 'blue'}
                    fontSize="sm"
                  >
                    {overview.platform_health || 'Good'}
                  </Badge>
                </HStack>
              </Box>
            </VStack>
          </Flex>
        </Box>

        {/* ============ DETAILED CONTENT ANALYSIS ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaSearch} title="Detailed Content Analysis" />
          
          <Box bg={colors.cardBgLight} p={5} borderRadius="lg" mb={6}>
            <Text color={colors.textMuted} lineHeight="tall">
              {llmAnalysis.detailed_analysis || 
                'This section provides a comprehensive breakdown of analyzed content, including engagement patterns, content types, and compliance status for each post.'
              }
            </Text>
          </Box>
          
          {/* Analysis Metadata */}
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4} mb={6}>
            <Box bg={colors.cardBgLight} p={3} borderRadius="lg">
              <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Analysis Date</Text>
              <Text color={colors.text} fontSize="sm" fontWeight="600">{generatedAt}</Text>
            </Box>
            <Box bg={colors.cardBgLight} p={3} borderRadius="lg">
              <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Data Source</Text>
              <Text color={colors.text} fontSize="sm" fontWeight="600">Platform Content</Text>
            </Box>
            <Box bg={colors.cardBgLight} p={3} borderRadius="lg">
              <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Analysis Type</Text>
              <Text color={colors.text} fontSize="sm" fontWeight="600">AI-Powered</Text>
            </Box>
            <Box bg={colors.cardBgLight} p={3} borderRadius="lg">
              <Text fontSize="xs" color={colors.textMuted} textTransform="uppercase">Report ID</Text>
              <Text color={colors.text} fontSize="sm" fontWeight="600">{reportData.report_id?.slice(0, 8) || 'N/A'}</Text>
            </Box>
          </SimpleGrid>
          
          {/* Content Status Summary */}
          <Box overflowX="auto">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th color={colors.textMuted} borderColor={colors.border}>Content Status</Th>
                  <Th color={colors.textMuted} borderColor={colors.border} isNumeric>Count</Th>
                  <Th color={colors.textMuted} borderColor={colors.border} isNumeric>Percentage</Th>
                </Tr>
              </Thead>
              <Tbody>
                <Tr>
                  <Td color={colors.text} borderColor={colors.border}>
                    <HStack>
                      <Box w={3} h={3} borderRadius="full" bg={colors.success} />
                      <Text>Approved Content</Text>
                    </HStack>
                  </Td>
                  <Td color={colors.text} borderColor={colors.border} isNumeric>
                    {(overview.total_posts || 0) - (quality.flagged_posts || 0)}
                  </Td>
                  <Td color={colors.success} borderColor={colors.border} isNumeric fontWeight="600">
                    {professionalFocus}%
                  </Td>
                </Tr>
                <Tr>
                  <Td color={colors.text} borderColor={colors.border}>
                    <HStack>
                      <Box w={3} h={3} borderRadius="full" bg={colors.warning} />
                      <Text>Flagged for Review</Text>
                    </HStack>
                  </Td>
                  <Td color={colors.text} borderColor={colors.border} isNumeric>
                    {quality.flagged_posts || 0}
                  </Td>
                  <Td color={colors.warning} borderColor={colors.border} isNumeric fontWeight="600">
                    {100 - professionalFocus}%
                  </Td>
                </Tr>
                <Tr>
                  <Td color={colors.text} borderColor={colors.border}>
                    <HStack>
                      <Box w={3} h={3} borderRadius="full" bg={colors.danger} />
                      <Text>Policy Violations</Text>
                    </HStack>
                  </Td>
                  <Td color={colors.text} borderColor={colors.border} isNumeric>
                    {quality.policy_violations || 0}
                  </Td>
                  <Td color={colors.danger} borderColor={colors.border} isNumeric fontWeight="600">
                    {Math.round((quality.policy_violations || 0) / Math.max(overview.total_posts || 1, 1) * 100)}%
                  </Td>
                </Tr>
              </Tbody>
            </Table>
          </Box>
        </Box>

        {/* ============ THEME DISTRIBUTION ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaChartPie} title="Theme Distribution & Key Findings" />
          
          {/* Key Findings with formatted sections */}
          {llmAnalysis.key_findings && (
            <Box bg={colors.cardBgLight} p={5} borderRadius="lg" mb={6}>
              <MarkdownText content={llmAnalysis.key_findings} />
            </Box>
          )}
          
          {/* Theme Distribution Table */}
          <Box overflowX="auto">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr bg={colors.accentGradient}>
                  <Th color="white" borderColor={colors.border}>Content Category</Th>
                  <Th color="white" borderColor={colors.border} isNumeric>Posts</Th>
                  <Th color="white" borderColor={colors.border} isNumeric>Percentage</Th>
                </Tr>
              </Thead>
              <Tbody>
                {llmAnalysis.theme_distribution ? (
                  Object.entries(llmAnalysis.theme_distribution).map(([theme, percentage], idx) => (
                    <Tr key={idx}>
                      <Td color={colors.text} borderColor={colors.border}>{theme}</Td>
                      <Td color={colors.text} borderColor={colors.border} isNumeric>
                        {Math.round((percentage / 100) * (overview.total_posts || 0))}
                      </Td>
                      <Td color={colors.accent} borderColor={colors.border} isNumeric fontWeight="600">
                        {percentage}%
                      </Td>
                    </Tr>
                  ))
                ) : (
                  <>
                    <Tr>
                      <Td color={colors.text} borderColor={colors.border}>Professional Content</Td>
                      <Td color={colors.text} borderColor={colors.border} isNumeric>
                        {(overview.total_posts || 0) - (quality.flagged_posts || 0)}
                      </Td>
                      <Td color={colors.accent} borderColor={colors.border} isNumeric fontWeight="600">
                        {professionalFocus}%
                      </Td>
                    </Tr>
                    <Tr>
                      <Td color={colors.text} borderColor={colors.border}>Flagged Content</Td>
                      <Td color={colors.text} borderColor={colors.border} isNumeric>
                        {quality.flagged_posts || 0}
                      </Td>
                      <Td color={colors.warning} borderColor={colors.border} isNumeric fontWeight="600">
                        {100 - professionalFocus}%
                      </Td>
                    </Tr>
                  </>
                )}
              </Tbody>
            </Table>
          </Box>
        </Box>

        {/* ============ REPUTATION INSIGHTS & RECOMMENDATIONS ============ */}
        <Box w="100%" bg={colors.cardBg} p={6} borderRadius="xl">
          <SectionHeader icon={FaLightbulb} title="Reputation Insights & Recommendations" />
          
          {/* Profile Overview from LLM */}
          {llmAnalysis.profile_overview && (
            <Box bg={colors.cardBgLight} p={5} borderRadius="lg" mb={6}>
              <Text color={colors.accent} fontWeight="700" mb={2}>Profile Analysis</Text>
              <Text color={colors.textMuted} lineHeight="tall">
                {llmAnalysis.profile_overview}
              </Text>
            </Box>
          )}
          
          {/* Detailed Analysis */}
          {llmAnalysis.detailed_analysis && (
            <Box bg={colors.cardBgLight} p={5} borderRadius="lg" mb={6}>
              <Text color={colors.accent} fontWeight="700" mb={2}>Content Strategy Assessment</Text>
              <MarkdownText content={llmAnalysis.detailed_analysis} />
            </Box>
          )}
          
          {/* Recommendations */}
          <Text color={colors.text} fontWeight="700" mb={4}>Recommendations for Comprehensive Analysis</Text>
          <Text color={colors.textMuted} fontSize="sm" mb={4}>
            The following recommendations are designed to help maintain and improve your digital reputation and content strategy.
          </Text>
          <VStack align="stretch" spacing={3}>
            {reportData.recommendations?.length > 0 ? (
              reportData.recommendations.map((rec, idx) => (
                <HStack key={idx} align="start" bg={colors.cardBgLight} p={4} borderRadius="lg">
                  <Icon as={FaCheckCircle} color={colors.accent} boxSize={5} mt={0.5} />
                  <Text color={colors.textMuted}>{rec}</Text>
                </HStack>
              ))
            ) : (
              <>
                <HStack align="start" bg={colors.cardBgLight} p={4} borderRadius="lg">
                  <Icon as={FaCheckCircle} color={colors.accent} boxSize={5} mt={0.5} />
                  <Box>
                    <Text color={colors.text} fontWeight="600">Multi-Platform Monitoring</Text>
                    <Text color={colors.textMuted} fontSize="sm">Extend analysis across all social media platforms for comprehensive coverage.</Text>
                  </Box>
                </HStack>
                <HStack align="start" bg={colors.cardBgLight} p={4} borderRadius="lg">
                  <Icon as={FaCheckCircle} color={colors.accent} boxSize={5} mt={0.5} />
                  <Box>
                    <Text color={colors.text} fontWeight="600">Historical Analysis</Text>
                    <Text color={colors.textMuted} fontSize="sm">Review past content to identify patterns and trends over time.</Text>
                  </Box>
                </HStack>
                <HStack align="start" bg={colors.cardBgLight} p={4} borderRadius="lg">
                  <Icon as={FaCheckCircle} color={colors.accent} boxSize={5} mt={0.5} />
                  <Box>
                    <Text color={colors.text} fontWeight="600">AI-Powered Reputation Scanning</Text>
                    <Text color={colors.textMuted} fontSize="sm">Use Contentry.ai&apos;s platform for continuous monitoring and real-time alerts.</Text>
                  </Box>
                </HStack>
              </>
            )}
          </VStack>
        </Box>

        {/* ============ FOOTER ============ */}
        <Box w="100%" textAlign="center" py={8}>
          {/* Logo */}
          <HStack justify="center" spacing={3} mb={4}>
            <Box
              w="40px"
              h="40px"
              bgGradient={colors.accentGradient}
              borderRadius="lg"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Icon as={FaShieldAlt} boxSize={5} color="white" />
            </Box>
            <Heading size="md" color={colors.text} fontWeight="800">Contentry.ai</Heading>
          </HStack>
          
          <Text color={colors.textMuted} fontSize="sm" mb={2}>
            Powered by Contentry.ai – World&apos;s First Agentic AI Reputation Management Platform
          </Text>
          <Text color={colors.accent} fontSize="sm" fontWeight="600" mb={6}>
            Protect Your Digital Reputation | Secure Your Global Future
          </Text>
          
          <Divider borderColor={colors.border} mb={6} />
          
          <Text color={colors.textMuted} fontSize="xs" mb={1}>
            Global Intech AS | Vestland, Høylandsbygd, Norway
          </Text>
          <Text color={colors.textMuted} fontSize="xs" mb={6}>
            Contact@contentry.ai | www.contentry.ai
          </Text>
          
          {/* CTA Button */}
          <Button
            bgGradient="linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)"
            color="white"
            size="lg"
            px={8}
            _hover={{ opacity: 0.9 }}
            onClick={() => window.open('https://contentry.ai', '_blank')}
          >
            Secure My Reputation Now
          </Button>
          
          <Text color={colors.textMuted} fontSize="xs" mt={6}>
            Report Generated: {generatedAt} | Confidential Analysis
          </Text>
        </Box>
      </VStack>
    </Box>
  );
}

// Export with Suspense wrapper for useSearchParams
export default function ReportPage() {
  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <ReportPageContent />
    </Suspense>
  );
}
