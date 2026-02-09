'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  HStack,
  VStack,
  Text,
  Icon,
  useColorModeValue,
  Progress,
  Badge,
  IconButton,
  Tooltip,
  Fade,
  ScaleFade,
  Portal,
} from '@chakra-ui/react';
import { FaPlay, FaTimes, FaChevronRight, FaChevronLeft, FaLightbulb, FaCheckCircle, FaRedo } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';

const MotionBox = motion(Box);

// Tutorial step highlight component - creates a spotlight effect
function TutorialSpotlight({ targetSelector, isActive }) {
  const [targetRect, setTargetRect] = useState(null);

  useEffect(() => {
    if (!isActive || !targetSelector) return;

    const updatePosition = () => {
      const element = document.querySelector(targetSelector);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect({
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height,
        });
        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);

    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [targetSelector, isActive]);

  if (!isActive || !targetRect) return null;

  return (
    <Portal>
      {/* Overlay with cutout */}
      <Box
        position="fixed"
        top={0}
        left={0}
        right={0}
        bottom={0}
        pointerEvents="none"
        zIndex={9998}
      >
        {/* Dark overlay with CSS mask for spotlight effect */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="blackAlpha.700"
          style={{
            maskImage: `radial-gradient(ellipse ${targetRect.width + 40}px ${targetRect.height + 40}px at ${targetRect.left + targetRect.width / 2}px ${targetRect.top - window.scrollY + targetRect.height / 2}px, transparent 50%, black 51%)`,
            WebkitMaskImage: `radial-gradient(ellipse ${targetRect.width + 40}px ${targetRect.height + 40}px at ${targetRect.left + targetRect.width / 2}px ${targetRect.top - window.scrollY + targetRect.height / 2}px, transparent 50%, black 51%)`,
          }}
        />
        {/* Highlight border around target */}
        <Box
          position="absolute"
          top={`${targetRect.top - window.scrollY - 4}px`}
          left={`${targetRect.left - 4}px`}
          width={`${targetRect.width + 8}px`}
          height={`${targetRect.height + 8}px`}
          border="3px solid"
          borderColor="brand.400"
          borderRadius="lg"
          boxShadow="0 0 20px rgba(66, 153, 225, 0.6)"
          animation="pulse 2s infinite"
          sx={{
            '@keyframes pulse': {
              '0%, 100%': { boxShadow: '0 0 20px rgba(66, 153, 225, 0.6)' },
              '50%': { boxShadow: '0 0 30px rgba(66, 153, 225, 0.9)' },
            },
          }}
        />
      </Box>
    </Portal>
  );
}

// Tutorial tooltip/popover component
function TutorialTooltip({ step, currentStep, totalSteps, onNext, onPrev, onClose, position = 'bottom' }) {
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('brand.200', 'brand.600');

  const positionStyles = {
    bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', mt: 4 },
    top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', mb: 4 },
    left: { right: '100%', top: '50%', transform: 'translateY(-50%)', mr: 4 },
    right: { left: '100%', top: '50%', transform: 'translateY(-50%)', ml: 4 },
  };

  return (
    <ScaleFade in={true} initialScale={0.9}>
      <Box
        position="absolute"
        {...positionStyles[position]}
        zIndex={10000}
        bg={bg}
        borderRadius="xl"
        boxShadow="2xl"
        border="2px solid"
        borderColor={borderColor}
        p={5}
        maxW="350px"
        minW="300px"
      >
        {/* Header */}
        <HStack justify="space-between" mb={3}>
          <HStack>
            <Icon as={FaLightbulb} color="yellow.400" />
            <Badge colorScheme="brand" fontSize="xs">
              Step {currentStep} of {totalSteps}
            </Badge>
          </HStack>
          <IconButton
            icon={<FaTimes />}
            size="xs"
            variant="ghost"
            onClick={onClose}
            aria-label="Close tutorial"
          />
        </HStack>

        {/* Progress */}
        <Progress
          value={(currentStep / totalSteps) * 100}
          size="xs"
          colorScheme="brand"
          borderRadius="full"
          mb={4}
        />

        {/* Content */}
        <VStack align="start" spacing={3} mb={4}>
          <Text fontWeight="bold" fontSize="lg" color="brand.500">
            {step.title}
          </Text>
          <Text fontSize="sm" color="gray.600">
            {step.description}
          </Text>
          {step.tip && (
            <Box bg="yellow.50" p={3} borderRadius="md" w="full">
              <HStack spacing={2} align="start">
                <Icon as={FaLightbulb} color="yellow.500" mt={0.5} />
                <Text fontSize="xs" color="yellow.800">
                  {step.tip}
                </Text>
              </HStack>
            </Box>
          )}
        </VStack>

        {/* Navigation */}
        <HStack justify="space-between">
          <Button
            size="sm"
            variant="ghost"
            leftIcon={<FaChevronLeft />}
            onClick={onPrev}
            isDisabled={currentStep === 1}
          >
            Back
          </Button>
          <Button
            size="sm"
            colorScheme="brand"
            rightIcon={currentStep === totalSteps ? <FaCheckCircle /> : <FaChevronRight />}
            onClick={onNext}
          >
            {currentStep === totalSteps ? 'Finish' : 'Next'}
          </Button>
        </HStack>
      </Box>
    </ScaleFade>
  );
}

// Main Interactive Tutorial Component
export function InteractiveTutorial({ 
  tutorialId,
  steps, 
  onComplete,
  autoStart = false,
  showRestartButton = true,
}) {
  const [isActive, setIsActive] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completed, setCompleted] = useState(false);

  const bg = useColorModeValue('brand.50', 'brand.900');
  const borderColor = useColorModeValue('brand.200', 'brand.700');

  // Check if tutorial was completed before
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const completedTutorials = JSON.parse(localStorage.getItem('completedTutorials') || '{}');
      if (completedTutorials[tutorialId]) {
        setCompleted(true);
      } else if (autoStart) {
        setIsActive(true);
      }
    }
  }, [tutorialId, autoStart]);

  const handleStart = () => {
    setIsActive(true);
    setCurrentStepIndex(0);
    setCompleted(false);
  };

  const handleClose = () => {
    setIsActive(false);
  };

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
    } else {
      // Tutorial completed
      setIsActive(false);
      setCompleted(true);
      // Save completion to localStorage
      if (typeof window !== 'undefined') {
        const completedTutorials = JSON.parse(localStorage.getItem('completedTutorials') || '{}');
        completedTutorials[tutorialId] = true;
        localStorage.setItem('completedTutorials', JSON.stringify(completedTutorials));
      }
      onComplete?.();
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  const currentStep = steps[currentStepIndex];

  return (
    <>
      {/* Tutorial Start/Restart Button */}
      {!isActive && (
        <Box
          bg={bg}
          borderRadius="lg"
          border="1px solid"
          borderColor={borderColor}
          p={4}
          mb={4}
        >
          <HStack justify="space-between" align="center">
            <HStack spacing={3}>
              <Icon as={FaPlay} color="brand.500" />
              <VStack align="start" spacing={0}>
                <Text fontWeight="600" fontSize="sm">
                  {completed ? 'Tutorial Completed!' : 'Interactive Tutorial Available'}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {completed 
                    ? 'Click restart to go through it again'
                    : `${steps.length} steps to help you get started`
                  }
                </Text>
              </VStack>
            </HStack>
            <Button
              size="sm"
              colorScheme="brand"
              leftIcon={completed ? <FaRedo /> : <FaPlay />}
              onClick={handleStart}
            >
              {completed ? 'Restart' : 'Start Tutorial'}
            </Button>
          </HStack>
        </Box>
      )}

      {/* Active Tutorial */}
      {isActive && currentStep && (
        <>
          <TutorialSpotlight 
            targetSelector={currentStep.targetSelector} 
            isActive={isActive} 
          />
          
          {/* Floating tooltip - positioned near target */}
          <Portal>
            <Box
              position="fixed"
              bottom={8}
              left="50%"
              transform="translateX(-50%)"
              zIndex={10000}
            >
              <TutorialTooltip
                step={currentStep}
                currentStep={currentStepIndex + 1}
                totalSteps={steps.length}
                onNext={handleNext}
                onPrev={handlePrev}
                onClose={handleClose}
              />
            </Box>
          </Portal>
        </>
      )}
    </>
  );
}

