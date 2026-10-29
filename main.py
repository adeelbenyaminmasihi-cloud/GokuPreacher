import os
import re
import json
import math
import wave
import struct
import random
import asyncio
import subprocess
import urllib.parse
import textwrap
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# =====================================================================
# ENVIRONMENT SECRETS & CONFIGURATION
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
GIPHY_API_KEY = (
    os.environ.get("GIPHY_API_KEY", "").strip()
    or os.environ.get("GIPHY_KEY", "").strip()
    or os.environ.get("GIPHY_SECRET", "").strip()
)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FB_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, application/xhtml+xml, image/webp, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

USED_TOPICS_FILE = "used_topics.json"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
USED_MEDIA_URLS = set()

# =====================================================================
# INFINITE SEED MATRIX (COMBINATORIAL 2-MINUTE DOCUMENTARY ENGINE)
# =====================================================================
SCIENCE_DOMAINS = [
    {
        "domain": "Thermodynamics & Heat Transfer",
        "nasa_tie": "James Webb Space Telescope Cryocooler & Apollo Heat Shields",
        "nasa_query": "spacecraft heat shield thermal",
        "everyday_hook": "Inverter AC, Car Radiators, aur Geyser ke bill ka choona",
        "scientist": "Sadi Carnot aur Lord Kelvin",
        "law": "Second Law of Thermodynamics & Entropy",
        "pixabay_vid": "thermal energy fire",
        "giphy_query": "heat explosion thermodynamics"
    },
    {
        "domain": "Fluid Dynamics & Aerodynamics",
        "nasa_tie": "SpaceX Raptor Engine Nozzle & NASA Supersonic Wind Tunnels",
        "nasa_query": "supersonic wind tunnel rocket engine",
        "everyday_hook": "Bike Carburetor jet, Water Pump impellers aur Fuel Injectors ka dhoka",
        "scientist": "Daniel Bernoulli aur Claude-Louis Navier",
        "law": "Bernoulli's Principle & Venturi Effect",
        "pixabay_vid": "jet engine turbine",
        "giphy_query": "airflow aerodynamics wind tunnel"
    },
    {
        "domain": "Electromagnetism & Power Grids",
        "nasa_tie": "International Space Station Solar Arrays & Ion Thrusters",
        "nasa_query": "international space station solar array",
        "everyday_hook": "Solar Inverter efficiency, Fake Power Saver boxes aur Transformer losses",
        "scientist": "Michael Faraday aur Nikola Tesla",
        "law": "Faraday's Law of Induction & Lenz's Law",
        "pixabay_vid": "high voltage electricity",
        "giphy_query": "electric arc tesla coil"
    },
    {
        "domain": "Tribology, Friction & Viscosity",
        "nasa_tie": "Mars Perseverance Rover Mechanical Bearings in Extreme Cold",
        "nasa_query": "mars rover perseverance wheel",
        "everyday_hook": "Engine Oil grades (20W-50 vs 5W-30), Tyre Rolling Resistance aur Fake Additives",
        "scientist": "Charles-Augustin de Coulomb aur Osborne Reynolds",
        "law": "Fluid Viscosity & Coefficient of Rolling Friction",
        "pixabay_vid": "engine pistons oil",
        "giphy_query": "gears friction machine"
    },
    {
        "domain": "Quantum Optics & Photovoltaics",
        "nasa_tie": "Hubble Space Telescope Mirrors & Deep Space Solar Sails",
        "nasa_query": "hubble space telescope mirror",
        "everyday_hook": "Solar Panel shading loss, Fiber Optic internet speed aur Laser sensors",
        "scientist": "Albert Einstein aur Max Planck",
        "law": "Photoelectric Effect & Quantum Photon Absorption",
        "pixabay_vid": "solar panels sunlight",
        "giphy_query": "laser beam photon light"
    },
    {
        "domain": "Materials Science & Metallurgy",
        "nasa_tie": "Saturn V Rocket Cryogenic Tanks & Titanium Alloy Fatigue",
        "nasa_query": "saturn v rocket launch",
        "everyday_hook": "Engine Block cracks, Fake Coolant corrosion aur Brake Disc warping",
        "scientist": "Robert Hooke aur William Rankine",
        "law": "Thermal Expansion, Cavitation & Metal Fatigue",
        "pixabay_vid": "molten metal steel factory",
        "giphy_query": "metal forging sparks"
    },
    {
        "domain": "Acoustics, Resonance & Vibrations",
        "nasa_tie": "Rocket Launch Acoustic Suppression Water Systems at Kennedy Space Center",
        "nasa_query": "rocket launch water sound suppression",
        "everyday_hook": "Car Suspension bushes, Engine Knocking (Detonation) aur Bearing failure",
        "scientist": "Ernst Chladni aur Heinrich Hertz",
        "law": "Mechanical Resonance & Acoustic Shockwaves",
        "pixabay_vid": "sound waves vibration",
        "giphy_query": "shockwave sound frequency"
    },
    {
        "domain": "Orbital Mechanics & Gyroscopic Stability",
        "nasa_tie": "Apollo Guidance Computer & Voyager Attitude Control Gyroscopes",
        "nasa_query": "apollo spacecraft guidance",
        "everyday_hook": "Wheel Balancing, Smartphone Gyroscope sensors aur High-speed Bike Wobble",
        "scientist": "Isaac Newton aur Leon Foucault",
        "law": "Conservation of Angular Momentum & Gyroscopic Precession",
        "pixabay_vid": "spinning wheel gyroscope",
        "giphy_query": "gyroscope gravity orbit"
    },
    {
        "domain": "Electrochemistry & Energy Storage",
        "nasa_tie": "Spacewalk Suit Lithium-Ion Battery Packs & Deep Space RTGs",
        "nasa_query": "astronaut spacewalk suit",
        "everyday_hook": "Tubular Battery acid gravity, Fast Charger heat damage aur Dry Battery scams",
        "scientist": "Alessandro Volta aur Walther Nernst",
        "law": "Electrochemical Sulfation & Internal Resistance (I2R Loss)",
        "pixabay_vid": "battery charging circuit",
        "giphy_query": "battery energy charge"
    },
    {
        "domain": "Pressure Systems & Phase Transitions",
        "nasa_tie": "Space Shuttle External Tank Liquid Oxygen & Vacuum Chambers",
        "nasa_query": "space shuttle external tank",
        "everyday_hook": "AC Compressor Closed-Loop Gas, Pressure Cooker bursts aur Radiator Caps",
        "scientist": "Robert Boyle aur Francois-Marie Raoult",
        "law": "Ideal Gas Law (PV=nRT) & Vapor Pressure Boiling Point Elevation",
        "pixabay_vid": "steam pressure gauge",
        "giphy_query": "pressure gauge explosion"
    }
]

