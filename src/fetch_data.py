"""
Fetches anime data from the OFFICIAL MyAnimeList API v2
and saves it as JSON for ingestion into the RAG pipeline.

Official docs: https://myanimelist.net/apiconfig/references/api/v2
Requires a free Client ID from https://myanimelist.net/apiconfig (no OAuth needed
for public read-only endpoints like ranking — just the X-MAL-CLIENT-ID header).
"""
import os

# Always resolve paths relative to the project root, no matter where this script is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "anime_data.json")
BASE_URL = "https://api.myanimelist.net/v2/anime/ranking"
LIMIT_PER_PAGE = 100  # MAL API max per request
PAGES_TO_FETCH = 6  # 6 x 100 = 600 anime total
SLEEP_BETWEEN_REQUESTS = 1.0

FIELDS = "id,title,alternative_titles,synopsis,genres,mean,num_episodes,start_season,status,rank,popularity"


def fetch_top_anime(pages: int = PAGES_TO_FETCH) -> list:
    if not MAL_CLIENT_ID:
        print("ERROR: MAL_CLIENT_ID not found in .env file. Add it before running this script.")
        return []

    headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
    all_anime = []
    offset = 0

    for page in range(1, pages + 1):
        print(f"Fetching page {page}/{pages} (offset {offset})...")

        params = {
            "ranking_type": "all",
            "limit": LIMIT_PER_PAGE,
            "offset": offset,
            "fields": FIELDS
        }

        response = None
        for attempt in range(3):
            try:
                response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    break
                print(f"  Attempt {attempt + 1} failed (status {response.status_code}): {response.text[:150]}")
            except requests.exceptions.RequestException as e:
                print(f"  Attempt {attempt + 1} failed ({e}), retrying...")
            time.sleep(3)

        if response is None or response.status_code != 200:
            print(f"  Skipping page {page} after 3 failed attempts.")
            offset += LIMIT_PER_PAGE
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue

        payload = response.json()
        entries = payload.get("data", [])

        if not entries:
            print("  No more entries, stopping.")
            break

        for item in entries:
            anime = item.get("node", {})
            alt_titles = anime.get("alternative_titles", {})
            start_season = anime.get("start_season", {}) or {}

            all_anime.append({
                "mal_id": anime.get("id"),
                "title": anime.get("title"),
                "title_english": alt_titles.get("en") or anime.get("title"),
                "synopsis": anime.get("synopsis") or "",
                "genres": [g["name"] for g in anime.get("genres", [])],
                "themes": [],  # v2 ranking endpoint doesn't return themes separately
                "score": anime.get("mean"),
                "episodes": anime.get("num_episodes"),
                "year": start_season.get("year"),
                "type": None,
                "status": anime.get("status"),
                "rank": anime.get("rank"),
                "popularity": anime.get("popularity"),
            })

        offset += LIMIT_PER_PAGE
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    return all_anime


def save_anime_data(anime_list: list):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(anime_list, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(anime_list)} anime entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    anime_list = fetch_top_anime()
    if anime_list:
        save_anime_data(anime_list)
    else:
        print("No anime data was fetched — check your internet connection or try again later.") 