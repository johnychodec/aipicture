# AI Slovo Image Generator

## Description
This script generates images based on Bible quotes and posts them to Telegram and Twitter. It uses Together AI for image generation and either Groq AI or Venice.ai for prompt enhancement.

## Features
- Fetches Bible quotes from multiple sources (bible21.cz and dailyverses.net)
- Generates images using Together AI's FLUX.1-schnell-Free model
- Enhances prompts using either Groq AI or Venice.ai
- Posts images to Telegram and Twitter
- Includes weather information in captions
- Supports multiple art styles with weighted selection
- Robust error handling and retry mechanisms
- Comprehensive logging system

## Configuration
The script uses environment variables for configuration. Create a `.env` file with the following variables:

### Basic Configuration
- `PRODUCTION`: Set to 'true' or 'false' to enable/disable production mode
- `WEATHER`: Set to 'true' or 'false' to enable/disable weather data fetching
- `TWITTER`: Set to 'true' or 'false' to enable/disable Twitter posting
- `AI_SERVICE`: Set to 'groq' or 'venice' to select the AI service for prompt enhancement

### Telegram Configuration
- `TELEGRAM_TOKEN`: Your Telegram bot token
- `TELEGRAM_TEST_TOKEN`: Your test Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram channel ID
- `TELEGRAM_TEST_CHAT_ID`: Your test Telegram channel ID

### Twitter Configuration
- `TWITTER_API_KEY`: Your Twitter API key
- `TWITTER_API_SECRET`: Your Twitter API secret
- `TWITTER_ACCESS_TOKEN`: Your Twitter access token
- `TWITTER_ACCESS_TOKEN_SECRET`: Your Twitter access token secret
- `TWITTER_BEARER_TOKEN`: Your Twitter bearer token

### API Keys
- `TOGETHER_API_KEY`: Your Together AI API key
- `GROQ_API_KEY`: Your Groq AI API key
- `VENICE_API_KEY`: Your Venice.ai API key
- `WEATHER_API_KEY`: Your Meteosource API key
- `WEATHER_PLACE_ID`: Your Meteosource place ID (default: kutna-hora)

### Retry Configuration
- `MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `RETRY_DELAY`: Delay between retries in seconds (default: 5)

## Art Styles
The script supports various art styles for image generation. Each style has a weight that determines its selection probability and a shortcut used in captions:

- Impressionism (weight: 8, shortcut: imp)
- Post-impressionism (weight: 8, shortcut: pim)
- Fauvism (weight: 5, shortcut: fau)
- Expressionism (weight: 8, shortcut: exp)
- Cubism (weight: 8, shortcut: cub)
- Futurism (weight: 4, shortcut: fut)
- Dada (weight: 8, shortcut: dad)
- Surrealism (weight: 5, shortcut: sur)
- Abstract Expressionism (weight: 7, shortcut: aex)
- Minimalism (weight: 8, shortcut: min)
- Mixed Media (weight: 8, shortcut: mix)
- Street Art (weight: 4, shortcut: str)
- Deconstructivist Art (weight: 8, shortcut: dec)
- Art Deco (weight: 8, shortcut: ade)

## Usage
1. Set up your environment variables in `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the script: `python bible_image_generator.py`

## Output Format
The script generates images with captions in the following format:

### Telegram
```
[Weather Icon] [Date]

[Quote Text] ([Art Style Shortcut])
```

### Twitter
```
[Quote Text]

#Bible21 #[ArtStyle] #VerseOfTheDay
```

## Error Handling
The script includes comprehensive error handling:
- Retries failed API calls
- Falls back to alternative quote sources
- Falls back to alternative AI services
- Logs errors and warnings
- Continues operation even if Twitter posting fails
- Handles rate limits gracefully
- Provides detailed error logging

## AI Services
The script supports two AI services for prompt enhancement:

### Groq AI
- Uses llama-3.3-70b-versatile model
- Temperature: 0.7
- Max tokens: 500

### Venice.ai
- Uses venice-uncensored model
- Temperature: 0.7
- Max tokens: 500
- Top p: 0.9
- Frequency penalty: 0
- Presence penalty: 0

## Dependencies
- together
- python-dotenv
- requests
- beautifulsoup4
- python-telegram-bot
- Pillow
- groq
- tweepy

## Recent Updates
- Added Venice.ai integration as an alternative AI service
- Updated art style weights for better distribution
- Added Art Deco style
- Improved error handling and logging
- Optimized Twitter posting logic
- Added comprehensive documentation

## License
MIT License

