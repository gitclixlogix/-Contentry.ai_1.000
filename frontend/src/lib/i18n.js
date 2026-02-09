// i18n configuration - Re-exports from main config
// This file provides backward compatibility for existing imports

export { 
  default,
  SUPPORTED_LANGUAGES, 
  getUserLanguage, 
  setUserLanguage,
  getSupportedLanguages,
  getLanguageName,
  getLanguageNativeName
} from '../i18n/config';