ANGLES = [
    "Mistri ka Jugaar vs NASA Engineering",
    "Har Mahine 20,000 Rupay ka Choona aur Asli Physics",
    "Desi Myth Exposed: Science Kya Kehti Hai?",
    "100 Saal Purana Physics Qanoon Jo Aaj Bhi Aapki Jeb Bachata Hai",
    "Space Technology se Aapke Ghar ki Machine Tak ka Raaz",
    "Kyun Sasta Jugaar Engine Aur Machine Tabah Karta Hai?"
]


def load_used_topics():
    if os.path.exists(USED_TOPICS_FILE):
        try:
            with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_used_topic(topic_id):
    used = load_used_topics()
    if topic_id not in used:
        used.append(topic_id)
    used = used[-500:]
    with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2, ensure_ascii=False)


# =====================================================================
# INFINITE 2-MINUTE DOCUMENTARY SCRIPT GENERATOR (12 SCENES = ~120s)
# =====================================================================
def generate_infinite_documentary_script():
    used = load_used_topics()

    candidates = []
    for dom in SCIENCE_DOMAINS:
        for ang in ANGLES:
            seed_id = f"{dom['domain']} | {ang}"
            if seed_id not in used:
                candidates.append((seed_id, dom, ang))

    if not candidates:
        dom = random.choice(SCIENCE_DOMAINS)
        ang = random.choice(ANGLES)
        seed_id = f"{dom['domain']} | {ang} | Ep-{len(used)+1}"
    else:
        seed_id, dom, ang = random.choice(candidates)

    save_used_topic(seed_id)
    print(f"🧠 Selected Unique 2-Minute Documentary Seed: {seed_id}")

    if GEMINI_API_KEY:
        try:
            script = fetch_gemini_2min_script(dom, ang, used[-15:])
            if script and len(script.get("scenes", [])) >= 10:
                print(f"✨ Gemini Generated {len(script['scenes'])} Documentary Scenes (~2 Mins)!")
                return script
        except Exception as e:
            print(f"⚠️ Gemini generation fallback triggered: {e}")

    print("🎬 Building 12-Scene (2-Minute) Documentary via Procedural Science Engine...")
    return build_procedural_2min_documentary(dom, ang)


def fetch_gemini_2min_script(dom, ang, recent_topics):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
You are the chief documentary writer for 'Logic Aur Dhoka', a high-production Pakistani Urdu science & investigative documentary channel.
Create a gripping, non-repetitive 2-MINUTE documentary script (exactly 12 scenes, ~10 seconds per scene = 120 seconds total).

TOPIC DOMAIN: {dom['domain']}
LOCAL EVERYDAY CONNECTION: {dom['everyday_hook']}
NASA / SPACE CONNECTION: {dom['nasa_tie']}
CORE SCIENTIFIC LAW & SCIENTIST: {dom['law']} by {dom['scientist']}
DOCUMENTARY ANGLE: {ang}
RECENTLY COVERED TOPICS TO AVOID REPEATING: {json.dumps(recent_topics)}

REQUIREMENTS FOR 2-MINUTE LENGTH & QUALITY:
1. Write exactly 12 scenes structured across 4 Documentary Acts:
   - Scenes 1-2: ACT I - THE HOOK & STREET MYSTERY
   - Scenes 3-5: ACT II - THE SCIENTIFIC DISCOVERY & PHYSICS LAW
   - Scenes 6-8: ACT III - NASA SPACE ENGINEERING CONNECTION
   - Scenes 9-12: ACT IV - THE DESI SCAM EXPOSED & SCIENTIFIC VERDICT
2. Each scene's "tts_urdu" MUST be written in pure, natural Urdu script (اردو) and MUST be 24 to 30 words long (approx 10 seconds of rich documentary narration per scene, totaling ~2 minutes across 12 scenes).
3. Use an investigative, cinematic documentary tone. Never repeat sentences across scenes.
4. For each scene provide:
   - "act": Short English act badge (e.g. "ACT I: THE MYSTERY", "ACT III: NASA PHYSICS")
   - "tts_urdu": 24-30 words of gripping Urdu narration.
   - "caption_part1": Punchy Roman-Urdu/English headline for first half (max 24 chars).
   - "caption_part2": Punchy Roman-Urdu/English headline for second half (max 24 chars).
   - "media_source_pref": Choose "nasa", "pixabay", or "giphy".
   - "search_query_1": 2-4 English keywords for visual cut 1.
   - "search_query_2": 2-4 English keywords for visual cut 2.
   - "video_query": 1-3 English keywords for stock video or NASA video.
   - "sfx_type": Choose one of ["boom", "whoosh", "riser", "pulse"].

Return ONLY valid JSON matching this structure:
{{
  "title": "🧠 [Gripping Roman Urdu Title] | Logic Aur Dhoka Documentary",
  "tagline": "[Punchy 1-line hook with emojis]",
  "description": "[3-sentence summary explaining the physics law, NASA connection, and local scam]",
  "hashtags": "#LogicAurDhoka #UrduDocumentary #PhysicsLogic #NASAScience #PakistaniReels #ScienceFacts",
  "category_badge": "[SHORT CAPS BADGE]",
  "scenes": [ ... 12 scene objects ... ]
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "responseMimeType": "application/json"
        }
    }

    resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=75)
    if resp.status_code != 200:
        url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        resp = requests.post(url_fallback, headers={"Content-Type": "application/json"}, json=payload, timeout=75)

    if resp.status_code == 200:
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw_text = re.sub(r"^```json\s*|\s*```$", "", raw_text.strip())
        return json.loads(raw_text)
    raise RuntimeError(f"Gemini API HTTP {resp.status_code}: {resp.text[:160]}")


