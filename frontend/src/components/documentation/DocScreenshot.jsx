'use client';

/**
 * DocScreenshot - Interactive Documentation Screenshot Component
 * 
 * Displays documentation screenshots with:
 * - Clickable deep links to the actual application pages
 * - Loading states and fallback images
 * - Refresh capability
 * - Timestamp showing when captured
 * - Hover effects indicating interactivity
 * 
 * @param {string} pageId - The ID of the screenshot to display
 * @param {string} alt - Alt text for the image
 * @param {boolean} showCaption - Whether to show the screenshot caption
 * @param {boolean} enableDeepLink - Whether clicking opens the app page (default: true)
 * @param {string} size - Size variant: 'sm', 'md', 'lg', 'full' (default: 'md')
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Image,
  Text,
  Skeleton,
  VStack,
  HStack,
  Badge,
  Icon,
  Tooltip,
  Link as ChakraLink,
  useColorModeValue,
  IconButton,
} from '@chakra-ui/react';
import { FaExternalLinkAlt, FaSync, FaClock, FaImage } from 'react-icons/fa';
import Link from 'next/link';
import api from '@/lib/api';

// Size configurations
const SIZE_CONFIG = {
  sm: { maxW: '300px', maxH: '200px' },
  md: { maxW: '500px', maxH: '350px' },
  lg: { maxW: '800px', maxH: '500px' },
  full: { maxW: '100%', maxH: '600px' },
};

export function DocScreenshot({
  pageId,
  alt,
  showCaption = true,
  enableDeepLink = true,
  size = 'md',
  onLoad,
  onError,
}) {
  const [screenshot, setScreenshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  // Theme colors
  const bgColor = useColorModeValue('gray.100', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBorderColor = useColorModeValue('brand.400', 'brand.300');
  const captionBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const linkColor = useColorModeValue('brand.500', 'brand.300');

  // Fetch screenshot data
  useEffect(() => {
    const fetchScreenshot = async () => {
      if (!pageId) return;
      
      try {
        setLoading(true);
        const response = await api.get(
          `/documentation/screenshots/${pageId}`
        );
        setScreenshot(response.data);
        setError(null);
        onLoad?.(response.data);
      } catch (err) {
        console.error(`Failed to fetch screenshot ${pageId}:`, err);
        setError(err.message || 'Failed to load screenshot');
        onError?.(err);
      } finally {
        setLoading(false);
      }
    };

    fetchScreenshot();
  }, [pageId, onLoad, onError]);

  // Refresh screenshot
  const handleRefresh = async (e) => {
    e?.preventDefault();
    e?.stopPropagation();
    
    try {
      setRefreshing(true);
      await api.post(
        `/documentation/screenshots/refresh/${pageId}`
      );
      // Wait for capture and refetch
      setTimeout(async () => {
        const response = await api.get(
          `/documentation/screenshots/${pageId}`
        );
        setScreenshot(response.data);
        setRefreshing(false);
      }, 5000);
    } catch (err) {
      console.error(`Failed to refresh screenshot ${pageId}:`, err);
      setRefreshing(false);
    }
  };

  // Format timestamp
  const formatTimestamp = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get the app URL for deep linking
  const getAppUrl = () => {
    if (!screenshot?.path) return null;
    // Construct full URL - the path already includes /contentry prefix
    return screenshot.path;
  };

  const sizeConfig = SIZE_CONFIG[size] || SIZE_CONFIG.md;
  const appUrl = getAppUrl();

  // Loading state
  if (loading) {
    return (
      <VStack spacing={2} align="stretch" {...sizeConfig}>
        <Skeleton height="200px" borderRadius="md" />
        {showCaption && <Skeleton height="20px" width="60%" />}
      </VStack>
    );
  }

  // Error state
  if (error || !screenshot) {
    return (
      <Box
        p={8}
        bg={bgColor}
        borderRadius="md"
        textAlign="center"
        {...sizeConfig}
      >
        <Icon as={FaImage} boxSize={8} color="gray.400" mb={2} />
        <Text color={textColor} fontSize="sm">
          Screenshot not available
        </Text>
      </Box>
    );
  }

  // Image content
  const imageContent = (
    <Box
      position="relative"
      borderRadius="lg"
      overflow="hidden"
      borderWidth="2px"
      borderColor={isHovered && enableDeepLink ? hoverBorderColor : borderColor}
      transition="all 0.2s"
      cursor={enableDeepLink ? 'pointer' : 'default'}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      {...sizeConfig}
    >
      {/* Screenshot Image */}
      {screenshot.image_data ? (
        <Image
          src={`data:image/png;base64,${screenshot.image_data}`}
          alt={alt || screenshot.name || 'Documentation screenshot'}
          objectFit="contain"
          w="100%"
          h="auto"
          maxH={sizeConfig.maxH}
          bg={bgColor}
        />
      ) : (
        <Box
          h="200px"
          bg={bgColor}
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <VStack>
            <Icon as={FaClock} boxSize={6} color="gray.400" />
            <Text color={textColor} fontSize="sm">Capture pending...</Text>
          </VStack>
        </Box>
      )}

      {/* Hover Overlay with Deep Link indicator */}
      {enableDeepLink && isHovered && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="blackAlpha.500"
          display="flex"
          alignItems="center"
          justifyContent="center"
          transition="all 0.2s"
        >
          <VStack spacing={2}>
            <Icon as={FaExternalLinkAlt} boxSize={6} color="white" />
            <Text color="white" fontWeight="600" fontSize="sm">
              Click to open in app
            </Text>
          </VStack>
        </Box>
      )}

      {/* Refresh Button */}
      <Tooltip label="Refresh screenshot">
        <IconButton
          icon={<FaSync />}
          size="xs"
          position="absolute"
          top={2}
          right={2}
          colorScheme="gray"
          variant="solid"
          opacity={isHovered ? 1 : 0.6}
          isLoading={refreshing}
          onClick={handleRefresh}
          aria-label="Refresh screenshot"
        />
      </Tooltip>
    </Box>
  );

  return (
    <VStack spacing={2} align="stretch" maxW={sizeConfig.maxW}>
      {/* Wrap in Link if deep link enabled */}
      {enableDeepLink && appUrl ? (
        <Link href={appUrl} passHref legacyBehavior>
          <ChakraLink _hover={{ textDecoration: 'none' }}>
            {imageContent}
          </ChakraLink>
        </Link>
      ) : (
        imageContent
      )}

      {/* Caption */}
      {showCaption && (
        <Box bg={captionBg} p={2} borderRadius="md">
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={0}>
              <HStack spacing={2}>
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  {screenshot.name}
                </Text>
                {enableDeepLink && appUrl && (
                  <Tooltip label="Opens the actual page in the app">
                    <Badge colorScheme="brand" fontSize="xs" variant="subtle">
                      <HStack spacing={1}>
                        <Icon as={FaExternalLinkAlt} boxSize={2} />
                        <Text>Deep Link</Text>
                      </HStack>
                    </Badge>
                  </Tooltip>
                )}
              </HStack>
              {screenshot.description && (
                <Text fontSize="xs" color={textColor}>
                  {screenshot.description}
                </Text>
              )}
            </VStack>
            {screenshot.captured_at && (
              <Tooltip label="Last captured">
                <HStack spacing={1} color={textColor}>
                  <Icon as={FaClock} boxSize={3} />
                  <Text fontSize="xs">{formatTimestamp(screenshot.captured_at)}</Text>
                </HStack>
              </Tooltip>
            )}
          </HStack>
        </Box>
      )}
    </VStack>
  );
}

/**
 * DocScreenshotGrid - Display multiple screenshots in a grid
 */
export function DocScreenshotGrid({ 
  pageIds, 
  columns = { base: 1, md: 2 }, 
  enableDeepLinks = true,
  size = 'md'
}) {
  return (
    <Box
      display="grid"
      gridTemplateColumns={{
        base: '1fr',
        md: `repeat(${columns.md || 2}, 1fr)`,
      }}
      gap={6}
    >
      {pageIds.map((pageId) => (
        <DocScreenshot
          key={pageId}
          pageId={pageId}
          enableDeepLink={enableDeepLinks}
          size={size}
        />
      ))}
    </Box>
  );
}

export default DocScreenshot;
