'use client';
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
import { FaTimesCircle } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';

export default function SubscriptionCancelPage() {
  const { t } = useTranslation();
  const router = useRouter();

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');

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
            <Icon as={FaTimesCircle} boxSize={16} color="orange.500" />
            
            <Heading size="xl" color={textColor}>
              {t('subscription.cancel.title')}
            </Heading>
            
            <Text fontSize="lg" color="gray.500">
              {t('subscription.cancel.subtitle')}
            </Text>

            <Text fontSize="md" color={textColor}>
              {t('subscription.cancel.keepBenefits')}
            </Text>

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
                onClick={() => router.push('/contentry/auth/login')}
              >
                {t('common.goBack')}
              </Button>
            </VStack>

            <Text fontSize="sm" color="gray.500" pt={4}>
              {t('common.contactSupport')}
            </Text>
          </VStack>
        </Box>
      </Container>
    </Flex>
  );
}
