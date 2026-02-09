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
} from '@chakra-ui/react';
import { FaTrophy, FaMedal, FaExternalLinkAlt, FaStar } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { createAuthenticatedAxios } from '@/lib/api';
import ExportButton from './ExportButton';

export default function MyPerformanceWidget({ userId }) {
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

  useEffect(() => {
    fetchMyTopPosts();
  }, [userId]);

  const fetchMyTopPosts = async () => {
    setLoading(true);
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      const response = await api.get('/dashboard/my-top-posts?limit=3', {
        headers: {
          'x-user-id': userId,
        },
      });

      setData(response.data);
    } catch (err) {
      console.error('My performance error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePostClick = (drillDownUrl) => {
    if (drillDownUrl) {
      router.push(drillDownUrl);
    }
  };

  const getMedalIcon = (index) => {
    const medals = [
      { icon: FaTrophy, color: 'gold' },
      { icon: FaMedal, color: 'silver' },
      { icon: FaMedal, color: '#CD7F32' }, // Bronze
    ];
    return medals[index] || medals[2];
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'green';
    if (score >= 80) return 'teal';
    if (score >= 70) return 'yellow';
    if (score >= 60) return 'orange';
    return 'red';
  };

  return (
    <Card bg={cardBg} boxShadow="lg" borderRadius="xl">
      <CardHeader pb={2}>
        <Flex justify="space-between" align="center">
          <HStack spacing={3}>
            <Icon as={FaStar} boxSize={5} color="yellow.500" />
            <Box>
              <Heading size="md" color={textColor}>
                {t('dashboard.myPerformance.title', 'My Performance')}
              </Heading>
              <Text fontSize="sm" color={textColorSecondary}>
                {t('dashboard.myPerformance.description', 'Your top 3 performing posts')}
              </Text>
            </Box>
          </HStack>
          <ExportButton widgetType="top-posts" />
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
            {(data?.top_posts || []).length === 0 ? (
              <Flex direction="column" align="center" py={6} color={textColorSecondary}>
                <Icon as={FaTrophy} boxSize={8} mb={2} opacity={0.5} />
                <Text>{t('dashboard.myPerformance.noPosts', 'No posts yet. Create your first post!')}</Text>
                <Button
                  size="sm"
                  colorScheme="brand"
                  mt={3}
                  onClick={() => router.push('/contentry/content-moderation?tab=generate')}
                >
                  {t('dashboard.myPerformance.createPost', 'Create Post')}
                </Button>
              </Flex>
            ) : (
              (data?.top_posts || []).map((post, index) => {
                const medal = getMedalIcon(index);
                return (
                  <Box key={post.id}>
                    <Flex
                      align="center"
                      p={3}
                      borderRadius="lg"
                      cursor="pointer"
                      _hover={{ bg: hoverBg, transform: 'translateX(4px)' }}
                      transition="all 0.2s"
                      onClick={() => handlePostClick(post.drill_down_url)}
                    >
                      {/* Medal */}
                      <Box mr={3}>
                        <Icon as={medal.icon} boxSize={6} color={medal.color} />
                      </Box>

                      {/* Post info */}
                      <Box flex={1} minW={0}>
                        <Text fontWeight="600" fontSize="sm" isTruncated color={textColor}>
                          {post.title}
                        </Text>
                        <HStack spacing={2} mt={1}>
                          {(post.platforms || []).slice(0, 2).map((platform) => (
                            <Badge key={platform} size="sm" variant="subtle" colorScheme="brand">
                              {platform}
                            </Badge>
                          ))}
                          {(post.platforms || []).length > 2 && (
                            <Badge size="sm" variant="subtle">
                              +{post.platforms.length - 2}
                            </Badge>
                          )}
                        </HStack>
                      </Box>

                      {/* Score */}
                      <HStack spacing={2}>
                        <Badge 
                          colorScheme={getScoreColor(post.score)} 
                          fontSize="md" 
                          px={3} 
                          py={1}
                          borderRadius="full"
                        >
                          {post.score}
                        </Badge>
                        <Icon as={FaExternalLinkAlt} boxSize={3} color="gray.400" />
                      </HStack>
                    </Flex>
                    {index < (data?.top_posts?.length || 0) - 1 && <Divider />}
                  </Box>
                );
              })
            )}

            {/* View all link */}
            {(data?.top_posts || []).length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                rightIcon={<FaExternalLinkAlt />}
                onClick={() => router.push('/contentry/content-moderation?tab=posts')}
                alignSelf="center"
              >
                View all {data?.total_posts || 0} posts
              </Button>
            )}
          </VStack>
        )}
      </CardBody>
    </Card>
  );
}
