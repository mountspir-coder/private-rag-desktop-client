"""
core/ollama_client.py — Thin wrapper around the Ollama HTTP API.

Public API:
    • ping()                          -> bool
    • has_model(name)                 -> bool
    • get_embedding(text, model)      -> list[float]
    • get_embeddings(texts, model)    -> list[list[float]]
    • chat(messages, model)           -> str               (non-streaming)
    • chat_stream(messages, model)    -> Iterator[str]     (streaming)

Why we explicitly set host= and NO_PROXY:
    • The Ollama Python client reads OLLAMA_HOST from the environment.
      On Windows, the Ollama installer often sets OLLAMA_HOST=0.0.0.0
      (a *bind* address for the server), which then leaks into child
      processes. If the client picks it up, it tries to connect to
      http://0.0.0.0:11434 and fails.
    • Fix: pass host= explicitly so the client never reads OLLAMA_HOST.
    • Defense-in-depth: append localhost addresses to NO_PROXY so that
      even behind a corporate HTTP proxy, requests to the local Ollama
      server bypass it.
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import ollama


# ──────────────────────── Proxy safety net ────────────────────────
# Ensure localhost never goes through an HTTP proxy (Windows corporate
# environments sometimes set HTTP_PROXY / HTTPS_PROXY globally).
_no_proxy = os.environ.get("NO_PROXY", "") or os.environ.get("no_proxy", "")
for _h in ("localhost", "127.0.0.1", "::1"):
    if _h not in _no_proxy:
        _no_proxy = f"{_no_proxy},{_h}" if _no_proxy else _h
os.environ["NO_PROXY"] = _no_proxy
os.environ["no_proxy"] = _no_proxy


# ──────────────────────── Defaults ────────────────────────

OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

DEFAULT_LLM_MODEL: str = "llama3"
DEFAULT_EMBED_MODEL: str = "nomic-embed-text"
DEFAULT_TEMPERATURE: float = 0.1

OLLAMA_HOST_HINT: str = (
    "Cannot reach Ollama at http://127.0.0.1:11434. "
    "Make sure the Ollama server is running."
)


# ──────────────────────── Client ────────────────────────
# Pass host= explicitly. This overrides OLLAMA_HOST from the environment
# (which on Windows is often wrongly set to 0.0.0.0 by the Ollama installer).
_client: ollama.Client = ollama.Client(host=OLLAMA_BASE_URL)


# ──────────────────────── Health checks ────────────────────────

def ping() -> bool:
    """Return True if the Ollama server responds, False otherwise."""
    try:
        _client.list()
        return True
    except Exception:
        return False


def has_model(name: str) -> bool:
    """Return True if model `name` is present in the local Ollama library."""
    try:
        response: dict[str, Any] = _client.list()
    except Exception:
        return False

    models = response.get("models") or response.get("model") or []
    for item in models:
        model_name = item.get("name") or item.get("model") or ""
        if model_name == name or model_name.startswith(f"{name}:"):
            return True
    return False


# ──────────────────────── Embeddings ────────────────────────

def get_embedding(text: str, model: str = DEFAULT_EMBED_MODEL) -> list[float]:
    """Get an embedding vector for a single text via /api/embeddings."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot embed empty text.")

    try:
        response: dict[str, Any] = _client.embeddings(model=model, prompt=text)
    except ollama.ResponseError as exc:
        raise RuntimeError(
            f"Ollama failed to embed (model '{model}'). "
            f"Pull it with: `ollama pull {model}`. Details: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"{OLLAMA_HOST_HINT} Details: {exc}") from exc

    embedding = response.get("embedding")
    if not embedding:
        raise RuntimeError("Ollama returned an empty embedding.")
    return embedding


def get_embeddings(
    texts: list[str],
    model: str = DEFAULT_EMBED_MODEL,
) -> list[list[float]]:
    """Batch embeddings (sequential loop — reliable on all Ollama versions)."""
    return [get_embedding(t, model=model) for t in texts]


# ──────────────────────── Chat ────────────────────────

def chat(
    messages: list[dict[str, str]],
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """Non-streaming chat completion. Returns the full answer string."""
    try:
        response: dict[str, Any] = _client.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
        )
    except ollama.ResponseError as exc:
        raise RuntimeError(
            f"Ollama failed to generate (model '{model}'). "
            f"Pull it with: `ollama pull {model}`. Details: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"{OLLAMA_HOST_HINT} Details: {exc}") from exc

    content = ((response.get("message") or {}).get("content") or "").strip()
    return content


def chat_stream(
    messages: list[dict[str, str]],
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> Iterator[str]:
    """Streaming chat completion — yields content chunks as they arrive."""
    try:
        stream = _client.chat(
            model=model,
            messages=messages,
            stream=True,
            options={"temperature": temperature},
        )
        for chunk in stream:
            content = ((chunk.get("message") or {}).get("content") or "")
            if content:
                yield content
    except ollama.ResponseError as exc:
        raise RuntimeError(
            f"Ollama failed to generate (model '{model}'). "
            f"Pull it with: `ollama pull {model}`. Details: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"{OLLAMA_HOST_HINT} Details: {exc}") from exc