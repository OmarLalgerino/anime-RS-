import feedparser
import csv
import requests
import re
import cloudscraper
import os

SOURCES = [
    "https://nyaa.si/?page=rss&q=Arabic+1080p",
    "https://nyaa.si/?page=rss&q=Arabic+720p",
    "https://nyaa.si/?page=rss&q=Arabic+480p",
    "https://www.tokyotosho.info/rss.php?filter=1,11&z=Arabic"
]

MAX_ROWS = 10000  # الحد الأقصى للأسطر في كل ملف

def get_current_db_file():
    """البحث عن آخر ملف متاح أو إنشاء واحد جديد"""
    i = 0
    while True:
        filename = f'database_{i}.csv' if i > 0 else 'database.csv'
        if not os.path.exists(filename):
            return filename
        
        # التأكد من عدد الأسطر في الملف الحالي
        with open(filename, 'r', encoding='utf-8') as f:
            row_count = sum(1 for row in f)
        
        if row_count < MAX_ROWS:
            return filename
        i += 1

def clean_and_translate(text):
    clean_text = re.sub(r'\[.*?\]|\(.*?\)|1080p|720p|480p|HEVC|x264|x265|AAC', '', text).strip()
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q={requests.utils.quote(clean_text)}"
        res = requests.get(url, timeout=5)
        return res.json()[0][0][0]
    except:
        return clean_text

def get_clean_hash_link(entry):
    if hasattr(entry, 'nyaa_infohash'):
        return f"https://webtor.io/player/embed/{entry.nyaa_infohash}"
    link = getattr(entry, 'link', '')
    hash_match = re.search(r'btih:([a-fA-F0-9]{40})', link)
    if hash_match:
        return f"https://webtor.io/player/embed/{hash_match.group(1).lower()}"
    return None

def start_bot():
    scraper = cloudscraper.create_scraper()
    db_file = get_current_db_file()
    print(f"📂 الملف الحالي للعمل: {db_file}")

    new_entries = []
    for rss_url in SOURCES:
        try:
            resp = scraper.get(rss_url, timeout=15)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:25]:
                streaming_link = get_clean_hash_link(entry)
                if streaming_link:
                    final_name = clean_and_translate(entry.title)
                    quality = "1080p (FHD)" if "1080p" in entry.title else "720p (HD)" if "720p" in entry.title else "480p (SD)"
                    
                    new_entries.append({
                        'name_ar': final_name,
                        'name_en': final_name,
                        'torrent_url': streaming_link,
                        'status': quality
                    })
        except Exception as e:
            print(f"❌ خطأ: {e}")

    # الكتابة بنظام Append (الإضافة) لعدم مسح الحلقات القديمة
    file_exists = os.path.isfile(db_file)
    with open(db_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['name_ar', 'name_en', 'torrent_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.stat(db_file).st_size == 0:
            writer.writeheader()
        writer.writerows(new_entries)
    
    print(f"✅ تم إضافة {len(new_entries)} حلقة جديدة إلى {db_file}")

if __name__ == "__main__":
    start_bot()
