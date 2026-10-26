import os
import re
import json
import random
import asyncio
import subprocess
import urllib.parse
import textwrap
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Browser headers so servers NEVER block GitHub Actions
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

USED_TOPICS_FILE = "used_topics.json"

ALL_TOPICS = [
    {"topic": "70cc aur 125cc bike mein petrol average barhane wale Carburetor mistri ka choona aur Bernoulli Principle", "keywords": ["motorcycle engine", "mechanic repair", "fuel pump", "motorbike"]},
    {"topic": "Inverter AC ko 16 degree par chalane ka nuqsan, bijli ka bhari bill aur Thermodynamics", "keywords": ["air conditioner", "electricity meter", "summer heat", "money bills"]},
    {"topic": "Fridge ki gas har saal khatam hone ka mistri scam aur Closed Loop Thermodynamics", "keywords": ["refrigerator kitchen", "repairman tools", "ice cooling", "wallet cash"]},
    {"topic": "Gaadi aur bike ke tyre mein hawa kam rakhne ka nuqsan, petrol ki tabahi aur Rolling Friction", "keywords": ["car tire pressure", "asphalt road", "petrol station", "car wheel"]},
    {"topic": "Solar panels par mitti jamne se 40% bijli gayab hone ki haqeeqat aur Photoelectric Effect", "keywords": ["solar panels roof", "sunlight energy", "dust storm", "battery inverter"]},
    {"topic": "Gaadi ke radiator mein saada paani dalne se engine seize hone ka choona aur Boiling Point Elevation", "keywords": ["car hood smoke", "engine coolant", "auto mechanic", "boiling water"]},
    {"topic": "Fake 20,000 mAh Power Bank ka dhanda aur Lithium Ion Energy Density ki physics", "keywords": ["powerbank charging", "lithium battery", "electronics market", "smartphone"]},
    {"topic": "Sardi mein geyser ka bill double aane ki waja aur Thermal Insulation ka desi jugaar", "keywords": ["water heater", "winter cold", "gas flame", "plumber pipe"]},
    {"topic": "Mehngay Engine Flush aur Fuel Injector cleaner ka scam vs Fluid Detergency", "keywords": ["motor oil pouring", "car engine pistons", "auto parts shop", "cash money"]},
    {"topic": "UPS ki tubular battery jaldi kharab hone ka raaz aur Lead Acid Sulfation", "keywords": ["car battery acid", "power outage dark", "electrician wires", "sparks"]},
    {"topic": "3-Pin Plug mein Earth wire na lagane ki Pakistani ghalti aur AC Current Grounding", "keywords": ["electric socket plug", "electrical sparks", "house wiring", "shock"]},
    {"topic": "Microfiber kapray ki jagah purani banyan se gaadi saaf karne ka nuqsan aur Abrasion Physics", "keywords": ["washing car", "scratched paint", "luxury car shine", "auto detailing"]},
    {"topic": "Pressure Cooker ki seeti aur paharon par daal na galne ka raaz: Atmospheric Pressure", "keywords": ["cooking pot steam", "kitchen fire", "mountains clouds", "boiling food"]},
    {"topic": "LED Bulbs ke har 6 mahine baad jalne ka scam aur Heat Sink Thermal Dissipation", "keywords": ["light bulb glowing", "circuit board", "electric shop", "dark room"]},
    {"topic": "Bike ke silencer mein patakhay marne se engine valves tootne ki physics: Backpressure", "keywords": ["motorcycle exhaust fire", "biker street", "broken engine", "mechanic"]}
]

