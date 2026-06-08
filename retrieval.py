"""Embedding + vector store + retrieval for The Unofficial Guide.

Pipeline stages 3 and 4 from planning.md:
    3. EMBEDDING + VECTOR STORE -> embed each chunk with all-MiniLM-L6-v2, store in
                                   ChromaDB with source metadata.
    4. RETRIEVAL                -> embed the query, similarity-search the top-k chunks.

Usage:
    python retrieval.py --build          # (re)build the index from documents/
    python retrieval.py                  # build if needed, then run the eval queries
    python retrieval.py -q "your query"  # ad-hoc query against the existing index

Design choices (see planning.md > Retrieval Approach):
  - Embedding model: all-MiniLM-L6-v2 (local, free, 384-dim).
  - Distance: cosine. With normalized embeddings, distance = 1 - cosine similarity, so
    0 = identical and ~1 = unrelated. This matches the 0.6-0.7 "weak match" thresholds
    the assignment uses for debugging.
  - Each chunk is embedded WITH its source label prepended (helps building-name queries),
    but the clean chunk text is what's stored and returned for the LLM and for display.
  - Top-k defaults to 5.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import chromadb

from ingest import build_chunks

MODEL_NAME = "all-MiniLM-L6-v2"
PERSIST_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "housing"
DEFAULT_TOP_K = 5

# Test queries (planning.md > Evaluation Plan).
EVAL_QUERIES = [
    "What do tenants say about flooding or water problems at the Hudson Tea Building?",
    "How should I pick an apartment in Hoboken to minimize flood risk?",
    "Is Uptown or Downtown Hoboken better and cheaper for a quieter place to live?",
    "For a student on a budget, how does renting in Jersey City compare to Hoboken?",
    "What are tenants' complaints about management at Hoboken South Waterfront (333 River Street)?",
]


@dataclass
class RetrievedChunk:
    text: str
    source: str
    chunk_index: int
    distance: float


# --- Embedding model (loaded once) --------------------------------------------

_model = None


def get_model():
    """Load the SentenceTransformer once and reuse it (loading is the slow part)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]):
    """Embed a list of texts into normalized vectors (so cosine distance is meaningful)."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


# --- Stage 3: build the vector store ------------------------------------------

def build_index(persist_dir: Path = PERSIST_DIR, reset: bool = True):
    """Load -> clean -> chunk -> embed -> store every chunk in ChromaDB with metadata."""
    chunks = build_chunks()
    if not chunks:
        raise RuntimeError("No chunks produced — add documents to documents/ and re-run.")

    client = chromadb.PersistentClient(path=str(persist_dir))
    if reset:
        # Start clean so re-running doesn't pile up duplicates.
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine distance, not the L2 default
    )

    # Assign each chunk its position within its own source document.
    per_source_counter: dict[str, int] = {}
    ids, documents, metadatas, embed_inputs = [], [], [], []
    for chunk in chunks:
        idx = per_source_counter.get(chunk.source, 0)
        per_source_counter[chunk.source] = idx + 1
        ids.append(f"{chunk.source}::{idx}")
        documents.append(chunk.text)                       # clean text (shown to LLM)
        metadatas.append({"source": chunk.source, "chunk_index": idx})
        embed_inputs.append(chunk.with_source_prefix())    # embed WITH source label

    print(f"Embedding {len(documents)} chunks ...")
    embeddings = embed(embed_inputs)
    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Stored {collection.count()} chunks in collection '{COLLECTION_NAME}' at {persist_dir}")
    return collection


def get_collection(persist_dir: Path = PERSIST_DIR):
    """Open the existing persisted collection (build it first if missing/empty)."""
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return build_index(persist_dir)
    if collection.count() == 0:
        return build_index(persist_dir)
    return collection


# --- Stage 4: retrieval -------------------------------------------------------

def retrieve(query: str, k: int = DEFAULT_TOP_K,
             max_distance: float | None = None,
             persist_dir: Path = PERSIST_DIR) -> list[RetrievedChunk]:
    """Return the top-k chunks most similar to `query`, each with source + distance.

    If `max_distance` is set, chunks weaker than that cosine distance are dropped so a
    sparse query doesn't pad the context with loosely related material (planning.md k=5
    + relevance threshold).
    """
    collection = get_collection(persist_dir)
    query_embedding = embed([query])
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved: list[RetrievedChunk] = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        if max_distance is not None and dist > max_distance:
            continue
        retrieved.append(RetrievedChunk(
            text=doc, source=meta["source"],
            chunk_index=meta["chunk_index"], distance=dist,
        ))
    return retrieved


# --- Test harness (do not skip — verify retrieval before adding generation) ---

def _print_results(query: str, results: list[RetrievedChunk]) -> None:
    print("\n" + "=" * 78)
    print(f"QUERY: {query}")
    print("=" * 78)
    if not results:
        print("  (no results)")
        return
    for rank, r in enumerate(results, 1):
        flag = "  <-- weak match (>0.6)" if r.distance > 0.6 else ""
        print(f"\n[{rank}] distance={r.distance:.3f}{flag}")
        print(f"    source: {r.source}  (chunk {r.chunk_index})")
        preview = r.text.replace("\n", " ")
        print(f"    {preview[:300]}{'...' if len(preview) > 300 else ''}")


def run_eval(k: int = DEFAULT_TOP_K) -> None:
    for query in EVAL_QUERIES:
        _print_results(query, retrieve(query, k=k))


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunks and test retrieval.")
    parser.add_argument("--build", action="store_true", help="rebuild the index from documents/")
    parser.add_argument("-q", "--query", help="run a single ad-hoc query")
    parser.add_argument("-k", type=int, default=DEFAULT_TOP_K, help="top-k chunks to retrieve")
    args = parser.parse_args()

    if args.build:
        build_index()
    if args.query:
        _print_results(args.query, retrieve(args.query, k=args.k))
    else:
        run_eval(k=args.k)


if __name__ == "__main__":
    main()
