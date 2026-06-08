# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Off-campus housing for Stevens Institute of Technology students** in Hoboken, NJ and the
surrounding Hudson County towns (Jersey City, Weehawken, Union City).

Stevens' own pages only point students to listing sites and offer generic advice like "visit
the area during the day and at night" — they don't tell you which specific buildings nickel-and-dime
tenants, which streets and floors flood, where broker fees and mid-lease rent hikes bite hardest,
or how the Hoboken-vs-Jersey-City price tradeoff actually plays out on a student budget. That
lived-experience knowledge is scattered across building-review sites, neighborhood blogs, and
Reddit threads, so answering one concrete question (e.g. "is the Hudson Tea Building worth the rent?")
means reading across all of them — exactly the gap a retrieval system can close.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Stevens — "Living on Your Own" | Official off-campus housing guidance: safety, commuting, finding an apartment | https://www.stevens.edu/living-on-your-own |
| 2 | Stevens — Graduate Student Housing | Official off-campus + international student resources, roommate discussion board | https://www.stevens.edu/housing-resources-for-graduate-students |
| 3 | Redfin — Hoboken Neighborhood Guide | Where-to-live breakdown by area (Downtown / Uptown / Waterfront) | https://www.redfin.com/blog/hoboken-nj-neighborhoods/ |
| 4 | Apartments.com — Hoboken Local Guide | Rental price ranges by bedroom count and neighborhood | https://www.apartments.com/local-guide/hoboken-nj/ |
| 5 | NJ Real Estate Network — Moving to Hoboken | Long-form guide: cost of living, flooding risk, parking, commute | https://www.newjerseyrealestatenetwork.com/blog/moving-to-hoboken-nj/ |
| 6 | ApartmentRatings — Hoboken South Waterfront (333 River St) | 155 tenant reviews; management/fee complaints vs. amenities | https://www.apartmentratings.com/nj/hoboken/hoboken-south-waterfront_201222100007030/ |
| 7 | ApartmentRatings — Hudson Tea Building (1500 Washington St) | 61 tenant reviews; recurring flooding/maintenance issues | https://www.apartmentratings.com/nj/hoboken/the-hudson-tea-building_201792890007030/ |
| 8 | ApartmentRatings — 101 Clinton Street | 14 tenant reviews; strict-but-well-run, lower comparable rent | https://www.apartmentratings.com/nj/hoboken/101-clinton-street_201659900707030/ |
| 9 | ApartmentRatings — Hoboken (sorted by reviews) | Aggregate page across ~50 buildings; cross-building comparison | https://www.apartmentratings.com/nj/hoboken/sort-by-reviews/ |
| 10 | Renters Canary — Hoboken | Tenant reviews on rent hikes and landlord behavior across addresses | https://www.renterscanary.com/city/Hoboken |
| 11 | Quora — Cost of living for a student in Hoboken / JC / Union City | Student-perspective Q&A comparing the three towns | https://www.quora.com/What-is-the-cost-of-living-for-a-student-in-Hoboken-Jersey-City-or-Union-City-NJ |
| 12 | r/Hoboken | Community threads on neighborhoods, broker fees, landlords, "where to live" | https://www.reddit.com/r/Hoboken/ |
| 13 | r/Stevens | Student threads on off-campus apartments and roommates near campus | https://www.reddit.com/r/Stevens/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 600 characters (≈130–150 word-piece tokens)

**Overlap:** 100 characters (≈1 sentence)

**Reasoning:** My corpus is structurally mixed — many short, self-contained tenant reviews
(ApartmentRatings, Renters Canary, Reddit) and a handful of long-form guides (Stevens pages,
Redfin, NJ Real Estate Network). Two constraints set the size:

- The embedding model `all-MiniLM-L6-v2` silently **truncates input at 256 tokens**, so a chunk
  must stay well under that or the tail of a chunk never gets embedded. 600 chars (~140 tokens)
  leaves comfortable headroom.
- Most individual reviews are *shorter* than 600 chars, so they stay intact as a single chunk —
  exactly what I want, since one review = one coherent opinion and splitting it would scatter a
  single tenant's experience across vectors.

