'use client';
import { useTranslation } from 'react-i18next';
import { FaShareAlt, FaTwitter, FaLinkedin, FaFacebook, FaInstagram, FaLink, FaUnlink, FaShieldAlt, FaCalendarAlt, FaChartLine, FaCog } from 'react-icons/fa';
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

// Platform Card Component
function PlatformCard({ icon, name, color, features, limitations }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} shadow="sm">
      <CardBody>
        <VStack align="start" spacing={3}>
          <HStack spacing={3}>
            <Box p={2} borderRadius="lg" bg={`${color}.100`}>
              <Icon as={icon} boxSize={6} color={`${color}.500`} />
            </Box>
            <Text fontWeight="bold" fontSize="lg">{name}</Text>
          </HStack>
          <Divider />
          <Box>
            <Text fontWeight="600" fontSize="sm" color="green.500" mb={1}>Features:</Text>
            <VStack align="start" spacing={1}>
              {features.map((feature, idx) => (
                <HStack key={idx} spacing={2}>
                  <Icon as={FaLink} color="green.400" boxSize={3} />
                  <Text fontSize="sm">{feature}</Text>
                </HStack>
              ))}
            </VStack>
          </Box>
          {limitations && limitations.length > 0 && (
            <Box>
              <Text fontWeight="600" fontSize="sm" color="orange.500" mb={1}>Limitations:</Text>
              <VStack align="start" spacing={1}>
                {limitations.map((limit, idx) => (
                  <Text key={idx} fontSize="sm" color="gray.500">• {limit}</Text>
                ))}
              </VStack>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// Connection Step Component
function ConnectionStep({ number, title, description }) {
  const bgColor = useColorModeValue('blue.50', 'blue.900');
  
  return (
    <HStack align="start" spacing={4} p={4} bg={bgColor} borderRadius="lg">
      <Box
        w="32px"
        h="32px"
        borderRadius="full"
        bg="blue.500"
        color="white"
        display="flex"
        alignItems="center"
        justifyContent="center"
        fontWeight="bold"
        fontSize="md"
        flexShrink={0}
      >
        {number}
      </Box>
      <VStack align="start" spacing={1}>
        <Text fontWeight="600">{title}</Text>
        <Text fontSize="sm" color="gray.600">{description}</Text>
      </VStack>
    </HStack>
  );
}

export default function SocialGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'overview', title: 'Overview' },
    { id: 'why-connect', title: 'Why Connect Social Accounts?' },
    { id: 'supported-platforms', title: 'Supported Platforms' },
    { id: 'connecting-accounts', title: 'Connecting Your Accounts' },
    { id: 'permissions', title: 'Permissions & Security' },
    { id: 'using-connected', title: 'Using Connected Accounts' },
    { id: 'managing-accounts', title: 'Managing Connected Accounts' },
    { id: 'troubleshooting', title: 'Troubleshooting' },
  ];

  return (
    <DocumentationLayout
      title="Social Accounts Guide"
      description="Learn how to connect and manage your social media accounts for seamless content publishing"
      icon={FaShareAlt}
      iconColor="cyan"
      sections={sections}
    >
      {/* Overview */}
      <DocSection id="overview" title="Overview">
        {/* Interactive Tutorial */}
        <InteractiveTutorial
          tutorialId="social-accounts"
          steps={TUTORIAL_CONFIGS.socialAccounts.steps}
          onComplete={() => console.log('Social Accounts tutorial completed')}
        />
        
        <DocParagraph>
          Connecting your social media accounts to Contentry.ai enables you to publish and schedule content 
          directly to your platforms without leaving the application. This integration streamlines your 
          workflow and ensures consistent content distribution across all your channels.
        </DocParagraph>
        
        <DocFeatureList
          items={[
            'Direct publishing to connected social platforms',
            'Schedule posts for optimal engagement times',
            'Preview how content will appear on each platform',
            'Track engagement metrics in one dashboard',
            'Secure OAuth-based authentication',
          ]}
        />

        <DocTip type="info">
          Social account connections are personal to your user account. Team members each need to 
          connect their own accounts, or use shared brand accounts with appropriate permissions.
        </DocTip>
      </DocSection>

      {/* Why Connect */}
      <DocSection id="why-connect" title="Why Connect Social Accounts?">
        <DocParagraph>
          While you can use Contentry.ai purely for content analysis and generation, connecting your 
          social accounts unlocks several powerful features:
        </DocParagraph>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaCalendarAlt} color="blue.500" />
                  <Text fontWeight="bold">Direct Publishing</Text>
                </HStack>
                <Text fontSize="sm">
                  Publish approved content directly to your social platforms with one click. 
                  No need to copy-paste or switch between apps.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaCalendarAlt} color="green.500" />
                  <Text fontWeight="bold">Smart Scheduling</Text>
                </HStack>
                <Text fontSize="sm">
                  Schedule posts for future publication. Set specific times or let AI suggest 
                  optimal posting times based on your audience.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaChartLine} color="purple.500" />
                  <Text fontWeight="bold">Performance Tracking</Text>
                </HStack>
                <Text fontSize="sm">
                  See engagement metrics for published content directly in Contentry.ai. 
                  Track what works across all your platforms.
                </Text>
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaCog} color="orange.500" />
                  <Text fontWeight="bold">Platform-Specific Optimization</Text>
                </HStack>
                <Text fontSize="sm">
                  Content analysis considers each platform&apos;s best practices. Get tailored 
                  suggestions for character limits, hashtags, and formatting.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Not Required for Analysis</Text>
            <Text fontSize="sm">
              You can still analyze and generate content without connecting social accounts. 
              Connection is only required for direct publishing and scheduling features.
            </Text>
          </Box>
        </Alert>
      </DocSection>

      {/* Supported Platforms */}
      <DocSection id="supported-platforms" title="Supported Platforms">
        <DocParagraph>
          Contentry.ai currently supports the following social media platforms. Each platform has 
          specific features and some limitations based on their API capabilities.
        </DocParagraph>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
          <PlatformCard
            icon={FaTwitter}
            name="X (Twitter)"
            color="blue"
            features={[
              'Post tweets and threads',
              'Schedule tweets',
              'Image and video attachments',
              'Track engagement metrics',
            ]}
            limitations={[
              '280 character limit per tweet',
              'Thread support up to 25 tweets',
            ]}
          />
          <PlatformCard
            icon={FaLinkedin}
            name="LinkedIn"
            color="blue"
            features={[
              'Personal and Company pages',
              'Long-form articles',
              'Image carousels',
              'Schedule posts',
            ]}
            limitations={[
              '3000 character limit',
              'Video upload requires Business plan',
            ]}
          />
          <PlatformCard
            icon={FaFacebook}
            name="Facebook"
            color="blue"
            features={[
              'Pages and Groups posting',
              'Photo and video posts',
              'Schedule content',
              'Engagement tracking',
            ]}
            limitations={[
              'Personal profiles not supported',
              'Requires Page admin access',
            ]}
          />
          <PlatformCard
            icon={FaInstagram}
            name="Instagram"
            color="pink"
            features={[
              'Feed posts',
              'Carousel posts',
              'Schedule posts',
              'Caption suggestions',
            ]}
            limitations={[
              'Stories not supported via API',
              'Reels not supported via API',
              'Business/Creator account required',
            ]}
          />
        </SimpleGrid>

        <DocTip type="tip">
          For platforms with character limits, Contentry.ai will warn you during content creation 
          and suggest optimizations to fit within the limit.
        </DocTip>
      </DocSection>

      {/* Connecting Accounts */}
      <DocSection id="connecting-accounts" title="Connecting Your Accounts">
        <DocParagraph>
          Connecting a social account is a secure, one-time process using OAuth authentication. 
          This means you never share your password with Contentry.ai.
        </DocParagraph>

        <DocScreenshot pageId="social-accounts" caption="Social Accounts settings page" />

        <DocSubsection title="Step-by-Step Connection">
          <VStack spacing={3} align="stretch" mb={6}>
            <ConnectionStep 
              number={1} 
              title="Go to Settings → Social Accounts" 
              description="Navigate to your settings and select the Social Accounts section."
            />
            <ConnectionStep 
              number={2} 
              title="Click 'Connect' on Your Platform" 
              description="Find the platform you want to connect and click the Connect button."
            />
            <ConnectionStep 
              number={3} 
              title="Authorize in Pop-up Window" 
              description="A secure pop-up will open. Log into your social account and authorize Contentry.ai."
            />
            <ConnectionStep 
              number={4} 
              title="Select Pages/Profiles (if applicable)" 
              description="For platforms with multiple pages, select which ones to connect."
            />
            <ConnectionStep 
              number={5} 
              title="Connection Complete" 
              description="Your account is now connected and ready for publishing."
            />
          </VStack>
        </DocSubsection>

        <DocTip type="warning">
          Make sure pop-ups are enabled in your browser. The OAuth authorization flow 
          requires a pop-up window to complete securely.
        </DocTip>
      </DocSection>

      {/* Permissions & Security */}
      <DocSection id="permissions" title="Permissions & Security">
        <DocParagraph>
          We take security seriously. Here&apos;s what you need to know about how we handle your 
          social account connections:
        </DocParagraph>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mb={6}>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaShieldAlt} color="green.500" />
                  <Text fontWeight="bold">What We Can Do</Text>
                </HStack>
                <DocFeatureList
                  items={[
                    'Post content on your behalf',
                    'Read your posts and engagement metrics',
                    'Access page/profile information',
                    'Schedule content for future posting',
                  ]}
                />
              </VStack>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <Icon as={FaShieldAlt} color="red.500" />
                  <Text fontWeight="bold">What We Cannot Do</Text>
                </HStack>
                <DocFeatureList
                  items={[
                    'Access your password',
                    'Read your private messages',
                    'Access accounts you haven\'t authorized',
                    'Post without your explicit action',
                  ]}
                />
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        <DocSubsection title="Token Security">
          <DocFeatureList
            items={[
              'OAuth tokens are encrypted at rest',
              'Tokens are automatically refreshed to maintain connection',
              'You can revoke access at any time from Settings',
              'Revoking access immediately removes our ability to post',
            ]}
          />
        </DocSubsection>
      </DocSection>

      {/* Using Connected Accounts */}
      <DocSection id="using-connected" title="Using Connected Accounts">
        <DocParagraph>
          Once connected, you can use your social accounts throughout Contentry.ai:
        </DocParagraph>

        <DocSubsection title="In Content Generation">
          <DocFeatureList
            items={[
              'Select target platform(s) when generating content',
              'AI adjusts content length and format for each platform',
              'Get platform-specific optimization suggestions',
              'Preview how content will appear on each platform',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="In Publishing">
          <DocFeatureList
            items={[
              'Publish approved content to one or multiple platforms',
              'Schedule posts for specific dates and times',
              'Add platform-specific customizations (hashtags, mentions)',
              'Track publishing status and any errors',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="In Analytics">
          <DocFeatureList
            items={[
              'View engagement metrics for published content',
              'Compare performance across platforms',
              'Track best-performing content types',
              'Identify optimal posting times',
            ]}
          />
        </DocSubsection>
      </DocSection>

      {/* Managing Accounts */}
      <DocSection id="managing-accounts" title="Managing Connected Accounts">
        <DocParagraph>
          You have full control over your connected accounts at all times.
        </DocParagraph>

        <DocSubsection title="Disconnecting an Account">
          <DocFeatureList
            items={[
              'Go to Settings → Social Accounts',
              'Find the connected account',
              'Click "Disconnect" and confirm',
              'Scheduled posts for that account will be cancelled',
              'You can reconnect at any time',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Reconnecting After Password Change">
          <DocParagraph>
            If you change your password on a social platform, you may need to reconnect:
          </DocParagraph>
          <DocFeatureList
            items={[
              'Disconnect the existing connection',
              'Wait a few minutes for tokens to clear',
              'Reconnect following the standard process',
              'Re-authorize with your new credentials',
            ]}
          />
        </DocSubsection>

        <DocTip type="info">
          We recommend reviewing your connected accounts quarterly and disconnecting any 
          you no longer actively use.
        </DocTip>
      </DocSection>

      {/* Troubleshooting */}
      <DocSection id="troubleshooting" title="Troubleshooting">
        <DocSubsection title="Connection Failed">
          <DocFeatureList
            items={[
              'Ensure pop-ups are enabled in your browser',
              'Try a different browser if issues persist',
              'Check that you have admin access for pages/profiles',
              'Make sure your social account is in good standing',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Publishing Failed">
          <DocFeatureList
            items={[
              'Check if your connection is still active (may need reconnection)',
              'Verify content meets platform requirements (length, media)',
              'Ensure you have posting permissions for the selected page',
              'Check if the platform is experiencing outages',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Token Expired">
          <DocFeatureList
            items={[
              'Some platforms expire tokens periodically',
              'You\'ll see a "Reconnect Required" message',
              'Simply reconnect using the same process',
              'Your posting history and scheduled content are preserved',
            ]}
          />
        </DocSubsection>

        <DocTip type="warning">
          If you encounter persistent issues, try disconnecting completely, waiting 5 minutes, 
          then reconnecting. This clears any stale tokens.
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
