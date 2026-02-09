'use client';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Icon,
  useColorModeValue,
  Link as ChakraLink,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Divider,
  Image,
  Card,
  CardBody,
  Badge,
  List,
  ListItem,
  ListIcon,
  Alert,
  AlertIcon,
  Code,
  Skeleton,
  Button,
  IconButton,
  Tooltip,
} from '@chakra-ui/react';
import { FaChevronRight, FaChevronLeft, FaCheckCircle, FaInfoCircle, FaLightbulb, FaBook, FaSyncAlt, FaExternalLinkAlt } from 'react-icons/fa';
import Link from 'next/link';
import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';

// Sticky navigation component for documentation - FIXED for proper sticky behavior
function DocNavigation({ sections, activeSection }) {
  const activeBg = useColorModeValue('brand.50', 'brand.900');
  const activeColor = useColorModeValue('brand.600', 'brand.200');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box
      as="aside"
      position="sticky"
      top="90px"
      alignSelf="flex-start"
      w="250px"
      minW="250px"
      maxH="calc(100vh - 120px)"
      overflowY="auto"
      display={{ base: 'none', lg: 'block' }}
      pr={4}
      pb={8}
      bg={bgColor}
      borderRadius="lg"
      p={4}
      boxShadow="sm"
      css={{
        '&::-webkit-scrollbar': { width: '4px' },
        '&::-webkit-scrollbar-track': { background: 'transparent' },
        '&::-webkit-scrollbar-thumb': { background: '#CBD5E0', borderRadius: '4px' },
      }}
    >
      <Text fontWeight="600" fontSize="sm" mb={4} textTransform="uppercase" letterSpacing="wide" color={textColor}>
        On this page
      </Text>
      <VStack align="stretch" spacing={1}>
        {sections.map((section) => (
          <ChakraLink
            key={section.id}
            href={`#${section.id}`}
            px={3}
            py={2}
            borderRadius="md"
            fontSize="sm"
            bg={activeSection === section.id ? activeBg : 'transparent'}
            color={activeSection === section.id ? activeColor : textColor}
            fontWeight={activeSection === section.id ? '600' : '400'}
            borderLeftWidth="3px"
            borderLeftColor={activeSection === section.id ? activeColor : 'transparent'}
            _hover={{ bg: hoverBg, textDecoration: 'none' }}
            transition="all 0.2s"
          >
            {section.title}
          </ChakraLink>
        ))}
      </VStack>
    </Box>
  );
}

// Documentation section component
export function DocSection({ id, title, children }) {
  const textColor = useColorModeValue('navy.700', 'white');
  
  return (
    <Box id={id} scrollMarginTop="120px" mb={10}>
      <Heading size="lg" color={textColor} mb={4}>
        {title}
      </Heading>
      {children}
    </Box>
  );
}

// Documentation subsection component
export function DocSubsection({ title, children }) {
  const textColor = useColorModeValue('navy.700', 'white');
  
  return (
    <Box mb={6}>
      <Heading size="md" color={textColor} mb={3}>
        {title}
      </Heading>
      {children}
    </Box>
  );
}

// Documentation paragraph component
export function DocParagraph({ children }) {
  const textColor = useColorModeValue('gray.700', 'gray.300');
  
  return (
    <Text color={textColor} lineHeight="1.8" mb={4}>
      {children}
    </Text>
  );
}

// Documentation feature list component
export function DocFeatureList({ items }) {
  const textColor = useColorModeValue('gray.700', 'gray.300');
  
  return (
    <List spacing={2} mb={4}>
      {items.map((item, idx) => (
        <ListItem key={idx} display="flex" alignItems="flex-start">
          <ListIcon as={FaCheckCircle} color="green.500" mt={1} />
          <Text color={textColor}>{item}</Text>
        </ListItem>
      ))}
    </List>
  );
}

