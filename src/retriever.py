"""
Retrieves relevant anime from ChromaDB based on a natural-language query,
then asks Gemini to reason over the retrieved entries and give a grounded,
explainable recommendation — citing actual anime titles instead of just
returning a similarity-ranked list.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from ingest import get_vectorstore

load_dotenv()

CHAT_MODEL = "gemini-2.5-flash"  # fast + free-tier friendly
TOP_K = 5  # how many anime chunks to retrieve per query


def retrieve_anime(query: str, k: int = TOP_K):
    """Returns the top-k most relevant anime chunks for a query,
    each with similarity score and source metadata."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=k)
    return results


def format_context(results) -> str:
    """Turns retrieved chunks into a clean context block for the LLM prompt."""
    blocks = []
    for doc, score in results:
        blocks.append(f"{doc.page_content}\n(Relevance score: {1 - score:.2f})")
    return "\n\n---\n\n".join(blocks)


def generate_answer(query: str, results) -> str:
    """Sends retrieved anime context + the user's question to Gemini
    and returns a grounded, explainable recommendation."""
    context = format_context(results)

    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.4)

    prompt = (
        "You are an anime recommendation assistant. Answer the user's question "
        "using ONLY the anime information provided below. Always mention the "
        "specific anime titles you're recommending and briefly explain why each "
        "one fits the request. If none of the provided anime fit well, say so "
        "honestly instead of forcing a recommendation.\n\n"
        f"ANIME DATA:\n{context}\n\n"
        f"USER QUESTION: {query}\n\n"
        "ANSWER:"
    )

    response = llm.invoke(prompt)
    return response.content


def ask(query: str, k: int = TOP_K) -> dict:
    """Main entry point: retrieve + generate, returns answer plus sources."""
    results = retrieve_anime(query, k=k)

    if not results:
        return {
            "answer": "I couldn't find any matching anime in the database. Try a different query.",
            "sources": []
        }

    answer = generate_answer(query, results)
    sources = [doc.metadata.get("title", "Unknown") for doc, _ in results]

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":
    test_query = "Recommend something like Death Note but less dark"
    result = ask(test_query)
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:", result["sources"])

def retrieve_anime(query: str, k: int = TOP_K):
    vectorstore = get_vectorstore()
    raw_results = vectorstore.similarity_search_with_score(query, k=k * 4)
    
    # Deduplicate by title — keep only the best-scoring chunk per anime
    seen_titles = {}
    for doc, score in raw_results:
        title = doc.metadata.get("title", "Unknown")
        if title not in seen_titles or score < seen_titles[title][1]:
            seen_titles[title] = (doc, score)
    
    deduped = sorted(seen_titles.values(), key=lambda x: x[1])  # lower score = more similar
    return deduped[:k]