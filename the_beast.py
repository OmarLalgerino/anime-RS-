def run_beast():
    # 1. محاولة قراءة البيانات القديمة بدلاً من البدء من الصفر
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
                # تحويل القائمة القديمة إلى قاموس (Dictionary) لتجنب التكرار
                database = {item['title']: item for item in old_data}
            except:
                database = {}
    else:
        database = {}

    for source, url in SOURCES.items():
        print(f"📡 سحب من {source}...")
        try:
            feed = feedparser.parse(requests.get(url, timeout=10).content)
            for entry in feed.entries:
                name = clean_name(entry.title)
                
                # 2. إذا كان الأنمي غير موجود مسبقاً، نقوم بإضافته
                if name not in database:
                    info = get_anilist_info(name)
                    database[name] = {
                        "title": name,
                        "info": {
                            "poster": info['coverImage']['extraLarge'] if info else "https://via.placeholder.com/300",
                            "description": info['description'] if info else "No description",
                        },
                        "links": {"torrent": entry.link}
                    }
        except Exception as e:
            print(f"❌ خطأ: {e}")

    # 3. حفظ الكل (القديم + الجديد)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(list(database.values()), f, ensure_ascii=False, indent=4)
