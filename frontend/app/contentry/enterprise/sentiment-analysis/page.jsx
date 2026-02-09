'use client';

import { useState, useRef } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Input,
  Button,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  IconButton,
  useColorModeValue,
  useToast,
  Divider,
  Progress,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { Plus, Trash2, FileText, MessageCircle, TrendingUp, TrendingDown, Minus, Printer, Globe, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useWorkspace } from '@/context/WorkspaceContext';
import api, { getApiUrl } from '@/lib/api';

export default function SentimentAnalysisPage() {
  const { user } = useAuth();
  const { isEnterpriseWorkspace, enterpriseInfo } = useWorkspace();
  const toast = useToast();
  
  const [socialLinks, setSocialLinks] = useState([]);
  const [newLink, setNewLink] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  
  // Check if user is admin
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  
  if (!isEnterpriseWorkspace || !isAdmin) {
    return (
      <Box p={8}>
        <Alert status="warning">
          <AlertIcon />
          <Text>Sentiment Analysis is only available for Company Admins. Please switch to Company Workspace and ensure you have Admin access.</Text>
        </Alert>
      </Box>
    );
  }
  
  // Normalize URL - auto-add https:// if missing
  const normalizeUrl = (url) => {
    let normalized = url.trim();
    if (!normalized) return '';
    
    // If no protocol, add https://
    if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
      normalized = `https://${normalized}`;
    }
    
    return normalized;
  };
  
  // Detect platform from URL
  const detectPlatform = (url) => {
    const urlLower = url.toLowerCase();
    if (urlLower.includes('linkedin.com')) return 'linkedin';
    if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) return 'twitter';
    if (urlLower.includes('facebook.com')) return 'facebook';
    if (urlLower.includes('instagram.com')) return 'instagram';
    if (urlLower.includes('tiktok.com')) return 'tiktok';
    if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) return 'youtube';
    if (urlLower.includes('threads.net')) return 'threads';
    if (urlLower.includes('pinterest.com')) return 'pinterest';
    return 'website';
  };
  
  const addLink = () => {
    if (!newLink.trim()) {
      toast({
        title: 'Please enter a URL',
        status: 'warning',
        duration: 2000,
      });
      return;
    }
    
    // Normalize URL (auto-add https:// if missing)
    const normalizedUrl = normalizeUrl(newLink);
    
    // Basic URL validation
    try {
      new URL(normalizedUrl);
    } catch {
      toast({
        title: 'Invalid URL',
        description: 'Please enter a valid URL (e.g., linkedin.com/company/example)',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    // Check for duplicates
    if (socialLinks.some(link => link.url === normalizedUrl)) {
      toast({
        title: 'Duplicate URL',
        description: 'This URL has already been added.',
        status: 'warning',
        duration: 2000,
      });
      return;
    }
    
    const platform = detectPlatform(normalizedUrl);
    
    setSocialLinks([...socialLinks, { 
      id: Date.now().toString(), 
      url: normalizedUrl, 
      platform,
      status: 'pending'
    }]);
    setNewLink('');
    
    // Show toast if URL was normalized
    if (normalizedUrl !== newLink.trim()) {
      toast({
        title: 'URL normalized',
        description: `Added https:// to your URL`,
        status: 'info',
        duration: 2000,
      });
    }
  };
  
  const removeLink = (id) => {
    setSocialLinks(socialLinks.filter(link => link.id !== id));
  };
  
  const analyzeSentiment = async () => {
    if (socialLinks.length === 0) {
      toast({
        title: 'No links added',
        description: 'Please add at least one social profile link to analyze.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }
    
    setAnalyzing(true);
    
    try {
      // Call the real sentiment analysis API using authenticated axios
      const response = await api.post('/sentiment/analyze', {
        urls: socialLinks.map(link => link.url),
        enterprise_id: enterpriseInfo?.id || 'techcorp-international',
        enterprise_name: enterpriseInfo?.name || 'TechCorp International'
      });
      
      const results = response.data;
      
      // Update social links with analysis results
      const updatedLinks = socialLinks.map(link => {
        const profileResult = results.profiles?.find(p => p.url === link.url);
        if (profileResult) {
          return {
            ...link,
            status: profileResult.status,
            sentiment: profileResult.sentiment,
            title: profileResult.title,
            error: profileResult.error
          };
        }
        return { ...link, status: 'error', error: 'No result returned' };
      });
      
      setAnalysisResults(results);
      setSocialLinks(updatedLinks);
      
      const successCount = updatedLinks.filter(l => l.status === 'analyzed').length;
      const errorCount = updatedLinks.filter(l => l.status === 'error').length;
      
      toast({
        title: 'Analysis Complete',
        description: `Successfully analyzed ${successCount} profile(s)${errorCount > 0 ? `, ${errorCount} failed` : ''}`,
        status: successCount > 0 ? 'success' : 'error',
        duration: 3000,
      });
      
    } catch (error) {
      console.error('Sentiment analysis error:', error);
      toast({
        title: 'Analysis Failed',
        description: error.response?.data?.detail || error.message || 'Failed to analyze sentiment',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setAnalyzing(false);
    }
  };
  
  const viewProfileDetails = (profile) => {
    setSelectedProfile(profile);
    onOpen();
  };
  
  const printReport = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Sentiment Analysis Report - ${enterpriseInfo?.name || 'Company'}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; }
            h1 { color: #2D3748; border-bottom: 2px solid #4A5568; padding-bottom: 10px; }
            h2 { color: #4A5568; margin-top: 30px; }
            .profile { margin: 20px 0; padding: 20px; border: 1px solid #E2E8F0; border-radius: 8px; }
            .score { font-size: 24px; font-weight: bold; color: #48BB78; }
            .negative { color: #F56565; }
            .neutral { color: #ECC94B; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #E2E8F0; }
            th { background: #F7FAFC; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
            .badge-positive { background: #C6F6D5; color: #22543D; }
            .badge-negative { background: #FED7D7; color: #822727; }
            .badge-neutral { background: #FEFCBF; color: #744210; }
            .footer { margin-top: 40px; color: #718096; font-size: 12px; border-top: 1px solid #E2E8F0; padding-top: 20px; }
            .insight { background: #EBF8FF; padding: 10px; border-radius: 4px; margin: 5px 0; }
          </style>
        </head>
        <body>
          <h1>Sentiment Analysis Report</h1>
          <p><strong>Company:</strong> ${enterpriseInfo?.name || 'TechCorp International'}</p>
          <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
          <p><strong>Profiles Analyzed:</strong> ${socialLinks.filter(l => l.sentiment).length}</p>
          
          ${socialLinks.filter(p => p.sentiment).map(profile => `
            <div class="profile">
              <h2>${profile.platform.charAt(0).toUpperCase() + profile.platform.slice(1)} Profile</h2>
              <p><strong>URL:</strong> ${profile.url}</p>
              ${profile.title ? `<p><strong>Title:</strong> ${profile.title}</p>` : ''}
              <p><strong>Overall Sentiment:</strong> <span class="score ${profile.sentiment.overall === 'negative' ? 'negative' : profile.sentiment.overall === 'neutral' ? 'neutral' : ''}">${profile.sentiment.score}/100 (${profile.sentiment.overall?.toUpperCase() || 'N/A'})</span></p>
              
              ${profile.sentiment.summary ? `<p><strong>Summary:</strong> ${profile.sentiment.summary}</p>` : ''}
              
              <h3>Key Insights</h3>
              ${profile.sentiment.key_insights?.map(insight => `
                <div class="insight">${insight}</div>
              `).join('') || '<p>No insights available</p>'}
              
              ${profile.sentiment.trending_topics?.length > 0 ? `
                <h3>Trending Topics</h3>
                <table>
                  <tr>
                    <th>Topic</th>
                    <th>Sentiment</th>
                    <th>Mentions</th>
                  </tr>
                  ${profile.sentiment.trending_topics.map(topic => `
                    <tr>
                      <td>${topic.topic}</td>
                      <td><span class="badge badge-${topic.sentiment}">${topic.sentiment}</span></td>
                      <td>${topic.count}</td>
                    </tr>
                  `).join('')}
                </table>
              ` : ''}
              
              ${profile.sentiment.recommendations?.length > 0 ? `
                <h3>Recommendations</h3>
                <ul>
                  ${profile.sentiment.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
              ` : ''}
            </div>
          `).join('')}
          
          <div class="footer">
            <p>This report was generated by Contentry.ai Sentiment Analysis Tool</p>
            <p>© ${new Date().getFullYear()} ${enterpriseInfo?.name || 'TechCorp International'}. All rights reserved.</p>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };
  
  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'green';
      case 'negative': return 'red';
      default: return 'yellow';
    }
  };
  
  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'positive': return <TrendingUp size={16} />;
      case 'negative': return <TrendingDown size={16} />;
      default: return <Minus size={16} />;
    }
  };
  
  const getPlatformColor = (platform) => {
    switch (platform) {
      case 'linkedin': return 'blue';
      case 'twitter': return 'cyan';
      case 'facebook': return 'facebook';
      case 'instagram': return 'pink';
      case 'youtube': return 'red';
      case 'tiktok': return 'purple';
      default: return 'gray';
    }
  };
  
  return (
    <Box p={{ base: 4, md: 8 }} maxW="1400px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between" wrap="wrap" gap={4}>
          <VStack align="start" spacing={1}>
            <Heading size="lg" color={textColor}>Sentiment Analysis</Heading>
            <Text color={mutedColor}>
              Analyze public sentiment from web pages and social media profiles for {enterpriseInfo?.name || 'your company'}
            </Text>
          </VStack>
          
          {analysisResults && socialLinks.some(l => l.sentiment) && (
            <Button
              leftIcon={<Printer size={18} />}
              colorScheme="blue"
              onClick={printReport}
            >
              Print Report
            </Button>
          )}
        </HStack>
        
        {/* Add Links Section */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader pb={2}>
            <Heading size="md">Add URLs to Analyze</Heading>
            <Text fontSize="sm" color={mutedColor} mt={1}>
              Enter URLs to web pages or social profiles. No need to add https:// - we'll do that automatically.
            </Text>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack>
                <Input
                  placeholder="linkedin.com/company/example or any website URL"
                  value={newLink}
                  onChange={(e) => setNewLink(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addLink()}
                  data-testid="sentiment-url-input"
                />
                <Button 
                  leftIcon={<Plus size={18} />} 
                  colorScheme="blue" 
                  onClick={addLink}
                  data-testid="sentiment-add-btn"
                >
                  Add
                </Button>
              </HStack>
              
              {socialLinks.length > 0 && (
                <TableContainer>
                  <Table size="sm">
                    <Thead>
                      <Tr>
                        <Th>Platform</Th>
                        <Th>URL</Th>
                        <Th>Status</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {socialLinks.map((link) => (
                        <Tr key={link.id}>
                          <Td>
                            <Badge colorScheme={getPlatformColor(link.platform)}>
                              {link.platform}
                            </Badge>
                          </Td>
                          <Td>
                            <Text fontSize="sm" noOfLines={1} maxW="400px">
                              {link.url}
                            </Text>
                          </Td>
                          <Td>
                            <HStack spacing={1}>
                              <Badge colorScheme={
                                link.status === 'analyzed' ? 'green' : 
                                link.status === 'error' ? 'red' : 'gray'
                              }>
                                {link.status}
                              </Badge>
                              {link.error && (
                                <IconButton
                                  icon={<AlertTriangle size={14} />}
                                  size="xs"
                                  variant="ghost"
                                  colorScheme="red"
                                  aria-label="View error"
                                  title={link.error}
                                />
                              )}
                            </HStack>
                          </Td>
                          <Td>
                            <HStack spacing={2}>
                              {link.sentiment && (
                                <Button
                                  size="xs"
                                  leftIcon={<FileText size={14} />}
                                  onClick={() => viewProfileDetails(link)}
                                  data-testid={`view-details-${link.id}`}
                                >
                                  Details
                                </Button>
                              )}
                              <IconButton
                                size="xs"
                                icon={<Trash2 size={14} />}
                                colorScheme="red"
                                variant="ghost"
                                onClick={() => removeLink(link.id)}
                                aria-label="Remove link"
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </TableContainer>
              )}
              
              <Button
                colorScheme="green"
                isLoading={analyzing}
                loadingText="Analyzing..."
                onClick={analyzeSentiment}
                isDisabled={socialLinks.length === 0}
                leftIcon={<MessageCircle size={18} />}
                data-testid="analyze-sentiment-btn"
              >
                Analyze Sentiment
              </Button>
            </VStack>
          </CardBody>
        </Card>
        
        {/* Analysis Loading State */}
        {analyzing && (
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <VStack spacing={4}>
                <HStack spacing={3}>
                  <HStack spacing={1}>
                    <Box 
                      w="8px" h="8px" 
                      borderRadius="full" 
                      bg="blue.500"
                      sx={{
                        animation: 'pulse 1.4s ease-in-out infinite',
                        '@keyframes pulse': {
                          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                          '40%': { transform: 'scale(1)', opacity: 1 }
                        }
                      }}
                    />
                    <Box 
                      w="8px" h="8px" 
                      borderRadius="full" 
                      bg="blue.500"
                      sx={{
                        animation: 'pulse 1.4s ease-in-out 0.2s infinite',
                        '@keyframes pulse': {
                          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                          '40%': { transform: 'scale(1)', opacity: 1 }
                        }
                      }}
                    />
                    <Box 
                      w="8px" h="8px" 
                      borderRadius="full" 
                      bg="blue.500"
                      sx={{
                        animation: 'pulse 1.4s ease-in-out 0.4s infinite',
                        '@keyframes pulse': {
                          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: 0.4 },
                          '40%': { transform: 'scale(1)', opacity: 1 }
                        }
                      }}
                    />
                  </HStack>
                  <Text fontWeight="600" color="blue.600">Analyzing content...</Text>
                </HStack>
                <Text fontSize="sm" color={mutedColor}>
                  Scraping {socialLinks.length} URL(s) and performing AI sentiment analysis
                </Text>
                <Progress size="xs" isIndeterminate w="100%" colorScheme="blue" />
              </VStack>
            </CardBody>
          </Card>
        )}
        
        {/* Analysis Results */}
        {analysisResults && !analyzing && socialLinks.some(l => l.sentiment) && (
          <Box data-testid="sentiment-results">
            {/* Summary Stats */}
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardBody>
                  <Stat>
                    <StatLabel>URLs Analyzed</StatLabel>
                    <StatNumber>{socialLinks.filter(l => l.sentiment).length}</StatNumber>
                    <StatHelpText>of {socialLinks.length} total</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardBody>
                  <Stat>
                    <StatLabel>Average Sentiment Score</StatLabel>
                    <StatNumber>
                      {Math.round(
                        socialLinks
                          .filter(l => l.sentiment?.score)
                          .reduce((acc, p) => acc + p.sentiment.score, 0) / 
                        (socialLinks.filter(l => l.sentiment?.score).length || 1)
                      )}
                    </StatNumber>
                    <StatHelpText>Out of 100</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardBody>
                  <Stat>
                    <StatLabel>Most Common Sentiment</StatLabel>
                    <StatNumber textTransform="capitalize">
                      {(() => {
                        const sentiments = socialLinks.filter(l => l.sentiment?.overall).map(l => l.sentiment.overall);
                        const counts = sentiments.reduce((acc, s) => ({ ...acc, [s]: (acc[s] || 0) + 1 }), {});
                        return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';
                      })()}
                    </StatNumber>
                    <StatHelpText>Across all profiles</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardBody>
                  <Stat>
                    <StatLabel>Analysis Time</StatLabel>
                    <StatNumber>
                      {analysisResults.analyzed_at ? new Date(analysisResults.analyzed_at).toLocaleTimeString() : 'N/A'}
                    </StatNumber>
                    <StatHelpText>{new Date(analysisResults.analyzed_at).toLocaleDateString()}</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
            
            {/* Profile Results */}
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardHeader>
                <Heading size="md">Analysis Results</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  {socialLinks.filter(p => p.sentiment).map((profile) => (
                    <Box
                      key={profile.id}
                      p={4}
                      borderWidth="1px"
                      borderColor={borderColor}
                      borderRadius="md"
                    >
                      <HStack justify="space-between" mb={3} wrap="wrap" gap={2}>
                        <VStack align="start" spacing={1}>
                          <HStack>
                            <Badge colorScheme={getPlatformColor(profile.platform)} fontSize="sm">
                              {profile.platform}
                            </Badge>
                            {profile.title && (
                              <Text fontWeight="600" fontSize="sm">{profile.title}</Text>
                            )}
                          </HStack>
                          <Text fontSize="xs" color={mutedColor} noOfLines={1} maxW="400px">
                            {profile.url}
                          </Text>
                        </VStack>
                        <HStack>
                          <Badge 
                            colorScheme={getSentimentColor(profile.sentiment.overall)} 
                            fontSize="md" 
                            px={3} 
                            py={1}
                          >
                            <HStack spacing={1}>
                              {getSentimentIcon(profile.sentiment.overall)}
                              <Text>{profile.sentiment.overall?.toUpperCase() || 'N/A'}</Text>
                            </HStack>
                          </Badge>
                          <Text fontWeight="bold" fontSize="xl">
                            {profile.sentiment.score}/100
                          </Text>
                        </HStack>
                      </HStack>
                      
                      {profile.sentiment.summary && (
                        <Text fontSize="sm" color={mutedColor} mb={3}>
                          {profile.sentiment.summary}
                        </Text>
                      )}
                      
                      {profile.sentiment.key_insights?.length > 0 && (
                        <Box mb={3}>
                          <Text fontSize="sm" fontWeight="600" mb={1}>Key Insights:</Text>
                          <VStack align="start" spacing={1}>
                            {profile.sentiment.key_insights.slice(0, 2).map((insight, idx) => (
                              <Text key={idx} fontSize="sm" color={mutedColor}>• {insight}</Text>
                            ))}
                          </VStack>
                        </Box>
                      )}
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => viewProfileDetails(profile)}
                      >
                        View Full Report
                      </Button>
                    </Box>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          </Box>
        )}
      </VStack>
      
      {/* Profile Detail Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <HStack>
              <Badge colorScheme={getPlatformColor(selectedProfile?.platform)}>
                {selectedProfile?.platform}
              </Badge>
              <Text>Sentiment Report</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedProfile?.sentiment && (
              <VStack spacing={4} align="stretch">
                {/* Score */}
                <Box textAlign="center" p={4} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                  <Text fontSize="4xl" fontWeight="bold" color={`${getSentimentColor(selectedProfile.sentiment.overall)}.500`}>
                    {selectedProfile.sentiment.score}
                  </Text>
                  <Badge colorScheme={getSentimentColor(selectedProfile.sentiment.overall)} fontSize="md">
                    {selectedProfile.sentiment.overall?.toUpperCase()} SENTIMENT
                  </Badge>
                  {selectedProfile.sentiment.confidence && (
                    <Text fontSize="sm" color={mutedColor} mt={1}>
                      Confidence: {selectedProfile.sentiment.confidence}%
                    </Text>
                  )}
                </Box>
                
                {/* Summary */}
                {selectedProfile.sentiment.summary && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>Summary</Heading>
                      <Text>{selectedProfile.sentiment.summary}</Text>
                    </Box>
                  </>
                )}
                
                {/* Key Insights */}
                {selectedProfile.sentiment.key_insights?.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={3}>Key Insights</Heading>
                      <VStack align="start" spacing={2}>
                        {selectedProfile.sentiment.key_insights.map((insight, idx) => (
                          <Box key={idx} p={3} bg={useColorModeValue('blue.50', 'blue.900')} borderRadius="md" w="100%">
                            <Text fontSize="sm">{insight}</Text>
                          </Box>
                        ))}
                      </VStack>
                    </Box>
                  </>
                )}
                
                {/* Trending Topics */}
                {selectedProfile.sentiment.trending_topics?.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={3}>Trending Topics</Heading>
                      <TableContainer>
                        <Table size="sm">
                          <Thead>
                            <Tr>
                              <Th>Topic</Th>
                              <Th>Sentiment</Th>
                              <Th isNumeric>Mentions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {selectedProfile.sentiment.trending_topics.map((topic, idx) => (
                              <Tr key={idx}>
                                <Td>{topic.topic}</Td>
                                <Td>
                                  <Badge colorScheme={getSentimentColor(topic.sentiment)}>
                                    {topic.sentiment}
                                  </Badge>
                                </Td>
                                <Td isNumeric>{topic.count}</Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      </TableContainer>
                    </Box>
                  </>
                )}
                
                {/* Recommendations */}
                {selectedProfile.sentiment.recommendations?.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={3}>Recommendations</Heading>
                      <VStack align="start" spacing={2}>
                        {selectedProfile.sentiment.recommendations.map((rec, idx) => (
                          <HStack key={idx} align="start">
                            <Text color="green.500">•</Text>
                            <Text fontSize="sm">{rec}</Text>
                          </HStack>
                        ))}
                      </VStack>
                    </Box>
                  </>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
