import os
import asyncio
import subprocess
import requests
import google.generativeai as genai
import edge_tts

# Environment secrets fetch
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def generate_script():
    print("Generating script using Gemini...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Write a short, engaging 45-second direct-to-camera short video script in Roman Urdu about a real-world physics fact or an everyday scam (like mobile chargers, fuel average myths, or engine oil) that has a shocking hook, a story/fact, a direct pocket impact, and a call to action. Keep it punchy and energetic. Do not include timestamps, just the spoken words.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in Gemini: {e}")
        # Fallback script in case of API issue
        return "Mechanic har do mahine baad aapko choona kaise lagata hai? Aur hairat ki baat ye hai ke isme ghalti mechanic ki nahi, aapki physics ki hai! Sardi mein jab aap mota oil dalte ho toh engine start par do guna zor lagata hai. Agli dafa mechanic ke paas jao toh oil ka grade zaroor check karna. Roz aisi real-world logic sikhne ke liye follow ka button daba do!"

async def generate_audio(text):
    print("Converting text to speech (Urdu)...")
    voice = "ur-PK-AsadNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("voiceover.mp3")

def create_video():
    print("Rendering video using FFmpeg...")
    output_file = "output_video.mp4"
    
    # 1080x1920 (Reels / Shorts format), 24 fps, clean dark background
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x141414:s=1080x1920:r=24",
        "-i", "voiceover.mp3",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ]
    subprocess.run(cmd, check=True)
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