For the long guides, 600 chars splits them into paragraph-sized pieces, and the 100-char overlap
carries a sentence across each boundary so a fact that straddles a split (e.g. "...avoid basement
and first-floor apartments" / "...because Hoboken floods") isn't cut in half.

**Preprocessing before chunking:** strip HTML/boilerplate (nav, ads, cookie banners), collapse
repeated whitespace, and prepend each chunk with its source label (building name / page title) so
attribution survives into retrieval.

**Implementation note (added during Milestone 2):** the chunker (`ingest.py`) is *paragraph-aware*
rather than a blind fixed-width window. It packs whole blocks (a short review, a guide paragraph)
up to 600 chars so a single review/opinion stays in one chunk, and only applies the 100-char
overlap when it must window a paragraph that is itself longer than 600 chars. Bare section headers
(e.g. "Flooding") are merged forward into the section they introduce so a heading is never orphaned
at the end of a chunk. On the current sample corpus this yields **51 chunks across 13 documents**
(avg ~424 chars, max token length 157 — well under the embedder's 256-token cap).

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally, free,
fast on CPU — well suited to a small student corpus).

**Top-k:** 5 chunks per query. Housing answers usually require synthesizing across *several*
reviews ("what do tenants say about X building"), so a single top result is too thin; 5 gives the
model enough corroborating voices without flooding the context with off-topic chunks. I'll also
filter out chunks below a relevance threshold so a sparse query doesn't pad the context with junk.

**Production tradeoff reflection:** If cost weren't a constraint and this served real students, I'd
weigh:

- **Domain accuracy** — MiniLM is a small general model. A stronger hosted embedder (OpenAI
  `text-embedding-3-large`, Voyage `voyage-3`, which Anthropic recommends for retrieval) would
  better distinguish near-duplicate housing language ("broker fee" vs "application fee," or that
  "333 River St" *is* "Hoboken South Waterfront").
- **Context length** — MiniLM's 256-token cap forces aggressive chunking; models with 8k+ token
  windows would let me embed whole reviews or guide sections without splitting.
- **Multilingual support** — Stevens has many international students; a multilingual embedder
  (e.g. Cohere `embed-multilingual-v3`) would let non-English queries/sources work.
- **Latency & hosting** — local MiniLM has zero network latency and no API cost or privacy
  exposure; an API embedder adds per-call cost and latency but offloads compute. For a class
  project the local model wins; at scale I'd benchmark a hosted model's accuracy gain against its
  cost-per-query before switching.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do tenants say about flooding or water problems at the Hudson Tea Building? | Reviewers report recurring bathroom flooding (one says 4–5×/week for the first ~5 months) that took significant hassle to get fixed. (Source: ApartmentRatings #7) |
| 2 | How should I pick an apartment in Hoboken to minimize flood risk? | Avoid basement and first-floor units; Hoboken is low-lying and floods, so upper floors are safer. (Source: NJ Real Estate Network #5) |
| 3 | Is Uptown or Downtown Hoboken better/cheaper for a quieter place to live? | Uptown (north end) is quieter and more residential with somewhat lower 1-BR rent (~$3,852); Downtown is pricier with more nightlife, foot traffic, and PATH access. (Sources: Redfin #3, Apartments.com #4) |
| 4 | For a student on a budget, how does renting in Jersey City compare to Hoboken? | Hoboken has the highest rents in the area; Jersey City, Union City, and Weehawken are cheaper alternatives within commuting distance of Stevens. (Sources: Stevens #2, Quora #11) |
| 5 | What are tenants' main complaints about management at Hoboken South Waterfront (333 River St)? | Despite great amenities/location, tenants report management "nickel-and-diming" — e.g. over a replacement kitchen light and proof-of-renters-insurance. (Source: ApartmentRatings #6) |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Mixed document structure breaks a single chunk size.** Short reviews and long guides live in
   the same corpus. A chunk size tuned for guides over-fragments reviews; one tuned for reviews
   splits a guide's key fact (e.g. flood advice) across a boundary so retrieval returns only half
   the context. Mitigation: a chunk size + overlap chosen to keep most reviews whole while still
   splitting guides cleanly (see Chunking Strategy), and overlap to bridge boundary facts.

2. **Subjective, conflicting reviews → biased or overgeneralized answers.** Two tenants can rate
   the same building 1★ and 5★. Top-k retrieval might surface only one side, and the LLM could
   present a single opinion as fact. Mitigation: retrieve enough chunks (k=5) to capture multiple
   voices, and instruct the model to attribute and hedge ("some tenants report…") rather than state
   opinions as universal truth.

3. **Stale prices and listings stated as current.** Rent figures and "current" availability go out
   of date fast, but the model can't tell. Mitigation: keep source attribution on every chunk so
   answers cite where a figure came from, and frame numbers as approximate/as-of rather than live.

4. **Building name vs. address ambiguity.** A query for "333 River Street" may not embed close to
   "Hoboken South Waterfront," missing relevant reviews. Mitigation: prepend each chunk with both
   the building name and address during preprocessing so either phrasing retrieves it.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. DOCUMENT INGESTION                                                     │
│     documents/*.txt|*.md  (saved reviews, guides, Reddit/Quora threads)    │
│     tools: Python file I/O  ·  python-dotenv (config/keys)                 │
└───────────────────────────────┬───────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. CHUNKING                                                               │
│     clean HTML/whitespace → split into 600-char chunks, 100-char overlap   │
│     prepend source label (building name + address / page title)            │
│     tools: custom chunk_text() in Python                                   │
└───────────────────────────────┬───────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. EMBEDDING + VECTOR STORE                                               │
│     embed each chunk → 384-dim vector → store with source metadata         │
│     tools: sentence-transformers (all-MiniLM-L6-v2)  ·  ChromaDB           │
└───────────────────────────────┬───────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. RETRIEVAL                                                              │
│     embed user query → similarity search → top-k=5 chunks (+ threshold)    │
│     tools: ChromaDB query  ·  sentence-transformers (same model)           │
└───────────────────────────────┬───────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. GENERATION                                                             │
│     stuff retrieved chunks + sources into a grounded prompt → answer       │
│     with citations; refuse if context is insufficient                      │
│     tools: Groq API (LLM)  ·  Gradio/Streamlit front-end (Milestone 5)     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- *Tool:* Claude (in Claude Code).
- *Input I'll give it:* my **Chunking Strategy** section (600-char chunks, 100-char overlap,
  source-label prepend, HTML/whitespace cleaning) plus a sample of two real documents — one short
  review file and one long guide file.
- *What I expect it to produce:* a `load_documents()` that reads `documents/` and a `chunk_text()`
  that returns chunks with `{text, source}` metadata, matching my exact size/overlap numbers.
- *How I'll verify:* run it on my corpus, print the chunk count and the longest chunk's token
  length to confirm nothing exceeds the model's 256-token limit, and eyeball that a review wasn't
  split mid-opinion.

**Milestone 4 — Embedding and retrieval:**
- *Tool:* Claude.
- *Input I'll give it:* my **Retrieval Approach** section (all-MiniLM-L6-v2, ChromaDB, top-k=5 with
  a relevance threshold) and the chunk format from Milestone 3.
- *What I expect it to produce:* code to embed chunks, persist them in ChromaDB with source
  metadata, and a `retrieve(query, k=5)` that returns chunks + sources + scores.
- *How I'll verify:* run my 5 evaluation questions through `retrieve()` and check that the expected
  source document appears in the top-5 for each (e.g. the Hudson Tea review surfaces for the
  flooding question).

**Milestone 5 — Generation and interface:**
- *Tool:* Claude.
- *Input I'll give it:* my **Grounded Generation** requirement and the retrieval output format.
- *What I expect it to produce:* a Groq call with a system prompt that forces the model to answer
  only from retrieved chunks, cite sources, and say "I don't have that in my documents" when
  context is insufficient — wrapped in a Gradio or Streamlit UI.
- *How I'll verify:* ask an out-of-domain question (e.g. "what's the best pizza in Hoboken?") and
  confirm it declines instead of hallucinating, and check that in-domain answers cite the right
  building/page.
