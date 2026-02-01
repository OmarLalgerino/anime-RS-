import feedparser
import csv
import requests
import re
import cloudscraper

# البحث عن المصادر التي توفر الجودات الثلاث مع الترجمة
SOURCES = [
    "https://nyaa.si/?page=rss&q=Arabic+1080p",
    "https://nyaa.si/?page=rss&q=Arabic+720p",
    "https://nyaa.si/?page=rss&q=Arabic+480p"
]
DB_FILE = 'database.csv'

def get_clean_hash_link(entry):
    if hasattr(entry, 'nyaa_infohash'):
        return f"https://webtor.io/player/embed/{entry.nyaa_infohash}"
    hash_match = re.search(r'btih:([a-fA-F0-9]{40})', entry.link)
    if hash_match:
        return f"https://webtor.io/player/embed/{hash_match.group(1).lower()}"
    return None

def start_bot():
    database = {}
    scraper = cloudscraper.create_scraper()
    print("🎬 جاري تجميع الحلقات بجميع الجودات (1080, 720, 480)...")

    for rss_url in SOURCES:
        try:
            resp = scraper.get(rss_url, timeout=15)
            feed = feedparser.parse(resp.text)
            
            for entry in feed.entries[:30]:
                name_en = entry.title
                streaming_link = get_clean_hash_link(entry)
                
                if streaming_link:
                    # تحديد الوسم بناءً على الجودة الموجودة في العنوان
                    if "1080p" in name_en:
                        quality = "1080p (FHD)"
                    elif "720p" in name_en:
                        quality = "720p (HD)"
                    elif "480p" in name_en:
                        quality = "480p (SD)"
                    else:
                        quality = "Auto"

                    # تخزين الجودة في العمود المخصص
                    database[name_en] = {
                        'name_ar': name_en,
                        'name_en': name_en,
                        'torrent_url': streaming_link,
                        'status': quality # هنا ستظهر الجودة بوضوح
                    }
        except Exception as e:
            print(f"❌ خطأ في المصدر: {e}")

    with open(DB_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name_ar', 'name_en', 'torrent_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(database.values())
    print(f"✅ تم بنجاح! تم العثور على {len(database)} رابط بجودات مختلفة.")

if __name__ == "__main__":
    start_bot()
