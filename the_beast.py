import cloudscraper
from bs4 import BeautifulSoup
import csv
import os
import requests

# إعداد القناص لتجاوز الحماية
scraper = cloudscraper.create_scraper()

def check_link_status(url):
    """يفحص إذا كان الرابط لا يزال يعمل"""
    if not url: return False
    try:
        # بعض السيرفرات تمنع طلبات HEAD، لذا نستخدم GET مع stream
        response = requests.get(url, timeout=5, stream=True)
        return response.status_code == 200
    except:
        return False

def get_video_links(page_url):
    """يسحب روابط الجودات من قلب صفحة ماي سيما"""
    links = {"1080p": "", "720p": "", "480p": ""}
    try:
        res = scraper.get(page_url)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # ماي سيما يضع السيرفرات غالباً في قائمة 'WatchServersList' أو داخل أزرار
        servers = soup.find_all('btn', {'data-url': True}) or soup.find_all('iframe', src=True)
        
        for s in servers:
            # محاولة جلب الرابط سواء كان في data-url أو src
            url = s.get('data-url') or s.get('src')
            if not url: continue
            if url.startswith('//'): url = 'https:' + url
            
            # تحديد الجودة بناءً على نص الزر أو الرابط
            label = s.text.lower()
            if "1080" in label or "fhd" in url: links["1080p"] = url
            elif "720" in label or "hd" in url: links["720p"] = url
            elif "480" in label or "sd" in url: links["480p"] = url
        
        # إذا لم يتم تحديد جودة معينة، نضع أول رابط نده كجودة أساسية 720p
        if not links["720p"] and servers:
            links["720p"] = servers[0].get('data-url') or servers[0].get('src')
            
        return links
    except:
        return links

def update_database():
    # الرابط المستهدف (قسم المسلسلات التركية في ماي سيما)
    source_url = "https://mycima.gold/category/series/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/"
    db_file = 'database.csv'
    temp_data = []

    # 1. قراءة البيانات القديمة لفحصها والحفاظ على الروابط الشغالة
    if os.path.exists(db_file):
        with open(db_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # نحافظ على الحلقة القديمة إذا كان رابطها لا يزال يعمل
                if check_link_status(row.get('url_720p')):
                    temp_data.append(row)

    # 2. سحب الحلقات الجديدة من الموقع
    print(f"🔍 جاري فحص: {source_url}")
    try:
        res = scraper.get(source_url)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # تحديد حاوية الحلقات في ماي سيما (غالباً GridItem)
        items = soup.find_all('div', class_='GridItem')

        for item in items[:15]: # فحص آخر 15 حلقة مضافة
            title_tag = item.find('strong') or item.find('h2')
            link_tag = item.find('a', href=True)
            
            if not title_tag or not link_tag: continue
            
            name = title_tag.text.strip()
            link = link_tag['href']
            
            # منع التكرار: إذا كانت الحلقة موجودة بالفعل في البيانات القديمة، تخطاها
            if any(d['name'] == name for d in temp_data):
                continue
            
            print(f"📡 جاري سحب روابط قلب الحلقة: {name}")
            v_links = get_video_links(link)
            
            temp_data.append({
                'name': name,
                'url_1080p': v_links['1080p'],
                'url_720p': v_links['720p'],
                'url_480p': v_links['480p']
            })
    except Exception as e:
        print(f"❌ خطأ في السحب: {e}")

    # 3. حفظ الجدول النهائي (الاسم ثم الروابط) بشكل مرتب
    with open(db_file, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'url_1080p', 'url_720p', 'url_480p']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(temp_data)
    
    print(f"✅ تم التحديث بنجاح. إجمالي الحلقات في الجدول: {len(temp_data)}")

if __name__ == "__main__":
    update_database()
