'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Flex,
  VStack,
  HStack,
  useColorModeValue,
  Spinner,
  Icon,
  Badge,
  Button,
  Divider,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { FaTasks, FaExclamationTriangle, FaEdit, FaExternalLinkAlt, FaCheckCircle } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { createAuthenticatedAxios } from '@/lib/api';
import ExportButton from './ExportButton';
import { formatDistanceToNow } from 'date-fns';

export default function MyActionItemsWidget({ userId }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.700', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const brandColor = useColorModeValue('brand.500', 'brand.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const warningBg = useColorModeValue('orange.50', 'orange.900');

  useEffect(() => {
    fetchActionItems();
  }, [userId]);

  const fetchActionItems = async () => {
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      const response = await api.get('/dashboard/my-action-items', {
        headers: {
          'x-user-id': userId,
        },
      });

      setData(response.data);
    } catch (err) {
      console.error('Action items error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (drillDownUrl) => {
    if (drillDownUrl) {
      router.push(drillDownUrl);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      revisions_requested: { label: t('dashboard.myActionItems.revisionsRequested', 'Revisions Requested'), color: 'orange' },
      changes_requested: { label: t('dashboard.myActionItems.changesRequested', 'Changes Requested'), color: 'orange' },
      rejected: { label: t('dashboard.myActionItems.rejected', 'Rejected'), color: 'red' },
    };
    return statusConfig[status] || { label: status, color: 'gray' };
  };

  const actionItems = data?.action_items || [];

  return (
    <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaTasks} boxSize={5} color="orange.500" />
            <Box>
              <Heading size="md" color={textColor}>
                {t('dashboard.myActionItems.title', 'My Action Items')}
              </Heading>
              <Text fontSize="sm" color={textColorSecondary}>
                {t('dashboard.myActionItems.description', 'Posts requiring your attention')}
              </Text>
            </Box>
          </HStack>
          <HStack>
            {actionItems.length > 0 && (
              <Badge colorScheme="orange" borderRadius="full" px={2}>
                {actionItems.length}
              </Badge>
            )}
            <ExportButton widgetType="action-items" />
          </HStack>
        </Flex>
      </CardHeader>
      <CardBody>
        {loading ? (
          <Flex justify="center" py={6}>
            <Spinner size="lg" color="brand.500" />
          </Flex>
        ) : error ? (
          <Text color="red.500" textAlign="center" py={4}>{error}</Text>
        ) : (
          <VStack spacing={3} align="stretch">
            {actionItems.length === 0 ? (
              <Flex direction="column" align="center" py={6}>
                <Icon as={FaCheckCircle} boxSize={10} color="green.400" mb={3} />
                <Text color={textColorSecondary} fontWeight="500">
                  {t('dashboard.myActionItems.allCaughtUp', 'All caught up!')} 🎉
                </Text>
                <Text fontSize="sm" color={textColorSecondary}>
                  {t('dashboard.myActionItems.noPendingItems', 'No pending action items')}
                </Text>
              </Flex>
            ) : (
              <>
                {actionItems.slice(0, 5).map((item, index) => {
                  const status = getStatusBadge(item.status);
                  return (
                    <Box key={item.id}>
                      <Box
                        p={3}
                        borderRadius="lg"
                        bg={warningBg}
                        cursor="pointer"
                        _hover={{ transform: 'translateX(4px)', opacity: 0.9 }}
                        transition="all 0.2s"
                        onClick={() => handleItemClick(item.drill_down_url)}
                      >
                        <Flex justify="space-between" align="start" mb={2}>
                          <HStack>
                            <Icon as={FaExclamationTriangle} color="orange.500" />
                            <Text fontWeight="600" fontSize="sm" color={textColor} isTruncated maxW="200px">
                              {item.title}
                            </Text>
                          </HStack>
                          <Badge colorScheme={status.color} size="sm">
                            {status.label}
                          </Badge>
                        </Flex>

                        {item.feedback && (
                          <Text fontSize="xs" color={textColorSecondary} mb={2} noOfLines={2}>
                            <Text as="span" fontWeight="600">{t('dashboard.myActionItems.feedback', 'Feedback')}:</Text> {item.feedback}
                          </Text>
                        )}

                        <Flex justify="space-between" align="center">
                          <Text fontSize="xs" color={textColorSecondary}>
                            {item.requested_by && `By ${item.requested_by} • `}
                            {formatDate(item.requested_at)}
                          </Text>
                          <Button
                            size="xs"
                            colorScheme="orange"
                            leftIcon={<FaEdit />}
                            rightIcon={<FaExternalLinkAlt />}
                            variant="ghost"
                          >
                            {t('dashboard.myActionItems.edit', 'Edit')}
                          </Button>
                        </Flex>
                      </Box>
                      {index < actionItems.slice(0, 5).length - 1 && <Box h={2} />}
                    </Box>
                  );
                })}

                {actionItems.length > 5 && (
                  <Button
                    variant="outline"
                    size="sm"
                    colorScheme="orange"
                    onClick={() => router.push('/contentry/content-moderation?tab=posts&status=revisions_requested')}
                    alignSelf="center"
                  >
                    View all {actionItems.length} action items
                  </Button>
                )}
              </>
            )}
          </VStack>
        )}
      </CardBody>
    </Card>
  );
}