def build_procedural_2min_documentary(dom, ang):
    """12-Scene (~2 Minute / 120s) Documentary Engine."""
    d_name = dom["domain"]
    nasa_tie = dom["nasa_tie"]
    nasa_q = dom["nasa_query"]
    hook = dom["everyday_hook"]
    sci = dom["scientist"]
    law = dom["law"]
    p_vid = dom["pixabay_vid"]
    g_q = dom["giphy_query"]

    scenes = [
        # ACT I: THE HOOK & MYSTERY (Scenes 1-2)
        {
            "act": "ACT I: THE MYSTERY",
            "tts_urdu": "کیا آپ نے کبھی سوچا ہے کہ ہر چند مہینے بعد آپ کے گھر کی مشینیں، گاڑی کا انجن یا بجلی کا بل اچانک آپ کی جیب سے ہزاروں روپے کیسے نکال لیتا ہے؟",
            "caption_part1": "HAR CHAND MAHINE BAAD",
            "caption_part2": "HAZAROON KA NAYA KHARCHA?",
            "media_source_pref": "pixabay",
            "search_query_1": "counting money bills",
            "search_query_2": "broken car engine smoke",
            "video_query": p_vid,
            "sfx_type": "boom"
        },
        {
            "act": "ACT I: THE MYSTERY",
            "tts_urdu": "مارکیٹ میں بیٹھا کاریگر اسے آپ کی قسمت کا قصور بتاتا ہے، مگر اصل حقیقت یہ ہے کہ وہاں دیسی جگاڑ کے نام پر فزکس کے قانون کا قتل ہو رہا ہوتا ہے!",
            "caption_part1": "QISMAT KA QASOOR NAHI",
            "caption_part2": "PHYSICS KA QATAL HAI!",
            "media_source_pref": "giphy",
            "search_query_1": "mechanic workshop tools",
            "search_query_2": "physics equations blackboard",
            "video_query": "mechanic repair",
            "sfx_type": "whoosh"
        },
        # ACT II: SCIENTIFIC DISCOVERY & LAW (Scenes 3-5)
        {
            "act": "ACT II: SCIENCE HISTORY",
            "tts_urdu": "اس سائنسی راز کی شروعات یورپ کی قدیم لیبارٹریز میں ہوئی، جہاں عظیم سائنسدانوں نے رات دن کے تجربات سے توانائی، دباؤ اور حرارت کے قدرتی قوانین دریافت کیے۔",
            "caption_part1": "SCIENCE KI LABORATORY",
            "caption_part2": "AUR TAREEKHI KHOJ!",
            "media_source_pref": "pixabay",
            "search_query_1": "vintage science laboratory",
            "search_query_2": "engineering blueprint",
            "video_query": "science laboratory",
            "sfx_type": "riser"
        },
        {
            "act": "ACT II: SCIENCE HISTORY",
            "tts_urdu": "ان تجربات نے ثابت کیا کہ دنیا کی کوئی بھی مشین انسان کی مرضی سے نہیں چلتی، بلکہ جب تک اس میں توانائی اور دباؤ کا ریاضیاتی توازن رہے تبھی وہ محفوظ رہتی ہے۔",
            "caption_part1": law[:22].upper(),
            "caption_part2": "ENGINEERING KI BUNYAD!",
            "media_source_pref": "giphy",
            "search_query_1": g_q,
            "search_query_2": "precision metal gears",
            "video_query": "engineering",
            "sfx_type": "pulse"
        },
        {
            "act": "ACT II: SCIENCE HISTORY",
            "tts_urdu": "فزکس کے اس اصول کے مطابق جب کسی انجن یا سرکٹ کا قدرتی توازن بگاڑا جائے، تو بچنے والی توانائی غائب نہیں ہوتی بلکہ اندرونی رگڑ اور تباہی بن جاتی ہے۔",
            "caption_part1": "ENERGY GAYAB NAHI HOTI",
            "caption_part2": "ANDAR TABAHI MACHATI HAI!",
            "media_source_pref": "pixabay",
            "search_query_1": "fire sparks metal",
            "search_query_2": "pressure gauge danger",
            "video_query": "fire sparks",
            "sfx_type": "boom"
        },
        # ACT III: NASA SPACE ENGINEERING (Scenes 6-8)
        {
            "act": "ACT III: NASA PHYSICS",
            "tts_urdu": "اب ذرا دیکھیے کہ زمین سے سینکڑوں کلومیٹر اوپر خلا کی بے رحم ویکیوم میں ناسا کے انجینئرز اسی سائنسی قانون کو استعمال کر کے اربوں ڈالر کے مشن کیسے بچاتے ہیں!",
            "caption_part1": "KHALA MEIN NASA MISSION",
            "caption_part2": "PURE PHYSICS PROTECTION!",
            "media_source_pref": "nasa",
            "search_query_1": nasa_q,
            "search_query_2": "astronaut spacewalk",
            "video_query": nasa_q,
            "sfx_type": "riser"
        },
        {
            "act": "ACT III: NASA PHYSICS",
            "tts_urdu": "جب راکٹ کے انجن سے تین ہزار ڈگری کی آگ نکلتی ہے یا سیٹلائٹ خلا میں گھومتا ہے، تو وہاں دباؤ اور حرارت کے صرف ایک فیصد فرق سے پورا مشن تباہ ہو سکتا ہے۔",
            "caption_part1": "3,000 DEGREE KI AAG",
            "caption_part2": "GALTI KI GUNJAISH ZERO!",
            "media_source_pref": "nasa",
            "search_query_1": "rocket engine test fire",
            "search_query_2": "mission control nasa",
            "video_query": "rocket launch",
            "sfx_type": "boom"
        },
        {
            "act": "ACT III: NASA PHYSICS",
            "tts_urdu": "سب سے حیرت انگیز حقیقت یہ ہے کہ جو فزکس ناسا کے راکٹ اور خلائی اسٹیشن کو بچاتی ہے، بالکل وہی فزکس آپ کی گاڑی، اے سی اور سولر سسٹم کے اندر بھی کام کرتی ہے!",
            "caption_part1": "NASA WALI SAME PHYSICS",
            "caption_part2": "AAPKE GHAR KI MACHINE MEIN!",
            "media_source_pref": "nasa",
            "search_query_1": "international space station",
            "search_query_2": "car engine closeup",
            "video_query": p_vid,
            "sfx_type": "pulse"
        },
        # ACT IV: DESI SCAM EXPOSED & VERDICT (Scenes 9-12)
        {
            "act": "ACT IV: SCAM EXPOSED",
            "tts_urdu": "مگر المیہ تب ہوتا ہے جب ہم کمپنی کی اس باریک انجینئرنگ کو کسی ایسے کاریگر کے حوالے کرتے ہیں جو بغیر کسی سائنسی میٹر کے پیچ کس گھما کر سستا جگاڑ لگاتا ہے۔",
            "caption_part1": "BINA METER KE JUGAAR",
            "caption_part2": "AUR PHYSICS BALANCE KHATAM!",
            "media_source_pref": "pixabay",
            "search_query_1": "local mechanic wrench",
            "search_query_2": "electrical wires sparks",
            "video_query": "mechanic",
            "sfx_type": "whoosh"
        },
        {
            "act": "ACT IV: SCAM EXPOSED",
            "tts_urdu": "شروع کے چند ہفتے تو سب ٹھیک لگتا ہے، لیکن اندر ہی اندر غیر معمولی حرارت، زنگ اور رگڑ قیمتی پرزوں کو گلا کر پچاس ہزار کا نیا خرچہ کھڑا کر دیتی ہے!",
            "caption_part1": "500 BACHANE KE CHAKKAR MEIN",
            "caption_part2": "50,000 KA SEEDHA NUQSAN!",
            "media_source_pref": "giphy",
            "search_query_1": "overheating car radiator",
            "search_query_2": "empty wallet money",
            "video_query": "smoke engine",
            "sfx_type": "boom"
        },
        {
            "act": "ACT IV: THE VERDICT",
            "tts_urdu": "اس نقصان سے بچنے کا واحد سائنسی حل یہ ہے کہ کبھی فیکٹری کے سٹینڈرڈ، کولنٹ، آئل گریڈ یا سرکٹ کو بائی پاس نہ کروائیں اور ہر کام میٹر کی ریڈنگ سے پرکھیں۔",
            "caption_part1": "ASLI SCIENTIFIC SOLUTION:",
            "caption_part2": "FACTORY STANDARD NA CHHEREIN!",
            "media_source_pref": "pixabay",
            "search_query_1": "digital multimeter gauge",
            "search_query_2": "clean solar panels",
            "video_query": "technology",
            "sfx_type": "pulse"
        },
        {
            "act": "ACT IV: THE VERDICT",
            "tts_urdu": "یاد رکھیں، فزکس کوئی بورنگ مضمون نہیں بلکہ اس کائنات کا سورس کوڈ ہے! ایسی مزید معلوماتی ڈاکیومنٹریز کے لیے لاجک اور دھوکہ پیج کو ابھی فالو اور شیئر کریں!",
            "caption_part1": "LOGIC AUR DHOKA DOCUMENTARY",
            "caption_part2": "ABHI FOLLOW AUR SHARE KAREIN!",
            "media_source_pref": "nasa",
            "search_query_1": "galaxy stars universe",
            "search_query_2": "smartphone social media",
            "video_query": "space galaxy",
            "sfx_type": "riser"
        }
    ]

    return {
        "title": f"🧠 {d_name}: {ang} | 2-Min Documentary",
        "tagline": f"{hook} — NASA Engineering aur {law} ki roshni mein asli haqeeqat! 🚀🔬",
        "description": f"Is 2-minute documentary mein samjhein ke {sci} ka {law} kaise {nasa_tie} se le kar aapke ghar ki machines ({hook}) tak kaam karta hai.",
        "hashtags": "#LogicAurDhoka #UrduDocumentary #PhysicsLogic #NASAScience #EngineeringFacts #DesiScamExposed #ScienceUrdu #ViralReels",
        "category_badge": d_name.split("&")[0].strip().upper()[:22],
        "scenes": scenes
    }


