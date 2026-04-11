from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
import threading

app = Flask(__name__)

BASE_URL = "https://h5.aoneroom.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

CACHE_FILE = "movies.json"
UPDATE_INTERVAL = 60 * 60 * 6  # 6 hours

lock = threading.Lock()

# =========================
# SCRAPER
# =========================

def get_movie_details(detail_url):
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')

        description = soup.find('p').text.strip() if soup.find('p') else ""

        # poster fix
        img_tag = soup.find('img')
        poster = img_tag['src'] if img_tag and img_tag.get('src') else ""

        if poster and not poster.startswith("http"):
            poster = BASE_URL + poster

        video_links = re.findall(
            r'https?://[^\s"\'<>]+?\.(?:mp4|m3u8)',
            r.text
        )

        return {
            "description": description,
            "poster": poster,
            "video_url": video_links[0] if video_links else None,
        }

    except Exception as e:
        return {
            "description": "",
            "poster": "",
            "video_url": None
        }


def scrape_movies():
    print("🔄 Scraping movies...")

    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')

        movies = []
        links = soup.find_all('a', href=re.compile(r'/detail/'))

        for link in links[:30]:
            href = link.get('href')
            title = link.text.strip()

            if not title:
                title = "New Movie"

            full_url = BASE_URL + href

            meta = get_movie_details(full_url)

            movies.append({
                "title": title,
                "url": full_url,
                **meta
            })

        # save cache safely
        with lock:
            with open(CACHE_FILE, "w") as f:
                json.dump(movies, f, indent=2)

        print(f"✅ Saved {len(movies)} movies")

    except Exception as e:
        print("❌ Scrape error:", e)


# =========================
# LOAD CACHE SAFELY
# =========================

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []

    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return []


# =========================
# AUTO UPDATE THREAD
# =========================

def auto_update():
    while True:
        scrape_movies()
        time.sleep(UPDATE_INTERVAL)


# =========================
# API ROUTES
# =========================

@app.route("/")
def home():
    return "Movie API Running 🚀"


@app.route("/movies")
def movies():
    data = load_cache()

    # fallback scrape if empty
    if not data:
        scrape_movies()
        data = load_cache()

    return jsonify(data)


@app.route("/search")
def search():
    query = request.args.get("q", "").lower().strip()

    data = load_cache()

    if not data:
        scrape_movies()
        data = load_cache()

    if not query:
        return jsonify(data)

    results = []

    for m in data:
        title = m.get("title", "").lower()

        # stronger matching
        if (
            query in title or
            title.startswith(query) or
            any(word.startswith(query) for word in title.split())
        ):
            results.append(m)

    return jsonify(results)


# =========================
# STARTUP
# =========================

if __name__ == "__main__":
    # initial scrape (important for Render cold start)
    scrape_movies()

    # background updater
    threading.Thread(target=auto_update, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
