'use client';
import { useTranslation } from 'react-i18next';
import { FaClipboardCheck, FaEdit, FaUserCog, FaCheckCircle, FaTimesCircle, FaClock, FaPaperPlane, FaHistory, FaBell, FaUser, FaUserShield } from 'react-icons/fa';
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Icon,
  useColorModeValue,
  SimpleGrid,
  Card,
  CardBody,
  Heading,
  Divider,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import DocumentationLayout, {
  DocSection,
  DocSubsection,
  DocParagraph,
  DocFeatureList,
  DocTip,
  DocScreenshot,
} from '../DocumentationLayout';
import { InteractiveTutorial, TUTORIAL_CONFIGS } from '@/components/documentation/InteractiveTutorial';

// Workflow Step Component
function WorkflowStep({ number, title, description, icon, status, role }) {
  const bgColor = useColorModeValue('brand.50', 'brand.900');
  const statusColors = {
    pending: 'yellow',
    approved: 'green',
    rejected: 'red',
    published: 'blue',
  };
  const roleColors = {
    creator: 'purple',
    manager: 'green',
  };
  
  return (
    <HStack align="start" spacing={4} p={4} bg={bgColor} borderRadius="lg">
      <Box
        w="40px"
        h="40px"
        borderRadius="full"
        bg="brand.500"
        color="white"
        display="flex"
        alignItems="center"
        justifyContent="center"
        fontWeight="bold"
        fontSize="lg"
        flexShrink={0}
      >
        {number}
      </Box>
      <VStack align="start" spacing={1} flex={1}>
        <HStack justify="space-between" w="full" flexWrap="wrap" gap={2}>
          <HStack>
            <Icon as={icon} color="brand.500" />
            <Text fontWeight="600">{title}</Text>
          </HStack>
          <HStack>
            {role && (
              <Badge colorScheme={roleColors[role]} variant="solid" fontSize="xs">
                {role === 'creator' ? '👤 Creator' : '🛡️ Manager'}
              </Badge>
            )}
            {status && (
              <Badge colorScheme={statusColors[status]}>{status}</Badge>
            )}
          </HStack>
        </HStack>
        <Text fontSize="sm" color="gray.600">{description}</Text>
      </VStack>
    </HStack>
  );
}

