'use client';
import { useTranslation } from 'react-i18next';
import { FaUsers, FaShieldAlt, FaUserPlus, FaCheckCircle, FaUserCog, FaEdit, FaClipboardCheck } from 'react-icons/fa';
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

// Role Cards Component for visual role explanation
function RoleCard({ icon, title, color, permissions, description }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} shadow="sm">
      <CardBody>
        <VStack align="start" spacing={3}>
          <HStack spacing={3}>
            <Box
              p={2}
              borderRadius="lg"
              bg={`${color}.100`}
            >
              <Icon as={icon} boxSize={5} color={`${color}.500`} />
            </Box>
            <Box>
              <Text fontWeight="bold" fontSize="lg">{title}</Text>
              <Badge colorScheme={color} variant="subtle" fontSize="xs">
                {permissions.length} permissions
              </Badge>
            </Box>
          </HStack>
          <Text fontSize="sm" color="gray.600">{description}</Text>
          <Divider />
          <VStack align="start" spacing={1} w="full">
            {permissions.map((perm, idx) => (
              <HStack key={idx} spacing={2}>
                <Icon as={FaCheckCircle} color={`${color}.400`} boxSize={3} />
                <Text fontSize="sm">{perm}</Text>
              </HStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
}

// Workflow Step Component
function WorkflowStep({ number, title, description, icon }) {
  const bgColor = useColorModeValue('brand.50', 'brand.900');
  const textColor = useColorModeValue('gray.700', 'gray.200');
  
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
      <VStack align="start" spacing={1}>
        <HStack>
          <Icon as={icon} color="brand.500" />
          <Text fontWeight="600">{title}</Text>
        </HStack>
        <Text fontSize="sm" color={textColor}>{description}</Text>
      </VStack>
    </HStack>
  );
}

export default function TeamsGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'overview', title: 'Overview' },
    { id: 'team-management', title: 'Team Management' },
    { id: 'roles-permissions', title: 'Roles & Permissions' },
    { id: 'assigning-roles', title: 'Assigning Roles' },
    { id: 'approval-workflow', title: 'Content Approval Workflow' },
    { id: 'best-practices', title: 'Best Practices' },
  ];

  return (
    <DocumentationLayout
      title="Teams & Roles Guide"
      description="Learn how to manage your team and set up content approval workflows"
      icon={FaUsers}
      iconColor="purple"
      sections={sections}
    >
      {/* Overview */}
      <DocSection id="overview" title="Overview">
        {/* Interactive Tutorial */}
        <InteractiveTutorial
          tutorialId="team-management"
          steps={TUTORIAL_CONFIGS.teamManagement.steps}
          onComplete={() => console.log('Team Management tutorial completed')}
        />
        
        <DocParagraph>
          Contentry.ai provides a comprehensive team management system that allows you to collaborate 
          effectively while maintaining control over content quality and compliance. With role-based 
          access control, you can define exactly who can create, review, approve, and publish content.
        </DocParagraph>
        
        <DocFeatureList
          items={[
            'Invite team members and assign roles',
            'Three predefined roles: Creator, Manager, and Admin',
            'Set up multi-stage content approval workflows',
            'Manage enterprise-wide teams with hierarchy support',
          ]}
        />

        <DocTip type="info">
          Team management features are available on Pro and Enterprise plans. Free users can upgrade 
          to access team collaboration features.
        </DocTip>
      </DocSection>

      {/* Team Management */}
      <DocSection id="team-management" title="Team Management">
        <DocParagraph>
          The Team Management page is your central hub for managing collaborators. Here you can 
          invite new members, view current team composition, and manage member roles.
        </DocParagraph>

        <DocScreenshot pageId="team-management" caption="Team Management interface showing team members and their roles" />

        <DocSubsection title="Inviting Team Members">
          <DocParagraph>
            To invite a new team member:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Navigate to Settings → Team from the sidebar',
              'Click the "Invite Team Member" button',
              'Enter the email address of the person you want to invite',
              'Select an appropriate role from the dropdown',
              'Optionally add a personal message',
              'Click "Send Invitation" to dispatch the invite',
            ]}
          />
          
          <DocTip type="tip">
            You can also copy the invitation link directly and share it via your preferred 
            communication channel (Slack, email, etc.).
          </DocTip>
        </DocSubsection>

        <DocSubsection title="Managing Existing Members">
          <DocParagraph>
            For each team member, you can:
          </DocParagraph>
          <DocFeatureList
            items={[
              'View their current role and permissions',
              'Change their role (if you have admin privileges)',
              'Remove them from the team',
              'See when they joined and their last activity',
            ]}
          />
        </DocSubsection>
      </DocSection>

      {/* Roles & Permissions */}
      <DocSection id="roles-permissions" title="Roles & Permissions">
        <DocParagraph>
          Contentry.ai comes with three predefined roles designed to cover common collaboration scenarios. 
          Each role has a specific set of permissions that determine what actions members can perform.
        </DocParagraph>

        <DocScreenshot pageId="team-management" caption="Team Management page showing members and their roles" />

        <Box mb={6}>
          <Heading size="md" mb={4}>Available Roles</Heading>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            <RoleCard
              icon={FaEdit}
              title="Creator"
              color="blue"
              description="For team members who create content that needs review before publishing."
              permissions={[
                'Create & edit content',
                'View strategic profiles',
                'Submit for approval',
                'View own analytics',
              ]}
            />
            <RoleCard
              icon={FaUserCog}
              title="Manager"
              color="green"
              description="For supervisors who review and approve content from creators."
              permissions={[
                'All Creator permissions',
                'Approve/reject content',
                'Publish directly',
                'View team analytics',
                'Manage strategic profiles',
              ]}
            />
            <RoleCard
              icon={FaShieldAlt}
              title="Admin"
              color="purple"
              description="Full access to all features including team and billing management."
              permissions={[
                'All Manager permissions',
                'Manage team members',
                'Invite new members',
                'Access billing & settings',
                'View all analytics',
              ]}
            />
          </SimpleGrid>
        </Box>

        <DocTip type="info">
          These predefined roles are designed to support the content approval workflow. Creators submit 
          content for review, Managers approve or reject it, and Admins have full control over the team.
        </DocTip>
      </DocSection>

      {/* Assigning Roles */}
      <DocSection id="assigning-roles" title="Assigning Roles">
        <DocParagraph>
          Once you have roles configured, you can assign them to team members. Role assignment 
          can happen during invitation or by updating existing members.
        </DocParagraph>

        <DocSubsection title="Assign During Invitation">
          <DocFeatureList
            items={[
              'When inviting a new member, select their role from the dropdown',
              'The invitee will have this role immediately upon accepting',
              'You can only assign roles with equal or fewer permissions than your own',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Change Existing Member's Role">
          <DocParagraph>
            To change a team member&apos;s role:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Go to Settings → Team',
              'Find the member in the list',
              'Click the role dropdown next to their name (Admin only)',
              'Select the new role',
              'The change takes effect immediately',
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          Role changes are logged in the audit log. You can review all role assignments and 
          changes in Settings → Roles → Audit Log.
        </DocTip>
      </DocSection>

      {/* Content Approval Workflow */}
      <DocSection id="approval-workflow" title="Content Approval Workflow">
        <DocParagraph>
          The content approval workflow ensures that content created by team members is reviewed 
          before publication. This is especially important for maintaining brand consistency and 
          compliance with regulations.
        </DocParagraph>

        <DocScreenshot pageId="approval-queue" caption="Content approval queue showing pending items for review" />

        <DocSubsection title="How It Works">
          <VStack spacing={4} align="stretch" mb={6}>
            <WorkflowStep 
              number={1} 
              title="Creator Submits Content" 
              description="A Creator writes content and clicks 'Submit for Approval'. The content enters the approval queue."
              icon={FaEdit}
            />
            <WorkflowStep 
              number={2} 
              title="Manager Reviews" 
              description="Managers see pending items in their approval queue. They can preview the full content and analysis scores."
              icon={FaUserCog}
            />
            <WorkflowStep 
              number={3} 
              title="Approve or Request Changes" 
              description="The Manager can approve (content moves to scheduled/published) or reject with feedback for the Creator."
              icon={FaClipboardCheck}
            />
            <WorkflowStep 
              number={4} 
              title="Creator Revises (if rejected)" 
              description="If rejected, the Creator receives feedback, makes changes, and resubmits for another review cycle."
              icon={FaEdit}
            />
          </VStack>
        </DocSubsection>

        <DocSubsection title="Approval Statuses">
          <DocFeatureList
            items={[
              'Pending Review - Awaiting manager review',
              'Approved - Ready for scheduling or immediate publication',
              'Rejected - Needs revision with feedback provided',
              'Published - Successfully posted to connected platforms',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Bypassing Approval">
          <DocParagraph>
            Users with the &quot;content.publish&quot; permission can bypass the approval workflow 
            and publish directly. This is typically reserved for Managers and Admins.
          </DocParagraph>
        </DocSubsection>

        <DocTip type="tip">
          For time-sensitive content, Managers can use the &quot;Quick Approve&quot; feature to batch-approve 
          multiple items from the same creator.
        </DocTip>
      </DocSection>

      {/* Best Practices */}
      <DocSection id="best-practices" title="Best Practices">
        <DocSubsection title="Role Design">
          <DocFeatureList
            items={[
              'Start with built-in roles and customize only when necessary',
              'Follow the principle of least privilege - grant only required permissions',
              'Use descriptive names and descriptions for custom roles',
              'Review role assignments quarterly to ensure they\'re still appropriate',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Team Organization">
          <DocFeatureList
            items={[
              'Assign at least two Admins to avoid single points of failure',
              'Use Managers as the primary content approvers to reduce Admin workload',
              'Group creators by project or brand using Strategic Profiles',
              'Set up email notifications for pending approvals',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Security">
          <DocFeatureList
            items={[
              'Regularly review the audit log for unusual permission changes',
              'Remove access immediately when team members leave',
              'Use strong invitation links that expire (auto-expires after 7 days)',
              'Enable 2FA for all Admin accounts',
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          Always maintain at least one Admin account with full access. If all Admins lose access, 
          contact support to restore account access.
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
