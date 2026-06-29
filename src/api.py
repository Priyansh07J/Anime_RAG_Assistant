"""
FastAPI layer for the Anime Discovery Assistant.

Wraps the existing retriever.py RAG logic (unchanged) as REST endpoints,
and adds a small live MAL image-lookup endpoint so the frontend can show
real cover art on source cards without re-ingesting the dataset.
"""
import os
import sys
import time
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import json
from fastapi.responses import StreamingResponse

from retriever import retrieve_anime, generate_answer_stream

load_dotenv()

MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
MAL_DETAIL_URL = "https://api.myanimelist.net/v2/anime/{id}"
MAL_FIELDS = "id,title,main_picture,mean,genres"

app = FastAPI(title="Anime Discovery Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # same-origin in production (served from one container); open for local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- simple in-memory cache for MAL image lookups (per mal_id) ----
# Avoids re-hitting MAL's API for titles that show up across multiple queries.
# Resets on container restart — acceptable, this is a cache, not the source of truth.
_image_cache: dict[int, dict] = {}

PLACEHOLDER_IMAGE = {
    "image_url": None,
    "title": None,
}


class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []  # [{role, content}, ...] — reserved for future multi-turn use


class SourceOut(BaseModel):
    mal_id: int | None
    title: str
    score: float | None       # MAL community rating, out of 10
    genres: str
    relevance: float          # retrieval similarity, 0-1, rounded


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


@app.get("/api/health")
def health():
    """Used by Render and by the frontend's cold-start detector."""
    return {"status": "ok"}


@app.get("/api/suggestions")
def suggestions():
    pool = [
        "Something like Death Note but less dark",
        "A short, feel-good anime under 13 episodes",
        "Best slow-burn romance with strong characters",
        "Mind-bending sci-fi like Steins;Gate",
        "Something with a found-family theme",
        "Underrated psychological thriller anime",
    ]
    return {"prompts": random.sample(pool, k=4)}


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = retrieve_anime(query)

    def event_stream():
        if not results:
            payload = {
                "sources": [],
                "no_match": True,
            }
            yield "I couldn't find any matching anime in the database. Try a different query."
            yield f"\n__SOURCES__{json.dumps(payload)}"
            return

        for chunk in generate_answer_stream(query, results):
            yield chunk

        sources = []
        for doc, dist in results:
            meta = doc.metadata
            sources.append({
                "mal_id": meta.get("mal_id"),
                "title": meta.get("title", "Unknown"),
                "score": _safe_float(meta.get("score")),
                "genres": meta.get("genres", ""),
                "relevance": round(max(0.0, 1 - dist), 2),
            })

        # Sources are sent as one final marked chunk after all answer text,
        # so the frontend can split the stream into "prose so far" vs
        # "structured source cards" without needing a second request.
        yield f"\n__SOURCES__{json.dumps({'sources': sources})}"

    return StreamingResponse(event_stream(), media_type="text/plain")


@app.get("/api/anime-image/{mal_id}")
def anime_image(mal_id: int):
    """
    Live lookup of an anime's cover image from the official MAL API,
    by mal_id. Cached in-memory so repeat titles across queries don't
    re-hit MAL. Falls back to a null image_url (frontend shows a
    placeholder) rather than failing the whole chat response.
    """
    if mal_id in _image_cache:
        return _image_cache[mal_id]

    if not MAL_CLIENT_ID:
        return PLACEHOLDER_IMAGE

    try:
        resp = requests.get(
            MAL_DETAIL_URL.format(id=mal_id),
            headers={"X-MAL-CLIENT-ID": MAL_CLIENT_ID},
            params={"fields": MAL_FIELDS},
            timeout=6,
        )
        if resp.status_code != 200:
            _image_cache[mal_id] = PLACEHOLDER_IMAGE
            return PLACEHOLDER_IMAGE

        data = resp.json()
        picture = data.get("main_picture", {}) or {}
        result = {
            "image_url": picture.get("large") or picture.get("medium"),
            "title": data.get("title"),
        }
        _image_cache[mal_id] = result
        return result

    except requests.exceptions.RequestException:
        # Network hiccup or rate limit — don't break the chat response over an image.
        _image_cache[mal_id] = PLACEHOLDER_IMAGE
        return PLACEHOLDER_IMAGE


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---- serve the built React frontend (production) ----
# In Docker, the React build output is copied to ./static relative to this file.
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(_static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        """Any non-API route falls through to index.html so React Router
        (if added later) and direct page refreshes both work."""
        index_path = os.path.join(_static_dir, "index.html")
        return FileResponse(index_path)
