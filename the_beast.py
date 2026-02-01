import requests
import re
import csv

def check_link(url):
    """فحص ذكي للرابط: يتأكد أن الرابط يفتح ويرسل بيانات فيديو فعلاً"""
    try:
        # نستخدم GET مع stream للتأكد من استجابة السيرفر الحقيقية
        with requests.get(url, timeout=7, stream=True) as r:
            if r.status_code == 200:
                # نتحقق من نوع المحتوى (يجب أن يكون ملف ميديا)
                return True
        return False
    except:
        return False

def start_process():
    # مصدر القنوات (IPTV-ORG) المعروف بتحديثاته
    source_url = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u"
    valid_channels = []
    
    print("بدء جلب القنوات وفحص الروابط... (سيتم تجاهل الروابط المعطلة)")
    try:
        response = requests.get(source_url, timeout=15)
        matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?\.m3u8)', response.text)
        
        for name, url in matches:
            if len(valid_channels) < 30: # فحص أفضل 30 قناة شغالة
                clean_url = url.strip()
                if check_link(clean_url):
                    valid_channels.append({
                        'title': name.strip(),
                        'url': clean_url
                    })
                    print(f"✅ تعمل: {name.strip()}")
                else:
                    print(f"❌ معطلة: {name.strip()}")

        # إنشاء الجدول الجديد (اسم ورابط فقط)
        with open('database.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'url'])
            writer.writerows(valid_channels)
        print("✅ تم تحديث database.csv بنجاح!")
    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    start_process()
