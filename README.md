# Anime Discovery Assistant 🎌

A RAG-powered conversational anime recommendation system. Ask natural-language questions like *"something like Death Note but less dark"* and get grounded, explainable recommendations — not just a similarity score, but actual reasoning over real anime synopses and metadata, with honest fallback when no good match exists.

**🔗 Live demo:** [anime-rag-assistant.onrender.com](https://anime-rag-assistant.onrender.com)
*(Free-tier hosting — first load after inactivity may take 30-60s to spin up.)*

---

## Why RAG (not just collaborative filtering)

Traditional recommendation engines compare user ratings/embeddings and can't handle open-ended natural-language queries or explain their reasoning. This system retrieves the most semantically relevant anime entries based on the question itself, then uses an LLM to reason over that retrieved context and generate a grounded, citable recommendation — and explicitly says so if nothing in the dataset is a good fit, rather than forcing a bad answer.

## Architecture

```
MyAnimeList Official API (v2)
        ↓  fetch_data.py
data/anime_data.json   (600 anime: title, synopsis, genres, score, episodes)
        ↓  ingest.py
1. Build rich text doc per anime
2. Hash content → skip unchanged anime (incremental ingestion)
3. Chunk (800 chars, 100 overlap) → embed (Gemini) → store
        ↓
ChromaDB  (1,180 chunks)
        ↓
User query → embed query → similarity search (top-k) → format context
        ↓
Gemini (gemini-2.5-flash) reasons over ONLY the retrieved context
        ↓
Grounded recommendation + source citations  →  Streamlit chat UI
```

## Tech Stack

- **Data source:** MyAnimeList Official API v2 (free Client ID via [myanimelist.net/apiconfig](https://myanimelist.net/apiconfig))
- **LangChain** — RAG orchestration (document loaders, text splitting, vector store interface)
- **ChromaDB** (via `langchain-chroma`) — vector store, 1,180 embedded chunks
- **Gemini API** — `gemini-embedding-001` for embeddings, `gemini-2.5-flash` for generation and evaluation
- **Streamlit** — chat interface
- **GitHub Actions** — CI pipeline (syntax check + unit tests on every push)
- **Render** — live deployment, auto-deploys on push to `main`
- **pytest** — unit tests for core logic (hashing, document formatting)

## Evaluation

Rather than assume the system works, retrieval and generation quality are measured directly using **LLM-as-judge metrics** (faithfulness, answer relevancy, context precision) implemented in `evaluator.py` — built as direct Gemini judge prompts after the `ragas` library failed to compile on Windows (a `scikit-network` C++ build dependency issue).

**What evaluation found:**
- ✅ **Answer relevancy** is consistently strong (~1.0) — answers directly address the question asked.
- ⚠️ **Faithfulness** is generally good but evaluation did catch a real instance of the model citing a genre tag not actually present in the retrieved context — caught automatically, not by manual inspection.
- ⚠️ **Context precision is a known, documented weak spot** for abstract/comparative queries (e.g. *"like X but less Y"*). Raw similarity scores for this query type cluster tightly (≈0.31–0.44) across both relevant and irrelevant candidates — a limitation of single-vector dense retrieval on a small (600-title), narrow-domain dataset, not a retrieval bug. Threshold filtering and deduplication were both tried and didn't meaningfully change this; the most likely real fix is a reranking stage, which is a natural next step (see Roadmap).
- Direct, concrete genre/keyword queries retrieve noticeably more precisely than negated/comparative ones.

## Setup

```bash
git clone https://github.com/Priyansh07J/Anime_RAG_Assistant.git
cd Anime_RAG_Assistant
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add:
#   GEMINI_API_KEY  (free at https://aistudio.google.com/apikey)
#   MAL_CLIENT_ID   (free at https://myanimelist.net/apiconfig)
```

## Usage

```bash
# 1. Fetch anime data (one-time; ~600 entries from the official MAL API)
python src/fetch_data.py

# 2. Ingest into ChromaDB — embeds + stores (incremental: re-running only
#    processes new/changed entries, skipping anything already embedded)
python src/ingest.py

# 3. Run the chat app
streamlit run app.py

# 4. (Optional) Run evaluation on a test query
python src/evaluator.py
```

> **Note on free-tier API limits:** Gemini's free tier caps embedding calls at 1,000/day and chat calls at 20/day. Full ingestion of ~1,180 chunks may need to run across more than one day on a brand-new dataset — `ingest.py`'s hash-based incremental design means re-running it simply picks up where it left off with zero wasted re-embedding.

## Running tests

```bash
pytest tests/ -v
```
Tests deliberately cover only pure logic (hash determinism, document formatting) — no live API calls — so CI can run cleanly without secrets configured.

## Project structure

```
Anime_RAG_Assistant/
├── .github/workflows/ci.yml    # CI: install, syntax check, pytest — on every push
├── data/anime_data.json        # Fetched anime data (600 entries)
├── chroma_db/                  # Pre-embedded vector store (committed for deploy)
├── src/
│   ├── fetch_data.py           # Pulls data from the official MAL API v2
│   ├── ingest.py                # Hashes, chunks, embeds, stores in ChromaDB (incremental)
│   ├── retriever.py             # Semantic search + LLM reasoning + source citations
│   └── evaluator.py             # LLM-as-judge evaluation (faithfulness, relevancy, precision)
├── tests/test_ingest.py        # Unit tests (no API key needed)
├── rebuild_hashes.py            # Recovery script — rebuilds hash index from ChromaDB directly
├── check_retrieval.py           # Diagnostic — raw similarity scores, zero LLM calls
├── app.py                       # Streamlit chat UI
├── Dockerfile                    # Container definition
├── requirements.txt              # Pinned dependencies
└── .env.example
```

## Roadmap / Known Limitations

- **Reranking** — adding a lightweight cross-encoder reranking pass over the top 15–20 retrieved candidates is the most likely fix for the context-precision gap on comparative queries.
- **CI/CD gating** — GitHub Actions (testing) and Render (deployment) currently run independently; a failing test does not yet block a deploy.
- **Static dataset** — fetched once; a scheduled re-fetch combined with the existing incremental ingestion would keep it current.

---

⭐ If you find this useful, feel free to star the repo.