// Status Card Component
function StatusCard({ icon, title, color, description, actions }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} shadow="sm">
      <CardBody>
        <VStack align="start" spacing={3}>
          <HStack spacing={3}>
            <Box p={2} borderRadius="lg" bg={`${color}.100`}>
              <Icon as={icon} boxSize={5} color={`${color}.500`} />
            </Box>
            <Box>
              <Text fontWeight="bold">{title}</Text>
              <Badge colorScheme={color} variant="subtle" fontSize="xs">
                Status
              </Badge>
            </Box>
          </HStack>
          <Text fontSize="sm" color="gray.600">{description}</Text>
          {actions && actions.length > 0 && (
            <>
              <Divider />
              <Box>
                <Text fontWeight="600" fontSize="xs" color="gray.500" mb={1}>Available Actions:</Text>
                <VStack align="start" spacing={1}>
                  {actions.map((action, idx) => (
                    <HStack key={idx} spacing={2}>
                      <Icon as={FaCheckCircle} color={`${color}.400`} boxSize={3} />
                      <Text fontSize="sm">{action}</Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            </>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// Notification Example Card
function NotificationCard({ icon, title, message, time, type, forRole }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  const typeColors = {
    approved: 'green',
    rejected: 'red',
    pending: 'yellow',
    info: 'blue',
  };
  const roleColors = {
    creator: 'purple',
    manager: 'green',
  };
  
  return (
    <Card bg={cardBg} borderLeftWidth="4px" borderLeftColor={`${typeColors[type]}.400`} shadow="sm">
      <CardBody py={3}>
        <HStack justify="space-between" mb={2}>
          <HStack spacing={2}>
            <Icon as={icon} color={`${typeColors[type]}.500`} />
            <Text fontWeight="600" fontSize="sm">{title}</Text>
          </HStack>
          <Badge colorScheme={roleColors[forRole]} size="sm" variant="outline">
            {forRole === 'creator' ? 'Creator' : 'Manager'}
          </Badge>
        </HStack>
        <Text fontSize="sm" color="gray.600" mb={2}>{message}</Text>
        <Text fontSize="xs" color="gray.400">{time}</Text>
      </CardBody>
    </Card>
  );
}

export default function ApprovalGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'overview', title: 'Overview' },
    { id: 'why-approval', title: 'Why Use Approval Workflows?' },
    { id: 'workflow-stages', title: 'Workflow Stages' },
    { id: 'creator-workflow', title: 'Creator: Creating & Submitting Posts' },
    { id: 'manager-workflow', title: 'Manager: Reviewing & Approving Posts' },
    { id: 'notifications', title: 'Notifications & Alerts' },
    { id: 'best-practices', title: 'Best Practices' },
  ];

  return (
    <DocumentationLayout
      title="Content Approval Workflow Guide"
      description="Learn how to set up and manage content approval workflows for quality control and compliance"
      icon={FaClipboardCheck}
      iconColor="green"
      sections={sections}
    >
      {/* Overview */}
      <DocSection id="overview" title="Overview">
        {/* Interactive Tutorial */}
        <InteractiveTutorial
          tutorialId="approval-workflow"
          steps={TUTORIAL_CONFIGS.approvalWorkflow.steps}
          onComplete={() => console.log('Approval Workflow tutorial completed')}
        />
        
        <DocParagraph>
          The Content Approval Workflow ensures that all content published through Contentry.ai meets your 
          organization&apos;s quality standards and compliance requirements. Content created by team members 
          goes through a review process before being published, maintaining brand consistency and reducing risk.
        </DocParagraph>
        
        <DocFeatureList
          items={[
            'Multi-stage review process with clear status tracking',
            'Role-based permissions determine who can approve content',
            'Automatic re-analysis before scheduled posts go live',
            'Feedback system for revision requests',
            'Complete audit trail of all approval decisions',
          ]}
        />

        <DocTip type="info">
          The approval workflow is automatically enabled for team members with the &quot;Creator&quot; role. 
          Managers and Admins can publish directly but may still choose to use the approval process.
        </DocTip>
      </DocSection>

      {/* Why Use Approval Workflows */}
      <DocSection id="why-approval" title="Why Use Approval Workflows?">
        <DocParagraph>
          Approval workflows provide several critical benefits for teams managing content at scale:
        </DocParagraph>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaCheckCircle} color="green.500" />
                  <Text fontWeight="bold">Quality Control</Text>
                </HStack>
                <Text fontSize="sm">
                  Ensure all published content meets brand standards and quality benchmarks before it goes live.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaUserCog} color="blue.500" />
                  <Text fontWeight="bold">Compliance Assurance</Text>
                </HStack>
                <Text fontSize="sm">
                  Managers can verify content meets regulatory and industry requirements before publication.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaHistory} color="purple.500" />
                  <Text fontWeight="bold">Audit Trail</Text>
                </HStack>
                <Text fontSize="sm">
                  Complete history of who created, reviewed, approved, and published each piece of content.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaEdit} color="orange.500" />
                  <Text fontWeight="bold">Feedback Loop</Text>
                </HStack>
                <Text fontSize="sm">
                  Structured feedback when content needs revision, helping creators improve over time.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>
      </DocSection>

      {/* Workflow Stages */}
      <DocSection id="workflow-stages" title="Workflow Stages">
        <DocParagraph>
          Content moves through several stages in the approval workflow. Understanding each stage helps 
          you track where your content is and what actions are needed.
        </DocParagraph>

        <Box mb={6}>
          <Heading size="md" mb={4}>Content Status Flow</Heading>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
            <StatusCard
              icon={FaEdit}
              title="Draft"
              color="gray"
              description="Content is being created or edited. Not yet submitted for review."
              actions={['Edit content', 'Submit for approval', 'Delete draft']}
            />
            <StatusCard
              icon={FaClock}
              title="Pending Review"
              color="yellow"
              description="Content has been submitted and is waiting for a Manager to review."
              actions={['View status', 'Cancel submission']}
            />
            <StatusCard
              icon={FaCheckCircle}
              title="Approved"
              color="green"
              description="Content has been approved and is ready for publishing or scheduling."
              actions={['Publish now', 'Schedule for later', 'View feedback']}
            />
            <StatusCard
              icon={FaTimesCircle}
              title="Rejected"
              color="red"
              description="Content needs changes. Review the feedback and resubmit."
              actions={['View feedback', 'Edit content', 'Resubmit for review']}
            />
          </SimpleGrid>
        </Box>

        <DocTip type="warning">
          Once content is published, it cannot be unpublished through Contentry.ai. 
          Ensure thorough review before final approval.
        </DocTip>
      </DocSection>

      {/* CREATOR WORKFLOW - Detailed Step-by-Step */}
      <DocSection id="creator-workflow" title="Creator: Creating & Submitting Posts">
        <Alert status="info" borderRadius="md" mb={6}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">This section is for users with the Creator role</Text>
            <Text fontSize="sm">Creators can generate content but need Manager approval before publishing.</Text>
          </Box>
        </Alert>

        <DocSubsection title="Step 1: Access Content Generation">
          <DocParagraph>
            Navigate to &quot;Content Intelligence&quot; → &quot;Content Generation&quot; from the sidebar to start creating new content.
          </DocParagraph>
          <DocScreenshot pageId="creator-content-generation" caption="Content Generation page where Creators write or generate new posts" />
        </DocSubsection>

        <DocSubsection title="Step 2: Create Your Content">
          <DocParagraph>
            Write your content manually or use AI to generate it. Select the target platform (Twitter/X, LinkedIn, etc.) 
            and adjust the tone and style as needed.
          </DocParagraph>
          <DocFeatureList
            items={[
              'Choose your target social media platform',
              'Enter a prompt or write content directly',
              'Use AI generation for suggestions',
              'Adjust tone (Professional, Casual, etc.)',
              'Add images or media if needed',
            ]}
          />
          <DocScreenshot pageId="creator-writing-content" caption="Creator writing content with platform and tone selection" />
        </DocSubsection>

        <DocSubsection title="Step 3: Review AI Analysis Scores">
          <DocParagraph>
            Before submitting, review the AI analysis scores. These show how well your content aligns with 
            brand guidelines, cultural sensitivity requirements, and compliance rules.
          </DocParagraph>
          <DocScreenshot pageId="creator-analysis-scores" caption="AI analysis showing Cultural Fit, Brand Alignment, and Compliance scores" />
          <DocTip type="tip">
            Address any flagged issues before submitting. Content with low scores may be rejected by Managers.
          </DocTip>
        </DocSubsection>

        <DocSubsection title="Step 4: Submit for Approval">
          <DocParagraph>
            When you&apos;re satisfied with your content, click the &quot;Submit for Approval&quot; button. 
            You can add an optional note explaining the context or any special considerations for the reviewer.
          </DocParagraph>
          <DocScreenshot pageId="creator-submit-approval" caption="Submit for Approval button and optional note field" />
          <Box my={4}>
            <WorkflowStep 
              number={1} 
              title="Click 'Submit for Approval'" 
              description="Find the Submit button at the bottom of the content editor."
              icon={FaPaperPlane}
              role="creator"
            />
            <Box mt={2}>
              <WorkflowStep 
                number={2} 
                title="Add a Note (Optional)" 
                description="Explain context, urgency, or special requirements for the reviewer."
                icon={FaEdit}
                role="creator"
              />
            </Box>
            <Box mt={2}>
              <WorkflowStep 
                number={3} 
                title="Confirm Submission" 
                description="Your content enters the approval queue and Managers are notified."
                icon={FaCheckCircle}
                role="creator"
                status="pending"
              />
            </Box>
          </Box>
        </DocSubsection>

        <DocSubsection title="Step 5: Wait for Manager Review">
          <DocParagraph>
            After submission, your content appears in the &quot;Scheduled&quot; tab with a &quot;Pending Review&quot; status. 
            You&apos;ll receive a notification when a Manager makes a decision.
          </DocParagraph>
          <DocScreenshot pageId="creator-pending-status" caption="Content showing 'Pending Review' status in the Scheduled tab" />
        </DocSubsection>
      </DocSection>

      {/* MANAGER WORKFLOW - Detailed Step-by-Step */}
      <DocSection id="manager-workflow" title="Manager: Reviewing & Approving Posts">
        <Alert status="success" borderRadius="md" mb={6}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">This section is for users with the Manager or Admin role</Text>
            <Text fontSize="sm">Managers review submitted content and decide whether to approve or reject it.</Text>
          </Box>
        </Alert>

        <DocSubsection title="Step 1: Access the Approval Queue">
          <DocParagraph>
            Navigate to &quot;Content Intelligence&quot; → &quot;Scheduled&quot; tab to see all content pending approval. 
            You&apos;ll see a notification badge when new items are waiting for review.
          </DocParagraph>
          <DocScreenshot pageId="manager-approval-queue" caption="Approval queue showing all pending content submissions" />
        </DocSubsection>

        <DocSubsection title="Step 2: Review Content Details">
          <DocParagraph>
            Click on any pending item to view the full content, AI analysis scores, the creator&apos;s notes, 
            and submission history.
          </DocParagraph>
          <DocScreenshot pageId="manager-review-content" caption="Manager viewing content details, scores, and creator notes" />
          <DocFeatureList
            items={[
              'Full content preview as it will appear on the platform',
              'AI analysis scores (Cultural Fit, Brand Alignment, Compliance)',
              'Creator name and submission timestamp',
              'Any notes added by the creator',
              'Previous revision history (if resubmitted)',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Step 3: Make Your Decision">
          <DocParagraph>
            After reviewing, you have two options: Approve the content or Reject it with feedback.
          </DocParagraph>
          
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={4}>
            <Card borderColor="green.300" borderWidth="2px">
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Icon as={FaCheckCircle} color="green.500" boxSize={6} />
                    <Text fontWeight="bold" fontSize="lg">Approve</Text>
                  </HStack>
                  <Text fontSize="sm">
                    Content meets all standards. The Creator can now publish or schedule it immediately.
                  </Text>
                  <DocScreenshot pageId="manager-approve-action" caption="Click 'Approve' to allow publishing" />
                </VStack>
              </CardBody>
            </Card>
            <Card borderColor="red.300" borderWidth="2px">
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Icon as={FaTimesCircle} color="red.500" boxSize={6} />
                    <Text fontWeight="bold" fontSize="lg">Reject with Feedback</Text>
                  </HStack>
                  <Text fontSize="sm">
                    Content needs changes. Provide specific feedback so the Creator knows what to fix.
                  </Text>
                  <DocScreenshot pageId="manager-reject-feedback" caption="Rejection dialog with feedback field" />
                </VStack>
              </CardBody>
            </Card>
          </SimpleGrid>

          <DocTip type="tip">
            When rejecting content, always provide constructive, specific feedback. Instead of &quot;Not good enough,&quot; 
            try &quot;The tone is too casual for our B2B audience. Please make it more professional.&quot;
          </DocTip>
        </DocSubsection>

        <DocSubsection title="Step 4: Track Approved/Rejected Content">
          <DocParagraph>
            Use the filter options in the Scheduled tab to view all approved or rejected content. 
            This helps you track workflow efficiency and identify patterns.
          </DocParagraph>
          <DocScreenshot pageId="manager-filter-status" caption="Filtering content by approval status" />
        </DocSubsection>
      </DocSection>

      {/* NOTIFICATIONS - With Screenshots */}
      <DocSection id="notifications" title="Notifications & Alerts">
        <DocParagraph>
          Stay informed about approval workflow events through in-app notifications and email alerts. 
          Different roles receive different notifications based on their responsibilities.
        </DocParagraph>

        <DocSubsection title="Creator Notifications">
          <DocParagraph>
            Creators receive notifications when their submitted content is reviewed:
          </DocParagraph>
          
          <VStack spacing={3} mb={4}>
            <NotificationCard
              icon={FaCheckCircle}
              title="Content Approved"
              message="Your post 'Q4 Product Launch Announcement' has been approved by Sarah (Manager). You can now publish or schedule it."
              time="2 minutes ago"
              type="approved"
              forRole="creator"
            />
            <NotificationCard
              icon={FaTimesCircle}
              title="Content Needs Revision"
              message="Your post 'Holiday Sale Campaign' was returned for revision. Feedback: 'Please update the discount percentage to match the approved 20% limit.'"
              time="15 minutes ago"
              type="rejected"
              forRole="creator"
            />
          </VStack>
          
          <DocScreenshot pageId="creator-notification-approved" caption="Creator receiving approval notification with publish options" />
          <DocScreenshot pageId="creator-notification-rejected" caption="Creator receiving rejection notification with Manager feedback" />
        </DocSubsection>

        <DocSubsection title="Manager Notifications">
          <DocParagraph>
            Managers receive notifications when new content is submitted for review:
          </DocParagraph>
          
          <VStack spacing={3} mb={4}>
            <NotificationCard
              icon={FaClock}
              title="New Content Pending Review"
              message="John (Creator) submitted 'Weekly Newsletter Draft' for approval. Click to review."
              time="Just now"
              type="pending"
              forRole="manager"
            />
            <NotificationCard
              icon={FaBell}
              title="Approval Queue Summary"
              message="You have 5 items pending review. 2 are marked as urgent."
              time="9:00 AM"
              type="info"
              forRole="manager"
            />
          </VStack>
          
          <DocScreenshot pageId="manager-notification-new" caption="Manager notification for new content submission" />
          <DocScreenshot pageId="manager-notification-queue" caption="Daily approval queue summary notification" />
        </DocSubsection>

        <DocSubsection title="Notification Settings">
          <DocParagraph>
            You can customize which notifications you receive in Settings → Notifications:
          </DocParagraph>
          <DocFeatureList
            items={[
              'In-app notifications (always enabled)',
              'Email notifications (configurable)',
              'Push notifications (if browser enabled)',
              'Daily digest vs. real-time alerts',
              'Urgent-only mode for managers',
            ]}
          />
        </DocSubsection>
      </DocSection>

      {/* Best Practices */}
      <DocSection id="best-practices" title="Best Practices">
        <DocSubsection title="For Creators">
          <DocFeatureList
            items={[
              'Review AI analysis scores before submitting - fix flagged issues first',
              'Add helpful notes for reviewers explaining context or urgency',
              'Don\'t submit incomplete drafts - review thoroughly first',
              'Learn from rejection feedback to improve future content',
              'Check the Scheduled tab to track your submission status',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="For Managers">
          <DocFeatureList
            items={[
              'Review pending items promptly - don\'t create bottlenecks',
              'Provide specific, actionable feedback when rejecting',
              'Use Quick Approve for trusted creators to improve efficiency',
              'Set expectations with creators about review turnaround times',
              'Regularly check the approval queue for pending items',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="For Teams">
          <DocFeatureList
            items={[
              'Establish clear content guidelines that everyone understands',
              'Document common rejection reasons to reduce repeat issues',
              'Schedule regular reviews of the approval process efficiency',
              'Consider multiple reviewers for high-stakes content',
            ]}
          />
        </DocSubsection>
      </DocSection>
    </DocumentationLayout>
  );
}
