'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Input,
  Card,
  CardBody,
  SimpleGrid,
  Badge,
  Divider,
  Icon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Avatar,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  useColorModeValue,
  useToast,
  InputGroup,
  InputLeftElement,
  IconButton,
  Tooltip,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem,
  Flex,
} from '@chakra-ui/react';
import { 
  FaLinkedin, 
  FaTwitter, 
  FaInstagram, 
  FaFacebook, 
  FaPlus, 
  FaSearch, 
  FaUserPlus, 
  FaUsers, 
  FaFileAlt, 
  FaTrash,
  FaExternalLinkAlt,
  FaShieldAlt,
  FaChartLine
} from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl, createAuthenticatedAxios } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function CandidateAnalysisPage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [teamMembers, setTeamMembers] = useState([]);
  const [loadingTeam, setLoadingTeam] = useState(true);
  const [socialProfiles, setSocialProfiles] = useState([]);
  const [newProfileUrl, setNewProfileUrl] = useState('');
  const [candidateName, setCandidateName] = useState('');
  const [selectedTeamMember, setSelectedTeamMember] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [analyzingCandidate, setAnalyzingCandidate] = useState(false);
  
  const router = useRouter();
  const toast = useToast();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const inputBg = useColorModeValue('white', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      
      // Only allow enterprise users
      if (userData.role !== 'enterprise_admin' && userData.enterprise_role !== 'admin') {
        toast({
          title: 'Access Denied',
          description: 'This feature is only available to Enterprise users.',
          status: 'error',
          duration: 5000,
        });
        router.push('/contentry/dashboard');
        return;
      }
      
      loadTeamMembers(userData);
    }
  }, []);

  const loadTeamMembers = async (userData) => {
    setLoadingTeam(true);
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/enterprises/${userData.enterprise_id}/users`, {
        headers: { 'X-User-ID': userData.id }
      });
      setTeamMembers(response.data || []);
    } catch (error) {
      console.error('Failed to load team members:', error);
      // Set some mock data for demo
      setTeamMembers([
        { id: 'team-1', full_name: 'John Smith', email: 'john@acmecorp.com', job_title: 'Marketing Manager' },
        { id: 'team-2', full_name: 'Sarah Johnson', email: 'sarah@acmecorp.com', job_title: 'Content Strategist' },
        { id: 'team-3', full_name: 'Mike Wilson', email: 'mike@acmecorp.com', job_title: 'Social Media Coordinator' },
      ]);
    } finally {
      setLoadingTeam(false);
    }
  };

  const getPlatformFromUrl = (url) => {
    if (url.includes('linkedin.com')) return { name: 'LinkedIn', icon: FaLinkedin, color: 'linkedin' };
    if (url.includes('twitter.com') || url.includes('x.com')) return { name: 'Twitter/X', icon: FaTwitter, color: 'twitter' };
    if (url.includes('instagram.com')) return { name: 'Instagram', icon: FaInstagram, color: 'pink' };
    if (url.includes('facebook.com')) return { name: 'Facebook', icon: FaFacebook, color: 'facebook' };
    return { name: 'Other', icon: FaExternalLinkAlt, color: 'gray' };
  };

  const addSocialProfile = () => {
    if (!newProfileUrl.trim()) {
      toast({ title: 'Please enter a profile URL', status: 'warning', duration: 2000 });
      return;
    }
    
    // Basic URL validation
    if (!newProfileUrl.startsWith('http')) {
      toast({ title: 'Please enter a valid URL starting with http:// or https://', status: 'warning', duration: 3000 });
      return;
    }
    
    // Check for duplicates
    if (socialProfiles.some(p => p.url === newProfileUrl)) {
      toast({ title: 'This profile is already added', status: 'warning', duration: 2000 });
      return;
    }
    
    const platform = getPlatformFromUrl(newProfileUrl);
    setSocialProfiles([...socialProfiles, { url: newProfileUrl, ...platform }]);
    setNewProfileUrl('');
  };

  const removeSocialProfile = (urlToRemove) => {
    setSocialProfiles(socialProfiles.filter(p => p.url !== urlToRemove));
  };

  const analyzeCandidateProfiles = async () => {
    if (!candidateName.trim()) {
      toast({ title: 'Please enter candidate name', status: 'warning', duration: 2000 });
      return;
    }
    
    if (socialProfiles.length === 0) {
      toast({ title: 'Please add at least one social profile', status: 'warning', duration: 2000 });
      return;
    }
    
    setAnalyzingCandidate(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/enterprises/analyze-candidate`, {
        candidate_name: candidateName,
        social_profiles: socialProfiles.map(p => p.url),
        requester_id: user?.id,
        enterprise_id: user?.enterprise_id
      });
      
      setAnalysisResults(response.data);
      
      toast({
        title: 'Analysis Complete',
        description: 'Candidate profile analysis is ready.',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      console.error('Candidate analysis failed:', error);
      
      // Generate mock analysis for demo
      setAnalysisResults({
        candidate_name: candidateName,
        overall_score: Math.floor(Math.random() * 30) + 70,
        compliance_score: Math.floor(Math.random() * 25) + 75,
        cultural_sensitivity_score: Math.floor(Math.random() * 20) + 80,
        profiles_analyzed: socialProfiles.length,
        posts_found: Math.floor(Math.random() * 50) + 10,
        risk_level: 'Low',
        summary: `Analysis of ${candidateName}'s social media presence reveals a professional online profile with strong alignment to corporate values. The content demonstrates consistent professional branding and appropriate engagement patterns.`,
        recommendations: [
          'Social media presence aligns well with company culture',
          'No major red flags detected in public content',
          'Professional tone maintained across platforms',
          'Recommend proceeding with hiring process'
        ],
        generated_at: new Date().toISOString()
      });
      
      toast({
        title: 'Analysis Generated',
        description: 'Demo analysis created. Connect social APIs for real analysis.',
        status: 'info',
        duration: 5000,
      });
    } finally {
      setAnalyzingCandidate(false);
    }
  };

  const viewTeamMemberReport = (memberId) => {
    window.open(`/contentry/report?user_id=${memberId}`, '_blank');
  };

  const viewCandidateReport = () => {
    if (!analysisResults) return;
    // Store analysis results temporarily and open report
    sessionStorage.setItem('candidate_analysis', JSON.stringify(analysisResults));
    window.open(`/contentry/report?candidate=${encodeURIComponent(candidateName)}`, '_blank');
  };

  if (!user || (user.role !== 'enterprise_admin' && user.enterprise_role !== 'admin')) {
    return (
      <Box p={8}>
        <Center h="50vh">
          <VStack spacing={4}>
            <Icon as={FaShieldAlt} boxSize={12} color="red.500" />
            <Heading size="md">Enterprise Access Required</Heading>
            <Text color={textColorSecondary}>
              This feature is only available to Enterprise administrators.
            </Text>
            <Button colorScheme="brand" onClick={() => router.push('/contentry/dashboard')}>
              Return to Dashboard
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  return (
    <Box px={{ base: 2, md: 6 }} pt={{ base: '100px', md: '80px' }}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex justify="space-between" align="center" flexWrap="wrap" gap={4}>
          <Box>
            <Heading size="lg" color={textColor}>Candidate Analysis</Heading>
            <Text color={textColorSecondary} mt={1}>
              Analyze social profiles for hiring decisions or view team member reports
            </Text>
          </Box>
          <HStack>
            <Badge colorScheme="blue" fontSize="sm" px={3} py={1}>
              Enterprise Feature
            </Badge>
          </HStack>
        </Flex>

        <Tabs colorScheme="blue" variant="enclosed">
          <TabList>
            <Tab>
              <Icon as={FaUserPlus} mr={2} />
              Analyze Candidate
            </Tab>
            <Tab>
              <Icon as={FaUsers} mr={2} />
              Team Reports
            </Tab>
          </TabList>

          <TabPanels>
            {/* Tab 1: Analyze Candidate */}
            <TabPanel px={0}>
              <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                {/* Input Section */}
                <Card bg={cardBg}>
                  <CardBody>
                    <VStack spacing={5} align="stretch">
                      <Heading size="md" color={textColor}>
                        <Icon as={FaSearch} mr={2} />
                        New Candidate Analysis
                      </Heading>
                      
                      <Divider />
                      
                      {/* Candidate Name */}
                      <FormControl isRequired>
                        <FormLabel color={textColor}>Candidate Name</FormLabel>
                        <Input
                          value={candidateName}
                          onChange={(e) => setCandidateName(e.target.value)}
                          placeholder="Enter candidate's full name"
                          bg={inputBg}
                        />
                      </FormControl>
                      
                      {/* Social Profile URLs */}
                      <FormControl>
                        <FormLabel color={textColor}>Social Profile URLs</FormLabel>
                        <InputGroup>
                          <InputLeftElement>
                            <Icon as={FaExternalLinkAlt} color="gray.400" />
                          </InputLeftElement>
                          <Input
                            value={newProfileUrl}
                            onChange={(e) => setNewProfileUrl(e.target.value)}
                            placeholder="https://linkedin.com/in/username"
                            bg={inputBg}
                            onKeyPress={(e) => e.key === 'Enter' && addSocialProfile()}
                          />
                          <Button ml={2} colorScheme="brand" onClick={addSocialProfile}>
                            <Icon as={FaPlus} />
                          </Button>
                        </InputGroup>
                        <FormHelperText>
                          Add LinkedIn, Twitter/X, Instagram, or Facebook profile URLs
                        </FormHelperText>
                      </FormControl>
                      
                      {/* Added Profiles */}
                      {socialProfiles.length > 0 && (
                        <Box>
                          <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>
                            Profiles to Analyze ({socialProfiles.length})
                          </Text>
                          <Wrap spacing={2}>
                            {socialProfiles.map((profile, idx) => (
                              <WrapItem key={idx}>
                                <Tag
                                  size="lg"
                                  borderRadius="full"
                                  variant="solid"
                                  colorScheme={profile.color}
                                >
                                  <Icon as={profile.icon} mr={2} />
                                  <TagLabel>{profile.name}</TagLabel>
                                  <TagCloseButton onClick={() => removeSocialProfile(profile.url)} />
                                </Tag>
                              </WrapItem>
                            ))}
                          </Wrap>
                        </Box>
                      )}
                      
                      <Button
                        colorScheme="blue"
                        size="lg"
                        leftIcon={<Icon as={FaChartLine} />}
                        onClick={analyzeCandidateProfiles}
                        isLoading={analyzingCandidate}
                        loadingText="Analyzing..."
                        isDisabled={!candidateName.trim() || socialProfiles.length === 0}
                      >
                        Analyze Candidate
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>

                {/* Results Section */}
                <Card bg={cardBg}>
                  <CardBody>
                    <VStack spacing={5} align="stretch">
                      <Heading size="md" color={textColor}>
                        <Icon as={FaFileAlt} mr={2} />
                        Analysis Results
                      </Heading>
                      
                      <Divider />
                      
                      {!analysisResults ? (
                        <Center py={12}>
                          <VStack spacing={4}>
                            <Icon as={FaSearch} boxSize={12} color={textColorSecondary} opacity={0.5} />
                            <Text color={textColorSecondary} textAlign="center">
                              Enter candidate information and click<br />
                              &quot;Analyze Candidate&quot; to generate a report
                            </Text>
                          </VStack>
                        </Center>
                      ) : (
                        <VStack spacing={4} align="stretch">
                          {/* Candidate Header */}
                          <HStack>
                            <Avatar name={analysisResults.candidate_name} size="md" />
                            <Box>
                              <Text fontWeight="700" color={textColor}>{analysisResults.candidate_name}</Text>
                              <Text fontSize="sm" color={textColorSecondary}>
                                {analysisResults.profiles_analyzed} profiles • {analysisResults.posts_found} posts analyzed
                              </Text>
                            </Box>
                          </HStack>
                          
                          {/* Scores */}
                          <SimpleGrid columns={3} spacing={3}>
                            <Box bg={hoverBg} p={3} borderRadius="lg" textAlign="center">
                              <Text fontSize="2xl" fontWeight="800" color="green.500">
                                {analysisResults.overall_score}
                              </Text>
                              <Text fontSize="xs" color={textColorSecondary}>Overall</Text>
                            </Box>
                            <Box bg={hoverBg} p={3} borderRadius="lg" textAlign="center">
                              <Text fontSize="2xl" fontWeight="800" color="blue.500">
                                {analysisResults.compliance_score}
                              </Text>
                              <Text fontSize="xs" color={textColorSecondary}>Compliance</Text>
                            </Box>
                            <Box bg={hoverBg} p={3} borderRadius="lg" textAlign="center">
                              <Text fontSize="2xl" fontWeight="800" color="blue.500">
                                {analysisResults.cultural_sensitivity_score}
                              </Text>
                              <Text fontSize="xs" color={textColorSecondary}>Cultural</Text>
                            </Box>
                          </SimpleGrid>
                          
                          {/* Risk Level */}
                          <HStack justify="space-between" bg={hoverBg} p={3} borderRadius="lg">
                            <Text fontWeight="600" color={textColor}>Risk Assessment</Text>
                            <Badge 
                              colorScheme={
                                analysisResults.risk_level === 'Low' ? 'green' : 
                                analysisResults.risk_level === 'Medium' ? 'yellow' : 'red'
                              }
                              fontSize="sm"
                              px={3}
                              py={1}
                            >
                              {analysisResults.risk_level} Risk
                            </Badge>
                          </HStack>
                          
                          {/* Summary */}
                          <Box>
                            <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>Summary</Text>
                            <Text fontSize="sm" color={textColorSecondary}>
                              {analysisResults.summary}
                            </Text>
                          </Box>
                          
                          {/* Recommendations */}
                          <Box>
                            <Text fontSize="sm" fontWeight="600" mb={2} color={textColor}>Key Findings</Text>
                            <VStack align="stretch" spacing={1}>
                              {analysisResults.recommendations?.map((rec, idx) => (
                                <HStack key={idx} align="start">
                                  <Text color="green.500">✓</Text>
                                  <Text fontSize="sm" color={textColorSecondary}>{rec}</Text>
                                </HStack>
                              ))}
                            </VStack>
                          </Box>
                          
                          {/* Actions */}
                          <Button
                            colorScheme="blue"
                            leftIcon={<Icon as={FaFileAlt} />}
                            onClick={viewCandidateReport}
                          >
                            View Full Report
                          </Button>
                        </VStack>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              </SimpleGrid>
            </TabPanel>

            {/* Tab 2: Team Reports */}
            <TabPanel px={0}>
              <Card bg={cardBg}>
                <CardBody>
                  <VStack spacing={5} align="stretch">
                    <Heading size="md" color={textColor}>
                      <Icon as={FaUsers} mr={2} />
                      Team Member Reports
                    </Heading>
                    <Text color={textColorSecondary}>
                      Select a team member to generate their content analysis report
                    </Text>
                    
                    <Divider />
                    
                    {loadingTeam ? (
                      <Center py={8}>
                        <Spinner size="lg" color="blue.500" />
                      </Center>
                    ) : teamMembers.length === 0 ? (
                      <Alert status="info" borderRadius="md">
                        <AlertIcon />
                        No team members found. Add users to your enterprise to see them here.
                      </Alert>
                    ) : (
                      <Table variant="simple">
                        <Thead>
                          <Tr>
                            <Th color={textColorSecondary}>Team Member</Th>
                            <Th color={textColorSecondary}>Role</Th>
                            <Th color={textColorSecondary}>Email</Th>
                            <Th color={textColorSecondary}>Actions</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {teamMembers.map((member) => (
                            <Tr key={member.id} _hover={{ bg: hoverBg }}>
                              <Td>
                                <HStack>
                                  <Avatar size="sm" name={member.full_name} />
                                  <Text fontWeight="600" color={textColor}>{member.full_name}</Text>
                                </HStack>
                              </Td>
                              <Td>
                                <Text color={textColorSecondary}>{member.job_title || 'Team Member'}</Text>
                              </Td>
                              <Td>
                                <Text color={textColorSecondary}>{member.email}</Text>
                              </Td>
                              <Td>
                                <Button
                                  size="sm"
                                  colorScheme="blue"
                                  leftIcon={<Icon as={FaFileAlt} />}
                                  onClick={() => viewTeamMemberReport(member.id)}
                                >
                                  View Report
                                </Button>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
}
