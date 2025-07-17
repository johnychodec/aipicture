#######
# author: @jan_hru
# date: 2024-04-11
# version: 1.0.0
# description: This script generates an image based on a Bible quote and sends it to a Telegram channel.
#######

"""
Bible Image Generator

This script automates the process of creating visual interpretations of Bible quotes:
1. Fetches a daily Bible quote from bible21.cz
2. Uses Groq AI to analyze the quote and create a detailed image generation prompt
3. Uses Together AI to generate an image based on the prompt
4. Sends the image with the quote as caption to a Telegram channel

Configuration:
- WEATHER: Set to 'true' or 'false' to enable/disable weather data fetching (default: true)
- When enabled, weather data is used to enhance the image generation prompt
- When disabled, images are generated without weather context

Dependencies:
- together: For AI-powered image generation
- python-dotenv: For environment variable management
- requests: For HTTP requests
- beautifulsoup4: For web scraping
- python-telegram-bot: For Telegram bot integration
- Pillow: For image processing
- groq: For prompt enhancement
"""

import os
import logging
import requests
import time
from bs4 import BeautifulSoup as bs
from datetime import datetime
from typing import Optional, Dict, Union
from dotenv import load_dotenv
from together import Together
from telegram import Bot
import asyncio
from groq import Groq
import random
import io
from PIL import Image
import tweepy
from abc import ABC, abstractmethod

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bible_image_generator.log'),
        logging.StreamHandler()
    ]
)

# Debug logging for environment variables
logging.info(f"Raw PRODUCTION value from env: {os.getenv('PRODUCTION')}")

class QuoteSource(ABC):
    """Abstract base class for quote sources."""
    
    @abstractmethod
    def fetch_quote(self) -> Optional[str]:
        """Fetch a quote from the source."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate source configuration."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the quote source."""
        pass

