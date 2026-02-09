import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
import { isRTL, SUPPORTED_LANGUAGES, loadLanguage, setUserLanguage } from '@/i18n/config';

/**
 * Hook to get the current language code for API calls
 * @returns {string} Current language code (e.g., 'en', 'es', 'fr')
 */
export default function useLanguage() {
  const { i18n } = useTranslation();
  return i18n.language || 'en';
}

/**
 * Enhanced hook with RTL support and language metadata
 * @returns {Object} Language state and utilities
 */
export function useLanguageConfig() {
  const { i18n, t } = useTranslation();
  const [isRTLMode, setIsRTLMode] = useState(false);
  const [languageInfo, setLanguageInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const lang = i18n.language || 'en';
    setIsRTLMode(isRTL(lang));
    setLanguageInfo(SUPPORTED_LANGUAGES[lang] || SUPPORTED_LANGUAGES['en']);
  }, [i18n.language]);

  const changeLanguage = async (langCode) => {
    if (!SUPPORTED_LANGUAGES[langCode]) {
      console.warn(`Language not supported: ${langCode}`);
      return false;
    }

    setIsLoading(true);
    try {
      await loadLanguage(langCode);
      await setUserLanguage(langCode);
      return true;
    } catch (error) {
      console.error('Failed to change language:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    // Current language code
    language: i18n.language || 'en',
    
    // Whether current language is RTL
    isRTL: isRTLMode,
    
    // Language metadata (name, native, flag, etc.)
    languageInfo,
    
    // Loading state when switching languages
    isLoading,
    
    // Function to change language
    changeLanguage,
    
    // Translation function
    t,
    
    // i18n instance for advanced usage
    i18n,
    
    // All supported languages
    supportedLanguages: Object.values(SUPPORTED_LANGUAGES),
    
    // Total number of supported languages
    languageCount: Object.keys(SUPPORTED_LANGUAGES).length,
  };
}

/**
 * Hook to detect and manage RTL direction
 * @returns {Object} RTL state and utilities
 */
export function useRTL() {
  const { i18n } = useTranslation();
  const [direction, setDirection] = useState('ltr');

  useEffect(() => {
    const lang = i18n.language || 'en';
    const rtl = isRTL(lang);
    setDirection(rtl ? 'rtl' : 'ltr');
    
    // Update document attributes
    if (typeof document !== 'undefined') {
      document.documentElement.dir = rtl ? 'rtl' : 'ltr';
      document.documentElement.lang = lang;
    }
  }, [i18n.language]);

  return {
    direction,
    isRTL: direction === 'rtl',
    isLTR: direction === 'ltr',
  };
}
