#!/usr/bin/env node

/**
 * Translation Management CLI Tool
 * 
 * This script automates the translation of i18n resource files using 
 * Google Cloud Translation API.
 * 
 * Usage:
 *   npm run translate:create <lang>    - Create a new language file from English
 *   npm run translate:update <lang>    - Update existing file with missing keys
 *   npm run translate:update-all       - Update all existing language files
 * 
 * Example:
 *   npm run translate:create ja        - Creates Japanese translation
 *   npm run translate:update fr        - Updates French with new keys
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Configuration
const CONFIG = {
  sourceLocale: 'en',
  localesDir: path.join(__dirname, '..', 'src', 'i18n', 'locales'),
  apiKeyEnvVar: 'GOOGLE_TRANSLATE_API_KEY',
  backendEnvPath: path.join(__dirname, '..', '..', 'backend', '.env'),
  rateLimitDelay: 100, // ms between API calls to avoid rate limiting
};

// Supported language codes for reference
const SUPPORTED_LANGUAGES = {
  'en': 'English',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'no': 'Norwegian',
  'ar': 'Arabic',
  'ja': 'Japanese',
  'zh': 'Chinese (Simplified)',
  'zh-TW': 'Chinese (Traditional)',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'hi': 'Hindi',
  'fil': 'Filipino',
  'ko': 'Korean',
  'it': 'Italian',
  'nl': 'Dutch',
  'pl': 'Polish',
  'sv': 'Swedish',
  'da': 'Danish',
  'fi': 'Finnish',
  'tr': 'Turkish',
  'th': 'Thai',
  'vi': 'Vietnamese',
  'id': 'Indonesian',
  'ms': 'Malay',
  'he': 'Hebrew',
  'uk': 'Ukrainian',
  'cs': 'Czech',
  'el': 'Greek',
  'ro': 'Romanian',
  'hu': 'Hungarian',
  'bn': 'Bengali',
  'ta': 'Tamil',
  'te': 'Telugu',
  'mr': 'Marathi',
  'gu': 'Gujarati',
};

// Load API key from backend .env file
function loadApiKey() {
  // First try environment variable
  if (process.env[CONFIG.apiKeyEnvVar]) {
    return process.env[CONFIG.apiKeyEnvVar];
  }

  // Try loading from backend .env file
  try {
    const envContent = fs.readFileSync(CONFIG.backendEnvPath, 'utf8');
    const match = envContent.match(new RegExp(`${CONFIG.apiKeyEnvVar}=(.+)`));
    if (match && match[1]) {
      return match[1].trim();
    }
  } catch (err) {
    // File doesn't exist or can't be read
  }

  return null;
}

// Google Translate API call
function translateText(text, targetLang, apiKey) {
  return new Promise((resolve, reject) => {
    const url = `https://translation.googleapis.com/language/translate/v2?key=${apiKey}`;
    
    const postData = JSON.stringify({
      q: text,
      source: 'en',
      target: targetLang,
      format: 'text'
    });

    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.error) {
            reject(new Error(response.error.message));
          } else if (response.data && response.data.translations && response.data.translations[0]) {
            resolve(response.data.translations[0].translatedText);
          } else {
            reject(new Error('Unexpected API response format'));
          }
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`));
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

// Delay helper for rate limiting
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Recursively translate all string values in an object
async function translateObject(obj, targetLang, apiKey, parentKey = '', stats = { total: 0, translated: 0 }) {
  const result = {};

  // First pass: count total strings
  if (parentKey === '') {
    countStrings(obj, stats);
    console.log(`\n📊 Found ${stats.total} strings to translate\n`);
  }

  for (const [key, value] of Object.entries(obj)) {
    const currentPath = parentKey ? `${parentKey}.${key}` : key;

    if (typeof value === 'string') {
      try {
        // Translate the string
        const translated = await translateText(value, targetLang, apiKey);
        result[key] = translated;
        stats.translated++;
        
        // Progress indicator
        const progress = Math.round((stats.translated / stats.total) * 100);
        process.stdout.write(`\r⏳ Progress: ${stats.translated}/${stats.total} (${progress}%) - ${currentPath}`);
        process.stdout.write(' '.repeat(50)); // Clear any previous longer text
        
        // Rate limiting delay
        await delay(CONFIG.rateLimitDelay);
      } catch (err) {
        console.error(`\n⚠️  Failed to translate "${currentPath}": ${err.message}`);
        result[key] = value; // Keep original on failure
      }
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Recursively translate nested objects
      result[key] = await translateObject(value, targetLang, apiKey, currentPath, stats);
    } else {
      // Keep other types as-is (arrays, numbers, booleans, null)
      result[key] = value;
    }
  }

  return result;
}

// Count total strings in object
function countStrings(obj, stats) {
  for (const value of Object.values(obj)) {
    if (typeof value === 'string') {
      stats.total++;
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      countStrings(value, stats);
    }
  }
}

// Find missing keys between source and target
function findMissingKeys(source, target, parentKey = '') {
  const missing = {};

  for (const [key, value] of Object.entries(source)) {
    const currentPath = parentKey ? `${parentKey}.${key}` : key;

    if (typeof value === 'string') {
      if (!target || target[key] === undefined) {
        missing[key] = value;
      }
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const targetNested = target && typeof target[key] === 'object' ? target[key] : {};
      const nestedMissing = findMissingKeys(value, targetNested, currentPath);
      
      if (Object.keys(nestedMissing).length > 0) {
        missing[key] = nestedMissing;
      }
    }
  }

  return missing;
}

// Merge translated keys into existing object
function mergeTranslations(existing, newTranslations) {
  const result = { ...existing };

  for (const [key, value] of Object.entries(newTranslations)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      result[key] = mergeTranslations(result[key] || {}, value);
    } else {
      result[key] = value;
    }
  }

  return result;
}

// Get list of existing language files
function getExistingLanguages() {
  const files = fs.readdirSync(CONFIG.localesDir);
  return files
    .filter(f => f.endsWith('.json') && f !== `${CONFIG.sourceLocale}.json`)
    .map(f => f.replace('.json', ''));
}

// Load JSON file
function loadJsonFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    return null;
  }
}

// Save JSON file with pretty printing
function saveJsonFile(filePath, data) {
  const content = JSON.stringify(data, null, 2) + '\n';
  fs.writeFileSync(filePath, content, 'utf8');
}

// ============================================
// COMMAND: CREATE
// ============================================
async function commandCreate(targetLang) {
  console.log('\n🌍 Translation Create Command');
  console.log('═'.repeat(50));

  const apiKey = loadApiKey();
  if (!apiKey) {
    console.error('❌ Error: Google Translate API key not found.');
    console.error(`   Please set ${CONFIG.apiKeyEnvVar} in backend/.env`);
    process.exit(1);
  }

  const sourcePath = path.join(CONFIG.localesDir, `${CONFIG.sourceLocale}.json`);
  const targetPath = path.join(CONFIG.localesDir, `${targetLang}.json`);

  // Check if source exists
  if (!fs.existsSync(sourcePath)) {
    console.error(`❌ Error: Source file not found: ${sourcePath}`);
    process.exit(1);
  }

  // Check if target already exists
  if (fs.existsSync(targetPath)) {
    console.log(`⚠️  Warning: ${targetLang}.json already exists.`);
    console.log('   Use "translate:update" to add missing keys instead.');
    console.log('   Or delete the file first if you want to recreate it.');
    process.exit(1);
  }

  const langName = SUPPORTED_LANGUAGES[targetLang] || targetLang;
  console.log(`📄 Source: ${CONFIG.sourceLocale}.json (English)`);
  console.log(`🎯 Target: ${targetLang}.json (${langName})`);

  // Load source
  const sourceData = loadJsonFile(sourcePath);
  if (!sourceData) {
    console.error('❌ Error: Failed to load source file.');
    process.exit(1);
  }

  console.log('\n🚀 Starting translation...');
  const startTime = Date.now();

  try {
    const translatedData = await translateObject(sourceData, targetLang, apiKey);
    
    // Save translated file
    saveJsonFile(targetPath, translatedData);
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`\n\n✅ Success! Created ${targetLang}.json in ${duration}s`);
    console.log(`📁 File saved to: ${targetPath}`);
    
    // Reminder to update i18n config
    console.log('\n📝 Next Steps:');
    console.log(`   1. Review the translated file for accuracy`);
    console.log(`   2. Add the language to src/i18n/config.js if not already present`);
    
  } catch (err) {
    console.error(`\n❌ Translation failed: ${err.message}`);
    process.exit(1);
  }
}

// ============================================
// COMMAND: UPDATE
// ============================================
async function commandUpdate(targetLang) {
  console.log('\n🔄 Translation Update Command');
  console.log('═'.repeat(50));

  const apiKey = loadApiKey();
  if (!apiKey) {
    console.error('❌ Error: Google Translate API key not found.');
    console.error(`   Please set ${CONFIG.apiKeyEnvVar} in backend/.env`);
    process.exit(1);
  }

  const sourcePath = path.join(CONFIG.localesDir, `${CONFIG.sourceLocale}.json`);
  const targetPath = path.join(CONFIG.localesDir, `${targetLang}.json`);

  // Check if source exists
  if (!fs.existsSync(sourcePath)) {
    console.error(`❌ Error: Source file not found: ${sourcePath}`);
    process.exit(1);
  }

  // Check if target exists
  if (!fs.existsSync(targetPath)) {
    console.log(`⚠️  Target file ${targetLang}.json does not exist.`);
    console.log('   Use "translate:create" to create it first.');
    process.exit(1);
  }

  const langName = SUPPORTED_LANGUAGES[targetLang] || targetLang;
  console.log(`📄 Source: ${CONFIG.sourceLocale}.json (English)`);
  console.log(`🎯 Target: ${targetLang}.json (${langName})`);

  // Load files
  const sourceData = loadJsonFile(sourcePath);
  const targetData = loadJsonFile(targetPath);

  if (!sourceData || !targetData) {
    console.error('❌ Error: Failed to load files.');
    process.exit(1);
  }

  // Find missing keys
  const missingKeys = findMissingKeys(sourceData, targetData);
  const missingCount = countStringsInObject(missingKeys);

  if (missingCount === 0) {
    console.log('\n✅ No new keys found. File is up to date!');
    return;
  }

  console.log(`\n🔍 Found ${missingCount} new keys to translate`);
  console.log('\n🚀 Starting translation of new keys...');
  const startTime = Date.now();

  try {
    const translatedMissing = await translateObject(missingKeys, targetLang, apiKey);
    
    // Merge with existing
    const mergedData = mergeTranslations(targetData, translatedMissing);
    
    // Save updated file
    saveJsonFile(targetPath, mergedData);
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`\n\n✅ Success! Updated ${targetLang}.json with ${missingCount} new keys in ${duration}s`);
    
  } catch (err) {
    console.error(`\n❌ Translation failed: ${err.message}`);
    process.exit(1);
  }
}

// Helper to count strings in object
function countStringsInObject(obj) {
  let count = 0;
  for (const value of Object.values(obj)) {
    if (typeof value === 'string') {
      count++;
    } else if (typeof value === 'object' && value !== null) {
      count += countStringsInObject(value);
    }
  }
  return count;
}

// ============================================
// COMMAND: UPDATE-ALL
// ============================================
async function commandUpdateAll() {
  console.log('\n🌐 Translation Update-All Command');
  console.log('═'.repeat(50));

  const languages = getExistingLanguages();
  
  if (languages.length === 0) {
    console.log('⚠️  No existing language files found (other than English).');
    console.log('   Use "translate:create <lang>" to create a new language file.');
    return;
  }

  console.log(`📋 Found ${languages.length} language files to update:`);
  console.log(`   ${languages.join(', ')}\n`);

  for (const lang of languages) {
    console.log('\n' + '─'.repeat(50));
    await commandUpdate(lang);
  }

  console.log('\n' + '═'.repeat(50));
  console.log('🎉 All language files have been processed!');
}

// ============================================
// MAIN CLI HANDLER
// ============================================
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const targetLang = args[1];

  console.log('\n🔤 i18n Translation Management Tool');
  console.log('   Powered by Google Cloud Translation API\n');

  switch (command) {
    case 'create':
      if (!targetLang) {
        console.error('❌ Error: Please specify a target language code.');
        console.error('   Usage: npm run translate:create <lang>');
        console.error('   Example: npm run translate:create ja');
        console.error('\n   Supported language codes:');
        Object.entries(SUPPORTED_LANGUAGES).slice(0, 10).forEach(([code, name]) => {
          console.error(`     ${code} - ${name}`);
        });
        console.error('     ... and many more');
        process.exit(1);
      }
      await commandCreate(targetLang);
      break;

    case 'update':
      if (!targetLang) {
        console.error('❌ Error: Please specify a target language code.');
        console.error('   Usage: npm run translate:update <lang>');
        console.error('   Example: npm run translate:update ja');
        process.exit(1);
      }
      await commandUpdate(targetLang);
      break;

    case 'update-all':
      await commandUpdateAll();
      break;

    case 'list':
      console.log('📋 Existing language files:');
      const existing = getExistingLanguages();
      if (existing.length === 0) {
        console.log('   (none)');
      } else {
        existing.forEach(lang => {
          const name = SUPPORTED_LANGUAGES[lang] || 'Unknown';
          console.log(`   ${lang}.json - ${name}`);
        });
      }
      console.log('\n📚 Supported language codes for new translations:');
      Object.entries(SUPPORTED_LANGUAGES).forEach(([code, name]) => {
        const exists = existing.includes(code) || code === 'en';
        const status = exists ? '✓' : ' ';
        console.log(`   [${status}] ${code} - ${name}`);
      });
      break;

    default:
      console.log('Usage:');
      console.log('  npm run translate:create <lang>   Create a new language file');
      console.log('  npm run translate:update <lang>   Update existing file with new keys');
      console.log('  npm run translate:update-all      Update all existing language files');
      console.log('  npm run translate:list            List existing and supported languages');
      console.log('\nExamples:');
      console.log('  npm run translate:create ja       # Create Japanese translation');
      console.log('  npm run translate:update fr       # Update French with new keys');
      console.log('  npm run translate:update-all      # Update all languages');
      process.exit(1);
  }
}

// Run the CLI
main().catch(err => {
  console.error('❌ Unexpected error:', err.message);
  process.exit(1);
});
