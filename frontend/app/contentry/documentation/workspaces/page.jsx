'use client';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  Badge,
  Icon,
  useColorModeValue,
  Divider,
  List,
  ListItem,
  ListIcon,
  Alert,
  AlertIcon,
  SimpleGrid,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
} from '@chakra-ui/react';
import { FaBuilding, FaUser, FaCheck, FaTimes, FaExchangeAlt, FaLock, FaUsers, FaChartBar, FaCog, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { Building2, User, ArrowLeftRight, Shield, Users, BarChart3, Settings } from 'lucide-react';
import Link from 'next/link';

export default function WorkspacesDocumentation() {
  const { t } = useTranslation();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const tableBg = useColorModeValue('gray.50', 'gray.700');
  const personalBg = useColorModeValue('blue.50', 'blue.900');
  const companyBg = useColorModeValue('purple.50', 'purple.900');
  const backButtonBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }} px={4}>
      {/* Back Button and Breadcrumb */}
      <HStack justify="space-between" align="center" mb={4} flexWrap="wrap" gap={2}>
        <Button
          as={Link}
          href="/contentry/documentation"
          leftIcon={<FaChevronLeft />}
          variant="ghost"
          size="sm"
          bg={backButtonBg}
          fontWeight="500"
        >
          Back to All Guides
        </Button>
        
        <Breadcrumb
          spacing="8px"
          separator={<FaChevronRight color="gray.500" size="10px" />}
        >
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} href="/contentry/documentation" color={textColorSecondary}>
              Documentation
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink color={textColor} fontWeight="600">
              Workspaces Guide
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </HStack>
      
      <Box maxW="4xl" mx="auto" py={4}>
        {/* Header */}
        <VStack align="start" spacing={4} mb={8}>
          <HStack spacing={3}>
            <Icon as={ArrowLeftRight} boxSize={8} color="brand.500" />
            <Heading size="xl" color={textColor}>
              Workspaces Guide
            </Heading>
            <Badge colorScheme="green">NEW</Badge>
          </HStack>
          <Text fontSize="lg" color={textColorSecondary}>
            Learn how to switch between Personal and Company workspaces to manage your content effectively.
          </Text>
        </VStack>

        {/* Overview Section */}
        <Card bg={cardBg} mb={8}>
          <CardBody>
            <Heading size="md" mb={4} color={textColor}>What are Workspaces?</Heading>
            <Text color={textColorSecondary} mb={4}>
              Workspaces allow you to separate your personal content from company/brand content. 
              When you switch workspaces, you'll see different content, settings, and analytics 
              relevant to that context.
            </Text>
            
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mt={6}>
              {/* Personal Workspace */}
              <Card bg={personalBg} variant="outline">
                <CardBody>
                  <HStack spacing={3} mb={3}>
                    <Icon as={User} boxSize={6} color="blue.500" />
                    <Heading size="sm" color={textColor}>Personal Workspace</Heading>
                  </HStack>
                  <List spacing={2}>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Your personal posts and drafts
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Personal social accounts
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Individual performance metrics
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Personal settings & preferences
                    </ListItem>
                  </List>
                </CardBody>
              </Card>

              {/* Company Workspace */}
              <Card bg={companyBg} variant="outline">
                <CardBody>
                  <HStack spacing={3} mb={3}>
                    <Icon as={Building2} boxSize={6} color="purple.500" />
                    <Heading size="sm" color={textColor}>Company Workspace</Heading>
                  </HStack>
                  <List spacing={2}>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Company brand content
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Official company social profiles
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Team-wide analytics
                    </ListItem>
                    <ListItem fontSize="sm" color={textColorSecondary}>
                      <ListIcon as={FaCheck} color="green.500" />
                      Company settings (Admin only)
                    </ListItem>
                  </List>
                </CardBody>
              </Card>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* How to Switch Workspaces */}
        <Card bg={cardBg} mb={8}>
          <CardBody>
            <Heading size="md" mb={4} color={textColor}>
              <HStack spacing={2}>
                <Icon as={FaExchangeAlt} color="brand.500" />
                <Text>How to Switch Workspaces</Text>
              </HStack>
            </Heading>
            
            <VStack align="start" spacing={4}>
              <Box>
                <Text fontWeight="600" color={textColor} mb={2}>Step 1: Locate the Workspace Switcher</Text>
                <Text color={textColorSecondary} fontSize="sm">
                  Find the workspace switcher in the top navigation bar. It displays your current workspace 
                  (e.g., "Company Workspace" or "Personal Workspace").
                </Text>
              </Box>
              
              <Box>
                <Text fontWeight="600" color={textColor} mb={2}>Step 2: Click to Open Options</Text>
                <Text color={textColorSecondary} fontSize="sm">
                  Click on the workspace name to open a dropdown menu showing available workspaces.
                </Text>
              </Box>
              
              <Box>
                <Text fontWeight="600" color={textColor} mb={2}>Step 3: Select Your Workspace</Text>
                <Text color={textColorSecondary} fontSize="sm">
                  Choose either "Personal Workspace" or "Company Workspace" (if you have enterprise access).
                  The page will automatically update to show content relevant to that workspace.
                </Text>
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* Feature Comparison Table */}
        <Card bg={cardBg} mb={8}>
          <CardBody>
            <Heading size="md" mb={4} color={textColor}>Feature Comparison</Heading>
            
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead bg={tableBg}>
                  <Tr>
                    <Th>Feature</Th>
                    <Th textAlign="center">
                      <HStack justify="center">
                        <Icon as={User} boxSize={4} color="blue.500" />
                        <Text>Personal</Text>
                      </HStack>
                    </Th>
                    <Th textAlign="center">
                      <HStack justify="center">
                        <Icon as={Building2} boxSize={4} color="purple.500" />
                        <Text>Company</Text>
                      </HStack>
                    </Th>
                  </Tr>
                </Thead>
                <Tbody>
                  <Tr>
                    <Td fontWeight="500">Posts & Content</Td>
                    <Td textAlign="center">Personal only</Td>
                    <Td textAlign="center">Company brand content</Td>
                  </Tr>
                  <Tr>
                    <Td fontWeight="500">Social Accounts</Td>
                    <Td textAlign="center">Personal profiles</Td>
                    <Td textAlign="center">Company profiles</Td>
                  </Tr>
                  <Tr>
                    <Td fontWeight="500">Analytics</Td>
                    <Td textAlign="center">Individual metrics</Td>
                    <Td textAlign="center">Company-wide metrics</Td>
                  </Tr>
                  <Tr>
                    <Td fontWeight="500">Settings Menu</Td>
                    <Td textAlign="center">
                      <Icon as={FaCheck} color="green.500" />
                    </Td>
                    <Td textAlign="center">
                      <Icon as={FaTimes} color="gray.400" />
                    </Td>
                  </Tr>
                  <Tr>
                    <Td fontWeight="500">Company Settings</Td>
                    <Td textAlign="center">
                      <Icon as={FaTimes} color="gray.400" />
                    </Td>
                    <Td textAlign="center">
                      <Badge colorScheme="purple" fontSize="2xs">Admin only</Badge>
                    </Td>
                  </Tr>
                  <Tr>
                    <Td fontWeight="500">Team Management</Td>
                    <Td textAlign="center">
                      <Icon as={FaTimes} color="gray.400" />
                    </Td>
                    <Td textAlign="center">
                      <Badge colorScheme="purple" fontSize="2xs">Admin only</Badge>
                    </Td>
                  </Tr>
                </Tbody>
              </Table>
            </Box>
          </CardBody>
        </Card>

        {/* Admin-Only Features */}
        <Card bg={cardBg} mb={8}>
          <CardBody>
            <Heading size="md" mb={4} color={textColor}>
              <HStack spacing={2}>
                <Icon as={Shield} color="purple.500" />
                <Text>Admin-Only Features (Company Workspace)</Text>
              </HStack>
            </Heading>
            
            <Alert status="info" mb={4} borderRadius="md">
              <AlertIcon />
              <Text fontSize="sm">
                The following features are only visible to users with the Admin role when in Company Workspace.
              </Text>
            </Alert>
            
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <HStack align="start" spacing={3}>
                <Icon as={Building2} boxSize={5} color="purple.500" />
                <Box>
                  <Text fontWeight="600" color={textColor}>Company Profile</Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    Manage company name, logo, address, and social profiles
                  </Text>
                </Box>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Icon as={Users} boxSize={5} color="purple.500" />
                <Box>
                  <Text fontWeight="600" color={textColor}>Team Management</Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    Add, remove, and manage team member roles
                  </Text>
                </Box>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Icon as={FaUsers} boxSize={5} color="purple.500" />
                <Box>
                  <Text fontWeight="600" color={textColor}>Users</Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    View and manage all users in your organization
                  </Text>
                </Box>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Icon as={BarChart3} boxSize={5} color="purple.500" />
                <Box>
                  <Text fontWeight="600" color={textColor}>Billing & Usage</Text>
                  <Text fontSize="sm" color={textColorSecondary}>
                    Monitor subscription and usage across the company
                  </Text>
                </Box>
              </HStack>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Best Practices */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="md" mb={4} color={textColor}>Best Practices</Heading>
            
            <VStack align="start" spacing={3}>
              <HStack align="start" spacing={3}>
                <Badge colorScheme="green" fontSize="xs">TIP</Badge>
                <Text fontSize="sm" color={textColorSecondary}>
                  Always check which workspace you're in before creating content to ensure it goes to the right place.
                </Text>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Badge colorScheme="green" fontSize="xs">TIP</Badge>
                <Text fontSize="sm" color={textColorSecondary}>
                  Use Company Workspace for official brand communications that need team review and approval.
                </Text>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Badge colorScheme="green" fontSize="xs">TIP</Badge>
                <Text fontSize="sm" color={textColorSecondary}>
                  Use Personal Workspace for drafts, experiments, or personal social media content.
                </Text>
              </HStack>
              
              <HStack align="start" spacing={3}>
                <Badge colorScheme="blue" fontSize="xs">NOTE</Badge>
                <Text fontSize="sm" color={textColorSecondary}>
                  Posts created in Company Workspace will show a purple "Company" badge in the posts list.
                </Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </Box>
    </Box>
  );
}
