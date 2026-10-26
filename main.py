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
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FB_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

USED_TOPICS_FILE = "used_topics.json"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ALL_TOPICS = [
    {
        "topic": "70cc aur 125cc bike mein petrol average barhane wale Carburetor mistri ka choona",
        "tagline": "Mistri ka ek pechkas aap ke engine ka 15,000 ka kharcha kaise nikalta hai? 🛠️🔥",
        "description": "Jab mistri carburetor ka jet band karta hai to petrol bachne ke bajaye engine overheat ho kar piston aur valves jala deta hai. Asli Stoichiometric Ratio aur Bernoulli Physics samjhein!",
        "badge": "BIKE PETROL SCAM",
        "hook_visual_1": "motorcycle engine",
        "hook_visual_2": "counting money",
        "scientist_urdu": "سترہ سو اڑتیس میں سوئس سائنسدان ڈینیئل برنولی نے فلوئڈ ڈائنامکس کا وہ اصول بنایا جس پر آج آپ کی بائیک کا کاربوریٹر اور ہوائی جہاز چلتے ہیں!",
        "scientist_cap1": "1738 MEIN SCIENTIST",
        "scientist_cap2": "BERNOULLI KA QANOON!",
        "sci_visual_1": "science laboratory",
        "sci_visual_2": "motorcycle engine",
        "fact_urdu": "برنولی پرنسپل کے مطابق پٹرول کو مکمل جلنے کے لیے چودہ حصے ہوا اور ایک حصہ پٹرول کا پرفیکٹ بیلنس چاہیے ہوتا ہے جسے سٹوكیومیٹرک ریشو کہتے ہیں۔",
        "fact_cap1": "14 HISSE HAWA AUR",
        "fact_cap2": "1 HISSA PETROL BALANCE!",
        "fact_visual_1": "fire sparks",
        "fact_visual_2": "car engine",
        "scam_urdu": "مگر جب محلے کا استاد پیچ کس گھما کر کاربوریٹر کا جیٹ ضرورت سے زیادہ بند کرتا ہے تو پٹرول بچنے کے بجائے انجن شدید اوور ہیٹ ہو جاتا ہے!",
        "scam_cap1": "MISTRI KA PECHKAS",
        "scam_cap2": "AUR ENGINE OVERHEAT!",
        "scam_visual_1": "mechanic repair",
        "scam_visual_2": "smoke engine",
        "loss_visual_1": "broken machine gears",
        "loss_visual_2": "auto repair shop",
        "vid_queries": ["motorcycle", "mechanic", "fuel"]
    },
    {
        "topic": "Inverter AC ko 16 degree par chalane ka nuqsan aur Thermodynamics ka qanoon",
        "tagline": "AC ko 16 degree par rakhne se kamra jaldi thanda nahi hota, sirf 50,000 ka bill aata hai! ❄️💸",
        "description": "Thermodynamics ke mutabiq AC ki grill se nikalne wali hawa hamesha ek jaisi thandi hoti hai. 16 degree par compressor kabhi trip nahi karta aur bijli ka bill double ho jata hai!",
        "badge": "AC BILL CHOONA",
        "hook_visual_1": "air conditioner",
        "hook_visual_2": "electricity bill money",
        "scientist_urdu": "اٹھارہ سو چوبیس میں فرانسیسی انجینئر سادی کارنو نے تھرمو ڈائنامکس کا وہ قانون دریافت کیا جس سے آج دنیا کے تمام اے سی اور فریج ٹھنڈک پیدا کرتے ہیں!",
        "scientist_cap1": "1824 KA THERMODYNAMICS",
        "scientist_cap2": "COOLING KA ASLI QANOON!",
        "sci_visual_1": "physics laboratory",
        "sci_visual_2": "air conditioning unit",
        "fact_urdu": "فزکس کہتی ہے کہ اے سی سولہ ڈگری کرنے سے کمرہ جلدی ٹھنڈا نہیں ہوتا، کیونکہ اے سی کی نالیوں سے نکلنے والی ہوا ہمیشہ ایک جیسی ٹھنڈی ہوتی ہے۔",
        "fact_cap1": "16 DEGREE SE KAMRA",
        "fact_cap2": "JALDI THANDA NAHI HOTA!",
        "fact_visual_1": "remote control",
        "fact_visual_2": "ice cold frost",
        "scam_urdu": "جب آپ ریموٹ سولہ پر رکھتے ہیں تو انورٹر اے سی کا کمپریسر کبھی سلو نہیں ہوتا اور مہینے کے آخر میں پچاس ہزار کا بل آپ کے ہوش اڑا دیتا ہے!",
        "scam_cap1": "COMPRESSOR LAGATAR CHALTA HAI",
        "scam_cap2": "50,000 KA BIJLI BILL!",
        "scam_visual_1": "electricity meter",
        "scam_visual_2": "stressed man headache",
        "loss_visual_1": "electronic circuit board",
        "loss_visual_2": "cash money",
        "vid_queries": ["electricity", "money", "technology"]
    },
    {
        "topic": "Fridge ki gas har saal khatam hone ka mistri scam aur Closed Loop Physics",
        "tagline": "Fridge ki gas petrol ki tarah kabhi khatam nahi hoti! Mistri ke 5,000 ke choonay se bachein 🧊🔧",
        "description": "Fridge ka compressor ek sealed Closed-Loop system hota hai. Garmiyon mein aksar sirf 200 rupay ka relay ya capacitor kharab hota hai magar gas bharne ke naam par 5,000 le liye jate hain!",
        "badge": "FRIDGE GAS SCAM",
        "hook_visual_1": "refrigerator kitchen",
        "hook_visual_2": "repairman tools",
        "scientist_urdu": "انیس سو تیس میں جب فریون گیس دریافت ہوئی تو انجینئرز نے فریج کے کمپریسر کو ایک مکمل سیل بند کلوزڈ لوپ سسٹم بنایا جس سے گیس کبھی ختم ہو ہی نہیں سکتی!",
        "scientist_cap1": "1930 KA CLOSED LOOP",
        "scientist_cap2": "GAS KABHI KHATAM NAHI HOTI!",
        "sci_visual_1": "copper pipes",
        "sci_visual_2": "electric motor",
        "fact_urdu": "آئیڈیل گیس لا کے مطابق فریج کی گیس پٹرول کی طرح جلتی نہیں ہے، بلکہ وہ بیس سال تک انہی تانبے کے پائپوں میں گھوم کر ٹھنڈک بناتی رہتی ہے۔",
        "fact_cap1": "GAS JALTI NAHI HAI,",
        "fact_cap2": "20 SAAL PIPE MEIN GHOOMTI HAI!",
        "fact_visual_1": "ice cubes frost",
        "fact_visual_2": "pressure gauge",
        "scam_urdu": "اکثر گرمیوں میں صرف دو سو روپے کا ریلے یا کیپیسٹر خراب ہوتا ہے، مگر کاریگر آ کر کہتا ہے باجی گیس اڑ گئی ہے اور پانچ ہزار روپے جیب میں ڈال لیتا ہے!",
        "scam_cap1": "200 KA RELAY KHARAB,",
        "scam_cap2": "5,000 GAS KA JHOOTA BILL!",
        "scam_visual_1": "electronics repair",
        "scam_visual_2": "welding torch",
        "loss_visual_1": "technician tools",
        "loss_visual_2": "paying cash money",
        "vid_queries": ["kitchen", "tools", "ice"]
    },
    {
        "topic": "Gaadi ke radiator mein saada paani dalne se engine tabah hone ki physics",
        "tagline": "Radiator mein saada paani dalna = 40,000 ke Head Gasket ka kharcha! 🚗💨",
        "description": "Saada paani 100 degree par ubal kar bhaap aur zang banata hai, jabke Coolant Raoult's Law ke tehat 130 degree tak engine ko safe rakhta hai.",
        "badge": "RADIATOR SCAM",
        "hook_visual_1": "car engine smoke",
        "hook_visual_2": "pouring water car",
        "scientist_urdu": "اٹھارہ سو چھیاسی میں فرانسیسی کیمسٹ فرانسوا راؤلٹ نے ثابت کیا کہ خالص پانی میں گلائیکول کیمیکل ملانے سے اس کا ابلنے کا پوائنٹ حیرت انگیز طور پر بڑھ جاتا ہے!",
        "scientist_cap1": "1886 KA RAOULT'S LAW:",
        "scientist_cap2": "BOILING POINT KI PHYSICS!",
        "sci_visual_1": "chemistry lab",
        "sci_visual_2": "motor oil liquid",
        "fact_urdu": "سادہ نلکے کا پانی سو ڈگری پر ابل کر بھاپ بن جاتا ہے اور لوہے کے انجن کو اندر سے زنگ لگا دیتا ہے، جبکہ اصلی کولنٹ ایک سو تیس ڈگری تک انجن بچاتا ہے۔",
        "fact_cap1": "SAADA PAANI = 100°C BHAAP",
        "fact_cap2": "AUR ENGINE MEIN ZANG!",
        "fact_visual_1": "rusty metal",
        "fact_visual_2": "boiling water steam",
        "scam_urdu": "پٹرول پمپ اور ورکشاپ والے کہتے ہیں استاد جی سادہ پانی ڈالو سب چلتا ہے، اور چھ مہینے بعد ہیڈ گیسکٹ جلنے کا چالیس ہزار کا بل بن جاتا ہے!",
        "scam_cap1": "USTAAD KA SAADA PAANI",
        "scam_cap2": "40,000 HEAD GASKET KA BILL!",
        "scam_visual_1": "auto mechanic car",
        "scam_visual_2": "broken car engine",
        "loss_visual_1": "car breakdown road",
        "loss_visual_2": "counting money",
        "vid_queries": ["car", "mechanic", "smoke"]
    },
    {
        "topic": "Solar panels par mitti jamne se 40% bijli gayab hone ka raaz aur Photoelectric Effect",
        "tagline": "Lakhon ka Solar System sirf 5 minute ki mitti saaf na karne se 40% bijli gawa deta hai! ☀️⚡",
        "description": "Einstein ke Photoelectric Effect aur Series Circuit physics ke mutabiq agar solar plate ke ek kone par bhi mitti jam jaye to poori string ka current gir jata hai.",
        "badge": "SOLAR PANEL LOGIC",
        "hook_visual_1": "solar panels roof",
        "hook_visual_2": "electric power meter",
        "scientist_urdu": "انیس سو پانچ میں البرٹ آئن سٹائن نے فوٹو الیکٹرک ایفیکٹ دریافت کیا جس پر انہیں نوبل پرائز ملا، اور آج آپ کا سولر پینل اسی اصول پر دھوپ سے بجلی بناتا ہے!",
        "scientist_cap1": "1905 EINSTEIN NOBEL PRIZE:",
        "scientist_cap2": "PHOTOELECTRIC EFFECT!",
        "sci_visual_1": "physics blackboard",
        "sci_visual_2": "sunlight solar panel",
        "fact_urdu": "فزکس کے مطابق سولر پلیٹ کے سیلز سیریز میں جڑے ہوتے ہیں۔ اگر ایک کونے پر بھی مٹی جم جائے تو وہ پورا سیل رکاوٹ بن کر تیس فیصد بجلی کھا جاتا ہے۔",
        "fact_cap1": "EK KONE PAR MITTI =",
        "fact_cap2": "30% BIJLI SEEDHA GAYAB!",
        "fact_visual_1": "solar cell",
        "fact_visual_2": "dust storm sand",
        "scam_urdu": "لوگ لاکھوں روپے کا سولر لگوا کر مہینوں دھوتے نہیں اور پھر دکاندار کو گالیاں دیتے ہیں، حالانکہ قصور صرف پانچ منٹ پانی نہ مارنے کا ہوتا ہے!",
        "scam_cap1": "LAKHON KA SOLAR SYSTEM",
        "scam_cap2": "SIRF MITTI KI WAJA SE FAIL!",
        "scam_visual_1": "washing water spray",
        "scam_visual_2": "clean solar energy",
        "loss_visual_1": "battery charger",
        "loss_visual_2": "bright light bulb",
        "vid_queries": ["solar", "sunlight", "energy"]
    },
    {
        "topic": "Tyre mein hawa kam rakhne ka desi jugaar, petrol ki tabahi aur Rolling Friction",
        "tagline": "Tyre mein 5 point kam hawa rakhne se har mahine hazaroon ka extra petrol jalta hai! 🛞⛽",
        "description": "Coulomb ke Rolling Friction qanoon ke mutabiq kam hawa wala tyre sarak se chipak kar chalta hai jis se engine par 15% zyada load aur petrol kharch hota hai.",
        "badge": "TYRE PRESSURE LOGIC",
        "hook_visual_1": "car tire wheel",
        "hook_visual_2": "petrol station fuel",
        "scientist_urdu": "سترہ سو ننانوے میں چارلس کولمب نے رگڑ یعنی فریکشن کے قوانین پیش کیے جن سے پتہ چلا کہ زمین اور پہیے کا ملاپ آپ کی گاڑی کے پٹرول کا فیصلہ کرتا ہے!",
        "scientist_cap1": "1799 COULOMB'S LAW:",
        "scientist_cap2": "ROLLING FRICTION KI SCIENCE!",
        "sci_visual_1": "car wheel asphalt",
        "sci_visual_2": "pressure gauge tire",
        "fact_urdu": "جب ٹائر میں ہوا صرف پانچ پوائنٹ کم ہوتی ہے تو رولنگ ریزسٹنس بڑھ جاتی ہے۔ ٹائر سڑک کے ساتھ چپک کر چلتا ہے اور انجن پندرہ فیصد زیادہ پٹرول پیتا ہے۔",
        "fact_cap1": "5 POINT KAM HAWA =",
        "fact_cap2": "15% ZYADA PETROL KI TABAHI!",
        "fact_visual_1": "highway road traffic",
        "fact_visual_2": "car dashboard fuel",
        "scam_urdu": "ٹائر والا کہتا ہے بھائی ہوا کم رکھو جھٹکے نہیں لگیں گے، مگر اس آرام کے چکر میں ہر مہینے ہزاروں کا پٹرول جلتا ہے اور ٹائر جلدی پھٹ جاتا ہے!",
        "scam_cap1": "TYRE WALE KA MASHWARA",
        "scam_cap2": "AUR HAR MAHINE HAZAROON LOSS!",
        "scam_visual_1": "mechanic tire repair",
        "scam_visual_2": "damaged car tire",
        "loss_visual_1": "new car tires",
        "loss_visual_2": "paying cash money",
        "vid_queries": ["car", "traffic", "wheel"]
    }
]

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

