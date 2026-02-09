'use client';
import { useTranslation } from 'react-i18next';
import { FaUserTie, FaGlobe, FaBullseye, FaUsers, FaShieldAlt, FaChartLine, FaEdit, FaCheckCircle, FaLightbulb } from 'react-icons/fa';
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

// Profile Field Card Component
function ProfileFieldCard({ icon, title, description, usedFor, example }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const exampleBg = useColorModeValue('blue.50', 'blue.900');
  
  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} shadow="sm">
      <CardBody>
        <VStack align="start" spacing={3}>
          <HStack spacing={3}>
            <Box p={2} borderRadius="lg" bg="brand.100">
              <Icon as={icon} boxSize={5} color="brand.500" />
            </Box>
            <Text fontWeight="bold" fontSize="lg">{title}</Text>
          </HStack>
          <Text fontSize="sm" color="gray.600">{description}</Text>
          <Divider />
          <Box>
            <Text fontWeight="600" fontSize="sm" color="brand.500" mb={1}>Used for:</Text>
            <Text fontSize="sm">{usedFor}</Text>
          </Box>
          {example && (
            <Box w="full" bg={exampleBg} p={3} borderRadius="md">
              <Text fontWeight="600" fontSize="xs" color="brand.600" mb={1}>Example:</Text>
              <Text fontSize="sm" fontStyle="italic">{example}</Text>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// How It's Used Card
function UsageCard({ title, description, icon, color }) {
  const cardBg = useColorModeValue('white', 'gray.700');
  
  return (
    <Card bg={cardBg} shadow="sm">
      <CardBody>
        <HStack spacing={4} align="start">
          <Box p={3} borderRadius="full" bg={`${color}.100`}>
            <Icon as={icon} boxSize={6} color={`${color}.500`} />
          </Box>
          <VStack align="start" spacing={1}>
            <Text fontWeight="bold">{title}</Text>
            <Text fontSize="sm" color="gray.600">{description}</Text>
          </VStack>
        </HStack>
      </CardBody>
    </Card>
  );
}

export default function ProfilesGuide() {
  const { t } = useTranslation();

  const sections = [
    { id: 'overview', title: 'Overview' },
    { id: 'what-is-profile', title: 'What is a Strategic Profile?' },
    { id: 'setting-up', title: 'Setting Up Your Profile' },
    { id: 'profile-fields', title: 'Profile Fields Explained' },
    { id: 'how-used-analysis', title: 'How Profiles Affect Analysis' },
    { id: 'how-used-generation', title: 'How Profiles Affect Content Generation' },
    { id: 'best-practices', title: 'Best Practices' },
  ];

  return (
    <DocumentationLayout
      title="Strategic Profiles Guide"
      description="Learn how to set up and use Strategic Profiles to ensure your content aligns with your brand, audience, and regional requirements"
      icon={FaUserTie}
      iconColor="blue"
      sections={sections}
    >
      {/* Overview */}
      <DocSection id="overview" title="Overview">
        {/* Interactive Tutorial */}
        <InteractiveTutorial
          tutorialId="strategic-profiles"
          steps={TUTORIAL_CONFIGS.strategicProfiles.steps}
          onComplete={() => console.log('Strategic Profiles tutorial completed')}
        />
        
        <DocParagraph>
          Strategic Profiles are the foundation of intelligent content analysis and generation in Contentry.ai. 
          They define who you are, who your audience is, and what regions you operate in - enabling the AI to 
          provide contextually relevant feedback and generate content that truly resonates with your target market.
        </DocParagraph>
        
        <DocFeatureList
          items={[
            'Define your brand voice, values, and communication style',
            'Specify target audience demographics and preferences',
            'Set regional and cultural compliance requirements',
            'Enable AI to provide personalized content recommendations',
            'Ensure consistency across all generated content',
          ]}
        />

        <DocTip type="info">
          Every piece of content you analyze or generate uses your Strategic Profile to provide 
          contextually relevant scores and suggestions. A well-configured profile dramatically 
          improves the quality of AI recommendations.
        </DocTip>
      </DocSection>

      {/* What is a Strategic Profile */}
      <DocSection id="what-is-profile" title="What is a Strategic Profile?">
        <DocParagraph>
          A Strategic Profile is a comprehensive description of your brand, audience, and operational context. 
          It acts as the &quot;lens&quot; through which the AI views and evaluates your content.
        </DocParagraph>

        <Box mb={6}>
          <Heading size="md" mb={4}>How Profiles Work</Heading>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            <UsageCard
              icon={FaEdit}
              title="You Define"
              description="Set up your brand identity, target audience, and regional focus in your profile settings."
              color="blue"
            />
            <UsageCard
              icon={FaChartLine}
              title="AI Analyzes"
              description="When analyzing content, the AI compares it against your profile requirements."
              color="green"
            />
            <UsageCard
              icon={FaCheckCircle}
              title="You Get Insights"
              description="Receive scores and recommendations tailored to your specific context."
              color="purple"
            />
          </SimpleGrid>
        </Box>

        <DocSubsection title="Without a Profile vs. With a Profile">
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              <Box>
                <Text fontWeight="bold">Without Profile</Text>
                <Text fontSize="sm">Generic analysis based on universal best practices. May miss industry-specific or regional nuances.</Text>
              </Box>
            </Alert>
            <Alert status="success" borderRadius="md">
              <AlertIcon />
              <Box>
                <Text fontWeight="bold">With Profile</Text>
                <Text fontSize="sm">Personalized analysis considering your brand voice, audience preferences, and regional compliance needs.</Text>
              </Box>
            </Alert>
          </SimpleGrid>
        </DocSubsection>
      </DocSection>

      {/* Setting Up Your Profile */}
      <DocSection id="setting-up" title="Setting Up Your Profile">
        <DocParagraph>
          You can create and manage Strategic Profiles from the Settings menu. Each profile can represent 
          a different brand, product line, or regional campaign.
        </DocParagraph>

        <DocScreenshot pageId="strategic-profile" caption="Strategic Profile configuration screen" />

        <DocSubsection title="Step-by-Step Setup">
          <DocFeatureList
            items={[
              'Navigate to Settings → Company Profile from the sidebar',
              'Click "Edit Profile" or "Create New Profile" if you have multiple brands',
              'Fill in your Company/Brand Information section',
              'Define your Target Audience characteristics',
              'Specify your Operating Regions and any restricted regions',
              'Add any compliance requirements or guidelines',
              'Save your profile - it will be used for all future analyses',
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          You can create multiple profiles if you manage different brands or regional campaigns. 
          Switch between profiles before analyzing content to get context-specific feedback.
        </DocTip>
      </DocSection>

      {/* Profile Fields Explained */}
      <DocSection id="profile-fields" title="Profile Fields Explained">
        <DocParagraph>
          Each field in your Strategic Profile serves a specific purpose in content analysis and generation. 
          Here&apos;s what each field does and why it matters:
        </DocParagraph>

        <Box mb={6}>
          <Heading size="md" mb={4}>Company/Brand Information</Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <ProfileFieldCard
              icon={FaUserTie}
              title="Company Name"
              description="Your official brand or company name"
              usedFor="Identifying your content in analyses and ensuring brand name consistency"
              example="Acme Corporation"
            />
            <ProfileFieldCard
              icon={FaLightbulb}
              title="Industry"
              description="Your primary business sector"
              usedFor="Applying industry-specific compliance rules and terminology standards"
              example="Financial Services, Healthcare, Technology"
            />
            <ProfileFieldCard
              icon={FaBullseye}
              title="Brand Voice"
              description="Your communication style and tone"
              usedFor="Evaluating if content matches your brand personality and generating content in your voice"
              example="Professional yet approachable, innovative, trustworthy"
            />
            <ProfileFieldCard
              icon={FaShieldAlt}
              title="Brand Values"
              description="Core principles your brand stands for"
              usedFor="Checking content alignment with your values and flagging potential conflicts"
              example="Sustainability, Innovation, Customer-first"
            />
          </SimpleGrid>
        </Box>

        <Box mb={6}>
          <Heading size="md" mb={4}>Target Audience</Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <ProfileFieldCard
              icon={FaUsers}
              title="Demographics"
              description="Age range, profession, and characteristics of your audience"
              usedFor="Adjusting language complexity, references, and cultural touchpoints"
              example="25-45 year old professionals, tech-savvy, urban"
            />
            <ProfileFieldCard
              icon={FaBullseye}
              title="Interests & Pain Points"
              description="What your audience cares about and their challenges"
              usedFor="Evaluating content relevance and engagement potential"
              example="Career growth, work-life balance, productivity tools"
            />
          </SimpleGrid>
        </Box>

        <Box mb={6}>
          <Heading size="md" mb={4}>Regional Settings</Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <ProfileFieldCard
              icon={FaGlobe}
              title="Operating Regions"
              description="Countries/regions where you actively market"
              usedFor="Applying regional compliance rules, cultural sensitivity checks, and language appropriateness"
              example="United States, United Kingdom, Germany, Japan"
            />
            <ProfileFieldCard
              icon={FaShieldAlt}
              title="Restricted Regions"
              description="Regions where your content should not be distributed"
              usedFor="Flagging content that might inadvertently target restricted markets"
              example="Sanctioned countries, regions with regulatory restrictions"
            />
          </SimpleGrid>
        </Box>
      </DocSection>

      {/* How Profiles Affect Analysis */}
      <DocSection id="how-used-analysis" title="How Profiles Affect Content Analysis">
        <DocParagraph>
          When you analyze content, your Strategic Profile directly influences multiple scoring dimensions:
        </DocParagraph>

        <Box mb={6}>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <Card>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Badge colorScheme="blue">Brand Alignment Score</Badge>
                  </HStack>
                  <Text fontSize="sm">
                    Compares your content&apos;s tone, language, and messaging against your defined Brand Voice and Values. 
                    Low scores indicate the content may not sound like your brand.
                  </Text>
                </VStack>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Badge colorScheme="green">Cultural Fit Score</Badge>
                  </HStack>
                  <Text fontSize="sm">
                    Evaluates if content is appropriate for your Operating Regions. Flags cultural sensitivities, 
                    inappropriate references, or language that may not translate well.
                  </Text>
                </VStack>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Badge colorScheme="purple">Audience Relevance Score</Badge>
                  </HStack>
                  <Text fontSize="sm">
                    Measures how well content speaks to your Target Audience. Considers language complexity, 
                    topic relevance, and engagement potential for your specific demographic.
                  </Text>
                </VStack>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Badge colorScheme="red">Compliance Score</Badge>
                  </HStack>
                  <Text fontSize="sm">
                    Checks content against industry-specific regulations based on your Industry setting. 
                    Financial services, healthcare, and other regulated industries have stricter checks.
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>

        <DocTip type="warning">
          Without a configured profile, these scores will use generic benchmarks that may not reflect 
          your actual brand requirements. Always set up your profile before relying on analysis scores.
        </DocTip>
      </DocSection>

      {/* How Profiles Affect Generation */}
      <DocSection id="how-used-generation" title="How Profiles Affect Content Generation">
        <DocParagraph>
          When generating content, your Strategic Profile shapes the AI&apos;s output:
        </DocParagraph>

        <DocFeatureList
          items={[
            'Brand Voice → The AI writes in your defined tone and style',
            'Target Audience → Language complexity and references are adjusted for your audience',
            'Industry → Technical terminology and compliance language are incorporated',
            'Operating Regions → Content avoids culturally inappropriate references for your markets',
            'Brand Values → Generated content reinforces your core principles',
          ]}
        />

        <DocSubsection title="Example: Same Prompt, Different Profiles">
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <Card>
              <CardBody>
                <Text fontWeight="bold" mb={2} color="blue.500">Tech Startup Profile</Text>
                <Text fontSize="sm" fontStyle="italic" mb={2}>Prompt: &quot;Announce our new feature&quot;</Text>
                <Text fontSize="sm">
                  &quot;🚀 Big news! We just shipped something awesome - our new AI dashboard is live! 
                  It&apos;s fast, it&apos;s smart, and it&apos;s going to change how you work. Try it now!&quot;
                </Text>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Text fontWeight="bold" mb={2} color="purple.500">Enterprise Bank Profile</Text>
                <Text fontSize="sm" fontStyle="italic" mb={2}>Prompt: &quot;Announce our new feature&quot;</Text>
                <Text fontSize="sm">
                  &quot;We are pleased to announce the launch of our enhanced Analytics Dashboard. 
                  This secure, compliant solution provides comprehensive insights for informed decision-making.&quot;
                </Text>
              </CardBody>
            </Card>
          </SimpleGrid>
        </DocSubsection>
      </DocSection>

      {/* Best Practices */}
      <DocSection id="best-practices" title="Best Practices">
        <DocSubsection title="Profile Setup">
          <DocFeatureList
            items={[
              'Be specific with your Brand Voice - vague descriptions lead to generic outputs',
              'List actual customer demographics, not aspirational ones',
              'Include all regions you actively target, even smaller markets',
              'Update your profile when your brand positioning changes',
            ]}
          />
        </DocSubsection>

        <DocSubsection title="Using Multiple Profiles">
          <DocFeatureList
            items={[
              'Create separate profiles for distinct brands or product lines',
              'Use regional profiles for market-specific campaigns',
              'Switch profiles before analyzing/generating content for different contexts',
              'Regularly review and update profiles as your business evolves',
            ]}
          />
        </DocSubsection>

        <DocTip type="tip">
          The more detailed your Strategic Profile, the more accurate and useful your content 
          analysis and generation will be. Take time to fill in all fields thoughtfully.
        </DocTip>
      </DocSection>
    </DocumentationLayout>
  );
}
