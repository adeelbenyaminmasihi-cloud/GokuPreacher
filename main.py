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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

USED_TOPICS_FILE = "used_topics.json"

ALL_TOPICS = [
    {
        "topic": "LED Bulbs ke har 6 mahine baad jalne ka scam aur Heat Sink Physics",
        "badge": "LED BULB SCAM",
        "scientist_story": "انیس سو اکسٹھ میں جب رابرٹ بائرڈ نے ایل ای ڈی ایجاد کی تو سائنسدانوں کا خیال تھا کہ یہ بلب پچاس سال تک نہیں جلے گا، مگر آج کا لوکل بلب چھ مہینے بھی نہیں نکالتا!",
        "science_fact": "تھرمل ڈسی پیشن یعنی ہیٹ سنک کی فزکس کہتی ہے کہ ایل ای ڈی کی چپ جتنی ٹھنڈی رہے گی اتنی لمبی چلے گی۔ اصلی بلب کے اندر ایلومینیم کی موٹی پلیٹ ہوتی ہے جو گرمی باہر پھینکتی ہے۔",
        "scam_detail": "مگر سستے لوکل بلب بنانے والے اندر سے ایلومینیم غائب کر کے خالی پلاسٹک لگا دیتے ہیں تاکہ بلب کی گرمی اندر ہی قید ہو جائے اور آپ ہر تیسرے مہینے نیا بلب خریدیں!",
        "keywords": ["light bulb glowing", "electronic circuit board", "electrician repair", "counting money cash"],
        "vid_kw": "electricity"
    },
    {
        "topic": "70cc aur 125cc bike mein petrol average barhane wale Carburetor mistri ka choona",
        "badge": "BIKE PETROL SCAM",
        "scientist_story": "سترہ سو اڑتیس میں سوئس سائنسدان ڈینیئل برنولی نے فلوئڈ ڈائنامکس کا وہ اصول بنایا جس پر آج آپ کی بائیک کا کاربوریٹر اور ہوائی جہاز کے انجن چلتے ہیں!",
        "science_fact": "برنولی پرنسپل کے مطابق پٹرول کو مکمل جلنے کے لیے چودہ اعشاریہ سات حصے ہوا اور ایک حصہ پٹرول کا پرفیکٹ بیلنس چاہیے ہوتا ہے جسے سٹوكیومیٹرک ریشو کہتے ہیں۔",
        "scam_detail": "مگر جب محلے کا استاد پیچ کس گھما کر کاربوریٹر کا جیٹ ضرورت سے زیادہ بند کرتا ہے تو پٹرول بچنے کے بجائے انجن اوور ہیٹ ہوتا ہے اور دو مہینے بعد والوز اور پسٹن کا دس ہزار کا خرچہ نکل آتا ہے!",
        "keywords": ["motorcycle engine", "auto mechanic tools", "petrol pump fuel", "broken engine piston"],
        "vid_kw": "mechanic"
    },
    {
        "topic": "Inverter AC ko 16 degree par chalane ka nuqsan aur Thermodynamics ka qanoon",
        "badge": "AC BILL CHOONA",
        "scientist_story": "اٹھارہ سو چوبیس میں فرانسیسی انجینئر سادی کارنو نے تھرمو ڈائنامکس کا وہ قانون دریافت کیا جس سے آج دنیا کے تمام اے سی اور فریج ٹھنڈک پیدا کرتے ہیں!",
        "science_fact": "فزکس کہتی ہے کہ اے سی سولہ ڈگری کرنے سے کمرہ جلدی ٹھنڈا نہیں ہوتا، کیونکہ اے سی کی نالیوں سے نکلنے والی ہوا کا درجہ حرارت ہمیشہ ایک جیسا رہتا ہے، صرف کمپریسر کی محنت بدلتی ہے۔",
        "scam_detail": "جب آپ ریموٹ سولہ پر رکھتے ہیں تو انورٹر اے سی کا سینسر سمجھتا ہے کہ کمرے کو شملہ بنانا ہے، کمپریسر کبھی سلو نہیں ہوتا اور مہینے کے آخر میں پچاس ہزار کا بل آپ کے ہوش اڑا دیتا ہے!",
        "keywords": ["air conditioner room", "electricity meter", "summer heat sweat", "shocked man bill"],
        "vid_kw": "technology"
    },
    {
        "topic": "Fridge ki gas har saal khatam hone ka mistri scam aur Closed Loop Physics",
        "badge": "FRIDGE GAS SCAM",
        "scientist_story": "انیس سو تیس میں جب فریون گیس دریافت ہوئی تو انجینئرز نے فریج کے کمپریسر کو ایک مکمل سیل بند کلوزڈ لوپ سسٹم بنایا جس میں سے گیس کبھی خود ختم ہو ہی نہیں سکتی!",
        "science_fact": "آئیڈیل گیس لا کے مطابق فریج کی گیس پٹرول کی طرح جلتی نہیں ہے، بلکہ وہ صرف مائع سے گیس اور گیس سے مائع بن کر بیس سال تک انہی پائپوں میں گھومتی رہتی ہے۔",
        "scam_detail": "اکثر گرمیوں میں صرف دو سو روپے کا ریلے یا کیپیسٹر خراب ہوتا ہے، مگر کاریگر آ کر کہتا ہے باجی گیس اڑ گئی ہے اور بغیر لیکج چیک کیے پانچ ہزار روپے جیب میں ڈال لیتا ہے!",
        "keywords": ["refrigerator kitchen", "repairman tools", "cold ice cubes", "handing cash money"],
        "vid_kw": "tools"
    },
    {
        "topic": "Gaadi ke radiator mein saada paani dalne se engine tabah hone ki physics",
        "badge": "RADIATOR SCAM",
        "scientist_story": "اٹھارہ سو چھیاسی میں فرانسیسی کیمسٹ فرانسوا راؤلٹ نے ثابت کیا کہ خالص پانی میں خاص کیمیکل ملانے سے اس کا ابلنے کا پوائنٹ حیرت انگیز طور پر بڑھ جاتا ہے!",
        "science_fact": "سادہ نلکے کا پانی سو ڈگری پر ابل کر بھاپ بن جاتا ہے اور لوہے کے انجن کو اندر سے زنگ لگا دیتا ہے، جبکہ اصلی کولنٹ ایک سو تیس ڈگری تک انجن کو ٹھنڈا اور محفوظ رکھتا ہے۔",
        "scam_detail": "پٹرول پمپ اور ورکشاپ والے کہتے ہیں استاد جی سادہ پانی ڈالو سب چلتا ہے، اور چھ مہینے بعد جب زنگ سے ریڈی ایٹر چوک ہوتا ہے تو ہیڈ گیسکٹ جلنے کا چالیس ہزار کا بل بن جاتا ہے!",
        "keywords": ["car hood smoke", "pouring engine coolant", "rusty metal pipe", "auto repair garage"],
        "vid_kw": "car"
    },
    {
        "topic": "Solar panels par mitti jamne se 40% bijli gayab hone ka raaz aur Photoelectric Effect",
        "badge": "SOLAR PANEL LOGIC",
        "scientist_story": "انیس سو پانچ میں البرٹ آئن سٹائن نے فوٹو الیکٹرک ایفیکٹ دریافت کیا جس پر انہیں نوبل پرائز ملا، اور آج آپ کی چھت پر لگا سولر پینل اسی اصول پر دھوپ سے بجلی بناتا ہے!",
        "science_fact": "فزکس کے مطابق سولر پلیٹ کے سیلز سیریز میں جڑے ہوتے ہیں۔ اگر ایک کونے پر بھی مٹی یا پرندے کی بیٹ جم جائے تو وہ پورا سیل لوڈ بن کر باقی پلیٹ کی تیس فیصد بجلی کھا جاتا ہے۔",
        "scam_detail": "لوگ لاکھوں روپے کا سولر لگوا کر چھ مہینے کپڑا تک نہیں مارتے، اور پھر شکایت کرتے ہیں کہ سولر والا دھوکہ دے گیا، حالانکہ قصور صرف پانچ منٹ کی صفائی نہ کرنے کا ہوتا ہے!",
        "keywords": ["solar panels roof", "bright sunlight sky", "cleaning glass water", "inverter battery"],
        "vid_kw": "technology"
    },
    {
        "topic": "Tyre mein hawa kam rakhne ka desi jugaar, petrol ki tabahi aur Rolling Friction",
        "badge": "TYRE PRESSURE LOGIC",
        "scientist_story": "سترہ سو ننانوے میں چارلس کولمب نے رگڑ یعنی فریکشن کے قوانین پیش کیے جن سے پتہ چلا کہ زمین اور پہیے کا ملاپ آپ کی گاڑی کی رفتار اور پٹرول کا فیصلہ کرتا ہے!",
        "science_fact": "جب ٹائر میں ہوا صرف پانچ پوائنٹ کم ہوتی ہے تو رولنگ ریزسٹنس بڑھ جاتی ہے۔ ٹائر سڑک کے ساتھ چپک کر چلتا ہے جس سے انجن کو پندرہ فیصد زیادہ پٹرول پھونکنا پڑتا ہے۔",
        "scam_detail": "ٹائر والا کہتا ہے بھائی ہوا کم رکھو جھٹکے نہیں لگیں گے، مگر اس سستے آرام کے چکر میں ہر مہینے ہزاروں کا اضافی پٹرول جلتا ہے اور ٹائر کی سائیڈ کی تاریں وقت سے پہلے ٹوٹ جاتی ہیں!",
        "keywords": ["car tire pressure", "asphalt highway road", "petrol station nozzle", "car wheel closeup"],
        "vid_kw": "traffic"
    },
    {
        "topic": "Fake 20,000 mAh Power Bank ka dhanda aur Lithium Ion Energy Density",
        "badge": "POWERBANK SCAM",
        "scientist_story": "انیس سو اسی کی دہائی میں جان گڈ اینف نے لیتھیم آئن بیٹری ایجاد کی جس نے پوری دنیا کے موبائل فونز کو جیب میں رکھنا ممکن بنایا!",
        "science_fact": "انرجی ڈینسٹی کی فزکس کہتی ہے کہ بیس ہزار ایم اے ایچ کی توانائی سٹور کرنے کے لیے خالص لیتھیم سیلز کا ایک خاص وزن اور حجم ہونا لازمی ہے جس کی قیمت کبھی ہزار روپے نہیں ہو سکتی۔",
        "scam_detail": "مارکیٹ میں ملنے والے سستے پاور بینک کھولو تو اندر صرف ایک چھوٹا سا سیل لگا ہوتا ہے اور باقی ڈبے میں وزن بڑھانے کے لیے ریت یا لوہے کی پتریاں بھری ہوتی ہیں!",
        "keywords": ["powerbank charging phone", "lithium battery cells", "electronics market shop", "broken gadget repair"],
        "vid_kw": "phone"
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
    print(f"🔥 Today's Fresh Topic: {chosen['topic']}")
    return build_rich_script_for_topic(chosen)

def build_rich_script_for_topic(chosen):
    topic = chosen["topic"]
    kw = chosen["keywords"]
    v_kw = chosen["vid_kw"]
    badge = chosen["badge"]

    return {
        "title": f"{topic} - Asli Physics!",
        "hashtags": "#PhysicsLogic #DesiScam #PakistaniReels #ScienceUrdu #DimaagKholo",
        "category_badge": badge,
        "scenes": [
            {
                "tts_urdu": "ہر دو مہینے بعد آپ کی جیب سے ہزاروں روپے کیسے نکالے جاتے ہیں؟ اور حیرت کی بات یہ ہے کہ اس میں غلطی کاریگر کی نہیں، آپ کی فزکس کی ہے!",
                "caption_part1": "HAR 2 MAHINE BAAD",
                "caption_part2": "HAZAROON KA CHOONA?!",
                "search_query_1": kw[0],
                "search_query_2": "counting money cash",
                "video_keyword": v_kw
            },
            {
                "tts_urdu": chosen["scientist_story"],
                "caption_part1": "SCIENCE KI ASLI",
                "caption_part2": "KAHANI SUNO!",
                "search_query_1": "scientist laboratory physics",
                "search_query_2": kw[1],
                "video_keyword": "technology"
            },
            {
                "tts_urdu": chosen["science_fact"],
                "caption_part1": "YAHAN CHALTI HAI",
                "caption_part2": "PURE PHYSICS!",
                "search_query_1": kw[1],
                "search_query_2": "engineering machine closeup",
                "video_keyword": "electricity"
            },
            {
                "tts_urdu": "جب تک کسی مشین یا سرکٹ میں توانائی اور حرارت کا قدرتی توازن برقرار رہتا ہے، وہ سالوں سال بغیر کسی خرچے کے مکھن کی طرح چلتی ہے۔",
                "caption_part1": "JAB TAK BALANCE HAI",
                "caption_part2": "TAB TAK BACHAT HAI!",
                "search_query_1": kw[2],
                "search_query_2": kw[0],
                "video_keyword": v_kw
            },
            {
                "tts_urdu": chosen["scam_detail"],
                "caption_part1": "AUR YAHAN HOTA HAI",
                "caption_part2": "SABSE BADA SCAM!",
                "search_query_1": "mechanic repairman smiling",
                "search_query_2": kw[2],
                "video_keyword": "mechanic"
            },
            {
                "tts_urdu": "دکاندار یا استاد بڑے پیار سے کہتا ہے کہ بھائی جان یہ سستا جگاڑ لگا لو، سب چلتا ہے، اور آپ خوشی خوشی پیسے بچانے کے چکر میں پھنس جاتے ہو!",
                "caption_part1": "USTAAD KI MEETHI BAAT",
                "caption_part2": "AUR SASTA JUGAAR!",
                "search_query_1": "workshop tools repair",
                "search_query_2": kw[3],
                "video_keyword": "tools"
            },
            {
                "tts_urdu": "شروع کے چند ہفتے تو سب ٹھیک لگتا ہے، مگر اندر ہی اندر فزکس کا قانون اپنا کام دکھاتا ہے اور قیمتی پرزے گرم ہو کر جلنا شروع ہو جاتے ہیں۔",
                "caption_part1": "CHAND HAFTE BAAD",
                "caption_part2": "ANDAR SE TABAHI!",
                "search_query_1": "sparks fire wires",
                "search_query_2": kw[1],
                "video_keyword": "fire"
            },
            {
                "tts_urdu": "پھر جب آپ دوبارہ مارکیٹ جاتے ہو تو پانچ سو بچانے کے چکر میں سیدھا دس سے پندرہ ہزار روپے کا نیا خرچہ آپ کے ہاتھ میں تھما دیا جاتا ہے!",
                "caption_part1": "500 BACHAYE THE,",
                "caption_part2": "15,000 KA FATKA LAGA!",
                "search_query_1": "stressed man holding head",
                "search_query_2": "paying cash bill",
                "video_keyword": "money"
            },
            {
                "tts_urdu": "ایلون مسک کے راکٹ سے لے کر آپ کے گھر کی عام چیزوں تک، ہر جگہ فزکس کا یہی پکا حساب چلتا ہے جو کسی دیسی جگاڑ کو معاف نہیں کرتا۔",
                "caption_part1": "ROCKET SE LE KAR",
                "caption_part2": "APKE GHAR TAK!",
                "search_query_1": "rocket launch fire",
                "search_query_2": kw[0],
                "video_keyword": "engine"
            },
            {
                "tts_urdu": "فزکس کوئی بورڈ امتحان کا بورنگ نصاب نہیں بلکہ اس دنیا کا سورس کوڈ ہے! روزانہ ایسی اصلی لاجک سیکھنے کے لیے ابھی فالو کا بٹن دبا دو!",
                "caption_part1": "DUNYA KA SOURCE CODE!",
                "caption_part2": "ABHI FOLLOW DABAO!",
                "search_query_1": "smartphone social media",
                "search_query_2": "modern technology glow",
                "video_keyword": "phone"
            }
        ]
    }

USED_MEDIA_URLS = set()

def fetch_real_stock_video(keyword, filename):
    slug = urllib.parse.quote(keyword.lower().strip())
    search_url = f"https://mixkit.co/free-stock-video/{slug}/"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            mp4_urls = re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)
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
    # 1. Try Bing Images HD Search
    try:
        encoded = urllib.parse.quote(f"{query} photography")
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

    # 2. Try Unsplash Public NAPI
    try:
        encoded = urllib.parse.quote(query)
        u_url = f"https://unsplash.com/napi/search/photos?query={encoded}&per_page=15"
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

    # 3. Guaranteed Valid Image Backup
    img = Image.new("RGB", (1080, 1920), (25, 30, 45))
    img.save(filename, "JPEG", quality=92)
    return filename

def verify_and_prepare_image(filepath):
    try:
        with Image.open(filepath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w < 200 or h < 200:
                return False
            im = ImageEnhance.Contrast(im).enhance(1.12)
            im = ImageEnhance.Color(im).enhance(1.18)
            im.save(filepath, "JPEG", quality=92)
        return True
    except Exception:
        return False

def create_caption_overlay(caption_text, badge_text, scene_idx, total_scenes, part_num):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(320):
        alpha = int(175 * (1 - y / 320))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1250, 1920):
        alpha = int(230 * ((y - 1250) / 670))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        badge_font = ImageFont.truetype(font_path, 36)
        cap_font = ImageFont.truetype(font_path, 70)
    except Exception:
        badge_font = ImageFont.load_default()
        cap_font = ImageFont.load_default()

    bw, bh = 560, 74
    bx, by = (1080 - bw) // 2, 105
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=37, fill=(220, 38, 38, 245), outline=(255, 255, 255, 230), width=3)
    draw.text((540, by + bh // 2), badge_text.upper(), font=badge_font, fill=(255, 255, 255, 255), anchor="mm")

    lines = textwrap.wrap(caption_text.upper(), width=16)
    y_start = 1470 - (len(lines) * 48)

    for i, line in enumerate(lines):
        y_pos = y_start + i * 100
        if part_num == 1:
            color = (255, 230, 0, 255) if i % 2 == 0 else (255, 255, 255, 255)
        else:
            color = (0, 255, 163, 255) if i % 2 == 0 else (255, 255, 255, 255)
        draw.text((540, y_pos), line, font=cap_font, fill=color, anchor="mm", stroke_width=12, stroke_fill=(0, 0, 0, 255))

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
    """100% Crash-Proof FFmpeg Renderer for both Stock Videos and Stock Photos."""
    if is_video:
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
        # Fixed width/height (1080:1920) with smooth time-based x/y camera pan (Never crashes!)
        direction = 1 if sub_idx % 2 == 0 else -1
        vf = (
            f"[0:v]scale=1240:2200:force_original_aspect_ratio=increase,crop=1240:2200,"
            f"crop=1080:1920:'(in_w-out_w)/2+({direction}*55)*sin(t*1.1)':'(in_h-out_h)/2+70*cos(t*0.8)'[bg];"
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

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Ultimate failsafe if any downloaded image/video has unusual dimensions
        safe_vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
            "[bg][1:v]overlay=0:0,format=yuv420p[v]"
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

    q1 = scene.get("search_query_1", "car mechanic")
    q2 = scene.get("search_query_2", "counting money")
    v_kw = scene.get("video_keyword", "mechanic")

    vid_file = fetch_real_stock_video(v_kw, f"stock_vid_{idx}.mp4")
    if vid_file:
        media1, is_vid1 = vid_file, True
    else:
        media1 = fetch_real_stock_photo(q1, f"photo_{idx}_1.jpg")
        is_vid1 = False

    media2 = fetch_real_stock_photo(q2, f"photo_{idx}_2.jpg")

    ov1 = create_caption_overlay(scene.get("caption_part1", "ASLI HAQEEQAT"), badge, idx, total_scenes, 1)
    ov2 = create_caption_overlay(scene.get("caption_part2", "DEKHO KAISE!"), badge, idx, total_scenes, 2)

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
