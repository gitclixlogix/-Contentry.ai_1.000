'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  Text,
  Button,
  Input,
  Textarea,
  VStack,
  HStack,
  Icon,
  Spinner,
  useToast,
  Progress,
  useColorModeValue,
  Circle,
  Badge,
  Link,
} from '@chakra-ui/react';
import { keyframes } from '@emotion/react';
import {
  Sparkles,
  Globe,
  FileText,
  Zap,
  CheckCircle,
  ArrowRight,
  Upload,
  Shield,
  Users,
  Target,
  ChevronRight,
  PartyPopper,
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

// Animation keyframes
const pulseKeyframes = keyframes`
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
`;

const floatKeyframes = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
`;

// Step definitions
const STEPS = [
  { id: 'welcome', title: 'Welcome', icon: Sparkles },
  { id: 'website', title: 'Your Website', icon: Globe },
  { id: 'document', title: 'Brand Rules', icon: FileText },
  { id: 'analyze', title: 'First Analysis', icon: Zap },
  { id: 'complete', title: 'Complete', icon: CheckCircle },
];

export default function OnboardingWizard() {
  const { user } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const fileInputRef = useRef(null);

  // State
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [wizardData, setWizardData] = useState({
    websiteUrl: '',
    websiteScraped: false,
    documentUploaded: false,
    documentName: '',
    contentToAnalyze: '',
    analysisResult: null,
    profileId: null,
  });

  // Colors
  const bgColor = useColorModeValue('gray.50', 'navy.900');
  const cardBg = useColorModeValue('white', 'navy.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const brandColor = useColorModeValue('brand.500', 'brand.400');

  // Check onboarding status on mount
  useEffect(() => {
    const checkStatus = async () => {
      // If no user, redirect to auth page
      if (!user?.id) {
        // Wait a bit for auth to potentially load
        setTimeout(() => {
          if (!user?.id) {
            router.push('/contentry/auth');
          }
        }, 1500);
        return;
      }

      try {
        const response = await axios.get(`${getApiUrl()}/onboarding/status`, {
          headers: { 'X-User-ID': user.id },
        });

        if (response.data.has_completed_onboarding) {
          // User already completed onboarding, redirect to dashboard
          router.push('/contentry/dashboard');
          return;
        }

        // Resume from saved progress
        const stepIndex = response.data.step_index || 0;
        setCurrentStep(stepIndex);

        if (response.data.data) {
          setWizardData((prev) => ({
            ...prev,
            ...response.data.data,
            profileId: response.data.profile_id,
          }));
        }
      } catch (error) {
        console.error('Error checking onboarding status:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkStatus();
  }, [user?.id, router]);

  // Save progress
  const saveProgress = async (step, data = {}) => {
    if (!user?.id) return;

    try {
      await axios.put(
        `${getApiUrl()}/onboarding/progress`,
        {
          current_step: STEPS[step].id,
          data: { ...wizardData, ...data },
        },
        { headers: { 'X-User-ID': user.id } }
      );
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  };

  // Go to next step
  const nextStep = (data = {}) => {
    const newStep = Math.min(currentStep + 1, STEPS.length - 1);
    setCurrentStep(newStep);
    setWizardData((prev) => ({ ...prev, ...data }));
    saveProgress(newStep, data);
  };

  // Skip current step
  const skipStep = () => {
    nextStep();
  };

  // Skip entire wizard
  const skipWizard = async () => {
    try {
      await axios.post(
        `${getApiUrl()}/onboarding/skip`,
        {},
        { headers: { 'X-User-ID': user.id } }
      );
      router.push('/contentry/dashboard');
    } catch (error) {
      console.error('Error skipping onboarding:', error);
      router.push('/contentry/dashboard');
    }
  };

  // Complete onboarding
  const completeOnboarding = async () => {
    try {
      await axios.post(
        `${getApiUrl()}/onboarding/complete`,
        {},
        { headers: { 'X-User-ID': user.id } }
      );
      router.push('/contentry/dashboard');
    } catch (error) {
      console.error('Error completing onboarding:', error);
      router.push('/contentry/dashboard');
    }
  };

  // Scrape website
  const handleScrapeWebsite = async () => {
    if (!wizardData.websiteUrl.trim()) {
      toast({
        title: 'Please enter a website URL',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsProcessing(true);
    try {
      const response = await axios.post(
        `${getApiUrl()}/onboarding/scrape-website`,
        { url: wizardData.websiteUrl },
        { headers: { 'X-User-ID': user.id } }
      );

      toast({
        title: 'Website analyzed!',
        description: response.data.message,
        status: 'success',
        duration: 3000,
      });

      nextStep({
        websiteScraped: true,
        profileId: response.data.profile_id,
      });
    } catch (error) {
      toast({
        title: 'Could not analyze website',
        description: error.response?.data?.detail || 'Please check the URL and try again',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Upload document
  const handleUploadDocument = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${getApiUrl()}/onboarding/upload-document`,
        formData,
        {
          headers: {
            'X-User-ID': user.id,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      toast({
        title: 'Document uploaded!',
        description: response.data.message,
        status: 'success',
        duration: 3000,
      });

      nextStep({
        documentUploaded: true,
        documentName: file.name,
        profileId: response.data.profile_id,
      });
    } catch (error) {
      toast({
        title: 'Could not upload document',
        description: error.response?.data?.detail || 'Please try again',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Analyze content
  const handleAnalyzeContent = async () => {
    if (!wizardData.contentToAnalyze.trim() || wizardData.contentToAnalyze.length < 10) {
      toast({
        title: 'Please enter some content',
        description: 'Enter at least a sentence to analyze',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsProcessing(true);
    try {
      const response = await axios.post(
        `${getApiUrl()}/onboarding/analyze-content`,
        { content: wizardData.contentToAnalyze },
        { headers: { 'X-User-ID': user.id } }
      );

      nextStep({
        analysisResult: response.data.analysis,
      });
    } catch (error) {
      toast({
        title: 'Analysis error',
        description: 'Could not analyze content. Please try again.',
        status: 'error',
        duration: 4000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg={bgColor}>
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  // Render current step
  const renderStep = () => {
    switch (STEPS[currentStep].id) {
      case 'welcome':
        return (
          <VStack spacing={8} textAlign="center" maxW="600px">
            <Box animation={`${floatKeyframes} 3s ease-in-out infinite`}>
              <Circle size="100px" bg="brand.100">
                <Icon as={Sparkles} boxSize={12} color="brand.500" />
              </Circle>
            </Box>
            <VStack spacing={3}>
              <Text fontSize="3xl" fontWeight="bold" color={textColor}>
                Welcome to Contentry.ai! 🎉
              </Text>
              <Text fontSize="lg" color={textSecondary} maxW="500px">
                Let's set up your first "Brand Brain" in the next 60 seconds. 
                This will teach the AI how to analyze content just for you.
              </Text>
            </VStack>
            <Button
              size="lg"
              colorScheme="brand"
              rightIcon={<ArrowRight />}
              onClick={() => nextStep()}
              px={8}
            >
              Let's Get Started
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={skipWizard} 
              color={textSecondary}
              _hover={{ color: brandColor }}
            >
              Skip for now, explore the app →
            </Button>
          </VStack>
        );

      case 'website':
        return (
          <VStack spacing={6} maxW="500px" w="100%">
            <Circle size="80px" bg="blue.100">
              <Icon as={Globe} boxSize={10} color="blue.500" />
            </Circle>
            <VStack spacing={2} textAlign="center">
              <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                What is your company's website?
              </Text>
              <Text color={textSecondary}>
                The AI will analyze your website to learn your brand's tone, voice, and key topics.
                You can add more sources later.
              </Text>
            </VStack>
            <Input
              size="lg"
              placeholder="https://www.example.com"
              value={wizardData.websiteUrl}
              onChange={(e) => setWizardData({ ...wizardData, websiteUrl: e.target.value })}
              bg={cardBg}
              borderColor={borderColor}
            />
            <HStack spacing={4} w="100%">
              <Button
                flex={1}
                size="lg"
                colorScheme="brand"
                rightIcon={isProcessing ? <Spinner size="sm" /> : <ArrowRight />}
                onClick={handleScrapeWebsite}
                isDisabled={isProcessing}
              >
                {isProcessing ? 'Analyzing...' : 'Analyze Website'}
              </Button>
            </HStack>
            <Button variant="ghost" size="sm" onClick={skipStep} color={textSecondary}>
              Skip this step →
            </Button>
          </VStack>
        );

      case 'document':
        return (
          <VStack spacing={6} maxW="500px" w="100%">
            <Circle size="80px" bg="green.100">
              <Icon as={FileText} boxSize={10} color="green.500" />
            </Circle>
            <VStack spacing={2} textAlign="center">
              <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                What are your core rules?
              </Text>
              <Text color={textSecondary}>
                Upload a brand guide, compliance document, or a simple text file with your "dos and don'ts."
                The AI will learn these rules instantly.
              </Text>
            </VStack>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={handleUploadDocument}
            />
            <Box
              w="100%"
              p={8}
              border="2px dashed"
              borderColor={borderColor}
              borderRadius="xl"
              textAlign="center"
              cursor="pointer"
              onClick={() => fileInputRef.current?.click()}
              _hover={{ borderColor: 'brand.500', bg: useColorModeValue('brand.50', 'whiteAlpha.50') }}
              transition="all 0.2s"
            >
              {isProcessing ? (
                <VStack spacing={3}>
                  <Spinner size="lg" color="brand.500" />
                  <Text color={textSecondary}>Processing document...</Text>
                </VStack>
              ) : (
                <VStack spacing={3}>
                  <Icon as={Upload} boxSize={10} color={textSecondary} />
                  <Text fontWeight="medium" color={textColor}>
                    Click to upload or drag and drop
                  </Text>
                  <Text fontSize="sm" color={textSecondary}>
                    PDF, DOCX, DOC, TXT, or MD (max 20MB)
                  </Text>
                </VStack>
              )}
            </Box>
            <Button variant="ghost" size="sm" onClick={skipStep} color={textSecondary}>
              Skip this step →
            </Button>
          </VStack>
        );

      case 'analyze':
        return (
          <VStack spacing={6} maxW="600px" w="100%">
            <Circle size="80px" bg="blue.100">
              <Icon as={Zap} boxSize={10} color="blue.500" />
            </Circle>
            <VStack spacing={2} textAlign="center">
              <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                Let's see it in action!
              </Text>
              <Text color={textSecondary}>
                Paste a recent social media post, a paragraph from an email, or any other piece of content
                below to get your first score.
              </Text>
            </VStack>
            <Textarea
              size="lg"
              placeholder="Enter your content here... (e.g., a social media post, email paragraph, or marketing copy)"
              value={wizardData.contentToAnalyze}
              onChange={(e) => setWizardData({ ...wizardData, contentToAnalyze: e.target.value })}
              rows={6}
              bg={cardBg}
              borderColor={borderColor}
            />
            <Button
              size="lg"
              colorScheme="brand"
              rightIcon={isProcessing ? <Spinner size="sm" /> : <Zap />}
              onClick={handleAnalyzeContent}
              isDisabled={isProcessing || wizardData.contentToAnalyze.length < 10}
              w="100%"
            >
              {isProcessing ? 'Analyzing...' : 'Analyze My Content'}
            </Button>
          </VStack>
        );

      case 'complete':
        const analysis = wizardData.analysisResult || {};
        return (
          <VStack spacing={8} maxW="600px" w="100%" textAlign="center">
            <Box animation={`${pulseKeyframes} 2s ease-in-out infinite`}>
              <Circle size="100px" bg="green.100">
                <Icon as={PartyPopper} boxSize={12} color="green.500" />
              </Circle>
            </Box>
            <VStack spacing={3}>
              <Text fontSize="3xl" fontWeight="bold" color={textColor}>
                Your First Content Score is In! 🎉
              </Text>
              <Text color={textSecondary}>
                Contentry.ai has checked your content against your website and brand rules.
              </Text>
            </VStack>

            {/* Score Cards */}
            <HStack spacing={4} w="100%" justify="center" flexWrap="wrap">
              <ScoreCard
                label="Overall"
                score={analysis.overall_score || 78}
                icon={Target}
                color="brand"
              />
              <ScoreCard
                label="Compliance"
                score={analysis.compliance_score || 82}
                icon={Shield}
                color="blue"
              />
              <ScoreCard
                label="Cultural"
                score={analysis.cultural_sensitivity_score || 80}
                icon={Users}
                color="blue"
              />
              <ScoreCard
                label="Accuracy"
                score={analysis.accuracy_score || 75}
                icon={CheckCircle}
                color="green"
              />
            </HStack>

            {analysis.summary && (
              <Box p={4} bg={useColorModeValue('gray.50', 'whiteAlpha.100')} borderRadius="lg" w="100%">
                <Text fontSize="sm" color={textSecondary}>
                  {analysis.summary}
                </Text>
              </Box>
            )}

            <Text color={textSecondary} fontSize="sm">
              You can now do this for any piece of content to ensure it's always on-brand and compliant.
            </Text>

            <Button
              size="lg"
              colorScheme="brand"
              rightIcon={<ChevronRight />}
              onClick={completeOnboarding}
              px={8}
            >
              Finish & Enter My Dashboard
            </Button>
          </VStack>
        );

      default:
        return null;
    }
  };

  return (
    <Flex
      minH="100vh"
      bg={bgColor}
      align="center"
      justify="center"
      position="relative"
      overflow="hidden"
    >
      {/* Background decoration */}
      <Box
        position="absolute"
        top="-20%"
        right="-10%"
        w="600px"
        h="600px"
        borderRadius="full"
        bg="brand.500"
        opacity={0.05}
        filter="blur(100px)"
      />

      <VStack spacing={8} p={8} maxW="800px" w="100%">
        {/* Progress indicator */}
        <HStack spacing={2} w="100%" maxW="400px">
          {STEPS.map((step, index) => (
            <Box
              key={step.id}
              flex={1}
              h="4px"
              bg={index <= currentStep ? 'brand.500' : borderColor}
              borderRadius="full"
              transition="all 0.3s"
            />
          ))}
        </HStack>

        {/* Step indicator */}
        <Text fontSize="sm" color={textSecondary}>
          Step {currentStep + 1} of {STEPS.length}
        </Text>

        {/* Main content card */}
        <Box
          bg={cardBg}
          borderRadius="2xl"
          p={{ base: 6, md: 10 }}
          shadow="xl"
          w="100%"
          border="1px solid"
          borderColor={borderColor}
        >
          <Flex justify="center" align="center" minH="400px">
            {renderStep()}
          </Flex>
        </Box>

        {/* Skip wizard link */}
        {currentStep < STEPS.length - 1 && (
          <Link
            fontSize="sm"
            color={textSecondary}
            onClick={skipWizard}
            _hover={{ color: brandColor }}
            cursor="pointer"
          >
            I'll do this later, take me to my dashboard →
          </Link>
        )}
      </VStack>
    </Flex>
  );
}

// Score Card Component
function ScoreCard({ label, score, icon: IconComponent, color }) {
  const cardBg = useColorModeValue('white', 'navy.700');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');

  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    return 'red';
  };

  return (
    <VStack
      p={4}
      bg={cardBg}
      borderRadius="xl"
      border="1px solid"
      borderColor={borderColor}
      minW="120px"
      spacing={2}
    >
      <Icon as={IconComponent} boxSize={5} color={`${color}.500`} />
      <Text fontSize="2xl" fontWeight="bold" color={`${getScoreColor(score)}.500`}>
        {score}
      </Text>
      <Text fontSize="xs" color="gray.500" textTransform="uppercase">
        {label}
      </Text>
    </VStack>
  );
}
