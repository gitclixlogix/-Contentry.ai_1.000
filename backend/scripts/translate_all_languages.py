"""
Translate UI strings to all Google Translate supported languages.
Uses Google Cloud Translation API with proper batching.
"""

import json
import os
import time
from pathlib import Path
import requests
from typing import Dict, List

# Google Translate API configuration
API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY', 'AIzaSyApkV7J7soqyCmMh09YLq9vQ6GgOUjSims')
TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

# Paths
LOCALES_DIR = Path("/app/frontend/src/i18n/locales")
EN_FILE = LOCALES_DIR / "en.json"

# Google Translate API limits: 128 text segments per request
MAX_SEGMENTS = 100  # Stay safely under the limit

# All languages to translate (comprehensive list)
ALL_LANGUAGES = {
    'af': {'name': 'Afrikaans', 'native': 'Afrikaans', 'flag': '🇿🇦'},
    'sq': {'name': 'Albanian', 'native': 'Shqip', 'flag': '🇦🇱'},
    'am': {'name': 'Amharic', 'native': 'አማርኛ', 'flag': '🇪🇹'},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦', 'rtl': True},
    'hy': {'name': 'Armenian', 'native': 'Հայdelays', 'flag': '🇦🇲'},
    'as': {'name': 'Assamese', 'native': 'অসমীয়া', 'flag': '🇮🇳'},
    'ay': {'name': 'Aymara', 'native': 'Aymar aru', 'flag': '🇧🇴'},
    'az': {'name': 'Azerbaijani', 'native': 'Azərbaycan', 'flag': '🇦🇿'},
    'bm': {'name': 'Bambara', 'native': 'Bamanankan', 'flag': '🇲🇱'},
    'eu': {'name': 'Basque', 'native': 'Euskara', 'flag': '🇪🇸'},
    'be': {'name': 'Belarusian', 'native': 'Беларуская', 'flag': '🇧🇾'},
    'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': '🇧🇩'},
    'bho': {'name': 'Bhojpuri', 'native': 'भोजपुरी', 'flag': '🇮🇳'},
    'bs': {'name': 'Bosnian', 'native': 'Bosanski', 'flag': '🇧🇦'},
    'bg': {'name': 'Bulgarian', 'native': 'Български', 'flag': '🇧🇬'},
    'ca': {'name': 'Catalan', 'native': 'Català', 'flag': '🇪🇸'},
    'ceb': {'name': 'Cebuano', 'native': 'Cebuano', 'flag': '🇵🇭'},
    'ny': {'name': 'Chichewa', 'native': 'Chichewa', 'flag': '🇲🇼'},
    'zh': {'name': 'Chinese (Simplified)', 'native': '简体中文', 'flag': '🇨🇳'},
    'zh-TW': {'name': 'Chinese (Traditional)', 'native': '繁體中文', 'flag': '🇹🇼'},
    'co': {'name': 'Corsican', 'native': 'Corsu', 'flag': '🇫🇷'},
    'hr': {'name': 'Croatian', 'native': 'Hrvatski', 'flag': '🇭🇷'},
    'cs': {'name': 'Czech', 'native': 'Čeština', 'flag': '🇨🇿'},
    'da': {'name': 'Danish', 'native': 'Dansk', 'flag': '🇩🇰'},
    'dv': {'name': 'Dhivehi', 'native': 'ދިވެހި', 'flag': '🇲🇻', 'rtl': True},
    'nl': {'name': 'Dutch', 'native': 'Nederlands', 'flag': '🇳🇱'},
    'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧'},
    'eo': {'name': 'Esperanto', 'native': 'Esperanto', 'flag': '🌍'},
    'et': {'name': 'Estonian', 'native': 'Eesti', 'flag': '🇪🇪'},
    'ee': {'name': 'Ewe', 'native': 'Eʋegbe', 'flag': '🇬🇭'},
    'tl': {'name': 'Filipino', 'native': 'Filipino', 'flag': '🇵🇭'},
    'fi': {'name': 'Finnish', 'native': 'Suomi', 'flag': '🇫🇮'},
    'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
    'fy': {'name': 'Frisian', 'native': 'Frysk', 'flag': '🇳🇱'},
    'gl': {'name': 'Galician', 'native': 'Galego', 'flag': '🇪🇸'},
    'ka': {'name': 'Georgian', 'native': 'ქართული', 'flag': '🇬🇪'},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
    'el': {'name': 'Greek', 'native': 'Ελληνικά', 'flag': '🇬🇷'},
    'gn': {'name': 'Guarani', 'native': "Avañe'ẽ", 'flag': '🇵🇾'},
    'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'flag': '🇮🇳'},
    'ht': {'name': 'Haitian Creole', 'native': 'Kreyòl ayisyen', 'flag': '🇭🇹'},
    'ha': {'name': 'Hausa', 'native': 'Hausa', 'flag': '🇳🇬'},
    'haw': {'name': 'Hawaiian', 'native': 'ʻŌlelo Hawaiʻi', 'flag': '🇺🇸'},
    'he': {'name': 'Hebrew', 'native': 'עברית', 'flag': '🇮🇱', 'rtl': True},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳'},
    'hmn': {'name': 'Hmong', 'native': 'Hmoob', 'flag': '🌏'},
    'hu': {'name': 'Hungarian', 'native': 'Magyar', 'flag': '🇭🇺'},
    'is': {'name': 'Icelandic', 'native': 'Íslenska', 'flag': '🇮🇸'},
    'ig': {'name': 'Igbo', 'native': 'Igbo', 'flag': '🇳🇬'},
    'ilo': {'name': 'Ilocano', 'native': 'Ilokano', 'flag': '🇵🇭'},
    'id': {'name': 'Indonesian', 'native': 'Bahasa Indonesia', 'flag': '🇮🇩'},
    'ga': {'name': 'Irish', 'native': 'Gaeilge', 'flag': '🇮🇪'},
    'it': {'name': 'Italian', 'native': 'Italiano', 'flag': '🇮🇹'},
    'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
    'jv': {'name': 'Javanese', 'native': 'Basa Jawa', 'flag': '🇮🇩'},
    'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'flag': '🇮🇳'},
    'kk': {'name': 'Kazakh', 'native': 'Қазақ', 'flag': '🇰🇿'},
    'km': {'name': 'Khmer', 'native': 'ខ្មែរ', 'flag': '🇰🇭'},
    'rw': {'name': 'Kinyarwanda', 'native': 'Ikinyarwanda', 'flag': '🇷🇼'},
    'gom': {'name': 'Konkani', 'native': 'कोंकणी', 'flag': '🇮🇳'},
    'ko': {'name': 'Korean', 'native': '한국어', 'flag': '🇰🇷'},
    'kri': {'name': 'Krio', 'native': 'Krio', 'flag': '🇸🇱'},
    'ku': {'name': 'Kurdish (Kurmanji)', 'native': 'Kurdî', 'flag': '🇮🇶'},
    'ckb': {'name': 'Kurdish (Sorani)', 'native': 'سۆرانی', 'flag': '🇮🇶', 'rtl': True},
    'ky': {'name': 'Kyrgyz', 'native': 'Кыргызча', 'flag': '🇰🇬'},
    'lo': {'name': 'Lao', 'native': 'ລາວ', 'flag': '🇱🇦'},
    'la': {'name': 'Latin', 'native': 'Latina', 'flag': '🏛️'},
    'lv': {'name': 'Latvian', 'native': 'Latviešu', 'flag': '🇱🇻'},
    'ln': {'name': 'Lingala', 'native': 'Lingála', 'flag': '🇨🇩'},
    'lt': {'name': 'Lithuanian', 'native': 'Lietuvių', 'flag': '🇱🇹'},
    'lg': {'name': 'Luganda', 'native': 'Luganda', 'flag': '🇺🇬'},
    'lb': {'name': 'Luxembourgish', 'native': 'Lëtzebuergesch', 'flag': '🇱🇺'},
    'mk': {'name': 'Macedonian', 'native': 'Македонски', 'flag': '🇲🇰'},
    'mai': {'name': 'Maithili', 'native': 'मैथिली', 'flag': '🇮🇳'},
    'mg': {'name': 'Malagasy', 'native': 'Malagasy', 'flag': '🇲🇬'},
    'ms': {'name': 'Malay', 'native': 'Bahasa Melayu', 'flag': '🇲🇾'},
    'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'flag': '🇮🇳'},
    'mt': {'name': 'Maltese', 'native': 'Malti', 'flag': '🇲🇹'},
    'mi': {'name': 'Maori', 'native': 'Māori', 'flag': '🇳🇿'},
    'mr': {'name': 'Marathi', 'native': 'मराठी', 'flag': '🇮🇳'},
    'mni-Mtei': {'name': 'Meiteilon', 'native': 'ꯃꯤꯇꯩꯂꯣꯟ', 'flag': '🇮🇳'},
    'lus': {'name': 'Mizo', 'native': 'Mizo ṭawng', 'flag': '🇮🇳'},
    'mn': {'name': 'Mongolian', 'native': 'Монгол', 'flag': '🇲🇳'},
    'my': {'name': 'Myanmar (Burmese)', 'native': 'မြန်မာ', 'flag': '🇲🇲'},
    'ne': {'name': 'Nepali', 'native': 'नेपाली', 'flag': '🇳🇵'},
    'no': {'name': 'Norwegian', 'native': 'Norsk', 'flag': '🇳🇴'},
    'or': {'name': 'Odia (Oriya)', 'native': 'ଓଡ଼ିଆ', 'flag': '🇮🇳'},
    'om': {'name': 'Oromo', 'native': 'Afaan Oromoo', 'flag': '🇪🇹'},
    'ps': {'name': 'Pashto', 'native': 'پښتو', 'flag': '🇦🇫', 'rtl': True},
    'fa': {'name': 'Persian', 'native': 'فارسی', 'flag': '🇮🇷', 'rtl': True},
    'pl': {'name': 'Polish', 'native': 'Polski', 'flag': '🇵🇱'},
    'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇧🇷'},
    'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'flag': '🇮🇳'},
    'qu': {'name': 'Quechua', 'native': 'Runasimi', 'flag': '🇵🇪'},
    'ro': {'name': 'Romanian', 'native': 'Română', 'flag': '🇷🇴'},
    'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
    'sm': {'name': 'Samoan', 'native': 'Gagana Samoa', 'flag': '🇼🇸'},
    'sa': {'name': 'Sanskrit', 'native': 'संस्कृतम्', 'flag': '🇮🇳'},
    'gd': {'name': 'Scots Gaelic', 'native': 'Gàidhlig', 'flag': '🏴󠁧󠁢󠁳󠁣󠁴󠁿'},
    'nso': {'name': 'Sepedi', 'native': 'Sepedi', 'flag': '🇿🇦'},
    'sr': {'name': 'Serbian', 'native': 'Српски', 'flag': '🇷🇸'},
    'st': {'name': 'Sesotho', 'native': 'Sesotho', 'flag': '🇱🇸'},
    'sn': {'name': 'Shona', 'native': 'chiShona', 'flag': '🇿🇼'},
    'sd': {'name': 'Sindhi', 'native': 'سنڌي', 'flag': '🇵🇰', 'rtl': True},
    'si': {'name': 'Sinhala', 'native': 'සිංහල', 'flag': '🇱🇰'},
    'sk': {'name': 'Slovak', 'native': 'Slovenčina', 'flag': '🇸🇰'},
    'sl': {'name': 'Slovenian', 'native': 'Slovenščina', 'flag': '🇸🇮'},
    'so': {'name': 'Somali', 'native': 'Soomaali', 'flag': '🇸🇴'},
    'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
    'su': {'name': 'Sundanese', 'native': 'Basa Sunda', 'flag': '🇮🇩'},
    'sw': {'name': 'Swahili', 'native': 'Kiswahili', 'flag': '🇰🇪'},
    'sv': {'name': 'Swedish', 'native': 'Svenska', 'flag': '🇸🇪'},
    'tg': {'name': 'Tajik', 'native': 'Тоҷикӣ', 'flag': '🇹🇯'},
    'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳'},
    'tt': {'name': 'Tatar', 'native': 'Татар', 'flag': '🇷🇺'},
    'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳'},
    'th': {'name': 'Thai', 'native': 'ไทย', 'flag': '🇹🇭'},
    'ti': {'name': 'Tigrinya', 'native': 'ትግርኛ', 'flag': '🇪🇷'},
    'ts': {'name': 'Tsonga', 'native': 'Xitsonga', 'flag': '🇿🇦'},
    'tr': {'name': 'Turkish', 'native': 'Türkçe', 'flag': '🇹🇷'},
    'tk': {'name': 'Turkmen', 'native': 'Türkmen', 'flag': '🇹🇲'},
    'ak': {'name': 'Twi', 'native': 'Twi', 'flag': '🇬🇭'},
    'uk': {'name': 'Ukrainian', 'native': 'Українська', 'flag': '🇺🇦'},
    'ur': {'name': 'Urdu', 'native': 'اردو', 'flag': '🇵🇰', 'rtl': True},
    'ug': {'name': 'Uyghur', 'native': 'ئۇيغۇرچە', 'flag': '🇨🇳', 'rtl': True},
    'uz': {'name': 'Uzbek', 'native': "O'zbek", 'flag': '🇺🇿'},
    'vi': {'name': 'Vietnamese', 'native': 'Tiếng Việt', 'flag': '🇻🇳'},
    'cy': {'name': 'Welsh', 'native': 'Cymraeg', 'flag': '🏴󠁧󠁢󠁷󠁬󠁳󠁿'},
    'xh': {'name': 'Xhosa', 'native': 'isiXhosa', 'flag': '🇿🇦'},
    'yi': {'name': 'Yiddish', 'native': 'ייִדיש', 'flag': '🇮🇱', 'rtl': True},
    'yo': {'name': 'Yoruba', 'native': 'Yorùbá', 'flag': '🇳🇬'},
    'zu': {'name': 'Zulu', 'native': 'isiZulu', 'flag': '🇿🇦'},
    'fil': {'name': 'Filipino', 'native': 'Filipino', 'flag': '🇵🇭'},
    'yue': {'name': 'Cantonese', 'native': '粵語', 'flag': '🇭🇰'},
    'fj': {'name': 'Fijian', 'native': 'Vosa Vakaviti', 'flag': '🇫🇯'},
}

