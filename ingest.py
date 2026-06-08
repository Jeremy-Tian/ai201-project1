"""Document ingestion + chunking for The Unofficial Guide (Off-Campus Housing @ Stevens).

Pipeline stages 1 and 2 from planning.md:
    1. DOCUMENT INGESTION  -> load every file in documents/ into memory
    2. CHUNKING            -> clean text, then split into 600-char chunks with 100-char
                              overlap, each tagged with its source.

Run it directly to load -> clean -> chunk -> inspect:

    python ingest.py                 # load, chunk, and print inspection report
    python ingest.py --check-tokens  # also verify no chunk exceeds the embedder's 256-token cap

The chunk size / overlap numbers come straight from the Chunking Strategy section of
planning.md. If you change them here, update planning.md too (and say why).
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

# --- Configuration (mirrors planning.md > Chunking Strategy) -------------------

DOCUMENTS_DIR = Path(__file__).parent / "documents"

# all-MiniLM-L6-v2 truncates input at 256 word-piece tokens. 600 chars (~140 tokens)
# leaves headroom, keeps most short reviews intact as a single chunk, and splits long
# guides into paragraph-sized pieces.
CHUNK_SIZE = 600          # characters of body text per chunk
CHUNK_OVERLAP = 100       # characters carried from the end of one chunk into the next

# File extensions we treat as documents. PDFs are out of scope unless you uncomment
# pdfplumber in requirements.txt; copy PDF text into a .txt file instead.
SUPPORTED_EXTENSIONS = {".txt", ".md"}


# --- Data model ---------------------------------------------------------------

@dataclass
class Chunk:
    """A single retrievable chunk plus the source it came from."""
    text: str       # the chunk body (without the source prefix)
    source: str     # filename / document label, kept as metadata for attribution

    def with_source_prefix(self) -> str:
        """Text as it will be embedded: source label prepended so attribution and
        building/page names survive into the vector (see planning.md challenge #4)."""
        return f"[Source: {self.source}]\n{self.text}"


# --- Stage 1: load ------------------------------------------------------------

def load_documents(directory: Path = DOCUMENTS_DIR) -> list[tuple[str, str]]:
    """Read every supported file in `directory`. Returns (source_name, raw_text) pairs."""
    if not directory.exists():
        raise FileNotFoundError(f"documents directory not found: {directory}")

    docs: list[tuple[str, str]] = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            print(f"  ! skipping empty file: {path.name}")
            continue
        docs.append((path.name, raw))
    return docs


# --- Stage 2a: clean ----------------------------------------------------------

# Boilerplate lines that show up when text is copied from a web page. Matched
# case-insensitively against a whole stripped line; extend this as you spot junk.
_BOILERPLATE_PATTERNS = [
    r"^read more$",
    r"^show more$",
    r"^see all reviews?$",
    r"^share$",
    r"^reply$",
    r"^report$",
    r"^\d+ comments?$",
    r"^\d+ (likes?|upvotes?)$",
    r"^helpful\??$",
    r"^was this review helpful.*$",
    r"^advertisement$",
    r"^cookie.*(policy|consent|settings).*$",
    r"^accept all cookies$",
    r"^sign in$",
    r"^log in$",
    r"^menu$",
]
_BOILERPLATE_RE = re.compile("|".join(_BOILERPLATE_PATTERNS), re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def clean_text(text: str) -> str:
    """Strip HTML, decode entities, drop common web boilerplate, normalize whitespace.

    Keeps the substantive content (reviews, opinions, ratings, building/page context)
    and removes nav/ads/footers/share buttons per the Milestone 2 cleaning checklist.
    """
    # Remove HTML tags, then decode entities (&amp; &#39; &nbsp; ...).
    text = _HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")  # leftover non-breaking spaces

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")          # keep blank lines as paragraph breaks
            continue
        if _BOILERPLATE_RE.match(stripped):
            continue                          # drop boilerplate line entirely
        stripped = re.sub(r"[ \t]+", " ", stripped)  # collapse runs of spaces/tabs
        cleaned_lines.append(stripped)

    # Collapse 3+ blank lines down to a single paragraph break.
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# --- Stage 2b: chunk ----------------------------------------------------------

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def _split_long_block(block: str, chunk_size: int, overlap: int) -> list[str]:
    """Sliding window over a block too big to be one chunk. Breaks at sentence
    boundaries where possible (falls back to a hard char cut), with `overlap` chars
    carried between consecutive windows so boundary-straddling facts aren't severed."""
    sentences = _SENTENCE_END_RE.split(block)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # A single sentence longer than chunk_size: hard-slice it with overlap.
        if len(sentence) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(sentence):
                chunks.append(sentence[start:start + chunk_size].strip())
                start += chunk_size - overlap
            continue

        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            chunks.append(current.strip())
            # Start the next window with the tail (overlap) of the one we just closed.
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {sentence}".strip()

    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c]


def _looks_like_header(block: str) -> bool:
    """A short, single-line block with no sentence-ending punctuation — e.g. a section
    heading like "Flooding" or "Neighborhoods" that belongs with the text below it."""
    return (
        "\n" not in block
        and len(block) < 50
        and not block.endswith((".", "!", "?", ":"))
        and not block.lstrip().startswith("★")
    )


def _merge_headers(blocks: list[str]) -> list[str]:
    """Attach a bare section header to the block that follows it, so a heading is never
    orphaned at the end of a chunk away from the content it introduces."""
    merged: list[str] = []
    i = 0
    while i < len(blocks):
        if _looks_like_header(blocks[i]) and i + 1 < len(blocks):
            merged.append(f"{blocks[i]}\n\n{blocks[i + 1]}")
            i += 2
        else:
            merged.append(blocks[i])
            i += 1
    return merged


def chunk_document(text: str, source: str,
                   chunk_size: int = CHUNK_SIZE,
                   overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    """Paragraph-aware chunking. Short reviews (separated by blank lines) stay whole;
    paragraphs are packed up to chunk_size; anything still too long is windowed."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    blocks = _merge_headers(blocks)
    chunks: list[str] = []
    current = ""

    for block in blocks:
        # Block alone exceeds the budget -> flush, then window the block.
        if len(block) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_block(block, chunk_size, overlap))
            continue

        # Pack this block onto the current chunk if it fits.
        if len(current) + len(block) + 2 <= chunk_size:
            current = f"{current}\n\n{block}".strip()
        else:
            if current:
                chunks.append(current.strip())
            current = block

    if current.strip():
        chunks.append(current.strip())

    return [Chunk(text=c, source=source) for c in chunks if c]


def build_chunks(directory: Path = DOCUMENTS_DIR,
                 chunk_size: int = CHUNK_SIZE,
                 overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    """Full stages 1-2: load -> clean -> chunk every document in `directory`."""
    documents = load_documents(directory)
    all_chunks: list[Chunk] = []
    for source, raw in documents:
        cleaned = clean_text(raw)
        all_chunks.extend(chunk_document(cleaned, source, chunk_size, overlap))
    return all_chunks


# --- Inspection (do not skip — Milestone 2 requires verifying chunk quality) ---

def inspect(chunks: list[Chunk], check_tokens: bool = False) -> None:
    """Print the stats and sample chunks the assignment asks you to eyeball."""
    sources = sorted({c.source for c in chunks})
    print("\n" + "=" * 70)
    print("CHUNK INSPECTION REPORT")
    print("=" * 70)
    print(f"Documents:      {len(sources)}")
    print(f"Total chunks:   {len(chunks)}")

    if not chunks:
        print("\nNo chunks produced. Add .txt/.md files to documents/ and re-run.")
        return

    lengths = [len(c.text) for c in chunks]
    print(f"Chunk chars:    min {min(lengths)} | avg {sum(lengths)//len(lengths)} | max {max(lengths)}")

    # Sanity flags from the milestone instructions.
    if len(chunks) < 50:
        print("  ! WARNING: <50 chunks across your corpus — chunks may be too large.")
    if len(chunks) > 2000:
        print("  ! WARNING: >2000 chunks — chunks may be too small to carry meaning.")

    print("\nChunks per document:")
    for s in sources:
        print(f"  {sum(1 for c in chunks if c.source == s):>4}  {s}")

    if check_tokens:
        _check_token_lengths(chunks)

    # 5 representative chunks, evenly spaced through the corpus.
    print("\n" + "-" * 70)
    print("5 REPRESENTATIVE CHUNKS (read these — can each answer a question alone?)")
    print("-" * 70)
    step = max(1, len(chunks) // 5)
    for i, chunk in enumerate(chunks[::step][:5]):
        print(f"\n[{i+1}] source={chunk.source}  ({len(chunk.text)} chars)")
        print(chunk.text)


def _check_token_lengths(chunks: list[Chunk]) -> None:
    """Confirm no chunk exceeds all-MiniLM-L6-v2's 256-token truncation limit."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\n  ! sentence-transformers not installed; skipping token check.")
        return
    print("\nLoading tokenizer to verify token lengths (<=256)...")
    tokenizer = SentenceTransformer("all-MiniLM-L6-v2").tokenizer
    token_counts = [len(tokenizer.encode(c.with_source_prefix())) for c in chunks]
    over = sum(1 for t in token_counts if t > 256)
    print(f"Token counts:   min {min(token_counts)} | avg {sum(token_counts)//len(token_counts)} | max {max(token_counts)}")
    if over:
        print(f"  ! WARNING: {over} chunk(s) exceed 256 tokens and will be truncated.")
    else:
        print("  OK: all chunks fit within the 256-token embedding limit.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load, clean, and chunk documents.")
    parser.add_argument("--check-tokens", action="store_true",
                        help="load the embedder's tokenizer and verify chunk token lengths")
    args = parser.parse_args()

    chunks = build_chunks()
    inspect(chunks, check_tokens=args.check_tokens)


if __name__ == "__main__":
    main()
