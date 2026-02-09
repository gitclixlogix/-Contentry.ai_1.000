'use client';
import { useEffect, useState } from 'react';
import {
  Box,
  Flex,
  Text,
  useColorModeValue,
  Alert,
  AlertIcon,
  Button,
  Icon,
  VStack,
  HStack,
  Badge,
} from '@chakra-ui/react';
import { FaArrowLeft, FaBook, FaBuilding } from 'react-icons/fa';
import Card from '@/components/card/Card';
import KnowledgeBase from '@/components/settings/KnowledgeBase';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function CompanyKnowledgeSettingsPage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  
  // Theme colors
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColorPrimary = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  
  useEffect(() => {
    loadUser();
  }, []);
  
  const loadUser = async () => {
    try {
      // First try localStorage for enterprise user info
      const storedUser = localStorage.getItem('contentry_user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        
        // Check if user has admin access
        const isAdmin = userData.enterprise_role === 'enterprise_admin' || 
                       userData.role === 'admin' || 
                       userData.role === 'manager' ||
                       userData.role === 'owner';
        
        if (!isAdmin) {
          router.push('/contentry/dashboard');
          return;
        }
        
        setUser(userData);
        setLoading(false);
        return;
      }
      
      // Fallback to API
      const response = await api.get('/auth/me');
      if (response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <Flex justify="center" align="center" minH="50vh">
        <Text>Loading...</Text>
      </Flex>
    );
  }
  
  const isAdmin = user?.enterprise_role === 'enterprise_admin' || 
                  user?.role === 'admin' || 
                  user?.role === 'manager' ||
                  user?.role === 'owner';
  
  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      {/* Back button */}
      <Button
        leftIcon={<Icon as={FaArrowLeft} />}
        variant="ghost"
        mb={4}
        onClick={() => router.push('/contentry/enterprise/settings/company')}
        data-testid="back-to-company-settings"
      >
        Back to Company Settings
      </Button>
      
      <Box maxW="900px" mx="auto">
        {/* Header */}
        <Flex align="center" gap={3} mb={6}>
          <Box p={2} bg="purple.100" borderRadius="md">
            <Icon as={FaBuilding} boxSize={6} color="purple.600" />
          </Box>
          <Box>
            <Text fontSize="2xl" fontWeight="bold" color={textColorPrimary} data-testid="page-title">
              Company Knowledge Base
            </Text>
            <Text color={textColorSecondary}>
              Manage company-wide knowledge that applies to all team members.
            </Text>
          </Box>
        </Flex>
        
        {/* Info Alert */}
        <Alert status="info" mb={6} borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="600">Company-Wide Knowledge</Text>
            <Text fontSize="sm">
              Knowledge entries added here will be automatically applied when generating or analyzing content 
              for all team members in your organization. Use this for brand guidelines, terminology preferences, 
              and company-specific rules.
            </Text>
          </Box>
        </Alert>
        
        {/* Difference from Documents Alert */}
        <Alert status="warning" mb={6} borderRadius="md" variant="left-accent">
          <AlertIcon />
          <Box>
            <HStack mb={1}>
              <Text fontWeight="600">Different from Policy Documents</Text>
              <Badge colorScheme="purple" fontSize="xs">Text-Based</Badge>
            </HStack>
            <Text fontSize="sm">
              This Knowledge Base is for quick, text-based rules and preferences. For comprehensive 
              policy documents (PDFs, DOCXs), use the{' '}
              <Text as="span" color="blue.500" cursor="pointer" fontWeight="600" 
                onClick={() => router.push('/contentry/enterprise/settings/company')}>
                Company Profile → Policy Documents
              </Text>{' '}
              section instead.
            </Text>
          </Box>
        </Alert>
        
        {/* Company Knowledge Base Component */}
        <Card p={6} bg={cardBg} mb={6} data-testid="company-knowledge-card">
          <KnowledgeBase
            scope="company"
            userId={user?.id}
            isAdmin={isAdmin}
            cardBg={cardBg}
            textColorPrimary={textColorPrimary}
            textColorSecondary={textColorSecondary}
          />
        </Card>
        
        {/* Usage Examples */}
        <Card p={6} bg={cardBg}>
          <Text fontWeight="600" color={textColorPrimary} mb={4}>
            <Icon as={FaBook} mr={2} color="purple.500" />
            Example Knowledge Entries
          </Text>
          <VStack align="stretch" spacing={3}>
            <Box p={3} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
              <Text fontWeight="600" fontSize="sm" color="purple.600">Brand Terminology</Text>
              <Text fontSize="sm" color={textColorSecondary}>
                "Always refer to our product as 'TechCorp Suite' not 'TechCorp software'. Use 'team members' instead of 'employees'."
              </Text>
            </Box>
            <Box p={3} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
              <Text fontWeight="600" fontSize="sm" color="purple.600">Tone of Voice</Text>
              <Text fontSize="sm" color={textColorSecondary}>
                "Our brand voice is professional yet approachable. Avoid jargon. Use active voice. Keep sentences concise."
              </Text>
            </Box>
            <Box p={3} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
              <Text fontWeight="600" fontSize="sm" color="purple.600">Compliance Rule</Text>
              <Text fontSize="sm" color={textColorSecondary}>
                "All financial claims must include the disclaimer: 'Past performance is not indicative of future results.'"
              </Text>
            </Box>
          </VStack>
        </Card>
      </Box>
    </Box>
  );
}
