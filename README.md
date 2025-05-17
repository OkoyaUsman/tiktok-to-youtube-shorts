# TT2YT - TikTok to YouTube Shorts Converter Bot

A Telegram bot that automatically converts TikTok videos to YouTube Shorts format with custom text overlays. The bot handles video downloading, formatting, and direct upload to YouTube.

## Features

- 🔄 Convert TikTok videos to YouTube Shorts format (9:16 aspect ratio)
- 📝 Add custom text overlays with proper formatting and centering
- 🤖 Telegram bot interface for easy interaction
- 🎥 Automatic video processing with FFmpeg
- 📤 Direct upload to YouTube
- 🎨 Custom font support
- 🧹 Automatic cleanup of temporary files

## Prerequisites

- Python 3.7+
- FFmpeg installed and accessible in PATH
- Telegram Bot Token
- YouTube API Credentials
- Custom font file (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/okoyausman/tiktok-to-youtube-shorts.git
cd tiktok-to-youtube-shorts
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Set up FFmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

4. Configure YouTube API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials with "Desktop App"
   - Download credentials and save as `credentials.json` in the project directory

5. Set up Telegram Bot:
   - Create a new bot using [@BotFather](https://t.me/botfather)
   - Get the bot token and update it in the code

## Configuration

1. Place your custom font file (if any) as `font.ttf` in the project directory
2. Update the Telegram bot token in `bot.py`
3. Ensure `credentials.json` is in the project directory for YouTube API

## Usage

1. Start the bot:
```bash
python bot.py
```

2. In Telegram:
   - Send `/start` to begin
   - Send a TikTok video URL
   - Provide caption text when prompted
   - Review the formatted video
   - Accept or reject the upload

## Project Structure

```
tt2yt/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── credentials.json    # YouTube API credentials
├── font.ttf           # Custom font file (optional)
├── temp/              # Temporary files directory
└── README.md          # This file
```

## Dependencies

- python-telegram-bot
- google-api-python-client
- google-auth-oauthlib
- Pillow
- requests

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Google YouTube API](https://developers.google.com/youtube/v3)
- [FFmpeg](https://ffmpeg.org/) 
