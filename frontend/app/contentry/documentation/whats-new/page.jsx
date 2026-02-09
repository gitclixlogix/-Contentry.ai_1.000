'use client';

/**
 * What's New - Living Changelog Page
 * 
 * Displays automatically detected UI changes with:
 * - AI-generated descriptions
 * - Screenshots of changed pages
 * - Deep links to the actual pages
 * - Timestamps showing when changes were detected
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Badge,
  Icon,
  Image,
  Button,
  Skeleton,
  Alert,
  AlertIcon,
  useColorModeValue,
  Divider,
  Flex,
  IconButton,
  Tooltip,
  Link as ChakraLink,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FaRocket,
  FaStar,
  FaHistory,
  FaExternalLinkAlt,
  FaSync,
  FaCalendarAlt,
  FaChevronLeft,
  FaBell,
  FaPlus,
  FaEdit,
} from 'react-icons/fa';
import Link from 'next/link';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

// Change type configurations
const CHANGE_TYPE_CONFIG = {
  new_page: {
    label: 'New Page',
    color: 'green',
    icon: FaPlus,
    description: 'A new page has been added',
  },
  major_change: {
    label: 'Major Update',
    color: 'blue',
    icon: FaRocket,
    description: 'Significant changes to an existing page',
  },
  feature: {
    label: 'New Feature',
    color: 'blue',
    icon: FaStar,
    description: 'A new feature has been added',
  },
  update: {
    label: 'Update',
    color: 'orange',
    icon: FaEdit,
    description: 'Updates to existing functionality',
  },
};

function ChangelogEntry({ entry, isLast, isEven }) {
  const [showScreenshot, setShowScreenshot] = useState(false);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const alternateBg = useColorModeValue('gray.50', 'gray.750');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const dividerColor = useColorModeValue('gray.300', 'gray.600');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const screenshotBg = useColorModeValue('gray.100', 'gray.900');
  
  const typeConfig = CHANGE_TYPE_CONFIG[entry.type] || CHANGE_TYPE_CONFIG.update;
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };
  
  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  return (
    <Box>
      <Card 
        bg={isEven ? alternateBg : cardBg} 
        borderWidth="1px" 
        borderColor={borderColor} 
        _hover={{ boxShadow: 'md', transform: 'translateY(-1px)' }}
        transition="all 0.2s"
      >
        <CardBody py={5}>
          <Flex direction={{ base: 'column', md: 'row' }} gap={4}>
            {/* Timeline indicator */}
            <VStack spacing={0} align="center" display={{ base: 'none', md: 'flex' }}>
              <Box
                w="44px"
                h="44px"
                borderRadius="full"
                bg={`${typeConfig.color}.100`}
                display="flex"
                alignItems="center"
                justifyContent="center"
                boxShadow="sm"
              >
                <Icon as={typeConfig.icon} color={`${typeConfig.color}.500`} boxSize={5} />
              </Box>
            </VStack>
            
            {/* Content */}
            <Box flex={1}>
              {/* Header */}
              <HStack justify="space-between" mb={2} flexWrap="wrap" gap={2}>
                <HStack spacing={2}>
                <Badge colorScheme={typeConfig.color} fontSize="xs" px={2}>
                  {typeConfig.label}
                </Badge>
                {entry.page_name && (
                  <Badge variant="outline" fontSize="xs">
                    {entry.page_name}
                  </Badge>
                )}
              </HStack>
              <HStack spacing={1} color={textColorSecondary} fontSize="sm">
                <Icon as={FaCalendarAlt} boxSize={3} />
                <Text>{formatDate(entry.detected_at)}</Text>
                <Text>at {formatTime(entry.detected_at)}</Text>
              </HStack>
            </HStack>
            
            {/* Description */}
            <Text color={textColor} fontSize="md" mb={3}>
              {entry.description}
            </Text>
            
            {/* Feature Details (for feature entries with details array) */}
            {entry.details && entry.details.length > 0 && (
              <VStack align="start" spacing={1} mb={3} pl={2}>
                {entry.details.map((detail, idx) => (
                  <HStack key={idx} spacing={2} align="start">
                    <Box w="6px" h="6px" borderRadius="full" bg={typeConfig.color + ".500"} mt={2} flexShrink={0} />
                    <Text fontSize="sm" color={textColorSecondary}>
                      {detail}
                    </Text>
                  </HStack>
                ))}
              </VStack>
            )}
            
            {/* Actions */}
            <HStack spacing={2}>
              {entry.page_path && (
                <Button
                  as={Link}
                  href={entry.page_path}
                  size="sm"
                  leftIcon={<FaExternalLinkAlt />}
                  colorScheme="brand"
                  variant="outline"
                >
                  {entry.is_external ? 'View Documentation' : 'View in App'}
                </Button>
              )}
              {entry.screenshot_data && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowScreenshot(!showScreenshot)}
                >
                  {showScreenshot ? 'Hide Screenshot' : 'Show Screenshot'}
                </Button>
              )}
            </HStack>
            
            {/* Screenshot (collapsible) */}
            {showScreenshot && entry.screenshot_data && (
              <Box
                mt={4}
                borderRadius="md"
                overflow="hidden"
                borderWidth="1px"
                borderColor={borderColor}
              >
                <Link href={entry.page_path || '#'} passHref legacyBehavior>
                  <ChakraLink _hover={{ opacity: 0.9 }}>
                    <Image
                      src={`data:image/png;base64,${entry.screenshot_data}`}
                      alt={`Screenshot of ${entry.page_name}`}
                      w="100%"
                      maxH="400px"
                      objectFit="contain"
                      bg={screenshotBg}
                    />
                  </ChakraLink>
                </Link>
              </Box>
            )}
          </Box>
        </Flex>
      </CardBody>
    </Card>
    {/* Visual separator between entries */}
    {!isLast && (
      <Divider 
        borderColor={dividerColor} 
        borderWidth="1px" 
        my={1}
        opacity={0.6}
      />
    )}
  </Box>
  );
}