// Pre-built tutorial configurations
export const TUTORIAL_CONFIGS = {
  teamManagement: {
    id: 'team-management',
    steps: [
      {
        title: 'Welcome to Team Management',
        description: 'This is where you manage your team members, invite new collaborators, and assign roles.',
        targetSelector: '[data-testid="team-management-page"]',
        tip: 'Team management is only available to Admin users.',
      },
      {
        title: 'View Team Members',
        description: 'See all current team members, their roles, and status. Click on a member to see more details.',
        targetSelector: '[data-testid="team-members-table"]',
      },
      {
        title: 'Invite New Members',
        description: 'Click the "Invite Member" button to add new team members. You can assign them a role during invitation.',
        targetSelector: '[data-testid="invite-member-btn"]',
        tip: 'New members will receive an email with login instructions.',
      },
      {
        title: 'Change Member Roles',
        description: 'Click on the role badge to change a team member\'s role. Roles determine what actions they can perform.',
        targetSelector: '[data-testid="member-role-badge"]',
      },
    ],
  },
  strategicProfiles: {
    id: 'strategic-profiles',
    steps: [
      {
        title: 'Strategic Profiles Overview',
        description: 'Strategic Profiles define your brand identity, target audience, and regional settings for AI-powered analysis.',
        targetSelector: '[data-testid="profile-section"]',
      },
      {
        title: 'Brand Information',
        description: 'Set your company name, industry, brand voice, and values. This helps the AI generate content that sounds like your brand.',
        targetSelector: '[data-testid="brand-info-section"]',
        tip: 'Be specific with your brand voice - vague descriptions lead to generic outputs.',
      },
      {
        title: 'Target Audience',
        description: 'Define who your content is for. The AI uses this to adjust language complexity and topic relevance.',
        targetSelector: '[data-testid="audience-section"]',
      },
      {
        title: 'Regional Settings',
        description: 'Specify your operating regions for cultural sensitivity checks and compliance validation.',
        targetSelector: '[data-testid="regions-section"]',
      },
    ],
  },
  approvalWorkflow: {
    id: 'approval-workflow',
    steps: [
      {
        title: 'Content Approval Workflow',
        description: 'The approval workflow ensures content is reviewed before publishing. Let\'s see how it works.',
        targetSelector: '[data-testid="approval-section"]',
      },
      {
        title: 'Submit for Approval',
        description: 'After creating content, click "Submit for Approval" to send it to reviewers.',
        targetSelector: '[data-testid="submit-approval-btn"]',
      },
      {
        title: 'Review Queue',
        description: 'Managers and Admins can see pending content in the approval queue.',
        targetSelector: '[data-testid="approval-queue"]',
        tip: 'Content with low compliance scores may require additional review.',
      },
      {
        title: 'Approve or Request Changes',
        description: 'Reviewers can approve content for publishing or request changes with feedback.',
        targetSelector: '[data-testid="approval-actions"]',
      },
    ],
  },
  socialAccounts: {
    id: 'social-accounts',
    steps: [
      {
        title: 'Connect Social Accounts',
        description: 'Link your social media accounts to publish content directly from Contentry.',
        targetSelector: '[data-testid="social-accounts-section"]',
      },
      {
        title: 'Add New Account',
        description: 'Click "Connect Account" and follow the authorization flow for each platform.',
        targetSelector: '[data-testid="connect-account-btn"]',
        tip: 'You\'ll need admin access to your social accounts to connect them.',
      },
      {
        title: 'Manage Connections',
        description: 'View connected accounts, check their status, and disconnect if needed.',
        targetSelector: '[data-testid="connected-accounts-list"]',
      },
    ],
  },
};

// Quick-access tooltip component for contextual help
export function ContextualHelpTooltip({ label, children }) {
  const bg = useColorModeValue('white', 'gray.700');
  
  return (
    <Tooltip
      label={
        <Box p={2}>
          <HStack spacing={2} mb={1}>
            <Icon as={FaLightbulb} color="yellow.400" boxSize={3} />
            <Text fontWeight="600" fontSize="xs">Quick Tip</Text>
          </HStack>
          <Text fontSize="xs">{label}</Text>
        </Box>
      }
      bg={bg}
      borderRadius="md"
      boxShadow="lg"
      hasArrow
      placement="top"
    >
      {children}
    </Tooltip>
  );
}

export default InteractiveTutorial;
