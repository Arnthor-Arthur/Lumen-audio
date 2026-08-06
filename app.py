"""
Lumen Audio — grounded Q&A over a knowledge base.

This skeleton runs as-is and returns a stub response. Your job is to fill in the
RAG logic where marked TODO:
  1. chunk + index the documents in data/
  2. retrieve the most relevant chunk(s) for a question
  3. generate a grounded answer WITH a citation to the source file
  4. decline gracefully when the question isn't covered by the KB

Helpers for embeddings and chat completion are in llm.py.
Run with:  python app.py
"""

import os
import glob
import numpy as np
from flask import Flask, request, jsonify

import llm  # embed() and complete() — see llm.py

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Below this cosine similarity, we don't trust retrieval enough to even ask the LLM.
SIM_THRESHOLD = float(os.environ.get("SIM_THRESHOLD", "0.25"))
# A second chunk is included as extra context only if it's this close to the top match.
SECOND_CHUNK_MARGIN = 0.05
REFUSAL_TEXT = "I don't know — that isn't covered in our policy knowledge base."

SYSTEM_PROMPT = (
    "You are a support assistant for Lumen Audio, a consumer-audio company. "
    "Answer the customer's question using ONLY the context provided below — never use "
    "outside knowledge or make anything up. "
    "If the context does not contain the answer, respond with exactly this sentence and "
    f"nothing else: \"{REFUSAL_TEXT}\" "
    "Otherwise, answer concisely and directly, in 1-3 sentences."
)


def load_documents():
    """Load every markdown article in data/ as (source_name, text)."""
    docs = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            docs.append((os.path.basename(path), f.read().strip()))
    return docs


# Load once at startup. The candidate decides how to chunk/index from here.
DOCUMENTS = load_documents()

# Each article is already short and single-topic, so one chunk per document is enough —
# no benefit to splitting further at this KB size.
CHUNK_SOURCES = [source for source, _ in DOCUMENTS]
CHUNK_TEXTS = [text for _, text in DOCUMENTS]
_vectors = np.array(llm.embed(CHUNK_TEXTS), dtype=np.float32)
CHUNK_VECTORS = _vectors / np.linalg.norm(_vectors, axis=1, keepdims=True)


def retrieve(question, top_k=2):
    """Return up to `top_k` (source, text, score) tuples for the question, best first."""
    q_vec = np.array(llm.embed([question])[0], dtype=np.float32)
    q_vec = q_vec / np.linalg.norm(q_vec)
    scores = CHUNK_VECTORS @ q_vec

    order = np.argsort(-scores)
    best_score = scores[order[0]]
    hits = [(CHUNK_SOURCES[order[0]], CHUNK_TEXTS[order[0]], float(best_score))]
    for idx in order[1:top_k]:
        if best_score - scores[idx] <= SECOND_CHUNK_MARGIN:
            hits.append((CHUNK_SOURCES[idx], CHUNK_TEXTS[idx], float(scores[idx])))
    return hits


@app.route("/health")
def health():
    return jsonify({"ok": True, "documents_loaded": len(DOCUMENTS)})


@app.route("/ask", methods=["POST"])
def ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "send JSON like {\"question\": \"...\"}"}), 400

    hits = retrieve(question)

    # Guardrail 1: nothing similar enough to the question — don't even ask the LLM.
    if hits[0][2] < SIM_THRESHOLD:
        return jsonify({"answer": REFUSAL_TEXT, "sources": []})

    context = "\n\n".join(f"[{source}]\n{text}" for source, text, _ in hits)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = llm.complete(SYSTEM_PROMPT, user_prompt).strip()

    # Guardrail 2: the LLM itself decided the context doesn't answer the question —
    # a topically-close chunk can pass guardrail 1 without actually containing the answer.
    if REFUSAL_TEXT.lower() in answer.lower():
        return jsonify({"answer": REFUSAL_TEXT, "sources": []})

    return jsonify({
        "answer": answer,
        "sources": [source for source, _, _ in hits],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
