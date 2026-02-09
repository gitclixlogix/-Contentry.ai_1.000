'use client';
import { useEffect, useState } from 'react';
import {
  Box,
  Flex,
  Text,
  useColorModeValue,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import Card from '@/components/card/Card';
import KnowledgeBase from '@/components/settings/KnowledgeBase';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function KnowledgeSettingsPage() {
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
      // First try localStorage for user info (faster)
      const storedUser = localStorage.getItem('contentry_user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
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
      router.push('/contentry/auth/login');
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
  
  return (
    <Box p={6} bg={bgColor} minH="100vh">
      <Box maxW="900px" mx="auto">
        {/* Header */}
        <Box mb={6}>
          <Text fontSize="2xl" fontWeight="bold" color={textColorPrimary} mb={2}>
            Knowledge Base
          </Text>
          <Text color={textColorSecondary}>
            Manage knowledge that gets automatically applied when generating or analyzing content.
          </Text>
        </Box>
        
        {/* Info Alert */}
        <Alert status="info" mb={6} borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="600">How it works</Text>
            <Text fontSize="sm">
              Knowledge entries are automatically injected into AI prompts for content generation and analysis.
              The AI learns from your feedback and suggests new knowledge based on patterns it detects.
            </Text>
          </Box>
        </Alert>
        
        {/* Personal Knowledge */}
        <Card p={6} bg={cardBg} mb={6}>
          <KnowledgeBase
            scope="personal"
            userId={user?.id}
            isAdmin={['admin', 'manager', 'owner'].includes(user?.role)}
            cardBg={cardBg}
            textColorPrimary={textColorPrimary}
            textColorSecondary={textColorSecondary}
          />
        </Card>
      </Box>
    </Box>
  );
}
