"""
Thin LLM wrapper used by app.py.

Use your own model and key — there's nothing to request from us. Config is read from
environment variables you set in your local .env (copy .env.example):
    LLM_API_BASE    e.g. https://api.openai.com/v1   (or your Azure OpenAI base URL)
    LLM_API_KEY     your API key
    LLM_EMBED_MODEL e.g. text-embedding-3-small
    LLM_CHAT_MODEL  e.g. gpt-4o-mini

The defaults below assume an OpenAI-compatible API, which also covers Azure OpenAI
once LLM_API_BASE is pointed at your deployment. If you'd rather use Anthropic's
Messages API, replace the body of complete() — the shape is different.

You're free to ignore this file entirely and do embeddings/generation your own way,
including a local/offline model if you prefer no hosted API at all.
"""

import os
import requests

API_BASE = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
API_KEY = os.environ.get("LLM_API_KEY", "")
EMBED_MODEL = os.environ.get("LLM_EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.environ.get("LLM_CHAT_MODEL", "gpt-4o-mini")

_HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def embed(texts):
    """Return a list of embedding vectors, one per input string."""
    resp = requests.post(
        f"{API_BASE}/embeddings",
        headers=_HEADERS,
        json={"model": EMBED_MODEL, "input": texts},
        timeout=30,
    )
    resp.raise_for_status()
    return [item["embedding"] for item in resp.json()["data"]]


def complete(system, user):
    """Return the model's text reply to a system + user prompt."""
    resp = requests.post(
        f"{API_BASE}/chat/completions",
        headers=_HEADERS,
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
