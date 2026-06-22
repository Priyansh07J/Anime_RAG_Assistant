"""
RAGAS-style evaluation metrics implemented directly with Gemini,
avoiding the full ragas library (which fails to build on Windows
due to a scikit-network C++ dependency).

Implements the same core LLM-as-judge metrics RAGAS uses:
- Faithfulness: is the answer grounded in the retrieved context, or does it hallucinate?
- Answer Relevancy: does the answer actually address the user's question?
- Context Precision: were the retrieved chunks actually relevant to the question?

Each metric asks Gemini to act as a judge and return a score 0.0-1.0 plus reasoning.
"""

import os
import re
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

JUDGE_MODEL = "gemini-2.5-flash"


def _get_judge():
    return ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0.0)


def _extract_score(response_text: str) -> tuple[float, str]:
    """Parses a 'SCORE: 0.x' and 'REASON: ...' formatted judge response."""
    score_match = re.search(r"SCORE:\s*([0-9]*\.?[0-9]+)", response_text)
    reason_match = re.search(r"REASON:\s*(.+)", response_text, re.DOTALL)

    score = float(score_match.group(1)) if score_match else 0.0
    reason = reason_match.group(1).strip() if reason_match else response_text.strip()
    return min(max(score, 0.0), 1.0), reason


def evaluate_faithfulness(answer: str, context: str) -> dict:
    """Is the answer grounded in the retrieved context, or does it invent facts
    not present in the retrieved anime data?"""
    judge = _get_judge()
    prompt = (
        "You are evaluating an AI assistant's answer for FAITHFULNESS to its source context.\n"
        "Faithfulness means: every factual claim in the answer must be supported by the context. "
        "If the answer mentions anime, genres, or facts NOT present in the context, faithfulness is low.\n\n"
        f"CONTEXT (retrieved anime data):\n{context}\n\n"
        f"ANSWER TO EVALUATE:\n{answer}\n\n"
        "Score faithfulness from 0.0 (completely made up, not grounded in context) "
        "to 1.0 (every claim is directly supported by the context).\n\n"
        "Respond in EXACTLY this format:\n"
        "SCORE: <number between 0.0 and 1.0>\n"
        "REASON: <one sentence explanation>"
    )
    response = judge.invoke(prompt)
    score, reason = _extract_score(response.content)
    return {"metric": "faithfulness", "score": score, "reason": reason}


def evaluate_answer_relevancy(query: str, answer: str) -> dict:
    """Does the answer actually address what the user asked, or does it
    go off-topic / dodge the question?"""
    judge = _get_judge()
    prompt = (
        "You are evaluating an AI assistant's answer for RELEVANCY to the user's question.\n"
        "Relevancy means: the answer directly addresses what was asked, without padding, "
        "irrelevant tangents, or dodging the question.\n\n"
        f"USER QUESTION:\n{query}\n\n"
        f"ANSWER TO EVALUATE:\n{answer}\n\n"
        "Score relevancy from 0.0 (does not address the question at all) "
        "to 1.0 (directly and completely addresses the question).\n\n"
        "Respond in EXACTLY this format:\n"
        "SCORE: <number between 0.0 and 1.0>\n"
        "REASON: <one sentence explanation>"
    )
    response = judge.invoke(prompt)
    score, reason = _extract_score(response.content)
    return {"metric": "answer_relevancy", "score": score, "reason": reason}


def evaluate_context_precision(query: str, context: str) -> dict:
    """Were the retrieved anime chunks actually relevant to the question,
    or was retrieval noisy / off-target?"""
    judge = _get_judge()
    prompt = (
        "You are evaluating the PRECISION of retrieved context for a search query.\n"
        "Precision means: the retrieved anime entries are actually relevant and useful "
        "for answering the query, without irrelevant or off-topic entries mixed in.\n\n"
        f"USER QUERY:\n{query}\n\n"
        f"RETRIEVED CONTEXT:\n{context}\n\n"
        "Score precision from 0.0 (retrieved entries are mostly irrelevant to the query) "
        "to 1.0 (every retrieved entry is genuinely relevant to the query).\n\n"
        "Respond in EXACTLY this format:\n"
        "SCORE: <number between 0.0 and 1.0>\n"
        "REASON: <one sentence explanation>"
    )
    response = judge.invoke(prompt)
    score, reason = _extract_score(response.content)
    return {"metric": "context_precision", "score": score, "reason": reason}


def evaluate_response(query: str, answer: str, context: str) -> dict:
    """Runs all three metrics for a single query/answer/context triple.
    Returns a combined results dict."""
    faithfulness = evaluate_faithfulness(answer, context)
    relevancy = evaluate_answer_relevancy(query, answer)
    precision = evaluate_context_precision(query, context)

    overall = round((faithfulness["score"] + relevancy["score"] + precision["score"]) / 3, 2)

    return {
        "query": query,
        "faithfulness": faithfulness,
        "answer_relevancy": relevancy,
        "context_precision": precision,
        "overall_score": overall
    }


if __name__ == "__main__":
    from retriever import ask, retrieve_anime, format_context

    test_query = "Recommend something like Death Note but less dark"

    results = retrieve_anime(test_query)
    context = format_context(results)
    response = ask(test_query)
    answer = response["answer"]

    print("Running evaluation...\n")
    eval_result = evaluate_response(test_query, answer, context)

    print(json.dumps(eval_result, indent=2))