def generate_script_data():
    chosen = pick_unused_topic()
    topic = chosen["topic"]
    badge = chosen["badge"]
    print(f"🔥 Building Scene-Matched Script for: {topic}")

    return {
        "title": f"🧠 {topic} | Logic Aur Dhoka",
        "tagline": chosen["tagline"],
        "description": chosen["description"],
        "hashtags": "#LogicAurDhoka #PhysicsLogic #DesiScam #UrduFacts #ReelsPakistan #DimaagKholo #ScienceUrdu #ViralReels",
        "category_badge": badge,
        "scenes": [
            {
                "tts_urdu": "ہر دو مہینے بعد آپ کی جیب سے ہزاروں روپے کیسے نکالے جاتے ہیں؟ اور حیرت کی بات یہ ہے کہ اس میں غلطی کاریگر کی نہیں، آپ کی فزکس کی ہے!",
                "caption_part1": "HAR 2 MAHINE BAAD",
                "caption_part2": "HAZAROON KA CHOONA?!",
                "search_query_1": chosen["hook_visual_1"],
                "search_query_2": chosen["hook_visual_2"],
                "video_query": chosen["vid_queries"][0]
            },
            {
                "tts_urdu": chosen["scientist_urdu"],
                "caption_part1": chosen["scientist_cap1"],
                "caption_part2": chosen["scientist_cap2"],
                "search_query_1": chosen["sci_visual_1"],
                "search_query_2": chosen["sci_visual_2"],
                "video_query": ""
            },
            {
                "tts_urdu": chosen["fact_urdu"],
                "caption_part1": chosen["fact_cap1"],
                "caption_part2": chosen["fact_cap2"],
                "search_query_1": chosen["fact_visual_1"],
                "search_query_2": chosen["fact_visual_2"],
                "video_query": chosen["vid_queries"][1]
            },
            {
                "tts_urdu": "جب تک کسی مشین یا انجن میں توانائی اور حرارت کا یہ قدرتی توازن برقرار رہتا ہے، وہ سالوں سال بغیر کسی خرچے کے مکھن کی طرح چلتی ہے۔",
                "caption_part1": "JAB TAK PHYSICS BALANCE HAI",
                "caption_part2": "MACHINE MAKHAN CHALTI HAI!",
                "search_query_1": chosen["sci_visual_2"],
                "search_query_2": "metal gears machine",
                "video_query": ""
            },
            {
                "tts_urdu": chosen["scam_urdu"],
                "caption_part1": chosen["scam_cap1"],
                "caption_part2": chosen["scam_cap2"],
                "search_query_1": chosen["scam_visual_1"],
                "search_query_2": chosen["scam_visual_2"],
                "video_query": chosen["vid_queries"][2]
            },
            {
                "tts_urdu": "دکاندار یا استاد بڑے پیار سے کہتا ہے کہ بھائی جان یہ سستا جگاڑ لگا لو، سب چلتا ہے، اور آپ تھوڑے سے پیسے بچانے کے چکر میں پھنس جاتے ہو!",
                "caption_part1": "USTAAD KI MEETHI BAAT:",
                "caption_part2": "'BHAI SAB CHALTA HAI!'",
                "search_query_1": "auto mechanic workshop",
                "search_query_2": chosen["scam_visual_1"],
                "video_query": ""
            },
            {
                "tts_urdu": "شروع کے چند ہفتے تو سب ٹھیک لگتا ہے، مگر اندر ہی اندر فزکس کا قانون اپنا کام دکھاتا ہے اور قیمتی پرزے رگڑ کھا کر جلنا شروع ہو جاتے ہیں۔",
                "caption_part1": "CHAND HAFTE BAAD",
                "caption_part2": "ANDAR SE PURZAY TABAH!",
                "search_query_1": chosen["loss_visual_1"],
                "search_query_2": "fire sparks welding",
                "video_query": ""
            },
            {
                "tts_urdu": "پھر جب آپ دوبارہ مارکیٹ جاتے ہو تو پانچ سو بچانے کے چکر میں سیدھا دس سے پندرہ ہزار روپے کا نیا خرچہ آپ کے ہاتھ میں تھما دیا جاتا ہے!",
                "caption_part1": "500 BACHANE KE CHAKKAR MEIN",
                "caption_part2": "15,000 KA FATKA LAGA!",
                "search_query_1": chosen["loss_visual_2"],
                "search_query_2": "paying cash money",
                "video_query": ""
            },
            {
                "tts_urdu": "ایلون مسک کے راکٹ سے لے کر آپ کے گھر کی عام مشینوں تک، ہر جگہ فزکس کا یہی پکا حساب چلتا ہے جو کسی دیسی جگاڑ کو معاف نہیں کرتا۔",
                "caption_part1": "SPACE ROCKET SE LE KAR",
                "caption_part2": "APKE GHAR KI MACHINE TAK!",
                "search_query_1": "rocket launch space",
                "search_query_2": chosen["hook_visual_1"],
                "video_query": "rocket"
            },
            {
                "tts_urdu": "فزکس کوئی بورڈ امتحان کا بورنگ نصاب نہیں بلکہ اس دنیا کا سورس کوڈ ہے! روزانہ ایسی اصلی لاجک سیکھنے کے لیے لاجک اور دھوکہ پیج کو ابھی فالو کر لو!",
                "caption_part1": "LOGIC AUR DHOKA:",
                "caption_part2": "ABHI FOLLOW DABAO! 🚀",
                "search_query_1": "smartphone social media",
                "search_query_2": "technology brain network",
                "video_query": ""
            }
        ]
    }

