import cloudscraper
from bs4 import BeautifulSoup
import csv
import os

# الإعدادات الأساسية
BASE_URL = "https://mycima.rip"
DB_FILE = "database.csv"
scraper = cloudscraper.create_scraper()

def get_direct_video_link(movie_page_url):
    """الدخول لصفحة الفيلم واستخراج رابط التحميل الحقيقي"""
    links = {"1080": "", "720": "", "480": ""}
    try:
        # 1. الدخول لصفحة الفيلم
        res = scraper.get(movie_page_url, timeout=15)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # 2. البحث عن رابط صفحة التحميل (غالباً يكون زر كبير مكتوب عليه تحميل)
        download_page_btn = soup.find('a', class_='btn-download') or soup.find('a', href=lambda x: x and 'download' in x)
        
        if download_page_btn:
            download_url = download_page_btn['href']
            # الدخول لصفحة الروابط المباشرة
            res_dl = scraper.get(download_url, timeout=15)
            dl_soup = BeautifulSoup(res_dl.content, 'html.parser')
            
            # 3. استخراج الروابط التي تنتهي بصيغة فيديو أو تحتوي على كلمة direct
            all_links = dl_soup.find_all('a', href=True)
            for a in all_links:
                href = a['href']
                text = a.text.lower()
                
                # التأكد أن الرابط ليس مجرد رابط تصنيف (تجنب الروابط التي تنتهي بـ /)
                if href.endswith('/') or "quality" in href:
                    continue
                
                if "1080" in text: links["1080"] = href
                elif "720" in text: links["720"] = href
                elif "480" in text: links["480"] = href
                
        return links
    except:
        return links

def main():
    print("بدء عملية الاستخراج العميق...")
    res = scraper.get(BASE_URL)
    soup = BeautifulSoup(res.content, 'html.parser')
    items = soup.select('.GridItem')
    
    data_to_save = []
    for item in items[:15]: # تجربة على أول 15 فيلم لضمان السرعة
        name = item.find('strong').text.strip()
        movie_url = item.find('a')['href']
        
        print(f"جاري استخراج الرابط الحقيقي لـ: {name}")
        sources = get_direct_video_link(movie_url)
        
        data_to_save.append({
            "Name": name,
            "URL_1080": sources["1080"],
            "URL_720": sources["720"],
            "URL_480": sources["480"],
            "Status": "Active" if sources["1080"] or sources["720"] else "Broken"
        })

    # حفظ النتائج
    with open(DB_FILE, mode='w', encoding='utf-8', newline='') as f:
        fieldnames = ["Name", "URL_1080", "URL_720", "URL_480", "Status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_to_save)
    print("تم التحديث بنجاح!")

if __name__ == "__main__":
    main()
