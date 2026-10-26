import os
import json
import random
import asyncio
import subprocess
import urllib.parse
import textwrap
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

TOPICS = [
    "Mobile ke 300 rupay wale local charger ka scam aur Georg Ohm ki Resistance physics",
    "70cc aur 125cc bike mein petrol average barhane wale Carburetor mistri ka choona aur Bernoulli Principle",
    "Inverter AC ko 16 degree par chalane ka nuqsan aur Thermodynamics ka asli kanoon",
    "Fridge ki gas har saal khatam hone ka scam aur Ideal Gas Law ki haqeeqat",
    "Tyre mein hawa kam rakhne ka desi jugaar, petrol ki tabahi aur Rolling Friction",
    "Sardi mein geyser aur paani ki tanki thandi hone ka masla aur Thermal Conductivity",
    "Mehngay detergent powder aur jhaag ka dhoka vs Surface Tension physics",
    "Solar panels par gard (dust) jamne se 40% bijli gayab hone ka scam aur Photoelectric Effect",
    "Gaadi ke radiator mein saada paani dalne ki ghalti aur Boiling Point Elevation",
    "Fake power banks jo 20,000 mAh likh kar 3,000 mAh dete hain aur Energy Density"
]

SYSTEM_PROMPT = """
You are an elite Pakistani short-form infotainment scriptwriter (like ZemTV meets funny Desi street smarts).
Write a hilarious, high-energy, 60-second vertical video script (10 scenes) about the requested topic.

Follow this exact structure:
- Scenes 1-2: THE HOOK (Shocking financial loss / "choona" + funny Desi observation + blame it on ignoring Physics).
- Scenes 3-5: THE STORY / EXPERIMENT (A bizarre historical event or real-world experiment showing this physics law in action).
- Scenes 6-8: THE POCKET IMPACT (How local mechanics, shopkeepers, or "ustaad" use this against common people and cost them thousands of rupees).
- Scenes 9-10: THE MORAL & PUNCHY CTA ("Physics koi boring syllabus nahi, dunya ka Source Code hai!").

CRITICAL RULES FOR VOICEOVER QUALITY:
1. "tts_urdu" MUST be written in PROPER URDU SCRIPT (اردو رسم الخط) using natural, conversational Pakistani spoken style (bol-chaal ki zaban). Write English words in Urdu script (e.g., فزکس, مکینک, بیٹری, وولٹیج) so the Urdu voice engine pronounces everything naturally without spelling out English letters!
2. "caption" MUST be short (4 to 7 words max) in punchy Roman Urdu + English (ALL CAPS) to display on screen.
3. "image_prompt" MUST be a vivid English visual description for generating a vertical 9:16 photorealistic scene (NO text in image).

Return ONLY valid JSON in this exact format (no markdown blocks):
{
  "title": "Catchy Roman Urdu Title",
  "hashtags": "#PhysicsLogic #DesiScam #UrduFacts #ReelsPakistan",
  "category_badge": "PHYSICS VS CHOONA",
  "scenes": [
    {
      "tts_urdu": "اردو رسم الخط میں قدرتی اور مزیدار جملہ جو کم از کم بارہ سے پندرہ الفاظ کا ہو۔",
      "caption": "HAR MAHINE 10,000 KA CHOONA?!",
      "image_prompt": "Cinematic close up of a cunning street mechanic holding an engine oil bottle smiling, dramatic lighting, photorealistic, 9:16 vertical"
    }
  ]
}
Ensure there are EXACTLY 10 scenes, and each scene's "tts_urdu" is 14 to 20 words long so the total video is ~60 seconds.
"""

def generate_script_data():
    topic = random.choice(TOPICS)
    print(f"Selected Topic: {topic}")
    full_prompt = f"{SYSTEM_PROMPT}\n\nTopic to write about today: {topic}"

    # 1. Try Gemini REST API first if a valid AIzaSy key is provided
    if GEMINI_API_KEY.startswith("AIza"):
        try:
            print("Trying Google Gemini API...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            resp = requests.post(url, json=payload, timeout=45)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return clean_and_parse_json(raw_text)
        except Exception as e:
            print(f"Gemini API skipped: {e}")

    # 2. Free Keyless AI Generator (Pollinations OpenAI GPT-4o-mini endpoint)
    for attempt in range(3):
        try:
            print(f"Generating script via Free AI Engine (Attempt {attempt+1})...")
            resp = requests.post(
                "https://text.pollinations.ai/",
                json={
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Create a 10-scene funny 60-second script on: {topic}. Return ONLY raw JSON."}
                    ],
                    "model": "openai",
                    "jsonMode": True,
                    "seed": random.randint(1, 999999)
                },
                timeout=60
            )
            if resp.status_code == 200 and resp.text.strip():
                return clean_and_parse_json(resp.text)
        except Exception as e:
            print(f"Free AI Attempt {attempt+1} error: {e}")

    print("Using built-in full 10-scene master script...")
    return get_backup_master_script()

