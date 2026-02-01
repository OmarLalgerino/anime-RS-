import feedparser
import csv
import requests
import re
import os

# المصادر التي حددتها أنت
RSS_SOURCES = [
    "https://nyaa.si/?page=rss",
    "https://www.tokyotosho.info/rss.php"
]
DB_FILE = 'database.csv'

def check_link_health(url):
    """5 & 6: فحص الرابط وإذا كان معطلاً يرجح تحديثه"""
    try:
        # فحص سريع للرابط
        r = requests.head(url, timeout=5)
        return r.status_code < 400
    except:
        return False

def get_embed_streaming(torrent_link):
    """تحويل التورنت إلى رابط مشغل Embed حقيقي"""
    # استخراج الـ Hash من الرابط (المعرف الفريد للفيديو)
    info_hash = ""
    if 'magnet:?' in torrent_link:
        match = re.search(r'xt=urn:btih:([a-fA-F0-9]+)', torrent_link)
        if match: info_hash = match.group(1)
    
    if info_hash:
        # هذا الرابط يفتح "مشغل فيديو" (Player) مباشرة وليس صفحة بحث
        return f"https://webtor.io/player/embed/{info_hash}"
    return ""

def update_db():
    # 4: قراءة البيانات الموجودة مسبقاً للحفاظ عليها
    database = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                database[row['name']] = row

    print("🚀 جاري سحب الروابط من Nyaa و TokyoTosho...")
    
    for rss in RSS_SOURCES:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:25]: # 3: سحب الجديد (25 حلقة من كل مصدر)
            name = entry.title
            torrent_link = entry.link
            
            # جلب رابط المشغل المباشر
            player_url = get_embed_streaming(torrent_link)
            
            if player_url:
                # 1 & 2: تنظيم الجدول بجودات متعددة واسم ورابط
                # 6: تحديث الرابط إذا كان غير موجود أو معطل
                if name not in database or not check_link_health(database[name]['url_1080p']):
                    database[name] = {
                        'name': name,
                        'url_1080p': f"{player_url}?quality=1080",
                        'url_720p': f"{player_url}?quality=720",
                        'url_480p': f"{player_url}?quality=480"
                    }

    # حفظ الجدول النهائي (القديم + الجديد)
    with open(DB_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'url_1080p', 'url_720p', 'url_480p']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(database.values())
    print(f"✨ تم تحديث {len(database)} حلقة بنجاح!")

if __name__ == "__main__":
    update_db()
