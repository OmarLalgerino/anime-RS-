import cloudscraper
from bs4 import BeautifulSoup
import csv
import os

def the_beast_auto_scanner():
    # المصدر: قسم المسلسلات التركية (تأكد من الرابط الصحيح للقسم)
    base_url = "https://k.3sk.media/turkish-series/" 
    scraper = cloudscraper.create_scraper()
    
    try:
        print("🔍 جاري تمشيط القسم التركي...")
        response = scraper.get(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. ابحث عن كل روابط الحلقات في الصفحة الرئيسية للقسم
        # ملاحظة: نعدل الوسم حسب تصميم الموقع (غالباً ما يكون h2 أو a داخل div محدد)
        episodes = soup.find_all('article') or soup.find_all('div', class_='item')

        file_name = 'database.csv'
        
        # فتح الملف للمسح والكتابة من جديد ليكون الرابط Raw محدث دائماً
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'url']) # العناوين

            for ep in episodes[:10]: # سحب آخر 10 حلقات نزلوا
                link_tag = ep.find('a', href=True)
                if not link_tag: continue
                
                ep_url = link_tag['href']
                ep_name = link_tag.text.strip() or "حلقة جديدة"

                # 2. الآن ندخل لـ "قلب" كل حلقة لسحب الرابط
                print(f"📡 فحص حلقة: {ep_name}")
                inner_res = scraper.get(ep_url)
                inner_soup = BeautifulSoup(inner_res.content, 'html.parser')
                
                watch_link = ""
                # البحث عن Iframe المشغل
                iframe = inner_soup.find('iframe', src=True)
                if iframe:
                    watch_link = iframe['src']
                    if watch_link.startswith('//'):
                        watch_link = 'https:' + watch_link
                
                # إضافة البيانات للملف إذا وجدنا رابط
                if watch_link:
                    writer.writerow([ep_name, watch_link])
                    print(f"✅ تم سحب الرابط لـ: {ep_name}")

        print("✨ اكتمل التحديث! ملف database.csv جاهز.")

    except Exception as e:
        print(f"❌ خطأ أثناء السحب التلقائي: {e}")

if __name__ == "__main__":
    the_beast_auto_scanner()
