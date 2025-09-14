# All-in-One Content Tool

## Project Overview

A comprehensive content creation dashboard that combines AI-powered content generation, video creation, news scraping, and text-to-speech capabilities in a single Streamlit application.

## Features

### Content Generation
- AI-Powered Content Creation: Generate high-quality content using Google Gemini Pro API
- Multiple Variations: Create 2-5 different versions of content with varying styles
- Content Enhancement: Expand, rewrite, improve, or summarize existing content
- Blog Pipeline: Complete blog packages including main content, SEO meta descriptions, and social media snippets

### Video Generation
- AI Video Creation: Generate videos using Stability AI's Stable Video Diffusion
- Customizable Settings: Adjust sampling steps, FPS, resolution, and motion parameters
- Prompt Templates: Pre-built templates for various scenarios (nature, urban, abstract, etc.)
- Video History: Track and download previously generated videos

### News & Content Scraping
- TechCrunch Scraper: Extract the latest articles from TechCrunch
- Multiple Categories: Search by technology, marketing, AI, startups, cybersecurity, and more
- Data Export: Download scraped articles as CSV
- Dual View Modes: Table view for quick scanning or card view for detailed reading

### Text-to-Speech
- Multi-language Support: Convert text to speech in English, Hindi, and Urdu
- Audio Download: Save generated audio files for later use

### Media Management
- Centralized Output: View all generated videos and audio files in one place
- Download Options: Easy access to all created media content

## Installation

1. Clone the repository:
```
git clone https://github.com/abdullahkhvlid/All-in-One-Content-Tool/)
cd all-in-one-content-tool
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables:
Create a .env file with your API keys:
```
GEMINI_API_KEY=your_gemini_api_key_here
STABILITY_API_KEY=your_stability_ai_key_here
```

## Requirements

The project requires the following Python packages:
- streamlit
- pandas
- requests
- beautifulsoup4
- gtts
- python-dotenv
- Additional dependencies listed in requirements.txt

## Usage

1. Start the application:
```
streamlit run app.py
```

2. Navigate through tabs:
   - Job Scraping: Scrape TechCrunch for latest articles
   - Video Generation: Create AI-powered videos
   - Text-to-Speech: Convert text to audio
   - Media Output: View all generated media files
   - Content Expansion: Generate and enhance content
   - Project Info: Learn about the application

3. Generate content:
   - Enter your topic or prompt
   - Select content type and style
   - Choose target word count
   - Download or save the generated content

4. Create videos:
   - Select a prompt template or create your own
   - Adjust generation parameters
   - Generate and download your video

## Project Structure

```
project/
├── app.py                 # Main Streamlit application
├── content_generator.py   # AI content generation module
├── video_generator.py     # Stability AI video generation
├── scraping/              # Web scraping utilities
│   └── content_scraper.py
├── utils/                 # Utility functions
│   ├── config.py
│   └── logger.py
├── media/                 # Generated media files
│   └── outputs/
├── outputs/               # Generated content files
└── requirements.txt       # Python dependencies
```

## Configuration

The application uses two main API services:

1. Google Gemini Pro API: For all text generation tasks
2. Stability AI API: For video generation using Stable Video Diffusion

API keys can be configured either:
- Directly in the code (for development)
- Via environment variables (recommended for production)
- Through a .env file

## Tips for Best Results

### Content Generation
- Be specific with your topics for more targeted results
- Use the "Multiple Variations" option to get different perspectives
- Experiment with different writing styles for varied tones

### Video Generation
- Include details about lighting, movement, and style in your prompts
- Start with template prompts and customize them
- Adjust motion parameters for more or less movement in videos

### Scraping
- Use broad search terms for more results
- Refresh data frequently to get the latest articles
- Export to CSV for further analysis outside the app

## License

This project is built for educational and demonstration purposes. Please ensure you comply with the terms of service for all integrated APIs (Google Gemini, Stability AI).

## Support

For issues or questions related to this application, please check the Project Info tab within the app or create an issue in the repository.

Built using Streamlit, Gemini AI, and Stability AI
