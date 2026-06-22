# Anime Discovery Assistant 🎌

A RAG-powered conversational anime recommendation system. Ask natural-language
questions like *"something like Death Note but less dark"* and get grounded,
explainable recommendations — not just a similarity score, but actual reasoning
over real anime synopses and metadata.

## Why RAG (not just collaborative filtering)

Traditional recommendation engines compare user ratings/embeddings and can't
handle open-ended natural-language queries or explain their reasoning. This
system retrieves the most semantically relevant anime entries based on the
question itself, then uses an LLM to reason over that retrieved context and
generate a grounded, citable recommendation.

## Architecture

```
User question
     ↓
ChromaDB similarity search (Gemini embeddings)
     ↓
Top-k relevant anime (title, genres, synopsis, score)
     ↓
Gemini LLM reasons over retrieved context
     ↓
Grounded recommendation + source citations
```

## Tech Stack

- **Data source:** MAL API v2 (official MyAnimeList API, free Client ID from https://myanimelist.net/apiconfig)
- **LangChain** — RAG orchestration
- **ChromaDB** (via `langchain-chroma`) — vector store
- **Gemini API** (`gemini-embedding-001` for embeddings, `gemini-2.5-flash` for generation)
- **Streamlit** — chat interface
- **GitHub Actions** — CI pipeline (syntax check + unit tests on every push)
- **pytest** — unit tests for core logic

## Setup

```bash
git clone <your-repo-url>
cd anime-rag-assistant
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your real Gemini API key (free at https://aistudio.google.com/apikey)
```

## Usage

```bash
# 1. Fetch anime data (one-time, ~5-10 min for 600+ entries)
cd src
python fetch_data.py

# 2. Ingest into ChromaDB (embeds + stores)
python ingest.py

# 3. Run the chat app
cd ..
streamlit run app.py
```

## Incremental re-ingestion

Re-running `ingest.py` only embeds new or changed anime entries — it hashes
each entry's content and skips anything unchanged, avoiding redundant API
calls and cost.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

## Project structure

```
anime-rag-assistant/
├── .github/workflows/ci.yml   # CI pipeline
├── data/anime_data.json       # Fetched anime data
├── src/
│   ├── fetch_data.py           # Pulls data from Jikan API
│   ├── ingest.py                # Chunks + embeds + stores in ChromaDB
│   └── retriever.py             # Semantic search + LLM reasoning
├── tests/test_ingest.py        # Unit tests (no API key needed)
├── app.py                       # Streamlit chat UI
├── requirements.txt
└── .env.example
```
