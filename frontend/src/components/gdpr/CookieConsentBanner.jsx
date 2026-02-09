'use client';
import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Flex,
  Text,
  VStack,
  HStack,
  useColorModeValue,
  Link,
  Slide,
  IconButton,
  Collapse,
  Checkbox,
  Divider,
} from '@chakra-ui/react';
import { FaCookieBite, FaTimes, FaCog } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';

const COOKIE_CONSENT_KEY = 'contentry_cookie_consent';
const COOKIE_PREFERENCES_KEY = 'contentry_cookie_preferences';

export default function CookieConsentBanner() {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState({
    essential: true, // Always required
    analytics: false,
    marketing: false,
  });

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.700', 'gray.200');
  const mutedColor = useColorModeValue('gray.500', 'gray.400');

  useEffect(() => {
    // Check if user has already consented
    const consent = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!consent) {
      // Small delay to prevent flash on page load
      const timer = setTimeout(() => setIsVisible(true), 1000);
      return () => clearTimeout(timer);
    } else {
      // Load saved preferences
      const savedPrefs = localStorage.getItem(COOKIE_PREFERENCES_KEY);
      if (savedPrefs) {
        setPreferences(JSON.parse(savedPrefs));
      }
    }
  }, []);

  const handleAcceptAll = () => {
    const allAccepted = {
      essential: true,
      analytics: true,
      marketing: true,
    };
    saveConsent(allAccepted);
  };

  const handleAcceptEssential = () => {
    const essentialOnly = {
      essential: true,
      analytics: false,
      marketing: false,
    };
    saveConsent(essentialOnly);
  };

  const handleSavePreferences = () => {
    saveConsent(preferences);
  };

  const saveConsent = (prefs) => {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
    localStorage.setItem(COOKIE_PREFERENCES_KEY, JSON.stringify(prefs));
    setPreferences(prefs);
    setIsVisible(false);
    
    // Dispatch event for analytics initialization if accepted
    if (prefs.analytics) {
      window.dispatchEvent(new CustomEvent('cookieConsentAnalytics', { detail: true }));
    }
    if (prefs.marketing) {
      window.dispatchEvent(new CustomEvent('cookieConsentMarketing', { detail: true }));
    }
  };

  if (!isVisible) return null;

  return (
    <Slide direction="bottom" in={isVisible} style={{ zIndex: 9999 }}>
      <Box
        position="fixed"
        bottom={0}
        left={0}
        right={0}
        bg={bgColor}
        borderTopWidth="1px"
        borderColor={borderColor}
        boxShadow="0 -4px 20px rgba(0, 0, 0, 0.1)"
        p={{ base: 4, md: 6 }}
      >
        <Box maxW="1200px" mx="auto">
          <Flex
            direction={{ base: 'column', lg: 'row' }}
            align={{ base: 'stretch', lg: 'center' }}
            justify="space-between"
            gap={4}
          >
            {/* Content */}
            <VStack align="start" spacing={2} flex={1}>
              <HStack spacing={2}>
                <FaCookieBite color={useColorModeValue('#DD6B20', '#ED8936')} />
                <Text fontWeight="600" color={textColor}>
                  {t('gdpr.weValuePrivacy', 'We Value Your Privacy')}
                </Text>
              </HStack>
              <Text fontSize="sm" color={mutedColor} maxW="700px">
                {t('gdpr.cookieDescription', 'We use cookies to enhance your browsing experience, serve personalized content, and analyze our traffic. By clicking "Accept All", you consent to our use of cookies. You can customize your preferences or decline non-essential cookies.')}
              </Text>
              <Link
                href="/contentry/privacy"
                fontSize="sm"
                color="brand.500"
                fontWeight="500"
              >
                {t('gdpr.readPrivacyPolicy', 'Read our Privacy Policy')}
              </Link>
            </VStack>

            {/* Buttons */}
            <VStack spacing={2} align={{ base: 'stretch', lg: 'end' }} minW={{ lg: '280px' }}>
              <HStack spacing={2} w="full" justify={{ base: 'stretch', lg: 'end' }}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAcceptEssential}
                  flex={{ base: 1, lg: 'none' }}
                >
                  {t('gdpr.essentialOnly', 'Essential Only')}
                </Button>
                <Button
                  colorScheme="brand"
                  size="sm"
                  onClick={handleAcceptAll}
                  flex={{ base: 1, lg: 'none' }}
                >
                  {t('gdpr.acceptAll', 'Accept All')}
                </Button>
              </HStack>
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<FaCog />}
                onClick={() => setShowPreferences(!showPreferences)}
                color={mutedColor}
              >
                {t('gdpr.customizePreferences', 'Customize Preferences')}
              </Button>
            </VStack>
          </Flex>

          {/* Preferences Panel */}
          <Collapse in={showPreferences} animateOpacity>
            <Box mt={4} pt={4} borderTopWidth="1px" borderColor={borderColor}>
              <VStack align="stretch" spacing={3}>
                <Text fontWeight="600" fontSize="sm" color={textColor}>
                  {t('gdpr.cookiePreferences', 'Cookie Preferences')}
                </Text>
                
                {/* Essential Cookies */}
                <Flex justify="space-between" align="center">
                  <Box>
                    <Text fontSize="sm" fontWeight="500" color={textColor}>
                      {t('gdpr.essentialCookies', 'Essential Cookies')}
                    </Text>
                    <Text fontSize="xs" color={mutedColor}>
                      {t('gdpr.essentialCookiesDesc', 'Required for authentication, security, and basic functionality. Cannot be disabled.')}
                    </Text>
                  </Box>
                  <Checkbox
                    isChecked={true}
                    isDisabled
                    colorScheme="brand"
                  />
                </Flex>

                <Divider />

                {/* Analytics Cookies */}
                <Flex justify="space-between" align="center">
                  <Box>
                    <Text fontSize="sm" fontWeight="500" color={textColor}>
                      {t('gdpr.analyticsCookies', 'Analytics Cookies')}
                    </Text>
                    <Text fontSize="xs" color={mutedColor}>
                      {t('gdpr.analyticsCookiesDesc', 'Help us understand how visitors interact with our platform to improve our services.')}
                    </Text>
                  </Box>
                  <Checkbox
                    isChecked={preferences.analytics}
                    onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                    colorScheme="brand"
                  />
                </Flex>

                <Divider />

                {/* Marketing Cookies */}
                <Flex justify="space-between" align="center">
                  <Box>
                    <Text fontSize="sm" fontWeight="500" color={textColor}>
                      {t('gdpr.marketingCookies', 'Marketing Cookies')}
                    </Text>
                    <Text fontSize="xs" color={mutedColor}>
                      {t('gdpr.marketingCookiesDesc', 'Used to deliver personalized advertisements and measure campaign effectiveness.')}
                    </Text>
                  </Box>
                  <Checkbox
                    isChecked={preferences.marketing}
                    onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                    colorScheme="brand"
                  />
                </Flex>

                <Button
                  colorScheme="brand"
                  size="sm"
                  onClick={handleSavePreferences}
                  alignSelf="end"
                  mt={2}
                >
                  {t('gdpr.savePreferences', 'Save Preferences')}
                </Button>
              </VStack>
            </Box>
          </Collapse>
        </Box>
      </Box>
    </Slide>
  );
}

// Export a hook to check cookie consent status
export function useCookieConsent() {
  const [consent, setConsent] = useState(null);

  useEffect(() => {
    const savedPrefs = localStorage.getItem(COOKIE_PREFERENCES_KEY);
    if (savedPrefs) {
      setConsent(JSON.parse(savedPrefs));
    }
  }, []);

  return consent;
}