# =====================================================================
# MULTI-SOURCE MEDIA FETCHERS (NASA API + GIPHY API + PIXABAY + BING)
# =====================================================================
def fetch_nasa_media(query, filename, prefer_video=True):
    """Fetches royalty-free HD Space/Engineering Videos or Photos from https://images-api.nasa.gov."""
    if not query:
        return None, False

    encoded = urllib.parse.quote(query.strip())
    media_types = "video,image" if prefer_video else "image"
    api_url = f"https://images-api.nasa.gov/search?q={encoded}&media_type={media_types}&page_size=15"

    try:
        r = requests.get(api_url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            items = r.json().get("collection", {}).get("items", [])
            random.shuffle(items)
            for item in items:
                data_list = item.get("data", [])
                if not data_list:
                    continue
                m_type = data_list[0].get("media_type", "")
                nasa_id = data_list[0].get("nasa_id", "")
                href = item.get("href", "")

                if prefer_video and m_type == "video" and href:
                    try:
                        asset_r = requests.get(href, headers=HEADERS, timeout=15)
                        if asset_r.status_code == 200:
                            asset_urls = asset_r.json()
                            mp4_links = [
                                u for u in asset_urls
                                if isinstance(u, str) and u.endswith(".mp4") and ("~mobile" in u or "~medium" in u or "~preview" in u)
                            ]
                            if not mp4_links:
                                mp4_links = [u for u in asset_urls if isinstance(u, str) and u.endswith(".mp4")]
                            for vid_url in mp4_links:
                                if vid_url not in USED_MEDIA_URLS:
                                    USED_MEDIA_URLS.add(vid_url)
                                    vid_url_clean = vid_url.replace(" ", "%20")
                                    vr = requests.get(vid_url_clean, headers=HEADERS, timeout=30)
                                    if vr.status_code == 200 and len(vr.content) > 50000:
                                        vid_out = filename if filename.endswith(".mp4") else f"{filename}.mp4"
                                        with open(vid_out, "wb") as f:
                                            f.write(vr.content)
                                        print(f"  [🚀 NASA VIDEO] Downloaded '{nasa_id}' for '{query}'")
                                        return vid_out, True
                    except Exception:
                        pass

                links = item.get("links", [])
                for lnk in links:
                    if lnk.get("render") == "image":
                        img_url = lnk.get("href", "")
                        if img_url and img_url not in USED_MEDIA_URLS:
                            USED_MEDIA_URLS.add(img_url)
                            ir = requests.get(img_url.replace(" ", "%20"), headers=HEADERS, timeout=15)
                            if ir.status_code == 200 and len(ir.content) > 15000:
                                img_out = filename if filename.endswith(".jpg") else f"{filename}.jpg"
                                with open(img_out, "wb") as f:
                                    f.write(ir.content)
                                if verify_and_grade_image(img_out):
                                    print(f"  [🛰️ NASA PHOTO] Downloaded '{nasa_id}' for '{query}'")
                                    return img_out, False
    except Exception as e:
        print(f"  [!] NASA API skip ({query}): {e}")

    return None, False


def fetch_giphy_mp4(query, filename):
    """Fetches dynamic MP4 visual loops using GIPHY_API_KEY."""
    if not GIPHY_API_KEY or not query:
        return None

    try:
        encoded = urllib.parse.quote(query.strip())
        g_url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={encoded}&limit=15&rating=g"
        r = requests.get(g_url, headers=HEADERS, timeout=18)
        if r.status_code == 200:
            data = r.json().get("data", [])
            random.shuffle(data)
            for item in data:
                images = item.get("images", {})
                mp4_url = (
                    images.get("original", {}).get("mp4")
                    or images.get("downsized_small", {}).get("mp4")
                    or images.get("fixed_height", {}).get("mp4")
                )
                if mp4_url and mp4_url not in USED_MEDIA_URLS:
                    USED_MEDIA_URLS.add(mp4_url)
                    vr = requests.get(mp4_url, headers=HEADERS, timeout=25)
                    if vr.status_code == 200 and len(vr.content) > 20000:
                        with open(filename, "wb") as f:
                            f.write(vr.content)
                        print(f"  [⚡ GIPHY MP4] Downloaded dynamic loop for '{query}'")
                        return filename
    except Exception as e:
        print(f"  [!] GIPHY API skip ({query}): {e}")
    return None


def fetch_contextual_stock_video(query, filename, pref="pixabay"):
    """Routes video requests across NASA, GIPHY, Pixabay, and Mixkit."""
    if not query:
        return None

    if pref == "nasa" or any(k in query.lower() for k in ["nasa", "rocket", "space", "satellite", "orbit", "solar flare", "mars", "astronaut"]):
        nasa_file, is_vid = fetch_nasa_media(query, filename, prefer_video=True)
        if nasa_file and is_vid:
            return nasa_file

    if pref == "giphy" and GIPHY_API_KEY:
        g_file = fetch_giphy_mp4(query, filename)
        if g_file:
            return g_file

    if PIXABAY_API_KEY:
        try:
            encoded = urllib.parse.quote(query.strip())
            p_url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={encoded}&safesearch=true&per_page=15"
            r = requests.get(p_url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for hit in hits:
                    videos = hit.get("videos", {})
                    vid_url = (
                        videos.get("medium", {}).get("url")
                        or videos.get("small", {}).get("url")
                        or videos.get("large", {}).get("url")
                    )
                    if vid_url and vid_url not in USED_MEDIA_URLS:
                        USED_MEDIA_URLS.add(vid_url)
                        vr = requests.get(vid_url, headers=HEADERS, timeout=30)
                        if vr.status_code == 200 and len(vr.content) > 50000:
                            with open(filename, "wb") as f:
                                f.write(vr.content)
                            print(f"  [🎬 PIXABAY VIDEO] Downloaded for '{query}'")
                            return filename
        except Exception as e:
            print(f"  [!] Pixabay video skip ({query}): {e}")

    if GIPHY_API_KEY:
        g_file = fetch_giphy_mp4(query, filename)
        if g_file:
            return g_file

    slug = urllib.parse.quote(query.lower().strip().split()[0])
    search_url = f"https://mixkit.co/free-stock-video/{slug}/"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            mp4_urls = re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)
            fresh_urls = [u for u in mp4_urls if u not in USED_MEDIA_URLS]
            if fresh_urls:
                chosen_url = random.choice(fresh_urls[:5])
                USED_MEDIA_URLS.add(chosen_url)
                vid_resp = requests.get(chosen_url, headers=HEADERS, timeout=25)
                if vid_resp.status_code == 200 and len(vid_resp.content) > 50000:
                    with open(filename, "wb") as f:
                        f.write(vid_resp.content)
                    print(f"  [✓ Mixkit Video] Downloaded for '{query}'")
                    return filename
    except Exception:
        pass
    return None


def fetch_exact_scene_photo(query, filename, pref="pixabay"):
    """Fetches HD Photos from NASA, Pixabay, or Bing HD."""
    if pref == "nasa" or any(k in query.lower() for k in ["nasa", "space", "rocket", "satellite", "planet", "astronaut", "galaxy", "telescope", "mars"]):
        nasa_img, is_vid = fetch_nasa_media(query, filename, prefer_video=False)
        if nasa_img and not is_vid:
            return nasa_img

    if PIXABAY_API_KEY:
        try:
            encoded = urllib.parse.quote(query.strip())
            p_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={encoded}&image_type=photo&safesearch=true&per_page=15"
            r = requests.get(p_url, headers=HEADERS, timeout=18)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for hit in hits:
                    img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                    if img_url and img_url not in USED_MEDIA_URLS:
                        USED_MEDIA_URLS.add(img_url)
                        img_r = requests.get(img_url, headers=HEADERS, timeout=15)
                        if img_r.status_code == 200 and len(img_r.content) > 15000:
                            with open(filename, "wb") as f:
                                f.write(img_r.content)
                            if verify_and_grade_image(filename):
                                print(f"  [📸 PIXABAY PHOTO] Downloaded for '{query}'")
                                return filename
        except Exception as e:
            print(f"  [!] Pixabay photo skip ({query}): {e}")

    nasa_img, is_vid = fetch_nasa_media(query, filename, prefer_video=False)
    if nasa_img and not is_vid:
        return nasa_img

    try:
        encoded = urllib.parse.quote(f"{query} realistic photography")
        b_url = f"https://www.bing.com/images/async?q={encoded}&first=1&count=15&adlt=off&qft=+filterui:imagesize-large"
        r = requests.get(b_url, headers=HEADERS, timeout=18)
        if r.status_code == 200:
            urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))&quot;', r.text)
            fresh = [u for u in urls if u not in USED_MEDIA_URLS]
            for img_url in fresh[:6]:
                try:
                    USED_MEDIA_URLS.add(img_url)
                    img_r = requests.get(img_url, headers=HEADERS, timeout=12)
                    if img_r.status_code == 200 and len(img_r.content) > 18000:
                        with open(filename, "wb") as f:
                            f.write(img_r.content)
                        if verify_and_grade_image(filename):
                            print(f"  [🌐 BING HD PHOTO] Downloaded for '{query}'")
                            return filename
                except Exception:
                    continue
    except Exception:
        pass

    img = Image.new("RGB", (1080, 1920), (14, 19, 32))
    img.save(filename, "JPEG", quality=92)
    return filename