USED_MEDIA_URLS = set()

def fetch_contextual_stock_video(query, filename):
    """Fetches HD Stock Video using Official PIXABAY_API_KEY first, then Mixkit fallback."""
    if not query:
        return None

    # 1. Official Pixabay Video API
    if PIXABAY_API_KEY:
        try:
            encoded = urllib.parse.quote(query.strip())
            p_url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={encoded}&safesearch=true&per_page=15"
            r = requests.get(p_url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
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
                            print(f"  [✓] Pixabay Stock Video downloaded for '{query}'")
                            return filename
        except Exception as e:
            print(f"  [!] Pixabay video skip ({query}): {e}")

    # 2. Mixkit Fallback
    slug = urllib.parse.quote(query.lower().strip())
    search_url = f"https://mixkit.co/free-stock-video/{slug}/"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=18)
        if resp.status_code == 200:
            mp4_urls = re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)
            fresh_urls = [u for u in mp4_urls if u not in USED_MEDIA_URLS]
            if fresh_urls:
                chosen_url = fresh_urls[0]
                USED_MEDIA_URLS.add(chosen_url)
                vid_resp = requests.get(chosen_url, headers=HEADERS, timeout=25)
                if vid_resp.status_code == 200 and len(vid_resp.content) > 50000:
                    with open(filename, "wb") as f:
                        f.write(vid_resp.content)
                    print(f"  [✓] Mixkit Stock Video downloaded for '{query}'")
                    return filename
    except Exception:
        pass
    return None

