'use client';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  VStack,
  HStack,
  Icon,
  useColorModeValue,
  Button,
  Badge,
} from '@chakra-ui/react';
import { FaUserShield, FaBuilding, FaUser, FaArrowRight, FaBook, FaLightbulb, FaClipboardList, FaBell, FaUsers, FaUserTie, FaShareAlt } from 'react-icons/fa';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function DocumentationHub() {
  const { t } = useTranslation();
  const { user } = useAuth();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  
  // Colors for guide cards
  const blueBg = useColorModeValue('blue.50', 'blue.900');
  const greenBg = useColorModeValue('green.50', 'green.900');
  const orangeBg = useColorModeValue('orange.50', 'orange.900');
  const tealBg = useColorModeValue('teal.50', 'teal.900');
  const purpleBg = useColorModeValue('purple.50', 'purple.900');
  const pinkBg = useColorModeValue('pink.50', 'pink.900');
  const cyanBg = useColorModeValue('cyan.50', 'cyan.900');
  
  // Check user roles
  const isAdmin = user?.role === 'admin';
  const isEnterprise = user?.role === 'enterprise_admin' || user?.enterprise_id;

  const allGuides = [
    {
      id: 'whats-new',
      icon: FaBell,
      color: 'pink.500',
      bgColor: pinkBg,
      title: t('documentation.whatsNew.title', "What's New"),
      description: t('documentation.whatsNew.description', 'Automatically detected updates and new features'),
      features: [
        t('documentation.whatsNew.feature1', 'Auto-detected UI changes'),
        t('documentation.whatsNew.feature2', 'AI-generated descriptions'),
        t('documentation.whatsNew.feature3', 'Interactive screenshots'),
        t('documentation.whatsNew.feature4', 'Historical changelog'),
      ],
      href: '/contentry/documentation/whats-new',
      requiredRole: null, // Available to all
      isHighlighted: true, // Special styling for What's New
    },
    {
      id: 'about',
      icon: FaLightbulb,
      color: 'orange.500',
      bgColor: orangeBg,
      title: t('documentation.aboutGuide.title'),
      description: t('documentation.aboutGuide.description'),
      features: [
        t('documentation.aboutGuide.feature1'),
        t('documentation.aboutGuide.feature2'),
        t('documentation.aboutGuide.feature3'),
        t('documentation.aboutGuide.feature4'),
      ],
      href: '/contentry/documentation/about',
      requiredRole: null, // Available to all
    },
    {
      id: 'workflows',
      icon: FaClipboardList,
      color: 'teal.500',
      bgColor: tealBg,
      title: t('documentation.workflowsGuide.title'),
      description: t('documentation.workflowsGuide.description'),
      features: [
        t('documentation.workflowsGuide.feature1'),
        t('documentation.workflowsGuide.feature2'),
        t('documentation.workflowsGuide.feature3'),
        t('documentation.workflowsGuide.feature4'),
      ],
      href: '/contentry/documentation/workflows',
      requiredRole: null, // Available to all
    },
    {
      id: 'workspaces',
      icon: FaBuilding,
      color: 'purple.500',
      bgColor: purpleBg,
      title: 'Workspaces Guide',
      description: 'Learn how to switch between Personal and Company workspaces to manage content effectively',
      features: [
        'Personal vs Company workspace',
        'Switching between workspaces',
        'Workspace-specific features',
        'Admin-only company settings',
      ],
      href: '/contentry/documentation/workspaces',
      requiredRole: null, // Available to all
      isNew: true, // Highlight as new feature
    },
    {
      id: 'teams',
      icon: FaUsers,
      color: 'purple.500',
      bgColor: purpleBg,
      title: 'Teams & Roles',
      description: 'Manage your team, create custom roles, and set up content approval workflows',
      features: [
        'Invite and manage team members',
        'Assign roles to team members',
        'Set up content approval workflows',
        'Best practices for team organization',
      ],
      href: '/contentry/documentation/teams',
      requiredRole: null, // Available to all
    },
    {
      id: 'profiles',
      icon: FaUserTie,
      color: 'blue.500',
      bgColor: blueBg,
      title: 'Strategic Profiles',
      description: 'Learn how to set up and use Strategic Profiles for personalized content analysis',
      features: [
        'Define your brand voice and values',
        'Configure target audience settings',
        'Set regional compliance requirements',
        'Understand how profiles affect scoring',
      ],
      href: '/contentry/documentation/profiles',
      requiredRole: null, // Available to all
    },
    {
      id: 'approval',
      icon: FaClipboardList,
      color: 'green.500',
      bgColor: greenBg,
      title: 'Approval Workflow',
      description: 'Master the content approval process for quality control and compliance',
      features: [
        'Submit content for review',
        'Approve or reject as a manager',
        'Manage the approval queue',
        'Handle scheduled content approvals',
      ],
      href: '/contentry/documentation/approval',
      requiredRole: null, // Available to all
    },
    {
      id: 'social',
      icon: FaShareAlt,
      color: 'cyan.500',
      bgColor: cyanBg,
      title: 'Social Accounts',
      description: 'Connect and manage your social media accounts for seamless publishing',
      features: [
        'Connect Twitter, LinkedIn, Facebook',
        'Direct publishing and scheduling',
        'Platform-specific optimization',
        'Security and permissions',
      ],
      href: '/contentry/documentation/social',
      requiredRole: null, // Available to all
    },
    {
      id: 'admin',
      icon: FaUserShield,
      color: 'blue.500',
      bgColor: blueBg,
      title: t('documentation.adminGuide.title'),
      description: t('documentation.adminGuide.description'),
      features: [
        t('documentation.adminGuide.feature1'),
        t('documentation.adminGuide.feature2'),
        t('documentation.adminGuide.feature3'),
        t('documentation.adminGuide.feature4'),
      ],
      href: '/contentry/documentation/admin',
      requiredRole: 'admin', // Admin only
    },
    {
      id: 'enterprise',
      icon: FaBuilding,
      color: 'blue.500',
      bgColor: blueBg,
      title: t('documentation.enterpriseGuide.title'),
      description: t('documentation.enterpriseGuide.description'),
      features: [
        t('documentation.enterpriseGuide.feature1'),
        t('documentation.enterpriseGuide.feature2'),
        t('documentation.enterpriseGuide.feature3'),
        t('documentation.enterpriseGuide.feature4'),
      ],
      href: '/contentry/documentation/enterprise',
      requiredRole: 'enterprise', // Enterprise only
    },
    {
      id: 'user',
      icon: FaUser,
      color: 'green.500',
      bgColor: greenBg,
      title: t('documentation.userGuide.title'),
      description: t('documentation.userGuide.description'),
      features: [
        t('documentation.userGuide.feature1'),
        t('documentation.userGuide.feature2'),
        t('documentation.userGuide.feature3'),
        t('documentation.userGuide.feature4'),
      ],
      href: '/contentry/documentation/user',
      requiredRole: null, // Available to all
    },
  ];
  
  // Filter guides based on user role
  const guides = allGuides.filter(guide => {
    if (guide.requiredRole === null) return true; // Available to all
    if (guide.requiredRole === 'admin' && isAdmin) return true;
    if (guide.requiredRole === 'enterprise' && isEnterprise) return true;
    return false;
  });

  return (
    <Box>
      {/* Header */}
      <VStack spacing={4} mb={10} textAlign="center">
        <HStack>
          <Icon as={FaBook} fontSize="3xl" color={brandColor} />
          <Heading size="xl" color={textColor}>
            {t('documentation.title')}
          </Heading>
        </HStack>
        <Text fontSize="lg" color={textColorSecondary} maxW="600px">
          {t('documentation.subtitle')}
        </Text>
      </VStack>

      {/* Guide Cards */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
        {guides.map((guide) => (
          <Link href={guide.href} key={guide.id} style={{ textDecoration: 'none' }}>
            <Card
              bg={cardBg}
              borderWidth="1px"
              borderColor="transparent"
              _hover={{
                borderColor: guide.color,
                transform: 'translateY(-4px)',
                shadow: 'lg',
              }}
              transition="all 0.2s"
              cursor="pointer"
              h="full"
            >
              <CardBody>
                <VStack align="start" spacing={4}>
                  {/* Icon */}
                  <Box
                    p={3}
                    borderRadius="lg"
                    bg={guide.bgColor}
                  >
                    <Icon as={guide.icon} fontSize="2xl" color={guide.color} />
                  </Box>

                  {/* Title & Description */}
                  <Box>
                    <HStack mb={2}>
                      <Heading size="md" color={textColor}>
                        {guide.title}
                      </Heading>
                      {guide.isNew && (
                        <Badge colorScheme="green" fontSize="2xs">NEW</Badge>
                      )}
                      {guide.isHighlighted && (
                        <Badge colorScheme="pink" fontSize="2xs">FEATURED</Badge>
                      )}
                    </HStack>
                    <Text fontSize="sm" color={textColorSecondary}>
                      {guide.description}
                    </Text>
                  </Box>

                  {/* Features */}
                  <VStack align="start" spacing={2} w="full">
                    {guide.features.map((feature, idx) => (
                      <HStack key={idx} spacing={2}>
                        <Box w="6px" h="6px" borderRadius="full" bg={guide.color} />
                        <Text fontSize="sm" color={textColorSecondary}>
                          {feature}
                        </Text>
                      </HStack>
                    ))}
                  </VStack>

                  {/* CTA */}
                  <HStack color={guide.color} fontWeight="600" fontSize="sm">
                    <Text>{t('documentation.readGuide')}</Text>
                    <Icon as={FaArrowRight} />
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </Link>
        ))}
      </SimpleGrid>
    </Box>
  );
}