def verify_and_grade_image(filepath):
    try:
        with Image.open(filepath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w < 220 or h < 220:
                return False
            im = ImageEnhance.Contrast(im).enhance(1.16)
            im = ImageEnhance.Color(im).enhance(1.15)
            im = ImageEnhance.Brightness(im).enhance(0.96)
            im.save(filepath, "JPEG", quality=92)
        return True
    except Exception:
        return False


# =====================================================================
# PURE-PYTHON CRASH-PROOF CINEMATIC SFX & BGM SYNTHESIZER
# =====================================================================
def write_synthesized_wav(filename, duration_sec, sample_fn, sample_rate=44100):
    """Writes a 16-bit mono WAV file using pure Python math (zero external filter errors)."""
    num_samples = int(duration_sec * sample_rate)
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            t = i / float(sample_rate)
            val = max(-1.0, min(1.0, sample_fn(t, duration_sec)))
            frames.extend(struct.pack("<h", int(val * 32767.0)))
        wf.writeframes(frames)
    return filename


def generate_cinematic_sfx_library():
    """Generates studio-clean documentary SFX in pure Python."""
    sfx_files = {}

    # 1. Sub-Bass Impact Boom
    sfx_files["boom"] = write_synthesized_wav(
        "sfx_boom.wav", 1.2,
        lambda t, d: 0.75 * math.exp(-3.2 * t) * math.sin(2.0 * math.pi * (85.0 * math.exp(-1.5 * t) + 34.0) * t)
    )

    # 2. Transition Whoosh
    sfx_files["whoosh"] = write_synthesized_wav(
        "sfx_whoosh.wav", 0.85,
        lambda t, d: 0.55 * math.sin(math.pi * (t / d)) * math.sin(2.0 * math.pi * (180.0 + 320.0 * (t / d)) * t)
    )

    # 3. Documentary Riser
    sfx_files["riser"] = write_synthesized_wav(
        "sfx_riser.wav", 1.1,
        lambda t, d: 0.5 * (t / d) * math.sin(2.0 * math.pi * (110.0 + 180.0 * (t / d) ** 2) * t)
    )

    # 4. Telemetry Science Pulse
    sfx_files["pulse"] = write_synthesized_wav(
        "sfx_pulse.wav", 0.75,
        lambda t, d: 0.45 * math.exp(-5.0 * t) * (math.sin(2.0 * math.pi * 440.0 * t) + 0.5 * math.sin(2.0 * math.pi * 220.0 * t))
    )

    return sfx_files


async def synthesize_scene_voice(urdu_text, index, sfx_path=None):
    """Synthesizes HD Urdu Documentary Voiceover and mixes synced transition SFX."""
    raw_audio = f"raw_voice_{index}.mp3"
    voice_clean = f"voice_clean_{index}.m4a"
    mastered_audio = f"voice_{index}.m4a"

    communicate = edge_tts.Communicate(urdu_text, voice="ur-PK-AsadNeural", rate="+2%", pitch="-3Hz")
    await communicate.save(raw_audio)

    af_chain = (
        "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
        "highpass=f=70,"
        "bass=g=4.5:f=105,"
        "treble=g=3.0:f=4800,"
        "acompressor=threshold=-16dB:ratio=3.2:attack=5:release=70:makeup=3.5dB,"
        "apad=pad_dur=0.30"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_audio,
        "-af", af_chain,
        "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        voice_clean
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if sfx_path and os.path.exists(sfx_path):
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", voice_clean,
                "-i", sfx_path,
                "-filter_complex", "[1:a]volume=0.22[sfx];[0:a][sfx]amix=inputs=2:duration=first:dropout_transition=1[a]",
                "-map", "[a]", "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
                mastered_audio
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return mastered_audio
        except Exception:
            pass

    return voice_clean


# =====================================================================
# DOCUMENTARY HUD OVERLAY (WITH ACT INDICATOR & PROGRESS BAR)
# =====================================================================
def create_burned_hud_overlay(caption_text, badge_text, act_text, scene_idx, total_scenes, part_num):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(320):
        alpha = int(185 * (1 - y / 320))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1140, 1920):
        alpha = int(230 * ((y - 1140) / 780))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    try:
        act_font = ImageFont.truetype(FONT_BOLD, 28)
        badge_font = ImageFont.truetype(FONT_BOLD, 36)
        cap_font = ImageFont.truetype(FONT_BOLD, 62)
    except Exception:
        act_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()
        cap_font = ImageFont.load_default()

    bw, bh = 660, 78
    bx, by = (1080 - bw) // 2, 78
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=39, fill=(210, 25, 25, 245), outline=(255, 255, 255, 240), width=4)
    b_text = badge_text.upper()[:24]
    b_bbox = draw.textbbox((0, 0), b_text, font=badge_font)
    b_tw, b_th = b_bbox[2] - b_bbox[0], b_bbox[3] - b_bbox[1]
    draw.text((bx + (bw - b_tw) // 2, by + (bh - b_th) // 2 - 4), b_text, font=badge_font, fill=(255, 255, 255, 255))

    act_str = f"🎬 {act_text.upper()}  •  SCENE {scene_idx + 1}/{total_scenes}"
    a_bbox = draw.textbbox((0, 0), act_str, font=act_font)
    a_tw = a_bbox[2] - a_bbox[0]
    draw.rounded_rectangle([(1080 - a_tw) // 2 - 24, 172, (1080 + a_tw) // 2 + 24, 218], radius=14, fill=(15, 23, 42, 220), outline=(0, 230, 255, 190), width=2)
    draw.text(((1080 - a_tw) // 2, 180), act_str, font=act_font, fill=(0, 240, 255, 255))

    lines = textwrap.wrap(caption_text.upper(), width=16)
    if not lines:
        lines = ["ASLI DOCUMENTARY!"]

    line_height = 88
    total_text_h = len(lines) * line_height
    box_y1 = 1365 - (total_text_h // 2)
    box_y2 = box_y1 + total_text_h + 44

    draw.rounded_rectangle([50, box_y1, 1030, box_y2], radius=26, fill=(8, 12, 22, 235), outline=(255, 215, 0, 230), width=4)

    for i, line in enumerate(lines):
        t_bbox = draw.textbbox((0, 0), line, font=cap_font)
        tw = t_bbox[2] - t_bbox[0]
        tx = (1080 - tw) // 2
        ty = box_y1 + 20 + (i * line_height)

        if part_num == 1:
            fill_col = (255, 230, 0, 255) if i == 0 else (255, 255, 255, 255)
        else:
            fill_col = (0, 255, 165, 255) if i == 0 else (255, 230, 0, 255)

        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, 5)]:
            draw.text((tx + dx, ty + dy), line, font=cap_font, fill=(0, 0, 0, 255))
        draw.text((tx, ty), line, font=cap_font, fill=fill_col)

    progress_fraction = (scene_idx + (0.5 if part_num == 1 else 1.0)) / total_scenes
    prog_w = int(980 * progress_fraction)
    draw.rounded_rectangle([50, 1835, 1030, 1855], radius=10, fill=(255, 255, 255, 75))
    draw.rounded_rectangle([50, 1835, 50 + max(prog_w, 25), 1855], radius=10, fill=(255, 215, 0, 255))

    out_png = f"hud_{scene_idx}_p{part_num}.png"
    overlay.save(out_png)
    return out_png


def get_audio_duration(audio_path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]).decode().strip()
    return max(float(out), 3.5)


def prepare_visual_subclip(media_path, is_video, overlay_path, duration, sub_idx, out_clip):
    if is_video:
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,eq=contrast=1.08:saturation=1.14[bg];"
            "[bg][1:v]overlay=0:0:shortest=1,format=yuv420p[v]"
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
        direction = 1 if sub_idx % 2 == 0 else -1
        vf = (
            f"[0:v]scale=1240:2200:force_original_aspect_ratio=increase,crop=1240:2200,setsar=1,"
            f"crop=1080:1920:'(in_w-out_w)/2+({direction}*50)*sin(t*0.9)':'(in_h-out_h)/2+65*cos(t*0.7)'[bg];"
            f"[bg][1:v]overlay=0:0:shortest=1,format=yuv420p[v]"
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

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        safe_vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];"
            "[bg][1:v]overlay=0:0:shortest=1,format=yuv420p[v]"
        )
        safe_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duration), "-i", media_path,
            "-loop", "1", "-t", str(duration), "-i", overlay_path,
            "-filter_complex", safe_vf,
            "-map", "[v]", "-r", "24", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            out_clip
        ]
        subprocess.run(safe_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_two_cut_scene(scene, idx, total_scenes, badge, sfx_library):
    sfx_type = scene.get("sfx_type", "whoosh")
    sfx_file = sfx_library.get(sfx_type)

    audio_path = asyncio.run(synthesize_scene_voice(scene["tts_urdu"], idx, sfx_file))
    total_dur = get_audio_duration(audio_path)
    half_dur = round(total_dur / 2.0, 2)
    rem_dur = round(total_dur - half_dur, 2)

    q1 = scene.get("search_query_1", "science laboratory")
    q2 = scene.get("search_query_2", "engineering machine")
    v_q = scene.get("video_query", q1)
    pref = scene.get("media_source_pref", "pixabay")
    act_text = scene.get("act", "DOCUMENTARY")

    vid_file = fetch_contextual_stock_video(v_q, f"stock_vid_{idx}.mp4", pref=pref) if v_q else None
    if vid_file:
        media1, is_vid1 = vid_file, True
    else:
        media1 = fetch_exact_scene_photo(q1, f"photo_{idx}_1.jpg", pref=pref)
        is_vid1 = False

    media2 = None
    is_vid2 = False
    if idx % 2 == 1 and GIPHY_API_KEY:
        g_clip = fetch_giphy_mp4(q2, f"giphy_{idx}_2.mp4")
        if g_clip:
            media2, is_vid2 = g_clip, True

    if not media2:
        media2 = fetch_exact_scene_photo(q2, f"photo_{idx}_2.jpg", pref=pref)
        is_vid2 = False

    ov1 = create_burned_hud_overlay(scene.get("caption_part1", "SCIENCE LOGIC"), badge, act_text, idx, total_scenes, 1)
    ov2 = create_burned_hud_overlay(scene.get("caption_part2", "ASLI HAQEEQAT"), badge, act_text, idx, total_scenes, 2)

    sub1 = f"sub_{idx}_1.mp4"
    sub2 = f"sub_{idx}_2.mp4"
    prepare_visual_subclip(media1, is_vid1, ov1, half_dur, 0, sub1)
    prepare_visual_subclip(media2, is_vid2, ov2, rem_dur, 1, sub2)

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

    for tmp in [sub1, sub2, ov1, ov2]:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

    return scene_out


def prepare_bgm_file():
    """Downloads dramatic ambient drone or synthesizes a pure-Python 12-second loopable documentary score."""
    bgm_urls = [
        "https://actions.google.com/sounds/v1/ambiences/cyberpunk_drone.ogg",
        "https://actions.google.com/sounds/v1/science_fiction/sci_fi_drone.ogg"
    ]
    for url in bgm_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200 and len(r.content) > 20000:
                with open("bgm_loop.ogg", "wb") as f:
                    f.write(r.content)
                return "bgm_loop.ogg"
        except Exception:
            continue

    # Pure-Python synthesized 10-second loopable ambient documentary score
    return write_synthesized_wav(
        "bgm_loop.wav", 10.0,
        lambda t, d: (
            0.25 * math.sin(2.0 * math.pi * 55.0 * t)
            + 0.15 * math.sin(2.0 * math.pi * 82.4 * t)
            + 0.12 * math.sin(2.0 * math.pi * 110.0 * t) * (0.6 + 0.4 * math.sin(2.0 * math.pi * 0.2 * t))
        )
    )


def build_full_video(script_data):
    scenes = script_data["scenes"]
    badge = script_data.get("category_badge", "PHYSICS DOCUMENTARY")
    sfx_library = generate_cinematic_sfx_library()
    scene_files = []

    for idx, scene in enumerate(scenes):
        print(f"🎬 Scene {idx+1}/{len(scenes)} [{scene.get('act', 'DOC')}]: '{scene['caption_part1']} | {scene['caption_part2']}'")
        s_file = render_two_cut_scene(scene, idx, len(scenes), badge, sfx_library)
        scene_files.append(s_file)

    with open("master_concat.txt", "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    raw_output = "raw_reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "master_concat.txt",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        raw_output
    ], check=True)

    total_vid_dur = get_audio_duration(raw_output)
    print(f"⏱️ Total Documentary Runtime: {round(total_vid_dur / 60.0, 2)} minutes ({int(total_vid_dur)} seconds)")

    print("🎵 Mixing Cinematic Documentary Score...")
    final_output = "final_reel.mp4"
    try:
        bgm_loop = prepare_bgm_file()
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", raw_output,
            "-stream_loop", "-1", "-i", bgm_loop,
            "-filter_complex", "[1:a]volume=0.11[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-maxrate", "2500k", "-bufsize", "5000k",
            "-c:a", "aac", "-b:a", "192k",
            final_output
        ]
        subprocess.run(mix_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return final_output
    except Exception as e:
        print(f"BGM mix fallback note: {e}")

    subprocess.run(["cp", raw_output, final_output], check=False)
    return final_output


# =====================================================================
# FACEBOOK & TELEGRAM PUBLISHING
# =====================================================================
def resolve_fb_page_credentials():
    page_id = FB_PAGE_ID
    token = FB_ACCESS_TOKEN

    m = re.search(r'(\d{8,})', page_id)
    if m:
        page_id = m.group(1)

    try:
        r = requests.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": token},
            timeout=15
        )
        if r.status_code == 200:
            pages = r.json().get("data", [])
            if pages:
                for p in pages:
                    if p.get("id") == page_id or p.get("name", "").lower() in page_id.lower():
                        print(f"  [✓] Matched Facebook Page: {p.get('name')} ({p.get('id')})")
                        return p.get("id"), p.get("access_token", token)
                first_page = pages[0]
                print(f"  [✓] Using Default Facebook Page: {first_page.get('name')} ({first_page.get('id')})")
                return first_page.get("id"), first_page.get("access_token", token)
    except Exception as e:
        print(f"  [!] FB account check note: {e}")

    return page_id, token