SYSTEM_PROMPT = """
You are Pakistan's top viral infotainment video creator (like ZemTV meets funny Desi street smarts).
Write a hilarious, high-energy, 60-second vertical video script (10 scenes) on the given topic.

Structure:
- Scenes 1-2: THE HOOK (Shocking financial "choona" + funny Desi observation + Physics twist).
- Scenes 3-5: THE SCIENCE / REAL STORY (How the physics law actually works in real life with vivid examples).
- Scenes 6-8: THE POCKET IMPACT (How local "ustaad", mechanics, or shopkeepers fool people and cost them 10,000+ rupees).
- Scenes 9-10: THE MORAL & PUNCHY CTA ("Physics koi ratta nahi, dunya ka Source Code hai! Follow daba do!").

STRICT RULES:
1. "tts_urdu": MUST be in PROPER URDU SCRIPT (اردو رسم الخط) using natural, conversational, witty Pakistani spoken Urdu. Transliterate English words into Urdu script (e.g. مکینک، انجن، فزکس، بیٹری، وولٹیج) so the Urdu voice pronounces them smoothly. Each scene MUST be 14 to 18 words long.
2. "caption_part1": First half of the punchline in Roman Urdu (3 to 4 words, ALL CAPS).
3. "caption_part2": Second half of the punchline in Roman Urdu (3 to 4 words, ALL CAPS).
4. "search_query_1": A 2-to-3 word English search query for a REAL stock photo/video for the first 3 seconds (e.g. "car mechanic engine", "burning electric wire", "counting money cash").
5. "search_query_2": A DIFFERENT 2-to-3 word English search query for the second 3 seconds (e.g. "broken smartphone screen", "petrol pump nozzle", "scientist laboratory").
6. "video_keyword": Single English category word for stock video search (choose from: "car", "mechanic", "phone", "money", "electricity", "fire", "water", "technology", "engine", "traffic", "tools", "battery").

Return ONLY valid raw JSON in this exact format:
{
  "title": "Catchy Roman Urdu Title",
  "hashtags": "#PhysicsLogic #DesiScam #UrduFacts #ReelsPakistan",
  "category_badge": "PHYSICS VS CHOONA",
  "scenes": [
    {
      "tts_urdu": "اردو رسم الخط میں قدرتی اور مزیدار جملہ۔",
      "caption_part1": "HAR 2 MAHINE BAAD",
      "caption_part2": "10,000 KA CHOONA?!",
      "search_query_1": "auto mechanic smiling",
      "search_query_2": "pouring engine oil",
      "video_keyword": "mechanic"
    }
  ]
}
"""

def pick_unused_topic():
    used = []
    if os.path.exists(USED_TOPICS_FILE):
        try:
            with open(USED_TOPICS_FILE, "r") as f:
                used = json.load(f)
        except Exception:
            used = []

    available = [t for t in ALL_TOPICS if t["topic"] not in used]
    if not available:
        used = []
        available = ALL_TOPICS

    chosen = random.choice(available)
    used.append(chosen["topic"])
    with open(USED_TOPICS_FILE, "w") as f:
        json.dump(used, f, indent=2)
    return chosen

def clean_json(raw_text):
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= 0:
        raise ValueError("No JSON object found")
    data = json.loads(text[start:end])
    if "scenes" in data and len(data["scenes"]) >= 8:
        return data
    raise ValueError("Too few scenes")

def generate_script_data():
    chosen = pick_unused_topic()
    topic_str = chosen["topic"]
    print(f"🔥 Today's Fresh Topic: {topic_str}")

    user_msg = f"Write a fresh, hilarious 10-scene 60-second script on: '{topic_str}'. Random Seed: {random.randint(10000,99999)}. Return ONLY valid JSON."

    # 1. Try Pollinations OpenAI Endpoint with Browser User-Agent
    for model_name in ["openai", "openai-large", "mistral"]:
        try:
            print(f"Requesting AI Script via model '{model_name}'...")
            resp = requests.post(
                "https://text.pollinations.ai/openai",
                headers={**HEADERS, "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.9,
                    "seed": random.randint(1, 999999)
                },
                timeout=65
            )
            if resp.status_code == 200:
                res_json = resp.json()
                content = res_json["choices"][0]["message"]["content"]
                return clean_json(content)
        except Exception as e:
            print(f"Model {model_name} attempt failed: {e}")

    # 2. Try Direct GET Pollinations Endpoint with Browser Headers
    try:
        print("Trying direct GET AI endpoint...")
        encoded = urllib.parse.quote(f"{SYSTEM_PROMPT}\n\n{user_msg}")
        url = f"https://text.pollinations.ai/{encoded}?model=openai&seed={random.randint(1,99999)}&json=true"
        resp = requests.get(url, headers=HEADERS, timeout=60)
        if resp.status_code == 200:
            return clean_json(resp.text)
    except Exception as e:
        print(f"GET endpoint error: {e}")

    # 3. Dynamic Topic-Specific Script Builder (Never repeats!)
    print("Building dynamic topic script...")
    return build_dynamic_script_for_topic(chosen)

