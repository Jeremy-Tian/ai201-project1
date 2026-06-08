"""Grounded generation for The Unofficial Guide (pipeline stage 5).

Wires retrieval -> LLM. The end-to-end entry point is `ask(question)`, which:
  1. retrieves the top-k chunks for the question,
  2. drops chunks weaker than a cosine-distance threshold (so an off-topic question
     retrieves nothing usable and we can refuse instead of hallucinating),
  3. builds a context block and a strict system prompt that forces the model to answer
     ONLY from that context,
  4. calls Groq's llama-3.3-70b-versatile, and
  5. returns {"answer": ..., "sources": [...]} where `sources` is built programmatically
     from the retrieved chunks' metadata — NOT parsed out of the model's text.

Grounding is enforced two ways:
  - If no chunk clears the relevance threshold, we short-circuit and return the
    "not enough information" answer without ever calling the LLM.
  - The system prompt instructs the model to use only the provided context and to refuse
    when the context is insufficient.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

from retrieval import retrieve, RetrievedChunk

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5
# Cosine distance above this is treated as "not really about the question". Observed
# in-domain top hits were ~0.21-0.31; clearly off-topic queries score much higher.
RELEVANCE_THRESHOLD = 0.65

REFUSAL = "I don't have enough information on that in the documents I have."

SYSTEM_PROMPT = """You are an assistant for off-campus housing near Stevens Institute of \
Technology in Hoboken, NJ. You answer ONLY using the numbered context passages provided in \
the user's message.

Rules:
- Use only facts stated in the context. Do not use any outside or general knowledge.
- If the context does not contain enough information to answer, reply with exactly: \
"I don't have enough information on that in the documents I have." Do not guess or pad with \
general advice.
- Cite the sources you used inline by their filename, e.g. (source: redfin_hoboken_neighborhoods.txt).
- When tenants disagree, attribute the opinions ("some reviewers say...") rather than stating \
them as universal fact.
- Be concise and specific."""


_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set — add it to your .env file.")
        _client = Groq(api_key=key)
    return _client


def _format_context(chunks: list[RetrievedChunk]) -> str:
    """Number each chunk and tag it with its source so the model can cite it."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c.source})\n{c.text}")
    return "\n\n".join(blocks)


def ask(question: str, k: int = TOP_K,
        threshold: float = RELEVANCE_THRESHOLD) -> dict:
    """Answer `question` grounded in retrieved documents.

    Returns {"answer": str, "sources": list[str], "chunks": list[RetrievedChunk]}.
    `sources` is derived from retrieval metadata, so attribution is guaranteed even if
    the model forgets to cite.
    """
    chunks = retrieve(question, k=k, max_distance=threshold)

    # No usable context -> refuse without calling the LLM (handles out-of-domain queries).
    if not chunks:
        return {"answer": REFUSAL, "sources": [], "chunks": []}

    context = _format_context(chunks)
    user_message = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )

    response = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0.1,  # low temperature keeps the model close to the source text
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = response.choices[0].message.content.strip()

    # If the model judged the context insufficient and refused, don't attach sources —
    # listing them would falsely imply the answer came from those documents.
    if answer.rstrip(".").strip().lower() == REFUSAL.rstrip(".").strip().lower():
        return {"answer": REFUSAL, "sources": [], "chunks": []}

    # Programmatic attribution: unique sources, in order of first appearance.
    seen, sources = set(), []
    for c in chunks:
        if c.source not in seen:
            seen.add(c.source)
            sources.append(c.source)

    return {"answer": answer, "sources": sources, "chunks": chunks}


def _demo() -> None:
    """Quick end-to-end check, including an out-of-domain question that should be refused."""
    questions = [
        "What do tenants say about flooding at the Hudson Tea Building?",
        "How do I minimize flood risk when renting in Hoboken?",
        "Is Jersey City cheaper than Hoboken for a student?",
        "What's the best pizza place in Hoboken?",  # out of domain -> should refuse
    ]
    for q in questions:
        result = ask(q)
        print("\n" + "=" * 78)
        print(f"Q: {q}")
        print("-" * 78)
        print(result["answer"])
        print(f"\nRetrieved from: {', '.join(result['sources']) or '(none)'}")


if __name__ == "__main__":
    _demo()
