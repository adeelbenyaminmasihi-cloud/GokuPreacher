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
                "tts_urdu": "دنیا بھر کے انجینئرز کروڑوں ڈالر لگا کر جو ڈیزائن بناتے ہیں، ہمار