def build_dynamic_script_for_topic(chosen):
    topic = chosen["topic"]
    kw = chosen["keywords"]
    return {
        "title": topic.split(" aur ")[0] + " Ka Asli Sach!",
        "hashtags": "#PhysicsLogic #DesiScam #PakistaniReels #ScienceUrdu #DimaagKholo",
        "category_badge": "USTAAD VS PHYSICS",
        "scenes": [
            {
                "tts_urdu": f"کیا آپ جانتے ہیں کہ ہر مہینے آپ کی جیب سے ہزاروں روپے کیسے نکالے جاتے ہیں؟ اور قصور آپ کی فزکس نہ جاننے کا ہے!",
                "caption_part1": "HAR MAHINE JEB SE",
                "caption_part2": "HAZAROON GAYAB?!",
                "search_query_1": kw[0],
                "search_query_2": "counting money cash",
                "video_keyword": "money"
            },
            {
                "tts_urdu": f"آج ہم بات کریں گے سب سے بڑے دیسی دھوکے کی، یعنی {topic} کے پیچھے چھپی اصلی سائنس کی!",
                "caption_part1": "DESI JUGAAR KA",
                "caption_part2": "SABSE BADA SCAM!",
                "search_query_1": kw[1],
                "search_query_2": kw[2],
                "video_keyword": "mechanic"
            },
            {
                "tts_urdu": "ہمارے گلی محلے کے استاد اکثر ایک ایسا مشورہ دیتے ہیں جو سننے میں بڑا سستا لگتا ہے مگر اندر ہی اندر مشین تباہ کر دیتا ہے۔",
                "caption_part1": "USTAAD KA SASTA",
                "caption_part2": "MASHWARA = TABAHI!",
                "search_query_1": "repairman tools workshop",
                "search_query_2": kw[0],
                "video_keyword": "tools"
            },
            {
                "tts_urdu": "فزکس کا بنیادی قانون کہتا ہے کہ توانائی نہ خود بنتی ہے اور نہ غائب ہوتی ہے، بلکہ غلط جگاڑ سے سیدھا ہیٹ اور نقصان میں بدل جاتی ہے!",
                "caption_part1": "ENERGY LOSS AUR",
                "caption_part2": "PHYSICS KA QANOON!",
                "search_query_1": "physics laboratory electricity",
                "search_query_2": "thermal heat camera",
                "video_keyword": "electricity"
            },
            {
                "tts_urdu": "جب آپ سستے جگاڑ کے چکر میں سسٹم کا قدرتی پریشر یا بیلنس چھیڑتے ہیں تو مشین کو دو گنا زیادہ زور لگانا پڑتا ہے۔",
                "caption_part1": "MACHINE PAR",
                "caption_part2": "DO GUNA LOAD!",
                "search_query_1": kw[2],
                "search_query_2": "engine gears closeup",
                "video_keyword": "engine"
            },
            {
                "tts_urdu": "شروع کے دس دن تو آپ خوش ہوتے ہیں کہ پیسے بچ گئے، مگر اندر کے پرزے رگڑ کھا کھا کر پورے ختم ہو رہے ہوتے ہیں۔",
                "caption_part1": "10 DIN KI KHUSHI",
                "caption_part2": "ANDAR SE PURZAY KHATAM!",
                "search_query_1": "broken metal gears",
                "search_query_2": kw[1],
                "video_keyword": "car"
            },
            {
                "tts_urdu": "پھر دو مہینے بعد جب آپ دوبارہ کاریگر کے پاس جاتے ہیں تو وہی استاد مسکرا کر دس ہزار روپے کا لمبا بل پکڑا دیتا ہے!",
                "caption_part1": "2 MAHINE BAAD",
                "caption_part2": "10,000 KA LAMBA BILL!",
                "search_query_1": "stressed man bill",
                "search_query_2": "auto repair shop",
                "video_keyword": "money"
            },
            {
                "tts_urdu": "دنیا بھر کے انجینئرز کروڑوں ڈالر لگا کر جو ڈیزائن بناتے ہیں، ہمارا دیسی استاد ایک پیچ کس سے اس کا جنازہ نکال دیتا ہے۔",
                "caption_part1": "ENGINEERS KI MEHNAT",
                "caption_part2": "VS EK PECHKAS!",
                "search_query_1": "engineer blueprint factory",
                "search_query_2": "screwdriver repair",
                "video_keyword": "technology"
            },
            {
                "tts_urdu": "اس لیے اگلی بار کسی کے سستے جگاڑ میں آنے سے پہلے فزکس کا حساب ضرور لگانا تاکہ آپ کی حلال کی کمائی محفوظ رہے۔",
                "caption_part1": "JUGAAR CHORO,",
                "caption_part2": "ASLI LOGIC SAMJHO!",
                "search_query_1": kw[3],
                "search_query_2": "smart man thinking",
                "video_keyword": "traffic"
            },
            {
                "tts_urdu": "فزکس کوئی بورنگ کتاب نہیں بلکہ اس دنیا کا سورس کوڈ ہے! روزانہ ایسی اصلی لاجک سیکھنے کے لیے ابھی فالو کا بٹن دبا دو!",
                "caption_part1": "DUNYA KA SOURCE CODE!",
                "caption_part2": "ABHI FOLLOW KARO!",
                "search_query_1": "futuristic technology hud",
                "search_query_2": "social media smartphone",
                "video_keyword": "phone"
            }
        ]
    }