class Bible21QuoteSource(QuoteSource):
    """Quote source for bible21.cz."""
    
    def __init__(self):
        self.url = Config.BIBLE21_URL
        self.quote_class = Config.BIBLE21_QUOTE_CLASS
    
    def debug_quote_element(self) -> None:
        """
        Debug function to help identify the current quote element class.
        
        This method:
        1. Fetches the Bible website
        2. Logs all span elements and their classes
        3. Helps identify the current quote element class when it changes
        """
        try:
            response = requests.get(self.url, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = bs(response.text, 'html.parser')
            
            # Find all span elements
            spans = soup.find_all('span')
            logging.info(f"Found {len(spans)} span elements on the page")
            
            # Log each span with its class
            for span in spans:
                if span.get('class'):
                    logging.info(f"Span class: {span.get('class')}")
                    logging.info(f"Span text: {span.get_text().strip()[:100]}...")
            
            # Try to find the quote using the current class
            quote_element = soup.find('span', attrs={'class': self.quote_class})
            if quote_element:
                logging.info(f"Quote found with current class '{self.quote_class}': {quote_element.get_text().strip()}")
            else:
                logging.warning(f"Quote NOT found with current class '{self.quote_class}'")
                
        except Exception as e:
            logging.error(f"Error in debug_quote_element: {str(e)}")
    
    def fetch_quote(self) -> Optional[str]:
        """Fetch the daily quote from bible21.cz."""
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.get(self.url, timeout=10)
                response.encoding = 'utf-8'
                response.raise_for_status()
                
                soup = bs(response.text, 'html.parser')
                quote_element = soup.find('span', attrs={'class': self.quote_class})
                
                if quote_element:
                    quote_text = quote_element.get_text().strip()
                    logging.info(f"Successfully fetched quote from bible21.cz: {quote_text[:100]}...")
                    return quote_text
                else:
                    logging.warning(f"Quote element with class '{self.quote_class}' not found on the page")
                    if attempt == Config.MAX_RETRIES - 1:
                        self.debug_quote_element()
                    return None
                    
            except requests.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logging.error("Max retries reached. Could not fetch Bible quote")
                    return None
    
    def validate_config(self) -> bool:
        """Validate Bible21 configuration."""
        if not self.url:
            logging.error("BIBLE21_URL is not set")
            return False
        if not self.quote_class:
            logging.error("BIBLE21_QUOTE_CLASS is not set")
            return False
        return True
    
    def get_source_name(self) -> str:
        return "bible21"

class DailyVersesQuoteSource(QuoteSource):
    """Quote source for dailyverses.net."""
    
    def __init__(self):
        self.url = Config.DAILY_VERSES_URL
        self.quote_class = Config.DAILY_VERSES_QUOTE_CLASS
    
    def debug_quote_element(self) -> None:
        """
        Debug function to help identify the current quote element class.
        
        This method:
        1. Fetches the Daily Verses website
        2. Logs all div elements with class b1
        3. Helps identify the current quote element structure
        """
        try:
            response = requests.get(self.url, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = bs(response.text, 'html.parser')
            
            # Find all div elements with class b1
            quote_divs = soup.find_all('div', attrs={'class': 'b1'})
            
            logging.info(f"Found {len(quote_divs)} div elements with class 'b1' on the page")
            
            # Log each quote div with its content
            for i, div in enumerate(quote_divs):
                # Find the span with class v1
                quote_span = div.find('span', attrs={'class': 'v1'})
                if quote_span:
                    quote_text = quote_span.get_text().strip()
                    logging.info(f"Quote div {i+1}: Text: {quote_text[:100]}...")
                
                # Find the reference div with class vr
                ref_div = div.find('div', attrs={'class': 'vr'})
                if ref_div:
                    ref_link = ref_div.find('a', attrs={'class': 'vc'})
                    if ref_link:
                        ref_text = ref_link.get_text().strip()
                        logging.info(f"Quote div {i+1}: Reference: {ref_text}")
            
            # Try to find the quote using the current class
            quote_element = soup.find('span', attrs={'class': self.quote_class})
            if quote_element:
                logging.info(f"Quote found with current class '{self.quote_class}': {quote_element.get_text().strip()}")
            else:
                logging.warning(f"Quote NOT found with current class '{self.quote_class}'")
                
        except Exception as e:
            logging.error(f"Error in debug_quote_element: {str(e)}")
    
    def fetch_quote(self) -> Optional[str]:
        """Fetch the daily quote from dailyverses.net."""
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.get(self.url, timeout=10)
                response.encoding = 'utf-8'
                response.raise_for_status()
                
                soup = bs(response.text, 'html.parser')
                quote_div = soup.find('div', attrs={'class': 'b1'})
                
                if quote_div:
                    # Find the verse text in span.v1
                    verse_span = quote_div.find('span', attrs={'class': 'v1'})
                    if verse_span:
                        verse_text = verse_span.get_text().strip()
                        
                        # Find the reference div with class vr
                        ref_div = quote_div.find('div', attrs={'class': 'vr'})
                        if ref_div:
                            ref_link = ref_div.find('a', attrs={'class': 'vc'})
                            if ref_link:
                                ref_text = ref_link.get_text().strip()
                                quote_text = f"{verse_text} ({ref_text})"
                                logging.info(f"Successfully fetched quote from dailyverses.net: {quote_text[:100]}...")
                                return quote_text
                        logging.info(f"Successfully fetched quote from dailyverses.net: {verse_text[:100]}...")
                        return verse_text
                else:
                    logging.warning("Quote element not found on the page")
                    if attempt == Config.MAX_RETRIES - 1:
                        self.debug_quote_element()
                    return None
                    
            except requests.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logging.error("Max retries reached. Could not fetch Daily Verses quote")
                    return None
    
    def validate_config(self) -> bool:
        """Validate Daily Verses configuration."""
        if not self.url:
            logging.error("DAILY_VERSES_URL is not set")
            return False
        if not self.quote_class:
            logging.error("DAILY_VERSES_QUOTE_CLASS is not set")
            return False
        return True
    
    def get_source_name(self) -> str:
        return "dailyverses"

class QuoteFetcher:
    """Class to handle quote fetching from multiple sources."""
    
    def __init__(self):
        self.sources: Dict[str, QuoteSource] = {
            'bible21': Bible21QuoteSource(),
            'dailyverses': DailyVersesQuoteSource()
        }
        self.current_source = Config.QUOTE_SOURCE
        self.fallback_source = Config.FALLBACK_SOURCE
        
        # Validate current source
        if self.current_source not in self.sources:
            logging.error(f"Invalid quote source: {self.current_source}")
            self.current_source = 'bible21'  # Default to bible21
            
        # Validate fallback source
        if self.fallback_source not in self.sources:
            logging.error(f"Invalid fallback source: {self.fallback_source}")
            self.fallback_source = 'bible21'  # Default to bible21
    
    def fetch_quote(self) -> Optional[str]:
        """Fetch a quote from the current source with fallback."""
        try:
            # Try current source
            quote = self.sources[self.current_source].fetch_quote()
            if quote:
                logging.info(f"Successfully fetched quote from {self.current_source}")
                return quote
                
            # Try fallback source if different from current
            if self.fallback_source != self.current_source:
                logging.info(f"Trying fallback source: {self.fallback_source}")
                quote = self.sources[self.fallback_source].fetch_quote()
                if quote:
                    logging.info(f"Successfully fetched quote from fallback source: {self.fallback_source}")
                    return quote
                    
            logging.error("Failed to fetch quote from both sources")
            return None
            
        except Exception as e:
            logging.error(f"Error fetching quote: {str(e)}")
            return None

class Config:
    """Configuration class to store all constants and settings."""
    
    @classmethod
    def reload_env(cls):
        """Reload environment variables from .env file."""
        load_dotenv(override=True)
        logging.info(f"Environment variables reloaded. Raw PRODUCTION value: {os.getenv('PRODUCTION')}")
    
    @classmethod
    def is_production(cls) -> bool:
        """Get current production mode status."""
        return str(os.getenv('PRODUCTION', 'false')).strip().lower() == 'true'
    
    @classmethod
    def is_weather_enabled(cls) -> bool:
        """Get current weather fetching status."""
        return str(os.getenv('WEATHER', 'true')).strip().lower() not in ('false', '0', 'no', 'n')
    
    @classmethod
    def is_twitter_enabled(cls) -> bool:
        """Get current Twitter posting status."""
        return str(os.getenv('TWITTER', 'true')).strip().lower() not in ('false', '0', 'no', 'n')
    
    @classmethod
    def get_telegram_token(cls) -> Optional[str]:
        """Get appropriate Telegram token based on production mode."""
        return cls.TELEGRAM_TOKEN if cls.is_production() else cls.TELEGRAM_TEST_TOKEN
    
    @classmethod
    def get_telegram_chat_id(cls) -> Optional[str]:
        """Get appropriate Telegram chat ID based on production mode."""
        return cls.TELEGRAM_CHAT_ID if cls.is_production() else cls.TELEGRAM_TEST_CHAT_ID
    
    @classmethod
    def get_ai_service(cls) -> str:
        """Get the current AI service to use."""
        return str(os.getenv('AI_SERVICE', 'groq')).strip().lower()
    
    @classmethod
    def get_image_service(cls) -> str:
        """Get the current image generation service to use."""
        return str(os.getenv('IMAGE_SERVICE', 'together')).strip().lower()
    
    @classmethod
    def get_prompt_length_limit(cls) -> int:
        """Get the prompt length limit for Venice.ai."""
        return int(os.getenv('PROMPT_LENGTH_LIMIT', '1500'))
    
    # Static configuration values
    BIBLE_URL = os.getenv('BIBLE_URL', 'https://bible21.cz')
    QUOTE_CLASS = os.getenv('QUOTE_CLASS', 'daily-word__quote')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_TEST_TOKEN = os.getenv('TELEGRAM_TEST_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    TELEGRAM_TEST_CHAT_ID = os.getenv('TELEGRAM_TEST_CHAT_ID')
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    VENICE_API_KEY = os.getenv('VENICE_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    WEATHER_PLACE_ID = os.getenv('WEATHER_PLACE_ID', 'kutna-hora')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))
    
    # Twitter configuration
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
    TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
    
    TEST_QUOTE = "Ti, kteří se vydávají na lodích na moře, kdo konají dílo na nesmírných vodách, spatřili Hospodinovy skutky, jeho divy na hlubině.(Ž107:23-24)"

    # Quote source configuration (hardcoded)
    QUOTE_SOURCE = 'bible21'  # Primary quote source
    FALLBACK_SOURCE = 'dailyverses'  # Fallback quote source
    BIBLE21_URL = 'https://bible21.cz'
    BIBLE21_QUOTE_CLASS = 'daily-word__quote'
    DAILY_VERSES_URL = 'https://dailyverses.net/cs'    
    DAILY_VERSES_QUOTE_CLASS = 'v1'
    
    @classmethod
    def validate_telegram_config(cls) -> bool:
        """Validate Telegram configuration settings."""
        if cls.is_production():
            if not cls.TELEGRAM_TOKEN:
                logging.error("TELEGRAM_TOKEN is not set for production mode")
                return False
            if not cls.TELEGRAM_CHAT_ID:
                logging.error("TELEGRAM_CHAT_ID is not set for production mode")
                return False
        else:
            if not cls.TELEGRAM_TEST_TOKEN:
                logging.error("TELEGRAM_TEST_TOKEN is not set for test mode")
                return False
            if not cls.TELEGRAM_TEST_CHAT_ID:
                logging.error("TELEGRAM_TEST_CHAT_ID is not set for test mode")
                return False
            
        logging.info(f"Telegram configuration validated. Production mode: {cls.is_production()}")
        if cls.is_production():
            logging.info(f"Using production token and chat ID: {cls.TELEGRAM_CHAT_ID}")
        else:
            logging.info(f"Using test token and chat ID: {cls.TELEGRAM_TEST_CHAT_ID}")
        return True

    @classmethod
    def validate_twitter_config(cls) -> bool:
        """Validate Twitter configuration settings."""
        if not cls.is_twitter_enabled():
            logging.info("Twitter posting is disabled")
            return True
            
        required_keys = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET',
            'TWITTER_BEARER_TOKEN'
        ]
        
        for key in required_keys:
            if not getattr(cls, key):
                logging.error(f"{key} is not set")
                return False
                
        logging.info("Twitter configuration validated")
        return True

    @classmethod
    def validate_ai_config(cls) -> bool:
        """Validate AI service configuration settings."""
        ai_service = cls.get_ai_service()
        image_service = cls.get_image_service()
        
        # Validate AI service for prompt generation
        if ai_service == 'groq':
            if not cls.GROQ_API_KEY:
                logging.error("GROQ_API_KEY is not set")
                return False
        elif ai_service == 'venice':
            if not cls.VENICE_API_KEY:
                logging.error("VENICE_API_KEY is not set")
                return False
        else:
            logging.error(f"Invalid AI service: {ai_service}")
            return False
        
        # Validate image generation service
        if image_service == 'together':
            if not cls.TOGETHER_API_KEY:
                logging.error("TOGETHER_API_KEY is not set")
                return False
        elif image_service == 'venice':
            if not cls.VENICE_API_KEY:
                logging.error("VENICE_API_KEY is not set for image generation")
                return False
        else:
            logging.error(f"Invalid image service: {image_service}")
            return False
            
        # Validate prompt length limit configuration
        prompt_limit = cls.get_prompt_length_limit()
        if prompt_limit <= 0 or prompt_limit > 2000:
            logging.warning(f"PROMPT_LENGTH_LIMIT ({prompt_limit}) seems unusual. Expected value is 1500 for Venice.ai")
        
        logging.info(f"AI configuration validated. Using AI service: {ai_service}, Image service: {image_service}")
        return True

# Dictionary of modern art styles for image generation
IMAGE_ART = {
    'impressionism': {
        'description': 'Capturing fleeting moments with visible brushstrokes and emphasis on light effects',
        'characteristics': ['loose brushwork', 'natural light', 'outdoor scenes', 'vibrant colors', 'captured moments'],
        'weight': 9,  # Highest weight - works excellently with nature and light themes
        'shortcut': 'imp'
    },
    'post_impressionism': {
        'description': 'Emotional and symbolic use of color and form beyond natural representation',
        'characteristics': ['bold colors', 'expressive brushstrokes', 'symbolic elements', 'emotional depth', 'structured composition'],
        'weight': 10,  # Very high weight - excellent for emotional and symbolic content
        'shortcut': 'pim'
    },
    'fauvism': {
        'description': 'Bold, non-naturalistic colors and simplified forms',
        'characteristics': ['intense colors', 'simplified forms', 'expressive brushwork', 'emotional impact', 'non-naturalistic palette'],
        'weight': 5,  # High weight - strong emotional impact
        'shortcut': 'fau'
    },
    'expressionism': {
        'description': 'Distorted forms and intense colors to express emotional experience',
        'characteristics': ['distorted forms', 'intense colors', 'emotional expression', 'subjective perspective', 'dramatic contrast'],
        'weight': 9,  # High weight - good for emotional content
        'shortcut': 'exp'
    },
    'cubism': {
        'description': 'Geometric fragmentation and multiple perspectives',
        'characteristics': ['geometric forms', 'multiple viewpoints', 'fragmented space', 'analytical approach', 'overlapping planes'],
        'weight': 8,  # Medium-high weight - interesting for abstract concepts
        'shortcut': 'cub'
    },
    'futurism': {
        'description': 'Dynamic movement and modern technology representation',
        'characteristics': ['dynamic lines', 'speed elements', 'technological themes', 'motion blur', 'modern subjects'],
        'weight': 4,  # Lower weight - less suitable for spiritual content
        'shortcut': 'fut'
    },
    'dada': {
        'description': 'Anti-art movement with absurd and irrational elements',
        'characteristics': ['absurd elements', 'found objects', 'irrational composition', 'challenging norms', 'experimental techniques'],
        'weight': 8,  # Low weight - might be too abstract
        'shortcut': 'dad'
    },
    'surrealism': {
        'description': 'Dreamlike imagery and unconscious mind exploration',
        'characteristics': ['dreamlike elements', 'unusual juxtapositions', 'symbolic imagery', 'fantastical scenes', 'psychological depth'],
        'weight': 4,  # Low weight - great for spiritual and symbolic content, but i dont like it
        'shortcut': 'sur'
    },
    'abstract_expressionism': {
        'description': 'Spontaneous, emotional expression through abstract forms',
        'characteristics': ['gestural brushstrokes', 'emotional intensity', 'abstract forms', 'spontaneous creation', 'large scale'],
        'weight': 7,  # High weight - good for emotional expression
        'shortcut': 'aex'
    },    
    'minimalism': {
        'description': 'Reduced to essential elements and geometric forms',
        'characteristics': ['simple forms', 'clean lines', 'limited palette', 'reduced elements', 'precise composition'],
        'weight': 7,  # Medium-high weight - good for clear messages
        'shortcut': 'min'
    },    
    'mixed_media': {
        'description': 'Combination of various materials and techniques',
        'characteristics': ['diverse materials', 'layered elements', 'textural variety', 'experimental combinations', 'multimedia approach'],
        'weight': 8,  # Medium weight - versatile but might be too complex
        'shortcut': 'mix'
    },    
    'street_art': {
        'description': 'Urban expression and public space intervention',
        'characteristics': ['urban elements', 'bold graphics', 'public space', 'social commentary', 'graffiti techniques'],
        'weight': 4,  # Low weight - might be too modern
        'shortcut': 'str'
    },
    'deconstructivist_art': {
        'description': 'Deconstructivist art is a style that deconstructs traditional forms and structures, often using geometric shapes and lines.',
        'characteristics': ['geometric shapes', 'lines', 'deconstruction', 'abstraction', 'modernism'],
        'weight': 8,  # Medium weight - balanced approach
        'shortcut': 'dec'
    }
    
    
}

class WeightedStyleSelector:
    """Class to handle weighted random selection of art styles."""
    
    def __init__(self, styles: dict):
        """Initialize the selector with a dictionary of styles.
        
        Args:
            styles: Dictionary of art styles with their weights
        """
        self.styles = styles
        self.total_weight = sum(style['weight'] for style in styles.values())
        logging.info(f"Initialized WeightedStyleSelector with total weight: {self.total_weight}")
        
    def select_style(self) -> tuple[str, dict]:
        """Select a random style based on weights.
        
        Returns:
            tuple: (style_name, style_dict)
        """
        if not self.styles:
            raise ValueError("No styles available for selection")
            
        r = random.uniform(0, self.total_weight)
        current = 0
        
        for style_name, style in self.styles.items():
            current += style['weight']
            if r <= current:
                logging.info(f"Selected style '{style_name}' with weight {style['weight']}")
                return style_name, style
                
        # Fallback to last style if something goes wrong
        last_style = list(self.styles.items())[-1]
        logging.warning(f"Falling back to last style: {last_style[0]}")
        return last_style

class WeatherIconMapper:
    """Class to map Meteosource weather codes to emoji icons."""
    
    # Mapping of Meteosource weather codes to emoji icons
    WEATHER_ICONS = {
        # Clear and sunny conditions
        'not_available': '❓',
        'sunny': '☀️',
        'mostly_sunny': '🌤️',
        'partly_sunny': '⛅',
        'mostly_cloudy': '🌥️',
        'cloudy': '☁️',
        'overcast': '☁️',
        'overcast_with_low_clouds': '☁️',
        
        # Fog and mist
        'fog': '🌫️',
        
        # Rain conditions
        'light_rain': '🌦️',
        'rain': '🌧️',
        'psbl_rain': '🌦️',
        'rain_shower': '🌧️',
        'thunderstorm': '⛈️',
        'local_thunderstorms': '⛈️',
        
        # Snow conditions
        'light_snow': '🌨️',
        'snow': '🌨️',
        'possible_snow': '🌨️',
        'snow_shower': '🌨️',
        'rain_and_snow': '🌨️',
        'psbl_rain_and_snow': '🌨️',
        'freezing_rain': '🌨️',
        'possible_freezing_rain': '🌨️',
        'hail': '🌨️',
        
        # Night conditions
        'clear_night': '🌙',
        'mostly_clear_night': '🌙',
        'partly_clear_night': '🌙',
        'mostly_cloudy_night': '☁️',
        'cloudy_night': '☁️',
        'overcast_with_low_clouds_night': '☁️',
        'rain_shower_night': '🌧️',
        'local_thunderstorms_night': '⛈️',
        'snow_shower_night': '🌨️',
        'rain_and_snow_night': '🌨️',
        'possible_freezing_rain_night': '🌨️',
        
        # Default/unknown conditions
        'default': '❓'
    }
    
    @classmethod
    def get_icon(cls, weather_code: str) -> str:
        """Get the appropriate emoji icon for a given weather code.
        
        Args:
            weather_code: The Meteosource weather code
            
        Returns:
            str: The corresponding emoji icon, or default icon if code not found
        """
        # Try to find exact match first
        if weather_code in cls.WEATHER_ICONS:
            return cls.WEATHER_ICONS[weather_code]
                
        # Return default icon if no match found
        logging.warning(f"No weather icon found for code: {weather_code}, using default")
        return cls.WEATHER_ICONS['default']

class WeatherAPI:
    """Class to handle weather data fetching from Meteosource API."""
    
    @staticmethod
    def fetch_weather() -> Optional[dict]:
        """Fetch current weather data for the specified location."""
        if not Config.is_weather_enabled():
            logging.info("Weather fetching is disabled")
            return None
            
        for attempt in range(Config.MAX_RETRIES):
            try:
                url = "https://www.meteosource.com/api/v1/free/point"
                parameters = {
                    'key': Config.WEATHER_API_KEY,
                    'place_id': Config.WEATHER_PLACE_ID,
                    'sections': 'daily',
                    'timezone': 'UTC',
                    'language': 'en',
                    'units': 'metric'
                }
                
                response = requests.get(url, params=parameters, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if 'daily' in data and 'data' in data['daily']:
                    logging.info(f"Successfully fetched weather data for {Config.WEATHER_PLACE_ID}")
                    return data
                else:
                    logging.warning("Weather data not found in response")
                    return None
                    
            except requests.RequestException as e:
                logging.error(f"Weather API attempt {attempt + 1} failed: {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logging.error("Max retries reached. Could not fetch weather data")
                    return None

    @staticmethod
    def get_weather_icon(weather_data: dict) -> str:
        """Get the weather icon for the current conditions.
        
        Args:
            weather_data: The weather data dictionary from Meteosource API
            
        Returns:
            str: The weather icon emoji
        """
        if not weather_data or 'daily' not in weather_data or 'data' not in weather_data['daily']:
            return WeatherIconMapper.get_icon('default')
            
        try:
            daily_data = weather_data['daily']['data'][0]
            weather_code = daily_data.get('weather', '')
            return WeatherIconMapper.get_icon(weather_code)
        except Exception as e:
            logging.error(f"Error getting weather icon: {str(e)}")
            return WeatherIconMapper.get_icon('default')

    @staticmethod
    def format_weather_for_prompt(weather_data: dict) -> str:
        """Format weather data into a prompt-friendly string."""
        if not weather_data or 'daily' not in weather_data or 'data' not in weather_data['daily']:
            return ""
            
        try:
            daily_data = weather_data['daily']['data'][0]  # Get first day's data
            
            # Extract weather information
            weather_desc = daily_data.get('weather', '')
            summary = daily_data.get('summary', '')
            
            # Extract temperature information
            temp_data = daily_data.get('all_day', {})
            temp = temp_data.get('temperature', '')
            temp_min = temp_data.get('temperature_min', '')
            temp_max = temp_data.get('temperature_max', '')
            
            # Extract wind information
            wind_data = temp_data.get('wind', {})
            wind_speed = wind_data.get('speed', '')
            wind_dir = wind_data.get('dir', '')
            
            # Extract cloud cover
            cloud_data = temp_data.get('cloud_cover', {})
            cloud_cover = cloud_data.get('total', '') if isinstance(cloud_data, dict) else cloud_data
            
            weather_context = (
                f"Daily weather forecast: {weather_desc}, {summary}\n"
                f"Temperature: {temp}°C (min: {temp_min}°C, max: {temp_max}°C)\n"
                f"Wind: {wind_speed} m/s from {wind_dir}\n"
                f"Cloud cover: {cloud_cover}%"
            )
            
            logging.info(f"Formatted weather context: {weather_context}")
            return weather_context
            
        except Exception as e:
            logging.error(f"Error formatting weather data: {str(e)}")
            return ""

    @staticmethod
    def format_weather_for_caption(weather_data: dict) -> str:
        """Format weather data into a caption-friendly string with icon.
        
        Args:
            weather_data: The weather data dictionary from Meteosource API
            
        Returns:
            str: Weather icon emoji, or empty string if no data
        """
        if not weather_data or 'daily' not in weather_data or 'data' not in weather_data['daily']:
            return ""
            
        try:
            weather_icon = WeatherAPI.get_weather_icon(weather_data)
            return weather_icon
            
        except Exception as e:
            logging.error(f"Error formatting weather for caption: {str(e)}")
            return ""

class GroqPromptGenerator:
    """Class to handle prompt generation using Groq AI."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(GroqPromptGenerator, cls).__new__(cls)
            cls._instance.style_selector = WeightedStyleSelector(IMAGE_ART)
        return cls._instance
    
    @classmethod
    def get_random_art_style(cls) -> dict:
        """Get a random art style using weighted selection."""
        if cls._instance is None:
            cls._instance = cls()
        style_name, style = cls._instance.style_selector.select_style()
        style['name'] = style_name
        logging.info(f"Selected art style: {style_name} - {style['description']}")
        return style
    
    @staticmethod
    def create_system_prompt(art_style: dict) -> str:
        """Create the system prompt for Groq AI."""
        return f"""You are an expert at creating short and vivid image generation prompts. Your task is to analyze Bible quotes and create prompts that will generate meaningful, symbolic, and visually striking images.

            The prompt should:
            1. Be in English and the prompt should be less than 1500 characters
            2. Capture the essence and meaning of the quote
            3. Use symbolic elements and metaphors            
            4. Mention that the image should not contain any text
            5. Mention that the image should be abstract and dynamic
            6. Mention that the image should not have central object, but rather little bit off center
            7. Mention that the image should use {art_style['name']} style with these characteristics: {', '.join(art_style['characteristics'])}            
            8. Mention that the image should avoid obvious digital look and feel
            9. Mention that the image should avoid obvious photography look and feel            
            10. Mention that the image should describe the frame that is suitable for the image and should not be too thick and should be from natural material
            11. Mention that the image should use carefull signature altogether with year (in range from 1980 to 2025)
            12. Consider the current weather conditions in the artistic style and mood, but do not use it as main focus


Format your response as a single, well-structured prompt that can be directly used for image generation."""

    @staticmethod
    def generate_enhanced_prompt(quote: str, art_style: dict) -> Optional[str]:
        """Generate an enhanced prompt using Groq AI."""
        try:
            # Fetch weather data
            weather_data = WeatherAPI.fetch_weather()
            weather_context = WeatherAPI.format_weather_for_prompt(weather_data)
            
            client = Groq(api_key=Config.GROQ_API_KEY)
            system_prompt = GroqPromptGenerator.create_system_prompt(art_style)
            
            user_prompt = f"Create a detailed image generation prompt for this Bible quote, but do not use the quote itself in the description of the image: {quote}"
            if weather_context:
                user_prompt += f"\n\nConsider this weather context, but do not use it as main focus: {weather_context}"
            
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=500
            )
            
            enhanced_prompt = response.choices[0].message.content
            logging.info("Successfully generated enhanced prompt using GROQ")
            return enhanced_prompt
            
        except Exception as e:
            logging.error(f"Error generating enhanced prompt: {str(e)}")
            return None

class VenicePromptGenerator:
    """Class to handle prompt generation using Venice.ai."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(VenicePromptGenerator, cls).__new__(cls)
            cls._instance.style_selector = WeightedStyleSelector(IMAGE_ART)
        return cls._instance
    
    @classmethod
    def get_random_art_style(cls) -> dict:
        """Get a random art style using weighted selection."""
        if cls._instance is None:
            cls._instance = cls()
        style_name, style = cls._instance.style_selector.select_style()
        style['name'] = style_name
        logging.info(f"Selected art style: {style_name} - {style['description']}")
        return style
    
    @staticmethod
    def create_system_prompt(art_style: dict) -> str:
        """Create the system prompt for Venice.ai."""
        return f"""You are an expert at creating short and vivid image generation prompts. Your task is to analyze Bible quotes and create prompts that will generate meaningful, symbolic, and visually striking images.

            The prompt should:
            1. Be in English and the prompt should be less than 1500 characters
            2. Capture the essence and meaning of the quote
            3. Use symbolic elements and metaphors            
            4. Mention that the image should not contain any text
            5. Mention that the image should be abstract and dynamic 
            6. Mention that the image should use {art_style['name']} style with these characteristics: {', '.join(art_style['characteristics'])}            
            7. Mention that the image should avoid obvious digital look and feel
            8. Mention that the image should avoid obvious photography look and feel            
            9. The prompt should describe picture frame that is suitable for the image and will be used to frame the image, the frame should not be too thick   
            10. Mention that the image should have the random artist signature and the random year of the image 
            11. Consider the current weather conditions in the artistic style and mood, but do not use it as main focus
            12. Mention that the image should not have central object, but rather little bit off center, preferably in the left or right side of the image
            

Format your response as a single, well-structured prompt that can be directly used for image generation."""

    @staticmethod
    def generate_enhanced_prompt(quote: str, art_style: dict) -> Optional[str]:
        """Generate an enhanced prompt using Venice.ai."""
        try:
            # Fetch weather data
            weather_data = WeatherAPI.fetch_weather()
            weather_context = WeatherAPI.format_weather_for_prompt(weather_data)
            
            headers = {
                'Authorization': f'Bearer {Config.VENICE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            system_prompt = VenicePromptGenerator.create_system_prompt(art_style)
            user_prompt = f"Create a detailed image generation prompt for this Bible quote, but do not use the quote itself in the description of the image: {quote}"
            if weather_context:
                user_prompt += f"\n\nConsider this weather context, but do not use it as main focus: {weather_context}"
            
            data = {
                'model': 'venice-uncensored',
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': user_prompt
                    }
                ],
                'temperature': 0.9,
                'max_tokens': 500,
                'top_p': 0.9,
                'frequency_penalty': 0,
                'presence_penalty': 0
            }
            
            for attempt in range(Config.MAX_RETRIES):
                try:
                    response = requests.post(
                        'https://api.venice.ai/api/v1/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 429:
                        logging.warning(f"Rate limit hit on attempt {attempt + 1}, retrying after delay")
                        time.sleep(Config.RETRY_DELAY)
                        continue
                        
                    response.raise_for_status()
                    result = response.json()
                    
                    enhanced_prompt = result['choices'][0]['message']['content']
                    
                    # Validate and optimize prompt length for Venice.ai
                    optimized_prompt, was_truncated = PromptLengthValidator.optimize_prompt(enhanced_prompt)
                    
                    if was_truncated:
                        logging.warning("Generated prompt was truncated to fit Venice.ai character limit")
                        stats = PromptLengthValidator.get_prompt_statistics(enhanced_prompt)
                        logging.info(f"Prompt statistics: {stats}")
                    
                    logging.info(f"Successfully generated enhanced prompt using VENICE (length: {len(optimized_prompt)} chars)")
                    return optimized_prompt
                    
                except requests.exceptions.RequestException as e:
                    if attempt < Config.MAX_RETRIES - 1:
                        logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(Config.RETRY_DELAY)
                    else:
                        raise
                        
        except Exception as e:
            logging.error(f"Error generating enhanced prompt: {str(e)}")
            return None

class PromptGeneratorFactory:
    """Factory class to create appropriate prompt generator based on configuration."""
    
    @staticmethod
    def get_prompt_generator() -> Union[GroqPromptGenerator, VenicePromptGenerator]:
        """Get the appropriate prompt generator based on configuration."""
        service = Config.get_ai_service()
        
        if service == 'venice':
            if not Config.VENICE_API_KEY:
                logging.error("Venice.ai API key not configured, falling back to Groq")
                return GroqPromptGenerator()
            return VenicePromptGenerator()
            
        return GroqPromptGenerator()

class ImageGenerator:
    """Class to handle image generation using Together AI."""
    
    @staticmethod
    def create_prompt(quote: str, art_style: dict) -> str:
        """Create a prompt for image generation based on the Bible quote."""
        prompt_generator = PromptGeneratorFactory.get_prompt_generator()
        enhanced_prompt = prompt_generator.generate_enhanced_prompt(quote, art_style)
        
        if not enhanced_prompt:
            logging.warning("Falling back to basic prompt generation")
            enhanced_prompt = f"""Create a symbolic and meaningful image representing this Bible quote: "{quote}"
            The image should:
            1. Capture the essence and meaning of the quote
            2. Use symbolic elements and metaphors
            3. Have a spiritual and contemplative atmosphere
            4. Be suitable for sharing on social media
            5. Use {art_style['name']} style with these characteristics: {', '.join(art_style['characteristics'])}"""
        
        return enhanced_prompt

    @staticmethod
    def generate_image(quote: str, art_style: dict) -> Optional[bytes]:
        """Generate image using Together AI API."""
        try:
            client = Together(api_key=Config.TOGETHER_API_KEY)
            prompt = ImageGenerator.create_prompt(quote, art_style)
            logging.info(f"Generating image with prompt: {prompt}")
            
            response = client.images.generate(
                model="black-forest-labs/FLUX.1-schnell-Free",
                width=1024,
                height=768,
                steps=4,
                prompt=prompt
            )
            
            if not hasattr(response, 'data') or not response.data:
                logging.error("Invalid response format from Together AI")
                return None
                
            image_url = response.data[0].url
            if not image_url:
                logging.error("No image URL in response")
                return None
                
            try:
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                return image_response.content
            except Exception as e:
                logging.error(f"Error downloading image from URL: {str(e)}")
                return None
                
        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            return None

class VeniceImageGenerator:
    """Class to handle image generation using Venice.ai."""
    
    @staticmethod
    def create_prompt(quote: str, art_style: dict) -> str:
        """Create a prompt for image generation based on the Bible quote."""
        prompt_generator = PromptGeneratorFactory.get_prompt_generator()
        enhanced_prompt = prompt_generator.generate_enhanced_prompt(quote, art_style)
        
        if not enhanced_prompt:
            logging.warning("Falling back to basic prompt generation")
            enhanced_prompt = f"""Create a symbolic and meaningful image representing this Bible quote: "{quote}"
            The image should:
            1. Capture the essence and meaning of the quote
            2. Use symbolic elements and metaphors
            3. Have a spiritual and contemplative atmosphere
            4. Be suitable for sharing on social media
            5. Use {art_style['name']} style with these characteristics: {', '.join(art_style['characteristics'])}"""
        
        return enhanced_prompt

    @staticmethod
    def generate_image(quote: str, art_style: dict) -> Optional[bytes]:
        """Generate image using Venice.ai API."""
        try:
            prompt = VeniceImageGenerator.create_prompt(quote, art_style)
            
            # Validate and optimize prompt length for Venice.ai image generation
            optimized_prompt, was_truncated = PromptLengthValidator.optimize_prompt(prompt)
            
            if was_truncated:
                logging.warning("Image generation prompt was truncated to fit Venice.ai character limit")
                stats = PromptLengthValidator.get_prompt_statistics(prompt)
                logging.info(f"Image prompt statistics: {stats}")
            
            logging.info(f"Generating image with Venice.ai using prompt (length: {len(optimized_prompt)} chars): {optimized_prompt}")
            
            headers = {
                'Authorization': f'Bearer {Config.VENICE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Venice.ai image generation parameters based on API docs
            data = {
                'model': 'hidream',
                'prompt': optimized_prompt,
                'size': '1024x1024',
                'response_format': 'b64_json',
                'output_format': 'png',
                'quality': 'auto',
                'style': 'natural',
                'n': 1,
                'background': 'auto',
                'moderation': 'auto',
                'output_compression': 100
            }
            
            for attempt in range(Config.MAX_RETRIES):
                try:
                    response = requests.post(
                        'https://api.venice.ai/api/v1/images/generations',
                        headers=headers,
                        json=data,
                        timeout=60  # Longer timeout for image generation
                    )
                    
                    if response.status_code == 429:
                        logging.warning(f"Rate limit hit on attempt {attempt + 1}, retrying after delay")
                        time.sleep(Config.RETRY_DELAY)
                        continue
                        
                    response.raise_for_status()
                    result = response.json()
                    
                    if not result.get('data') or not result['data']:
                        logging.error("No image data in Venice.ai response")
                        return None
                    
                    # Extract base64 image data
                    image_data = result['data'][0].get('b64_json')
                    if not image_data:
                        logging.error("No base64 image data in Venice.ai response")
                        return None
                    
                    # Decode base64 to bytes
                    import base64
                    image_bytes = base64.b64decode(image_data)
                    logging.info("Successfully generated image using Venice.ai")
                    return image_bytes
                    
                except requests.exceptions.RequestException as e:
                    if attempt < Config.MAX_RETRIES - 1:
                        logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(Config.RETRY_DELAY)
                    else:
                        raise
                        
        except Exception as e:
            logging.error(f"Error generating image with Venice.ai: {str(e)}")
            
            # Check if the error might be related to prompt length
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['length', 'size', 'too long', 'limit']):
                logging.warning("Error appears to be related to prompt length, attempting fallback to Together AI")
                try:
                    # Fallback to Together AI
                    logging.info("Attempting fallback to Together AI for image generation")
                    return ImageGenerator.generate_image(quote, art_style)
                except Exception as fallback_error:
                    logging.error(f"Fallback to Together AI also failed: {str(fallback_error)}")
            
            return None

class ImageGeneratorFactory:
    """Factory class to create appropriate image generator based on configuration."""
    
    @staticmethod
    def get_image_generator():
        """Get the appropriate image generator based on configuration."""
        service = Config.get_image_service()
        
        if service == 'venice':
            if not Config.VENICE_API_KEY:
                logging.error("Venice.ai API key not configured for image generation, falling back to Together AI")
                return ImageGenerator()
            logging.info("Using Venice.ai for image generation")
            return VeniceImageGenerator()
            
        logging.info("Using Together AI for image generation")
        return ImageGenerator()

class PromptLengthValidator:
    """Class to validate and optimize prompt length for Venice.ai API."""
    
    # Venice.ai has a strict 1500 character limit for image generation prompts
    VENICE_PROMPT_LIMIT = 1500
    
    @classmethod
    def validate_prompt_length(cls, prompt: str) -> tuple[bool, int]:
        """
        Validate if a prompt is within the Venice.ai character limit.
        
        Args:
            prompt: The prompt to validate
            
        Returns:
            tuple: (is_valid, character_count)
        """
        char_count = len(prompt)
        is_valid = char_count <= cls.VENICE_PROMPT_LIMIT
        return is_valid, char_count
    
    @classmethod
    def truncate_prompt(cls, prompt: str) -> str:
        """
        Intelligently truncate a prompt to fit within the Venice.ai character limit.
        
        Args:
            prompt: The prompt to truncate
            
        Returns:
            str: Truncated prompt that fits within the character limit
        """
        if len(prompt) <= cls.VENICE_PROMPT_LIMIT:
            return prompt
        
        logging.info(f"Prompt length ({len(prompt)}) exceeds Venice.ai limit ({cls.VENICE_PROMPT_LIMIT}). Truncating...")
        
        # Start with the original prompt
        truncated = prompt
        
        # First, try to remove common redundant phrases
        redundant_phrases = [
            "the image should",
            "the image must",
            "the image will",
            "make sure the image",
            "ensure the image",
            "the image needs to",
            "the image has to"
        ]
        
        for phrase in redundant_phrases:
            if len(truncated) <= cls.VENICE_PROMPT_LIMIT:
                break
            truncated = truncated.replace(phrase, "")
        
        # If still too long, try to remove repetitive words
        if len(truncated) > cls.VENICE_PROMPT_LIMIT:
            words_to_remove = ["very", "really", "quite", "extremely", "absolutely"]
            for word in words_to_remove:
                if len(truncated) <= cls.VENICE_PROMPT_LIMIT:
                    break
                truncated = truncated.replace(f" {word} ", " ")
        
        # If still too long, truncate at word boundary
        if len(truncated) > cls.VENICE_PROMPT_LIMIT:
            truncated = truncated[:cls.VENICE_PROMPT_LIMIT]
            # Find the last space to avoid cutting words in half
            last_space = truncated.rfind(' ')
            if last_space > cls.VENICE_PROMPT_LIMIT * 0.8:  # Only if we're not losing too much
                truncated = truncated[:last_space]
        
        # Add ellipsis if we truncated significantly
        if len(truncated) < len(prompt) * 0.9:
            truncated = truncated.rstrip() + "..."
        
        logging.info(f"Prompt truncated from {len(prompt)} to {len(truncated)} characters")
        return truncated
    
    @classmethod
    def optimize_prompt(cls, prompt: str) -> tuple[str, bool]:
        """
        Optimize a prompt for Venice.ai, ensuring it fits within the character limit.
        
        Args:
            prompt: The prompt to optimize
            
        Returns:
            tuple: (optimized_prompt, was_truncated)
        """
        is_valid, char_count = cls.validate_prompt_length(prompt)
        
        if is_valid:
            logging.info(f"Prompt is within limit: {char_count}/{cls.VENICE_PROMPT_LIMIT} characters")
            return prompt, False
        else:
            logging.warning(f"Prompt exceeds limit: {char_count}/{cls.VENICE_PROMPT_LIMIT} characters")
            optimized_prompt = cls.truncate_prompt(prompt)
            return optimized_prompt, True
    
    @classmethod
    def get_prompt_statistics(cls, prompt: str) -> dict:
        """
        Get statistics about a prompt's length and optimization potential.
        
        Args:
            prompt: The prompt to analyze
            
        Returns:
            dict: Statistics about the prompt
        """
        char_count = len(prompt)
        word_count = len(prompt.split())
        
        return {
            'character_count': char_count,
            'word_count': word_count,
            'is_within_limit': char_count <= cls.VENICE_PROMPT_LIMIT,
            'characters_over_limit': max(0, char_count - cls.VENICE_PROMPT_LIMIT),
            'percentage_of_limit': (char_count / cls.VENICE_PROMPT_LIMIT) * 100
        }

class TelegramBot:
    """Class to handle Telegram bot operations."""
    
    @staticmethod
    async def send_image_async(image_bytes: bytes, caption: str) -> bool:
        """Send image to Telegram channel asynchronously."""
        try:
            token = Config.get_telegram_token()
            chat_id = Config.get_telegram_chat_id()
            
            logging.info(f"Using {'production' if Config.is_production() else 'test'} environment")
            logging.info(f"Token: {token[:10]}...")  # Only log first 10 chars for security
            logging.info(f"Chat ID: {chat_id}")
            
            bot = Bot(token=token)
            await bot.send_photo(
                chat_id=chat_id,
                photo=image_bytes,
                caption=caption
            )
            logging.info("Successfully sent image to Telegram")
            return True
            
        except Exception as e:
            logging.error(f"Error sending image to Telegram: {str(e)}")
            return False

    @staticmethod
    def send_image(image_bytes: bytes, caption: str) -> bool:
        """Send image to Telegram channel."""
        return asyncio.run(TelegramBot.send_image_async(image_bytes, caption))

class TwitterBot:
    """Class to handle Twitter bot operations."""
    
    def __init__(self):
        """Initialize Twitter client with authentication."""
        self.client = tweepy.Client(
            consumer_key=Config.TWITTER_API_KEY,
            consumer_secret=Config.TWITTER_API_SECRET,
            access_token=Config.TWITTER_ACCESS_TOKEN,
            access_token_secret=Config.TWITTER_ACCESS_TOKEN_SECRET
        )
        self.media_client = tweepy.API(tweepy.OAuth1UserHandler(
            Config.TWITTER_API_KEY,
            Config.TWITTER_API_SECRET,
            Config.TWITTER_ACCESS_TOKEN,
            Config.TWITTER_ACCESS_TOKEN_SECRET
        ))
            
    def optimize_image(self, image_bytes: bytes) -> bytes:
        """Optimize image for Twitter upload."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            max_size = (2048, 2048)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            logging.error(f"Error optimizing image for Twitter: {str(e)}")
            return image_bytes
            
    def format_caption(self, quote: str, art_style: dict, weather_info: str) -> str:
        """Format caption for Twitter post."""
        caption = f"{quote}\n\n"
        hashtags = ["#Bible21", "#VerseOfTheDay"]
        style_name = art_style['name'].replace('_', ' ').title()
        style_hashtag = f"#{style_name.replace(' ', '')}"
        hashtags.append(style_hashtag)
        caption += " ".join(hashtags)
        return caption
        
    async def post_image(self, image_bytes: bytes, quote: str, art_style: dict, weather_info: str) -> bool:
        """Post image to Twitter with caption."""
        if not Config.is_twitter_enabled():
            logging.info("Twitter posting is disabled")
            return True
            
        try:
            optimized_image = self.optimize_image(image_bytes)
            caption = self.format_caption(quote, art_style, weather_info)
            
            try:
                media = self.media_client.media_upload(filename="image.jpg", file=io.BytesIO(optimized_image))
                response = self.client.create_tweet(
                    text=caption,
                    media_ids=[media.media_id]
                )
                logging.info(f"Successfully posted to Twitter: {response.data['id']}")
                return True
            except Exception as e:
                logging.error(f"Twitter posting failed: {str(e)}")
                return True
                
        except Exception as e:
            logging.error(f"Error in Twitter posting process: {str(e)}")
            return True

def process_quote_and_image(quote: str) -> bool:
    """Process the quote and generate/send image."""
    try:
        # Get weather info
        weather_info = WeatherAPI.format_weather_for_caption(WeatherAPI.fetch_weather())
        
        # Get current date
        current_date = datetime.now().strftime('%d/%m/%y')
        
        # Get art style once and reuse it
        art_style = GroqPromptGenerator.get_random_art_style()
        
        # Generate image using the selected art style and service
        image_generator = ImageGeneratorFactory.get_image_generator()
        image_bytes = image_generator.generate_image(quote, art_style)
        if not image_bytes:
            return False
            
        # Format Telegram caption (with weather, date, and shortcut at the end)
        telegram_caption = f"{weather_info}{current_date}\n\n{quote}({art_style['shortcut']})"
        
        # Send to Telegram
        telegram_success = TelegramBot.send_image(image_bytes, telegram_caption)
        if not telegram_success:
            return False
        
        # Only proceed with Twitter if enabled
        if Config.is_twitter_enabled():
            # Format Twitter caption (quote with verse reference)
            twitter_caption = quote  # The quote already includes the verse reference
            
            # Send to Twitter
            twitter_bot = TwitterBot()
            twitter_success = asyncio.run(twitter_bot.post_image(image_bytes, twitter_caption, art_style, weather_info))
            # Twitter success is optional, we don't fail the whole process if Twitter fails
            if not twitter_success:
                logging.warning("Twitter posting failed, but continuing with process")
        else:
            logging.info("Twitter posting is disabled")
        
        return True  # Return True if at least Telegram was successful
        
    except Exception as e:
        logging.error(f"Error processing quote and image: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    try:
        logging.info("Starting Bible quote image generator")
        logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Reload environment variables at start
        Config.reload_env()
        
        # Validate configuration
        if not Config.validate_telegram_config():
            logging.error("Invalid Telegram configuration. Exiting.")
            return
            
        if not Config.validate_twitter_config():
            logging.error("Invalid Twitter configuration. Exiting.")
            return
            
        if not Config.validate_ai_config():
            logging.error("Invalid AI configuration. Exiting.")
            return
            
        # Use new QuoteFetcher
        quote_fetcher = QuoteFetcher()
        quote = quote_fetcher.fetch_quote()
        #quote = Config.TEST_QUOTE
        
        if not quote:
            logging.error("Failed to fetch Bible quote")
            return
            
        logging.info(f"Successfully fetched quote: {quote}")
        
        if process_quote_and_image(quote):
            logging.info("Quote and image process completed successfully")
        else:
            logging.error("Failed to complete quote and image process")
            
    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main() 