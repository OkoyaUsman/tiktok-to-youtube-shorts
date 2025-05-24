import os
import re
import json
import uuid
import platform
import requests
import textwrap
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

path = os.path.dirname(os.path.abspath(__file__))

os_name = platform.system()
if os_name == 'Windows':
    ffmpeg = "C:\\ffmpeg\\bin\\ffmpeg.exe"
    ffprobe = "C:\\ffmpeg\\bin\\ffprobe.exe"
else:
    ffmpeg = "ffmpeg"
    ffprobe = "ffprobe"

scopes = ["https://www.googleapis.com/auth/youtube.upload"]
user_states = {}
URL_PATTERN = re.compile(
    r'^(?:http|https)://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def download_file(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(f"https://tikwm.com/api/?url={url}", headers=headers).json()
        video_id = response['data']['id']
        video_url = response['data']['play']
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        with open(os.path.join(path, f"temp/{video_id}.mp4"), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return video_id
    except:
        return None

def get_video_info(input_video_path: str):
    try:
        cmd = [
            ffprobe,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            input_video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        video_info = next(s for s in data['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        
        return {
            'width': width,
            'height': height,
            'duration': float(data['format'].get('duration', 0))
        }
    except Exception as e:
        log(f"Error getting video info: {e}")
        return None
    
def create_text_overlay(text: str, width: int, height: int, font_path: str = None) -> str:
    # Create a new image with transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 60)
        else:
            font = ImageFont.load_default()
    except Exception as e:
        log(f"Error loading font: {e}")
        font = ImageFont.load_default()
    
    max_chars = int(width * 0.9 / 30)
    wrapped_text = textwrap.fill(text, width=max_chars)
    lines = wrapped_text.split('\n')
    
    # Calculate text box height
    line_height = 80
    text_box_height = len(lines) * line_height + 100
    
    # Draw semi-transparent black background
    draw.rectangle([(0, 0), (width, text_box_height)], fill=(0, 0, 0, 230))
    
    # Draw each line of text
    y = 80
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        
        # Draw text
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height
    
    # Save the overlay image
    temp_dir = os.path.join(path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    overlay_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")
    img.save(overlay_path, 'PNG')
    return overlay_path, text_box_height

def format_video(video_path: str, caption: str) -> str:
    input_path = os.path.join(path, f"temp/{video_path}.mp4")
    font_path = os.path.join(path, "font.ttf")
    temp_dir = os.path.join(path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")

    # Get video dimensions
    video_info = get_video_info(input_path)
    if not video_info:
        return None
        
    width = video_info['width']
    height = video_info['height']
    target_width = 1080
    target_height = 1920

    # Create text overlay
    overlay_path, text_box_height = create_text_overlay(caption, target_width, target_height, font_path)
    
    # Calculate available height for video
    available_height = target_height - text_box_height

    # Calculate scaling to fit the video while maintaining aspect ratio
    scale_w = target_width
    scale_h = int(target_width * height / width)
    
    if scale_h > available_height:
        scale_h = available_height
        scale_w = target_width

    # Calculate padding to center the video vertically
    pad_w = 0
    pad_h = text_box_height + (available_height - scale_h) // 2

    # Construct the ffmpeg command
    cmd = [
        ffmpeg,
        '-y',
        '-f', 'lavfi',
        '-i', f'color=c=black:s={target_width}x{target_height}:d=1',
        '-i', input_path,
        '-i', overlay_path,
        '-filter_complex',
        f'[1:v]scale={scale_w}:{scale_h}[scaled];'
        f'[scaled]pad={target_width}:{target_height}:{pad_w}:{pad_h}:black[padded];'
        f'[0:v][padded]overlay=0:0[bg];'
        f'[bg][2:v]overlay=0:0[v]',
        '-map', '[v]',
        '-map', '1:a?',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-c:a', 'aac',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Error processing video: {result.stderr}")
            return None
        return output_path
    except Exception as e:
        log(f"Error running ffmpeg: {e}")
        return None
    finally:
        if os.path.exists(overlay_path):
            try:
                os.remove(overlay_path)
            except:
                pass

def authenticate_youtube():
    creds = None
    token_file = os.path.join(path, "oauth2.json")
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(os.path.join(path, "credentials.json"), scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def upload_youtube(video_path: str, title: str, description: str, tags: list) -> bool:
    video_id = None
    try:
        YouTube = authenticate_youtube()
        request = YouTube.videos().insert(
            part = "snippet,status",
            body = {
                "snippet": {
                    "title": f"{title} #shorts #meme #funny",
                    "description": f"{description} #shorts #meme #funny {' '.join(['#'+tag for tag in tags])}",
                    "tags": tags,
                    "categoryId": "24"
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body = MediaFileUpload(video_path)
        )
        response = request.execute()
        log(f"✅ Uploaded: {title}")
        video_id = response["id"]
    except Exception as e:
        log(f"Error while uploading to youtube: {str(e)}")
    return video_id

def log(*msg):
    log_entry = '[{:%d/%m/%Y - %H:%M:%S}] {}'.format(datetime.now(), msg[0])
    with open(os.path.join(path, "log.txt"), 'a', encoding="utf-8") as log_writer:
        log_writer.write(log_entry+'\n')
    print(log_entry)

def cleanup_temp_files():
    try:
        temp_dir = os.path.join(path, "temp")
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        log(f"Cleaned up file: {file_path}")
                except Exception as e:
                    log(f"Error removing file {file_path}: {e}")
            log("Temp directory cleaned successfully")
    except Exception as e:
        log(f"Error cleaning up temp directory: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log("Got new chat.")
    await update.message.reply_text("Welcome! Please send me a URL to process.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_states
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Handle different states
    if user_id in user_states:
        state = user_states[user_id]['state']
        
        if state == 'waiting_for_caption':
            log("Making caption video.")
            video_path = user_states[user_id]['video_path']
            formatted_path = format_video(video_path, text)
            if not formatted_path:
                log("Failed to format the video.")
                await update.message.reply_text("Failed to format the video. Please try again.")
                return
            log("Successfully formatted the video with caption.")
            user_states[user_id] = {
                'formatted_path': formatted_path,
                'caption': text,
                'state': 'waiting_for_title'
            }
            await update.message.reply_text("Video formatted successfully! Please provide a title for the video.")
            return
            
        elif state == 'waiting_for_title':
            user_states[user_id]['title'] = text
            user_states[user_id]['state'] = 'waiting_for_description'
            await update.message.reply_text("Great! Now please provide a description for the video.")
            return
            
        elif state == 'waiting_for_description':
            user_states[user_id]['description'] = text
            user_states[user_id]['state'] = 'waiting_for_tags'
            await update.message.reply_text("Almost done! Please provide tags for the video (comma-separated).")
            return
            
        elif state == 'waiting_for_tags':
            tags = [tag.strip() for tag in text.split(',')]
            user_states[user_id]['tags'] = tags
            user_states[user_id]['state'] = 'waiting_for_confirmation'
            
            # Show preview with all metadata
            preview_text = (
                f"📝 Title: {user_states[user_id]['title']}\n\n"
                f"📄 Description: {user_states[user_id]['description']}\n\n"
                f"🏷 Tags: {', '.join(tags)}\n\n"
                "Please review and confirm the upload."
            )
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Accept", callback_data="accept"), 
                 InlineKeyboardButton("Reject", callback_data="reject")]
            ])
            await update.message.reply_video(
                video=open(user_states[user_id]['formatted_path'], 'rb'),
                caption=preview_text,
                reply_markup=reply_markup
            )
            return
    
    # Handle URL input
    if not URL_PATTERN.match(text):
        log("Invalid URL")
        await update.message.reply_text("Please send a valid URL.")
        return
        
    video_path = download_file(text)
    if not video_path:
        log("Failed to download the file.")
        await update.message.reply_text("Failed to download the file. Please try again.")
        return
        
    user_states[user_id] = {
        'video_path': video_path,
        'state': 'waiting_for_caption'
    }
    log("File downloaded successfully!")
    await update.message.reply_text("File downloaded successfully! Please send a caption for the video.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_states
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_states or user_states[user_id]['state'] != 'waiting_for_confirmation':
        log("Invalid state.")
        await query.answer("Invalid state. Please start over.")
        return
    if query.data == "reject":
        user_states.pop(user_id, None)
        log("Video rejected.")
        await query.message.reply_text("Video rejected. Please send a new URL.")
    elif query.data == "accept":
        formatted_path = user_states[user_id]['formatted_path']
        title = user_states[user_id]['title']
        description = user_states[user_id]['description']
        tags = user_states[user_id]['tags']
        uppy = upload_youtube(formatted_path, title, description, tags)
        if uppy:
            log("Video successfully uploaded to youtube")
            await query.message.reply_text(f"Video successfully uploaded to youtube!\nhttps://youtube.com/shorts/{uppy}")
        else:
            log("Failed to upload video to youtube.")
            await query.message.reply_text("Failed to upload video to youtube.")
        user_states.pop(user_id, None)
        await query.message.reply_text("Please send a new URL to process.")
    cleanup_temp_files()
    await query.answer()

def main():
    _ = authenticate_youtube()
    log("Running...")
    application = Application.builder().token("7654345678IH:SDFLKJHGFDFIUGFDFJKJHGFLKJHBV").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()

if __name__ == '__main__':
    main() 