def upload_to_facebook(video_path, script_data):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️ Facebook credentials missing in environment variables.")
        return False, "FB Secrets missing"

    page_id, page_token = resolve_fb_page_credentials()
    print(f"🚀 Uploading 2-Minute Documentary to Facebook Page ID: {page_id}...")
    url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"

    title = script_data.get("title", "Logic Aur Dhoka - 2 Min Science Documentary")
    tagline = script_data.get("tagline", "Physics is dunya ka Source Code hai!")
    description = script_data.get("description", "Rozana aisi real-world science documentaries dekhne ke liye Logic Aur Dhoka ko follow karein!")
    hashtags = script_data.get("hashtags", "#LogicAurDhoka #PhysicsLogic #NASAScience #UrduDocumentary")

    full_post_description = (
        f"{title}\n\n"
        f"⚡ {tagline}\n\n"
        f"📌 {description}\n\n"
        f"👉 Follow Logic Aur Dhoka for daily real-world physics & investigative documentaries!\n\n"
        f"{hashtags}"
    )

    try:
        with open(video_path, "rb") as vf:
            payload = {
                "access_token": page_token,
                "title": title,
                "description": full_post_description
            }
            files = {"source": vf}
            resp = requests.post(url, data=payload, files=files, timeout=360)
            print("Facebook API Status:", resp.status_code, resp.text)
            if resp.status_code == 200 and "id" in resp.json():
                vid_id = resp.json()["id"]
                return True, f"Published on FB! (Video ID: {vid_id})"
            err_msg = resp.json().get("error", {}).get("message", resp.text[:140])
            return False, f"FB Error: {err_msg}"
    except Exception as e:
        print(f"Facebook Upload Exception: {e}")
        return False, str(e)[:120]


