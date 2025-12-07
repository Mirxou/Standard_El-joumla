"""
Lightweight Internationalization (i18n) for API
"""
import json
from typing import Optional, Dict, List
from pathlib import Path


class I18n:
    """Simple i18n service for API responses"""
    
    def __init__(self, locales_dir: str = "locales", default_locale: str = "ar"):
        self.locales_dir = Path(locales_dir)
        self._messages: Dict[str, Dict[str, str]] = {}
        self._default_locale = default_locale
        self._load_locales()
    
    def _load_locales(self):
        """Load locale JSON files"""
        if not self.locales_dir.exists():
            return
        
        for locale_file in self.locales_dir.glob("*.json"):
            locale_code = locale_file.stem
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self._messages[locale_code] = json.load(f)
            except Exception:
                pass
    
    def get_message(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """Get translated message"""
        locale = locale or self._default_locale
        
        # Try requested locale
        if locale in self._messages and key in self._messages[locale]:
            message = self._messages[locale][key]
            if kwargs:
                return message.format(**kwargs)
            return message
        
        # Fallback to default
        if self._default_locale in self._messages and key in self._messages[self._default_locale]:
            message = self._messages[self._default_locale][key]
            if kwargs:
                return message.format(**kwargs)
            return message
        
        return key
    
    def negotiate_locale(self, accept_language: Optional[str] = None, query_locale: Optional[str] = None) -> str:
        """Negotiate best locale"""
        if query_locale and query_locale in self._messages:
            return query_locale
        
        if accept_language:
            for lang_part in accept_language.split(","):
                lang = lang_part.split(";")[0].strip().split("-")[0]
                if lang in self._messages:
                    return lang
        
        return self._default_locale
    
    def get_available_locales(self) -> List[str]:
        """Get list of available locales"""
        return list(self._messages.keys())
    
    def has_locale(self, locale: str) -> bool:
        """Check if locale is available"""
        return locale in self._messages
    
    def get_all_messages(self, locale: Optional[str] = None) -> Dict[str, str]:
        """Get all messages for a locale"""
        locale = locale or self._default_locale
        return self._messages.get(locale, {})
    
    def format_message(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        Get and format a message with variables
        
        This is a convenience method that combines get_message with formatting.
        Useful for dynamic messages with multiple variables.
        
        Args:
            key: Translation key
            locale: Locale code (defaults to default locale)
            **kwargs: Variables to format into the message
            
        Returns:
            Formatted translated message
        """
        return self.get_message(key, locale=locale, **kwargs)
    
    def get_plural(self, key_singular: str, key_plural: str, count: int, locale: Optional[str] = None) -> str:
        """
        Get plural form of a message based on count
        
        Args:
            key_singular: Key for singular form
            key_plural: Key for plural form
            count: Number to determine plural form
            locale: Locale code
            
        Returns:
            Appropriate form based on count
        """
        if count == 1:
            return self.get_message(key_singular, locale=locale)
        return self.get_message(key_plural, locale=locale)
