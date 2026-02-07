import requests
from bs4 import BeautifulSoup
import csv
import os

# الإعدادات
BASE_URL = "https://mycima.rip"
DB_FILE = "database.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def extract_quality_links(movie_url):
    """يدخل لصفحة الفيلم ويستخرج الروابط الحقيقية"""
    links = {"1080": "", "720": "", "480": ""}
    try:
        res = requests.get(movie_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # البحث عن أزرار التحميل أو المشاهدة التي تحتوي على الجودة
        # ملاحظة: المواقع تغير أسماء الكلاسات، لذا نبحث عن النص
        download_links = soup.select('a.download-item') # قد يتغير حسب الموقع
        if not download_links:
            download_links = soup.find_all('a', href=True)

        for a in download_links:
            href = a['href']
            text = a.text.lower()
            if "1080" in text: links["1080"] = href
            elif "720" in text: links["720"] = href
            elif "480" in text: links["480"] = href
            
        return links
    except:
        return links

def main():
    # 1. قراءة البيانات القديمة للحفاظ عليها
    existing_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row['Name']] = row

    # 2. جلب الصفحة الرئيسية للأفلام الجديدة والقديمة
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select('.GridItem') # تأكد من أن هذا الكلاس صحيح في MyCima حالياً
        
        updated_rows = []
        for item in items:
            name = item.find('strong').text.strip()
            movie_url = item.find('a')['href']
            
            # 3. التحقق: هل الفيلم موجود بروابط صالحة؟
            if name in existing_data and existing_data[name]['URL_1080'] != "":
                # نحافظ على الرابط القديم إذا كان صالحاً
                updated_rows.append(existing_data[name])
            else:
                # 4. جلب روابط جديدة (للجديد أو إذا كان القديم فارغاً)
                print(f"جاري جلب روابط: {name}")
                sources = extract_quality_links(movie_url)
                updated_rows.append({
                    "Name": name,
                    "URL_1080": sources["1080"],
                    "URL_720": sources["720"],
                    "URL_480": sources["480"],
                    "Status": "Active" if sources["1080"] else "Broken"
                })

        # 5. حفظ الجدول النهائي
        with open(DB_FILE, mode='w', encoding='utf-8', newline='') as f:
            fieldnames = ["Name", "URL_1080", "URL_720", "URL_480", "Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
