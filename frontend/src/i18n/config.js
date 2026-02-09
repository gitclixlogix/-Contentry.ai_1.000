import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files - dynamic imports will be added for new languages
import enTranslations from './locales/en.json';

// Comprehensive list of all supported languages (130+ languages)
// RTL languages are marked with rtl: true
export const SUPPORTED_LANGUAGES = {
  // Core Languages (Most Common)
  'en': { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
  'es': { code: 'es', name: 'Spanish', native: 'Español', flag: '🇪🇸' },
  'fr': { code: 'fr', name: 'French', native: 'Français', flag: '🇫🇷' },
  'de': { code: 'de', name: 'German', native: 'Deutsch', flag: '🇩🇪' },
  'zh': { code: 'zh', name: 'Chinese (Simplified)', native: '简体中文', flag: '🇨🇳' },
  'zh_TW': { code: 'zh_TW', name: 'Chinese (Traditional)', native: '繁體中文', flag: '🇹🇼' },
  'ja': { code: 'ja', name: 'Japanese', native: '日本語', flag: '🇯🇵' },
  'ko': { code: 'ko', name: 'Korean', native: '한국어', flag: '🇰🇷' },
  'pt': { code: 'pt', name: 'Portuguese', native: 'Português', flag: '🇧🇷' },
  'ru': { code: 'ru', name: 'Russian', native: 'Русский', flag: '🇷🇺' },
  'it': { code: 'it', name: 'Italian', native: 'Italiano', flag: '🇮🇹' },
  'nl': { code: 'nl', name: 'Dutch', native: 'Nederlands', flag: '🇳🇱' },
  'pl': { code: 'pl', name: 'Polish', native: 'Polski', flag: '🇵🇱' },
  'tr': { code: 'tr', name: 'Turkish', native: 'Türkçe', flag: '🇹🇷' },
  'vi': { code: 'vi', name: 'Vietnamese', native: 'Tiếng Việt', flag: '🇻🇳' },
  'th': { code: 'th', name: 'Thai', native: 'ไทย', flag: '🇹🇭' },
  'id': { code: 'id', name: 'Indonesian', native: 'Bahasa Indonesia', flag: '🇮🇩' },
  'ms': { code: 'ms', name: 'Malay', native: 'Bahasa Melayu', flag: '🇲🇾' },
  
  // RTL Languages
  'ar': { code: 'ar', name: 'Arabic', native: 'العربية', flag: '🇸🇦', rtl: true },
  'he': { code: 'he', name: 'Hebrew', native: 'עברית', flag: '🇮🇱', rtl: true },
  'fa': { code: 'fa', name: 'Persian', native: 'فارسی', flag: '🇮🇷', rtl: true },
  'ur': { code: 'ur', name: 'Urdu', native: 'اردو', flag: '🇵🇰', rtl: true },
  'ps': { code: 'ps', name: 'Pashto', native: 'پښتو', flag: '🇦🇫', rtl: true },
  'sd': { code: 'sd', name: 'Sindhi', native: 'سنڌي', flag: '🇵🇰', rtl: true },
  'yi': { code: 'yi', name: 'Yiddish', native: 'ייִדיש', flag: '🇮🇱', rtl: true },
  'dv': { code: 'dv', name: 'Dhivehi', native: 'ދިވެހި', flag: '🇲🇻', rtl: true },
  'ug': { code: 'ug', name: 'Uyghur', native: 'ئۇيغۇرچە', flag: '🇨🇳', rtl: true },
  'ckb': { code: 'ckb', name: 'Kurdish (Sorani)', native: 'سۆرانی', flag: '🇮🇶', rtl: true },
  
  // South Asian Languages
  'hi': { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  'bn': { code: 'bn', name: 'Bengali', native: 'বাংলা', flag: '🇧🇩' },
  'ta': { code: 'ta', name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
  'te': { code: 'te', name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
  'mr': { code: 'mr', name: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
  'gu': { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી', flag: '🇮🇳' },
  'kn': { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
  'ml': { code: 'ml', name: 'Malayalam', native: 'മലയാളം', flag: '🇮🇳' },
  'pa': { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
  'or': { code: 'or', name: 'Odia (Oriya)', native: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
  'as': { code: 'as', name: 'Assamese', native: 'অসমীয়া', flag: '🇮🇳' },
  'ne': { code: 'ne', name: 'Nepali', native: 'नेपाली', flag: '🇳🇵' },
  'si': { code: 'si', name: 'Sinhala', native: 'සිංහල', flag: '🇱🇰' },
  'bho': { code: 'bho', name: 'Bhojpuri', native: 'भोजपुरी', flag: '🇮🇳' },
  'mai': { code: 'mai', name: 'Maithili', native: 'मैथिली', flag: '🇮🇳' },
  'gom': { code: 'gom', name: 'Konkani', native: 'कोंकणी', flag: '🇮🇳' },
  'sa': { code: 'sa', name: 'Sanskrit', native: 'संस्कृतम्', flag: '🇮🇳' },
  'mni_Mtei': { code: 'mni_Mtei', name: 'Meiteilon', native: 'ꯃꯤꯇꯩꯂꯣꯟ', flag: '🇮🇳' },
  'lus': { code: 'lus', name: 'Mizo', native: 'Mizo ṭawng', flag: '🇮🇳' },
  
  // Southeast Asian Languages
  'tl': { code: 'tl', name: 'Filipino', native: 'Filipino', flag: '🇵🇭' },
  'fil': { code: 'fil', name: 'Filipino', native: 'Filipino', flag: '🇵🇭' },
  'ceb': { code: 'ceb', name: 'Cebuano', native: 'Cebuano', flag: '🇵🇭' },
  'ilo': { code: 'ilo', name: 'Ilocano', native: 'Ilokano', flag: '🇵🇭' },
  'jv': { code: 'jv', name: 'Javanese', native: 'Basa Jawa', flag: '🇮🇩' },
  'su': { code: 'su', name: 'Sundanese', native: 'Basa Sunda', flag: '🇮🇩' },
  'my': { code: 'my', name: 'Myanmar (Burmese)', native: 'မြန်မာ', flag: '🇲🇲' },
  'km': { code: 'km', name: 'Khmer', native: 'ខ្មែរ', flag: '🇰🇭' },
  'lo': { code: 'lo', name: 'Lao', native: 'ລາວ', flag: '🇱🇦' },
  
  // East Asian Languages
  'yue': { code: 'yue', name: 'Cantonese', native: '粵語', flag: '🇭🇰' },
  'mn': { code: 'mn', name: 'Mongolian', native: 'Монгол', flag: '🇲🇳' },
  
  // European Languages
  'no': { code: 'no', name: 'Norwegian', native: 'Norsk', flag: '🇳🇴' },
  'sv': { code: 'sv', name: 'Swedish', native: 'Svenska', flag: '🇸🇪' },
  'da': { code: 'da', name: 'Danish', native: 'Dansk', flag: '🇩🇰' },
  'fi': { code: 'fi', name: 'Finnish', native: 'Suomi', flag: '🇫🇮' },
  'is': { code: 'is', name: 'Icelandic', native: 'Íslenska', flag: '🇮🇸' },
  'cs': { code: 'cs', name: 'Czech', native: 'Čeština', flag: '🇨🇿' },
  'sk': { code: 'sk', name: 'Slovak', native: 'Slovenčina', flag: '🇸🇰' },
  'hu': { code: 'hu', name: 'Hungarian', native: 'Magyar', flag: '🇭🇺' },
  'ro': { code: 'ro', name: 'Romanian', native: 'Română', flag: '🇷🇴' },
  'bg': { code: 'bg', name: 'Bulgarian', native: 'Български', flag: '🇧🇬' },
  'uk': { code: 'uk', name: 'Ukrainian', native: 'Українська', flag: '🇺🇦' },
  'be': { code: 'be', name: 'Belarusian', native: 'Беларуская', flag: '🇧🇾' },
  'hr': { code: 'hr', name: 'Croatian', native: 'Hrvatski', flag: '🇭🇷' },
  'sr': { code: 'sr', name: 'Serbian', native: 'Српски', flag: '🇷🇸' },
  'sl': { code: 'sl', name: 'Slovenian', native: 'Slovenščina', flag: '🇸🇮' },
  'bs': { code: 'bs', name: 'Bosnian', native: 'Bosanski', flag: '🇧🇦' },
  'mk': { code: 'mk', name: 'Macedonian', native: 'Македонски', flag: '🇲🇰' },
  'sq': { code: 'sq', name: 'Albanian', native: 'Shqip', flag: '🇦🇱' },
  'el': { code: 'el', name: 'Greek', native: 'Ελληνικά', flag: '🇬🇷' },
  'et': { code: 'et', name: 'Estonian', native: 'Eesti', flag: '🇪🇪' },
  'lv': { code: 'lv', name: 'Latvian', native: 'Latviešu', flag: '🇱🇻' },
  'lt': { code: 'lt', name: 'Lithuanian', native: 'Lietuvių', flag: '🇱🇹' },
  'mt': { code: 'mt', name: 'Maltese', native: 'Malti', flag: '🇲🇹' },
  'ga': { code: 'ga', name: 'Irish', native: 'Gaeilge', flag: '🇮🇪' },
  'cy': { code: 'cy', name: 'Welsh', native: 'Cymraeg', flag: '🏴󠁧󠁢󠁷󠁬󠁳󠁿' },
  'gd': { code: 'gd', name: 'Scots Gaelic', native: 'Gàidhlig', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿' },
  'lb': { code: 'lb', name: 'Luxembourgish', native: 'Lëtzebuergesch', flag: '🇱🇺' },
  'eu': { code: 'eu', name: 'Basque', native: 'Euskara', flag: '🇪🇸' },
  'ca': { code: 'ca', name: 'Catalan', native: 'Català', flag: '🇪🇸' },
  'gl': { code: 'gl', name: 'Galician', native: 'Galego', flag: '🇪🇸' },
  'fy': { code: 'fy', name: 'Frisian', native: 'Frysk', flag: '🇳🇱' },
  'co': { code: 'co', name: 'Corsican', native: 'Corsu', flag: '🇫🇷' },
  'la': { code: 'la', name: 'Latin', native: 'Latina', flag: '🏛️' },
  'eo': { code: 'eo', name: 'Esperanto', native: 'Esperanto', flag: '🌍' },
  
  // Caucasus & Central Asia
  'ka': { code: 'ka', name: 'Georgian', native: 'ქართული', flag: '🇬🇪' },
  'hy': { code: 'hy', name: 'Armenian', native: 'Հայерdelays', 'flag': '🇦🇲' },
  'az': { code: 'az', name: 'Azerbaijani', native: 'Azərbaycan', flag: '🇦🇿' },
  'kk': { code: 'kk', name: 'Kazakh', native: 'Қазақ', flag: '🇰🇿' },
  'ky': { code: 'ky', name: 'Kyrgyz', native: 'Кыргызча', flag: '🇰🇬' },
  'uz': { code: 'uz', name: 'Uzbek', native: "O'zbek", flag: '🇺🇿' },
  'tg': { code: 'tg', name: 'Tajik', native: 'Тоҷикӣ', flag: '🇹🇯' },
  'tk': { code: 'tk', name: 'Turkmen', native: 'Türkmen', flag: '🇹🇲' },
  'tt': { code: 'tt', name: 'Tatar', native: 'Татар', flag: '🇷🇺' },
  
  // African Languages
  'sw': { code: 'sw', name: 'Swahili', native: 'Kiswahili', flag: '🇰🇪' },
  'am': { code: 'am', name: 'Amharic', native: 'አማርኛ', flag: '🇪🇹' },
  'ha': { code: 'ha', name: 'Hausa', native: 'Hausa', flag: '🇳🇬' },
  'yo': { code: 'yo', name: 'Yoruba', native: 'Yorùbá', flag: '🇳🇬' },
  'ig': { code: 'ig', name: 'Igbo', native: 'Igbo', flag: '🇳🇬' },
  'zu': { code: 'zu', name: 'Zulu', native: 'isiZulu', flag: '🇿🇦' },
  'xh': { code: 'xh', name: 'Xhosa', native: 'isiXhosa', flag: '🇿🇦' },
  'af': { code: 'af', name: 'Afrikaans', native: 'Afrikaans', flag: '🇿🇦' },
  'sn': { code: 'sn', name: 'Shona', native: 'chiShona', flag: '🇿🇼' },
  'so': { code: 'so', name: 'Somali', native: 'Soomaali', flag: '🇸🇴' },
  'rw': { code: 'rw', name: 'Kinyarwanda', native: 'Ikinyarwanda', flag: '🇷🇼' },
  'ny': { code: 'ny', name: 'Chichewa', native: 'Chichewa', flag: '🇲🇼' },
  'mg': { code: 'mg', name: 'Malagasy', native: 'Malagasy', flag: '🇲🇬' },
  'st': { code: 'st', name: 'Sesotho', native: 'Sesotho', flag: '🇱🇸' },
  'lg': { code: 'lg', name: 'Luganda', native: 'Luganda', flag: '🇺🇬' },
  'om': { code: 'om', name: 'Oromo', native: 'Afaan Oromoo', flag: '🇪🇹' },
  'ti': { code: 'ti', name: 'Tigrinya', native: 'ትግርኛ', flag: '🇪🇷' },
  'ln': { code: 'ln', name: 'Lingala', native: 'Lingála', flag: '🇨🇩' },
  'ts': { code: 'ts', name: 'Tsonga', native: 'Xitsonga', flag: '🇿🇦' },
  'nso': { code: 'nso', name: 'Sepedi', native: 'Sepedi', flag: '🇿🇦' },
  'ee': { code: 'ee', name: 'Ewe', native: 'Eʋegbe', flag: '🇬🇭' },
  'ak': { code: 'ak', name: 'Twi', native: 'Twi', flag: '🇬🇭' },
  'bm': { code: 'bm', name: 'Bambara', native: 'Bamanankan', flag: '🇲🇱' },
  'kri': { code: 'kri', name: 'Krio', native: 'Krio', flag: '🇸🇱' },
  
  // Americas & Pacific
  'ht': { code: 'ht', name: 'Haitian Creole', native: 'Kreyòl ayisyen', flag: '🇭🇹' },
  'haw': { code: 'haw', name: 'Hawaiian', native: 'ʻŌlelo Hawaiʻi', flag: '🇺🇸' },
  'sm': { code: 'sm', name: 'Samoan', native: 'Gagana Samoa', flag: '🇼🇸' },
  'mi': { code: 'mi', name: 'Maori', native: 'Māori', flag: '🇳🇿' },
  'fj': { code: 'fj', name: 'Fijian', native: 'Vosa Vakaviti', flag: '🇫🇯' },
  'gn': { code: 'gn', name: 'Guarani', native: "Avañe'ẽ", flag: '🇵🇾' },
  'qu': { code: 'qu', name: 'Quechua', native: 'Runasimi', flag: '🇵🇪' },
  'ay': { code: 'ay', name: 'Aymara', native: 'Aymar aru', flag: '🇧🇴' },
  
  // Other Languages
  'ku': { code: 'ku', name: 'Kurdish (Kurmanji)', native: 'Kurdî', flag: '🇮🇶' },
  'hmn': { code: 'hmn', name: 'Hmong', native: 'Hmoob', flag: '🌏' },
};

// RTL language codes for easy lookup
export const RTL_LANGUAGES = new Set([
  'ar', 'he', 'fa', 'ur', 'ps', 'sd', 'yi', 'dv', 'ug', 'ckb'
]);

// Check if a language is RTL
export const isRTL = (langCode) => {
  return RTL_LANGUAGES.has(langCode) || SUPPORTED_LANGUAGES[langCode]?.rtl === true;
};

// Dynamic locale loading function
const loadLocale = async (langCode) => {
  try {
    // Handle special characters in language codes
    const safeCode = langCode.replace('-', '_');
    const localeModule = await import(`./locales/${safeCode}.json`);
    return localeModule.default;
  } catch (error) {
    console.warn(`Failed to load locale: ${langCode}`, error);
    return null;
  }
};

// Initial resources with English
const resources = {
  en: { translation: enTranslations },
};

// Initialize i18n with lazy loading support
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'contentry_language',
      caches: ['localStorage'],
    },
    // Enable lazy loading
    partialBundledLanguages: true,
  });

// Auto-load saved language on initialization
if (typeof window !== 'undefined') {
  const savedLang = localStorage.getItem('contentry_language');
  if (savedLang && savedLang !== 'en' && SUPPORTED_LANGUAGES[savedLang]) {
    // Load the language asynchronously
    loadLocale(savedLang).then(translations => {
      if (translations) {
        i18n.addResourceBundle(savedLang, 'translation', translations);
        i18n.changeLanguage(savedLang);
        // Update document direction for RTL
        document.documentElement.dir = RTL_LANGUAGES.has(savedLang) ? 'rtl' : 'ltr';
        document.documentElement.lang = savedLang;
      }
    });
  }
}

// Function to dynamically load a language
export const loadLanguage = async (langCode) => {
  if (!SUPPORTED_LANGUAGES[langCode]) {
    console.warn(`Language not supported: ${langCode}`);
    return false;
  }

  // Check if already loaded
  if (i18n.hasResourceBundle(langCode, 'translation')) {
    return true;
  }

  try {
    const translations = await loadLocale(langCode);
    if (translations) {
      i18n.addResourceBundle(langCode, 'translation', translations);
      return true;
    }
  } catch (error) {
    console.error(`Failed to load language ${langCode}:`, error);
  }
  return false;
};

// Helper functions
export const getUserLanguage = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('contentry_language');
    if (saved && SUPPORTED_LANGUAGES[saved]) {
      return saved;
    }
  }
  return 'en';
};

export const setUserLanguage = async (langCode) => {
  if (typeof window !== 'undefined' && SUPPORTED_LANGUAGES[langCode]) {
    // Load the language if not already loaded
    await loadLanguage(langCode);
    
    localStorage.setItem('contentry_language', langCode);
    i18n.changeLanguage(langCode);
    
    // Update document direction for RTL languages
    document.documentElement.dir = isRTL(langCode) ? 'rtl' : 'ltr';
    document.documentElement.lang = langCode;
    
    window.dispatchEvent(new Event('languageChanged'));
  }
};

export const getSupportedLanguages = () => {
  return Object.values(SUPPORTED_LANGUAGES);
};

export const getLanguageName = (code) => {
  return SUPPORTED_LANGUAGES[code]?.name || 'English';
};

export const getLanguageNativeName = (code) => {
  return SUPPORTED_LANGUAGES[code]?.native || 'English';
};

// Get languages grouped by region for better UX in language selector
export const getLanguagesByRegion = () => {
  const regions = {
    'Common': ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'pt', 'ru', 'ar', 'hi'],
    'Europe': ['it', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs', 'el', 'hu', 'ro', 'uk', 'bg', 'hr', 'sr', 'sk', 'sl'],
    'Asia': ['zh_TW', 'th', 'vi', 'id', 'ms', 'tl', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'my', 'km', 'lo', 'ne', 'si'],
    'Middle East': ['he', 'fa', 'ur', 'ps', 'ku', 'ckb'],
    'Africa': ['sw', 'am', 'ha', 'yo', 'ig', 'zu', 'xh', 'af', 'so', 'rw'],
    'Americas': ['ht', 'gn', 'qu'],
    'Others': Object.keys(SUPPORTED_LANGUAGES).filter(code => 
      !['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'pt', 'ru', 'ar', 'hi',
        'it', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs', 'el', 'hu', 'ro', 'uk', 'bg', 'hr', 'sr', 'sk', 'sl',
        'zh_TW', 'th', 'vi', 'id', 'ms', 'tl', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'my', 'km', 'lo', 'ne', 'si',
        'he', 'fa', 'ur', 'ps', 'ku', 'ckb',
        'sw', 'am', 'ha', 'yo', 'ig', 'zu', 'xh', 'af', 'so', 'rw',
        'ht', 'gn', 'qu'].includes(code)
    ),
  };

  return Object.entries(regions).map(([name, codes]) => ({
    name,
    languages: codes.map(code => SUPPORTED_LANGUAGES[code]).filter(Boolean),
  }));
};

export default i18n;