def send_to_telegram(video_path, script_data, fb_ok, fb_msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing.")
        return

    print("📲 Uploading 2-Min Documentary & Status Report to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    fb_status_line = f"✅ Facebook Auto-Post: {fb_msg}" if fb_ok else f"⚠️ Facebook Auto-Post: {fb_msg}"

    caption = (
        f"🔥 {script_data.get('title')}\n\n"
        f"⚡ Tagline:\n{script_data.get('tagline')}\n\n"
        f"📝 Description:\n{script_data.get('description')}\n\n"
        f"🏷️ Viral Tags:\n{script_data.get('hashtags')}\n\n"
        f"🛰️ Media Sources: NASA + Pixabay + GIPHY\n"
        f"{fb_status_line}"
    )[:1000]

    with open(video_path, "rb") as vf:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "supports_streaming": True},
            files={"video": vf},
            timeout=240
        )
        print("Telegram Upload Status:", resp.status_code, resp.text[:200])

    if resp.status_code != 200:
        print("Retrying Telegram upload without caption...")
        with open(video_path, "rb") as vf:
            requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"video": vf},
                timeout=240
            )


if __name__ == "__main__":
    data = generate_infinite_documentary_script()
    print("Documentary Title:", data.get("title"))
    final_vid = build_full_video(data)
    fb_success, fb_info = upload_to_facebook(final_vid, data)
    send_to_telegram(final_vid, data, fb_success, fb_info)
