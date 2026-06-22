"""
Unit tests for the anime RAG pipeline.
These tests avoid calling the live Gemini API or needing real credentials —
they test the pure logic (hashing, document formatting) so CI can run them
on every push without secrets configured.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ingest import get_text_hash, anime_to_document


def test_get_text_hash_is_deterministic():
    text = "Death Note synopsis here"
    assert get_text_hash(text) == get_text_hash(text)


def test_get_text_hash_changes_with_content():
    hash_a = get_text_hash("Death Note")
    hash_b = get_text_hash("Attack on Titan")
    assert hash_a != hash_b


def test_anime_to_document_includes_title():
    sample_anime = {
        "title": "Death Note",
        "title_english": "Death Note",
        "genres": ["Mystery", "Psychological"],
        "themes": ["Psychological"],
        "score": 8.6,
        "episodes": 37,
        "synopsis": "A high schooler finds a notebook that kills."
    }
    doc = anime_to_document(sample_anime)
    assert "Death Note" in doc.page_content
    assert "Mystery" in doc.page_content
    assert doc.metadata["title"] == "Death Note"


def test_anime_to_document_handles_missing_fields():
    sparse_anime = {"title": "Unknown Show"}
    doc = anime_to_document(sparse_anime)
    assert "Unknown Show" in doc.page_content
    assert "No synopsis available." in doc.page_content