// Documentation tip/note component
export function DocTip({ type = 'info', children }) {
  const statusMap = {
    info: 'info',
    tip: 'success',
    warning: 'warning',
  };
  
  return (
    <Alert status={statusMap[type]} borderRadius="md" mb={4}>
      <AlertIcon />
      <Text fontSize="sm">{children}</Text>
    </Alert>
  );
}

// Documentation image component (static)
export function DocImage({ src, alt, caption }) {
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const captionColor = useColorModeValue('gray.500', 'gray.400');
  
  return (
    <Box mb={6}>
      <Box
        borderWidth="1px"
        borderColor={borderColor}
        borderRadius="lg"
        overflow="hidden"
        mb={2}
      >
        <Image src={src} alt={alt} w="full" />
      </Box>
      {caption && (
        <Text fontSize="sm" color={captionColor} textAlign="center" fontStyle="italic">
          {caption}
        </Text>
      )}
    </Box>
  );
}

// Import and re-export WorkflowGif component for documentation pages
export { WorkflowGif, WorkflowGifGallery } from '@/components/documentation/WorkflowGif';

// Dynamic documentation screenshot component
export function DocScreenshot({ pageId, caption, showRefresh = true }) {
  const [screenshot, setScreenshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const captionColor = useColorModeValue('gray.500', 'gray.400');
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  
  // Get API URL - use same logic as other components
  const getApiBase = () => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return '/api/v1';
      }
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      if (backendUrl) {
        return `${backendUrl}/api/v1`;
      }
      return 'http://localhost:8001/api/v1';
    }
    return process.env.NEXT_PUBLIC_BACKEND_URL ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1` : '/api/v1';
  };

  const fetchScreenshot = useCallback(async () => {
    if (!pageId) return;
    
    try {
      setLoading(true);
      const apiBase = getApiBase();
      const response = await axios.get(
        `${apiBase}/documentation/screenshots/${pageId}`
      );
      setScreenshot(response.data);
      setError(null);
    } catch (err) {
      console.error(`Failed to fetch screenshot ${pageId}:`, err);
      setError('Screenshot not available');
    } finally {
      setLoading(false);
    }
  }, [pageId]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      const apiBase = getApiBase();
      await axios.post(
        `${apiBase}/documentation/screenshots/refresh/${pageId}`
      );
      // Wait for capture to complete
      setTimeout(() => {
        fetchScreenshot();
        setRefreshing(false);
      }, 8000);
    } catch (err) {
      console.error(`Failed to refresh screenshot ${pageId}:`, err);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchScreenshot();
  }, [fetchScreenshot]);

  if (loading) {
    return (
      <Box mb={6}>
        <Skeleton 
          height="300px" 
          borderRadius="lg"
          startColor={bgColor}
          endColor={borderColor}
        />
        {caption && (
          <Text fontSize="sm" color={captionColor} textAlign="center" fontStyle="italic" mt={2}>
            {caption}
          </Text>
        )}
      </Box>
    );
  }

  if (error || !screenshot?.image_data) {
    return (
      <Box mb={6}>
        <Box
          borderWidth="1px"
          borderColor={borderColor}
          borderRadius="lg"
          bg={bgColor}
          p={8}
          textAlign="center"
        >
          <Text color={captionColor} mb={4}>
            {error || 'Screenshot not yet captured'}
          </Text>
          {showRefresh && (
            <Button
              size="sm"
              colorScheme="brand"
              leftIcon={<FaSyncAlt />}
              onClick={handleRefresh}
              isLoading={refreshing}
              loadingText="Capturing..."
            >
              Capture Screenshot
            </Button>
          )}
        </Box>
        {caption && (
          <Text fontSize="sm" color={captionColor} textAlign="center" fontStyle="italic" mt={2}>
            {caption}
          </Text>
        )}
      </Box>
    );
  }

  return (
    <Box mb={6}>
      <Link href={screenshot.path || '#'} passHref legacyBehavior>
        <ChakraLink 
          _hover={{ textDecoration: 'none' }}
          display="block"
        >
          <Box
            borderWidth="2px"
            borderColor={borderColor}
            borderRadius="lg"
            overflow="hidden"
            position="relative"
            cursor="pointer"
            transition="all 0.2s"
            _hover={{ 
              borderColor: 'brand.400',
              transform: 'translateY(-2px)',
              boxShadow: 'lg',
              '.refresh-btn': { opacity: 1 },
              '.deep-link-overlay': { opacity: 1 }
            }}
          >
            <Image 
              src={`data:${screenshot.content_type || 'image/png'};base64,${screenshot.image_data}`} 
              alt={screenshot.name || caption || 'Screenshot'} 
              w="full" 
            />
            
            {/* Deep Link Overlay */}
            <Box
              className="deep-link-overlay"
              position="absolute"
              top={0}
              left={0}
              right={0}
              bottom={0}
              bg="blackAlpha.600"
              display="flex"
              alignItems="center"
              justifyContent="center"
              opacity={0}
              transition="opacity 0.2s"
            >
              <VStack spacing={2}>
                <Icon as={FaExternalLinkAlt} boxSize={8} color="white" />
                <Text color="white" fontWeight="600" fontSize="md">
                  Click to open in app
                </Text>
              </VStack>
            </Box>

            {/* Refresh Button */}
            {showRefresh && (
              <HStack 
                className="refresh-btn"
                position="absolute" 
                top={2} 
                right={2} 
                opacity={0}
                transition="opacity 0.2s"
                spacing={1}
                onClick={(e) => e.stopPropagation()}
              >
                <Tooltip label="Refresh screenshot">
                  <IconButton
                    size="sm"
                    icon={<FaSyncAlt />}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleRefresh();
                    }}
                    isLoading={refreshing}
                    colorScheme="brand"
                    variant="solid"
                    aria-label="Refresh screenshot"
                  />
                </Tooltip>
              </HStack>
            )}
            
            {/* Deep Link Badge */}
            <Badge 
              position="absolute" 
              bottom={2} 
              right={2} 
              colorScheme="brand" 
              fontSize="xs"
              px={2}
              py={1}
            >
              <HStack spacing={1}>
                <Icon as={FaExternalLinkAlt} boxSize={2} />
                <Text>Interactive</Text>
              </HStack>
            </Badge>
          </Box>
        </ChakraLink>
      </Link>
      <HStack justify="space-between" mt={2}>
        <Text fontSize="sm" color={captionColor} fontStyle="italic">
          {caption || screenshot.description}
        </Text>
        {screenshot.captured_at && (
          <Text fontSize="xs" color={captionColor}>
            Updated: {new Date(screenshot.captured_at).toLocaleDateString()}
          </Text>
        )}
      </HStack>
    </Box>
  );
}

// Main documentation layout component
export default function DocumentationLayout({ 
  title, 
  description, 
  icon: IconComponent, 
  iconColor,
  sections,
  children 
}) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('');
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const backButtonBg = useColorModeValue('gray.100', 'gray.700');
  const backButtonHoverBg = useColorModeValue('gray.200', 'gray.600');
  
  // Colors for sticky nav - must be called at component top level
  const navActiveBg = useColorModeValue('brand.50', 'brand.900');
  const navActiveColor = useColorModeValue('brand.600', 'brand.200');
  const navHoverBg = useColorModeValue('gray.100', 'gray.700');

  // Track active section on scroll
  useEffect(() => {
    const handleScroll = () => {
      const sectionElements = sections.map(s => document.getElementById(s.id));
      const scrollPosition = window.scrollY + 150;
      
      for (let i = sectionElements.length - 1; i >= 0; i--) {
        const section = sectionElements[i];
        if (section && section.offsetTop <= scrollPosition) {
          setActiveSection(sections[i].id);
          break;
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check
    return () => window.removeEventListener('scroll', handleScroll);
  }, [sections]);

  return (
    <Box>
      {/* Back Button and Breadcrumb Row */}
      <HStack justify="space-between" align="center" mb={4} flexWrap="wrap" gap={2}>
        <Button
          as={Link}
          href="/contentry/documentation"
          leftIcon={<FaChevronLeft />}
          variant="ghost"
          size="sm"
          bg={backButtonBg}
          _hover={{ bg: backButtonHoverBg }}
          fontWeight="500"
        >
          {t('documentation.backToGuides', 'Back to All Guides')}
        </Button>
        
        {/* Breadcrumb */}
        <Breadcrumb
          spacing="8px"
          separator={<FaChevronRight color="gray.500" size="10px" />}
        >
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} href="/contentry/documentation" color={textColorSecondary}>
              {t('documentation.title')}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink color={textColor} fontWeight="600">
              {title}
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </HStack>

      {/* Header */}
      <Card bg={cardBg} mb={8}>
        <CardBody>
          <HStack spacing={4}>
            <Box
              p={4}
              borderRadius="xl"
              bg={useColorModeValue(`${iconColor}.50`, `${iconColor}.900`)}
            >
              <Icon as={IconComponent} fontSize="3xl" color={`${iconColor}.500`} />
            </Box>
            <Box>
              <Heading size="lg" color={textColor}>
                {title}
              </Heading>
              <Text color={textColorSecondary} mt={1}>
                {description}
              </Text>
            </Box>
          </HStack>
        </CardBody>
      </Card>

      {/* Content Layout with Sticky Navigation */}
      <Flex gap={8} position="relative" align="flex-start">
        {/* Sticky Navigation - Fixed position sidebar for docs */}
        <Box
          as="aside"
          position={{ base: 'relative', lg: 'fixed' }}
          top={{ lg: '110px' }}
          w="250px"
          minW="250px"
          h="fit-content"
          maxH={{ lg: 'calc(100vh - 140px)' }}
          overflowY="auto"
          display={{ base: 'none', lg: 'block' }}
          bg={cardBg}
          borderRadius="lg"
          p={4}
          boxShadow="sm"
          zIndex={10}
          css={{
            '&::-webkit-scrollbar': { width: '4px' },
            '&::-webkit-scrollbar-track': { background: 'transparent' },
            '&::-webkit-scrollbar-thumb': { background: '#CBD5E0', borderRadius: '4px' },
          }}
        >
          <Text fontWeight="600" fontSize="sm" mb={4} textTransform="uppercase" letterSpacing="wide" color={textColorSecondary}>
            On this page
          </Text>
          <VStack align="stretch" spacing={1}>
            {sections.map((section) => (
              <ChakraLink
                key={section.id}
                href={`#${section.id}`}
                px={3}
                py={2}
                borderRadius="md"
                fontSize="sm"
                bg={activeSection === section.id ? navActiveBg : 'transparent'}
                color={activeSection === section.id ? navActiveColor : textColorSecondary}
                fontWeight={activeSection === section.id ? '600' : '400'}
                borderLeftWidth="3px"
                borderLeftColor={activeSection === section.id ? navActiveColor : 'transparent'}
                _hover={{ bg: navHoverBg, textDecoration: 'none' }}
                transition="all 0.2s"
              >
                {section.title}
              </ChakraLink>
            ))}
          </VStack>
        </Box>

        {/* Spacer for fixed nav on large screens */}
        <Box w="250px" minW="250px" display={{ base: 'none', lg: 'block' }} />

        {/* Main Content */}
        <Box flex="1" maxW={{ base: '100%', lg: 'calc(100% - 280px)' }}>
          <Card bg={cardBg}>
            <CardBody>
              {children}
            </CardBody>
          </Card>
          
          {/* Bottom back link */}
          <Button
            as={Link}
            href="/contentry/documentation"
            leftIcon={<FaChevronLeft />}
            variant="ghost"
            size="sm"
            mt={6}
            bg={backButtonBg}
            _hover={{ bg: backButtonHoverBg }}
            fontWeight="500"
          >
            {t('documentation.backToGuides', 'Back to All Guides')}
          </Button>
        </Box>
      </Flex>
    </Box>
  );
}
