# AI Slovo Image Generator

A Python script that generates artistic images from Bible quotes using AI. The script fetches daily Bible quotes, enhances them with AI-generated prompts, and creates unique visual interpretations using Together AI's image generation capabilities.

## Features

- Fetches daily Bible quotes from bible21.cz
- Uses Groq AI to create detailed image generation prompts
- Generates images using Together AI's FLUX.1-schnell-Free model
- Integrates weather data to enhance image context
- Sends generated images to Telegram with formatted captions
- Supports multiple art styles with weighted selection
- Includes weather icons in Telegram captions

## Prerequisites

- Python 3.x
- Together AI API key
- Groq AI API key
- Telegram Bot Token
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
WEATHER_API_KEY=your_weather_api_key
WEATHER_PLACE_ID=your_place_id
PRODUCTION=false
WEATHER=true
```

## Usage

Run the script:
```bash
python bible_image_generator.py
```

## Art Styles

The script supports multiple art styles with weighted selection:
- Impressionism (weight: 7)
- Post-impressionism (weight: 6)
- Fauvism (weight: 5)
- Expressionism (weight: 6)
- Cubism (weight: 9)
- Futurism (weight: 4)
- Dada (weight: 9)
- Surrealism (weight: 2)
- Abstract Expressionism (weight: 6)
- Minimalism (weight: 8)
- Mixed Media (weight: 10)
- Street Art (weight: 3)
- Deconstructivist Art (weight: 8)

## Configuration

- `PRODUCTION`: Set to 'true' or 'false' to switch between production and test environments
- `WEATHER`: Set to 'true' or 'false' to enable/disable weather data integration
- `WEATHER_PLACE_ID`: Set your location for weather data (default: 'kutna-hora')

## Dependencies

- together
- python-dotenv
- requests
- beautifulsoup4
- python-telegram-bot
- Pillow
- groq

## Author

- Jan Hruška (@jan_hru)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 