USED_MEDIA_URLS = set()

def fetch_real_stock_video(keyword, filename):
    """Downloads a REAL HD Stock Video MP4 from Mixkit (No API key needed)."""
    slug = urllib.parse.quote(keyword.lower().strip())
    search_url = f"https://mixkit.co/free-stock-video/{slug}/"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            mp4_urls = re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)
            # Filter unused URLs
            fresh_urls = [u for u in mp4_urls if u not in USED_MEDIA_URLS]
            if not fresh_urls and mp4_urls:
                fresh_urls = mp4_urls
            if fresh_urls:
                chosen_url = random.choice(fresh_urls[:10])
                USED_MEDIA_URLS.add(chosen_url)
                vid_resp = requests.get(chosen_url, headers=HEADERS, timeout=30)
                if vid_resp.status_code == 200 and len(vid_resp.content) > 50000:
                    with open(filename, "wb") as f:
                        f.write(vid_resp.content)
                    print(f"  [✓] Downloaded Real Stock Video: {chosen_url}")
                    return filename
    except Exception as e:
        print(f"  [!] Mixkit video search skip ({keyword}): {e}")
    return None

def fetch_real_stock_photo(query, filename):
    """Downloads a REAL Stock Photo from Unsplash NAPI or Bing Images HD (Zero purple/yellow fallbacks!)."""
    # 1. Try Unsplash Public NAPI (High-Res Professional Photography)
    try:
        encoded = urllib.parse.quote(query)
        u_url = f"https://unsplash.com/napi/search/photos?query={encoded}&per_page=15&orientation=portrait"
        r = requests.get(u_url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            results = r.json().get("results", [])
            photo_urls = [item["urls"]["regular"] for item in results if "urls" in item and "regular" in item["urls"]]
            fresh = [u for u in photo_urls if u not in USED_MEDIA_URLS]
            if not fresh and photo_urls:
                fresh = photo_urls
            for img_url in fresh[:5]:
                USED_MEDIA_URLS.add(img_url)
                img_r = requests.get(img_url, headers=HEADERS, timeout=20)
                if img_r.status_code == 200 and len(img_r.content) > 15000:
                    with open(filename, "wb") as f:
                        f.write(img_r.content)
                    if verify_and_prepare_image(filename):
                        print(f"  [✓] Downloaded Unsplash HD Photo for '{query}'")
                        return filename
    except Exception as e:
        print(f"  [!] Unsplash search skip ({query}): {e}")

    # 2. Try Bing Images Async HD Search (Finds exact real-world objects/scenes)
    try:
        encoded = urllib.parse.quote(f"{query} high quality photography")
        b_url = f"https://www.bing.com/images/async?q={encoded}&first=1&count=20&adlt=off"
        r = requests.get(b_url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))&quot;', r.text)
            fresh = [u for u in urls if u not in USED_MEDIA_URLS]
            for img_url in fresh[:8]:
                try:
                    USED_MEDIA_URLS.add(img_url)
                    img_r = requests.get(img_url, headers=HEADERS, timeout=15)
                    if img_r.status_code == 200 and len(img_r.content) > 15000:
                        with open(filename, "wb") as f:
                            f.write(img_r.content)
                        if verify_and_prepare_image(filename):
                            print(f"  [✓] Downloaded Bing Real Photo for '{query}'")
                            return filename
                except Exception:
                    continue
    except Exception as e:
        print(f"  [!] Bing search skip ({query}): {e}")

    # 3. Broad Unsplash fallback (e.g., "technology", "car", "money")
    broad_url = f"https://unsplash.com/napi/search/photos?query=technology+mechanic&per_page=20"
    r = requests.get(broad_url, headers=HEADERS, timeout=20)
    results = r.json().get("results", [])
    for item in results:
        u = item["urls"]["regular"]
        if u not in USED_MEDIA_URLS:
            USED_MEDIA_URLS.add(u)
            img_r = requests.get(u, headers=HEADERS, timeout=20)
            with open(filename, "wb") as f:
                f.write(img_r.content)
            if verify_and_prepare_image(filename):
                return filename
    return filename