def fetch_exact_scene_photo(query, filename):
    """Fetches HD Stock Photo using Official PIXABAY_API_KEY first, then Bing HD fallback."""
    # 1. Official Pixabay Image API
    if PIXABAY_API_KEY:
        try:
            encoded = urllib.parse.quote(query.strip())
            p_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={encoded}&image_type=photo&safesearch=true&per_page=15"
            r = requests.get(p_url, headers=HEADERS, timeout=18)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                    if img_url and img_url not in USED_MEDIA_URLS:
                        USED_MEDIA_URLS.add(img_url)
                        img_r = requests.get(img_url, headers=HEADERS, timeout=15)
                        if img_r.status_code == 200 and len(img_r.content) > 15000:
                            with open(filename, "wb") as f:
                                f.write(img_r.content)
                            if verify_and_grade_image(filename):
                                print(f"  [✓] Pixabay HD Photo downloaded for '{query}'")
                                return filename
        except Exception as e:
            print(f"  [!] Pixabay photo skip ({query}): {e}")

    # 2. Bing HD Search Fallback
    try:
        encoded = urllib.parse.quote(f"{query} realistic photo")
        b_url = f"https://www.bing.com/images/async?q={encoded}&first=1&count=15&adlt=off&qft=+filterui:imagesize-large"
        r = requests.get(b_url, headers=HEADERS, timeout=18)
        if r.status_code == 200:
            urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))&quot;', r.text)
            fresh = [u for u in urls if u not in USED_MEDIA_URLS]
            for img_url in fresh[:5]:
                try:
                    USED_MEDIA_URLS.add(img_url)
                    img_r = requests.get(img_url, headers=HEADERS, timeout=12)
                    if img_r.status_code == 200 and len(img_r.content) > 18000:
                        with open(filename, "wb") as f:
                            f.write(img_r.content)
                        if verify_and_grade_image(filename):
                            print(f"  [✓] Bing HD Photo downloaded for '{query}'")
                            return filename
                except Exception:
                    continue
    except Exception:
        pass

    img = Image.new("RGB", (1080, 1920), (22, 28, 42))
    img.save(filename, "JPEG", quality=92)
    return filename

