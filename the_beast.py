import requests
import csv
import re
import cloudscraper
import os

SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/s.m3u"
]
SPORTS_KEYWORDS = ['sport', 'beIN', 'SSC', 'KSA', 'رياضة']
DB_FILE = 'database.csv'

def check_link(url):
    """فحص حقيقي للرابط: هل يرسل بيانات فيديو؟"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        with requests.get(url, timeout=5, stream=True, headers=headers) as r:
            # إذا كان الكود 200 يعني الرابط حي
            return r.status_code == 200
    except:
        return False

def is_token_link(url):
    token_patterns = ['token=', 'key=', 'auth', 'pass', 'user']
    if any(p in url.lower() for p in token_patterns): return True
    return any(len(segment) > 25 for segment in url.split('/'))

def start_process():
    scraper = cloudscraper.create_scraper()
    final_list = []
    seen_urls = set()

    # 1. فحص القنوات القديمة وحذف التالف منها
    if os.path.exists(DB_FILE):
        print("🔍 فحص الروابط القديمة في الجدول...")
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['url']
                if check_link(url): # إذا كان لا يزال يعمل
                    final_list.append(row)
                    seen_urls.add(url)
                else:
                    print(f"🗑️ حذف رابط تالف: {row['title']}")

    # 2. جلب قنوات جديدة وإضافتها
    print("📡 جلب قنوات جديدة من المصادر...")
    for source in SOURCES:
        try:
            response = scraper.get(source, timeout=15)
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?)\n', response.text)
            for name, url in matches:
                url = url.strip()
                if any(key in name.lower() for key in SPORTS_KEYWORDS):
                    if not is_token_link(url) and url not in seen_urls:
                        if check_link(url):
                            final_list.append({'title': name.strip(), 'url': url})
                            seen_urls.add(url)
                            print(f"✅ إضافة قناة جديدة: {name}")
        except: continue

    # 3. إعادة كتابة الملف بالكامل (بالروابط الشغالة فقط)
    with open(DB_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'url'])
        writer.writeheader()
        writer.writerows(final_list)
    
    print(f"✨ تم التحديث! الإجمالي الحالي: {len(final_list)} قناة شغالة.")

if __name__ == "__main__":
    start_process()