def verify_and_prepare_image(filepath):
    """Verifies image integrity and enhances contrast/color like a pro editor."""
    try:
        with Image.open(filepath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w < 250 or h < 250:
                return False
            # Pro Color Grading: slight contrast and color saturation boost
            im = ImageEnhance.Contrast(im).enhance(1.12)
            im = ImageEnhance.Color(im).enhance(1.18)
            im.save(filepath, "JPEG", quality=92)
        return True
    except Exception:
        return False

def create_caption_overlay(caption_text, badge_text, scene_idx, total_scenes, part_num):
    """Creates crisp Hormozi-style pop-up caption overlay PNG."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Subtle top & bottom cinematic shadow vignette
    for y in range(320):
        alpha = int(175 * (1 - y / 320))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1250, 1920):
        alpha = int(230 * ((y - 1250) / 670))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        badge_font = ImageFont.truetype(font_path, 36)
        cap_font = ImageFont.truetype(font_path, 72)
    except Exception:
        badge_font = ImageFont.load_default()
        cap_font = ImageFont.load_default()

    # Top Red/Gold Category Pill
    bw, bh = 560, 74
    bx, by = (1080 - bw) // 2, 105
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=37, fill=(220, 38, 38, 245), outline=(255, 255, 255, 230), width=3)
    draw.text((540, by + bh // 2), badge_text.upper(), font=badge_font, fill=(255, 255, 255, 255), anchor="mm")

    # Dynamic Pop Caption Box
    lines = textwrap.wrap(caption_text.upper(), width=16)
    y_start = 1470 - (len(lines) * 48)

    for i, line in enumerate(lines):
        y_pos = y_start + i * 100
        # Part 1 pops in Bright Yellow/White, Part 2 pops in Cyber Green/Yellow
        if part_num == 1:
            color = (255, 230, 0, 255) if i % 2 == 0 else (255, 255, 255, 255)
        else:
            color = (0, 255, 163, 255) if i % 2 == 0 else (255, 255, 255, 255)

        draw.text((540, y_pos), line, font=cap_font, fill=color, anchor="mm", stroke_width=12, stroke_fill=(0, 0, 0, 255))

    # Smooth Progress Bar at Bottom
    progress_fraction = (scene_idx + (0.5 if part_num == 1 else 1.0)) / total_scenes
    prog_w = int(1000 * progress_fraction)
    draw.rounded_rectangle([40, 1845, 1040, 1863], radius=9, fill=(255, 255, 255, 65))
    draw.rounded_rectangle([40, 1845, 40 + max(prog_w, 20), 1863], radius=9, fill=(255, 215, 0, 255))

    out_png = f"overlay_{scene_idx}_p{part_num}.png"
    overlay.save(out_png)
    return out_png

async def synthesize_scene_voice(urdu_text, index):
    raw_audio = f"raw_voice_{index}.mp3"
    mastered_audio = f"voice_{index}.m4a"

    communicate = edge_tts.Communicate(urdu_text, voice="ur-PK-AsadNeural", rate="+14%", pitch="-2Hz")
    await communicate.save(raw_audio)

    af_chain = (
        "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-45dB,"
        "highpass=f=75,"
        "bass=g=4:f=110,"
        "treble=g=3:f=4500,"
        "acompressor=threshold=-16dB:ratio=3:attack=5:release=60:makeup=3dB,"
        "apad=pad_dur=0.15"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_audio,
        "-af", af_chain,
        "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        mastered_audio
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mastered_audio

def get_audio_duration(audio_path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]).decode().strip()
    return max(float(out), 3.0)

def prepare_visual_subclip(media_path, is_video, overlay_path, duration, sub_idx, out_clip):
    """Renders a 2.5s - 3s B-roll shot with dynamic camera zoom/pan and caption overlay."""
    if is_video:
        # Real moving Stock Video B-Roll cropped to 9:16 vertical + overlay
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,eq=contrast=1.08:saturation=1.15[bg];"
            "[bg][1:v]overlay=0:0,format=yuv420p[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-t", str(duration), "-i", media_path,
            "-loop", "1", "-t", str(duration), "-i", overlay_path,
            "-filter_complex", vf,
            "-map", "[v]", "-r", "24", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            out_clip
        ]
    else:
        # High-Res Real Stock Photo with dynamic punch-in / pan motion
        zoom_expr = f"1.0+0.12*(t/{duration})" if sub_idx % 2 == 0 else f"1.12-0.10*(t/{duration})"
        vf = (
            f"[0:v]scale=1350:2400:force_original_aspect_ratio=increase,crop=1350:2400,"
            f"crop=w='1080/{zoom_expr}':h='1920/{zoom_expr}':x='(in_w-out_w)/2':y='(in_h-out_h)/2',"
            f"scale=1080:1920[bg];"
            f"[bg][1:v]overlay=0:0,format=yuv420p[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duration), "-i", media_path,
            "-loop", "1", "-t", str(duration), "-i", overlay_path,
            "-filter_complex", vf,
            "-map", "[v]", "-r", "24", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            out_clip
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def render_two_cut_scene(scene, idx, total_scenes, badge):
    """Splits each scene into 2 rapid visual cuts (Shot A + Shot B) synced to the full Urdu voiceover."""
    audio_path = asyncio.run(synthesize_scene_voice(scene["tts_urdu"], idx))
    total_dur = get_audio_duration(audio_path)
    half_dur = round(total_dur / 2.0, 2)
    rem_dur = round(total_dur - half_dur, 2)

    q1 = scene.get("search_query_1", "car mechanic")
    q2 = scene.get("search_query_2", "counting money")
    v_kw = scene.get("video_keyword", "mechanic")

    # Shot 1: Try Real Stock Video MP4 first, else Real HD Photo
    vid_file = fetch_real_stock_video(v_kw, f"stock_vid_{idx}.mp4")
    if vid_file:
        media1, is_vid1 = vid_file, True
    else:
        media1 = fetch_real_stock_photo(q1, f"photo_{idx}_1.jpg")
        is_vid1 = False

    # Shot 2: Always a specific Real HD Photo matching the second half of the sentence
    media2 = fetch_real_stock_photo(q2, f"photo_{idx}_2.jpg")

    ov1 = create_caption_overlay(scene.get("caption_part1", "ASLI HAQEEQAT"), badge, idx, total_scenes, 1)
    ov2 = create_caption_overlay(scene.get("caption_part2", "DEKHO KAISE!"), badge, idx, total_scenes, 2)

    sub1 = f"sub_{idx}_1.mp4"
    sub2 = f"sub_{idx}_2.mp4"
    prepare_visual_subclip(media1, is_vid1, ov1, half_dur, 0, sub1)
    prepare_visual_subclip(media2, False, ov2, rem_dur, 1, sub2)

    # Combine Shot 1 + Shot 2 + Scene Voiceover seamlessly
    list_file = f"scene_list_{idx}.txt"
    with open(list_file, "w") as f:
        f.write(f"file '{sub1}'\nfile '{sub2}'\n")

    scene_out = f"scene_final_{idx}.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_file,
        "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "copy", "-shortest",
        scene_out
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return scene_out

def build_full_video(script_data):
    scenes = script_data["scenes"]
    badge = script_data.get("category_badge", "PHYSICS VS CHOONA")
    scene_files = []

    for idx, scene in enumerate(scenes):
        print(f"🎬 Editing Scene {idx+1}/{len(scenes)} (2 Fast Cuts)...")
        s_file = render_two_cut_scene(scene, idx, len(scenes), badge)
        scene_files.append(s_file)

    with open("master_concat.txt", "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    final_output = "final_reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "master_concat.txt",
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k",
        final_output
    ], check=True)
    return final_output

def send_to_telegram(video_path, script_data):
    print("Uploading Pro-Edited Reel to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    caption = (
        f"🔥 *{script_data.get('title')}*\n\n"
        f"📲 *Facebook Reels Caption:*\n{script_data.get('title')}\n"
        f"{script_data.get('hashtags', '#PhysicsLogic #ReelsPakistan')}\n\n"
        f"✅ _20 Real Stock Cuts | 1080p Vertical | Studio Urdu Voice_"
    )
    with open(video_path, "rb") as vf:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
            files={"video": vf},
            timeout=120
        )
        print("Telegram Status:", resp.status_code)

if __name__ == "__main__":
    data = generate_script_data()
    print("Video Title:", data.get("title"))
    final_vid = build_full_video(data)
    send_to_telegram(final_vid, data)
