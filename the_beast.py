import cloudscraper
from bs4 import BeautifulSoup
import csv
import re

# إعداد القناص لتجاوز الحماية البسيطة
scraper = cloudscraper.create_scraper()

def get_video_links(page_url):
    """سحب روابط الجودات من صفحة الحلقة في عرب سيد"""
    links = {"1080p": "", "720p": "", "480p": ""}
    try:
        res = scraper.get(page_url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # البحث في جميع الروابط الموجودة في الصفحة
        all_a = soup.find_all('a', href=True)
        for a in all_a:
            href = a['href']
            text = a.text.lower()
            
            # صيد روابط الفيديو المباشرة (mp4, mkv, m3u8)
            if any(ext in href for ext in ['.mp4', '.mkv', '.m3u8']):
                if "1080" in text or "1080" in href: 
                    if not links["1080p"]: links["1080p"] = href
                elif "720" in text or "720" in href: 
                    if not links["720p"]: links["720p"] = href
                elif "480" in text or "480" in href: 
                    if not links["480p"]: links["480p"] = href
        
        # إذا لم يجد روابط مباشرة، يبحث عن رابط المشغل (Iframe)
        if not links["720p"]:
            iframe = soup.find('iframe', src=True)
            if iframe:
                src = iframe['src']
                links["720p"] = src if src.startswith('http') else 'https:' + src
                
        return links
    except:
        return links

def update_database():
    # الرابط الجديد الذي زودتني به (قسم المسلسلات التركية)
    source_url = "https://asd.pics/home3/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/"
    db_file = 'database.csv'
    all_data = []

    print(f"🚀 انطلاق الوحش نحو: {source_url}")
    try:
        res = scraper.get(source_url)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # في عرب سيد، المسلسلات تكون داخل div بـ class MovieBlock
        items = soup.find_all('div', class_='MovieBlock')

        if not items:
            print("⚠️ لم يتم العثور على حلقات، قد يكون الكلاس قد تغير.")
        
        for item in items[:20]: # سحب آخر 20 حلقة
            name_tag = item.find('h2')
            link_tag = item.find('a', href=True)
            
            if name_tag and link_tag:
                name = name_tag.text.strip()
                link = link_tag['href']
                
                print(f"📡 جاري قنص: {name}")
                v_links = get_video_links(link)
                
                all_data.append({
                    'name': name,
                    'url_1080p': v_links['1080p'],
                    'url_720p': v_links['720p'],
                    'url_480p': v_links['480p']
                })

        # حفظ البيانات في الملف
        with open(db_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'url_1080p', 'url_720p', 'url_480p'])
            writer.writeheader()
            writer.writerows(all_data)
        print(f"✅ مبروك! تم تحديث {len(all_data)} حلقة بنجاح.")
        
    except Exception as e:
        print(f"❌ خطأ أثناء السحب: {e}")

if __name__ == "__main__":
    update_database()