def clean_and_parse_json(raw_text):
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    data = json.loads(text[start:end])
    if "scenes" in data and len(data["scenes"]) >= 6:
        return data
    raise ValueError("Incomplete scenes in JSON")

def get_backup_master_script():
    return {
        "title": "300 Wala Local Charger Aur Physics Ka Choona!",
        "hashtags": "#PhysicsLogic #MobileScam #PakistaniReels #TechUrdu #DimaagKholo",
        "category_badge": "PHYSICS VS DESI JUGAAR",
        "scenes": [
            {
                "tts_urdu": "فون کی بیٹری بیس فیصد سے سیدھا زیرو پر کیسے گر جاتی ہے؟ اور اس میں غلطی آپ کے فون کی نہیں، آپ کی فزکس کی ہے!",
                "caption": "BATTERY 20% SE SEEDHA ZERO?!",
                "image_prompt": "Shocked young Pakistani man looking at his smartphone with dead battery warning icon, dramatic neon lighting, photorealistic vertical"
            },
            {
                "tts_urdu": "جب آپ تین سو روپے والا لوکل چارجر یا سستی کیبل خریدتے ہو تو آپ کو لگتا ہے کہ آپ نے دکاندار کو ماموں بنا دیا۔",
                "caption": "300 WALA SASTA CHARGER KA SCAM!",
                "image_prompt": "Street mobile accessories shop with cheap tangled white charging cables hanging, cinematic lighting, vertical 9:16"
            },
            {
                "tts_urdu": "مگر اٹھارہ سو ستائیس میں جارج اوہم نے ایک ایسا قانون دریافت کیا تھا جو آج آپ کی جیب میں روز آگ لگا رہا ہے، یعنی اوہمز لا!",
                "caption": "1827 KA OHM'S LAW AUR APKI JEB!",
                "image_prompt": "Vintage 19th century scientist in a laboratory with glowing copper wires and electricity sparks, dramatic cinematic"
            },
            {
                "tts_urdu": "اصلی چارجر کی تار میں خالص کاپر ہوتا ہے جس میں بجلی مکھن کی طرح دوڑتی ہے، مگر سستی کیبل میں لوہا اور ہلکا ایلومینیم ملایا جاتا ہے۔",
                "caption": "PURE COPPER VS SASTA KACHRA WIRE",
                "image_prompt": "Macro close up of glowing copper wire strands versus burnt cheap aluminum wire, high detail 3d render vertical"
            },
            {
                "tts_urdu": "فزکس کہتی ہے کہ جب پتلی اور نقلی تار سے کرنٹ گزرتا ہے تو ریزسٹنس یعنی رکاوٹ دس گنا بڑھ جاتی ہے اور تار ہیٹر بن جاتی ہے!",
                "caption": "HIGH RESISTANCE = MOBILE BANA HEATER!",
                "image_prompt": "Glowing red hot electrical circuit board with sparks flying and heat waves, cinematic macro shot"
            },
            {
                "tts_urdu": "دکاندار بڑے پیار سے کہتا ہے کہ بھائی جان اوریجنل تین ہزار کا ہے، یہ تین سو والا لے لو، دونوں ایک ہی فیکٹری سے آتے ہیں۔",
                "caption": "DUKANDAR KA SABSE BADA JHOOT!",
                "image_prompt": "Clever electronics shopkeeper showing a cheap phone charger with a sly smile, cinematic realistic portrait"
            },
            {
                "tts_urdu": "مگر وہ سستا چارجر ہر سیکنڈ وولٹیج کے جھٹکے مارتا ہے جس سے آپ کے فون کی چارجنگ آئی سی اور بیٹری اندر ہی اندر جل جاتی ہے۔",
                "caption": "CHARGING IC AUR BATTERY TABAH!",
                "image_prompt": "Smartphone opened up on a repair table with smoke coming out of the battery and motherboard, dramatic lighting"
            },
            {
                "tts_urdu": "تین سو روپے بچانے کے چکر میں دو مہینے بعد جب آپ کاریگر کے پاس جاتے ہو تو سیدھا پندرہ ہزار روپے کا بل ہاتھ میں آتا ہے!",
                "caption": "300 BACHAYE, 15,000 KA FAtKA LAGA!",
                "image_prompt": "Phone repair technician handing a huge repair bill to a stressed customer, cinematic lighting"
            },
            {
                "tts_urdu": "ٹیسلا کی الیکٹرک گاڑیوں سے لے کر آپ کے موبائل فون تک، ہر جگہ واٹ، ایمپیئر اور ریزسٹنس کا یہی پکا حساب چلتا ہے۔",
                "caption": "TESLA SE LE KAR APKE PHONE TAK!",
                "image_prompt": "Futuristic electric car charging station glowing with blue energy next to a smartphone charging, high tech"
            },
            {
                "tts_urdu": "فزکس کوئی رٹے والا مضمون نہیں بلکہ اس دنیا کا سورس کوڈ ہے! روزانہ ایسی اصلی لاجک سیکھنے کے لیے ابھی فالو کا بٹن دبا دو!",
                "caption": "DUNYA KA SOURCE CODE SEEKHO - FOLLOW!",
                "image_prompt": "Confident smart creator pointing at camera with glowing physics formulas floating in background, vibrant cinematic"
            }
        ]
    }