def verify_and_grade_image(filepath):
    try:
        with Image.open(filepath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w < 220 or h < 220:
                return False
            im = ImageEnhance.Contrast(im).enhance(1.14)
            im = ImageEnhance.Color(im).enhance(1.18)
            im.save(filepath, "JPEG", quality=93)
        return True
    except Exception:
        return False

def create_burned_hud_overlay(caption_text, badge_text, scene_idx, total_scenes, part_num):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(280):
        alpha = int(170 * (1 - y / 280))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1180, 1920):
        alpha = int(220 * ((y - 1180) / 740))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    try:
        badge_font = ImageFont.truetype(FONT_BOLD, 38)
        cap_font = ImageFont.truetype(FONT_BOLD, 64)
    except Exception:
        badge_font = ImageFont.load_default()
        cap_font = ImageFont.load_default()

    bw, bh = 620, 82
    bx, by = (1080 - bw) // 2, 95
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=41, fill=(220, 30, 30, 250), outline=(255, 255, 255, 240), width=4)
    b_text = badge_text.upper()
    b_bbox = draw.textbbox((0, 0), b_text, font=badge_font)
    b_tw, b_th = b_bbox[2] - b_bbox[0], b_bbox[3] - b_bbox[1]
    draw.text((bx + (bw - b_tw) // 2, by + (bh - b_th) // 2 - 4), b_text, font=badge_font, fill=(255, 255, 255, 255))

    lines = textwrap.wrap(caption_text.upper(), width=15)
    if not lines:
        lines = ["ASLI HAQEEQAT!"]

    line_height = 92
    total_text_h = len(lines) * line_height
    box_y1 = 1360 - (total_text_h // 2)
    box_y2 = box_y1 + total_text_h + 44

    draw.rounded_rectangle([55, box_y1, 1025, box_y2], radius=28, fill=(10, 12, 18, 230), outline=(255, 215, 0, 220), width=4)

    for i, line in enumerate(lines):
        t_bbox = draw.textbbox((0, 0), line, font=cap_font)
        tw = t_bbox[2] - t_bbox[0]
        tx = (1080 - tw) // 2
        ty = box_y1 + 20 + (i * line_height)

        if part_num == 1:
            fill_col = (255, 230, 0, 255) if i == 0 else (255, 255, 255, 255)
        else:
            fill_col = (0, 255, 150, 255) if i == 0 else (255, 230, 0, 255)

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
        "apad=pad_dur=0.14"
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
    if is_video:
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,eq=contrast=1.08:saturation=1.15[bg];"
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
            f"[0:v]scale=1240:2200:force_original_aspect_ratio=increase,crop=1240:2200,"
            f"crop=1080:1920:'(in_w-out_w)/2+({direction}*55)*sin(t*1.1)':'(in_h-out_h)/2+70*cos(t*0.8)'[bg];"
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
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
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

def render_two_cut_scene(scene, idx, total_scenes, badge):
    audio_path = asyncio.run(synthesize_scene_voice(scene["tts_urdu"], idx))
    total_dur = get_audio_duration(audio_path)
    half_dur = round(total_dur / 2.0, 2)
    rem_dur = round(total_dur - half_dur, 2)

    q1 = scene["search_query_1"]
    q2 = scene["search_query_2"]
    v_q = scene.get("video_query", "")

    vid_file = fetch_contextual_stock_video(v_q, f"stock_vid_{idx}.mp4") if v_q else None
    if vid_file:
        media1, is_vid1 = vid_file, True
    else:
        media1 = fetch_exact_scene_photo(q1, f"photo_{idx}_1.jpg")
        is_vid1 = False

    media2 = fetch_exact_scene_photo(q2, f"photo_{idx}_2.jpg")

    ov1 = create_burned_hud_overlay(scene["caption_part1"], badge, idx, total_scenes, 1)
    ov2 = create_burned_hud_overlay(scene["caption_part2"], badge, idx, total_scenes, 2)

    sub1 = f"sub_{idx}_1.mp4"
    sub2 = f"sub_{idx}_2.mp4"
    prepare_visual_subclip(media1, is_vid1, ov1, half_dur, 0, sub1)
    prepare_visual_subclip(media2, False, ov2, rem_dur, 1, sub2)

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
        print(f"🎬 Scene {idx+1}/{len(scenes)}: '{scene['caption_part1']} | {scene['caption_part2']}'")
        s_file = render_two_cut_scene(scene, idx, len(scenes), badge)
        scene_files.append(s_file)

    with open("master_concat.txt", "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    raw_output = "raw_reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "master_concat.txt",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        raw_output
    ], check=True)

    print("🎵 Mixing Cinematic Background Music...")
    final_output = "final_reel.mp4"
    bgm_url = "https://actions.google.com/sounds/v1/ambiences/cyberpunk_drone.ogg"
    try:
        bgm_resp = requests.get(bgm_url, headers=HEADERS, timeout=20)
        if bgm_resp.status_code == 200:
            with open("bgm.ogg", "wb") as f:
                f.write(bgm_resp.content)
            mix_cmd = [
                "ffmpeg", "-y",
                "-i", raw_output,
                "-stream_loop", "-1", "-i", "bgm.ogg",
                "-filter_complex", "[1:a]volume=0.09[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                final_output
            ]
            subprocess.run(mix_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return final_output
    except Exception as e:
        print(f"BGM mixing skip: {e}")

    # Copy raw_output to final_reel.mp4 so artifact backup always finds final_reel.mp4
    subprocess.run(["cp", raw_output, final_output], check=False)
    return final_output

def resolve_fb_page_credentials():
    """Automatically resolves numeric Page ID and Page Access Token even if a User Token was provided."""
    page_id = FB_PAGE_ID
    token = FB_ACCESS_TOKEN

    # Extract numeric ID if full URL was pasted
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
                # If only one page exists on the account, use it automatically
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
    print(f"🚀 Uploading Video to Facebook Page ID: {page_id}...")
    url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"

    title = script_data.get("title", "Logic Aur Dhoka - Asli Physics!")
    tagline = script_data.get("tagline", "Physics koi boring syllabus nahi, is dunya ka Source Code hai!")
    description = script_data.get("description", "Rozana aisi real-world logic sikhne ke liye Logic Aur Dhoka ko follow karein!")
    hashtags = script_data.get("hashtags", "#LogicAurDhoka #PhysicsLogic #DesiScam #ReelsPakistan")

    full_post_description = (
        f"{title}\n\n"
        f"⚡ {tagline}\n\n"
        f"📌 {description}\n\n"
        f"👉 Follow Logic Aur Dhoka for daily real-world physics & scam alerts!\n\n"
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
            resp = requests.post(url, data=payload, files=files, timeout=240)
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
    """100% Crash-Proof Telegram Upload (No Markdown parsing errors!)."""
    print("📲 Uploading Reel & Status Report to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    fb_status_line = f"✅ Facebook Auto-Post: {fb_msg}" if fb_ok else f"⚠️ Facebook Auto-Post: {fb_msg}"

    caption = (
        f"🔥 {script_data.get('title')}\n\n"
        f"⚡ Tagline:\n{script_data.get('tagline')}\n\n"
        f"📝 Description:\n{script_data.get('description')}\n\n"
        f"🏷️ Viral Tags:\n{script_data.get('hashtags')}\n\n"
        f"{fb_status_line}"
    )

    # Telegram caption limit is 1024 characters
    caption = caption[:1000]

    with open(video_path, "rb") as vf:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"video": vf},
            timeout=180
        )
        print("Telegram Upload Status:", resp.status_code, resp.text)

    if resp.status_code != 200:
        print("Retrying Telegram video upload without caption...")
        with open(video_path, "rb") as vf:
            requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"video": vf},
                timeout=180
            )

if __name__ == "__main__":
    data = generate_script_data()
    print("Video Title:", data.get("title"))
    final_vid = build_full_video(data)
    fb_success, fb_info = upload_to_facebook(final_vid, data)
    send_to_telegram(final_vid, data, fb_success, fb_info)
