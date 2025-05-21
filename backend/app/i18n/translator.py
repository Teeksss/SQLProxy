"""
Internationalization (I18N) module for SQL Proxy

This module provides language translation services for the SQL Proxy
system, supporting multiple languages for the UI and error messages.

Last updated: 2025-05-20 10:30:03
Updated by: Teeksss
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

class Translator:
    """
    Translation service for internationalization
    
    Provides translations for UI text and error messages in multiple languages.
    """
    
    def __init__(self):
        """Initialize the translator"""
        self.translations = {}
        self.default_language = settings.DEFAULT_LANGUAGE
        self.available_languages = []
        self.lock = threading.RLock()
        
        # Load translations
        self.translations_dir = Path(settings.TRANSLATIONS_DIR)
        self._load_translations()
        
        logger.info(f"Translator initialized with {len(self.available_languages)} languages")
    
    def _load_translations(self):
        """Load all translation files"""
        try:
            if not self.translations_dir.exists():
                logger.warning(f"Translations directory not found: {self.translations_dir}")
                return
            
            with self.lock:
                # Reset translations
                self.translations = {}
                self.available_languages = []
                
                # Load all JSON files in the translations directory
                for file_path in self.translations_dir.glob("*.json"):
                    language_code = file_path.stem
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            translations = json.load(f)
                            
                            # Store translations
                            self.translations[language_code] = translations
                            self.available_languages.append(language_code)
                            
                            logger.debug(f"Loaded translations for {language_code}: {len(translations)} entries")
                    except Exception as e:
                        logger.error(f"Error loading translations for {language_code}: {str(e)}")
                
                # Ensure default language is available
                if self.default_language not in self.available_languages:
                    logger.warning(f"Default language {self.default_language} not available. Using first available language.")
                    if self.available_languages:
                        self.default_language = self.available_languages[0]
                    else:
                        # Create empty translations for default language
                        self.translations[self.default_language] = {}
                        self.available_languages.append(self.default_language)
                
                logger.info(f"Loaded translations for {len(self.available_languages)} languages: {', '.join(self.available_languages)}")
                
        except Exception as e:
            logger.error(f"Error loading translations: {str(e)}")
    
    def translate(
        self, 
        key: str, 
        language: Optional[str] = None, 
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Translate a message key to the specified language
        
        Args:
            key: Message key to translate
            language: Target language code (defaults to default language)
            params: Optional parameters for string formatting
            
        Returns:
            Translated string
        """
        # Determine language to use
        lang = language if language in self.available_languages else self.default_language
        
        with self.lock:
            # Get translation
            translation = self.translations.get(lang, {}).get(key)
            
            # Fall back to default language if translation not found
            if translation is None and lang != self.default_language:
                translation = self.translations.get(self.default_language, {}).get(key)
            
            # Fall back to key if translation still not found
            if translation is None:
                translation = key
            
            # Apply string formatting if params provided
            if params:
                try:
                    translation = translation.format(**params)
                except Exception as e:
                    logger.error(f"Error formatting translation for key '{key}': {str(e)}")
            
            return translation
    
    def get_language_name(self, language_code: str) -> str:
        """
        Get the display name of a language
        
        Args:
            language_code: Language code
            
        Returns:
            Language display name
        """
        with self.lock:
            # Check if language exists
            if language_code not in self.available_languages:
                return language_code
            
            # Get language name from translations
            language_name = self.translations.get(language_code, {}).get("language_name")
            
            if language_name:
                return language_name
            else:
                return language_code
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        Get list of available languages
        
        Returns:
            List of dictionaries with language code and name
        """
        with self.lock:
            languages = []
            
            for lang_code in self.available_languages:
                languages.append({
                    "code": lang_code,
                    "name": self.get_language_name(lang_code)
                })
            
            return languages
    
    def reload_translations(self):
        """Reload all translation files"""
        self._load_translations()
    
    def add_translation(
        self,
        language: str,
        key: str,
        value: str,
        persist: bool = False
    ) -> bool:
        """
        Add or update a translation
        
        Args:
            language: Language code
            key: Translation key
            value: Translated value
            persist: Whether to persist to file
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            # Ensure language exists
            if language not in self.translations:
                self.translations[language] = {}
                
                if language not in self.available_languages:
                    self.available_languages.append(language)
            
            # Add translation
            self.translations[language][key] = value
            
            # Persist to file if requested
            if persist:
                try:
                    file_path = self.translations_dir / f"{language}.json"
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Persisted translation for language '{language}', key '{key}'")
                    return True
                except Exception as e:
                    logger.error(f"Error persisting translation: {str(e)}")
                    return False
            
            return True
    
    def remove_translation(
        self,
        language: str,
        key: str,
        persist: bool = False
    ) -> bool:
        """
        Remove a translation
        
        Args:
            language: Language code
            key: Translation key
            persist: Whether to persist to file
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            # Check if language and key exist
            if language not in self.translations or key not in self.translations[language]:
                return False
            
            # Remove translation
            del self.translations[language][key]
            
            # Persist to file if requested
            if persist:
                try:
                    file_path = self.translations_dir / f"{language}.json"
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Persisted removal of translation for language '{language}', key '{key}'")
                    return True
                except Exception as e:
                    logger.error(f"Error persisting translation removal: {str(e)}")
                    return False
            
            return True
    
    def extract_translation_keys(self, source_dirs: List[str]) -> Dict[str, List[str]]:
        """
        Extract translation keys from source code
        
        Args:
            source_dirs: List of source directories to scan
            
        Returns:
            Dictionary of files and their translation keys
        """
        keys_by_file = {}
        translate_pattern = r't\([\'"]([^\'"]+)[\'"]\)'
        
        for source_dir in source_dirs:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Find all translate function calls
                            import re
                            matches = re.findall(translate_pattern, content)
                            
                            if matches:
                                keys_by_file[file_path] = matches
                        except Exception as e:
                            logger.error(f"Error scanning file {file_path}: {str(e)}")
        
        return keys_by_file
    
    def generate_template(self, keys: List[str]) -> Dict[str, str]:
        """
        Generate a translation template with empty values
        
        Args:
            keys: List of translation keys
            
        Returns:
            Dictionary with keys and empty values
        """
        template = {}
        
        for key in keys:
            template[key] = ""
        
        return template

# Create a singleton instance
translator = Translator()

# Son güncelleme: 2025-05-20 10:30:03
# Güncelleyen: Teeksss