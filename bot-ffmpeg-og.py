import os
import re
import json
import uuid
import platform
import requests
import textwrap
import subprocess
from datetime import datetime
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
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

user_states = {}
URL_PATTERN = re.compile(
    r'^(?:http|https)://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


storage = Storage(os.path.join(path, "oauth2.json"))
credentials = storage.get()
if credentials is None or credentials.invalid:
    with open(os.path.join(path, "credentials.json"), 'w') as f:
        f.write(json.dumps({
            "web": {
                "client_id": "134707659373-h15bdrrdlr7ing1eq5obdk6nkus2n8km.apps.googleusercontent.com",
                "client_secret": "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",
                "redirect_uris": ["https://localhost:8080/"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token"
            }
        }))
    flow = flow_from_clientsecrets("credentials.json", ["https://www.googleapis.com/auth/youtube.upload"])
    credentials = run_flow(flow, storage)
YouTube = build("youtube", "v3", credentials=credentials)

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
        return json.loads(result.stdout)
    except Exception as e:
        log(f"Error getting video info: {e}")
        return None
    
def format_video(video_path: str, caption: str) -> str:
    input_path = os.path.join(path, f"temp/{video_path}.mp4")
    font_path = os.path.join(path, "font.ttf")
    temp_dir = os.path.join(path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")

    probe_result = get_video_info(input_path)
    if not probe_result:
        return None
        
    video_info = next(s for s in probe_result['streams'] if s['codec_type'] == 'video')
    width = int(video_info['width'])
    height = int(video_info['height'])
    target_width = 1080
    target_height = 1920

    max_chars = int(target_width * 0.9 / 30)  # Approximate characters per line based on font size
    wrapped_text = textwrap.fill(caption, width=max_chars)
    
    lines = wrapped_text.split('\n')
    max_line_length = max(len(line) for line in lines)
    
    centered_lines = []
    for line in lines:
        # Calculate total spaces needed to match longest line
        total_spaces = max_line_length - len(line)
        # Split spaces between start and end
        spaces_before = total_spaces // 2
        spaces_after = total_spaces - spaces_before  # This handles odd numbers correctly
        # Create centered line with spaces before and after
        centered_line = ' ' * spaces_before + line + ' ' * spaces_after
        centered_lines.append(centered_line)
    wrapped_text = '\n'.join(centered_lines)
    
    num_lines = len(wrapped_text.split('\n'))
    text_box_height = num_lines * 80 + 100

    # Calculate available height for video (total height minus text overlay)
    available_height = target_height - text_box_height

    # Calculate scaling to fit the video while maintaining aspect ratio
    scale_w = target_width  # Always use full width
    scale_h = int(target_width * height / width)  # Calculate height based on aspect ratio
    
    if scale_h > available_height:
        scale_h = available_height
        scale_w = target_width  # Still use full width even if we need to crop height

    # Calculate padding to center the video vertically
    pad_w = 0  # No horizontal padding since we're using full width
    pad_h = text_box_height + (available_height - scale_h) // 2  # Add text_box_height to position video below text

    # Escape text for ffmpeg
    escaped_text = wrapped_text.replace("'", "'\\''")

    # Font settings
    if font_path and os.path.exists(font_path):
        font_settings = f"fontfile='{font_path}':"
    else:
        # Use system font if custom font not provided or not found
        font_settings = "font='Arial':"

    # Construct the ffmpeg command
    cmd = [
        ffmpeg,
        '-y',  # Overwrite output file if it exists
        '-f', 'lavfi',
        '-i', f'color=c=black:s={target_width}x{target_height}:d=1',
        '-i', input_path,
        '-filter_complex',
        f'[1:v]scale={scale_w}:{scale_h}[scaled];'
        f'[scaled]pad={target_width}:{target_height}:{pad_w}:{pad_h}:black[padded];'
        f'[0:v][padded]overlay=0:0[bg];'
        # Create black background for text that stretches full width
        f'[bg]drawbox=x=0:y=0:w={target_width}:h={text_box_height}:color=black@0.9:t=fill[textbg];'
        # Add text with custom font - center aligned and more padding
        f'[textbg]drawtext={font_settings}text=\'{escaped_text}\':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=80:line_spacing=20:box=0[v]',
        '-map', '[v]',
        '-map', '1:a?',  # Map audio if it exists
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

def upload_youtube(video_path: str, caption: str) -> bool:
    video_id = None
    try:
        tags = "meme,funny,local,weird,africa,europe,fails,core"
        request = YouTube.videos().insert(
            part = "snippet,status",
            body = {
                "snippet": {
                    "title": caption,
                    "description": caption,
                    "tags": tags.split(","),
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body = MediaFileUpload(video_path)
        )
        response = request.execute()
        log(f"✅ Uploaded: {caption}")
        video_id = response["id"]
    except Exception as e:
        log(f"Error while uploading to youtube: {str(e)}")
    return video_id

def log(*msg):
    log_entry = '[{:%d/%m/%Y - %H:%M:%S}] {}'.format(datetime.now(), msg[0])
    with open(os.path.join(path, "log.txt"), 'a', encoding="utf-8") as log_writer:
        log_writer.write(log_entry+'\n')
    print(log_entry)

def cleanup_temp_files(video_path: str, formatted_path: str = None):
    try:
        if video_path:
            original_path = os.path.join(path, f"temp/{video_path}.mp4")
            if os.path.exists(original_path):
                os.remove(original_path)
                log(f"Cleaned up original video: {original_path}")

        if formatted_path and os.path.exists(formatted_path):
            os.remove(formatted_path)
            log(f"Cleaned up formatted video: {formatted_path}")
    except Exception as e:
        log(f"Error cleaning up temp files: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log("Got new chat.")
    await update.message.reply_text("Welcome! Please send me a URL to process.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_states
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # If user is waiting for caption
    if user_id in user_states and user_states[user_id]['state'] == 'waiting_for_caption':
        log("Making caption video.")
        video_path = user_states[user_id]['video_path']
        formatted_path = format_video(video_path, text)
        if not formatted_path:
            log("Failed to format the video.")
            await update.message.reply_text("Failed to format the video. Please try again.")
            return
        log("Successfully formatted the video with caption.")
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Accept", callback_data="accept"), InlineKeyboardButton("Reject", callback_data="reject")]])
        user_states[user_id] = {
            'formatted_path': formatted_path,
            'caption': text,
            'state': 'waiting_for_confirmation'
        }
        await update.message.reply_video(video=open(formatted_path, 'rb'), reply_markup=reply_markup)
        return
    
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
        # Clean up files before removing state
        cleanup_temp_files(
            user_states[user_id].get('video_path'),
            user_states[user_id].get('formatted_path')
        )
        user_states.pop(user_id, None)
        log("Video rejected.")
        await query.message.reply_text("Video rejected. Please send a new URL.")
    elif query.data == "accept":
        formatted_path = user_states[user_id]['formatted_path']
        caption = user_states[user_id]['caption']
        uppy = upload_youtube(formatted_path, caption)
        if uppy:
            log("Video successfully uploaded to youtube")
            await query.message.reply_text(f"Video successfully uploaded to youtube!\nhttps://youtube.com/shorts/{uppy}")
        else:
            log("Failed to upload video to youtube.")
            await query.message.reply_text("Failed to upload video to youtube.")
        
        # Clean up files after upload (whether successful or not)
        cleanup_temp_files(
            user_states[user_id].get('video_path'),
            user_states[user_id].get('formatted_path')
        )
        user_states.pop(user_id, None)
        await query.message.reply_text("Please send a new URL to process.")
    await query.answer()

def main():
    log("Running...")
    application = Application.builder().token("7968267559:AAF_nXzpz2upEK2OyqPK_qmZh7S2oWZ3Tfo").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()

if __name__ == '__main__':
    main() 