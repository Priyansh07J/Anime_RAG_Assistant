# rebuild_hashes.py
import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ingest import anime_to_document, get_text_hash, save_hashes, DATA_PATH, get_vectorstore

with open(DATA_PATH, "r", encoding="utf-8") as f:
    anime_list = json.load(f)

vectorstore = get_vectorstore()
# Get all mal_ids currently stored in ChromaDB
existing = vectorstore._collection.get(include=["metadatas"])
embedded_mal_ids = set(str(m.get("mal_id")) for m in existing["metadatas"] if m.get("mal_id") is not None)

print(f"Found {len(embedded_mal_ids)} unique anime already embedded in ChromaDB")

hashes = {}
for anime in anime_list:
    mal_id = str(anime.get("mal_id"))
    if mal_id in embedded_mal_ids:
        doc = anime_to_document(anime)
        hashes[mal_id] = get_text_hash(doc.page_content)

save_hashes(hashes)
print(f"Rebuilt doc_hashes.json with {len(hashes)} entries")