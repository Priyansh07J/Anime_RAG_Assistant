# check_retrieval.py
from src.ingest import get_vectorstore

vs = get_vectorstore()
results = vs.similarity_search_with_score('something like Death Note but less dark', k=10)

for doc, score in results:
    title = doc.metadata.get('title')
    print(f"{1-score:.3f} | {title}")