'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
  useColorModeValue,
  Icon,
  Container,
} from '@chakra-ui/react';
import { FaLock } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';

export default function SubscriptionRequiredPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [user, setUser] = useState(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const userBoxBg = useColorModeValue('blue.50', 'blue.900');

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const pendingUser = localStorage.getItem('pending_user');
    if (pendingUser) {
      setUser(JSON.parse(pendingUser));
    }
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  return (
    <Flex minH="100vh" align="center" justify="center" bg={bgColor}>
      <Container maxW="600px">
        <Box
          bg={cardBg}
          boxShadow="xl"
          rounded="2xl"
          p={10}
          textAlign="center"
        >
          <VStack spacing={6}>
            <Icon as={FaLock} boxSize={16} color="orange.500" />
            
            <Heading size="xl" color={textColor}>
              {t('subscription.required.title')}
            </Heading>
            
            <Text fontSize="lg" color="gray.500">
              {t('subscription.required.subtitle')}
            </Text>

            {user && (
              <Box
                p={4}
                bg={userBoxBg}
                borderRadius="md"
                w="full"
              >
                <Text fontSize="sm" color={textColor}>
                  {t('auth.login.loggedInAs')}: <strong>{user.email}</strong>
                </Text>
              </Box>
            )}

            <VStack spacing={3} w="full" pt={4}>
              <Button
                colorScheme="brand"
                size="lg"
                w="full"
                onClick={() => router.push('/contentry/subscription/plans')}
              >
                {t('subscription.required.viewPlans')}
              </Button>
              
              <Button
                variant="ghost"
                size="lg"
                w="full"
                onClick={() => {
                  localStorage.removeItem('pending_user');
                  router.push('/contentry/auth/login');
                }}
              >
                {t('common.goBack')}
              </Button>
            </VStack>

            <Text fontSize="sm" color="gray.500" pt={4}>
              {t('subscription.required.selectPlan')}
            </Text>
          </VStack>
        </Box>
      </Container>
    </Flex>
  );
}
