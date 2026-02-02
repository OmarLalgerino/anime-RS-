import requests
import csv
import re
import cloudscraper
import os
from bs4 import BeautifulSoup

# الإعدادات
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/s.m3u"
]
EGYDEAD_URL = "https://egydead.rip/episode/a-knight-of-the-seven-kingdoms-s01e03/"
SPORTS_KEYWORDS = ['sport', 'beIN', 'SSC', 'KSA', 'رياضة']
DB_FILE = 'database.csv'

def check_link(url):
    """فحص هل الرابط يعمل ويرسل بيانات؟"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://egydead.rip/'
        }
        # نستخدم HEAD لسرعة الفحص دون تحميل الملف كاملاً
        with requests.head(url, timeout=5, headers=headers, allow_redirects=True) as r:
            return r.status_code == 200
    except:
        return False

def extract_egydead_servers(url):
    """استخراج روابط السيرفرات من صفحة Egydead"""
    print(f"📡 جاري استخراج السيرفرات من: {url}")
    scraper = cloudscraper.create_scraper()
    servers = []
    try:
        response = scraper.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن روابط المشاهدة (غالباً في iframes أو أزرار السيرفرات)
        # نبحث عن وسوم الـ iframe التي تحتوي على مشغلات فيديو
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src') or iframe.get('data-src')
            if src and ('http' in src):
                servers.append({'title': 'EgyDead Server (Iframe)', 'url': src})
        
        # البحث عن أزرار السيرفرات إذا كانت موجودة في قائمة
        server_list = soup.select('ul.servers-list li') # مثال لمحدد افتراضي
        for s in server_list:
            link = s.get('data-url')
            if link:
                servers.append({'title': f'EgyDead - {s.text.strip()}', 'url': link})
                
    except Exception as e:
        print(f"❌ خطأ في كشط الموقع: {e}")
    return servers

def is_token_link(url):
    token_patterns = ['token=', 'key=', 'auth', 'pass', 'user']
    if any(p in url.lower() for p in token_patterns): return True
    return any(len(segment) > 25 for segment in url.split('/'))

def start_process():
    scraper = cloudscraper.create_scraper()
    final_list = []
    seen_urls = set()

    # 1. فحص القنوات القديمة في قاعدة البيانات
    if os.path.exists(DB_FILE):
        print("🔍 فحص الروابط الموجودة مسبقاً...")
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if check_link(row['url']):
                    final_list.append(row)
                    seen_urls.add(row['url'])

    # 2. سحب الروابط من صفحة Egydead المحددة
    egy_servers = extract_egydead_servers(EGYDEAD_URL)
    for srv in egy_servers:
        if srv['url'] not in seen_urls:
            # ملاحظة: روابط السيرفرات أحياناً لا تعطي 200 HEAD مباشرة لأنها صفحات HTML
            # لذا سنضيفها مباشرة أو نفحصها بـ GET
            final_list.append(srv)
            seen_urls.add(srv['url'])
            print(f"✅ تم إضافة سيرفر مشاهدة: {srv['title']}")

    # 3. جلب قنوات IPTV الرياضية من المصادر العالمية
    print("📡 جلب القنوات الرياضية من GitHub...")
    for source in SOURCES:
        try:
            response = scraper.get(source, timeout=15)
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?)\n', response.text)
            for name, url in matches:
                url = url.strip()
                name = name.strip()
                if any(key in name.lower() for key in SPORTS_KEYWORDS):
                    if not is_token_link(url) and url not in seen_urls:
                        if check_link(url):
                            final_list.append({'title': name, 'url': url})
                            seen_urls.add(url)
                            print(f"✅ إضافة قناة رياضية: {name}")
        except: continue

    # 4. تحديث الملف
    with open(DB_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'url'])
        writer.writeheader()
        writer.writerows(final_list)
    
    print(f"\n✨ اكتمل التحديث! الإجمالي: {len(final_list)} رابط شغّال.")

if __name__ == "__main__":
    start_process()
