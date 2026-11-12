"""
core/rag_engine.py — RAG engine: ChromaDB vector store + chunking + retrieval.

Public API:
    • index_document(text, filename)            -> int
    • clear_collection()                        -> None
    • search_chunks(question, top_k)            -> list[dict]
    • build_messages(question, chunks)          -> list[dict]
    • ask(question, model, top_k)               -> dict           (non-streaming)
    • ask_stream(question, model, top_k)        -> Iterator[str]  (streaming)

Run the self-test with:
    python -m core.rag_engine
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Iterator

# Allow both `python -m core.rag_engine` and `python core/rag_engine.py`.
if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle (.exe)
    # __file__ is inside a temporary _MEI folder that gets deleted.
    # We want chroma_db to live next to the executable.
    _PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    # Running from source code
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.ollama_client import (
    DEFAULT_LLM_MODEL,
    chat,
    chat_stream,
    get_embedding,
    get_embeddings,
)


# ──────────────────────── Configuration ────────────────────────

# chroma_db lives at the project root (next to main.py / future .exe).
CHROMA_DB_PATH: str = str(_PROJECT_ROOT / "chroma_db")
COLLECTION_NAME: str = "documents"

CHUNK_SIZE: int = 800
CHUNK_OVERLAP: int = 150
TOP_K: int = 3

SYSTEM_PROMPT: str = (
    "You are a retrieval assistant. Answer strictly based on the provided context.\n"
    "If the answer is not present in the context, respond: "
    "\"The provided documents do not contain the answer.\"\n"
    "Do not invent facts. Answer in the same language as the question."
)


# ──────────────────────── ChromaDB client (cached) ────────────────────────

_client: Any = None


def get_client() -> Any:
    """Return (and cache) a single PersistentClient for the process."""
    global _client
    if _client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _client


def get_collection() -> Any:
    """Get-or-create the collection with cosine metric (best for text)."""
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def clear_collection() -> None:
    """Delete the entire collection (used by the 'Clear Database' button)."""
    try:
        get_client().delete_collection(COLLECTION_NAME)
    except Exception:
        # Collection may not exist — that's fine.
        pass


# ──────────────────────── Chunking ────────────────────────

def split_text(text: str) -> list[str]:
    """Split text into ~800-char chunks with 150-char overlap."""
    if not text or not text.strip():
        raise ValueError("Cannot split empty text.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = [c.strip() for c in splitter.split_text(text) if c.strip()]
    if not chunks:
        raise ValueError("No non-empty chunks produced after splitting.")
    return chunks


# ──────────────────────── Indexing ────────────────────────

def _make_chunk_ids(filename: str, count: int) -> list[str]:
    """
    Deterministic IDs — re-indexing the same file overwrites its chunks
    instead of duplicating them.
    """
    digest = hashlib.sha1(os.path.basename(filename).encode("utf-8")).hexdigest()[:10]
    return [f"{digest}::{i:04d}" for i in range(count)]


def index_document(text: str, filename: str) -> int:
    """
    Chunk, embed, and store a document in ChromaDB.

    Idempotent: previous chunks for `filename` are deleted first.

    Returns the number of chunks indexed.
    """
    chunks = split_text(text)
    embeddings = get_embeddings(chunks)
    ids = _make_chunk_ids(filename, len(chunks))
    metadatas = [
        {"source": filename, "chunk_index": i, "chunk_total": len(chunks)}
        for i in range(len(chunks))
    ]

    collection = get_collection()

    # Idempotency: drop old chunks for this file.
    if collection.count() > 0:
        try:
            collection.delete(where={"source": filename})
        except Exception:
            pass

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


# ──────────────────────── Retrieval ────────────────────────

def search_chunks(question: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Return top-K relevant chunks with metadata and cosine distance."""
    question = (question or "").strip()
    if not question:
        raise ValueError("Question is empty.")

    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []

    query_embedding = get_embedding(question)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total),
        include=["documents", "metadatas", "distances"],
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    hits: list[dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "chunk_index": meta.get("chunk_index"),
            "distance": dist,
        })
    return hits


# ──────────────────────── Prompt building ────────────────────────

