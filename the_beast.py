import feedparser
import json
import requests
import re
import time

# المصادر التي طلبتها
SOURCES = {
    "Nyaa": "https://nyaa.land/?page=rss&c=1_2&q=Arabic",
    "Tosho": "https://www.tokyotosho.info/rss.php?terms=Arabic"
}

def get_anilist_info(anime_name):
    query = '''
    query ($search: String) {
      Media (search: $search, type: ANIME) {
        title { romaji english native }
        description
        coverImage { extraLarge }
        averageScore
        genres
        status
      }
    }
    '''
    try:
        response = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'search': anime_name}}, timeout=10)
        if response.status_code == 200:
            return response.json()['data']['Media']
    except:
        return None

def clean_name(text):
    text = re.sub(r'\[.*?\]|\(.*?\)|\d+p|HEVC|x265|x264|Hi10P|60fps', '', text, flags=re.I)
    text = re.sub(r'\.mkv|\.mp4|_|-', ' ', text)
    match = re.search(r'^(.+?)(?:\s\d+|$)', text.strip())
    return match.group(1).strip() if match else text.strip()

def run_beast():
    database = {}
    for source, url in SOURCES.items():
        print(f"📡 سحب من {source}...")
        feed = feedparser.parse(requests.get(url).content)
        for entry in feed.entries:
            name = clean_name(entry.title)
            if name not in database:
                info = get_anilist_info(name)
                database[name] = {
                    "title": name,
                    "info": info if info else {"poster": "https://via.placeholder.com/300"},
                    "links": {}
                }
            quality = "1080p" if "1080" in entry.title else "720p" if "720" in entry.title else "480p"
            database[name]["links"][quality] = entry.link

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(list(database.values()), f, ensure_ascii=False, indent=4)
    print("✅ تم تحديث data.json بنجاح!")

if __name__ == "__main__":
    run_beast()
