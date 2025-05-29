# Bible Image Generator

A Python script that generates artistic images from Bible quotes using AI. The script fetches daily Bible quotes, enhances them with AI-generated prompts, and creates unique visual interpretations using Together AI's image generation capabilities.

## Features

- Fetches daily Bible quotes from bible21.cz
- Uses Groq AI to create detailed image generation prompts
- Generates images using Together AI's FLUX.1-schnell-Free model
- Integrates weather data to enhance image context
- Posts generated images to both Telegram and Twitter
- Supports multiple art styles with weighted selection
- Includes weather icons in Telegram captions
- Uses art style shortcuts in captions
- Optimizes images for different platforms

## Prerequisites

- Python 3.x
- Together AI API key
- Groq AI API key
- Telegram Bot Token
- Twitter API credentials
- Meteosource API key (for weather data)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/johnychodec/aipicture.git
cd aipicture
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
TOGETHER_API_KEY=your_together_api_key
GROQ_API_KEY=your_groq_api_key
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_TEST_TOKEN=your_test_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_TEST_CHAT_ID=your_test_chat_id
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
WEATHER_API_KEY=your_weather_api_key
WEATHER_PLACE_ID=your_place_id
PRODUCTION=false
WEATHER=true
TWITTER=true
```

## Usage

Run the script:
```bash
python bible_image_generator.py
```

## Art Styles

The script supports multiple art styles with weighted selection and shortcuts:
- Impressionism (weight: 7, shortcut: imp)
- Post-impressionism (weight: 6, shortcut: pim)
- Fauvism (weight: 5, shortcut: fau)
- Expressionism (weight: 6, shortcut: exp)
- Cubism (weight: 9, shortcut: cub)
- Futurism (weight: 4, shortcut: fut)
- Dada (weight: 9, shortcut: dad)
- Surrealism (weight: 2, shortcut: sur)
- Abstract Expressionism (weight: 6, shortcut: aex)
- Minimalism (weight: 8, shortcut: min)
- Mixed Media (weight: 10, shortcut: mix)
- Street Art (weight: 3, shortcut: str)
- Deconstructivist Art (weight: 8, shortcut: dec)

## Configuration

- `PRODUCTION`: Set to 'true' or 'false' to switch between production and test environments
- `WEATHER`: Set to 'true' or 'false' to enable/disable weather data integration
- `TWITTER`: Set to 'true' or 'false' to enable/disable Twitter posting
- `WEATHER_PLACE_ID`: Set your location for weather data (default: 'kutna-hora')

## Caption Format

### Telegram
```
[weather_icon][date]

[quote]([art_style_shortcut])
```

### Twitter
```
[quote]

#Bible21 #VerseOfTheDay #[ArtStyle]
```

## Dependencies

- together
- python-dotenv
- requests
- beautifulsoup4
- python-telegram-bot
- Pillow
- groq
- tweepy

## Author

- JohnyChodec

