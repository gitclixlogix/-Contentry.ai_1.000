'use client';
import {
  Box,
  HStack,
  VStack,
  Icon,
  Text,
  Link,
  Alert,
  AlertIcon,
  Badge,
  Tooltip,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import NextLink from 'next/link';
import { FaFacebookF, FaInstagram, FaLinkedinIn, FaYoutube, FaTwitter, FaCheckCircle, FaExternalLinkAlt, FaTiktok, FaPinterest } from 'react-icons/fa';
import { SiThreads } from 'react-icons/si';
import { useColorModeValue } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';

// Platform configuration with character limits
export const PLATFORM_CONFIG = {
  twitter: { 
    icon: FaTwitter, 
    color: '#1DA1F2', 
    label: 'X (Twitter)',
    charLimit: 280,
    description: 'Short, punchy content with strong hooks',
    toneGuidance: 'direct, conversational, hashtag-optimized'
  },
  instagram: { 
    icon: FaInstagram, 
    color: '#E4405F', 
    label: 'Instagram',
    charLimit: 2200,
    description: 'Visual-focused with community hashtags',
    toneGuidance: 'personal, aesthetic, call-to-action focused'
  },
  facebook: { 
    icon: FaFacebookF, 
    color: '#1877F2', 
    label: 'Facebook',
    charLimit: 2000, // Capped for UX (actual is 63,206)
    description: 'Engaging stories and community content',
    toneGuidance: 'friendly, conversational, shareable'
  },
  linkedin: { 
    icon: FaLinkedinIn, 
    color: '#0A66C2', 
    label: 'LinkedIn',
    charLimit: 3000,
    description: 'Professional insights and thought leadership',
    toneGuidance: 'professional, value-driven, structured with clear takeaways'
  },
  threads: { 
    icon: SiThreads, 
    color: '#000000', 
    label: 'Threads',
    charLimit: 500,
    description: 'Conversational micro-content',
    toneGuidance: 'casual, authentic, thread-friendly'
  },
  tiktok: { 
    icon: FaTiktok, 
    color: '#000000', 
    label: 'TikTok',
    charLimit: 2200,
    description: 'Trendy video descriptions',
    toneGuidance: 'trendy, casual, engagement-focused, Gen-Z friendly'
  },
  pinterest: { 
    icon: FaPinterest, 
    color: '#E60023', 
    label: 'Pinterest',
    charLimit: 500,
    description: 'Inspiring visual descriptions',
    toneGuidance: 'inspirational, keyword-rich, actionable'
  },
  youtube: { 
    icon: FaYoutube, 
    color: '#FF0000', 
    label: 'YouTube',
    charLimit: 5000,
    description: 'Detailed video descriptions with SEO',
    toneGuidance: 'informative, SEO-optimized, subscriber-focused'
  },
};

/**
 * Get the strictest (lowest) character limit from selected platforms
 */
export const getStrictestLimit = (selectedPlatforms = []) => {
  if (!selectedPlatforms || selectedPlatforms.length === 0) {
    return null; // No limit if no platforms selected
  }
  
  const limits = selectedPlatforms
    .map(p => PLATFORM_CONFIG[p]?.charLimit)
    .filter(l => l !== undefined);
  
  return limits.length > 0 ? Math.min(...limits) : null;
};

/**
 * Get platform guidance text for AI prompts
 */
export const getPlatformGuidance = (selectedPlatforms = []) => {
  if (!selectedPlatforms || selectedPlatforms.length === 0) {
    return null;
  }
  
  const guidance = selectedPlatforms
    .map(p => {
      const config = PLATFORM_CONFIG[p];
      if (!config) return null;
      return `${config.label}: ${config.toneGuidance}`;
    })
    .filter(Boolean)
    .join('\n');
  
  return guidance;
};

/**
 * Reusable Platform Selector component with character limit awareness
 * 
 * @param {string[]} connectedPlatforms - List of platform IDs that are connected (optional for target selection)
 * @param {string[]} selectedPlatforms - List of currently selected platform IDs
 * @param {function} onChange - Callback when selection changes
 * @param {boolean} showConnectLink - Whether to show link to connect more accounts
 * @param {boolean} showAllPlatforms - If true, show all platforms regardless of connection status
 * @param {boolean} showCharLimits - Whether to display character limits
 * @param {boolean} compact - Use compact layout
 */
export default function PlatformSelector({ 
  connectedPlatforms = [], 
  selectedPlatforms = [], 
  onChange, 
  showConnectLink = true,
  showAllPlatforms = false,
  showCharLimits = true,
  compact = false
}) {
  const { t } = useTranslation();
  const connectedBg = useColorModeValue('green.50', 'green.900');
  const platformBg = useColorModeValue('gray.50', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBorderColor = useColorModeValue('blue.400', 'blue.400');
  const charLimitBg = useColorModeValue('blue.50', 'blue.900');

  // Determine which platforms to show
  const platformsToShow = showAllPlatforms 
    ? Object.keys(PLATFORM_CONFIG) 
    : connectedPlatforms;

  // Calculate strictest limit
  const strictestLimit = getStrictestLimit(selectedPlatforms);

  return (
    <VStack align="stretch" spacing={3}>
      {platformsToShow.length === 0 && !showAllPlatforms ? (
        <Alert status="info" borderRadius="md" size="sm">
          <AlertIcon />
          <Box>
            <Text fontSize="sm">{t('platforms.noAccountsConnected', 'No social accounts connected.')}</Text>
            {showConnectLink && (
              <Link as={NextLink} href="/contentry/settings/social" color="brand.500" fontSize="sm">
                {t('platforms.connectAccounts', 'Connect accounts')} <Icon as={FaExternalLinkAlt} boxSize={3} ml={1} />
              </Link>
            )}
          </Box>
        </Alert>
      ) : (
        <>
          <Wrap spacing={2}>
            {platformsToShow.map((platform) => {
              const config = PLATFORM_CONFIG[platform];
              if (!config) return null;
              const isSelected = selectedPlatforms?.includes(platform);
              const isConnected = connectedPlatforms.includes(platform);
              
              return (
                <WrapItem key={platform}>
                  <Tooltip 
                    label={
                      <Box>
                        <Text fontWeight="bold">{config.label}</Text>
                        <Text fontSize="xs">{config.description}</Text>
                        {showCharLimits && (
                          <Text fontSize="xs" color="blue.200">
                            {t('platforms.characterLimit', 'Character limit')}: {config.charLimit.toLocaleString()}
                          </Text>
                        )}
                        {!isConnected && !showAllPlatforms && (
                          <Text fontSize="xs" color="orange.200">{t('platforms.notConnected', 'Not connected')}</Text>
                        )}
                      </Box>
                    }
                    hasArrow
                    placement="top"
                  >
                    <Box
                      as="button"
                      type="button"
                      p={compact ? 1.5 : 2}
                      borderRadius="md"
                      borderWidth="2px"
                      borderColor={isSelected ? 'blue.500' : borderColor}
                      bg={isSelected ? selectedBg : platformBg}
                      opacity={!isConnected && !showAllPlatforms ? 0.5 : 1}
                      onClick={() => {
                        if (!isConnected && !showAllPlatforms) return;
                        const newPlatforms = isSelected
                          ? selectedPlatforms.filter(p => p !== platform)
                          : [...(selectedPlatforms || []), platform];
                        onChange(newPlatforms);
                      }}
                      _hover={{ 
                        borderColor: (isConnected || showAllPlatforms) ? hoverBorderColor : borderColor,
                        transform: (isConnected || showAllPlatforms) ? 'scale(1.02)' : 'none'
                      }}
                      transition="all 0.2s"
                      cursor={(isConnected || showAllPlatforms) ? 'pointer' : 'not-allowed'}
                    >
                      <HStack spacing={1}>
                        {isSelected && <Icon as={FaCheckCircle} color="blue.500" boxSize={3} />}
                        <Icon as={config.icon} color={config.color} boxSize={compact ? 3 : 4} />
                        {!compact && (
                          <Text fontSize="xs" fontWeight="500">{config.label}</Text>
                        )}
                        {showCharLimits && !compact && (
                          <Badge 
                            size="sm" 
                            colorScheme={isSelected ? "blue" : "gray"} 
                            fontSize="2xs"
                            ml={1}
                          >
                            {config.charLimit}
                          </Badge>
                        )}
                      </HStack>
                    </Box>
                  </Tooltip>
                </WrapItem>
              );
            })}
          </Wrap>

          {/* Show active character limit when platforms are selected */}
          {selectedPlatforms.length > 0 && strictestLimit && showCharLimits && (
            <HStack 
              p={2} 
              bg={charLimitBg} 
              borderRadius="md"
              borderLeftWidth="3px"
              borderLeftColor="blue.500"
            >
              <Icon as={FaCheckCircle} color="blue.500" boxSize={3} />
              <Text fontSize="xs" fontWeight="500">
                {t('platforms.activeCharacterLimit', 'Active character limit')}: <Text as="span" fontWeight="bold" color="blue.600">{strictestLimit.toLocaleString()}</Text>
                {selectedPlatforms.length > 1 && (
                  <Text as="span" color="gray.500"> ({t('platforms.strictestOf', 'strictest of')} {selectedPlatforms.length} {t('platforms.platforms', 'platforms')})</Text>
                )}
              </Text>
            </HStack>
          )}
        </>
      )}
      
      {showConnectLink && platformsToShow.length > 0 && !showAllPlatforms && (
        <Link as={NextLink} href="/contentry/settings/social" color="brand.500" fontSize="xs">
          {t('platforms.manageAccounts', 'Manage connected accounts')} <Icon as={FaExternalLinkAlt} boxSize={3} ml={1} />
        </Link>
      )}
    </VStack>
  );
}

export { PLATFORM_CONFIG as default_PLATFORM_CONFIG };