# Skip English (source language)
SKIP_LANGUAGES = {'en'}

def flatten_json(obj: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, str]:
    """Flatten nested JSON to dot-notation keys."""
    items = []
    for k, v in obj.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep).items())
        else:
            items.append((new_key, str(v)))
    return dict(items)

def unflatten_json(flat_dict: Dict[str, str], sep: str = '.') -> Dict:
    """Convert flat dot-notation dict back to nested structure."""
    result = {}
    for key, value in flat_dict.items():
        parts = key.split(sep)
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result

def translate_batch(texts: List[str], target_lang: str, source_lang: str = 'en') -> List[str]:
    """Translate a batch of texts using Google Translate API with proper batching."""
    if not texts:
        return []
    
    results = []
    
    # Split into batches of MAX_SEGMENTS
    for i in range(0, len(texts), MAX_SEGMENTS):
        batch = texts[i:i + MAX_SEGMENTS]
        
        try:
            response = requests.post(
                TRANSLATE_URL,
                params={'key': API_KEY},
                json={
                    'q': batch,
                    'target': target_lang,
                    'source': source_lang,
                    'format': 'text'
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                translations = data.get('data', {}).get('translations', [])
                batch_results = [t.get('translatedText', batch[j]) for j, t in enumerate(translations)]
                results.extend(batch_results)
            else:
                print(f"    API error (batch {i//MAX_SEGMENTS + 1}): {response.status_code}")
                results.extend(batch)  # Keep original on error
                
        except Exception as e:
            print(f"    Exception (batch {i//MAX_SEGMENTS + 1}): {e}")
            results.extend(batch)  # Keep original on error
        
        # Small delay between batches to avoid rate limiting
        if i + MAX_SEGMENTS < len(texts):
            time.sleep(0.2)
    
    return results

def translate_language(en_data: Dict, target_lang: str) -> Dict:
    """Translate all strings from English to target language."""
    flat_en = flatten_json(en_data)
    keys = list(flat_en.keys())
    values = list(flat_en.values())
    
    num_batches = (len(values) + MAX_SEGMENTS - 1) // MAX_SEGMENTS
    print(f"  Translating {len(values)} strings in {num_batches} batches...")
    
    translated_values = translate_batch(values, target_lang)
    translated_flat = dict(zip(keys, translated_values))
    
    return unflatten_json(translated_flat)

def main():
    """Main translation function."""
    print("Loading English source file...")
    with open(EN_FILE, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    total_keys = len(flatten_json(en_data))
    print(f"Loaded {total_keys} translation keys")
    
    languages_to_translate = [
        lang for lang in ALL_LANGUAGES.keys() 
        if lang not in SKIP_LANGUAGES
    ]
    
    print(f"\nTranslating to {len(languages_to_translate)} languages...")
    
    successful = []
    failed = []
    
    for i, lang_code in enumerate(languages_to_translate, 1):
        lang_info = ALL_LANGUAGES[lang_code]
        
        # Handle special characters in filename
        safe_code = lang_code.replace('-', '_')
        output_file = LOCALES_DIR / f"{safe_code}.json"
        
        print(f"[{i}/{len(languages_to_translate)}] {lang_code} ({lang_info['name']})...")
        
        try:
            translated = translate_language(en_data, lang_code)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(translated, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ Saved to {output_file.name}")
            successful.append(lang_code)
            
            # Delay between languages
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed.append(lang_code)
    
    print(f"\n{'='*50}")
    print(f"Translation complete!")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print(f"  Failed languages: {', '.join(failed)}")
    
    return successful, failed

if __name__ == "__main__":
    main()