def download_scene_image(prompt, index):
    img_path = f"raw_scene_{index}.jpg"
    enhanced_prompt = f"{prompt}, ultra detailed, cinematic lighting, vibrant colors, vertical 9:16 aspect ratio, no text"
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={seed}"

    for attempt in range(2):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(img_path, "wb") as f:
                    f.write(r.content)
                return img_path
        except Exception as e:
            print(f"Image fetch retry {index}: {e}")

    # Attractive colorful gradient fallback if internet hiccups
    img = Image.new("RGB", (1080, 1920), (18, 24, 42))
    draw = ImageDraw.Draw(img)
    palette = [(14, 165, 233), (249, 115, 22), (168, 85, 247), (16, 185, 129), (239, 68, 68)]
    accent = palette[index % len(palette)]
    for y in range(1920):
        ratio = y / 1920
        r_c = int(15 * (1 - ratio) + accent[0] * ratio * 0.45)
        g_c = int(20 * (1 - ratio) + accent[1] * ratio * 0.45)
        b_c = int(35 * (1 - ratio) + accent[2] * ratio * 0.45)
        draw.line([(0, y), (1080, y)], fill=(r_c, g_c, b_c))
    img.save(img_path)
    return img_path

def create_overlay_png(caption_text, badge_text, scene_idx, total_scenes):
    """Creates a transparent 1080x1920 overlay with Hormozi-style captions and top badge."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top and bottom dark cinematic gradient for readability
    for y in range(380):
        alpha = int(190 * (1 - y / 380))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1250, 1920):
        alpha = int(235 * ((y - 1250) / 670))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        badge_font = ImageFont.truetype(font_path, 38)
        caption_font = ImageFont.truetype(font_path, 66)
    except Exception:
        badge_font = ImageFont.load_default()
        caption_font = ImageFont.load_default()

    # Top Category Pill Badge
    badge_w, badge_h = 580, 78
    bx1 = (1080 - badge_w) // 2
    by1 = 110
    draw.rounded_rectangle([bx1, by1, bx1 + badge_w, by1 + badge_h], radius=39, fill=(220, 38, 38, 240), outline=(255, 255, 255, 220), width=3)
    draw.text((1080 // 2, by1 + badge_h // 2), badge_text.upper(), font=badge_font, fill=(255, 255, 255, 255), anchor="mm")

    # Center-Bottom Bold Captions (Wrapped)
    lines = textwrap.wrap(caption_text.upper(), width=18)
    y_start = 1430 - (len(lines) * 45)

    for i, line in enumerate(lines):
        y_pos = y_start + i * 95
        # Alternating vibrant Yellow and White lines like viral Reels
        text_color = (255, 230, 0, 255) if i % 2 == 0 else (255, 255, 255, 255)
        # Black heavy stroke/shadow
        draw.text((540, y_pos), line, font=caption_font, fill=text_color, anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0, 255))

    # Bottom Progress Bar
    prog_width = int(1000 * ((scene_idx + 1) / total_scenes))
    draw.rounded_rectangle([40, 1840, 1040, 1860], radius=10, fill=(255, 255, 255, 70))
    draw.rounded_rectangle([40, 1840, 40 + prog_width, 1860], radius=10, fill=(255, 215, 0, 255))

    overlay_path = f"overlay_{scene_idx}.png"
    overlay.save(overlay_path)
    return overlay_path

async def synthesize_scene_voice(urdu_text, index):
    raw_audio = f"raw_voice_{index}.mp3"
    mastered_audio = f"voice_{index}.m4a"

    # Using Natural Pakistani Urdu Neural Voice with energetic speed (+12%)
    communicate = edge_tts.Communicate(urdu_text, voice="ur-PK-AsadNeural", rate="+12%", pitch="-2Hz")
    await communicate.save(raw_audio)

    # Studio Audio Mastering via FFmpeg: trims dead silence + adds warm podcast EQ & compression
    af_chain = (
        "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
        "highpass=f=75,"
        "bass=g=4:f=110,"
        "treble=g=3:f=4500,"
        "acompressor=threshold=-16dB:ratio=3:attack=5:release=60:makeup=3dB,"
        "apad=pad_dur=0.18"
    )
    cmd = [
        "ffmpeg", "-y", "-i", raw_audio,
        "-af", af_chain,
        "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        mastered_audio
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mastered_audio

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return max(float(out), 2.5)

def render_scene_clip(img_path, overlay_path, audio_path, index):
    duration = get_audio_duration(audio_path)
    clip_path = f"scene_clip_{index}.mp4"

    # Smooth continuous camera pan/motion on background while captions stay rock-solid
    direction = 1 if index % 2 == 0 else -1
    vf_filter = (
        f"[0:v]scale=1220:2168:force_original_aspect_ratio=increase,crop=1220:2168,"
        f"crop=1080:1920:'(in_w-out_w)/2+({direction}*45)*sin(t*0.9)':'(in_h-out_h)/2+60*cos(t*0.7)'[bg];"
        f"[bg][1:v]overlay=0:0,format=yuv420p[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration), "-i", img_path,
        "-loop", "1", "-t", str(duration), "-i", overlay_path,
        "-i", audio_path,
        "-filter_complex", vf_filter,
        "-map", "[v]", "-map", "2:a",
        "-r", "24",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "copy",
        "-shortest",
        clip_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return clip_path

def build_full_video(script_data):
    scenes = script_data["scenes"]
    badge = script_data.get("category_badge", "PHYSICS VS CHOONA")
    clip_files = []

    for idx, scene in enumerate(scenes):
        print(f"Processing Scene {idx+1}/{len(scenes)}: {scene['caption']}")
        audio_path = asyncio.run(synthesize_scene_voice(scene["tts_urdu"], idx))
        img_path = download_scene_image(scene["image_prompt"], idx)
        overlay_path = create_overlay_png(scene["caption"], badge, idx, len(scenes))
        clip_path = render_scene_clip(img_path, overlay_path, audio_path, idx)
        clip_files.append(clip_path)

    with open("concat_list.txt", "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")

    final_output = "final_reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "concat_list.txt",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        final_output
    ], check=True)
    return final_output

def send_to_telegram(video_path, script_data):
    print("Uploading HD video to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    caption = (
        f"🔥 *Title:* {script_data.get('title', 'Physics Scam Exposed!')}\n\n"
        f"📌 *Facebook Caption:*\n{script_data.get('title')}\n"
        f"{script_data.get('hashtags', '#PhysicsLogic #ReelsPakistan')}\n\n"
        f"✅ _1080x1920 Vertical HD | Studio Urdu Voice_"
    )
    with open(video_path, "rb") as vf:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
            files={"video": vf},
            timeout=120
        )
        print("Telegram Status:", resp.status_code, resp.text)

if __name__ == "__main__":
    data = generate_script_data()
    print("Generated Title:", data.get("title"))
    final_video = build_full_video(data)
    send_to_telegram(final_video, data)
