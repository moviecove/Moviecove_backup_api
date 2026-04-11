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

# -------- SCRAPER -------- #

def get_movie_details(detail_url):
    try:
        response = requests.get(detail_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        details = [t.text.strip() for t in soup.find_all('h4')][:10]
        description = soup.find('p').text.strip() if soup.find('p') else ""

        # Poster (IMPORTANT)
        img_tag = soup.find('img')
        poster = img_tag['src'] if img_tag else ""

        video_links = re.findall(r'https?://[^\s"\'<>]+?\.(?:mp4|m3u8)', response.text)

        return {
            "description": description,
            "poster": poster,
            "genres": [d for d in details if len(d) > 3 and not d.isdigit()],
            "video_url": video_links[0] if video_links else None,
            "year": next((d for d in details if d.isdigit()), "N/A")
        }
    except:
        return {}

def scrape_movies():
    print("Scraping movies...")

    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        movies = []
        links = soup.find_all('a', href=re.compile(r'/detail/'))

        for link in links[:25]:
            href = link.get('href')
            title = link.text.strip() or "New Release"
            full_url = BASE_URL + href

            meta = get_movie_details(full_url)

            movies.append({
                "title": title,
                "url": full_url,
                **meta
            })

        with open(CACHE_FILE, "w") as f:
            json.dump(movies, f, indent=4)

        print("Movies updated!")

    except Exception as e:
        print("Error:", e)

# -------- AUTO UPDATE -------- #

def auto_update():
    while True:
        scrape_movies()
        time.sleep(UPDATE_INTERVAL)

threading.Thread(target=auto_update, daemon=True).start()

# -------- API -------- #

@app.route("/movies")
def get_movies():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return jsonify(json.load(f))
    return jsonify([])

# 🔍 SEARCH ENDPOINT
@app.route("/search")
def search_movies():
    query = request.args.get("q", "").lower()

    if not os.path.exists(CACHE_FILE):
        return jsonify([])

    with open(CACHE_FILE) as f:
        movies = json.load(f)

    results = [
        m for m in movies
        if query in m.get("title", "").lower()
    ]

    return jsonify(results)

@app.route("/")
def home():
    return "Movie API Running 🚀"

if __name__ == "__main__":
    scrape_movies()
    app.run(host="0.0.0.0", port=10000)