def build_messages(question: str, chunks: list[str]) -> list[dict[str, str]]:
    """Build system + user messages for the LLM."""
    context = "\n\n---\n\n".join(chunks)
    user_content = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Answer strictly based on the context above. "
        "If information is insufficient, say so."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ──────────────────────── High-level API ────────────────────────

def ask(
    question: str,
    model: str = DEFAULT_LLM_MODEL,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """
    Full RAG pipeline (non-streaming).

    Returns:
        {
          "answer": str,
          "sources": [ {text, source, chunk_index, distance}, ... ],
          "context_found": bool,
        }
    """
    hits = search_chunks(question, top_k=top_k)
    if not hits:
        return {
            "answer": "The database is empty. Index documents first.",
            "sources": [],
            "context_found": False,
        }

    messages = build_messages(question, [h["text"] for h in hits])
    answer = chat(messages, model=model)
    return {"answer": answer, "sources": hits, "context_found": True}


def ask_stream(
    question: str,
    model: str = DEFAULT_LLM_MODEL,
    top_k: int = TOP_K,
) -> Iterator[str]:
    """
    Streaming RAG pipeline — yields content chunks.
    If no context is found, yields a single notice string.
    """
    hits = search_chunks(question, top_k=top_k)
    if not hits:
        yield "The database is empty. Index documents first."
        return

    messages = build_messages(question, [h["text"] for h in hits])
    yield from chat_stream(messages, model=model)


# ──────────────────────── Self-test ────────────────────────

SAMPLE_NAME: str = "sample_stage1.txt"

SAMPLE_TEXT: str = """\
"ROMASHKA" COMPANY — CUSTOMER HANDBOOK
======================================

1. ABOUT THE COMPANY
"Romashka" is a Russian manufacturer of home appliances. Founded in 2005.
Product line: kettles, multi-cookers, vacuum cleaners, irons, blenders.
Headquarters: Moscow.

2. WARRANTY
All "Romashka" products come with a 24-month warranty from the purchase date.
The warranty covers manufacturing defects.
The warranty does NOT cover mechanical damage, signs of tampering, or misuse.
A receipt and warranty card are required for a warranty claim.

3. RETURNS
Items in good condition may be returned within 14 days of purchase,
provided the receipt and original packaging are preserved. Items must show
no signs of use. Refunds are issued to the customer's card within 10
business days after approval of the request.

4. DELIVERY
Delivery within Moscow is free for orders over 5,000 RUB. Moscow delivery
is handled by courier within 1-2 business days. Regional delivery is
handled by partner logistics companies within 3-7 business days. Regional
shipping cost is calculated individually at checkout.

5. PAYMENT
We accept bank cards (Visa, MasterCard, MIR), cash on delivery,
and the Faster Payments System (SBP).

6. SUPPORT
Hotline: 8-800-555-35-35 (free within Russia).
Hours: daily, 9:00-21:00 Moscow time.
Email: support@romashka.example

7. LEGAL
LLC "Romashka", Tax ID 7701234567, Reg. ID 770101001.
Legal address: 1 Primernaya St., Office 100, Moscow.
"""


def _run_test() -> None:
    sample_path = _PROJECT_ROOT / SAMPLE_NAME
    if not sample_path.exists():
        sample_path.write_text(SAMPLE_TEXT, encoding="utf-8")
        print(f"[setup] Created sample file: {sample_path}")
    else:
        print(f"[setup] Sample file already exists: {sample_path}")

    text = sample_path.read_text(encoding="utf-8")

    print("\n[1/3] Clearing collection and indexing document...")
    clear_collection()
    n_chunks = index_document(text, SAMPLE_NAME)
    print(f"      Chunks indexed: {n_chunks}")

    question = "How many months does the warranty last?"
    print(f"\n[2/3] Question: {question}")
    result = ask(question)

    print(f"\n[3/3] Answer ({DEFAULT_LLM_MODEL}):")
    print("-" * 64)
    print(result["answer"] or "<empty>")
    print("-" * 64)

    print("\nSources (top-K):")
    for i, hit in enumerate(result["sources"], 1):
        preview = hit["text"][:120].replace("\n", " ")
        print(
            f"  {i}. {hit['source']} | chunk #{hit['chunk_index']} "
            f"| distance={hit['distance']:.4f} | \"{preview}...\""
        )


if __name__ == "__main__":
    try:
        _run_test()
    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)