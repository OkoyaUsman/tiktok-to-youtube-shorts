# TikTok to YouTube Shorts Bot

A Telegram bot that automatically downloads TikTok videos, adds custom captions, and uploads them to YouTube as Shorts.

## Features

- 🔄 Download TikTok videos via URL
- ✍️ Add custom captions with text overlay
- 🎨 Automatic video formatting for YouTube Shorts (9:16 aspect ratio)
- 📝 Custom metadata management:
  - Title
  - Description
  - Tags
- 🔍 Preview before upload
- 🎯 Automatic hashtag formatting
- 🧹 Automatic cleanup of temporary files
- 📊 Detailed logging system

## Prerequisites

- Python 3.7 or higher
- FFmpeg installed and accessible in system PATH
- Telegram Bot Token
- YouTube API credentials
- Internet connection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/okoyausman/tiktok-to-youtube-shorts.git
cd tiktok-to-youtube-shorts
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

4. Set up YouTube API:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download credentials and save as `credentials.json` in project root

5. Create a Telegram bot:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create new bot and get token
   - Update token in `bot.py`

## Configuration

1. Place your `credentials.json` in the project root directory
2. Update the Telegram bot token in `bot.py`
3. Create a `temp` directory in the project root (will be created automatically if not present)
4. (Optional) Add a custom font file named `font.ttf` in the project root

## Usage

1. Start the bot:
```bash
python bot.py
```

2. In Telegram:
   - Send `/start` to begin
   - Send a TikTok video URL
   - Add caption text
   - Provide video title
   - Add video description
   - Enter tags (comma-separated)
   - Review and confirm upload

## Project Structure

```
tt2yt/
├── bot.py              # Main bot script
├── requirements.txt    # Python dependencies
├── credentials.json    # YouTube API credentials
├── oauth2.json        # Generated OAuth token
├── font.ttf           # Custom font file (optional)
├── temp/              # Temporary files directory
└── log.txt           # Operation logs
```

## Dependencies

- python-telegram-bot>=20.0
- google-api-python-client>=2.0.0
- google-auth-oauthlib>=1.0.0
- Pillow>=9.0.0
- requests>=2.0.0

## Features in Detail

### Video Processing
- Automatically formats videos to 9:16 aspect ratio
- Adds black background for proper Shorts display
- Implements text overlay with custom font support
- Handles video scaling and padding

### Metadata Management
- Custom title with automatic #shorts hashtag
- Detailed description with formatted tags
- Custom tag support with automatic hashtag formatting
- Preview functionality before upload

### File Management
- Automatic temporary file cleanup
- Organized file structure
- Detailed logging system

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Google YouTube API](https://developers.google.com/youtube/v3)
- [FFmpeg](https://ffmpeg.org/) 
