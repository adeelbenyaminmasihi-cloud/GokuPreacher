import os
import asyncio
import google.generativeai as genai
import edge_tts
from moviepy.editor import AudioFileClip, ColorClip
import requests

# Secrets fetch from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

genai.configure(api_key=GEMINI_API_KEY)

def generate_script():
    print("Generating script using Gemini...")
    # Using standard gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = """
    Write a short, engaging 50-second direct-to-camera short video script in Roman Urdu about a real-world physics fact or an everyday scam (like mobile chargers, fuel average, or engine oil) that has a shocking hook, a story/fact, a direct pocket impact, and a call to action. Keep it punchy and energetic. Do not include timestamps, just the spoken words.
    """
    response = model.generate_content(prompt)
    return response.text

async def generate_audio(text):
    print("Converting text to speech (Urdu)...")
    voice = "ur-PK-AsadNeural" # Natural Urdu male voice
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("voiceover.mp3")

def create_video():
    print("Rendering video...")
    audio_clip = AudioFileClip("voiceover.mp3")
    duration = audio_clip.duration

    # Create a vertical background (Reels/TikTok format: 1080x1920)
    bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=duration)
    
    video = bg_clip.set_audio(audio_clip)
    
    output_file = "output_video.mp4"
    video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    return output_file

def send_to_telegram(video_path):
    print("Sending video to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_path, 'rb') as video_file:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': 'Aap ki rozana ki automated video tayar hai! 🚀'}
        files = {'video': video_file}
        response = requests.post(url, data=payload, files=files)
        print("Telegram Response:", response.text)

if __name__ == "__main__":
    script_text = generate_script()
    print("Script Generated:\n", script_text)
    
    # Run async TTS
    asyncio.run(generate_audio(script_text))
    
    # Render video
    video_path = create_video()
    
    # Send to Telegram
    send_to_telegram(video_path)
