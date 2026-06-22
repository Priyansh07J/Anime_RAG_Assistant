"""
Ingests anime data into ChromaDB for the RAG pipeline.

Each anime becomes one Document with a rich text body (title, genres,
themes, synopsis, score) so semantic search can match natural-language
queries like "dark psychological thriller anime" against the right entries.

Uses hash-based change detection so re-running this script after updating
data/anime_data.json only re-embeds what's new or changed.
"""
import os

# Always resolve paths relative to the project root, no matter where this script is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import os
import json
import hashlib
import time

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "anime_data.json")
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
HASH_FILE = os.path.join(PROJECT_ROOT, "chroma_db", "doc_hashes.json")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# For free-tier Gemini embedding (100 req/min quota):
# Embed ONE document at a time with 0.7s delay = ~85 req/minute (safe margin under 100/min)
BATCH_SIZE = 1
BATCH_DELAY = 0.7  # 0.7 sec between requests = ~86 requests/minute << 100/min limit

# IMPORTANT: model name as of 2026 — NOT "models/embedding-001" (deprecated)
EMBEDDING_MODEL = "gemini-embedding-001"


def get_text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def load_hashes() -> dict:
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE, "r") as f:
        return json.load(f)


def save_hashes(hashes: dict):
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        json.dump(hashes, f, indent=2)


def add_documents_with_retry(vectorstore, documents, max_retries=5):
    """Add documents with exponential backoff retry for transient API errors."""
    for attempt in range(max_retries):
        try:
            vectorstore.add_documents(documents)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Last attempt failed, re-raise
            
            # Exponential backoff: 2^attempt seconds (2, 4, 8, 16, 32)
            wait_time = 2 ** attempt
            print(f"  Transient API error: {str(e)[:80]}... Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)


def anime_to_document(anime: dict) -> Document:
    """Builds one rich text blob per anime so semantic search has
    enough signal (title + genres + themes + synopsis + score)."""
    title = anime.get("title_english") or anime.get("title") or "Unknown"
    genres = ", ".join(anime.get("genres", [])) or "Unknown"
    themes = ", ".join(anime.get("themes", [])) or "None"
    score = anime.get("score") or "N/A"
    episodes = anime.get("episodes") or "N/A"
    synopsis = anime.get("synopsis") or "No synopsis available."

    text = (
        f"Title: {title}\n"
        f"Genres: {genres}\n"
        f"Themes: {themes}\n"
        f"Score: {score}/10\n"
        f"Episodes: {episodes}\n"
        f"Synopsis: {synopsis}"
    )

    return Document(
        page_content=text,
        metadata={
            "mal_id": anime.get("mal_id"),
            "title": title,
            "score": score,
            "genres": genres,
        }
    )


def ingest_anime_data(force_reingest: bool = False):
    if not os.path.exists(DATA_PATH):
        print(f"No data file found at {DATA_PATH}. Run fetch_data.py first.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        anime_list = json.load(f)

    print(f"Loaded {len(anime_list)} anime entries from {DATA_PATH}")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    hashes = load_hashes()
    new_hashes = {}
    new_docs = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for anime in anime_list:
        mal_id = str(anime.get("mal_id"))
        doc = anime_to_document(anime)
        content_hash = get_text_hash(doc.page_content)

        if not force_reingest and hashes.get(mal_id) == content_hash:
            continue  # unchanged, skip re-embedding

        new_hashes[mal_id] = content_hash
        chunks = splitter.split_documents([doc])
        new_docs.extend(chunks)

    if not new_docs:
        print("No new or changed anime entries to ingest.")
        return

    print(f"Embedding {len(new_docs)} chunks from {len(new_hashes)} new/changed anime...")

    # Batch embeddings to respect free-tier rate limits (100 requests/minute)
    # Process in batches of 10 with 70-second delays between batches
    vectorstore = None
    for i in range(0, len(new_docs), BATCH_SIZE):
        batch = new_docs[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(new_docs) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} docs)...")
        
        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=CHROMA_DB_PATH,
                collection_name="anime_collection"
            )
        else:
            add_documents_with_retry(vectorstore, batch)
        
        # Save hash for this batch's source anime immediately after successful embedding
        batch_mal_id = batch[0].metadata.get("mal_id")
        if batch_mal_id is not None:
            mal_id_str = str(batch_mal_id)
            if mal_id_str in new_hashes:
                hashes[mal_id_str] = new_hashes[mal_id_str]
                save_hashes(hashes)  # persist progress after every batch
        
        if i + BATCH_SIZE < len(new_docs):
            print(f"  Waiting {BATCH_DELAY}s before next batch...")
            time.sleep(BATCH_DELAY)

    print("Ingestion complete.")


def get_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name="anime_collection"
    )


if __name__ == "__main__":
    ingest_anime_data()