export default function WhatsNewPage() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const loadChangelog = useCallback(async () => {
    try {
      setLoading(true);
      const API = getApiUrl();
      const response = await axios.get(`${API}/documentation/changelog`, {
        params: { page, limit: 20 }
      });
      setEntries(response.data.entries || []);
      setTotalPages(response.data.total_pages || 1);
      setError(null);
    } catch (err) {
      console.error('Failed to load changelog:', err);
      setError('Failed to load changelog entries');
    } finally {
      setLoading(false);
    }
  }, [page]);
  
  useEffect(() => {
    loadChangelog();
  }, [loadChangelog]);
  
  const handleScan = async () => {
    try {
      setScanning(true);
      const API = getApiUrl();
      await axios.post(`${API}/documentation/changelog/scan`);
      // Wait a bit and reload
      setTimeout(() => {
        loadChangelog();
        setScanning(false);
      }, 5000);
    } catch (err) {
      console.error('Failed to trigger scan:', err);
      setScanning(false);
    }
  };
  
  return (
    <Box>
      {/* Back Button */}
      <Button
        as={Link}
        href="/contentry/documentation"
        leftIcon={<FaChevronLeft />}
        variant="ghost"
        size="sm"
        mb={4}
      >
        {t('documentation.backToGuides', 'Back to All Guides')}
      </Button>
      
      {/* Header */}
      <Card bg={cardBg} mb={6}>
        <CardBody>
          <HStack justify="space-between" flexWrap="wrap" gap={4}>
            <HStack spacing={4}>
              <Box
                p={4}
                borderRadius="xl"
                bg={useColorModeValue('green.50', 'green.900')}
              >
                <Icon as={FaBell} fontSize="3xl" color="green.500" />
              </Box>
              <Box>
                <Heading size="lg" color={textColor}>
                  {t('documentation.whatsNew.title', "What's New")}
                </Heading>
                <Text color={textColorSecondary}>
                  {t('documentation.whatsNew.subtitle', 'Automatically detected changes and updates to the platform')}
                </Text>
              </Box>
            </HStack>
            <Tooltip label="Scan for new changes">
              <IconButton
                icon={<FaSync />}
                onClick={handleScan}
                isLoading={scanning}
                colorScheme="brand"
                aria-label="Scan for changes"
              />
            </Tooltip>
          </HStack>
        </CardBody>
      </Card>
      
      {/* Info Alert */}
      <Alert status="info" borderRadius="md" mb={6}>
        <AlertIcon />
        <Box>
          <Text fontWeight="500">Automatic Change Detection</Text>
          <Text fontSize="sm">
            This page is automatically updated when significant UI changes are detected. 
            All entries include AI-generated descriptions for clarity.
          </Text>
        </Box>
      </Alert>
      
      {/* Changelog Entries */}
      {loading ? (
        <VStack spacing={4}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height="150px" width="100%" borderRadius="lg" />
          ))}
        </VStack>
      ) : error ? (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          {error}
        </Alert>
      ) : entries.length === 0 ? (
        <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
          <CardBody textAlign="center" py={12}>
            <Icon as={FaHistory} boxSize={12} color="gray.400" mb={4} />
            <Heading size="md" color={textColor} mb={2}>
              No Changes Yet
            </Heading>
            <Text color={textColorSecondary} mb={4}>
              The changelog is automatically populated when UI changes are detected.
              Check back later or trigger a manual scan.
            </Text>
            <Button
              leftIcon={<FaSync />}
              colorScheme="brand"
              onClick={handleScan}
              isLoading={scanning}
            >
              Scan for Changes
            </Button>
          </CardBody>
        </Card>
      ) : (
        <VStack spacing={0} align="stretch">
          {entries.map((entry, index) => (
            <ChangelogEntry
              key={entry.id}
              entry={entry}
              isLast={index === entries.length - 1}
              isEven={index % 2 === 0}
            />
          ))}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <HStack justify="center" mt={4}>
              <Button
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                isDisabled={page === 1}
              >
                Previous
              </Button>
              <Text color={textColorSecondary} fontSize="sm">
                Page {page} of {totalPages}
              </Text>
              <Button
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                isDisabled={page === totalPages}
              >
                Next
              </Button>
            </HStack>
          )}
        </VStack>
      )}
    </Box>
  );
}
